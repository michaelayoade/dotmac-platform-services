"""
Production-ready structured logging for dotmac platform services.

Supports:
- JSON structured logging with correlation IDs
- Configurable log levels and formats
- Multi-tenant request context
- Performance metrics integration
- Audit logging for security events
- Log aggregation compatibility (ELK, Datadog, etc.)
"""

import logging
import logging.config
import random
import threading
import time
from collections.abc import Callable, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

import structlog

from .config import ObservabilityConfig


class LogLevel(str, Enum):
    """Log level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogContext:
    """
    Request context management for logging.

    Maintains contextual information throughout the request lifecycle,
    including correlation IDs, tenant information, and user context.
    """

    correlation_id: str = field(default_factory=lambda: str(uuid4()))
    tenant_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    request_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None
    operation: str | None = None
    additional_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary for logging."""
        context = {
            "correlation_id": self.correlation_id,
        }

        if self.tenant_id:
            context["tenant_id"] = self.tenant_id
        if self.user_id:
            context["user_id"] = self.user_id
        if self.session_id:
            context["session_id"] = self.session_id
        if self.request_id:
            context["request_id"] = self.request_id
        if self.trace_id:
            context["trace_id"] = self.trace_id
        if self.span_id:
            context["span_id"] = self.span_id
        if self.operation:
            context["operation"] = self.operation

        context.update(self.additional_context)
        return context

    def with_operation(self, operation: str) -> "LogContext":
        """Create new context with operation set."""
        return LogContext(
            correlation_id=self.correlation_id,
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            session_id=self.session_id,
            request_id=self.request_id,
            trace_id=self.trace_id,
            span_id=self.span_id,
            operation=operation,
            additional_context=self.additional_context.copy(),
        )

    def with_context(self, **kwargs) -> "LogContext":
        """Create new context with additional context."""
        return LogContext(
            correlation_id=self.correlation_id,
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            session_id=self.session_id,
            request_id=self.request_id,
            trace_id=self.trace_id,
            span_id=self.span_id,
            operation=self.operation,
            additional_context={**self.additional_context, **kwargs},
        )


class LogFilter:
    """
    Advanced log filtering based on various criteria.
    """

    def __init__(
        self,
        min_level: LogLevel = LogLevel.DEBUG,
        tenant_allowlist: list[str] | None = None,
        tenant_blocklist: list[str] | None = None,
        user_allowlist: list[str] | None = None,
        user_blocklist: list[str] | None = None,
        operation_allowlist: list[str] | None = None,
        operation_blocklist: list[str] | None = None,
        custom_filters: list[Callable[[dict[str, Any]], bool]] | None = None,
    ) -> None:
        self.min_level = min_level
        self.tenant_allowlist = tenant_allowlist or []
        self.tenant_blocklist = tenant_blocklist or []
        self.user_allowlist = user_allowlist or []
        self.user_blocklist = user_blocklist or []
        self.operation_allowlist = operation_allowlist or []
        self.operation_blocklist = operation_blocklist or []
        self.custom_filters = custom_filters or []

    def should_log(self, level: str, context: dict[str, Any]) -> bool:
        """Determine if log entry should be processed."""
        # Level check
        log_levels = {"debug": 10, "info": 20, "warning": 30, "error": 40, "critical": 50}
        # Normalize to lowercase to match keys in log_levels
        min_level_value = log_levels.get(self.min_level.value.lower(), 10)
        current_level_value = log_levels.get(level.lower(), 10)

        if current_level_value < min_level_value:
            return False

        # Tenant filtering
        tenant_id = context.get("tenant_id")
        if tenant_id:
            if self.tenant_allowlist and tenant_id not in self.tenant_allowlist:
                return False
            if self.tenant_blocklist and tenant_id in self.tenant_blocklist:
                return False

        # User filtering
        user_id = context.get("user_id")
        if user_id:
            if self.user_allowlist and user_id not in self.user_allowlist:
                return False
            if self.user_blocklist and user_id in self.user_blocklist:
                return False

        # Operation filtering
        operation = context.get("operation")
        if operation:
            if self.operation_allowlist and operation not in self.operation_allowlist:
                return False
            if self.operation_blocklist and operation in self.operation_blocklist:
                return False

        # Custom filters
        return all(custom_filter(context) for custom_filter in self.custom_filters)


class LogSampler:
    """
    Log sampling for high-volume scenarios.

    Implements various sampling strategies to reduce log volume
    while maintaining statistical significance.
    """

    def __init__(
        self,
        sample_rate: float = 1.0,
        burst_capacity: int = 100,
        per_tenant_rates: dict[str, float] | None = None,
        per_operation_rates: dict[str, float] | None = None,
    ) -> None:
        self.sample_rate = sample_rate
        self.burst_capacity = burst_capacity
        self.per_tenant_rates = per_tenant_rates or {}
        self.per_operation_rates = per_operation_rates or {}

        # Rate limiting state
        self._token_bucket = burst_capacity
        self._last_refill = time.time()
        self._lock = threading.Lock()

    def should_sample(self, context: dict[str, Any]) -> bool:
        """Determine if log entry should be sampled."""
        # Check rate limits first
        if not self._check_rate_limit():
            return False

        # Determine sampling rate
        effective_rate = self.sample_rate

        # Per-tenant sampling
        tenant_id = context.get("tenant_id")
        if tenant_id in self.per_tenant_rates:
            effective_rate = min(effective_rate, self.per_tenant_rates[tenant_id])

        # Per-operation sampling
        operation = context.get("operation")
        if operation in self.per_operation_rates:
            effective_rate = min(effective_rate, self.per_operation_rates[operation])

        # Always sample errors and critical logs
        level = context.get("level", "info").lower()
        if level in ["error", "critical"]:
            effective_rate = 1.0

        # Random sampling
        return random.random() < effective_rate

    def _check_rate_limit(self) -> bool:
        """Check if within rate limit using token bucket."""
        with self._lock:
            now = time.time()

            # Refill tokens
            time_elapsed = now - self._last_refill
            tokens_to_add = int(time_elapsed * self.burst_capacity)
            self._token_bucket = min(self.burst_capacity, self._token_bucket + tokens_to_add)
            self._last_refill = now

            # Check if we have tokens
            if self._token_bucket > 0:
                self._token_bucket -= 1
                return True

            return False


class LogAggregator:
    """
    Log aggregation helpers for reducing duplicate entries.

    Groups similar log entries and emits aggregated statistics.
    """

    def __init__(
        self,
        window_size: int = 60,
        max_entries: int = 1000,
        aggregate_keys: list[str] | None = None,
    ) -> None:
        self.window_size = window_size
        self.max_entries = max_entries
        self.aggregate_keys = aggregate_keys or ["level", "message", "operation"]

        self._entries: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._last_flush = time.time()

    def add_entry(self, level: str, message: str, context: dict[str, Any]) -> dict[str, Any] | None:
        """Add log entry for aggregation."""
        # Create aggregation key
        key_parts = []
        for key in self.aggregate_keys:
            if key == "level":
                key_parts.append(level)
            elif key == "message":
                key_parts.append(message)
            else:
                key_parts.append(str(context.get(key, "")))

        agg_key = "|".join(key_parts)

        with self._lock:
            current_time = time.time()

            # Check if we need to flush
            if current_time - self._last_flush > self.window_size:
                self._flush_entries()

            # Add or update entry
            if agg_key not in self._entries:
                self._entries[agg_key] = {
                    "level": level,
                    "message": message,
                    "context": context.copy(),
                    "count": 1,
                    "first_seen": current_time,
                    "last_seen": current_time,
                    "sample_contexts": [context.copy()],
                }
            else:
                entry = self._entries[agg_key]
                entry["count"] += 1
                entry["last_seen"] = current_time

                # Keep sample contexts (up to 5)
                if len(entry["sample_contexts"]) < 5:
                    entry["sample_contexts"].append(context.copy())

            # Check if we should emit aggregated entry
            entry = self._entries[agg_key]
            if entry["count"] == 1:
                # First occurrence, emit immediately
                return None
            if entry["count"] % 10 == 0:  # Emit every 10 occurrences
                return self._create_aggregated_entry(agg_key, entry)

            return None

    def _flush_entries(self) -> list[dict[str, Any]]:
        """Flush accumulated entries."""
        aggregated_entries = []

        for key, entry in self._entries.items():
            if entry["count"] > 1:
                aggregated_entries.append(self._create_aggregated_entry(key, entry))

        self._entries.clear()
        self._last_flush = time.time()

        return aggregated_entries

    def _create_aggregated_entry(self, key: str, entry: dict[str, Any]) -> dict[str, Any]:
        """Create aggregated log entry."""
        return {
            "level": entry["level"],
            "message": f"[AGGREGATED] {entry['message']} (occurred {entry['count']} times)",
            "context": {
                **entry["context"],
                "aggregation": {
                    "count": entry["count"],
                    "first_seen": entry["first_seen"],
                    "last_seen": entry["last_seen"],
                    "window_seconds": entry["last_seen"] - entry["first_seen"],
                    "sample_contexts": entry["sample_contexts"],
                },
            },
        }


class PerformanceLogger:
    """
    Specialized logger for performance metrics and timing.
    """

    def __init__(self, logger: "StructuredLogger") -> None:
        self.logger = logger
        self._active_operations: dict[str, float] = {}

    def start_operation(self, operation: str, context: dict[str, Any] | None = None) -> str:
        """Start timing an operation."""
        operation_id = f"{operation}_{uuid4()}"
        self._active_operations[operation_id] = time.time()

        self.logger.debug(
            f"Operation started: {operation}",
            operation=operation,
            operation_id=operation_id,
            **(context or {}),
        )

        return operation_id

    def end_operation(
        self, operation_id: str, success: bool = True, result_data: dict[str, Any] | None = None
    ) -> float:
        """End timing an operation."""
        if operation_id not in self._active_operations:
            self.logger.warning(f"Unknown operation ID: {operation_id}")
            return 0.0

        start_time = self._active_operations.pop(operation_id)
        duration_ms = (time.time() - start_time) * 1000

        self.logger.performance(
            "Operation completed",
            operation_id=operation_id,
            duration_ms=duration_ms,
            success=success,
            **(result_data or {}),
        )

        return duration_ms

    @contextmanager
    def time_operation(self, operation: str, **context):
        """Context manager for timing operations."""
        operation_id = self.start_operation(operation, context)
        try:
            yield operation_id
            self.end_operation(operation_id, success=True)
        except Exception as e:
            self.end_operation(operation_id, success=False, result_data={"error": str(e)})
            raise


class CorrelationIDFilter(logging.Filter):
    """
    Logging filter that adds correlation ID to log records.

    Ensures all log records include correlation ID for request tracing.
    """

    def __init__(self, correlation_id_key: str = "correlation_id") -> None:
        super().__init__()
        self.correlation_id_key = correlation_id_key
        self._local = threading.local()

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID for current thread."""
        self._local.correlation_id = correlation_id

    def get_correlation_id(self) -> str | None:
        """Get correlation ID for current thread."""
        return getattr(self._local, "correlation_id", None)

    def clear_correlation_id(self) -> None:
        """Clear correlation ID for current thread."""
        if hasattr(self._local, "correlation_id"):
            delattr(self._local, "correlation_id")

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to log record."""
        correlation_id = self.get_correlation_id()
        if correlation_id:
            setattr(record, self.correlation_id_key, correlation_id)
        return True


class StructuredLogger:
    """
    Production-ready structured logger with correlation ID tracking.
    """

    def __init__(
        self,
        service_name: str,
        config: ObservabilityConfig | None = None,
        correlation_id: str | None = None,
        tenant_id: str | None = None,
    ) -> None:
        """
        Initialize structured logger.

        Args:
            service_name: Name of the service
            config: Observability configuration
            correlation_id: Request correlation ID
            tenant_id: Tenant identifier
        """
        self.service_name = service_name
        self.config = config or ObservabilityConfig()
        self.correlation_id = correlation_id or str(uuid4())
        self.tenant_id = tenant_id

        # Configure structlog
        self._configure_structlog()

        # Create logger instance
        self.logger = structlog.get_logger(service_name)

    def _configure_structlog(self) -> None:
        """Configure structlog for structured logging."""
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            self._add_context,
        ]

        if self.config.json_logging:
            processors.append(structlog.processors.JSONRenderer())
        else:
            processors.append(structlog.processors.KeyValueRenderer())

        structlog.configure(
            processors=processors,
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        # Configure standard library logging
        logging.basicConfig(
            format="%(message)s", stream=None, level=getattr(logging, self.config.log_level.upper())
        )

    def _add_context(self, logger, method_name, event_dict):
        """Add common context to log events."""
        event_dict.update(
            {
                "service": self.service_name,
                "correlation_id": self.correlation_id,
            }
        )

        if self.tenant_id:
            event_dict["tenant_id"] = self.tenant_id

        return event_dict

    def with_log_context(self, context: LogContext) -> "StructuredLogger":
        """Create logger with LogContext."""
        new_logger = StructuredLogger(
            service_name=self.service_name,
            config=self.config,
            correlation_id=context.correlation_id,
            tenant_id=context.tenant_id,
        )
        new_logger.logger = self.logger.bind(**context.to_dict())
        return new_logger

    def debug(self, msg: str, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(msg, **kwargs)

    def info(self, msg: str, **kwargs) -> None:
        """Log info message."""
        self.logger.info(msg, **kwargs)

    def warning(self, msg: str, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(msg, **kwargs)

    def error(self, msg: str, **kwargs) -> None:
        """Log error message."""
        self.logger.error(msg, **kwargs)

    def critical(self, msg: str, **kwargs) -> None:
        """Log critical message."""
        self.logger.critical(msg, **kwargs)

    def audit(self, action: str, resource: str, success: bool = True, **kwargs) -> None:
        """Log audit event."""
        self.logger.info(
            "Audit event",
            event_type="audit",
            action=action,
            resource=resource,
            success=success,
            **kwargs,
        )

    def security(self, event: str, risk_level: str = "medium", **kwargs) -> None:
        """Log security event."""
        self.logger.warning(
            "Security event", event_type="security", event=event, risk_level=risk_level, **kwargs
        )

    def performance(self, operation: str, duration_ms: float, **kwargs) -> None:
        """Log performance metric."""
        self.logger.info(
            "Performance metric",
            event_type="performance",
            operation=operation,
            duration_ms=duration_ms,
            **kwargs,
        )

    @contextmanager
    def time_operation(self, operation: str, **kwargs):
        """Context manager to time operations."""
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.performance(operation, duration_ms, **kwargs)

    def with_context(self, **kwargs) -> "StructuredLogger":
        """Create a new logger with additional context."""
        new_logger = StructuredLogger(
            service_name=self.service_name,
            config=self.config,
            correlation_id=self.correlation_id,
            tenant_id=self.tenant_id,
        )
        new_logger.logger = self.logger.bind(**kwargs)
        return new_logger

    @property
    def name(self) -> str:
        """Provide a stdlib-compatible name attribute for tests and integrations."""
        return self.service_name


class AuditLogger:
    """
    Specialized audit logger for security and compliance.
    """

    def __init__(self, service_name: str, config: ObservabilityConfig | None = None) -> None:
        self.service_name = service_name
        self.config = config or ObservabilityConfig()
        self.logger = StructuredLogger(f"{service_name}.audit", config)

    def user_action(
        self,
        user_id: str,
        action: str,
        resource: str,
        success: bool = True,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        """Log user action for audit trail."""
        self.logger.audit(
            action=action,
            resource=resource,
            success=success,
            user_id=user_id,
            details=(dict(details) if details is not None else {}),
        )

    def system_event(
        self,
        event: str,
        component: str,
        severity: str = "info",
        details: Mapping[str, Any] | None = None,
    ) -> None:
        """Log system event."""
        self.logger.info(
            "System event",
            event_type="system",
            event=event,
            component=component,
            severity=severity,
            details=(dict(details) if details is not None else {}),
        )

    def data_access(
        self,
        user_id: str,
        resource: str,
        operation: str,
        record_count: int = 0,
        success: bool = True,
    ) -> None:
        """Log data access for compliance."""
        self.logger.audit(
            action="data_access",
            resource=resource,
            success=success,
            user_id=user_id,
            operation=operation,
            record_count=record_count,
        )

    def authentication_event(
        self,
        user_id: str,
        event_type: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        success: bool = True,
    ) -> None:
        """Log authentication events."""
        self.logger.audit(
            action="authentication",
            resource="auth_system",
            success=success,
            user_id=user_id,
            auth_event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
        )


class LoggingManager:
    """
    Central logging manager for the platform.

    Enhanced with filtering, sampling, and aggregation capabilities.
    """

    def __init__(
        self,
        config: ObservabilityConfig | None = None,
        log_filter: LogFilter | None = None,
        log_sampler: LogSampler | None = None,
        log_aggregator: LogAggregator | None = None,
    ) -> None:
        self.config = config or ObservabilityConfig()
        self.log_filter = log_filter or LogFilter()
        self.log_sampler = log_sampler or LogSampler()
        self.log_aggregator = log_aggregator or LogAggregator()
        self._loggers: dict[str, StructuredLogger] = {}
        self._performance_loggers: dict[str, PerformanceLogger] = {}

    def get_logger(
        self,
        service_name: str,
        correlation_id: str | None = None,
        tenant_id: str | None = None,
    ) -> StructuredLogger:
        """Get or create a logger for a service."""
        cache_key = f"{service_name}:{correlation_id}:{tenant_id}"

        if cache_key not in self._loggers:
            self._loggers[cache_key] = StructuredLogger(
                service_name=service_name,
                config=self.config,
                correlation_id=correlation_id,
                tenant_id=tenant_id,
            )

        return self._loggers[cache_key]

    def get_audit_logger(self, service_name: str) -> AuditLogger:
        """Get audit logger for a service."""
        return AuditLogger(service_name, self.config)

    def get_performance_logger(self, service_name: str) -> PerformanceLogger:
        """Get performance logger for a service."""
        cache_key = f"perf_{service_name}"

        if cache_key not in self._performance_loggers:
            base_logger = self.get_logger(service_name)
            self._performance_loggers[cache_key] = PerformanceLogger(base_logger)

        return self._performance_loggers[cache_key]

    def get_logger_with_context(self, service_name: str, context: LogContext) -> StructuredLogger:
        """Get logger with LogContext applied."""
        base_logger = self.get_logger(
            service_name, correlation_id=context.correlation_id, tenant_id=context.tenant_id
        )
        return base_logger.with_log_context(context)

    def configure_logging(self, log_config: dict[str, Any]) -> None:
        """Configure logging with custom configuration."""
        logging.config.dictConfig(log_config)

    def update_filters(
        self,
        log_filter: LogFilter | None = None,
        log_sampler: LogSampler | None = None,
        log_aggregator: LogAggregator | None = None,
    ) -> None:
        """Update logging filters and processors."""
        if log_filter:
            self.log_filter = log_filter
        if log_sampler:
            self.log_sampler = log_sampler
        if log_aggregator:
            self.log_aggregator = log_aggregator


# Factory functions
def create_logger(service_name: str, **kwargs) -> StructuredLogger:
    """Create a structured logger."""
    return StructuredLogger(service_name, **kwargs)


# ---------------------------------------------------------------------------
# Simple module-level helpers for tests and lightweight usage
# ---------------------------------------------------------------------------

_DEFAULT_LOGGING_MANAGER = None


def _get_default_manager() -> "LoggingManager":
    global _DEFAULT_LOGGING_MANAGER
    if _DEFAULT_LOGGING_MANAGER is None:
        _DEFAULT_LOGGING_MANAGER = LoggingManager()
    return _DEFAULT_LOGGING_MANAGER


def get_logger(service_name: str):  # noqa: D401 - simple wrapper
    """Get a logger using the default logging manager."""
    return _get_default_manager().get_logger(service_name)


def configure_logging(level: LogLevel = LogLevel.INFO) -> None:
    """Basic configuration wrapper for tests."""
    level_name = level.name if isinstance(level, LogLevel) else str(level)
    logging.basicConfig(level=getattr(logging, level_name, logging.INFO))


def create_audit_logger(service_name: str, **kwargs) -> AuditLogger:
    """Create an audit logger."""
    return AuditLogger(service_name, **kwargs)


def create_logging_manager(**kwargs) -> LoggingManager:
    """Create a logging manager."""
    return LoggingManager(**kwargs)


def create_log_context(**kwargs) -> LogContext:
    """Create a log context."""
    return LogContext(**kwargs)


def create_performance_logger(logger: StructuredLogger) -> PerformanceLogger:
    """Create a performance logger."""
    return PerformanceLogger(logger)


def create_log_filter(**kwargs) -> LogFilter:
    """Create a log filter."""
    return LogFilter(**kwargs)


def create_log_sampler(**kwargs) -> LogSampler:
    """Create a log sampler."""
    return LogSampler(**kwargs)


def create_log_aggregator(**kwargs) -> LogAggregator:
    """Create a log aggregator."""
    return LogAggregator(**kwargs)


# Stub functions for architectural validation
def init_structured_logging(config=None) -> None:
    """Initialize structured logging system. Stub implementation."""

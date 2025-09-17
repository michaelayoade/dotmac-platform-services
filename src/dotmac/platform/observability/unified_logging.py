"""
Unified logging configuration for DotMac Platform Services.

This module provides a centralized, consistent logging setup that:
- Integrates with OpenTelemetry for distributed tracing
- Uses structured logging with contextual information
- Supports multiple output formats (JSON, console, OTEL)
- Provides performance and audit logging
- Ensures consistency across all platform modules
"""

import logging
import sys
from contextvars import ContextVar
from typing import Any, Dict, Optional
from functools import wraps
import time
import json

import structlog
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource

# Context variables for request-scoped data
correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
tenant_id_var: ContextVar[Optional[str]] = ContextVar("tenant_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


class PlatformLogger:
    """
    Unified logger for DotMac Platform Services.

    Provides structured logging with OpenTelemetry integration.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._configure()
            self.__class__._initialized = True

    def _configure(self):
        """Configure structured logging with OpenTelemetry."""

        # Configure structlog processors
        processors = [
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            self._add_context_processor,
            self._add_otel_context,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.LINENO,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                ]
            ),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
        ]

        # Add appropriate renderer based on environment
        if self._is_development():
            processors.append(structlog.dev.ConsoleRenderer(colors=True))
        else:
            processors.append(structlog.processors.JSONRenderer())

        # Configure structlog
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

    def _add_context_processor(self, logger, method_name, event_dict):
        """Add context variables to log entries."""

        # Add correlation ID
        correlation_id = correlation_id_var.get()
        if correlation_id:
            event_dict["correlation_id"] = correlation_id

        # Add tenant context
        tenant_id = tenant_id_var.get()
        if tenant_id:
            event_dict["tenant_id"] = tenant_id

        # Add user context
        user_id = user_id_var.get()
        if user_id:
            event_dict["user_id"] = user_id

        # Add service metadata
        event_dict["service"] = "dotmac-platform"

        return event_dict

    def _add_otel_context(self, logger, method_name, event_dict):
        """Add OpenTelemetry trace context to logs."""

        span = trace.get_current_span()
        if span and span.is_recording():
            span_context = span.get_span_context()
            event_dict["trace_id"] = format(span_context.trace_id, "032x")
            event_dict["span_id"] = format(span_context.span_id, "016x")
            event_dict["trace_flags"] = span_context.trace_flags

        return event_dict

    def _is_development(self) -> bool:
        """Check if running in development mode."""
        import os

        env = os.getenv("ENVIRONMENT", "development").lower()
        return env in ("development", "dev", "local")

    def get_logger(self, name: str) -> structlog.BoundLogger:
        """
        Get a logger instance for a module.

        Args:
            name: Logger name (typically __name__)

        Returns:
            Configured structlog logger
        """
        return structlog.get_logger(name)


def setup_otel_logging(
    service_name: str = "dotmac-platform",
    otlp_endpoint: Optional[str] = None,
    insecure: bool = True,
):
    """
    Setup OpenTelemetry logging export.

    Args:
        service_name: Service name for telemetry
        otlp_endpoint: OTLP endpoint (defaults to localhost:4317)
        insecure: Use insecure connection
    """

    if not otlp_endpoint:
        otlp_endpoint = "localhost:4317"

    # Create resource
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.namespace": "dotmac",
        }
    )

    # Create OTLP log exporter
    otlp_exporter = OTLPLogExporter(endpoint=otlp_endpoint, insecure=insecure)

    # Create logger provider
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_exporter))

    # Set global logger provider
    set_logger_provider(logger_provider)

    # Add OTLP handler to root logger
    handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
    logging.getLogger().addHandler(handler)


def log_performance(func):
    """
    Decorator to log function performance metrics.

    Logs execution time and success/failure status.
    """

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            logger.info(
                "function_executed",
                function=func.__name__,
                duration_ms=duration * 1000,
                success=True,
            )

            return result

        except Exception as e:
            duration = time.time() - start_time

            logger.error(
                "function_failed",
                function=func.__name__,
                duration_ms=duration * 1000,
                success=False,
                error=str(e),
                exc_info=True,
            )

            raise

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time

            logger.info(
                "function_executed",
                function=func.__name__,
                duration_ms=duration * 1000,
                success=True,
            )

            return result

        except Exception as e:
            duration = time.time() - start_time

            logger.error(
                "function_failed",
                function=func.__name__,
                duration_ms=duration * 1000,
                success=False,
                error=str(e),
                exc_info=True,
            )

            raise

    # Return appropriate wrapper based on function type
    import asyncio

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


def audit_log(
    action: str, resource: str, outcome: str = "success", details: Optional[Dict[str, Any]] = None
):
    """
    Log an audit event.

    Args:
        action: Action performed (e.g., "user.login", "secret.access")
        resource: Resource affected
        outcome: Operation outcome ("success", "failure", "denied")
        details: Additional audit details
    """
    logger = get_logger("audit")

    audit_event = {
        "audit": True,
        "action": action,
        "resource": resource,
        "outcome": outcome,
        "timestamp": time.time(),
        "user_id": user_id_var.get(),
        "tenant_id": tenant_id_var.get(),
        "correlation_id": correlation_id_var.get(),
    }

    if details:
        audit_event["details"] = details

    # Log at appropriate level based on outcome
    if outcome == "failure":
        logger.error("audit_event", **audit_event)
    elif outcome == "denied":
        logger.warning("audit_event", **audit_event)
    else:
        logger.info("audit_event", **audit_event)


# Global logger instance
_platform_logger = PlatformLogger()


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a logger for a module.

    This is the primary function that all modules should use.

    Example:
        logger = get_logger(__name__)
        logger.info("Service started", port=8000)

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger with context
    """
    return _platform_logger.get_logger(name)


def set_context(
    correlation_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
):
    """
    Set logging context for the current request/operation.

    Args:
        correlation_id: Request correlation ID
        tenant_id: Tenant identifier
        user_id: User identifier
    """
    if correlation_id:
        correlation_id_var.set(correlation_id)
    if tenant_id:
        tenant_id_var.set(tenant_id)
    if user_id:
        user_id_var.set(user_id)


def clear_context():
    """Clear all context variables."""
    correlation_id_var.set(None)
    tenant_id_var.set(None)
    user_id_var.set(None)


# Initialize logging on import
if __name__ != "__main__":
    # Setup basic configuration
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)

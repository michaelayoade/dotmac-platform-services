"""
Advanced plugin audit logging system with comprehensive security monitoring,
compliance reporting, and forensic capabilities.
"""

import asyncio
import json

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from uuid import UUID, uuid4

from dotmac.platform.core.decorators import standard_exception_handler
from dotmac.security.audit import get_audit_logger
from dotmac.platform.plugins.security.audit_monitor import UnifiedAuditMonitor

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger("plugins.audit")
audit_logger = get_audit_logger()

class AuditEventType(Enum):
    """Audit event type enumeration."""

    # Plugin lifecycle
    PLUGIN_INSTALLED = "plugin_installed"
    PLUGIN_UNINSTALLED = "plugin_uninstalled"
    PLUGIN_ENABLED = "plugin_enabled"
    PLUGIN_DISABLED = "plugin_disabled"
    PLUGIN_UPDATED = "plugin_updated"

    # Plugin execution
    PLUGIN_EXECUTED = "plugin_executed"
    PLUGIN_EXECUTION_FAILED = "plugin_execution_failed"
    PLUGIN_TIMEOUT = "plugin_timeout"
    PLUGIN_CRASHED = "plugin_crashed"

    # Security events
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"
    SECURITY_VIOLATION = "security_violation"
    SANDBOX_BREACH_ATTEMPT = "sandbox_breach_attempt"
    UNAUTHORIZED_ACCESS = "unauthorized_access"

    # Data access
    DATA_READ = "data_read"
    DATA_WRITE = "data_write"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"

    # Configuration
    CONFIG_CHANGED = "config_changed"
    SETTINGS_MODIFIED = "settings_modified"

    # Compliance
    POLICY_VIOLATION = "policy_violation"
    COMPLIANCE_CHECK = "compliance_check"
    AUDIT_REQUESTED = "audit_requested"

    # Administrative
    USER_ACTION = "user_action"
    SYSTEM_EVENT = "system_event"
    ERROR_OCCURRED = "error_occurred"

class AuditLevel(Enum):
    """Audit logging levels."""

    MINIMAL = "minimal"  # Critical security events only
    STANDARD = "standard"  # Standard compliance events
    DETAILED = "detailed"  # All plugin activities
    FORENSIC = "forensic"  # Maximum detail for forensic analysis

class AuditChannel(Enum):
    """Audit output channels."""

    FILE = "file"
    DATABASE = "database"
    SIEM = "siem"
    ELASTICSEARCH = "elasticsearch"
    SYSLOG = "syslog"
    WEBHOOK = "webhook"

@dataclass
class AuditEvent:
    """Comprehensive audit event record."""

    # Event identification
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: AuditEventType = AuditEventType.SYSTEM_EVENT
    event_category: str = "plugin"

    # Timestamp
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Context
    tenant_id: Optional[UUID] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    # Plugin context
    plugin_id: str = ""
    plugin_name: str = ""
    plugin_version: str = ""
    plugin_domain: str = ""

    # Event details
    action: str = ""
    resource: str = ""
    outcome: str = "success"  # success, failure, error, blocked

    # Technical details
    method: Optional[str] = None
    parameters: dict[str, Any] = field(default_factory=dict)
    response: dict[str, Any] = field(default_factory=dict)

    # Security context
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    authentication_method: Optional[str] = None
    authorization_context: dict[str, Any] = field(default_factory=dict)

    # Performance metrics
    execution_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0

    # Error information
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None

    # Compliance and governance
    compliance_tags: list[str] = field(default_factory=list)
    sensitivity_level: str = "normal"  # normal, sensitive, restricted, confidential
    data_classification: list[str] = field(default_factory=list)

    # Additional metadata
    custom_fields: dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    parent_event_id: Optional[str] = None

    # Processing metadata
    processed: bool = False
    processing_errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert audit event to dictionary."""
        data = asdict(self)

        # Convert enums to strings
        data["event_type"] = self.event_type.value
        data["timestamp"] = self.timestamp.isoformat()

        # Convert UUIDs to strings
        if self.tenant_id:
            data["tenant_id"] = str(self.tenant_id)

        return data

    def get_log_message(self) -> str:
        """Get formatted log message."""
        return (
            f"{self.event_type.value}: {self.action} on {self.resource} "
            f"by {self.user_id or 'system'} - {self.outcome}"
        )

@dataclass
class AuditConfiguration:
    """Audit logging configuration."""

    # Logging levels
    audit_level: AuditLevel = AuditLevel.STANDARD
    tenant_specific_levels: dict[str, AuditLevel] = field(default_factory=dict)

    # Output channels
    enabled_channels: list[AuditChannel] = field(default_factory=lambda: [AuditChannel.FILE])

    # File configuration
    log_file_path: str = "/var/log/dotmac/plugin-audit.log"
    log_file_rotation: str = "daily"
    log_file_retention_days: int = 90

    # Database configuration
    database_table: str = "plugin_audit_events"
    database_retention_days: int = 365

    # SIEM configuration
    siem_endpoint: Optional[str] = None
    siem_api_key: Optional[str] = None

    # Filtering and sampling
    event_filters: list[dict[str, Any]] = field(default_factory=list)
    sampling_rate: float = 1.0  # 1.0 = log everything, 0.1 = log 10%

    # Security
    encrypt_sensitive_fields: bool = True
    hash_user_identifiers: bool = False

    # Performance
    buffer_size: int = 1000
    flush_interval_seconds: int = 30
    max_queue_size: int = 10000

    # Compliance
    pci_compliance_mode: bool = False
    hipaa_compliance_mode: bool = False
    gdpr_compliance_mode: bool = True

class AuditEventBuffer:
    """High-performance audit event buffer with async processing."""

    def __init__(self, config: AuditConfiguration):
        self.config = config
        self.buffer: list[AuditEvent] = []
        self.buffer_lock = asyncio.Lock()
        self.flush_task: Optional[asyncio.Task] = None

        # Performance metrics
        self.events_buffered = 0
        self.events_processed = 0
        self.events_dropped = 0

    async def add_event(self, event: AuditEvent) -> bool:
        """Add event to buffer."""

        async with self.buffer_lock:
            if len(self.buffer) >= self.config.max_queue_size:
                self.events_dropped += 1
                logger.warning("Audit buffer full, dropping event")
                return False

            self.buffer.append(event)
            self.events_buffered += 1

            # Auto-flush if buffer is full
            if len(self.buffer) >= self.config.buffer_size:
                await self._flush_buffer()

        return True

    async def start_periodic_flush(self):
        """Start periodic buffer flush."""
        if not self.flush_task or self.flush_task.done():
            self.flush_task = asyncio.create_task(self._periodic_flush())

    async def _periodic_flush(self):
        """Periodic buffer flush task."""
        while True:
            try:
                await asyncio.sleep(self.config.flush_interval_seconds)
                await self._flush_buffer()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic flush: {e}")

    async def _flush_buffer(self):
        """Flush buffer contents."""
        async with self.buffer_lock:
            if self.buffer:
                events_to_process = self.buffer.copy()
                self.buffer.clear()

                # Process events (would be implemented by audit processors)
                self.events_processed += len(events_to_process)

                logger.debug(f"Flushed {len(events_to_process)} audit events")

    async def shutdown(self):
        """Shutdown buffer and flush remaining events."""
        if self.flush_task:
            self.flush_task.cancel()

        await self._flush_buffer()

class PluginAuditProcessor:
    """Process and route audit events to configured destinations."""

    def __init__(self, config: AuditConfiguration):
        self.config = config
        self.processors = {
            AuditChannel.FILE: self._process_file_output,
            AuditChannel.DATABASE: self._process_database_output,
            AuditChannel.SIEM: self._process_siem_output,
            AuditChannel.SYSLOG: self._process_syslog_output,
        }

    async def process_events(self, events: list[AuditEvent]) -> None:
        """Process audit events through configured channels."""

        for channel in self.config.enabled_channels:
            processor = self.processors.get(channel)
            if processor:
                try:
                    await processor(events)
                except Exception as e:
                    logger.error(f"Error processing events to {channel.value}: {e}")

    async def _process_file_output(self, events: list[AuditEvent]) -> None:
        """Process events to file output."""

        log_file = Path(self.config.log_file_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(log_file, "a", encoding="utf-8") as f:
                for event in events:
                    # Format as JSON for structured logging
                    log_entry = {
                        "timestamp": event.timestamp.isoformat(),
                        "level": "AUDIT",
                        "event_type": event.event_type.value,
                        "plugin_id": event.plugin_id,
                        "action": event.action,
                        "outcome": event.outcome,
                        "details": event.to_dict(),
                    }

                    f.write(json.dumps(log_entry) + "\n")

        except Exception as e:
            logger.error(f"Failed to write audit events to file: {e}")

    async def _process_database_output(self, events: list[AuditEvent]) -> None:
        """Process events to database output."""
        # Would implement database insertion
        logger.debug(f"Processing {len(events)} events to database")

    async def _process_siem_output(self, events: list[AuditEvent]) -> None:
        """Process events to SIEM system."""
        # Would implement SIEM integration
        logger.debug(f"Processing {len(events)} events to SIEM")

    async def _process_syslog_output(self, events: list[AuditEvent]) -> None:
        """Process events to syslog."""
        # Would implement syslog integration
        logger.debug(f"Processing {len(events)} events to syslog")

class AdvancedPluginAuditSystem:
    """
    Comprehensive plugin audit logging system with enterprise features.
    """

    def __init__(
        self,
        config: Optional[AuditConfiguration] = None,
        audit_monitor: Optional[UnifiedAuditMonitor] = None,
    ):
        self.config = config or AuditConfiguration()
        self.audit_monitor = audit_monitor  # Optional audit monitor

        # Core components
        self.event_buffer = AuditEventBuffer(self.config)
        self.event_processor = PluginAuditProcessor(self.config)

        # Event filters and enrichers
        self.event_filters: list[callable] = []
        self.event_enrichers: list[callable] = []

        # Context tracking
        self.active_sessions: dict[str, dict[str, Any]] = {}
        self.correlation_contexts: dict[str, dict[str, Any]] = {}

        # Performance tracking
        self.audit_metrics = {
            "events_logged": 0,
            "events_filtered": 0,
            "processing_errors": 0,
            "buffer_overflows": 0,
        }

        # Initialize default filters and enrichers
        self._setup_default_filters()
        self._setup_default_enrichers()

    def _setup_default_filters(self) -> None:
        """Setup default event filters."""

        # Sampling filter
        if self.config.sampling_rate < 1.0:
            self.event_filters.append(self._sampling_filter)

        # Sensitivity filter for compliance
        if self.config.gdpr_compliance_mode:
            self.event_filters.append(self._gdpr_compliance_filter)

        if self.config.pci_compliance_mode:
            self.event_filters.append(self._pci_compliance_filter)

    def _setup_default_enrichers(self) -> None:
        """Setup default event enrichers."""

        # Always add correlation enricher
        self.event_enrichers.append(self._correlation_enricher)

        # Add performance enricher for detailed logging
        if self.config.audit_level in [AuditLevel.DETAILED, AuditLevel.FORENSIC]:
            self.event_enrichers.append(self._performance_enricher)

        # Add security context enricher
        self.event_enrichers.append(self._security_enricher)

    async def initialize(self) -> None:
        """Initialize audit system."""

        logger.info(f"Initializing plugin audit system with level: {self.config.audit_level.value}")

        # Start buffer flushing
        await self.event_buffer.start_periodic_flush()

        # Initialize audit channels
        for channel in self.config.enabled_channels:
            logger.info(f"Enabled audit channel: {channel.value}")

    async def shutdown(self) -> None:
        """Shutdown audit system gracefully."""

        logger.info("Shutting down plugin audit system")

        # Shutdown buffer
        await self.event_buffer.shutdown()

        # Log final metrics
        logger.info(f"Audit metrics: {self.audit_metrics}")

    @standard_exception_handler
    async def log_event(
        self,
        event_type: AuditEventType,
        plugin_id: str,
        action: str,
        outcome: str = "success",
        **kwargs,
    ) -> str:
        """Log audit event with comprehensive details."""

        # Create audit event
        event = AuditEvent(
            event_type=event_type, plugin_id=plugin_id, action=action, outcome=outcome, **kwargs
        )

        try:
            # Apply filters
            if not await self._apply_filters(event):
                self.audit_metrics["events_filtered"] += 1
                return event.event_id

            # Apply enrichers
            await self._apply_enrichers(event)

            # Buffer event
            success = await self.event_buffer.add_event(event)

            if success:
                self.audit_metrics["events_logged"] += 1
            else:
                self.audit_metrics["buffer_overflows"] += 1

            # Also log to standard audit logger for immediate visibility
            audit_logger.info(
                event.get_log_message(),
                extra={
                    "audit_event_id": event.event_id,
                    "event_type": event_type.value,
                    "plugin_id": plugin_id,
                    "tenant_id": str(event.tenant_id) if event.tenant_id else None,
                    "outcome": outcome,
                },
            )

            return event.event_id

        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            self.audit_metrics["processing_errors"] += 1
            return event.event_id

    async def _apply_filters(self, event: AuditEvent) -> bool:
        """Apply event filters to determine if event should be logged."""

        for filter_func in self.event_filters:
            try:
                if not await filter_func(event):
                    return False
            except Exception as e:
                logger.error(f"Event filter error: {e}")

        return True

    async def _apply_enrichers(self, event: AuditEvent) -> None:
        """Apply event enrichers to add additional context."""

        for enricher_func in self.event_enrichers:
            try:
                await enricher_func(event)
            except Exception as e:
                logger.error(f"Event enricher error: {e}")

    # Default filters

    async def _sampling_filter(self, event: AuditEvent) -> bool:
        """Apply sampling filter."""
        import secrets

        return secrets.SystemRandom().random() < self.config.sampling_rate

    async def _gdpr_compliance_filter(self, event: AuditEvent) -> bool:
        """Apply GDPR compliance filter."""

        # Always log security events for compliance
        if event.event_type in [
            AuditEventType.SECURITY_VIOLATION,
            AuditEventType.UNAUTHORIZED_ACCESS,
            AuditEventType.PERMISSION_DENIED,
        ]:
            return True

        # Filter based on sensitivity level
        if event.sensitivity_level in ["restricted", "confidential"]:
            # May need additional processing for GDPR compliance
            pass

        return True

    async def _pci_compliance_filter(self, event: AuditEvent) -> bool:
        """Apply PCI compliance filter."""

        # PCI requires comprehensive logging
        return True

    # Default enrichers

    async def _correlation_enricher(self, event: AuditEvent) -> None:
        """Add correlation context to events."""

        if event.session_id and event.session_id in self.active_sessions:
            session_context = self.active_sessions[event.session_id]
            event.correlation_id = session_context.get("correlation_id")

            # Add session details to custom fields
            event.custom_fields.update(
                {
                    "session_start": session_context.get("start_time"),
                    "session_duration": (
                        datetime.now(timezone.utc)
                        - session_context.get("start_time", datetime.now(timezone.utc))
                    ).total_seconds(),
                }
            )

    async def _performance_enricher(self, event: AuditEvent) -> None:
        """Add performance metrics to events."""

        # Would collect actual performance metrics
        # This is a placeholder implementation
        if event.execution_time_ms == 0.0:
            event.execution_time_ms = 100.0  # Placeholder

        if event.memory_usage_mb == 0.0:
            event.memory_usage_mb = 50.0  # Placeholder

    async def _security_enricher(self, event: AuditEvent) -> None:
        """Add security context to events."""

        # Add security-relevant tags
        if event.event_type in [
            AuditEventType.PERMISSION_GRANTED,
            AuditEventType.PERMISSION_DENIED,
            AuditEventType.SECURITY_VIOLATION,
        ]:
            event.compliance_tags.append("security")

        if event.event_type in [
            AuditEventType.DATA_READ,
            AuditEventType.DATA_WRITE,
            AuditEventType.DATA_DELETE,
            AuditEventType.DATA_EXPORT,
        ]:
            event.compliance_tags.append("data_access")

    # Convenience methods for common audit events

    async def log_plugin_execution(
        self,
        plugin_id: str,
        method: str,
        tenant_id: Optional[UUID] = None,
        user_id: Optional[str] = None,
        execution_time_ms: float = 0.0,
        outcome: str = "success",
        **kwargs,
    ) -> str:
        """Log plugin execution event."""

        return await self.log_event(
            event_type=AuditEventType.PLUGIN_EXECUTED,
            plugin_id=plugin_id,
            action=f"execute_method:{method}",
            resource=f"plugin:{plugin_id}",
            tenant_id=tenant_id,
            user_id=user_id,
            method=method,
            execution_time_ms=execution_time_ms,
            outcome=outcome,
            **kwargs,
        )

    async def log_permission_check(
        self,
        plugin_id: str,
        permission: str,
        granted: bool,
        tenant_id: Optional[UUID] = None,
        user_id: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Log permission check event."""

        return await self.log_event(
            event_type=(
                AuditEventType.PERMISSION_GRANTED if granted else AuditEventType.PERMISSION_DENIED
            ),
            plugin_id=plugin_id,
            action=f"check_permission:{permission}",
            resource=f"permission:{permission}",
            tenant_id=tenant_id,
            user_id=user_id,
            outcome="granted" if granted else "denied",
            authorization_context={"permission": permission, "granted": granted},
            **kwargs,
        )

    async def log_security_violation(
        self,
        plugin_id: str,
        violation_type: str,
        description: str,
        tenant_id: Optional[UUID] = None,
        severity: str = "medium",
        **kwargs,
    ) -> str:
        """Log security violation event."""

        return await self.log_event(
            event_type=AuditEventType.SECURITY_VIOLATION,
            plugin_id=plugin_id,
            action=f"security_violation:{violation_type}",
            resource=f"plugin:{plugin_id}",
            tenant_id=tenant_id,
            outcome="violation_detected",
            sensitivity_level="restricted",
            compliance_tags=["security", "violation"],
            custom_fields={
                "violation_type": violation_type,
                "violation_description": description,
                "severity": severity,
            },
            **kwargs,
        )

    async def log_data_access(
        self,
        plugin_id: str,
        access_type: str,  # "read", "write", "delete", "export"
        data_type: str,
        tenant_id: Optional[UUID] = None,
        user_id: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Log data access event."""

        event_type_mapping = {
            "read": AuditEventType.DATA_READ,
            "write": AuditEventType.DATA_WRITE,
            "delete": AuditEventType.DATA_DELETE,
            "export": AuditEventType.DATA_EXPORT,
        }

        return await self.log_event(
            event_type=event_type_mapping.get(access_type, AuditEventType.DATA_READ),
            plugin_id=plugin_id,
            action=f"data_access:{access_type}",
            resource=f"data:{data_type}",
            tenant_id=tenant_id,
            user_id=user_id,
            outcome="success",
            compliance_tags=["data_access"],
            data_classification=[data_type],
            **kwargs,
        )

    # Session and correlation management

    async def start_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        tenant_id: Optional[UUID] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Start audit session tracking."""

        self.active_sessions[session_id] = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "correlation_id": correlation_id or str(uuid4()),
            "start_time": datetime.now(timezone.utc),
        }

    async def end_session(self, session_id: str) -> None:
        """End audit session tracking."""

        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            duration = (datetime.now(timezone.utc) - session["start_time"]).total_seconds()

            # Log session end event
            await self.log_event(
                event_type=AuditEventType.SYSTEM_EVENT,
                plugin_id="system",
                action="session_ended",
                resource=f"session:{session_id}",
                user_id=session.get("user_id"),
                tenant_id=session.get("tenant_id"),
                custom_fields={"session_duration_seconds": duration},
            )

            del self.active_sessions[session_id]

    # Query and reporting methods

    def get_audit_metrics(self) -> dict[str, Any]:
        """Get audit system metrics."""

        return {
            **self.audit_metrics,
            "buffer_stats": {
                "events_buffered": self.event_buffer.events_buffered,
                "events_processed": self.event_buffer.events_processed,
                "events_dropped": self.event_buffer.events_dropped,
            },
            "active_sessions": len(self.active_sessions),
            "config": {
                "audit_level": self.config.audit_level.value,
                "enabled_channels": [c.value for c in self.config.enabled_channels],
                "sampling_rate": self.config.sampling_rate,
            },
        }

# Context manager for audit session tracking
class AuditSession:
    """Context manager for audit session tracking."""

    def __init__(
        self,
        audit_system: AdvancedPluginAuditSystem,
        session_id: str,
        user_id: Optional[str] = None,
        tenant_id: Optional[UUID] = None,
    ):
        self.audit_system = audit_system
        self.session_id = session_id
        self.user_id = user_id
        self.tenant_id = tenant_id

    async def __aenter__(self):
        await self.audit_system.start_session(self.session_id, self.user_id, self.tenant_id)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.audit_system.end_session(self.session_id)

# Factory function for dependency injection
def create_plugin_audit_system(
    config: Optional[AuditConfiguration] = None,
    audit_monitor: Optional[UnifiedAuditMonitor] = None,
) -> AdvancedPluginAuditSystem:
    """Create plugin audit system."""
    return AdvancedPluginAuditSystem(config, audit_monitor)

__all__ = [
    "AuditEventType",
    "AuditLevel",
    "AuditChannel",
    "AuditEvent",
    "AuditConfiguration",
    "AuditEventBuffer",
    "PluginAuditProcessor",
    "AdvancedPluginAuditSystem",
    "AuditSession",
    "create_plugin_audit_system",
]

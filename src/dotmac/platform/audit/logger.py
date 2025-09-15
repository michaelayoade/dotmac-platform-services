"""
Main audit logging service for security events.
"""

from typing import Any, Optional

import structlog

from .models import (
    AuditActor,
    AuditContext,
    AuditEvent,
    AuditEventType,
    AuditOutcome,
    AuditResource,
    AuditSeverity,
)
from .stores import AuditStore, InMemoryAuditStore

logger = structlog.get_logger(__name__)


class AuditLogger:
    """Main audit logging service for security events."""

    def __init__(
        self,
        store: Optional[AuditStore] = None,
        service_name: str = "dotmac-security",
        tenant_id: Optional[str] = None,
    ):
        self.store = store or InMemoryAuditStore()
        self.service_name = service_name
        self.tenant_id = tenant_id
        self._default_context = AuditContext(
            service_name=service_name,
            environment="production",  # Should be configurable
        )

    async def log_event(
        self,
        event_type: AuditEventType,
        message: str,
        actor: Optional[AuditActor] = None,
        resource: Optional[AuditResource] = None,
        context: Optional[AuditContext] = None,
        severity: AuditSeverity = AuditSeverity.LOW,
        outcome: AuditOutcome = AuditOutcome.SUCCESS,
        **kwargs,
    ) -> AuditEvent:
        """Log an audit event."""

        # Merge context with defaults
        effective_context = self._merge_context(context)

        # Create audit event
        event = AuditEvent(
            event_type=event_type,
            message=message,
            actor=actor,
            resource=resource,
            context=effective_context,
            severity=severity,
            outcome=outcome,
            **kwargs,
        )

        # Store the event
        try:
            await self.store.store_event(event)
            logger.debug("Audit event logged", event_id=event.event_id)
        except Exception as e:
            logger.error("Failed to store audit event", error=str(e))

        return event

    async def log_auth_event(
        self,
        event_type: AuditEventType,
        actor_id: str,
        outcome: AuditOutcome,
        message: str,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        **kwargs,
    ) -> AuditEvent:
        """Log authentication-related audit event."""

        actor = AuditActor(actor_id=actor_id, actor_type="user", tenant_id=self.tenant_id)

        context = AuditContext(client_ip=client_ip, user_agent=user_agent, service_name=self.service_name)

        severity = AuditSeverity.HIGH if outcome == AuditOutcome.FAILURE else AuditSeverity.MEDIUM

        return await self.log_event(
            event_type=event_type,
            message=message,
            actor=actor,
            context=context,
            severity=severity,
            outcome=outcome,
            **kwargs,
        )

    async def log_data_access(
        self,
        operation: str,
        resource_type: str,
        resource_id: str,
        actor_id: str,
        outcome: AuditOutcome = AuditOutcome.SUCCESS,
        before_state: Optional[dict] = None,
        after_state: Optional[dict] = None,
        **kwargs,
    ) -> AuditEvent:
        """Log data access audit event."""

        # Map operation to event type
        event_type_map = {
            "create": AuditEventType.DATA_CREATE,
            "read": AuditEventType.DATA_READ,
            "update": AuditEventType.DATA_UPDATE,
            "delete": AuditEventType.DATA_DELETE,
        }
        event_type = event_type_map.get(operation.lower(), AuditEventType.DATA_READ)

        actor = AuditActor(actor_id=actor_id, actor_type="user", tenant_id=self.tenant_id)

        resource = AuditResource(resource_id=resource_id, resource_type=resource_type)

        message = f"{operation.title()} {resource_type} {resource_id}"
        severity = AuditSeverity.HIGH if operation.lower() == "delete" else AuditSeverity.MEDIUM

        return await self.log_event(
            event_type=event_type,
            message=message,
            actor=actor,
            resource=resource,
            severity=severity,
            outcome=outcome,
            before_state=before_state,
            after_state=after_state,
            **kwargs,
        )

    async def log_security_event(
        self,
        event_type: AuditEventType,
        message: str,
        actor_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.HIGH,
        **kwargs,
    ) -> AuditEvent:
        """Log security-specific audit event."""

        actor = None
        if actor_id:
            actor = AuditActor(
                actor_id=actor_id,
                actor_type="user",
                tenant_id=self.tenant_id,
            )

        resource = None
        if resource_id:
            resource = AuditResource(
                resource_id=resource_id,
                resource_type="security",
            )

        return await self.log_event(
            event_type=event_type,
            message=message,
            actor=actor,
            resource=resource,
            severity=severity,
            **kwargs,
        )

    async def log_system_event(
        self,
        event_type: AuditEventType,
        message: str,
        severity: AuditSeverity = AuditSeverity.MEDIUM,
        **kwargs,
    ) -> AuditEvent:
        """Log system-level audit event."""

        actor = AuditActor(
            actor_id="system",
            actor_type="system",
            service_account=self.service_name,
            tenant_id=self.tenant_id,
        )

        return await self.log_event(
            event_type=event_type,
            message=message,
            actor=actor,
            severity=severity,
            **kwargs,
        )

    async def query_events(self, **kwargs) -> list[AuditEvent]:
        """Query audit events from the store."""
        return await self.store.query_events(**kwargs)

    async def get_event_stats(
        self, start_time: Optional[float] = None, end_time: Optional[float] = None
    ) -> dict[str, Any]:
        """Get audit event statistics."""
        events = await self.query_events(start_time=start_time, end_time=end_time, limit=10000)

        stats = {
            "total_events": len(events),
            "events_by_type": {},
            "events_by_severity": {},
            "events_by_outcome": {},
            "unique_actors": set(),
            "unique_resources": set(),
        }

        for event in events:
            # Count by type
            event_type = event.event_type.value
            stats["events_by_type"][event_type] = stats["events_by_type"].get(event_type, 0) + 1

            # Count by severity
            severity = event.severity.value
            stats["events_by_severity"][severity] = stats["events_by_severity"].get(severity, 0) + 1

            # Count by outcome
            outcome = event.outcome.value
            stats["events_by_outcome"][outcome] = stats["events_by_outcome"].get(outcome, 0) + 1

            # Track unique actors and resources
            if event.actor:
                stats["unique_actors"].add(event.actor.actor_id)
            if event.resource:
                stats["unique_resources"].add(f"{event.resource.resource_type}:{event.resource.resource_id}")

        # Convert sets to counts
        stats["unique_actors"] = len(stats["unique_actors"])
        stats["unique_resources"] = len(stats["unique_resources"])

        return stats

    def _merge_context(self, context: Optional[AuditContext]) -> AuditContext:
        """Merge provided context with default context."""
        if not context:
            return self._default_context

        # Create merged context
        merged = AuditContext(**self._default_context.__dict__)
        for key, value in context.__dict__.items():
            if value is not None:
                setattr(merged, key, value)

        return merged


# Global audit logger instance
_global_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    if _global_audit_logger is None:
        raise RuntimeError(
            "Audit logger not initialized. Call init_audit_logger() first or provide an audit logger instance."
        )
    return _global_audit_logger


def init_audit_logger(
    service_name: str,
    tenant_id: Optional[str] = None,
    store: Optional[AuditStore] = None,
) -> AuditLogger:
    """Initialize the global audit logger."""
    global _global_audit_logger
    _global_audit_logger = AuditLogger(store=store, service_name=service_name, tenant_id=tenant_id)
    return _global_audit_logger

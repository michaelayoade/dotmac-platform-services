"""Security audit system for DotMac Framework."""

from .decorators import log_security_event
from .logger import AuditLogger, get_audit_logger, record_audit_event
from .middleware import AuditMiddleware
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

__all__ = [
    "AuditEvent",
    "AuditActor",
    "AuditResource",
    "AuditContext",
    "AuditEventType",
    "AuditSeverity",
    "AuditOutcome",
    "AuditLogger",
    "AuditStore",
    "InMemoryAuditStore",
    "AuditMiddleware",
    "log_security_event",
    "get_audit_logger",
    "record_audit_event",
]

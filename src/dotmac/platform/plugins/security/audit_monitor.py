"""Lightweight unified audit monitor implementation for plugin security modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any, Optional

from dotmac.platform.observability.logging import create_audit_logger


@dataclass
class AuditEvent:
    """Represents an audit event captured by the monitor."""

    action: str
    resource: str
    actor: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class UnifiedAuditMonitor:
    """Minimal audit monitor used by plugin security components.

    The original implementation lived in ``dotmac_shared``. This replacement keeps
    the public surface area expected by the security modules while delegating
    storage to the structured audit logger exposed by the observability package.
    """

    def __init__(self, service_name: str = "dotmac-plugin-security") -> None:
        self.service_name = service_name
        self._logger = create_audit_logger(service_name)

    def record_event(self, event: AuditEvent | dict[str, Any]) -> None:
        """Record an audit event using the structured audit logger."""
        payload = event.__dict__ if isinstance(event, AuditEvent) else dict(event)
        payload.setdefault("service", self.service_name)
        payload.setdefault("timestamp", datetime.now(UTC).isoformat())
        action = payload.get("action", "unknown")
        self._logger.log_event(action=action, **payload)

    def capture_exception(self, exc: Exception, context: Optional[dict[str, Any]] = None) -> None:
        """Capture an exception within the audit trail."""
        payload = {
            "service": self.service_name,
            "exception": type(exc).__name__,
            "message": str(exc),
            "context": context or {},
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self._logger.log_event(action="exception", **payload)

    def flush(self) -> None:
        """Compatibility no-op to mirror original interface."""
        # Structured logger handles batching internally; nothing to flush.
        return None


__all__ = ["AuditEvent", "UnifiedAuditMonitor"]

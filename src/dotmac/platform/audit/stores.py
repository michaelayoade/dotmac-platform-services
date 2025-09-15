"""
Audit event storage backends.
"""

from abc import ABC, abstractmethod
from typing import Optional

import structlog

from .models import AuditEvent, AuditEventType

logger = structlog.get_logger(__name__)


class AuditStore(ABC):
    """Abstract base class for audit event storage backends."""

    @abstractmethod
    async def store_event(self, event: AuditEvent) -> bool:
        """Store a single audit event."""
        pass

    @abstractmethod
    async def store_events(self, events: list[AuditEvent]) -> int:
        """Store multiple audit events. Returns number of events successfully stored."""
        pass

    @abstractmethod
    async def query_events(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        event_types: Optional[list[AuditEventType]] = None,
        actor_ids: Optional[list[str]] = None,
        resource_types: Optional[list[str]] = None,
        tenant_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEvent]:
        """Query stored audit events."""
        pass


class InMemoryAuditStore(AuditStore):
    """In-memory audit store for testing and development."""

    def __init__(self, max_events: int = 10000):
        self.events: list[AuditEvent] = []
        self.max_events = max_events

    async def store_event(self, event: AuditEvent) -> bool:
        """Store audit event in memory."""
        try:
            self.events.append(event)
            # Maintain maximum events limit
            if len(self.events) > self.max_events:
                self.events = self.events[-self.max_events :]
            return True
        except Exception as e:
            logger.error("Failed to store audit event", error=str(e))
            return False

    async def store_events(self, events: list[AuditEvent]) -> int:
        """Store multiple audit events in memory."""
        stored = 0
        for event in events:
            if await self.store_event(event):
                stored += 1
        return stored

    async def query_events(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        event_types: Optional[list[AuditEventType]] = None,
        actor_ids: Optional[list[str]] = None,
        resource_types: Optional[list[str]] = None,
        tenant_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEvent]:
        """Query audit events from memory."""
        filtered_events = self.events

        # Apply filters
        if start_time:
            filtered_events = [e for e in filtered_events if e.timestamp >= start_time]
        if end_time:
            filtered_events = [e for e in filtered_events if e.timestamp <= end_time]
        if event_types:
            filtered_events = [e for e in filtered_events if e.event_type in event_types]
        if actor_ids and any(e.actor for e in filtered_events):
            filtered_events = [e for e in filtered_events if e.actor and e.actor.actor_id in actor_ids]
        if resource_types and any(e.resource for e in filtered_events):
            filtered_events = [e for e in filtered_events if e.resource and e.resource.resource_type in resource_types]
        if tenant_id and any(e.actor for e in filtered_events):
            filtered_events = [e for e in filtered_events if e.actor and e.actor.tenant_id == tenant_id]

        # Sort by timestamp (newest first)
        filtered_events.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply pagination
        return filtered_events[offset : offset + limit]

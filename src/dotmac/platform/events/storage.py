"""Event persistence storage."""

import json

import structlog

from dotmac.platform.core.caching import get_redis
from dotmac.platform.events.models import Event, EventStatus

logger = structlog.get_logger(__name__)


class EventStorage:
    """
    Event storage for persistence and querying.

    Supports both Redis and in-memory storage backends.
    """

    def __init__(self, use_redis: bool = True):
        """
        Initialize event storage.

        Args:
            use_redis: Whether to use Redis for storage
        """
        self._redis = get_redis() if use_redis else None
        self._memory_store: dict[str, Event] = {}

        logger.debug("EventStorage initialized", backend="redis" if self._redis else "memory")

    async def save_event(self, event: Event) -> None:
        """
        Save event to storage.

        Args:
            event: Event to save
        """
        if self._redis:
            try:
                key = f"event:{event.event_id}"
                value = json.dumps(event.to_dict())
                self._redis.setex(key, 86400 * 7, value)  # 7 days TTL

                # Add to indices
                self._add_to_index(event)
            except Exception as e:
                logger.warning("Failed to save event to Redis", error=str(e))
                self._memory_store[event.event_id] = event
        else:
            self._memory_store[event.event_id] = event

    def _add_to_index(self, event: Event) -> None:
        """Add event to type and status indices."""
        if not self._redis:
            return

        try:
            # Index by type
            type_key = f"events:type:{event.event_type}"
            self._redis.zadd(type_key, {event.event_id: event.created_at.timestamp()})
            self._redis.expire(type_key, 86400 * 7)

            # Index by status
            status_key = f"events:status:{event.status.value}"
            self._redis.zadd(status_key, {event.event_id: event.created_at.timestamp()})
            self._redis.expire(status_key, 86400 * 7)

            # Index by tenant if available
            if event.metadata.tenant_id:
                tenant_key = f"events:tenant:{event.metadata.tenant_id}"
                self._redis.zadd(tenant_key, {event.event_id: event.created_at.timestamp()})
                self._redis.expire(tenant_key, 86400 * 7)
        except Exception as e:
            logger.warning("Failed to update event indices", error=str(e))

    async def get_event(self, event_id: str) -> Event | None:
        """
        Get event by ID.

        Args:
            event_id: Event ID

        Returns:
            Event or None if not found
        """
        if self._redis:
            try:
                key = f"event:{event_id}"
                value = self._redis.get(key)
                if value:
                    data = json.loads(value)
                    return Event.from_dict(data)
            except Exception as e:
                logger.warning("Failed to get event from Redis", error=str(e))

        return self._memory_store.get(event_id)

    async def update_event(self, event: Event) -> None:
        """
        Update event in storage.

        Args:
            event: Event to update
        """
        await self.save_event(event)

    async def query_events(
        self,
        event_type: str | None = None,
        status: EventStatus | None = None,
        tenant_id: str | None = None,
        limit: int = 100,
    ) -> list[Event]:
        """
        Query events from storage.

        Args:
            event_type: Filter by event type
            status: Filter by status
            tenant_id: Filter by tenant
            limit: Maximum events to return

        Returns:
            List of matching events
        """
        if self._redis:
            return await self._query_redis(event_type, status, tenant_id, limit)
        else:
            return await self._query_memory(event_type, status, tenant_id, limit)

    def _determine_index_key(
        self,
        event_type: str | None,
        status: EventStatus | None,
        tenant_id: str | None,
    ) -> str:
        """Determine which Redis index to use based on filters."""
        if event_type:
            return f"events:type:{event_type}"
        elif status:
            return f"events:status:{status.value}"
        elif tenant_id:
            return f"events:tenant:{tenant_id}"
        else:
            # Get all events (not recommended for production)
            return "events:type:*"

    def _decode_event_id(self, event_id: bytes | str) -> str:
        """Decode event ID from bytes to string if needed."""
        return event_id.decode() if isinstance(event_id, bytes) else event_id

    def _event_matches_filters(
        self,
        event: Event,
        event_type: str | None,
        status: EventStatus | None,
        tenant_id: str | None,
    ) -> bool:
        """Check if event matches all specified filters."""
        if event_type and event.event_type != event_type:
            return False
        if status and event.status != status:
            return False
        if tenant_id and event.metadata.tenant_id != tenant_id:
            return False
        return True

    async def _query_redis(
        self,
        event_type: str | None,
        status: EventStatus | None,
        tenant_id: str | None,
        limit: int,
    ) -> list[Event]:
        """Query events from Redis."""
        if not self._redis:
            return []

        try:
            # Determine which index to use
            index_key = self._determine_index_key(event_type, status, tenant_id)

            # Get event IDs from index (newest first)
            event_ids = self._redis.zrevrange(index_key, 0, limit - 1)

            # Fetch events
            events = []
            for event_id in event_ids:
                decoded_id = self._decode_event_id(event_id)
                event = await self.get_event(decoded_id)

                if event and self._event_matches_filters(event, event_type, status, tenant_id):
                    events.append(event)

            return events[:limit]

        except Exception as e:
            logger.warning("Failed to query events from Redis", error=str(e))
            return []

    async def _query_memory(
        self,
        event_type: str | None,
        status: EventStatus | None,
        tenant_id: str | None,
        limit: int,
    ) -> list[Event]:
        """Query events from memory storage."""
        events = list(self._memory_store.values())

        # Apply filters
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if status:
            events = [e for e in events if e.status == status]
        if tenant_id:
            events = [e for e in events if e.metadata.tenant_id == tenant_id]

        # Sort by creation time (newest first)
        events.sort(key=lambda e: e.created_at, reverse=True)

        return events[:limit]

    async def get_dead_letter_events(self, limit: int = 100) -> list[Event]:
        """
        Get events in dead letter queue.

        Args:
            limit: Maximum events to return

        Returns:
            List of dead letter events
        """
        return await self.query_events(status=EventStatus.DEAD_LETTER, limit=limit)

    async def clear_old_events(self, days: int = 30) -> int:
        """
        Clear events older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            Number of events deleted
        """
        # Implementation depends on backend
        # For Redis, TTL handles this automatically
        # For memory, we'd need to implement manual cleanup
        return 0

"""Dead Letter Queue abstractions and utilities."""


import asyncio
import time
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from .bus import EventBus
from .message import Event
from dotmac.platform.observability.unified_logging import get_logger

__all__ = [
    "DLQError",
    "DLQEntry",
    "DLQ",
    "SimpleDLQ",
    "DLQConsumer",
    "DLQHandler",
    "create_dlq_consumer",
]

logger = get_logger(__name__)

class DLQError(Exception):
    """Base exception for DLQ operations."""
    pass

@dataclass
class DLQEntry:
    """Represents an entry in the Dead Letter Queue."""

    original_event: Event
    original_topic: str
    error: str
    error_type: str
    retry_count: int
    first_failure_time: datetime
    last_failure_time: datetime
    dlq_topic: str
    dlq_timestamp: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_event(cls, dlq_event: Event) -> "DLQEntry":
        """Create DLQEntry from a DLQ event."""
        headers = dlq_event.headers or {}

        # Extract DLQ metadata from headers
        original_topic = headers.get("x-original-topic", dlq_event.topic)
        retry_count = int(headers.get("x-retry-count", "0"))
        error = headers.get("x-error", "Unknown error")
        error_type = headers.get("x-error-type", "Exception")
        dlq_timestamp_str = headers.get("x-dlq-timestamp", str(int(time.time())))

        # Parse timestamps
        dlq_timestamp = datetime.fromtimestamp(float(dlq_timestamp_str))
        first_failure_str = headers.get("x-first-failure-time")
        last_failure_str = headers.get("x-last-failure-time")

        if first_failure_str:
            first_failure_time = datetime.fromtimestamp(float(first_failure_str))
        else:
            first_failure_time = dlq_timestamp

        if last_failure_str:
            last_failure_time = datetime.fromtimestamp(float(last_failure_str))
        else:
            last_failure_time = dlq_timestamp

        # Reconstruct original event (remove DLQ headers)
        original_headers = {k: v for k, v in headers.items() if not k.startswith("x-")}
        original_event = Event(
            topic=original_topic,
            payload=dlq_event.payload,
            key=dlq_event.key,
            headers=original_headers if original_headers else None,
            tenant_id=dlq_event.tenant_id,
            metadata=dlq_event.metadata,
        )

        return cls(
            original_event=original_event,
            original_topic=original_topic,
            error=error,
            error_type=error_type,
            retry_count=retry_count,
            first_failure_time=first_failure_time,
            last_failure_time=last_failure_time,
            dlq_topic=dlq_event.topic,
            dlq_timestamp=dlq_timestamp,
        )

    def to_event(self) -> Event:
        """Convert DLQEntry back to an event for reprocessing."""
        headers = (self.original_event.headers or {}).copy()
        headers.update(
            {
                "x-dlq-reprocessing": "true",
                "x-original-retry-count": str(self.retry_count),
                "x-dlq-reprocess-timestamp": str(int(time.time())),
            }
        )

        return Event(
            topic=self.original_topic,
            payload=self.original_event.payload,
            key=self.original_event.key,
            headers=headers,
            tenant_id=self.original_event.tenant_id,
            metadata=self.original_event.metadata,
        )

class DLQ(ABC):
    """Abstract base class for Dead Letter Queue implementations."""

    @abstractmethod
    async def send_to_dlq(
        self,
        event: Event,
        error: Exception,
        retry_count: int,
        dlq_topic: Optional[str] = None,
    ) -> None:
        """
        Send an event to the Dead Letter Queue.

        Args:
            event: Original event that failed
            error: Exception that caused the failure
            retry_count: Number of retries attempted
            dlq_topic: DLQ topic name (uses default if None)
        """
        ...

    @abstractmethod
    async def list_dlq_entries(
        self,
        dlq_topic: str,
        limit: Optional[int] = None,
        since: Optional[datetime] = None,
    ) -> list[DLQEntry]:
        """
        List entries in a DLQ topic.

        Args:
            dlq_topic: DLQ topic to list from
            limit: Maximum number of entries to return
            since: Only return entries newer than this timestamp

        Returns:
            List of DLQ entries
        """
        ...

    @abstractmethod
    async def reprocess_event(self, dlq_entry: DLQEntry) -> None:
        """
        Reprocess a DLQ entry by publishing back to original topic.

        Args:
            dlq_entry: DLQ entry to reprocess
        """
        ...

    async def reprocess_all(
        self,
        dlq_topic: str,
        filter_func: Optional[Callable[[DLQEntry], bool]] = None,
    ) -> int:
        """
        Reprocess all entries in a DLQ topic.

        Args:
            dlq_topic: DLQ topic to reprocess
            filter_func: Optional filter function

        Returns:
            Number of entries reprocessed
        """
        entries = await self.list_dlq_entries(dlq_topic)

        if filter_func:
            entries = [entry for entry in entries if filter_func(entry)]

        for entry in entries:
            await self.reprocess_event(entry)

        return len(entries)

class SimpleDLQ(DLQ):
    """
    Simple DLQ implementation using the event bus.

    This implementation simply publishes failed events to a DLQ topic
    with additional metadata headers.
    """

    def __init__(self, bus: EventBus, default_dlq_suffix: str = ".DLQ"):
        """
        Initialize simple DLQ.

        Args:
            bus: Event bus to use for DLQ operations
            default_dlq_suffix: Suffix to add to topic names for DLQ topics
        """
        self.bus = bus
        self.default_dlq_suffix = default_dlq_suffix

    async def send_to_dlq(
        self,
        event: Event,
        error: Exception,
        retry_count: int,
        dlq_topic: Optional[str] = None,
    ) -> None:
        """Send event to DLQ topic."""
        try:
            if dlq_topic is None:
                dlq_topic = f"{event.topic}{self.default_dlq_suffix}"

            # Create DLQ headers
            dlq_headers = (event.headers or {}).copy()
            current_time = str(int(time.time()))

            dlq_headers.update(
                {
                    "x-original-topic": event.topic,
                    "x-retry-count": str(retry_count),
                    "x-error": str(error),
                    "x-error-type": type(error).__name__,
                    "x-dlq-timestamp": current_time,
                    "x-first-failure-time": dlq_headers.get("x-first-failure-time", current_time),
                    "x-last-failure-time": current_time,
                }
            )

            # Create DLQ event
            dlq_event = Event(
                topic=dlq_topic,
                payload=event.payload,
                key=event.key,
                headers=dlq_headers,
                tenant_id=event.tenant_id,
                metadata=event.metadata,
            )

            # Publish to DLQ
            await self.bus.publish(dlq_event)

            logger.info(f"Sent event {event.id} to DLQ topic '{dlq_topic}'")

        except Exception as dlq_error:
            raise DLQError(f"Failed to send event to DLQ: {dlq_error}") from dlq_error

    async def list_dlq_entries(
        self,
        dlq_topic: str,
        limit: Optional[int] = None,
        since: Optional[datetime] = None,
    ) -> list[DLQEntry]:
        """
        List DLQ entries by consuming from the DLQ topic.

        This implementation creates a temporary consumer to read messages
        from the DLQ topic without processing them.

        Args:
            dlq_topic: The DLQ topic to list entries from
            limit: Maximum number of entries to return (default: 100)
            since: Only return entries after this timestamp

        Returns:
            List of DLQ entries
        """
        entries = []
        limit = limit or 100
        read_timeout = 2.0  # seconds to wait for messages

        # Track message collection
        messages_collected = 0
        start_time = time.time()

        async def collect_dlq_messages(event: Event):
            """Collect DLQ messages without processing."""
            nonlocal messages_collected

            try:
                # Check timestamp filter
                if since:
                    event_time = event.metadata.get('timestamp')
                    if event_time:
                        event_dt = datetime.fromisoformat(event_time) if isinstance(event_time, str) else event_time
                        if event_dt < since:
                            return

                # Parse DLQ entry from event
                dlq_entry = DLQEntry.from_event(event)
                entries.append(dlq_entry)
                messages_collected += 1

                # Stop if we've reached the limit
                if messages_collected >= limit:
                    raise StopAsyncIteration("Limit reached")

            except Exception as e:
                if "Limit reached" not in str(e):
                    logger.warning(f"Error parsing DLQ entry: {e}")

        # Create temporary subscription
        subscription_id = f"dlq-list-{time.time()}"

        try:
            # Subscribe to DLQ topic
            await self.bus.subscribe(dlq_topic, collect_dlq_messages, subscription_id)

            # Wait for messages or timeout
            while (time.time() - start_time) < read_timeout and messages_collected < limit:
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Error listing DLQ entries: {e}")
        finally:
            # Clean up subscription
            try:
                await self.bus.unsubscribe(dlq_topic, subscription_id)
            except:
                pass

        # Sort by timestamp (newest first)
        entries.sort(key=lambda x: x.dlq_timestamp, reverse=True)

        logger.info(f"Listed {len(entries)} DLQ entries from topic '{dlq_topic}'")
        return entries

    async def reprocess_event(self, dlq_entry: DLQEntry) -> None:
        """Reprocess a DLQ entry."""
        try:
            # Convert back to original event
            reprocessed_event = dlq_entry.to_event()

            # Publish back to original topic
            await self.bus.publish(reprocessed_event)

            logger.info(
                f"Reprocessed DLQ entry {dlq_entry.original_event.id} "
                f"back to topic '{dlq_entry.original_topic}'"
            )

        except Exception as reprocess_error:
            raise DLQError(f"Failed to reprocess DLQ entry: {reprocess_error}") from reprocess_error

# Type alias for DLQ handlers
DLQHandler = Callable[[DLQEntry], Awaitable[None]]

class DLQConsumer:
    """
    Consumer for processing DLQ entries.

    This can be used to monitor DLQ topics and handle failed events,
    for example by sending alerts or logging to external systems.
    """

    def __init__(
        self,
        bus: EventBus,
        dlq: DLQ,
        handler: DLQHandler,
        auto_reprocess: bool = False,
        reprocess_filter: Optional[Callable[[DLQEntry], bool]] = None,
    ):
        """
        Initialize DLQ consumer.

        Args:
            bus: Event bus to consume from
            dlq: DLQ implementation
            handler: Handler for DLQ entries
            auto_reprocess: If True, automatically reprocess entries after handling
            reprocess_filter: Filter function for auto-reprocessing
        """
        self.bus = bus
        self.dlq = dlq
        self.handler = handler
        self.auto_reprocess = auto_reprocess
        self.reprocess_filter = reprocess_filter

    async def start(self, dlq_topic: str, group: str = "dlq-processor") -> None:
        """Start consuming from a DLQ topic."""

        async def _dlq_event_handler(event: Event) -> None:
            """Handle DLQ events."""
            try:
                # Convert event to DLQ entry
                dlq_entry = DLQEntry.from_event(event)

                # Call user handler
                await self.handler(dlq_entry)

                # Auto-reprocess if enabled
                if self.auto_reprocess:
                    should_reprocess = True
                    if self.reprocess_filter:
                        should_reprocess = self.reprocess_filter(dlq_entry)

                    if should_reprocess:
                        await self.dlq.reprocess_event(dlq_entry)
                        logger.info(f"Auto-reprocessed DLQ entry {dlq_entry.original_event.id}")

            except Exception as e:
                logger.error(f"Error processing DLQ event: {e}", exc_info=True)

        # Subscribe to DLQ topic
        await self.bus.subscribe(dlq_topic, _dlq_event_handler, group=group)

async def create_dlq_consumer(
    bus: EventBus,
    dlq_topic: str,
    handler: DLQHandler,
    *,
    dlq: Optional[DLQ] = None,
    group: str = "dlq-processor",
    auto_reprocess: bool = False,
    reprocess_filter: Optional[Callable[[DLQEntry], bool]] = None,
) -> DLQConsumer:
    """
    Create and start a DLQ consumer.

    Args:
        bus: Event bus
        dlq_topic: DLQ topic to consume from
        handler: DLQ entry handler
        dlq: DLQ implementation (creates SimpleDLQ if None)
        group: Consumer group name
        auto_reprocess: Enable auto-reprocessing
        reprocess_filter: Filter for auto-reprocessing

    Returns:
        Started DLQ consumer
    """
    if dlq is None:
        dlq = SimpleDLQ(bus)

    consumer = DLQConsumer(
        bus=bus,
        dlq=dlq,
        handler=handler,
        auto_reprocess=auto_reprocess,
        reprocess_filter=reprocess_filter,
    )

    await consumer.start(dlq_topic, group)
    return consumer

# Common DLQ handlers

async def log_dlq_entry(dlq_entry: DLQEntry) -> None:
    """Log DLQ entry details."""
    logger.warning(
        f"DLQ Entry: topic={dlq_entry.original_topic}, "
        f"error={dlq_entry.error_type}: {dlq_entry.error}, "
        f"retries={dlq_entry.retry_count}, "
        f"event_id={dlq_entry.original_event.id}"
    )

async def alert_on_dlq_entry(dlq_entry: DLQEntry) -> None:
    """Send alert for DLQ entry (placeholder implementation)."""
    # In a real implementation, this would send to an alerting system
    logger.critical(
        f"ALERT: Event failed and sent to DLQ - "
        f"Topic: {dlq_entry.original_topic}, "
        f"Error: {dlq_entry.error}, "
        f"EventID: {dlq_entry.original_event.id}"
    )

def create_reprocess_after_delay_filter(delay_minutes: int = 30) -> Callable[[DLQEntry], bool]:
    """Create a filter that reprocesses entries after a delay."""

    def filter_func(dlq_entry: DLQEntry) -> bool:
        age = datetime.utcnow() - dlq_entry.dlq_timestamp
        return age >= timedelta(minutes=delay_minutes)

    return filter_func

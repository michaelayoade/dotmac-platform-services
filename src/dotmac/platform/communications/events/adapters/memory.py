"""In-memory event bus adapter for development and testing."""

import asyncio

from collections import defaultdict
from typing import Any, Optional

from ..bus import ConsumeError, EventHandler, PublishError
from ..message import Event
from .base import AdapterConfig, AdapterMetadata, BaseAdapter
from dotmac.platform.observability.unified_logging import get_logger

__all__ = [
    "MemoryEventBus",
    "MemoryConfig",
    "create_memory_bus",
]

logger = get_logger(__name__)

class MemoryConfig(AdapterConfig):
    """Configuration for memory event bus."""

    def __init__(
        self,
        *,
        max_queue_size: int = 1000,
        enable_persistence: bool = False,
        **kwargs: Any,
    ):
        """
        Initialize memory config.

        Args:
            max_queue_size: Maximum size of topic queues
            enable_persistence: If True, keep event history (for testing)
            **kwargs: Base adapter config options
        """
        super().__init__(**kwargs)
        self.max_queue_size = max_queue_size
        self.enable_persistence = enable_persistence

class TopicSubscription:
    """Represents a subscription to a topic."""

    def __init__(
        self,
        topic: str,
        handler: EventHandler,
        group: str,
        concurrency: int = 1,
    ):
        self.topic = topic
        self.handler = handler
        self.group = group
        self.concurrency = concurrency
        self.task: Optional[asyncio.Task[None]] = None
        self._stop_event = asyncio.Event()

    async def stop(self) -> None:
        """Stop the subscription."""
        self._stop_event.set()
        if self.task:
            await self.task

class MemoryEventBus(BaseAdapter):
    """
    In-memory event bus implementation.

    This adapter stores events in memory queues and is suitable for
    development, testing, and single-process applications. Events
    are lost when the process terminates.
    """

    def __init__(self, config: Optional[MemoryConfig] = None):
        """
        Initialize memory event bus.

        Args:
            config: Memory-specific configuration
        """
        super().__init__(config)
        self.config: MemoryConfig = config or MemoryConfig()

        # Topic queues - each topic has its own queue
        self._topic_queues: dict[str, asyncio.Queue[Event]] = {}

        # Consumer groups - track which events have been consumed by which groups
        self._consumer_groups: dict[str, dict[str, set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )

        # Active subscriptions
        self._subscriptions: list[TopicSubscription] = []

        # Event history (if persistence enabled)
        self._event_history: list[Event] = []

        # Stats
        self._published_count = 0
        self._consumed_count = 0

        self._lock = asyncio.Lock()

    @property
    def metadata(self) -> AdapterMetadata:
        """Get adapter metadata."""
        return AdapterMetadata(
            name="memory",
            version="1.0.0",
            description="In-memory event bus for development and testing",
            supported_features={
                "publish",
                "subscribe",
                "consumer_groups",
                "request_reply",
                "persistence_optional",
            },
        )

    async def publish(
        self,
        event: Event,
        *,
        partition_key: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        """
        Publish an event to the memory bus.

        Args:
            event: Event to publish
            partition_key: Ignored in memory adapter
            headers: Additional headers to add to event
        """
        self._ensure_not_closed()

        try:
            # Add headers if provided
            if headers:
                event = event.with_headers(**headers)

            # Get or create queue for topic
            async with self._lock:
                if event.topic not in self._topic_queues:
                    self._topic_queues[event.topic] = asyncio.Queue(
                        maxsize=self.config.max_queue_size
                    )

                queue = self._topic_queues[event.topic]

            # Put event in queue (non-blocking)
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                raise PublishError(
                    f"Topic '{event.topic}' queue is full (max_size={self.config.max_queue_size})",
                    event=event,
                )

            # Update stats and history
            self._published_count += 1
            if self.config.enable_persistence:
                self._event_history.append(event)

            self._logger.debug(f"Published event to topic '{event.topic}': {event.id}")

        except Exception as e:
            if isinstance(e, PublishError):
                raise
            raise PublishError(f"Failed to publish event: {e}", event=event, cause=e) from e

    async def subscribe(
        self,
        topic: str,
        handler: EventHandler,
        *,
        group: str = "default",
        concurrency: int = 1,
        auto_offset_reset: str = "latest",
        **kwargs: Any,
    ) -> None:
        """
        Subscribe to events on a topic.

        Args:
            topic: Topic to subscribe to
            handler: Event handler function
            group: Consumer group name
            concurrency: Number of concurrent handlers
            auto_offset_reset: Ignored in memory adapter (always latest)
            **kwargs: Additional options (ignored)
        """
        self._ensure_not_closed()

        try:
            subscription = TopicSubscription(topic, handler, group, concurrency)
            self._subscriptions.append(subscription)

            # Start consumer task
            subscription.task = asyncio.create_task(self._consume_loop(subscription))

            self._logger.info(
                f"Subscribed to topic '{topic}' with group '{group}' "
                f"and concurrency {concurrency}"
            )

        except Exception as e:
            raise ConsumeError(
                f"Failed to subscribe to topic '{topic}': {e}", topic=topic, cause=e
            ) from e

    async def request(
        self,
        subject: str,
        payload: dict[str, Any],
        timeout: float = 5.0,
    ) -> dict[str, Any]:
        """
        Send a request and wait for response (simplified implementation).

        Note: This is a basic implementation. In production, you'd want
        proper correlation ID handling and reply-to topics.
        """
        self._ensure_not_closed()

        # Create request event with correlation ID
        import uuid

        correlation_id = str(uuid.uuid4())

        request_event = Event(
            topic=subject,
            payload=payload,
            headers={"correlation_id": correlation_id, "reply_required": "true"},
        )

        # Create response future
        response_future: asyncio.Future[dict[str, Any]] = asyncio.Future()

        # Temporary response handler
        async def response_handler(event: Event) -> None:
            if event.headers and event.headers.get("correlation_id") == correlation_id:
                if not response_future.done():
                    response_future.set_result(event.payload)

        # Subscribe to response topic temporarily
        response_topic = f"{subject}.reply"
        await self.subscribe(response_topic, response_handler, group=f"temp_{correlation_id}")

        try:
            # Publish request
            await self.publish(request_event)

            # Wait for response
            response = await asyncio.wait_for(response_future, timeout=timeout)
            return response

        except asyncio.TimeoutError:
            from dotmac.platform.communications.events.bus import TimeoutError

            raise TimeoutError(f"No response received within {timeout}s")

    async def _consume_loop(self, subscription: TopicSubscription) -> None:
        """Main consumer loop for a subscription."""
        topic = subscription.topic
        group = subscription.group

        try:
            # Ensure topic queue exists
            async with self._lock:
                if topic not in self._topic_queues:
                    self._topic_queues[topic] = asyncio.Queue(maxsize=self.config.max_queue_size)
                queue = self._topic_queues[topic]

            # Create semaphore for concurrency control
            semaphore = asyncio.Semaphore(subscription.concurrency)

            self._logger.info(f"Started consumer loop for topic '{topic}', group '{group}'")

            while not subscription._stop_event.is_set():
                try:
                    # Get event from queue (with timeout to check stop event)
                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=1.0)
                    except asyncio.TimeoutError:
                        continue

                    # Check if this consumer group has already processed this event
                    event_id = str(event.id)
                    if event_id in self._consumer_groups[topic][group]:
                        # Event already processed by this group, skip
                        queue.task_done()
                        continue

                    # Mark event as consumed by this group
                    self._consumer_groups[topic][group].add(event_id)

                    # Process event with concurrency control
                    async with semaphore:
                        await self._handle_event_safely(subscription, event)

                    queue.task_done()
                    self._consumed_count += 1

                except Exception as e:
                    self._logger.error(f"Error in consumer loop for '{topic}': {e}")
                    await asyncio.sleep(1.0)  # Brief pause on error

        except Exception as e:
            self._logger.error(f"Consumer loop failed for topic '{topic}': {e}")

        self._logger.info(f"Consumer loop stopped for topic '{topic}', group '{group}'")

    async def _handle_event_safely(self, subscription: TopicSubscription, event: Event) -> None:
        """Handle an event with error catching."""
        try:
            await subscription.handler(event)
            self._logger.debug(f"Handled event {event.id} for topic '{subscription.topic}'")
        except Exception as e:
            self._logger.error(
                f"Handler error for event {event.id} on topic '{subscription.topic}': {e}",
                exc_info=True,
            )
            # In a real implementation, this would trigger retry logic

    async def _close_impl(self) -> None:
        """Close memory event bus."""
        # Stop all subscriptions
        for subscription in self._subscriptions:
            await subscription.stop()

        self._subscriptions.clear()

        # Clear queues
        self._topic_queues.clear()
        self._consumer_groups.clear()

        if self.config.enable_persistence:
            self._event_history.clear()

    # Utility methods for testing

    def get_queue_size(self, topic: str) -> int:
        """Get current queue size for a topic (testing utility)."""
        if topic in self._topic_queues:
            return self._topic_queues[topic].qsize()
        return 0

    def get_event_history(self) -> list[Event]:
        """Get event history (only if persistence enabled)."""
        return self._event_history.copy()

    def get_stats(self) -> dict[str, Any]:
        """Get bus statistics."""
        return {
            "published_count": self._published_count,
            "consumed_count": self._consumed_count,
            "active_topics": len(self._topic_queues),
            "active_subscriptions": len(self._subscriptions),
            "total_queue_size": sum(q.qsize() for q in self._topic_queues.values()),
        }

def create_memory_bus(config: Optional[MemoryConfig] = None) -> MemoryEventBus:
    """
    Factory function to create a memory event bus.

    Args:
        config: Optional memory configuration

    Returns:
        Configured memory event bus
    """
    return MemoryEventBus(config)

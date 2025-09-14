"""Event bus for pub/sub messaging."""

import asyncio
import json
import logging
import time
import uuid
from typing import Any, Callable

from pydantic import BaseModel, Field

from .config import EventBusConfig

logger = logging.getLogger(__name__)


class Event(BaseModel):
    """Event model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = Field(..., description="Event type/name")
    data: dict[str, Any] = Field(default_factory=dict, description="Event data")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Event metadata")
    timestamp: float = Field(default_factory=time.time, description="Event timestamp")
    source: str | None = Field(None, description="Event source identifier")
    correlation_id: str | None = Field(None, description="Correlation ID for tracing")

    def to_json(self) -> str:
        """Serialize event to JSON."""
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> "Event":
        """Deserialize event from JSON."""
        return cls.model_validate_json(json_str)


EventHandler = Callable[[Event], None]
AsyncEventHandler = Callable[[Event], Any]


class EventBus:
    """
    Generic event bus with memory and Redis backends.

    Provides pub/sub messaging for decoupled communication.
    """

    def __init__(self, config: EventBusConfig):
        """
        Initialize event bus.

        Args:
            config: Event bus configuration
        """
        self.config = config
        self._handlers: dict[str, list[EventHandler | AsyncEventHandler]] = {}
        self._running = False
        self._redis_client = None
        self._consumer_task = None

        # Memory backend queue
        self._memory_queue: asyncio.Queue[Event] = asyncio.Queue()

    async def start(self):
        """Start the event bus."""
        self._running = True

        if self.config.backend == "redis" and self.config.redis_url:
            await self._init_redis()

        # Start consumer
        self._consumer_task = asyncio.create_task(self._consume_events())
        logger.info("Event bus started with %s backend", self.config.backend)

    async def stop(self):
        """Stop the event bus."""
        self._running = False

        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass

        if self._redis_client:
            await self._redis_client.close()

        logger.info("Event bus stopped")

    async def _init_redis(self):
        """Initialize Redis connection."""
        try:
            import redis.asyncio as redis

            self._redis_client = redis.from_url(self.config.redis_url)
            await self._redis_client.ping()
            logger.info("Connected to Redis for event bus")
        except Exception as e:
            logger.error("Failed to connect to Redis: %s", e)
            # Fall back to memory backend
            self.config.backend = "memory"

    def subscribe(
        self,
        event_type: str,
        handler: EventHandler | AsyncEventHandler,
    ):
        """
        Subscribe to events of a specific type.

        Args:
            event_type: Event type to subscribe to
            handler: Function to handle events
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug("Subscribed handler to event type: %s", event_type)

    def unsubscribe(
        self,
        event_type: str,
        handler: EventHandler | AsyncEventHandler,
    ):
        """
        Unsubscribe from events.

        Args:
            event_type: Event type
            handler: Handler to remove
        """
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                logger.debug("Unsubscribed handler from event type: %s", event_type)
            except ValueError:
                pass

    async def publish(self, event: Event):
        """
        Publish an event.

        Args:
            event: Event to publish
        """
        logger.debug("Publishing event: type=%s, id=%s", event.type, event.id)

        if self.config.backend == "redis" and self._redis_client:
            await self._publish_redis(event)
        else:
            await self._publish_memory(event)

    async def _publish_memory(self, event: Event):
        """Publish event to memory queue."""
        await self._memory_queue.put(event)

    async def _publish_redis(self, event: Event):
        """Publish event to Redis stream."""
        try:
            await self._redis_client.xadd(
                f"{self.config.redis_stream_key}:{event.type}",
                {"event": event.to_json()},
                maxlen=10000,  # Keep last 10k events
            )
        except Exception as e:
            logger.error("Failed to publish to Redis: %s", e)
            # Fall back to memory
            await self._publish_memory(event)

    async def _consume_events(self):
        """Consume events from the backend."""
        while self._running:
            try:
                if self.config.backend == "redis" and self._redis_client:
                    await self._consume_redis()
                else:
                    await self._consume_memory()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error consuming events: %s", e)
                await asyncio.sleep(1)

    async def _consume_memory(self):
        """Consume events from memory queue."""
        try:
            event = await asyncio.wait_for(
                self._memory_queue.get(),
                timeout=1.0,
            )
            await self._handle_event(event)
        except asyncio.TimeoutError:
            pass

    async def _consume_redis(self):
        """Consume events from Redis streams."""
        try:
            # Subscribe to all event types we have handlers for
            streams = {
                f"{self.config.redis_stream_key}:{event_type}": "$"
                for event_type in self._handlers.keys()
            }

            if not streams:
                await asyncio.sleep(1)
                return

            # Read from streams
            messages = await self._redis_client.xread(
                streams,
                count=10,
                block=1000,  # Block for 1 second
            )

            for stream_name, stream_messages in messages:
                for message_id, data in stream_messages:
                    event_json = data.get(b"event", b"{}").decode()
                    event = Event.from_json(event_json)
                    await self._handle_event(event)

                    # Acknowledge message
                    await self._redis_client.xdel(stream_name, message_id)

        except Exception as e:
            logger.error("Error consuming from Redis: %s", e)
            await asyncio.sleep(1)

    async def _handle_event(self, event: Event):
        """Handle an event by calling registered handlers."""
        handlers = self._handlers.get(event.type, [])

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    # Run sync handler in executor
                    await asyncio.get_event_loop().run_in_executor(
                        None, handler, event
                    )
            except Exception as e:
                logger.error(
                    "Error in event handler for %s: %s",
                    event.type,
                    e,
                )

    def emit(self, event_type: str, data: dict[str, Any] | None = None, **kwargs):
        """
        Synchronous helper to emit an event.

        Args:
            event_type: Event type
            data: Event data
            **kwargs: Additional event fields
        """
        event = Event(
            type=event_type,
            data=data or {},
            **kwargs,
        )

        # Schedule publish in the event loop
        asyncio.create_task(self.publish(event))

    async def wait_for_event(
        self,
        event_type: str,
        timeout: float | None = None,
        filter_func: Callable[[Event], bool] | None = None,
    ) -> Event | None:
        """
        Wait for a specific event.

        Args:
            event_type: Event type to wait for
            timeout: Timeout in seconds
            filter_func: Optional filter function

        Returns:
            Event if received, None if timeout
        """
        received_event = None
        event_received = asyncio.Event()

        def handler(event: Event):
            nonlocal received_event
            if filter_func is None or filter_func(event):
                received_event = event
                event_received.set()

        self.subscribe(event_type, handler)

        try:
            await asyncio.wait_for(event_received.wait(), timeout)
            return received_event
        except asyncio.TimeoutError:
            return None
        finally:
            self.unsubscribe(event_type, handler)
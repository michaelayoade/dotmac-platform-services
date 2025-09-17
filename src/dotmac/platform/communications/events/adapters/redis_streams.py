"""Redis Streams event bus adapter."""

import asyncio

from typing import Any, Optional
from urllib.parse import urlparse

from ..bus import ConsumeError, EventHandler, NotSupportedError, PublishError
from ..codecs.json_codec import JsonCodec
from ..message import Event, MessageCodec
from .base import AdapterConfig, AdapterMetadata, BaseAdapter
from dotmac.platform.observability.unified_logging import get_logger

__all__ = [
    "RedisEventBus",
    "RedisStreamsEventBus",  # Alias for backward compatibility
    "RedisConfig",
    "create_redis_bus",
]

logger = get_logger(__name__)

# Optional Redis import
try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None  # type: ignore

class RedisConfig(AdapterConfig):
    """Configuration for Redis Streams event bus."""

    def __init__(
        self,
        *,
        url: Optional[str] = None,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        ssl: bool = False,
        max_stream_length: Optional[int] = 10000,
        consumer_timeout: float = 1.0,
        block_time: int = 1000,  # milliseconds
        prefetch_count: int = 10,
        codec: Optional[MessageCodec] = None,
        **kwargs: Any,
    ):
        """
        Initialize Redis configuration.

        Args:
            url: Redis URL (redis://host:port/db)
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            ssl: Use SSL connection
            max_stream_length: Maximum stream length (None for unlimited)
            consumer_timeout: Consumer read timeout
            block_time: XREAD block time in milliseconds
            prefetch_count: Number of messages to prefetch
            codec: Message codec for serialization
            **kwargs: Base adapter config options
        """
        super().__init__(**kwargs)

        # Connection settings
        if url:
            parsed = urlparse(url)
            self.host = parsed.hostname or host
            self.port = parsed.port or port
            self.db = int(parsed.path.lstrip("/")) if parsed.path else db
            self.password = parsed.password or password
            self.ssl = url.startswith("rediss://")
        else:
            self.host = host
            self.port = port
            self.db = db
            self.password = password
            self.ssl = ssl

        # Stream settings
        self.max_stream_length = max_stream_length
        self.consumer_timeout = consumer_timeout
        self.block_time = block_time
        self.prefetch_count = prefetch_count

        # Codec
        self.codec = codec or JsonCodec.compact()

class ConsumerGroupInfo:
    """Information about a Redis consumer group."""

    def __init__(self, topic: str, group: str, handler: EventHandler, task: asyncio.Task[None]):
        self.topic = topic
        self.group = group
        self.handler = handler
        self.task = task
        self._stop_event = asyncio.Event()

    async def stop(self) -> None:
        """Stop the consumer group."""
        self._stop_event.set()
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

class RedisEventBus(BaseAdapter):
    """
    Redis Streams event bus implementation.

    Uses Redis Streams for reliable message delivery with consumer groups.
    Each topic becomes a Redis Stream, and consumer groups provide
    at-least-once delivery semantics.
    """

    def __init__(self, config: RedisConfig):
        """
        Initialize Redis event bus.

        Args:
            config: Redis-specific configuration
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "Redis support not available. Install with: pip install 'dotmac-events[redis]'"
            )

        super().__init__(config)
        self.config: RedisConfig = config

        # Redis connection
        self._redis: Optional[redis.Redis] = None

        # Active consumer groups
        self._consumer_groups: list[ConsumerGroupInfo] = []

        # Connection lock
        self._connection_lock = asyncio.Lock()

    @property
    def metadata(self) -> AdapterMetadata:
        """Get adapter metadata."""
        return AdapterMetadata(
            name="redis_streams",
            version="1.0.0",
            description="Redis Streams event bus with consumer groups",
            supported_features={
                "publish",
                "subscribe",
                "consumer_groups",
                "at_least_once_delivery",
                "persistence",
                "acknowledgments",
            },
        )

    async def _get_connection(self) -> redis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            async with self._connection_lock:
                if self._redis is None:
                    self._redis = redis.Redis(
                        host=self.config.host,
                        port=self.config.port,
                        db=self.config.db,
                        password=self.config.password,
                        ssl=self.config.ssl,
                        socket_connect_timeout=self.config.connection_timeout,
                        socket_timeout=self.config.operation_timeout,
                        retry_on_timeout=True,
                        max_connections=self.config.max_connections,
                        decode_responses=False,  # We handle bytes ourselves
                    )

                    # Test connection
                    try:
                        await self._redis.ping()
                        self._logger.info(
                            f"Connected to Redis at {self.config.host}:{self.config.port}"
                        )
                    except Exception as e:
                        await self._redis.close()
                        self._redis = None
                        raise ConsumeError(f"Failed to connect to Redis: {e}", cause=e) from e

        return self._redis

    async def publish(
        self,
        event: Event,
        *,
        partition_key: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        """
        Publish an event to a Redis Stream.

        Args:
            event: Event to publish
            partition_key: Ignored in Redis Streams (events are ordered)
            headers: Additional headers to add to event
        """
        self._ensure_not_closed()

        try:
            # Add headers if provided
            if headers:
                event = event.with_headers(**headers)

            # Serialize event
            event_data = self.config.codec.encode(event)

            # Create Redis stream entry
            fields = {
                "data": event_data,
                "content_type": self.config.codec.content_type,
            }

            # Add metadata as separate fields for easier querying
            if event.metadata:
                fields.update(event.metadata.to_headers())

            # Add event headers
            if event.headers:
                for key, value in event.headers.items():
                    fields[f"header_{key}"] = value

            # Get Redis connection
            redis_conn = await self._get_connection()

            # Add to stream
            message_id = await redis_conn.xadd(
                event.topic,
                fields,
                maxlen=self.config.max_stream_length,
                approximate=True if self.config.max_stream_length else False,
            )

            self._logger.debug(
                f"Published event to Redis stream '{event.topic}' with ID {message_id.decode()}: {event.id}"
            )

        except Exception as e:
            if isinstance(e, PublishError):
                raise
            raise PublishError(
                f"Failed to publish event to Redis: {e}", event=event, cause=e
            ) from e

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
        Subscribe to events on a Redis Stream.

        Args:
            topic: Stream name to subscribe to
            handler: Event handler function
            group: Consumer group name
            concurrency: Number of concurrent consumers
            auto_offset_reset: Where to start consuming ("earliest" or "latest")
            **kwargs: Additional options (ignored)
        """
        self._ensure_not_closed()

        try:
            redis_conn = await self._get_connection()

            # Create consumer group if it doesn't exist
            try:
                start_id = "0" if auto_offset_reset == "earliest" else "$"
                await redis_conn.xgroup_create(topic, group, id=start_id, mkstream=True)
                self._logger.info(f"Created consumer group '{group}' for stream '{topic}'")
            except redis.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    # BUSYGROUP means group already exists, which is fine
                    raise ConsumeError(
                        f"Failed to create consumer group: {e}", topic=topic, cause=e
                    ) from e

            # Start consumer tasks
            tasks = []
            for i in range(concurrency):
                consumer_name = f"{group}-consumer-{i}"
                task = asyncio.create_task(self._consume_loop(topic, group, consumer_name, handler))
                tasks.append(task)

            # Create consumer group info
            # For simplicity, we use the first task as the main task
            consumer_info = ConsumerGroupInfo(topic, group, handler, tasks[0])
            self._consumer_groups.append(consumer_info)

            self._logger.info(
                f"Subscribed to Redis stream '{topic}' with group '{group}' "
                f"and {concurrency} consumers"
            )

        except Exception as e:
            if isinstance(e, ConsumeError):
                raise
            raise ConsumeError(
                f"Failed to subscribe to stream '{topic}': {e}", topic=topic, cause=e
            ) from e

    async def request(
        self,
        subject: str,
        payload: dict[str, Any],
        timeout: float = 5.0,
    ) -> dict[str, Any]:
        """Redis Streams doesn't naturally support request-reply."""
        raise NotSupportedError("Request-reply pattern not supported by Redis Streams adapter")

    async def _consume_loop(
        self,
        topic: str,
        group: str,
        consumer_name: str,
        handler: EventHandler,
    ) -> None:
        """Main consumer loop for Redis Streams."""
        redis_conn = await self._get_connection()

        self._logger.info(f"Started Redis consumer '{consumer_name}' for stream '{topic}'")

        try:
            while not self.is_closed:
                try:
                    # Read from stream with consumer group
                    messages = await redis_conn.xreadgroup(
                        group,
                        consumer_name,
                        {topic: ">"},
                        count=self.config.prefetch_count,
                        block=self.config.block_time,
                    )

                    # Process messages
                    for stream_name, stream_messages in messages:
                        for message_id, fields in stream_messages:
                            try:
                                # Decode message
                                event = self._decode_redis_message(fields)

                                # Handle event
                                await handler(event)

                                # Acknowledge message
                                await redis_conn.xack(topic, group, message_id)

                                self._logger.debug(
                                    f"Processed and acknowledged message {message_id.decode()} "
                                    f"from stream '{topic}'"
                                )

                            except Exception as e:
                                self._logger.error(
                                    f"Error processing message {message_id.decode()}: {e}",
                                    exc_info=True,
                                )
                                # In a real implementation, this would go to retry/DLQ logic
                                # For now, just acknowledge to prevent infinite retries
                                await redis_conn.xack(topic, group, message_id)

                except asyncio.TimeoutError:
                    # Normal timeout, continue
                    continue
                except Exception as e:
                    self._logger.error(f"Error in Redis consumer loop: {e}")
                    await asyncio.sleep(self.config.retry_delay)

        except asyncio.CancelledError:
            self._logger.info(f"Redis consumer '{consumer_name}' cancelled")
        except Exception as e:
            self._logger.error(f"Redis consumer '{consumer_name}' failed: {e}")

        self._logger.info(f"Redis consumer '{consumer_name}' stopped")

    def _decode_redis_message(self, fields: dict[bytes, bytes]) -> Event:
        """Decode a Redis Stream message to an Event."""
        # Extract event data
        event_data = fields.get(b"data")
        if not event_data:
            raise ValueError("Redis message missing 'data' field")

        # Decode event
        event = self.config.codec.decode(event_data)

        # Extract headers from Redis fields
        headers = {}
        for field_name, field_value in fields.items():
            field_str = field_name.decode("utf-8")
            if field_str.startswith("header_"):
                header_name = field_str[7:]  # Remove "header_" prefix
                headers[header_name] = field_value.decode("utf-8")

        # Add extracted headers to event
        if headers:
            event = event.with_headers(**headers)

        return event

    async def _close_impl(self) -> None:
        """Close Redis event bus."""
        # Stop all consumer groups
        for consumer_info in self._consumer_groups:
            await consumer_info.stop()

        self._consumer_groups.clear()

        # Close Redis connection
        if self._redis:
            await self._redis.close()
            self._redis = None

def create_redis_bus(config: Optional[RedisConfig] = None) -> RedisEventBus:
    """
    Factory function to create a Redis Streams event bus.

    Args:
        config: Redis configuration (uses defaults if None)

    Returns:
        Configured Redis event bus

    Raises:
        ImportError: If Redis support is not available
    """
    if not REDIS_AVAILABLE:
        raise ImportError(
            "Redis support not available. Install with: pip install 'dotmac-events[redis]'"
        )

    return RedisEventBus(config or RedisConfig())

# Backward compatibility alias
RedisStreamsEventBus = RedisEventBus

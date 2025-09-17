"""
Redis scaling backend for multi-instance WebSocket deployments.
"""

import asyncio
import json

import time
import uuid
from typing import Any, Optional

from .base import ScalingBackend

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

try:
    import redis.asyncio as redis
    from redis.asyncio import Redis

    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    Redis = None
    REDIS_AVAILABLE = False

class RedisScalingBackend(ScalingBackend):
    """Redis-based scaling backend for WebSocket gateway."""

    def __init__(self, redis_config, session_manager, channel_manager):
        if not REDIS_AVAILABLE:
            raise ImportError("Redis is not available. Install with: pip install redis")

        self.config = redis_config
        self.session_manager = session_manager
        self.channel_manager = channel_manager

        # Redis connections
        self.redis: Optional[Redis] = None
        self.pubsub = None

        # Instance identity
        self.instance_id = str(uuid.uuid4())

        # Subscription management
        self._subscribed_channels: set[str] = set()
        self._listener_task: Optional[asyncio.Task] = None

        # Statistics
        self._stats = {
            "messages_published": 0,
            "messages_received": 0,
            "connection_errors": 0,
            "reconnects": 0,
        }

        self._started = False
        self._start_time: Optional[float] = None

    async def start(self):
        """Start the Redis scaling backend."""
        if self._started:
            return

        try:
            # Create Redis connection
            self.redis = redis.from_url(
                self.config.to_url(),
                max_connections=self.config.max_connections,
                retry_on_timeout=self.config.retry_on_timeout,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
            )

            # Test connection
            await self.redis.ping()

            # Create pub/sub connection
            self.pubsub = self.redis.pubsub()

            # Subscribe to instance-wide channels
            await self._subscribe_to_instance_channels()

            # Start message listener
            self._listener_task = asyncio.create_task(self._listen_for_messages())

            self._started = True
            self._start_time = time.time()

            logger.info(f"Redis scaling backend started (instance: {self.instance_id})")

        except Exception as e:
            logger.error(f"Failed to start Redis scaling backend: {e}")
            self._stats["connection_errors"] += 1
            raise

    async def stop(self):
        """Stop the Redis scaling backend."""
        if not self._started:
            return

        try:
            # Stop listener task
            if self._listener_task and not self._listener_task.done():
                self._listener_task.cancel()
                try:
                    await self._listener_task
                except asyncio.CancelledError:
                    pass

            # Close pub/sub connection
            if self.pubsub:
                await self.pubsub.close()

            # Close Redis connection
            if self.redis:
                await self.redis.close()

            self._started = False
            logger.info(f"Redis scaling backend stopped (instance: {self.instance_id})")

        except Exception as e:
            logger.error(f"Error stopping Redis scaling backend: {e}")

    async def _subscribe_to_instance_channels(self):
        """Subscribe to Redis channels for this instance."""
        channels = [
            f"{self.config.channel_prefix}:broadcast:user",
            f"{self.config.channel_prefix}:broadcast:tenant",
            f"{self.config.channel_prefix}:broadcast:channel",
            f"{self.config.channel_prefix}:session:{self.instance_id}",
        ]

        for channel in channels:
            await self.pubsub.subscribe(channel)
            self._subscribed_channels.add(channel)

        logger.debug(f"Subscribed to Redis channels: {channels}")

    async def _listen_for_messages(self):
        """Listen for messages from other instances."""
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    await self._handle_redis_message(message["channel"], message["data"])
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Redis message listener error: {e}")
            self._stats["connection_errors"] += 1

            # Attempt to reconnect
            if self._started:
                logger.info("Attempting to reconnect to Redis...")
                try:
                    await asyncio.sleep(1)  # Brief delay
                    await self._reconnect()
                    self._stats["reconnects"] += 1
                except Exception as reconnect_error:
                    logger.error(f"Redis reconnection failed: {reconnect_error}")

    async def _reconnect(self):
        """Reconnect to Redis."""
        if self.pubsub:
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()

        # Recreate connections
        self.redis = redis.from_url(
            self.config.to_url(),
            max_connections=self.config.max_connections,
            retry_on_timeout=self.config.retry_on_timeout,
            socket_timeout=self.config.socket_timeout,
            socket_connect_timeout=self.config.socket_connect_timeout,
        )

        await self.redis.ping()
        self.pubsub = self.redis.pubsub()

        # Resubscribe to channels
        for channel in self._subscribed_channels:
            await self.pubsub.subscribe(channel)

    async def _handle_redis_message(self, channel: str, data: bytes):
        """Handle incoming Redis message."""
        try:
            message = json.loads(data.decode("utf-8"))
            self._stats["messages_received"] += 1

            # Skip messages from this instance
            if message.get("instance_id") == self.instance_id:
                return

            message.get("type")
            target_type = message.get("target_type")
            target_id = message.get("target_id")
            msg_type = message.get("message_type")
            msg_data = message.get("message_data")

            if target_type == "user":
                await self.session_manager.broadcast_to_user(target_id, msg_type, msg_data)
            elif target_type == "tenant":
                await self.session_manager.broadcast_to_tenant(target_id, msg_type, msg_data)
            elif target_type == "channel":
                await self.channel_manager.broadcast_to_channel(target_id, msg_type, msg_data)
            elif target_type == "session":
                session = self.session_manager.get_session(target_id)
                if session:
                    await session.send_message(msg_type, msg_data)

        except Exception as e:
            logger.error(f"Error handling Redis message: {e}")

    async def _publish_message(
        self, channel: str, target_type: str, target_id: str, message_type: str, data: Any = None
    ):
        """Publish message to Redis channel."""
        if not self.redis:
            return

        try:
            message = {
                "instance_id": self.instance_id,
                "timestamp": time.time(),
                "type": "broadcast",
                "target_type": target_type,
                "target_id": target_id,
                "message_type": message_type,
                "message_data": data,
            }

            await self.redis.publish(channel, json.dumps(message))
            self._stats["messages_published"] += 1

        except Exception as e:
            logger.error(f"Error publishing Redis message: {e}")
            self._stats["connection_errors"] += 1

    async def broadcast_to_user(self, user_id: str, message_type: str, data: Any = None):
        """Broadcast message to all instances for a specific user."""
        channel = f"{self.config.channel_prefix}:broadcast:user"
        await self._publish_message(channel, "user", user_id, message_type, data)

    async def broadcast_to_tenant(self, tenant_id: str, message_type: str, data: Any = None):
        """Broadcast message to all instances for a specific tenant."""
        channel = f"{self.config.channel_prefix}:broadcast:tenant"
        await self._publish_message(channel, "tenant", tenant_id, message_type, data)

    async def broadcast_to_channel(self, channel_name: str, message_type: str, data: Any = None):
        """Broadcast message to all instances for a specific channel."""
        channel = f"{self.config.channel_prefix}:broadcast:channel"
        await self._publish_message(channel, "channel", channel_name, message_type, data)

    async def send_to_session(self, session_id: str, message_type: str, data: Any = None) -> bool:
        """Send message to a specific session across all instances."""
        # Try local first
        session = self.session_manager.get_session(session_id)
        if session:
            return await session.send_message(message_type, data)

        # Broadcast to all instances to find the session
        channel = f"{self.config.channel_prefix}:broadcast:session"
        await self._publish_message(channel, "session", session_id, message_type, data)

        # We can't know for sure if it was delivered, so return True
        return True

    async def register_instance(self):
        """Register this instance in Redis."""
        if not self.redis:
            return

        try:
            instance_key = f"{self.config.channel_prefix}:instances:{self.instance_id}"
            instance_data = {
                "instance_id": self.instance_id,
                "started_at": time.time(),
                "last_heartbeat": time.time(),
                "stats": self._stats,
            }

            await self.redis.setex(
                instance_key, self.config.message_ttl_seconds, json.dumps(instance_data)
            )

        except Exception as e:
            logger.error(f"Error registering instance: {e}")

    async def heartbeat(self):
        """Send heartbeat to Redis."""
        await self.register_instance()

    async def get_active_instances(self) -> dict[str, Any]:
        """Get all active instances from Redis."""
        if not self.redis:
            return {}

        try:
            pattern = f"{self.config.channel_prefix}:instances:*"
            keys = await self.redis.keys(pattern)

            instances = {}
            for key in keys:
                data = await self.redis.get(key)
                if data:
                    instance_info = json.loads(data)
                    instances[instance_info["instance_id"]] = instance_info

            return instances

        except Exception as e:
            logger.error(f"Error getting active instances: {e}")
            return {}

    async def health_check(self) -> dict[str, Any]:
        """Health check for Redis backend."""
        health = {
            "status": "unhealthy",
            "backend_type": "redis",
            "instance_id": self.instance_id,
            "uptime_seconds": time.time() - self._start_time if self._start_time else 0,
        }

        if not self._started:
            health["status"] = "stopped"
            return health

        try:
            # Test Redis connection
            if self.redis:
                latency = await self.redis.ping()
                health["redis_ping_ms"] = latency * 1000 if isinstance(latency, float) else 1.0

                # Update heartbeat
                await self.heartbeat()

                # Get active instances
                instances = await self.get_active_instances()
                health["active_instances"] = len(instances)

                health["status"] = "healthy"
            else:
                health["error"] = "Redis connection not established"

        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)
            self._stats["connection_errors"] += 1

        return health

    def get_stats(self) -> dict[str, Any]:
        """Get Redis backend statistics."""
        stats = {
            "backend_type": "redis",
            "instance_id": self.instance_id,
            "started": self._started,
            "uptime_seconds": time.time() - self._start_time if self._start_time else 0,
            **self._stats,
        }

        if self._subscribed_channels:
            stats["subscribed_channels"] = list(self._subscribed_channels)

        return stats

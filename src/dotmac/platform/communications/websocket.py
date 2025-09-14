"""WebSocket service for real-time communication."""

import asyncio
import json
import logging
import time
import uuid
from typing import Any, Callable

from pydantic import BaseModel, Field

from .config import WebSocketConfig

logger = logging.getLogger(__name__)


class WebSocketMessage(BaseModel):
    """WebSocket message model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = Field(..., description="Message type")
    channel: str | None = Field(None, description="Channel/room name")
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)

    def to_json(self) -> str:
        """Serialize to JSON."""
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> "WebSocketMessage":
        """Deserialize from JSON."""
        return cls.model_validate_json(json_str)


class WebSocketConnection:
    """Represents a WebSocket connection."""

    def __init__(
        self,
        connection_id: str,
        websocket: Any,  # The actual websocket connection
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.id = connection_id
        self.websocket = websocket
        self.user_id = user_id
        self.metadata = metadata or {}
        self.channels: set[str] = set()
        self.created_at = time.time()
        self.last_ping = time.time()

    async def send(self, message: WebSocketMessage):
        """Send message to this connection."""
        try:
            await self.websocket.send(message.to_json())
        except Exception as e:
            logger.error("Error sending to connection %s: %s", self.id, e)
            raise

    async def close(self):
        """Close the connection."""
        try:
            await self.websocket.close()
        except Exception:
            pass


class WebSocketManager:
    """
    WebSocket manager for real-time communication.

    Features:
    - Channel-based messaging (rooms)
    - Broadcasting
    - Direct messaging
    - Connection management
    - Optional Redis for scaling
    """

    def __init__(self, config: WebSocketConfig):
        """
        Initialize WebSocket manager.

        Args:
            config: WebSocket configuration
        """
        self.config = config
        self._connections: dict[str, WebSocketConnection] = {}
        self._channels: dict[str, set[str]] = {}  # channel -> connection_ids
        self._redis_client = None
        self._redis_task = None
        self._running = False

    async def start(self):
        """Start the WebSocket manager."""
        self._running = True

        if self.config.use_redis and self.config.redis_url:
            await self._init_redis()

        logger.info("WebSocket manager started")

    async def stop(self):
        """Stop the WebSocket manager."""
        self._running = False

        # Close all connections
        for connection in list(self._connections.values()):
            await self.disconnect(connection.id)

        if self._redis_task:
            self._redis_task.cancel()
            try:
                await self._redis_task
            except asyncio.CancelledError:
                pass

        if self._redis_client:
            await self._redis_client.close()

        logger.info("WebSocket manager stopped")

    async def _init_redis(self):
        """Initialize Redis for pub/sub."""
        try:
            import redis.asyncio as redis

            self._redis_client = redis.from_url(self.config.redis_url)
            await self._redis_client.ping()

            # Start Redis subscription task
            self._redis_task = asyncio.create_task(self._redis_subscriber())

            logger.info("Connected to Redis for WebSocket pub/sub")
        except Exception as e:
            logger.error("Failed to connect to Redis: %s", e)
            self.config.use_redis = False

    async def _redis_subscriber(self):
        """Subscribe to Redis channels for cross-instance messaging."""
        try:
            pubsub = self._redis_client.pubsub()
            await pubsub.subscribe("websocket:broadcast")

            while self._running:
                try:
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=1.0,
                    )

                    if message and message["type"] == "message":
                        # Parse and handle message
                        data = json.loads(message["data"])
                        ws_message = WebSocketMessage(**data)

                        # Broadcast to local connections
                        if ws_message.channel:
                            await self._broadcast_local(ws_message, ws_message.channel)
                        else:
                            await self._broadcast_all_local(ws_message)

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error("Error in Redis subscriber: %s", e)

        except Exception as e:
            logger.error("Redis subscriber error: %s", e)

    async def connect(
        self,
        websocket: Any,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> WebSocketConnection:
        """
        Register a new WebSocket connection.

        Args:
            websocket: The WebSocket connection
            user_id: Optional user identifier
            metadata: Optional connection metadata

        Returns:
            WebSocketConnection instance
        """
        # Check connection limit
        if len(self._connections) >= self.config.max_connections:
            raise ConnectionError("Maximum connections reached")

        connection_id = str(uuid.uuid4())
        connection = WebSocketConnection(
            connection_id,
            websocket,
            user_id,
            metadata,
        )

        self._connections[connection_id] = connection

        logger.info(
            "WebSocket connected: id=%s, user=%s",
            connection_id,
            user_id,
        )

        # Send welcome message
        welcome = WebSocketMessage(
            type="connected",
            data={"connection_id": connection_id},
        )
        await connection.send(welcome)

        return connection

    async def disconnect(self, connection_id: str):
        """
        Disconnect and cleanup a WebSocket connection.

        Args:
            connection_id: Connection ID
        """
        connection = self._connections.get(connection_id)
        if not connection:
            return

        # Remove from channels
        for channel in connection.channels:
            if channel in self._channels:
                self._channels[channel].discard(connection_id)
                if not self._channels[channel]:
                    del self._channels[channel]

        # Close connection
        await connection.close()

        # Remove from connections
        del self._connections[connection_id]

        logger.info("WebSocket disconnected: id=%s", connection_id)

    async def join_channel(self, connection_id: str, channel: str):
        """
        Join a connection to a channel.

        Args:
            connection_id: Connection ID
            channel: Channel name
        """
        connection = self._connections.get(connection_id)
        if not connection:
            raise ValueError(f"Connection {connection_id} not found")

        # Check channel limit
        if len(connection.channels) >= self.config.max_channels_per_connection:
            raise ValueError("Maximum channels per connection reached")

        # Add to channel
        if channel not in self._channels:
            self._channels[channel] = set()
        self._channels[channel].add(connection_id)
        connection.channels.add(channel)

        logger.debug("Connection %s joined channel %s", connection_id, channel)

        # Notify
        message = WebSocketMessage(
            type="channel_joined",
            channel=channel,
            data={"channel": channel},
        )
        await connection.send(message)

    async def leave_channel(self, connection_id: str, channel: str):
        """
        Remove a connection from a channel.

        Args:
            connection_id: Connection ID
            channel: Channel name
        """
        connection = self._connections.get(connection_id)
        if not connection:
            return

        if channel in connection.channels:
            connection.channels.remove(channel)

        if channel in self._channels:
            self._channels[channel].discard(connection_id)
            if not self._channels[channel]:
                del self._channels[channel]

        logger.debug("Connection %s left channel %s", connection_id, channel)

        # Notify
        message = WebSocketMessage(
            type="channel_left",
            channel=channel,
            data={"channel": channel},
        )
        await connection.send(message)

    async def send_to_connection(
        self,
        connection_id: str,
        message: WebSocketMessage,
    ):
        """
        Send message to specific connection.

        Args:
            connection_id: Connection ID
            message: Message to send
        """
        connection = self._connections.get(connection_id)
        if connection:
            await connection.send(message)

    async def send_to_user(
        self,
        user_id: str,
        message: WebSocketMessage,
    ):
        """
        Send message to all connections of a user.

        Args:
            user_id: User ID
            message: Message to send
        """
        for connection in self._connections.values():
            if connection.user_id == user_id:
                await connection.send(message)

    async def broadcast(
        self,
        message: WebSocketMessage,
        channel: str | None = None,
        exclude_connection: str | None = None,
    ):
        """
        Broadcast message.

        Args:
            message: Message to broadcast
            channel: Optional channel to broadcast to
            exclude_connection: Optional connection to exclude
        """
        if self.config.use_redis and self._redis_client:
            # Publish to Redis for cross-instance broadcast
            message.channel = channel
            await self._redis_client.publish(
                "websocket:broadcast",
                json.dumps(message.model_dump()),
            )
        else:
            # Local broadcast only
            if channel:
                await self._broadcast_local(message, channel, exclude_connection)
            else:
                await self._broadcast_all_local(message, exclude_connection)

    async def _broadcast_local(
        self,
        message: WebSocketMessage,
        channel: str,
        exclude_connection: str | None = None,
    ):
        """Broadcast to local connections in a channel."""
        connection_ids = self._channels.get(channel, set())

        for conn_id in connection_ids:
            if conn_id != exclude_connection:
                connection = self._connections.get(conn_id)
                if connection:
                    try:
                        await connection.send(message)
                    except Exception as e:
                        logger.error("Error broadcasting to %s: %s", conn_id, e)

    async def _broadcast_all_local(
        self,
        message: WebSocketMessage,
        exclude_connection: str | None = None,
    ):
        """Broadcast to all local connections."""
        for conn_id, connection in self._connections.items():
            if conn_id != exclude_connection:
                try:
                    await connection.send(message)
                except Exception as e:
                    logger.error("Error broadcasting to %s: %s", conn_id, e)

    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self._connections)

    def get_channel_count(self) -> int:
        """Get number of active channels."""
        return len(self._channels)

    def get_channels(self) -> list[str]:
        """Get list of active channels."""
        return list(self._channels.keys())

    def get_connection_info(self, connection_id: str) -> dict[str, Any] | None:
        """Get connection information."""
        connection = self._connections.get(connection_id)
        if not connection:
            return None

        return {
            "id": connection.id,
            "user_id": connection.user_id,
            "channels": list(connection.channels),
            "created_at": connection.created_at,
            "metadata": connection.metadata,
        }
"""
Main WebSocket Gateway implementation.
"""


import time
from collections.abc import Awaitable, Callable
from typing import Any, Optional

import websockets
from websockets.server import WebSocketServerProtocol

from ..auth.manager import AuthManager
from ..backends.base import ScalingBackend
from ..backends.local import LocalBackend
from ..channels.manager import ConcreteChannelManager
from ..middleware.rate_limit import RateLimitMiddleware
from ..middleware.tenant import TenantMiddleware
from dotmac.platform.settings import settings
from .session import SessionManager, SessionMetadata, WebSocketSession

from dotmac.platform.logging import get_logger
logger = get_logger(__name__)

class WebSocketGateway:
    """Main WebSocket Gateway class."""

    def __init__(self, config: type(settings.websocket)):
        self.config = config
        self.session_manager = SessionManager(config)
        self.channel_manager = ConcreteChannelManager(config)

        # Initialize components
        self.auth_manager: Optional[AuthManager] = None
        if config.auth_config.enabled:
            self.auth_manager = AuthManager(config.auth_config)

        self.tenant_middleware = TenantMiddleware(config)
        self.rate_limit_middleware = RateLimitMiddleware(config.rate_limit_config)

        # Scaling backend
        self.scaling_backend: Optional[ScalingBackend] = None
        self._init_scaling_backend()

        # Server state
        self._server = None
        self._running = False

        # Message handlers
        self._message_handlers: dict[str, Callable[[WebSocketSession, Any], Awaitable[None]]] = {}
        self._connection_handlers: list[Callable[[WebSocketSession], Awaitable[None]]] = []
        self._disconnection_handlers: list[Callable[[WebSocketSession], Awaitable[None]]] = []

        # Built-in message handlers
        self._register_builtin_handlers()

        # Observability hooks
        self._observability_hooks = None

    def _init_scaling_backend(self):
        """Initialize scaling backend."""
        if self.config.backend_type.value == "redis":
            try:
                from ..backends.redis import RedisScalingBackend

                self.scaling_backend = RedisScalingBackend(
                    self.config.redis_config, self.session_manager, self.channel_manager
                )
            except ImportError:
                logger.warning("Redis not available, falling back to local backend")
                self.scaling_backend = LocalBackend()
        else:
            self.scaling_backend = LocalBackend()

    def _register_builtin_handlers(self):
        """Register built-in message handlers."""

        async def handle_ping(session: WebSocketSession, data: Any):
            """Handle ping messages."""
            await session.send_message("pong", {"timestamp": time.time()})

        async def handle_auth(session: WebSocketSession, data: Any):
            """Handle authentication messages."""
            if not self.auth_manager:
                await session.send_message("auth_error", {"message": "Authentication not enabled"})
                return

            try:
                token = data.get("token") if isinstance(data, dict) else None
                if not token:
                    await session.send_message("auth_error", {"message": "Token required"})
                    return

                auth_result = await self.auth_manager.authenticate_token(token)
                if auth_result.success:
                    # Update session with user info
                    self.session_manager.update_session_user_info(
                        session.session_id,
                        auth_result.user_info.user_id,
                        auth_result.user_info.tenant_id,
                        **auth_result.user_info.extra_data,
                    )

                    await session.send_message(
                        "auth_success",
                        {
                            "user_id": auth_result.user_info.user_id,
                            "tenant_id": auth_result.user_info.tenant_id,
                        },
                    )
                else:
                    await session.send_message("auth_error", {"message": auth_result.error})

            except Exception as e:
                logger.error(f"Authentication error: {e}")
                await session.send_message("auth_error", {"message": "Authentication failed"})

        async def handle_subscribe(session: WebSocketSession, data: Any):
            """Handle channel subscription."""
            if not isinstance(data, dict) or "channel" not in data:
                await session.send_message("subscribe_error", {"message": "Channel name required"})
                return

            channel_name = data["channel"]

            # Check if user can subscribe to this channel
            if not await self._can_access_channel(session, channel_name):
                await session.send_message(
                    "subscribe_error",
                    {"message": "Access denied to channel", "channel": channel_name},
                )
                return

            try:
                await self.channel_manager.subscribe_session(session, channel_name)
                await session.send_message("subscribe_success", {"channel": channel_name})
            except Exception as e:
                logger.error(f"Subscription error: {e}")
                await session.send_message(
                    "subscribe_error", {"message": "Subscription failed", "channel": channel_name}
                )

        async def handle_unsubscribe(session: WebSocketSession, data: Any):
            """Handle channel unsubscription."""
            if not isinstance(data, dict) or "channel" not in data:
                await session.send_message(
                    "unsubscribe_error", {"message": "Channel name required"}
                )
                return

            channel_name = data["channel"]

            try:
                await self.channel_manager.unsubscribe_session(session, channel_name)
                await session.send_message("unsubscribe_success", {"channel": channel_name})
            except Exception as e:
                logger.error(f"Unsubscription error: {e}")
                await session.send_message(
                    "unsubscribe_error",
                    {"message": "Unsubscription failed", "channel": channel_name},
                )

        async def handle_channel_message(session: WebSocketSession, data: Any):
            """Handle messages sent to channels."""
            if not isinstance(data, dict) or "channel" not in data or "message" not in data:
                await session.send_message(
                    "channel_error", {"message": "Channel and message required"}
                )
                return

            channel_name = data["channel"]
            message = data["message"]

            # Check if user can send to this channel
            if not await self._can_send_to_channel(session, channel_name):
                await session.send_message(
                    "channel_error", {"message": "Cannot send to channel", "channel": channel_name}
                )
                return

            try:
                await self.channel_manager.broadcast_to_channel(
                    channel_name,
                    "channel_message",
                    {
                        "channel": channel_name,
                        "message": message,
                        "sender": session.user_id,
                        "timestamp": time.time(),
                    },
                    exclude_session=session.session_id,
                )
            except Exception as e:
                logger.error(f"Channel broadcast error: {e}")
                await session.send_message(
                    "channel_error", {"message": "Failed to send message", "channel": channel_name}
                )

        # Register handlers
        self._message_handlers.update(
            {
                "ping": handle_ping,
                "auth": handle_auth,
                "authenticate": handle_auth,  # Alias
                "subscribe": handle_subscribe,
                "unsubscribe": handle_unsubscribe,
                "channel_message": handle_channel_message,
                "send": handle_channel_message,  # Alias
            }
        )

    async def _can_access_channel(self, session: WebSocketSession, channel_name: str) -> bool:
        """Check if session can access a channel."""
        # Basic tenant isolation
        if self.config.tenant_isolation_enabled and session.tenant_id:
            if not channel_name.startswith(f"tenant:{session.tenant_id}:"):
                return False

        # Check authentication requirements for private channels
        if channel_name.startswith("private:") and not session.is_authenticated:
            return False

        # Check user-specific channels
        if channel_name.startswith("user:") and session.is_authenticated:
            expected_user = channel_name.split(":", 2)[1]
            if expected_user != session.user_id:
                return False

        return True

    async def _can_send_to_channel(self, session: WebSocketSession, channel_name: str) -> bool:
        """Check if session can send messages to a channel."""
        # Must be able to access the channel first
        if not await self._can_access_channel(session, channel_name):
            return False

        # Read-only channels
        if channel_name.endswith(":readonly"):
            return False

        # Broadcast channels might require special permissions
        if channel_name.startswith("broadcast:"):
            # Only authenticated users can broadcast
            return session.is_authenticated

        return True

    def add_message_handler(
        self, message_type: str, handler: Callable[[WebSocketSession, Any], Awaitable[None]]
    ):
        """Add custom message handler."""
        self._message_handlers[message_type] = handler

    def add_connection_handler(self, handler: Callable[[WebSocketSession], Awaitable[None]]):
        """Add connection handler."""
        self._connection_handlers.append(handler)

    def add_disconnection_handler(self, handler: Callable[[WebSocketSession], Awaitable[None]]):
        """Add disconnection handler."""
        self._disconnection_handlers.append(handler)

    def set_observability_hooks(self, hooks):
        """Set observability hooks."""
        self._observability_hooks = hooks

    async def handle_websocket(self, websocket: WebSocketServerProtocol, path: str):
        """Handle individual WebSocket connection."""
        client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"

        # Rate limiting check
        if not await self.rate_limit_middleware.check_connection_limit(client_ip):
            await websocket.close(1008, "Connection limit exceeded")
            return

        # Create session metadata
        metadata = SessionMetadata(
            session_id="",  # Will be set by session manager
            ip_address=client_ip,
            user_agent=websocket.request_headers.get("User-Agent"),
        )

        # Apply tenant middleware to extract tenant info
        tenant_info = await self.tenant_middleware.extract_tenant_info(websocket)
        if tenant_info:
            metadata.tenant_id = tenant_info.get("tenant_id")
            metadata.custom_data.update(tenant_info)

        session = None
        try:
            # Create session
            session = await self.session_manager.create_session(websocket, metadata=metadata)

            # Add session to rate limiting
            self.rate_limit_middleware.add_session(session)

            # Set up session message handler
            async def handle_session_message(message_type: str, data: Any):
                await self._handle_message(session, message_type, data)

            session.add_message_handler(handle_session_message)

            # Call connection handlers
            for handler in self._connection_handlers:
                try:
                    await handler(session)
                except Exception as e:
                    logger.error(f"Connection handler error: {e}")

            # Emit connection event
            if self._observability_hooks:
                await self._observability_hooks.on_connection(session)

            logger.info(f"WebSocket connected: {session.session_id} from {client_ip}")

            # Handle messages
            async for raw_message in websocket:
                try:
                    # Rate limiting check
                    if not await self.rate_limit_middleware.check_message_rate(session):
                        await session.send_message(
                            "rate_limit", {"message": "Message rate limit exceeded"}
                        )
                        continue

                    # Handle the message
                    await session.handle_message(raw_message)

                    # Emit message event
                    if self._observability_hooks:
                        await self._observability_hooks.on_message(session, raw_message)

                except websockets.exceptions.ConnectionClosed:
                    break
                except Exception as e:
                    logger.error(f"Message handling error for {session.session_id}: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.debug(f"WebSocket connection closed: {client_ip}")
        except Exception as e:
            logger.error(f"WebSocket handler error: {e}")
            if session:
                await session.send_message("error", {"message": "Internal server error"})
        finally:
            if session:
                # Call disconnection handlers
                for handler in self._disconnection_handlers:
                    try:
                        await handler(session)
                    except Exception as e:
                        logger.error(f"Disconnection handler error: {e}")

                # Remove from rate limiting
                self.rate_limit_middleware.remove_session(session)

                # Emit disconnection event
                if self._observability_hooks:
                    await self._observability_hooks.on_disconnection(session)

                # Clean up session
                await self.session_manager.remove_session(session.session_id)

                logger.info(f"WebSocket disconnected: {session.session_id}")

    async def _handle_message(self, session: WebSocketSession, message_type: str, data: Any):
        """Handle incoming message from session."""
        handler = self._message_handlers.get(message_type)
        if handler:
            try:
                await handler(session, data)
            except Exception as e:
                logger.error(f"Message handler error for {message_type}: {e}")
                await session.send_message(
                    "error", {"message": f"Error handling {message_type}", "type": message_type}
                )
        else:
            logger.warning(f"Unknown message type: {message_type}")
            await session.send_message(
                "unknown_message_type",
                {"message": f"Unknown message type: {message_type}", "type": message_type},
            )

    async def start_server(self):
        """Start the WebSocket server."""
        if self._running:
            return

        logger.info(
            f"Starting WebSocket server on {self.config.host}:{self.config.port}{self.config.path}"
        )

        # Start session cleanup task
        self.session_manager.start_cleanup_task()

        # Start scaling backend
        if self.scaling_backend:
            await self.scaling_backend.start()

        # Start channel manager and set session manager reference
        self.channel_manager.set_session_manager(self.session_manager)
        await self.channel_manager.start()

        # Start rate limit cleanup
        self.rate_limit_middleware.start_cleanup_task()

        # Create WebSocket server
        self._server = await websockets.serve(
            self.handle_websocket,
            self.config.host,
            self.config.port,
            path=self.config.path,
            max_size=self.config.max_size,
            max_queue=self.config.max_queue,
            read_limit=self.config.read_limit,
            write_limit=self.config.write_limit,
            compression=self.config.compression,
            extra_headers=(
                list(self.config.extra_headers.items()) if self.config.extra_headers else None
            ),
        )

        self._running = True
        logger.info("WebSocket server started successfully")

        # Emit server started event
        if self._observability_hooks:
            await self._observability_hooks.on_server_start(self.config)

    async def stop_server(self):
        """Stop the WebSocket server."""
        if not self._running:
            return

        logger.info("Stopping WebSocket server...")

        try:
            # Stop server
            if self._server:
                self._server.close()
                await self._server.wait_closed()

            # Close all sessions
            await self.session_manager.close_all_sessions()

            # Stop components
            if self.scaling_backend:
                await self.scaling_backend.stop()

            await self.channel_manager.stop()
            self.rate_limit_middleware.stop_cleanup_task()

            self._running = False
            logger.info("WebSocket server stopped")

            # Emit server stopped event
            if self._observability_hooks:
                await self._observability_hooks.on_server_stop()

        except Exception as e:
            logger.error(f"Error stopping WebSocket server: {e}")

    async def broadcast_to_user(self, user_id: str, message_type: str, data: Any = None) -> int:
        """Broadcast message to all sessions of a user."""
        local_count = await self.session_manager.broadcast_to_user(user_id, message_type, data)

        # Also broadcast via scaling backend for multi-instance
        if self.scaling_backend:
            await self.scaling_backend.broadcast_to_user(user_id, message_type, data)

        return local_count

    async def broadcast_to_tenant(self, tenant_id: str, message_type: str, data: Any = None) -> int:
        """Broadcast message to all sessions of a tenant."""
        local_count = await self.session_manager.broadcast_to_tenant(tenant_id, message_type, data)

        # Also broadcast via scaling backend
        if self.scaling_backend:
            await self.scaling_backend.broadcast_to_tenant(tenant_id, message_type, data)

        return local_count

    async def broadcast_to_channel(
        self,
        channel_name: str,
        message_type: str,
        data: Any = None,
        tenant_id: Optional[str] = None,
    ) -> int:
        """Broadcast message to a channel."""
        return await self.channel_manager.broadcast_to_channel(
            channel_name, message_type, data, tenant_id=tenant_id
        )

    async def send_to_session(self, session_id: str, message_type: str, data: Any = None) -> bool:
        """Send message to a specific session."""
        session = self.session_manager.get_session(session_id)
        if session:
            return await session.send_message(message_type, data)

        # Try via scaling backend
        if self.scaling_backend:
            return await self.scaling_backend.send_to_session(session_id, message_type, data)

        return False

    def get_stats(self) -> dict[str, Any]:
        """Get gateway statistics."""
        stats = {
            "server": {
                "running": self._running,
                "config": {
                    "host": self.config.host,
                    "port": self.config.port,
                    "path": self.config.path,
                    "backend_type": self.config.backend_type.value,
                },
            },
            "sessions": self.session_manager.get_stats(),
            "channels": self.channel_manager.get_stats(),
            "rate_limiting": self.rate_limit_middleware.get_stats(),
        }

        if self.scaling_backend:
            stats["scaling_backend"] = self.scaling_backend.get_stats()

        return stats

    async def health_check(self) -> dict[str, Any]:
        """Perform health check."""
        health = {"status": "healthy", "timestamp": time.time(), "components": {}}

        # Check server
        health["components"]["server"] = {"status": "healthy" if self._running else "unhealthy"}

        # Check scaling backend
        if self.scaling_backend:
            backend_health = await self.scaling_backend.health_check()
            health["components"]["scaling_backend"] = backend_health
            if backend_health["status"] != "healthy":
                health["status"] = "degraded"

        # Check session manager
        session_stats = self.session_manager.get_stats()
        health["components"]["sessions"] = {
            "status": "healthy",
            "total_sessions": session_stats["total_sessions"],
        }

        # Check channel manager
        channel_stats = self.channel_manager.get_stats()
        health["components"]["channels"] = {
            "status": "healthy",
            "total_channels": channel_stats["total_channels"],
        }

        return health

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_server()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_server()

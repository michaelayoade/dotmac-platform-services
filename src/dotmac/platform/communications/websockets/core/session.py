"""
WebSocket session management.
"""

import asyncio
import json

import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from dotmac.platform.logging import get_logger
logger = get_logger(__name__)

class SessionState(str, Enum):
    """WebSocket session states."""

    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"

@dataclass
class SessionMetadata:
    """Session metadata and tracking."""

    session_id: str
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Connection info
    connected_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    last_ping: Optional[float] = None

    # Session data
    custom_data: dict[str, Any] = field(default_factory=dict)
    channels: set[str] = field(default_factory=set)

    # Statistics
    messages_sent: int = 0
    messages_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0

class WebSocketSession:
    """Individual WebSocket session wrapper."""

    def __init__(self, websocket, session_id: str, metadata: Optional[SessionMetadata] = None):
        self.websocket = websocket
        self.session_id = session_id
        self.metadata = metadata or SessionMetadata(session_id=session_id)
        self.state = SessionState.CONNECTING

        # Event handlers
        self._message_handlers: list[Callable[[str, Any], Awaitable[None]]] = []
        self._disconnect_handlers: list[Callable[[], Awaitable[None]]] = []

        # Internal state
        self._closed = False
        self._ping_task: Optional[asyncio.Task] = None

    @property
    def is_authenticated(self) -> bool:
        """Check if session is authenticated."""
        return self.state == SessionState.AUTHENTICATED

    @property
    def user_id(self) -> Optional[str]:
        """Get user ID if authenticated."""
        return self.metadata.user_id

    @property
    def tenant_id(self) -> Optional[str]:
        """Get tenant ID."""
        return self.metadata.tenant_id

    @property
    def is_connected(self) -> bool:
        """Check if session is still connected."""
        return not self._closed and self.state in (
            SessionState.CONNECTED,
            SessionState.AUTHENTICATED,
        )

    def set_user_info(self, user_id: str, tenant_id: Optional[str] = None, **extra_data):
        """Set user authentication information."""
        self.metadata.user_id = user_id
        if tenant_id:
            self.metadata.tenant_id = tenant_id

        self.metadata.custom_data.update(extra_data)
        self.state = SessionState.AUTHENTICATED

    def add_message_handler(self, handler: Callable[[str, Any], Awaitable[None]]):
        """Add message handler."""
        self._message_handlers.append(handler)

    def add_disconnect_handler(self, handler: Callable[[], Awaitable[None]]):
        """Add disconnect handler."""
        self._disconnect_handlers.append(handler)

    async def send_message(self, message_type: str, data: Any = None) -> bool:
        """Send structured message to client."""
        if not self.is_connected:
            return False

        try:
            message = {"type": message_type, "data": data, "timestamp": time.time()}

            message_json = json.dumps(message)
            await self.websocket.send(message_json)

            # Update statistics
            self.metadata.messages_sent += 1
            self.metadata.bytes_sent += len(message_json)

            return True

        except Exception as e:
            logger.warning(f"Failed to send message to session {self.session_id}: {e}")
            await self._handle_disconnect()
            return False

    async def send_raw(self, data: str) -> bool:
        """Send raw data to client."""
        if not self.is_connected:
            return False

        try:
            await self.websocket.send(data)

            # Update statistics
            self.metadata.messages_sent += 1
            self.metadata.bytes_sent += len(data)

            return True

        except Exception as e:
            logger.warning(f"Failed to send raw data to session {self.session_id}: {e}")
            await self._handle_disconnect()
            return False

    async def ping(self) -> bool:
        """Send ping to client."""
        try:
            await self.websocket.ping()
            self.metadata.last_ping = time.time()
            return True
        except Exception as e:
            logger.debug(f"Ping failed for session {self.session_id}: {e}")
            return False

    async def handle_message(self, raw_message: str):
        """Handle incoming message from client."""
        try:
            # Update activity and statistics
            self.metadata.last_activity = time.time()
            self.metadata.messages_received += 1
            self.metadata.bytes_received += len(raw_message)

            # Try to parse as JSON
            try:
                message = json.loads(raw_message)
                message_type = message.get("type", "unknown")
                message_data = message.get("data")
            except json.JSONDecodeError:
                # Handle as raw message
                message_type = "raw"
                message_data = raw_message

            # Call message handlers
            for handler in self._message_handlers:
                try:
                    await handler(message_type, message_data)
                except Exception as e:
                    logger.error(f"Message handler error in session {self.session_id}: {e}")

        except Exception as e:
            logger.error(f"Error handling message in session {self.session_id}: {e}")

    async def close(self, code: int = 1000, reason: str = "Session closed"):
        """Close the WebSocket session."""
        if self._closed:
            return

        self._closed = True
        self.state = SessionState.DISCONNECTING

        try:
            # Cancel ping task
            if self._ping_task and not self._ping_task.done():
                self._ping_task.cancel()

            # Close WebSocket
            await self.websocket.close(code, reason)

        except Exception as e:
            logger.debug(f"Error closing session {self.session_id}: {e}")

        finally:
            await self._handle_disconnect()

    async def _handle_disconnect(self):
        """Handle session disconnect."""
        if self.state == SessionState.DISCONNECTED:
            return

        self.state = SessionState.DISCONNECTED

        # Call disconnect handlers
        for handler in self._disconnect_handlers:
            try:
                await handler()
            except Exception as e:
                logger.error(f"Disconnect handler error in session {self.session_id}: {e}")

    def start_ping_task(self, interval: int = 30, timeout: int = 10):
        """Start periodic ping task."""

        async def ping_loop():
            while self.is_connected:
                try:
                    await asyncio.sleep(interval)
                    if not self.is_connected:
                        break

                    success = await self.ping()
                    if not success:
                        logger.warning(f"Ping failed for session {self.session_id}")
                        await self.close(1002, "Ping failed")
                        break

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Ping loop error for session {self.session_id}: {e}")
                    break

        self._ping_task = asyncio.create_task(ping_loop())

    def to_dict(self) -> dict[str, Any]:
        """Convert session to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "state": self.state.value,
            "metadata": {
                "user_id": self.metadata.user_id,
                "tenant_id": self.metadata.tenant_id,
                "ip_address": self.metadata.ip_address,
                "user_agent": self.metadata.user_agent,
                "connected_at": self.metadata.connected_at,
                "last_activity": self.metadata.last_activity,
                "last_ping": self.metadata.last_ping,
                "channels": list(self.metadata.channels),
                "messages_sent": self.metadata.messages_sent,
                "messages_received": self.metadata.messages_received,
                "bytes_sent": self.metadata.bytes_sent,
                "bytes_received": self.metadata.bytes_received,
                "custom_data": self.metadata.custom_data,
            },
        }

class SessionManager:
    """Manages WebSocket sessions."""

    def __init__(self, config):
        self.config = config
        self._sessions: dict[str, WebSocketSession] = {}
        self._user_sessions: dict[str, set[str]] = {}  # user_id -> session_ids
        self._tenant_sessions: dict[str, set[str]] = {}  # tenant_id -> session_ids
        self._cleanup_task: Optional[asyncio.Task] = None

    def start_cleanup_task(self):
        """Start session cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            return

        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(self.config.session_config.cleanup_interval_seconds)
                    await self._cleanup_expired_sessions()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Session cleanup error: {e}")

        self._cleanup_task = asyncio.create_task(cleanup_loop())

    def stop_cleanup_task(self):
        """Stop session cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()

    async def create_session(
        self,
        websocket,
        session_id: Optional[str] = None,
        metadata: Optional[SessionMetadata] = None,
    ) -> WebSocketSession:
        """Create a new WebSocket session."""
        if not session_id:
            session_id = str(uuid.uuid4())

        if session_id in self._sessions:
            # Close existing session
            await self.remove_session(session_id)

        # Create session metadata if not provided
        if not metadata:
            metadata = SessionMetadata(session_id=session_id)

        # Create session
        session = WebSocketSession(websocket, session_id, metadata)
        session.state = SessionState.CONNECTED

        # Add disconnect handler to auto-cleanup
        session.add_disconnect_handler(lambda: self.remove_session(session_id))

        # Store session
        self._sessions[session_id] = session

        # Start ping task if enabled
        if self.config.session_config.ping_interval_seconds > 0:
            session.start_ping_task(
                self.config.session_config.ping_interval_seconds,
                self.config.session_config.ping_timeout_seconds,
            )

        logger.info(f"Created session {session_id}")
        return session

    async def remove_session(self, session_id: str) -> bool:
        """Remove a WebSocket session."""
        session = self._sessions.pop(session_id, None)
        if not session:
            return False

        # Remove from user and tenant indexes
        if session.user_id:
            user_sessions = self._user_sessions.get(session.user_id, set())
            user_sessions.discard(session_id)
            if not user_sessions:
                self._user_sessions.pop(session.user_id, None)

        if session.tenant_id:
            tenant_sessions = self._tenant_sessions.get(session.tenant_id, set())
            tenant_sessions.discard(session_id)
            if not tenant_sessions:
                self._tenant_sessions.pop(session.tenant_id, None)

        # Close session if not already closed
        if session.is_connected:
            await session.close()

        logger.info(f"Removed session {session_id}")
        return True

    def get_session(self, session_id: str) -> Optional[WebSocketSession]:
        """Get session by ID."""
        return self._sessions.get(session_id)

    def get_user_sessions(self, user_id: str) -> list[WebSocketSession]:
        """Get all sessions for a user."""
        session_ids = self._user_sessions.get(user_id, set())
        return [self._sessions[sid] for sid in session_ids if sid in self._sessions]

    def get_tenant_sessions(self, tenant_id: str) -> list[WebSocketSession]:
        """Get all sessions for a tenant."""
        session_ids = self._tenant_sessions.get(tenant_id, set())
        return [self._sessions[sid] for sid in session_ids if sid in self._sessions]

    def get_all_sessions(self) -> list[WebSocketSession]:
        """Get all active sessions."""
        return list(self._sessions.values())

    def update_session_user_info(
        self, session_id: str, user_id: str, tenant_id: Optional[str] = None, **extra_data
    ):
        """Update session user information and indexes."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        # Remove from old indexes
        old_user_id = session.user_id
        old_tenant_id = session.tenant_id

        if old_user_id and old_user_id != user_id:
            user_sessions = self._user_sessions.get(old_user_id, set())
            user_sessions.discard(session_id)
            if not user_sessions:
                self._user_sessions.pop(old_user_id, None)

        if old_tenant_id and old_tenant_id != tenant_id:
            tenant_sessions = self._tenant_sessions.get(old_tenant_id, set())
            tenant_sessions.discard(session_id)
            if not tenant_sessions:
                self._tenant_sessions.pop(old_tenant_id, None)

        # Update session
        session.set_user_info(user_id, tenant_id, **extra_data)

        # Add to new indexes
        if user_id:
            self._user_sessions.setdefault(user_id, set()).add(session_id)

        if tenant_id:
            self._tenant_sessions.setdefault(tenant_id, set()).add(session_id)

        return True

    async def broadcast_to_user(self, user_id: str, message_type: str, data: Any = None) -> int:
        """Broadcast message to all sessions of a user."""
        sessions = self.get_user_sessions(user_id)
        success_count = 0

        for session in sessions:
            if await session.send_message(message_type, data):
                success_count += 1

        return success_count

    async def broadcast_to_tenant(self, tenant_id: str, message_type: str, data: Any = None) -> int:
        """Broadcast message to all sessions of a tenant."""
        sessions = self.get_tenant_sessions(tenant_id)
        success_count = 0

        for session in sessions:
            if await session.send_message(message_type, data):
                success_count += 1

        return success_count

    async def broadcast_to_all(self, message_type: str, data: Any = None) -> int:
        """Broadcast message to all sessions."""
        sessions = self.get_all_sessions()
        success_count = 0

        for session in sessions:
            if await session.send_message(message_type, data):
                success_count += 1

        return success_count

    async def _cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        current_time = time.time()
        expired_sessions = []

        for session in self._sessions.values():
            # Check idle timeout
            idle_time = current_time - session.metadata.last_activity
            if idle_time > self.config.session_config.idle_timeout_seconds:
                expired_sessions.append(session.session_id)
                continue

            # Check max session duration
            session_duration = current_time - session.metadata.connected_at
            if session_duration > self.config.session_config.max_session_duration_seconds:
                expired_sessions.append(session.session_id)
                continue

        # Remove expired sessions
        for session_id in expired_sessions:
            await self.remove_session(session_id)

        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

    def get_stats(self) -> dict[str, Any]:
        """Get session manager statistics."""
        total_sessions = len(self._sessions)
        authenticated_sessions = sum(1 for s in self._sessions.values() if s.is_authenticated)

        return {
            "total_sessions": total_sessions,
            "authenticated_sessions": authenticated_sessions,
            "anonymous_sessions": total_sessions - authenticated_sessions,
            "unique_users": len(self._user_sessions),
            "unique_tenants": len(self._tenant_sessions),
            "sessions_by_state": {
                state.value: sum(1 for s in self._sessions.values() if s.state == state)
                for state in SessionState
            },
        }

    async def close_all_sessions(self):
        """Close all active sessions."""
        sessions = list(self._sessions.values())
        for session in sessions:
            await session.close()

        self._sessions.clear()
        self._user_sessions.clear()
        self._tenant_sessions.clear()

        self.stop_cleanup_task()

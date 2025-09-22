"""
Channel abstractions and interfaces.
"""


import time
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Optional

from dotmac.platform.logging import get_logger
logger = get_logger(__name__)

@dataclass
class ChannelMetadata:
    """Metadata for a channel."""

    name: str
    created_at: float = field(default_factory=time.time)
    description: Optional[str] = None

    # Access control
    public: bool = True
    tenant_id: Optional[str] = None
    required_roles: list[str] = field(default_factory=list)
    required_permissions: list[str] = field(default_factory=list)

    # Channel settings
    persistent: bool = False  # Whether channel persists when empty
    max_subscribers: Optional[int] = None
    message_history: int = 0  # Number of messages to keep in history

    # Statistics
    total_messages: int = 0
    peak_subscribers: int = 0
    last_activity: float = field(default_factory=time.time)

    # Custom metadata
    custom_data: dict[str, Any] = field(default_factory=dict)

class Channel(ABC):
    """Abstract base class for channels."""

    def __init__(self, name: str, metadata: Optional[ChannelMetadata] = None):
        self.name = name
        self.metadata = metadata or ChannelMetadata(name=name)
        self._subscribers: set[str] = set()  # session_ids
        self._message_history: list[dict[str, Any]] = []

        # Event handlers
        self._subscription_handlers: list[Callable[[str, str], Awaitable[None]]] = []
        self._unsubscription_handlers: list[Callable[[str, str], Awaitable[None]]] = []
        self._message_handlers: list[Callable[[str, str, Any], Awaitable[None]]] = []

    @property
    def subscriber_count(self) -> int:
        """Get current number of subscribers."""
        return len(self._subscribers)

    @property
    def subscribers(self) -> set[str]:
        """Get set of subscriber session IDs."""
        return self._subscribers.copy()

    def add_subscription_handler(self, handler: Callable[[str, str], Awaitable[None]]):
        """Add handler for subscription events."""
        self._subscription_handlers.append(handler)

    def add_unsubscription_handler(self, handler: Callable[[str, str], Awaitable[None]]):
        """Add handler for unsubscription events."""
        self._unsubscription_handlers.append(handler)

    def add_message_handler(self, handler: Callable[[str, str, Any], Awaitable[None]]):
        """Add handler for message events."""
        self._message_handlers.append(handler)

    async def subscribe(self, session_id: str) -> bool:
        """Subscribe a session to this channel."""
        if (
            self.metadata.max_subscribers
            and len(self._subscribers) >= self.metadata.max_subscribers
        ):
            logger.warning(
                f"Channel {self.name} at max subscribers ({self.metadata.max_subscribers})"
            )
            return False

        if session_id not in self._subscribers:
            self._subscribers.add(session_id)

            # Update statistics
            if len(self._subscribers) > self.metadata.peak_subscribers:
                self.metadata.peak_subscribers = len(self._subscribers)

            # Call subscription handlers
            for handler in self._subscription_handlers:
                try:
                    await handler(self.name, session_id)
                except Exception as e:
                    logger.error(f"Subscription handler error: {e}")

            logger.debug(f"Session {session_id} subscribed to channel {self.name}")
            return True

        return False

    async def unsubscribe(self, session_id: str) -> bool:
        """Unsubscribe a session from this channel."""
        if session_id in self._subscribers:
            self._subscribers.remove(session_id)

            # Call unsubscription handlers
            for handler in self._unsubscription_handlers:
                try:
                    await handler(self.name, session_id)
                except Exception as e:
                    logger.error(f"Unsubscription handler error: {e}")

            logger.debug(f"Session {session_id} unsubscribed from channel {self.name}")
            return True

        return False

    async def add_message(self, message_type: str, data: Any, sender_id: Optional[str] = None):
        """Add a message to the channel history."""
        message = {
            "type": message_type,
            "data": data,
            "sender_id": sender_id,
            "timestamp": time.time(),
            "channel": self.name,
        }

        # Add to history
        if self.metadata.message_history > 0:
            self._message_history.append(message)

            # Trim history if needed
            if len(self._message_history) > self.metadata.message_history:
                self._message_history = self._message_history[-self.metadata.message_history :]

        # Update statistics
        self.metadata.total_messages += 1
        self.metadata.last_activity = time.time()

        # Call message handlers
        for handler in self._message_handlers:
            try:
                await handler(self.name, message_type, data)
            except Exception as e:
                logger.error(f"Message handler error: {e}")

    def get_message_history(self, limit: Optional[int] = None) -> list[dict[str, Any]]:
        """Get channel message history."""
        if limit:
            return self._message_history[-limit:]
        return self._message_history.copy()

    @abstractmethod
    async def broadcast(
        self, message_type: str, data: Any, exclude_session: Optional[str] = None
    ) -> int:
        """Broadcast message to all subscribers."""
        pass

    def is_empty(self) -> bool:
        """Check if channel has no subscribers."""
        return len(self._subscribers) == 0

    def should_persist(self) -> bool:
        """Check if channel should persist when empty."""
        return self.metadata.persistent

    def to_dict(self) -> dict[str, Any]:
        """Convert channel to dictionary."""
        return {
            "name": self.name,
            "subscriber_count": self.subscriber_count,
            "subscribers": list(self.subscribers),
            "metadata": {
                "created_at": self.metadata.created_at,
                "description": self.metadata.description,
                "public": self.metadata.public,
                "tenant_id": self.metadata.tenant_id,
                "required_roles": self.metadata.required_roles,
                "required_permissions": self.metadata.required_permissions,
                "persistent": self.metadata.persistent,
                "max_subscribers": self.metadata.max_subscribers,
                "message_history": self.metadata.message_history,
                "total_messages": self.metadata.total_messages,
                "peak_subscribers": self.metadata.peak_subscribers,
                "last_activity": self.metadata.last_activity,
                "custom_data": self.metadata.custom_data,
            },
            "message_history_count": len(self._message_history),
        }

class ChannelManager(ABC):
    """Abstract base class for channel managers."""

    @abstractmethod
    async def create_channel(
        self, name: str, metadata: Optional[ChannelMetadata] = None
    ) -> Channel:
        """Create a new channel."""
        pass

    @abstractmethod
    async def get_channel(self, name: str) -> Optional[Channel]:
        """Get a channel by name."""
        pass

    @abstractmethod
    async def delete_channel(self, name: str) -> bool:
        """Delete a channel."""
        pass

    @abstractmethod
    async def list_channels(self, tenant_id: Optional[str] = None) -> list[str]:
        """List all channels, optionally filtered by tenant."""
        pass

    @abstractmethod
    async def subscribe_session(self, session, channel_name: str) -> bool:
        """Subscribe a session to a channel."""
        pass

    @abstractmethod
    async def unsubscribe_session(self, session, channel_name: str) -> bool:
        """Unsubscribe a session from a channel."""
        pass

    @abstractmethod
    async def broadcast_to_channel(
        self,
        channel_name: str,
        message_type: str,
        data: Any = None,
        exclude_session: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> int:
        """Broadcast message to all subscribers of a channel."""
        pass

    @abstractmethod
    async def get_channel_subscribers(self, channel_name: str) -> list[str]:
        """Get list of subscribers for a channel."""
        pass

    @abstractmethod
    async def get_session_channels(self, session_id: str) -> list[str]:
        """Get list of channels a session is subscribed to."""
        pass

    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        """Get channel manager statistics."""
        pass

    @abstractmethod
    async def cleanup_empty_channels(self):
        """Clean up empty channels that don't need to persist."""
        pass

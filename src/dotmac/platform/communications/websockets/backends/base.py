"""
Base scaling backend interface.
"""

from abc import ABC, abstractmethod
from typing import Any


class ScalingBackend(ABC):
    """Base class for WebSocket scaling backends."""

    @abstractmethod
    async def start(self):
        """Start the scaling backend."""
        pass

    @abstractmethod
    async def stop(self):
        """Stop the scaling backend."""
        pass

    @abstractmethod
    async def broadcast_to_user(self, user_id: str, message_type: str, data: Any = None):
        """Broadcast message to all instances for a specific user."""
        pass

    @abstractmethod
    async def broadcast_to_tenant(self, tenant_id: str, message_type: str, data: Any = None):
        """Broadcast message to all instances for a specific tenant."""
        pass

    @abstractmethod
    async def broadcast_to_channel(self, channel_name: str, message_type: str, data: Any = None):
        """Broadcast message to all instances for a specific channel."""
        pass

    @abstractmethod
    async def send_to_session(self, session_id: str, message_type: str, data: Any = None) -> bool:
        """Send message to a specific session across all instances."""
        pass

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Perform health check of the scaling backend."""
        pass

    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        """Get scaling backend statistics."""
        pass

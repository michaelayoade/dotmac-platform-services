"""
Local scaling backend (no-op for single instance).
"""

import time
from typing import Any, Optional

from .base import ScalingBackend


class LocalBackend(ScalingBackend):
    """Local backend - no scaling, single instance only."""

    def __init__(self):
        self._started = False
        self._start_time: Optional[float] = None

    async def start(self):
        """Start the local backend."""
        self._started = True
        self._start_time = time.time()

    async def stop(self):
        """Stop the local backend."""
        self._started = False
        self._start_time = None

    async def broadcast_to_user(self, user_id: str, message_type: str, data: Any = None):
        """No-op for local backend - broadcasting handled by session manager."""
        pass

    async def broadcast_to_tenant(self, tenant_id: str, message_type: str, data: Any = None):
        """No-op for local backend - broadcasting handled by session manager."""
        pass

    async def broadcast_to_channel(self, channel_name: str, message_type: str, data: Any = None):
        """No-op for local backend - broadcasting handled by channel manager."""
        pass

    async def send_to_session(self, session_id: str, message_type: str, data: Any = None) -> bool:
        """No-op for local backend - session handled locally."""
        return False

    async def health_check(self) -> dict[str, Any]:
        """Health check for local backend."""
        return {
            "status": "healthy" if self._started else "stopped",
            "backend_type": "local",
            "uptime_seconds": time.time() - self._start_time if self._start_time else 0,
        }

    def get_stats(self) -> dict[str, Any]:
        """Get local backend statistics."""
        return {
            "backend_type": "local",
            "started": self._started,
            "uptime_seconds": time.time() - self._start_time if self._start_time else 0,
            "instances": 1,
            "message_routing": "local_only",
        }

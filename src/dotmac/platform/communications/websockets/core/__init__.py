"""
Core WebSocket components.
"""

from dotmac.platform.settings import settings, RedisConfig, WebSocketConfig
from .gateway import WebSocketGateway
from .session import SessionManager, SessionState, WebSocketSession

__all__ = [
    "WebSocketConfig",
    "RedisConfig",
    "AuthConfig",
    "SessionManager",
    "WebSocketSession",
    "SessionState",
    "WebSocketGateway",
]

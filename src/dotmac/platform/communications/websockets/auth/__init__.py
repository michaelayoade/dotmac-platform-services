"""
Authentication components for WebSocket gateway.
"""

from .manager import AuthManager
from .types import AuthResult, UserInfo

try:
    from .middleware import AuthMiddleware
except ImportError:
    AuthMiddleware = None

__all__ = [
    "AuthResult",
    "UserInfo",
    "AuthManager",
    "AuthMiddleware",  # May be None if JWT not available
]

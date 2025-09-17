"""
DotMac WebSocket Gateway Package.

A comprehensive WebSocket solution with:
- Multi-tenant session management
- Horizontal scaling with Redis pub/sub
- Channel abstractions and broadcast utilities
- Authentication and authorization middleware
- Observability and health monitoring integration
- FastAPI integration for HTTP endpoints
"""

from .auth.manager import AuthManager
from .auth.middleware import AuthMiddleware
from .auth.types import AuthResult, UserInfo
from .backends.local import LocalBackend
from .backends.redis import RedisScalingBackend
from .channels.abstractions import Channel, ChannelManager
from .channels.broadcast import BroadcastManager
from .core.config import AuthConfig, RedisConfig, WebSocketConfig
from .core.gateway import WebSocketGateway
from .core.session import SessionManager, WebSocketSession
from .middleware.rate_limit import RateLimitMiddleware
from .middleware.tenant import TenantMiddleware

try:
    from .observability.health import WebSocketHealthCheck
    from .observability.hooks import (
        WebSocketObservabilityHooks,
        create_default_hooks,
        create_dotmac_observability_hooks,
    )
except ImportError:
    # Observability not available
    create_default_hooks = None
    create_dotmac_observability_hooks = None
    WebSocketObservabilityHooks = None
    WebSocketHealthCheck = None

# Try to import FastAPI integration (optional)
try:
    from .integrations.fastapi import FastAPIWebSocketIntegration, create_fastapi_websocket_app
except ImportError:
    # FastAPI not available
    create_fastapi_websocket_app = None
    FastAPIWebSocketIntegration = None

__version__ = "1.0.0"
__author__ = "DotMac Team"
__email__ = "dev@dotmac.com"

__all__ = [
    # Core components
    "WebSocketGateway",
    "SessionManager",
    "WebSocketSession",
    "WebSocketConfig",
    "RedisConfig",
    "AuthConfig",
    # Channel system
    "Channel",
    "ChannelManager",
    "BroadcastManager",
    # Authentication
    "AuthManager",
    "AuthMiddleware",
    "AuthResult",
    "UserInfo",
    # Backends
    "RedisScalingBackend",
    "LocalBackend",
    # Middleware
    "TenantMiddleware",
    "RateLimitMiddleware",
    # Observability (may be None if not available)
    "create_default_hooks",
    "create_dotmac_observability_hooks",
    "WebSocketObservabilityHooks",
    "WebSocketHealthCheck",
    # FastAPI integration (may be None if not available)
    "create_fastapi_websocket_app",
    "FastAPIWebSocketIntegration",
]

"""
Observability components for WebSocket gateway.
"""

try:
    from .health import WebSocketHealthCheck
    from .hooks import (
        WebSocketObservabilityHooks,
        create_default_hooks,
        create_dotmac_observability_hooks,
    )
    from .metrics import WebSocketMetrics

    OBSERVABILITY_AVAILABLE = True
except ImportError:
    # Observability dependencies not available
    create_default_hooks = None
    create_dotmac_observability_hooks = None
    WebSocketObservabilityHooks = None
    WebSocketHealthCheck = None
    WebSocketMetrics = None

    OBSERVABILITY_AVAILABLE = False

__all__ = [
    "create_default_hooks",
    "create_dotmac_observability_hooks",
    "WebSocketObservabilityHooks",
    "WebSocketHealthCheck",
    "WebSocketMetrics",
    "OBSERVABILITY_AVAILABLE",
]

"""
API Gateway Service - Request routing, rate limiting, and versioning.

Provider-agnostic API management without vendor lock-in.
"""


from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

from .interfaces import RateLimiter, VersionStrategy, RateLimitConfig  # lightweight
from .config import GatewayConfig  # unified config
from .validation import RequestValidator, ValidationMiddleware, ValidationLevel

# ObservabilityManager removed - replaced with unified analytics
from .factory import create_gateway, setup_gateway_app
from .analytics_integration import APIGatewayAnalyticsAdapter, get_gateway_analytics

# Optional imports guarded to avoid hard dependency at package import time
try:
    from .gateway import APIGateway
except Exception as e:  # pragma: no cover - optional
    APIGateway = None
    logger.debug(f"APIGateway not available: {e}")

try:
    from .rate_limiting import (
        TokenBucketLimiter,
        SlidingWindowLimiter,
        FixedWindowLimiter,
    )
except Exception as e:  # pragma: no cover - optional
    TokenBucketLimiter = SlidingWindowLimiter = FixedWindowLimiter = None  # type: ignore
    logger.debug(f"Rate limiting implementations not available: {e}")

try:
    from .versioning import HeaderVersioning, PathVersioning, QueryVersioning
except Exception as e:  # pragma: no cover - optional
    HeaderVersioning = PathVersioning = QueryVersioning = None  # type: ignore
    logger.debug(f"Versioning strategies not available: {e}")

__all__ = [
    "RateLimiter",
    "VersionStrategy",
    "RateLimitConfig",
    "GatewayConfig",
    "RequestValidator",
    "ValidationMiddleware",
    "ValidationLevel",
    "APIGatewayAnalyticsAdapter",
    "get_gateway_analytics",
    "create_gateway",
    "setup_gateway_app",
]
if APIGateway is not None:
    __all__.append("APIGateway")

# Add rate limiting classes if available
if TokenBucketLimiter is not None:
    __all__.extend(["TokenBucketLimiter", "SlidingWindowLimiter", "FixedWindowLimiter"])

# Add versioning classes if available
if HeaderVersioning is not None:
    __all__.extend(["HeaderVersioning", "PathVersioning", "QueryVersioning"])

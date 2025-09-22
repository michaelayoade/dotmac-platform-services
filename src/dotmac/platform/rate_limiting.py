"""
Simple rate limiting using SlowAPI standard library.

Replaces custom rate limiting implementations with industry standard.
"""

from typing import Callable

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False
    Limiter = None
    RateLimitExceeded = None
    get_remote_address = None
    _rate_limit_exceeded_handler = None

from dotmac.platform.caching import redis_client
from dotmac.platform.logging import get_logger

logger = get_logger(__name__)


def get_limiter():
    """Get rate limiter instance using Redis storage."""
    if not SLOWAPI_AVAILABLE:
        logger.warning("SlowAPI not available")
        return None

    if redis_client:
        # Use Redis for distributed rate limiting
        storage_uri = f"redis://:{redis_client.connection_pool.connection_kwargs.get('password', '')}@{redis_client.connection_pool.connection_kwargs.get('host', 'localhost')}:{redis_client.connection_pool.connection_kwargs.get('port', 6379)}"
        return Limiter(
            key_func=get_remote_address,
            storage_uri=storage_uri,
        )
    else:
        # Use in-memory storage (development only)
        logger.warning("Using in-memory rate limiting - not suitable for production")
        return Limiter(key_func=get_remote_address)


# Global limiter instance
limiter = get_limiter()


def rate_limit(limit: str):
    """
    Rate limiting decorator using SlowAPI.

    Args:
        limit: Rate limit string (e.g., "100/minute", "10/second")

    Example:
        @rate_limit("100/minute")
        async def my_endpoint():
            return {"message": "success"}
    """
    def decorator(func: Callable):
        if not SLOWAPI_AVAILABLE or not limiter:
            logger.warning("Rate limiting not available, skipping")
            return func

        return limiter.limit(limit)(func)

    return decorator


# Export standard SlowAPI components if available
__all__ = [
    "limiter",
    "rate_limit",
    "RateLimitExceeded",
    "get_remote_address",
    "_rate_limit_exceeded_handler"
]

if SLOWAPI_AVAILABLE:
    # Re-export SlowAPI utilities
    pass
else:
    # Provide no-op fallbacks
    def rate_limit(limit: str):
        def decorator(func: Callable):
            return func
        return decorator

    class RateLimitExceeded(Exception):
        pass

    def get_remote_address(request):
        return "127.0.0.1"

    def _rate_limit_exceeded_handler(request, exc):
        return {"error": "Rate limit exceeded"}
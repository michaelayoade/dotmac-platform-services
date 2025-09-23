"""
Simple rate limiting using SlowAPI standard library.

Replaces custom rate limiting implementations with industry standard.
"""

from typing import Callable

import structlog
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from dotmac.platform.caching import redis_client

logger = structlog.get_logger(__name__)


def get_limiter():
    """Get rate limiter instance using Redis storage."""
    if redis_client:
        # Use Redis for distributed rate limiting - get URL from settings
        from dotmac.platform.settings import settings

        storage_uri = settings.redis.cache_url
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
        return limiter.limit(limit)(func)

    return decorator


# Export SlowAPI components directly - use established library
__all__ = [
    "limiter",
    "rate_limit",
    "RateLimitExceeded",
    "get_remote_address",
    "_rate_limit_exceeded_handler",
]

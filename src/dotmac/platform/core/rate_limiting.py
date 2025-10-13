"""
Simple rate limiting using SlowAPI standard library.

Replaces custom rate limiting implementations with industry standard.
"""

from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar, cast

import structlog
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from dotmac.platform.core.caching import redis_client

logger = structlog.get_logger(__name__)


_limiter: Limiter | None = None


def _create_limiter() -> Limiter:
    """Create a limiter instance using the best available storage backend."""
    from dotmac.platform.settings import settings

    storage_uri = settings.rate_limit.storage_url
    client = redis_client
    enabled = settings.rate_limit.enabled

    if not storage_uri and client:
        storage_uri = settings.redis.cache_url

    if storage_uri:
        logger.debug("rate_limit.storage.initialized", storage=storage_uri)
        return Limiter(key_func=get_remote_address, storage_uri=storage_uri, enabled=enabled)

    logger.warning(
        "rate_limit.storage.memory",
        message="Falling back to in-memory rate limiting; enable Redis for production",
    )
    return Limiter(key_func=get_remote_address, enabled=enabled)


def get_limiter() -> Limiter:
    """Return the shared rate limiter instance, creating it lazily if needed."""
    global _limiter
    if _limiter is None:
        _limiter = _create_limiter()
    return _limiter


def reset_limiter() -> None:
    """Reset the cached limiter instance and clear storage (useful for tests)."""
    global _limiter
    if _limiter is not None:
        # Clear the storage to reset rate limit counters
        try:
            if hasattr(_limiter, "_storage") and _limiter._storage:
                # SlowAPI storage has a reset() method in some implementations
                if hasattr(_limiter._storage, "reset"):
                    _limiter._storage.reset()
                # Note: clear() method requires a key parameter, so we skip it for global reset
        except Exception as e:
            logger.debug("rate_limit.storage.reset.failed", error=str(e))
    _limiter = None


P = ParamSpec("P")
R = TypeVar("R")


class _LimiterProxy:
    """Lazy proxy so existing imports continue to work."""

    def __getattr__(self, item: str) -> Any:
        return getattr(get_limiter(), item)


limiter = _LimiterProxy()


def rate_limit(limit: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Rate limiting decorator using SlowAPI.

    Args:
        limit: Rate limit string (e.g., "100/minute", "10/second")

    Example:
        @rate_limit("100/minute")
        async def my_endpoint():
            return {"message": "success"}
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        limited_callable = get_limiter().limit(limit)(func)
        return cast(Callable[P, R], limited_callable)

    return decorator


# Export SlowAPI components directly - use established library
__all__ = [
    "limiter",
    "get_limiter",
    "reset_limiter",
    "rate_limit",
    "RateLimitExceeded",
    "get_remote_address",
    "_rate_limit_exceeded_handler",
]

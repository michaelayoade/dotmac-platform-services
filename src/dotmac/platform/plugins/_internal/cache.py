"""
No-op cache service implementation for optional dependency.
"""

import asyncio

from typing import Any, Optional

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

class NoOpCacheService:
    """No-op cache service that does nothing but logs operations."""

    def __init__(self):
        logger.debug("Initialized no-op cache service")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (no-op)."""
        logger.debug(f"Cache get: {key} (no-op)")
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache (no-op)."""
        logger.debug(f"Cache set: {key} (no-op)")

    async def delete(self, key: str) -> None:
        """Delete value from cache (no-op)."""
        logger.debug(f"Cache delete: {key} (no-op)")

    async def clear(self) -> None:
        """Clear all cache entries (no-op)."""
        logger.debug("Cache clear (no-op)")

def get_cache_service() -> NoOpCacheService:
    """Get the cache service instance."""
    return NoOpCacheService()

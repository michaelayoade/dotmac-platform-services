"""Cache backend interfaces."""

from abc import ABC, abstractmethod
from typing import Any


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the cache backend."""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from the cache backend."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if backend is connected."""
        pass

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set value in cache with optional TTL."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """Clear all keys from cache."""
        pass

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        pass

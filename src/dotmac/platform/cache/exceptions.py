"""Cache-related exceptions."""


class CacheError(Exception):
    """Base exception for cache operations."""

    pass


class CacheConnectionError(CacheError):
    """Raised when cache backend connection fails."""

    pass


class CacheKeyError(CacheError):
    """Raised when cache key is invalid or not found."""

    pass
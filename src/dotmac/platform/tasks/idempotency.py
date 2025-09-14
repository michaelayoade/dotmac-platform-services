"""Idempotency utilities for ensuring operations run exactly once."""

from __future__ import annotations

import functools
import hashlib
import json
import logging
from typing import Any, Callable, TypeVar

from ..cache import CacheService

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])
AsyncF = TypeVar("AsyncF", bound=Callable[..., Any])


class IdempotencyError(Exception):
    """Raised when idempotency operations fail."""


def generate_idempotency_key(*args: Any, **kwargs: Any) -> str:
    """
    Generate a deterministic key from function arguments.

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        SHA256 hash of serialized arguments
    """
    # Create a deterministic representation of arguments
    key_data = {
        "args": args,
        "kwargs": dict(sorted(kwargs.items())),  # Sort for consistency
    }

    try:
        # Serialize to JSON for hashing
        serialized = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()
    except (TypeError, ValueError):
        # Fallback for non-JSON serializable arguments
        fallback = f"args:{len(args)}_kwargs:{len(kwargs)}_{hash(str(args))}_{hash(str(kwargs))}"
        return hashlib.sha256(fallback.encode()).hexdigest()


def idempotent(
    cache_service: CacheService | None = None,
    key: str | Callable[..., str] | None = None,
    ttl: int = 3600,
    include_result: bool = True,
    key_prefix: str = "idempotent:",
) -> Callable[[AsyncF], AsyncF]:
    """
    Async decorator for idempotent operations using cache service.

    Args:
        cache_service: Cache service for storing idempotency data
        key: Static key, key generator function, or None for auto-generation
        ttl: Time-to-live for stored results in seconds
        include_result: Whether to store and return cached results
        key_prefix: Prefix for cache keys

    Returns:
        Decorated function that ensures idempotent execution

    Example:
        @idempotent(cache_service, key="user_signup", ttl=300)
        async def signup_user(email: str):
            # This will only run once per email within 300 seconds
            return await create_user_account(email)

    Or with dependency injection:
        @idempotent(ttl=300)
        async def process_payment(payment_id: str, _cache: CacheService):
            # Cache service passed as parameter
            return await payment_gateway.process(payment_id)
    """

    def decorator(func: AsyncF) -> AsyncF:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get cache service from parameter or decorator argument
            _cache = cache_service or kwargs.pop("_cache", None)
            if not _cache:
                logger.warning(
                    "No cache service provided for idempotent function %s, "
                    "executing without idempotency",
                    func.__name__,
                )
                return await func(*args, **kwargs)

            # Generate idempotency key
            if callable(key):
                idem_key = key(*args, **kwargs)
            elif key is not None:
                idem_key = key
            else:
                # Auto-generate key from function name and arguments
                func_name = f"{func.__module__}.{func.__qualname__}"
                arg_key = generate_idempotency_key(*args, **kwargs)
                idem_key = f"{func_name}:{arg_key}"

            # Add prefix
            full_key = f"{key_prefix}{idem_key}"

            # Check if operation was already performed
            if await _cache.exists(full_key):
                if include_result:
                    cached_result = await _cache.get(full_key)
                    if cached_result is not None:
                        logger.debug(
                            "Idempotent operation %s already performed, "
                            "returning cached result",
                            func.__name__,
                        )
                        return cached_result["result"]
                else:
                    logger.debug(
                        "Idempotent operation %s already performed, skipping",
                        func.__name__,
                    )
                    return None

            # Perform the operation
            logger.debug("Executing idempotent operation %s", func.__name__)
            try:
                result = await func(*args, **kwargs)
            except Exception as e:
                # Don't cache failures
                logger.error(
                    "Idempotent operation %s failed: %s",
                    func.__name__,
                    str(e),
                )
                raise

            # Store the result or marker
            if include_result:
                await _cache.set(full_key, {"result": result}, ttl)
            else:
                # Store a marker indicating operation was performed
                await _cache.set(full_key, {"performed": True}, ttl)

            return result

        # Store decorator parameters for inspection
        wrapper._idempotent = True
        wrapper._idempotent_ttl = ttl
        wrapper._idempotent_key_prefix = key_prefix

        return wrapper  # type: ignore

    return decorator


def idempotent_sync(
    cache_service: Any | None = None,
    key: str | Callable[..., str] | None = None,
    ttl: int = 3600,
    include_result: bool = True,
    key_prefix: str = "idempotent:",
) -> Callable[[F], F]:
    """
    Synchronous decorator for idempotent operations.

    Note: This requires a synchronous cache backend, which is not
    implemented in the async-first platform-services. Consider using
    the async version instead.

    Args:
        cache_service: Cache service for storing idempotency data
        key: Static key, key generator function, or None for auto-generation
        ttl: Time-to-live for stored results in seconds
        include_result: Whether to store and return cached results
        key_prefix: Prefix for cache keys

    Returns:
        Decorated function that ensures idempotent execution
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger.warning(
                "Synchronous idempotency not fully supported in async-first "
                "platform. Consider using async version for %s",
                func.__name__,
            )
            # For now, just execute the function
            return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


class IdempotencyManager:
    """
    Context manager for manual idempotency control.

    Example:
        async with IdempotencyManager(cache_service, "operation_123") as mgr:
            if not mgr.already_performed:
                result = await perform_operation()
                await mgr.set_result(result)
            else:
                result = mgr.cached_result
    """

    def __init__(
        self,
        cache_service: CacheService,
        key: str,
        ttl: int = 3600,
        include_result: bool = True,
        key_prefix: str = "idempotent:",
    ):
        self.cache_service = cache_service
        self.key = f"{key_prefix}{key}"
        self.ttl = ttl
        self.include_result = include_result
        self.already_performed = False
        self.cached_result = None

    async def __aenter__(self) -> IdempotencyManager:
        # Check if operation was already performed
        if await self.cache_service.exists(self.key):
            self.already_performed = True
            if self.include_result:
                data = await self.cache_service.get(self.key)
                if data and "result" in data:
                    self.cached_result = data["result"]
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Don't cache if there was an exception
        if exc_type is not None:
            return False
        return None

    async def set_result(self, result: Any) -> None:
        """Store the result of the operation."""
        if self.include_result:
            await self.cache_service.set(self.key, {"result": result}, self.ttl)
        else:
            await self.cache_service.set(self.key, {"performed": True}, self.ttl)

    async def mark_performed(self) -> None:
        """Mark the operation as performed without storing result."""
        await self.cache_service.set(self.key, {"performed": True}, self.ttl)
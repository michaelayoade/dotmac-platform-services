"""
Standalone decorators for the notifications package
Replaces dependencies on dotmac_shared decorators
"""

import asyncio

import time
from collections import defaultdict
from collections.abc import Callable
from functools import wraps
from typing import Any, Optional

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

class RateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self):
        self._calls: dict[str, list] = defaultdict(list)

    def is_allowed(self, key: str, max_calls: int, time_window: int) -> bool:
        """Check if a call is allowed within rate limits"""
        now = time.time()
        window_start = now - time_window

        # Clean old entries
        self._calls[key] = [call_time for call_time in self._calls[key] if call_time > window_start]

        # Check if under limit
        if len(self._calls[key]) >= max_calls:
            return False

        # Record this call
        self._calls[key].append(now)
        return True

# Global rate limiter instance
_rate_limiter = RateLimiter()

def rate_limit(max_calls: int = 100, time_window: int = 60, key_func: Optional[Callable] = None):
    """
    Rate limiting decorator

    Args:
        max_calls: Maximum number of calls allowed
        time_window: Time window in seconds
        key_func: Function to generate rate limiting key
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # Generate rate limit key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                # Default key based on function name and first arg (if any)
                key = f"{func.__name__}:{args[0] if args else 'global'}"

            if not _rate_limiter.is_allowed(key, max_calls, time_window):
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: {max_calls} calls per {time_window} seconds",
                )

            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # Generate rate limit key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = f"{func.__name__}:{args[0] if args else 'global'}"

            if not _rate_limiter.is_allowed(key, max_calls, time_window):
                raise Exception(f"Rate limit exceeded: {max_calls} calls per {time_window} seconds")

            return func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator

def standard_exception_handler(func: Callable) -> Callable:
    """
    Standard exception handler decorator
    Replaces dotmac_shared.api.exception_handlers.standard_exception_handler
    """

    @wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Exception in {func.__name__}: {e}", exc_info=True)
            # Re-raise the exception - let the calling code handle it
            raise

    @wraps(func)
    def sync_wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Exception in {func.__name__}: {e}", exc_info=True)
            raise

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

def retry_on_failure(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Retry decorator for handling transient failures

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for delay
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        # Last attempt, re-raise
                        break

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {current_delay}s..."
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

            raise last_exception

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        break

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {current_delay}s..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff

            raise last_exception

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator

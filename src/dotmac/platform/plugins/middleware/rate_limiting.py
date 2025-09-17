"""
Rate limiting middleware for plugin execution.

Implements various rate limiting strategies to prevent plugin abuse and ensure fair resource usage.
"""


import time
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from ..core.exceptions import PluginError
from ..core.plugin_base import BasePlugin

from dotmac.platform.observability.unified_logging import get_logger
class RateLimitStrategy(Enum):
    """Rate limiting strategies."""

    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"

@dataclass
class RateLimit:
    """Rate limit configuration."""

    max_requests: int
    time_window: int  # seconds
    strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET
    burst_allowance: Optional[int] = None
    per_user: bool = False
    user_key_extractor: Optional[callable] = None

class RateLimiter(ABC):
    """Abstract base class for rate limiters."""

    def __init__(self, config: RateLimit):
        self.config = config
        self._logger = get_logger(f"plugins.rate_limiter.{self.__class__.__name__}")

    @abstractmethod
    async def is_allowed(self, key: str) -> tuple[bool, dict[str, Any]]:
        """
        Check if request is allowed.

        Args:
            key: Rate limiting key (plugin or user-specific)

        Returns:
            Tuple of (allowed, metadata) where metadata contains remaining requests, reset time, etc.
        """
        pass

    @abstractmethod
    def get_stats(self, key: str) -> dict[str, Any]:
        """Get rate limiting statistics for a key."""
        pass

    @abstractmethod
    def reset(self, key: str) -> None:
        """Reset rate limiting for a key."""
        pass

class TokenBucketLimiter(RateLimiter):
    """
    Token bucket rate limiter.

    Allows burst traffic up to bucket capacity, then limits to refill rate.
    """

    def __init__(self, config: RateLimit):
        super().__init__(config)
        self._buckets: dict[str, dict[str, float]] = defaultdict(
            lambda: {"tokens": config.max_requests, "last_refill": time.time()}
        )
        self._refill_rate = config.max_requests / config.time_window

    async def is_allowed(self, key: str) -> tuple[bool, dict[str, Any]]:
        """Check if request is allowed using token bucket algorithm."""
        current_time = time.time()
        bucket = self._buckets[key]

        # Refill tokens based on elapsed time
        elapsed = current_time - bucket["last_refill"]
        tokens_to_add = elapsed * self._refill_rate
        bucket["tokens"] = min(self.config.max_requests, bucket["tokens"] + tokens_to_add)
        bucket["last_refill"] = current_time

        # Check if request can be allowed
        if bucket["tokens"] >= 1.0:
            bucket["tokens"] -= 1.0
            allowed = True
        else:
            allowed = False

        # Calculate metadata
        remaining = int(bucket["tokens"])
        reset_time = (
            current_time + (self.config.max_requests - bucket["tokens"]) / self._refill_rate
        )

        metadata = {
            "remaining": remaining,
            "reset_time": reset_time,
            "retry_after": 1.0 / self._refill_rate if not allowed else None,
        }

        return allowed, metadata

    def get_stats(self, key: str) -> dict[str, Any]:
        """Get token bucket statistics."""
        bucket = self._buckets.get(
            key, {"tokens": self.config.max_requests, "last_refill": time.time()}
        )
        return {
            "strategy": "token_bucket",
            "tokens_available": int(bucket["tokens"]),
            "max_tokens": self.config.max_requests,
            "refill_rate": self._refill_rate,
            "last_refill": bucket["last_refill"],
        }

    def reset(self, key: str) -> None:
        """Reset token bucket for a key."""
        if key in self._buckets:
            self._buckets[key] = {
                "tokens": self.config.max_requests,
                "last_refill": time.time(),
            }

class SlidingWindowLimiter(RateLimiter):
    """
    Sliding window rate limiter.

    Tracks requests in a sliding time window for precise rate limiting.
    """

    def __init__(self, config: RateLimit):
        super().__init__(config)
        self._windows: dict[str, deque] = defaultdict(deque)

    async def is_allowed(self, key: str) -> tuple[bool, dict[str, Any]]:
        """Check if request is allowed using sliding window algorithm."""
        current_time = time.time()
        window = self._windows[key]

        # Remove expired requests from window
        cutoff_time = current_time - self.config.time_window
        while window and window[0] <= cutoff_time:
            window.popleft()

        # Check if request can be allowed
        if len(window) < self.config.max_requests:
            window.append(current_time)
            allowed = True
        else:
            allowed = False

        # Calculate metadata
        remaining = self.config.max_requests - len(window)
        oldest_request = window[0] if window else current_time
        reset_time = oldest_request + self.config.time_window

        metadata = {
            "remaining": remaining,
            "reset_time": reset_time,
            "requests_in_window": len(window),
            "retry_after": reset_time - current_time if not allowed else None,
        }

        return allowed, metadata

    def get_stats(self, key: str) -> dict[str, Any]:
        """Get sliding window statistics."""
        window = self._windows.get(key, deque())
        current_time = time.time()

        # Clean up expired requests for accurate stats
        cutoff_time = current_time - self.config.time_window
        active_requests = sum(1 for req_time in window if req_time > cutoff_time)

        return {
            "strategy": "sliding_window",
            "requests_in_window": active_requests,
            "max_requests": self.config.max_requests,
            "window_size": self.config.time_window,
            "remaining": self.config.max_requests - active_requests,
        }

    def reset(self, key: str) -> None:
        """Reset sliding window for a key."""
        if key in self._windows:
            self._windows[key].clear()

class FixedWindowLimiter(RateLimiter):
    """
    Fixed window rate limiter.

    Divides time into fixed windows and limits requests per window.
    """

    def __init__(self, config: RateLimit):
        super().__init__(config)
        self._windows: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"count": 0, "window_start": 0}
        )

    async def is_allowed(self, key: str) -> tuple[bool, dict[str, Any]]:
        """Check if request is allowed using fixed window algorithm."""
        current_time = time.time()
        window_start = int(current_time // self.config.time_window) * self.config.time_window

        window = self._windows[key]

        # Reset window if we're in a new time window
        if window["window_start"] != window_start:
            window["count"] = 0
            window["window_start"] = window_start

        # Check if request can be allowed
        if window["count"] < self.config.max_requests:
            window["count"] += 1
            allowed = True
        else:
            allowed = False

        # Calculate metadata
        remaining = self.config.max_requests - window["count"]
        reset_time = window_start + self.config.time_window

        metadata = {
            "remaining": remaining,
            "reset_time": reset_time,
            "requests_in_window": window["count"],
            "window_start": window_start,
            "retry_after": reset_time - current_time if not allowed else None,
        }

        return allowed, metadata

    def get_stats(self, key: str) -> dict[str, Any]:
        """Get fixed window statistics."""
        window = self._windows.get(key, {"count": 0, "window_start": 0})
        current_time = time.time()
        window_start = int(current_time // self.config.time_window) * self.config.time_window

        # Check if window has expired
        if window["window_start"] != window_start:
            current_count = 0
        else:
            current_count = window["count"]

        return {
            "strategy": "fixed_window",
            "requests_in_window": current_count,
            "max_requests": self.config.max_requests,
            "window_size": self.config.time_window,
            "remaining": self.config.max_requests - current_count,
            "window_start": window_start,
        }

    def reset(self, key: str) -> None:
        """Reset fixed window for a key."""
        if key in self._windows:
            self._windows[key] = {"count": 0, "window_start": 0}

class RateLimitingMiddleware:
    """
    Plugin rate limiting middleware.

    Applies rate limits to plugin method executions to prevent abuse and ensure fair resource usage.
    """

    def __init__(self):
        self._limiters: dict[str, RateLimiter] = {}  # plugin_key -> limiter
        self._global_limiters: dict[str, RateLimiter] = {}  # method_name -> limiter
        self._user_limiters: dict[str, dict[str, RateLimiter]] = (
            {}
        )  # user_id -> plugin_key -> limiter

        # Statistics
        self._stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "allowed_requests": 0,
            "rate_limited_plugins": set(),
            "rate_limited_users": set(),
        }

        self._logger = get_logger("plugins.rate_limiting_middleware")

    def add_plugin_rate_limit(self, plugin_key: str, rate_limit: RateLimit) -> None:
        """
        Add rate limit for a specific plugin.

        Args:
            plugin_key: Plugin key in format "domain.name"
            rate_limit: Rate limit configuration
        """
        limiter = self._create_limiter(rate_limit)
        self._limiters[plugin_key] = limiter

        self._logger.info(
            f"Added rate limit for plugin {plugin_key}: "
            f"{rate_limit.max_requests} requests per {rate_limit.time_window}s"
        )

    def add_method_rate_limit(self, method_name: str, rate_limit: RateLimit) -> None:
        """
        Add global rate limit for a method across all plugins.

        Args:
            method_name: Method name to rate limit
            rate_limit: Rate limit configuration
        """
        limiter = self._create_limiter(rate_limit)
        self._global_limiters[method_name] = limiter

        self._logger.info(
            f"Added global rate limit for method {method_name}: "
            f"{rate_limit.max_requests} requests per {rate_limit.time_window}s"
        )

    def remove_plugin_rate_limit(self, plugin_key: str) -> None:
        """Remove rate limit for a plugin."""
        if plugin_key in self._limiters:
            del self._limiters[plugin_key]
            self._logger.info(f"Removed rate limit for plugin {plugin_key}")

    def remove_method_rate_limit(self, method_name: str) -> None:
        """Remove global rate limit for a method."""
        if method_name in self._global_limiters:
            del self._global_limiters[method_name]
            self._logger.info(f"Removed global rate limit for method {method_name}")

    async def check_rate_limit(
        self,
        plugin: BasePlugin,
        method_name: str,
        user_id: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        Check rate limits before plugin method execution.

        Args:
            plugin: Plugin instance
            method_name: Method being called
            user_id: Optional user identifier for per-user rate limiting
            **kwargs: Additional context for rate limiting

        Raises:
            PluginError: If rate limit is exceeded
        """
        plugin_key = f"{plugin.domain}.{plugin.name}"
        self._stats["total_requests"] += 1

        # Check plugin-specific rate limit
        if plugin_key in self._limiters:
            limiter = self._limiters[plugin_key]
            key = user_id if limiter.config.per_user and user_id else plugin_key

            allowed, metadata = await limiter.is_allowed(key)
            if not allowed:
                self._stats["blocked_requests"] += 1
                self._stats["rate_limited_plugins"].add(plugin_key)
                if user_id:
                    self._stats["rate_limited_users"].add(user_id)

                self._logger.warning(
                    f"Rate limit exceeded for plugin {plugin_key} "
                    f"(user: {user_id}, method: {method_name})"
                )

                raise PluginError(
                    f"Rate limit exceeded for plugin {plugin.name}. "
                    f"Try again in {metadata.get('retry_after', 'a few')} seconds.",
                    plugin_name=plugin.name,
                    plugin_domain=plugin.domain,
                    context={"rate_limit_metadata": metadata, "rate_limited": True},
                )

        # Check global method rate limit
        if method_name in self._global_limiters:
            limiter = self._global_limiters[method_name]
            key = f"{method_name}:{user_id}" if limiter.config.per_user and user_id else method_name

            allowed, metadata = await limiter.is_allowed(key)
            if not allowed:
                self._stats["blocked_requests"] += 1
                if user_id:
                    self._stats["rate_limited_users"].add(user_id)

                self._logger.warning(
                    f"Global rate limit exceeded for method {method_name} "
                    f"(user: {user_id}, plugin: {plugin_key})"
                )

                raise PluginError(
                    f"Rate limit exceeded for method {method_name}. "
                    f"Try again in {metadata.get('retry_after', 'a few')} seconds.",
                    plugin_name=plugin.name,
                    plugin_domain=plugin.domain,
                    context={
                        "rate_limit_metadata": metadata,
                        "rate_limited": True,
                        "global_rate_limit": True,
                    },
                )

        self._stats["allowed_requests"] += 1

    def _create_limiter(self, config: RateLimit) -> RateLimiter:
        """Create appropriate limiter based on strategy."""
        if config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return TokenBucketLimiter(config)
        elif config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return SlidingWindowLimiter(config)
        elif config.strategy == RateLimitStrategy.FIXED_WINDOW:
            return FixedWindowLimiter(config)
        else:
            # Default to token bucket
            return TokenBucketLimiter(config)

    def get_rate_limit_status(
        self, plugin_key: str, user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Get current rate limit status for a plugin.

        Args:
            plugin_key: Plugin key
            user_id: Optional user ID

        Returns:
            Rate limit status information
        """
        status = {"plugin_key": plugin_key}

        # Get plugin-specific rate limit status
        if plugin_key in self._limiters:
            limiter = self._limiters[plugin_key]
            key = user_id if limiter.config.per_user and user_id else plugin_key
            status["plugin_rate_limit"] = limiter.get_stats(key)

        return status

    def get_global_rate_limit_status(
        self, method_name: str, user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Get global rate limit status for a method."""
        status = {"method_name": method_name}

        if method_name in self._global_limiters:
            limiter = self._global_limiters[method_name]
            key = f"{method_name}:{user_id}" if limiter.config.per_user and user_id else method_name
            status["global_rate_limit"] = limiter.get_stats(key)

        return status

    def reset_rate_limits(
        self, plugin_key: Optional[str] = None, user_id: Optional[str] = None
    ) -> None:
        """
        Reset rate limits.

        Args:
            plugin_key: Optional specific plugin to reset
            user_id: Optional specific user to reset
        """
        if plugin_key:
            # Reset specific plugin
            if plugin_key in self._limiters:
                limiter = self._limiters[plugin_key]
                key = user_id if limiter.config.per_user and user_id else plugin_key
                limiter.reset(key)
                self._logger.info(f"Reset rate limit for plugin {plugin_key}")
        else:
            # Reset all plugin rate limits
            for plugin_key, limiter in self._limiters.items():
                if user_id and limiter.config.per_user:
                    limiter.reset(user_id)
                else:
                    limiter.reset(plugin_key)

            # Reset global method rate limits
            for method_name, limiter in self._global_limiters.items():
                if user_id and limiter.config.per_user:
                    limiter.reset(f"{method_name}:{user_id}")
                else:
                    limiter.reset(method_name)

            self._logger.info("Reset all rate limits")

    def get_middleware_stats(self) -> dict[str, Any]:
        """Get rate limiting middleware statistics."""
        return {
            "total_requests": self._stats["total_requests"],
            "allowed_requests": self._stats["allowed_requests"],
            "blocked_requests": self._stats["blocked_requests"],
            "block_rate": (self._stats["blocked_requests"] / max(1, self._stats["total_requests"]))
            * 100,
            "active_plugin_limits": len(self._limiters),
            "active_method_limits": len(self._global_limiters),
            "rate_limited_plugins": list(self._stats["rate_limited_plugins"]),
            "rate_limited_users": list(self._stats["rate_limited_users"]),
            "unique_rate_limited_plugins": len(self._stats["rate_limited_plugins"]),
            "unique_rate_limited_users": len(self._stats["rate_limited_users"]),
        }

    @staticmethod
    def create_conservative_rate_limit() -> RateLimit:
        """Create a conservative rate limit configuration."""
        return RateLimit(
            max_requests=10,
            time_window=60,  # 10 requests per minute
            strategy=RateLimitStrategy.SLIDING_WINDOW,
        )

    @staticmethod
    def create_moderate_rate_limit() -> RateLimit:
        """Create a moderate rate limit configuration."""
        return RateLimit(
            max_requests=100,
            time_window=60,  # 100 requests per minute
            strategy=RateLimitStrategy.TOKEN_BUCKET,
            burst_allowance=20,
        )

    @staticmethod
    def create_permissive_rate_limit() -> RateLimit:
        """Create a permissive rate limit configuration."""
        return RateLimit(
            max_requests=1000,
            time_window=60,  # 1000 requests per minute
            strategy=RateLimitStrategy.TOKEN_BUCKET,
            burst_allowance=100,
        )

    @staticmethod
    def create_per_user_rate_limit() -> RateLimit:
        """Create a per-user rate limit configuration."""
        return RateLimit(
            max_requests=50,
            time_window=60,  # 50 requests per minute per user
            strategy=RateLimitStrategy.SLIDING_WINDOW,
            per_user=True,
        )

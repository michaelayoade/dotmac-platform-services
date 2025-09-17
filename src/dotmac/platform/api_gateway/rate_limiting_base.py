"""
Rate limiting implementations for API Gateway.
Provider-agnostic rate limiting with multiple algorithms.
"""

import asyncio
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Optional

import redis.asyncio as redis

from .interfaces import RateLimiter, RateLimitConfig, RateLimitResult

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

class TokenBucketLimiter(RateLimiter):
    """Token bucket algorithm implementation."""

    def __init__(self, config: RateLimitConfig, redis_client: Optional[redis.Redis] = None):
        self.config = config
        self.redis_client = redis_client
        self.local_buckets: Dict[str, Dict] = defaultdict(
            lambda: {"tokens": config.burst_size, "last_refill": time.time()}
        )

    async def check_limit(self, identifier: str, resource: Optional[str] = None) -> RateLimitResult:
        """Check if request is within rate limits."""
        key = f"{identifier}:{resource}" if resource else identifier

        if self.redis_client:
            return await self._check_redis(key)
        return await self._check_local(key)

    async def _check_local(self, key: str) -> RateLimitResult:
        """Check rate limit using local storage."""
        bucket = self.local_buckets[key]
        now = time.time()

        # Refill tokens
        time_passed = now - bucket["last_refill"]
        refill_rate = self.config.requests_per_minute / 60.0
        new_tokens = time_passed * refill_rate

        bucket["tokens"] = min(self.config.burst_size, bucket["tokens"] + new_tokens)
        bucket["last_refill"] = now

        # Check if tokens available
        if bucket["tokens"] >= 1:
            reset_at = datetime.utcnow() + timedelta(seconds=60)
            return RateLimitResult(allowed=True, remaining=int(bucket["tokens"]), reset_at=reset_at)

        # Calculate retry after
        tokens_needed = 1 - bucket["tokens"]
        retry_after = int(tokens_needed / refill_rate)
        reset_at = datetime.utcnow() + timedelta(seconds=retry_after)

        return RateLimitResult(
            allowed=False, remaining=0, reset_at=reset_at, retry_after=retry_after
        )

    async def _check_redis(self, key: str) -> RateLimitResult:
        """Check rate limit using Redis."""
        # Implementation with Redis for distributed rate limiting
        # Uses Lua script for atomic operations
        lua_script = """
        local key = KEYS[1]
        local burst = tonumber(ARGV[1])
        local rate = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])

        local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
        local tokens = tonumber(bucket[1]) or burst
        local last_refill = tonumber(bucket[2]) or now

        local time_passed = now - last_refill
        local new_tokens = time_passed * rate
        tokens = math.min(burst, tokens + new_tokens)

        if tokens >= 1 then
            tokens = tokens - 1
            redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
            redis.call('EXPIRE', key, 3600)
            return {1, tokens}
        else
            return {0, 0}
        end
        """

        result = await self.redis_client.eval(
            lua_script,
            1,
            key,
            str(self.config.burst_size),
            str(self.config.requests_per_minute / 60.0),
            str(time.time()),
        )

        allowed, remaining = result
        reset_at = datetime.utcnow() + timedelta(seconds=60)

        return RateLimitResult(
            allowed=bool(allowed),
            remaining=int(remaining),
            reset_at=reset_at,
            retry_after=None if allowed else 60,
        )

    async def consume(
        self, identifier: str, tokens: int = 1, resource: Optional[str] = None
    ) -> bool:
        """Consume tokens from the rate limit."""
        key = f"{identifier}:{resource}" if resource else identifier

        if self.redis_client:
            result = await self._check_redis(key)
        else:
            bucket = self.local_buckets[key]
            if bucket["tokens"] >= tokens:
                bucket["tokens"] -= tokens
                return True
            return False

        return result.allowed

    async def reset(self, identifier: str, resource: Optional[str] = None) -> None:
        """Reset rate limit for an identifier."""
        key = f"{identifier}:{resource}" if resource else identifier

        if self.redis_client:
            await self.redis_client.delete(key)
        else:
            if key in self.local_buckets:
                del self.local_buckets[key]

    async def get_usage(
        self, identifier: str, resource: Optional[str] = None
    ) -> Dict[str, any]:  # type: ignore
        """Get current usage statistics."""
        key = f"{identifier}:{resource}" if resource else identifier
        result = await self.check_limit(identifier, resource)

        return {
            "identifier": identifier,
            "resource": resource,
            "remaining": result.remaining,
            "reset_at": result.reset_at.isoformat(),
            "allowed": result.allowed,
        }

class SlidingWindowLimiter(RateLimiter):
    """Sliding window algorithm implementation."""

    def __init__(self, config: RateLimitConfig, redis_client: Optional[redis.Redis] = None):
        self.config = config
        self.redis_client = redis_client
        self.local_windows: Dict[str, deque] = defaultdict(deque)

    async def check_limit(self, identifier: str, resource: Optional[str] = None) -> RateLimitResult:
        """Check if request is within rate limits using sliding window."""
        key = f"{identifier}:{resource}" if resource else identifier
        now = time.time()
        window_start = now - 60  # 1 minute window

        if self.redis_client:
            return await self._check_redis_sliding(key, now, window_start)

        # Local implementation
        window = self.local_windows[key]

        # Remove old entries
        while window and window[0] < window_start:
            window.popleft()

        # Check limit
        if len(window) < self.config.requests_per_minute:
            return RateLimitResult(
                allowed=True,
                remaining=self.config.requests_per_minute - len(window),
                reset_at=datetime.utcnow() + timedelta(seconds=60),
            )

        # Rate limit exceeded
        oldest_request = window[0] if window else now
        retry_after = int(60 - (now - oldest_request))

        return RateLimitResult(
            allowed=False,
            remaining=0,
            reset_at=datetime.utcnow() + timedelta(seconds=retry_after),
            retry_after=retry_after,
        )

    async def consume(
        self, identifier: str, tokens: int = 1, resource: Optional[str] = None
    ) -> bool:
        """Consume tokens from the rate limit."""
        key = f"{identifier}:{resource}" if resource else identifier
        result = await self.check_limit(identifier, resource)

        if result.allowed:
            now = time.time()
            if self.redis_client:
                await self.redis_client.zadd(key, {str(now): now})
                await self.redis_client.expire(key, 60)
            else:
                self.local_windows[key].append(now)
            return True

        return False

    async def reset(self, identifier: str, resource: Optional[str] = None) -> None:
        """Reset rate limit for an identifier."""
        key = f"{identifier}:{resource}" if resource else identifier

        if self.redis_client:
            await self.redis_client.delete(key)
        else:
            if key in self.local_windows:
                del self.local_windows[key]

    async def get_usage(
        self, identifier: str, resource: Optional[str] = None
    ) -> Dict[str, any]:  # type: ignore
        """Get current usage statistics."""
        result = await self.check_limit(identifier, resource)
        return {
            "identifier": identifier,
            "resource": resource,
            "remaining": result.remaining,
            "reset_at": result.reset_at.isoformat(),
            "allowed": result.allowed,
        }

    async def _check_redis_sliding(
        self, key: str, now: float, window_start: float
    ) -> RateLimitResult:
        """Check sliding window rate limit using Redis."""
        # Remove old entries and count current
        pipe = self.redis_client.pipeline()  # type: ignore
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.expire(key, 60)

        _, count, _ = await pipe.execute()

        if count < self.config.requests_per_minute:
            return RateLimitResult(
                allowed=True,
                remaining=self.config.requests_per_minute - count,
                reset_at=datetime.utcnow() + timedelta(seconds=60),
            )

        return RateLimitResult(
            allowed=False,
            remaining=0,
            reset_at=datetime.utcnow() + timedelta(seconds=60),
            retry_after=60,
        )

class FixedWindowLimiter(RateLimiter):
    """Fixed window algorithm implementation."""

    def __init__(self, config: RateLimitConfig, redis_client: Optional[redis.Redis] = None):
        self.config = config
        self.redis_client = redis_client
        self.local_counters: Dict[str, Dict] = defaultdict(
            lambda: {"count": 0, "window_start": time.time()}
        )

    async def check_limit(self, identifier: str, resource: Optional[str] = None) -> RateLimitResult:
        """Check if request is within rate limits using fixed window."""
        key = f"{identifier}:{resource}" if resource else identifier
        now = time.time()

        if self.redis_client:
            return await self._check_redis_fixed(key, now)

        # Local implementation
        counter = self.local_counters[key]
        window_elapsed = now - counter["window_start"]

        # Reset window if expired
        if window_elapsed >= 60:
            counter["count"] = 0
            counter["window_start"] = now
            window_elapsed = 0

        # Check limit
        if counter["count"] < self.config.requests_per_minute:
            remaining = self.config.requests_per_minute - counter["count"]
            reset_at = datetime.utcfromtimestamp(counter["window_start"] + 60)

            return RateLimitResult(allowed=True, remaining=remaining, reset_at=reset_at)

        # Rate limit exceeded
        retry_after = int(60 - window_elapsed)
        reset_at = datetime.utcfromtimestamp(counter["window_start"] + 60)

        return RateLimitResult(
            allowed=False, remaining=0, reset_at=reset_at, retry_after=retry_after
        )

    async def consume(
        self, identifier: str, tokens: int = 1, resource: Optional[str] = None
    ) -> bool:
        """Consume tokens from the rate limit."""
        key = f"{identifier}:{resource}" if resource else identifier
        result = await self.check_limit(identifier, resource)

        if result.allowed:
            if self.redis_client:
                await self.redis_client.incr(key)
                await self.redis_client.expire(key, 60)
            else:
                self.local_counters[key]["count"] += tokens
            return True

        return False

    async def reset(self, identifier: str, resource: Optional[str] = None) -> None:
        """Reset rate limit for an identifier."""
        key = f"{identifier}:{resource}" if resource else identifier

        if self.redis_client:
            await self.redis_client.delete(key)
        else:
            if key in self.local_counters:
                del self.local_counters[key]

    async def get_usage(
        self, identifier: str, resource: Optional[str] = None
    ) -> Dict[str, any]:  # type: ignore
        """Get current usage statistics."""
        result = await self.check_limit(identifier, resource)
        return {
            "identifier": identifier,
            "resource": resource,
            "remaining": result.remaining,
            "reset_at": result.reset_at.isoformat(),
            "allowed": result.allowed,
        }

    async def _check_redis_fixed(self, key: str, now: float) -> RateLimitResult:
        """Check fixed window rate limit using Redis."""
        window_key = f"{key}:{int(now // 60)}"

        count = await self.redis_client.get(window_key)  # type: ignore
        count = int(count) if count else 0

        if count < self.config.requests_per_minute:
            return RateLimitResult(
                allowed=True,
                remaining=self.config.requests_per_minute - count,
                reset_at=datetime.utcnow() + timedelta(seconds=60 - (now % 60)),
            )

        retry_after = int(60 - (now % 60))
        return RateLimitResult(
            allowed=False,
            remaining=0,
            reset_at=datetime.utcnow() + timedelta(seconds=retry_after),
            retry_after=retry_after,
        )

"""
Rate limiting implementations for API Gateway.
Extends platform services with business-specific features.
"""


from typing import Optional, Any

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

# Import from platform services if available; fallback to local implementations
_PLATFORM_AVAILABLE = True
try:  # platform branch
    from dotmac.platform.core.rate_limiting import (  # type: ignore[import]
        RateLimiter as PlatformRateLimiter,
        TokenBucketLimiter as PlatformTokenBucket,
        SlidingWindowLimiter as PlatformSlidingWindow,
        FixedWindowLimiter as PlatformFixedWindow,
    )
    from dotmac.platform.cache import CacheService  # type: ignore[import]
except Exception as e:  # pragma: no cover - dev fallback
    _PLATFORM_AVAILABLE = False  # type: ignore[misc]
    logger.debug(f"Platform rate limiting not available, using local implementation: {e}")
    from .rate_limiting_base import (
        RateLimiter as PlatformRateLimiter,
        TokenBucketLimiter as PlatformTokenBucket,
        SlidingWindowLimiter as PlatformSlidingWindow,
        FixedWindowLimiter as PlatformFixedWindow,
    )

    # Minimal CacheService stub
    class CacheService:  # type: ignore
        async def get(self, key: str):
            return None

        async def set(self, key: str, value: Any, ttl: Optional[int] = None):
            return True

from .interfaces import RateLimitConfig, RateLimitAlgorithm

if _PLATFORM_AVAILABLE:

    class TokenBucketLimiter(PlatformTokenBucket):
        """Wrapper around platform token bucket with business config."""

        def __init__(self, config: RateLimitConfig, cache_service: Optional[CacheService] = None):
            super().__init__(
                max_requests=config.requests_per_minute,
                window_seconds=60,
                burst_size=config.burst_size,
                cache_service=cache_service,
            )
            self.config = config

    class SlidingWindowLimiter(PlatformSlidingWindow):
        def __init__(self, config: RateLimitConfig, cache_service: Optional[CacheService] = None):
            super().__init__(
                max_requests=config.requests_per_minute,
                window_seconds=60,
                cache_service=cache_service,
            )
            self.config = config

    class FixedWindowLimiter(PlatformFixedWindow):
        def __init__(self, config: RateLimitConfig, cache_service: Optional[CacheService] = None):
            super().__init__(
                max_requests=config.requests_per_minute,
                window_seconds=60,
                cache_service=cache_service,
            )
            self.config = config

else:
    # Fallback to local implementations directly
    TokenBucketLimiter = PlatformTokenBucket  # type: ignore
    SlidingWindowLimiter = PlatformSlidingWindow  # type: ignore
    FixedWindowLimiter = PlatformFixedWindow  # type: ignore

def create_rate_limiter(
    config: RateLimitConfig, cache_service: Optional[CacheService] = None
) -> PlatformRateLimiter:
    """Factory to create appropriate rate limiter based on algorithm."""
    logger.info(
        f"Creating rate limiter with algorithm: {getattr(config, 'algorithm', RateLimitAlgorithm.TOKEN_BUCKET)}"
    )

    algorithm = getattr(config, "algorithm", RateLimitAlgorithm.TOKEN_BUCKET)
    if algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
        return TokenBucketLimiter(config, cache_service)
    elif algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
        return SlidingWindowLimiter(config, cache_service)
    elif algorithm == RateLimitAlgorithm.FIXED_WINDOW:
        return FixedWindowLimiter(config, cache_service)
    else:
        # Default to token bucket
        logger.warning(f"Unknown rate limiting algorithm {algorithm}, defaulting to TOKEN_BUCKET")
        return TokenBucketLimiter(config, cache_service)

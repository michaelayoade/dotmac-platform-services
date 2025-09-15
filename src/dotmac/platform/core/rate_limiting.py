"""Rate limiting implementation."""

import asyncio
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

class RateLimitExceededError(Exception):
    """Raised when rate limit is exceeded."""
    pass


class RateLimiter:
    """Rate limiter for API endpoints."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum number of requests allowed
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.default_limit = max_requests
        self.window_minutes = window_seconds / 60
        self._requests: dict[str, list] = defaultdict(list)
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def check_rate_limit(self, identifier: str, limit: Optional[int] = None) -> bool:
        """Check if request is within rate limit."""
        limit = limit or self.default_limit
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=self.window_minutes)

        async with self._locks[identifier]:
            # Clean old requests
            self._requests[identifier] = [
                req_time for req_time in self._requests[identifier] if req_time > window_start
            ]

            # Check limit
            if len(self._requests[identifier]) >= limit:
                raise RateLimitExceededError(
                    f"Rate limit of {limit} requests per {self.window_minutes} minutes exceeded"
                )
            # Add current request
            self._requests[identifier].append(now)
            return True

    def get_remaining_requests(self, identifier: str, limit: Optional[int] = None) -> int:
        """Get remaining requests for identifier."""
        limit = limit or self.default_limit
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=self.window_minutes)

        # Clean old requests
        self._requests[identifier] = [req_time for req_time in self._requests[identifier] if req_time > window_start]

        return max(0, limit - len(self._requests[identifier]))

    def reset_limit(self, identifier: str):
        """Reset rate limit for identifier."""
        self._requests[identifier] = []

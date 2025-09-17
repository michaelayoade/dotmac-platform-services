"""Tests for rate limiting."""

import pytest
from dotmac.platform.core.rate_limiting import RateLimiter


class TestRateLimiting:
    def test_rate_limiter_creation(self):
        """Test creating a rate limiter."""
        limiter = RateLimiter(max_requests=100, window_seconds=60)
        assert limiter.max_requests == 100
        assert limiter.window_seconds == 60

    @pytest.mark.asyncio
    async def test_rate_limit_check(self):
        """Test rate limit checking."""
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        client_id = "test_client"

        # First two requests should pass
        assert await limiter.check_rate_limit(client_id) is True
        assert await limiter.check_rate_limit(client_id) is True

        # Third should fail
        assert await limiter.check_rate_limit(client_id) is False

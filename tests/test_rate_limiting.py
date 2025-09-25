"""
Tests for rate limiting functionality using SlowAPI.
"""

from unittest.mock import MagicMock, patch

import pytest
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Import the entire module to ensure it's tracked by coverage
import dotmac.platform.rate_limiting
from dotmac.platform.rate_limiting import (
    _rate_limit_exceeded_handler,
    get_limiter,
    limiter,
    rate_limit,
)


class TestGetLimiter:
    """Test limiter instance creation."""

    @patch('dotmac.platform.rate_limiting.redis_client')
    @patch('dotmac.platform.settings.settings')
    def test_get_limiter_with_redis(self, mock_settings, mock_redis_client):
        """Test limiter creation with Redis backend."""
        mock_redis_client.__bool__.return_value = True
        mock_settings.redis.cache_url = "redis://localhost:6379/0"

        result_limiter = get_limiter()

        assert isinstance(result_limiter, Limiter)

    @patch('dotmac.platform.rate_limiting.redis_client', None)
    def test_get_limiter_without_redis(self):
        """Test limiter creation without Redis (in-memory)."""
        result_limiter = get_limiter()

        assert isinstance(result_limiter, Limiter)

    @patch('dotmac.platform.rate_limiting.redis_client')
    def test_get_limiter_redis_false(self, mock_redis_client):
        """Test limiter creation when Redis client is falsy."""
        mock_redis_client.__bool__.return_value = False

        result_limiter = get_limiter()

        assert isinstance(result_limiter, Limiter)


class TestRateLimit:
    """Test rate limiting decorator."""

    def test_rate_limit_decorator_creation(self):
        """Test that rate_limit creates a decorator."""
        decorator = rate_limit("100/minute")
        assert callable(decorator)

    def test_rate_limit_decorator_application(self):
        """Test applying rate limit decorator to a function."""
        @rate_limit("10/minute")
        def test_func(request):
            return "success"

        # Function should be wrapped by limiter
        assert callable(test_func)

    def test_rate_limit_different_limits(self):
        """Test rate_limit with different limit strings."""
        # Test various limit formats
        limits = ["100/minute", "10/second", "1000/hour", "5/day"]

        for limit in limits:
            decorator = rate_limit(limit)
            assert callable(decorator)

            @decorator
            def test_func(request):
                return "test"

            assert callable(test_func)


class TestGlobalLimiter:
    """Test the global limiter instance."""

    def test_global_limiter_exists(self):
        """Test that global limiter is created."""
        assert limiter is not None
        assert isinstance(limiter, Limiter)

    def test_global_limiter_limit_method(self):
        """Test that global limiter has limit method."""
        assert hasattr(limiter, 'limit')
        assert callable(limiter.limit)


class TestRateLimitingIntegration:
    """Test rate limiting integration with functions."""

    def test_function_decoration_with_limiter(self):
        """Test decorating a function with rate limiting."""
        @limiter.limit("5/minute")
        def limited_function(request):
            return {"message": "success"}

        # Function should be callable
        assert callable(limited_function)

    def test_async_function_decoration(self):
        """Test decorating an async function with rate limiting."""
        @limiter.limit("10/minute")
        async def async_limited_function(request):
            return {"message": "async success"}

        assert callable(async_limited_function)


class TestRateLimitExports:
    """Test module exports."""

    def test_rate_limit_exceeded_export(self):
        """Test that RateLimitExceeded is exported."""
        from dotmac.platform.rate_limiting import RateLimitExceeded
        assert RateLimitExceeded is not None
        assert issubclass(RateLimitExceeded, Exception)

    def test_get_remote_address_export(self):
        """Test that get_remote_address is exported."""
        from dotmac.platform.rate_limiting import get_remote_address
        assert get_remote_address is not None
        assert callable(get_remote_address)

    def test_rate_limit_exceeded_handler_export(self):
        """Test that rate limit exceeded handler is exported."""
        from dotmac.platform.rate_limiting import _rate_limit_exceeded_handler
        assert _rate_limit_exceeded_handler is not None
        assert callable(_rate_limit_exceeded_handler)

    def test_all_exports_defined(self):
        """Test that __all__ contains expected exports."""
        from dotmac.platform.rate_limiting import __all__

        expected_exports = [
            "limiter",
            "rate_limit",
            "RateLimitExceeded",
            "get_remote_address",
            "_rate_limit_exceeded_handler",
        ]

        assert __all__ == expected_exports

    def test_all_exports_importable(self):
        """Test that all exported items can be imported."""
        from dotmac.platform.rate_limiting import (
            _rate_limit_exceeded_handler,
            RateLimitExceeded,
            get_remote_address,
            limiter,
            rate_limit,
        )

        # All should be non-None
        assert limiter is not None
        assert rate_limit is not None
        assert RateLimitExceeded is not None
        assert get_remote_address is not None
        assert _rate_limit_exceeded_handler is not None


class TestRateLimitingErrorScenarios:
    """Test error scenarios and edge cases."""

    def test_invalid_limit_string_handling(self):
        """Test behavior with invalid limit strings."""
        # SlowAPI should handle invalid strings gracefully
        # The decorator should still be created but may fail at runtime
        decorator = rate_limit("invalid_limit")
        assert callable(decorator)

    def test_zero_rate_limit(self):
        """Test zero rate limit."""
        decorator = rate_limit("0/minute")
        assert callable(decorator)

    def test_very_high_rate_limit(self):
        """Test very high rate limit."""
        decorator = rate_limit("1000000/second")
        assert callable(decorator)

    @patch('dotmac.platform.rate_limiting.logger')
    def test_warning_logged_for_in_memory_storage(self, mock_logger):
        """Test that warning is logged when using in-memory storage."""
        with patch('dotmac.platform.rate_limiting.redis_client', None):
            get_limiter()
            mock_logger.warning.assert_called_once_with(
                "Using in-memory rate limiting - not suitable for production"
            )


class TestRateLimitingWithMockRequests:
    """Test rate limiting behavior with mock requests."""

    def test_rate_limit_key_function(self):
        """Test that key function works with mock request."""
        # Mock a FastAPI request object
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"

        # This should work with the get_remote_address function
        key = get_remote_address(mock_request)
        assert key == "127.0.0.1"

    def test_rate_limit_with_different_ips(self):
        """Test that different IPs get different rate limit keys."""
        mock_request_1 = MagicMock()
        mock_request_1.client.host = "127.0.0.1"

        mock_request_2 = MagicMock()
        mock_request_2.client.host = "192.168.1.1"

        key1 = get_remote_address(mock_request_1)
        key2 = get_remote_address(mock_request_2)

        assert key1 != key2
        assert key1 == "127.0.0.1"
        assert key2 == "192.168.1.1"


class TestRateLimitingModuleStructure:
    """Test module structure and initialization."""

    def test_module_imports_successfully(self):
        """Test that the module imports without errors."""
        import dotmac.platform.rate_limiting
        assert dotmac.platform.rate_limiting is not None

    def test_slowapi_dependencies_available(self):
        """Test that SlowAPI dependencies are available."""
        try:
            from slowapi import Limiter
            from slowapi.errors import RateLimitExceeded
            from slowapi.util import get_remote_address
            assert True  # All imports successful
        except ImportError:
            pytest.fail("SlowAPI dependencies not available")

    def test_module_logger_configured(self):
        """Test that module logger is configured."""
        from dotmac.platform.rate_limiting import logger
        assert logger is not None
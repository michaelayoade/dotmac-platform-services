"""Tests for tenacity-based circuit breaker patterns."""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from typing import Any

# Use tenacity directly - no wrapper needed
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError,
)


class TestTenacityCircuitBreaker:
    """Test tenacity retry patterns as circuit breaker replacement."""

    def test_basic_retry_decorator(self):
        """Test basic retry decorator functionality."""
        call_count = 0

        @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.1, max=1))
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Simulated failure")
            return "success"

        result = failing_function()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_async_retry_decorator(self):
        """Test async retry decorator functionality."""
        call_count = 0

        @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=0.1, max=1))
        async def async_failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Network failure")
            return "async_success"

        result = await async_failing_function()
        assert result == "async_success"
        assert call_count == 2

    def test_retry_on_specific_exception(self):
        """Test retry only on specific exception types."""
        call_count = 0

        @retry(
            stop=stop_after_attempt(3),
            retry=retry_if_exception_type(ValueError),
            wait=wait_exponential(min=0.1, max=1)
        )
        def function_with_different_exceptions():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Should retry")
            elif call_count == 2:
                raise TypeError("Should not retry")
            return "success"

        # Should raise TypeError without retrying
        with pytest.raises(TypeError):
            function_with_different_exceptions()

        assert call_count == 2  # Called once for ValueError, once for TypeError

    def test_retry_exhaustion(self):
        """Test that retries are exhausted properly."""
        call_count = 0

        @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=0.1, max=1))
        def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise RuntimeError("Always fails")

        with pytest.raises(RetryError):
            always_failing_function()

        assert call_count == 2

    def test_no_retry_on_success(self):
        """Test that successful calls don't trigger retries."""
        call_count = 0

        @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.1, max=1))
        def successful_function():
            nonlocal call_count
            call_count += 1
            return "immediate_success"

        result = successful_function()
        assert result == "immediate_success"
        assert call_count == 1
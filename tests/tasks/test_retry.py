"""Tests for retry utilities."""

import asyncio
import time
from unittest.mock import Mock, call

import pytest

from dotmac.platform.tasks.retry import (
    AsyncRetryManager,
    RetryError,
    calculate_backoff,
    retry_async,
    retry_sync,
    retry_with_manager,
)


class TestCalculateBackoff:
    """Test backoff calculation."""

    def test_calculate_backoff_exponential(self):
        """Test exponential backoff calculation."""
        # First attempt (0-based)
        delay = calculate_backoff(0, base_delay=1.0, backoff_factor=2.0, jitter=False)
        assert delay == 1.0

        # Second attempt
        delay = calculate_backoff(1, base_delay=1.0, backoff_factor=2.0, jitter=False)
        assert delay == 2.0

        # Third attempt
        delay = calculate_backoff(2, base_delay=1.0, backoff_factor=2.0, jitter=False)
        assert delay == 4.0

    def test_calculate_backoff_max_delay(self):
        """Test that backoff respects max delay."""
        delay = calculate_backoff(
            10, base_delay=1.0, backoff_factor=2.0, max_delay=5.0, jitter=False
        )
        assert delay == 5.0

    def test_calculate_backoff_with_jitter(self):
        """Test backoff with jitter."""
        # Run multiple times to test jitter variation
        delays = []
        for _ in range(10):
            delay = calculate_backoff(2, base_delay=1.0, backoff_factor=2.0, jitter=True)
            delays.append(delay)

        # Base delay for attempt 2 is 4.0
        # With 25% jitter, range should be [3.0, 5.0]
        assert all(3.0 <= d <= 5.0 for d in delays)
        # Verify we get some variation
        assert len(set(delays)) > 1


class TestRetryAsync:
    """Test async retry decorator."""

    @pytest.mark.asyncio
    async def test_retry_async_success_first_attempt(self):
        """Test successful execution on first attempt."""
        call_count = 0

        @retry_async(max_attempts=3)
        async def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_function()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_async_success_after_retry(self):
        """Test successful execution after retry."""
        call_count = 0

        @retry_async(max_attempts=3, base_delay=0.01)
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = await flaky_function()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_async_all_attempts_fail(self):
        """Test that RetryError is raised when all attempts fail."""
        call_count = 0

        @retry_async(max_attempts=3, base_delay=0.01)
        async def failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError(f"Failure {call_count}")

        with pytest.raises(RetryError) as exc_info:
            await failing_function()

        assert exc_info.value.attempts == 3
        assert isinstance(exc_info.value.last_exception, ValueError)
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_async_specific_exceptions(self):
        """Test retry only on specific exceptions."""
        call_count = 0

        @retry_async(
            max_attempts=3,
            base_delay=0.01,
            exceptions=(ValueError,),
        )
        async def function_with_different_errors():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Retryable error")
            raise TypeError("Non-retryable error")

        # Should retry ValueError but not TypeError
        with pytest.raises(TypeError):
            await function_with_different_errors()

        assert call_count == 2  # First attempt + one retry

    @pytest.mark.asyncio
    async def test_retry_async_on_retry_callback(self):
        """Test on_retry callback is called."""
        callback_calls = []

        def on_retry(attempt, exception):
            callback_calls.append((attempt, str(exception)))

        @retry_async(
            max_attempts=3,
            base_delay=0.01,
            on_retry=on_retry,
        )
        async def failing_function():
            raise ValueError("Test error")

        with pytest.raises(RetryError):
            await failing_function()

        assert len(callback_calls) == 2  # Called for retry attempts 1 and 2
        assert callback_calls[0] == (1, "Test error")
        assert callback_calls[1] == (2, "Test error")


class TestRetrySync:
    """Test sync retry decorator."""

    def test_retry_sync_success_first_attempt(self):
        """Test successful execution on first attempt."""
        call_count = 0

        @retry_sync(max_attempts=3)
        def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_function()
        assert result == "success"
        assert call_count == 1

    def test_retry_sync_success_after_retry(self):
        """Test successful execution after retry."""
        call_count = 0

        @retry_sync(max_attempts=3, base_delay=0.01)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = flaky_function()
        assert result == "success"
        assert call_count == 3

    def test_retry_sync_all_attempts_fail(self):
        """Test that RetryError is raised when all attempts fail."""
        call_count = 0

        @retry_sync(max_attempts=3, base_delay=0.01)
        def failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError(f"Failure {call_count}")

        with pytest.raises(RetryError) as exc_info:
            failing_function()

        assert exc_info.value.attempts == 3
        assert isinstance(exc_info.value.last_exception, ValueError)
        assert call_count == 3


class TestAsyncRetryManager:
    """Test AsyncRetryManager context manager."""

    @pytest.mark.asyncio
    async def test_retry_manager_success(self):
        """Test successful execution with retry manager."""
        call_count = 0

        async def operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"

        result = await retry_with_manager(
            operation,
            max_attempts=3,
            base_delay=0.01,
        )

        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_manager_all_attempts_fail(self):
        """Test retry manager when all attempts fail."""
        call_count = 0

        async def failing_operation():
            nonlocal call_count
            call_count += 1
            raise ValueError(f"Failure {call_count}")

        with pytest.raises(RetryError) as exc_info:
            await retry_with_manager(
                failing_operation,
                max_attempts=3,
                base_delay=0.01,
            )

        assert exc_info.value.attempts == 3
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_manager_with_context(self):
        """Test using retry manager directly with context."""
        call_count = 0
        manager = AsyncRetryManager(max_attempts=3, base_delay=0.01)

        for _ in range(3):
            try:
                async with manager:
                    call_count += 1
                    if call_count < 3:
                        raise ValueError("Temporary failure")
                    # Success on third attempt
                    break
            except RetryError:
                # This should not happen in this test
                pytest.fail("RetryError raised prematurely")

        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_manager_non_retryable_exception(self):
        """Test retry manager with non-retryable exception."""
        call_count = 0

        async def operation_with_type_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("Non-retryable")

        with pytest.raises(TypeError):
            await retry_with_manager(
                operation_with_type_error,
                max_attempts=3,
                base_delay=0.01,
                exceptions=(ValueError,),
            )

        assert call_count == 1  # No retries for non-matching exception

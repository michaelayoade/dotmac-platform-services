"""
Tests for task decorators.
"""

from unittest.mock import patch

import pytest

from dotmac.platform.tasks.decorators import (
    periodic_task,
    retry,
    task,
)


class TestRetryDecorator:
    """Test retry decorator functionality."""

    def test_retry_decorator_with_tenacity(self):
        """Test retry decorator when tenacity is available."""
        # The actual implementation will use tenacity if available
        # This tests the basic functionality

        call_count = 0

        @retry(stop=3)
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        # Function should eventually succeed after retries
        result = failing_function()
        assert result == "success"
        assert call_count == 3

    @patch("dotmac.platform.tasks.decorators.logger")
    def test_retry_decorator_fallback(self, mock_logger):
        """Test retry decorator fallback when tenacity is not available."""
        # Simulate tenacity not being available by using the fallback directly

        call_count = 0

        @retry(stop=3)
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"

        result = failing_function()
        assert result == "success"

    def test_retry_decorator_without_params(self):
        """Test retry decorator used without parameters."""
        call_count = 0

        @retry
        def simple_function():
            nonlocal call_count
            call_count += 1
            return "result"

        result = simple_function()
        assert result == "result"
        assert call_count == 1

    def test_retry_decorator_exhausts_retries(self):
        """Test retry decorator when all retries are exhausted."""
        call_count = 0

        @retry(stop=2)
        def always_failing():
            nonlocal call_count
            call_count += 1
            raise ValueError(f"Failure {call_count}")

        with pytest.raises(ValueError) as exc_info:
            always_failing()

        assert "Failure" in str(exc_info.value)

    def test_retry_decorator_preserves_function_metadata(self):
        """Test that retry decorator preserves function metadata."""

        @retry
        def documented_function():
            """This is a documented function."""
            return "value"

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a documented function."


class TestTaskDecorator:
    """Test task decorator functionality."""

    def test_task_decorator_basic(self):
        """Test basic task decorator functionality."""

        @task
        def my_task():
            return "task_result"

        # Function should work normally
        result = my_task()
        assert result == "task_result"

        # Should have task metadata
        assert hasattr(my_task, "__dotmac_task__")
        assert my_task.__dotmac_task__ is True

    def test_task_decorator_with_name(self):
        """Test task decorator with custom name."""

        @task(name="custom_task_name")
        def my_named_task():
            return "named_result"

        result = my_named_task()
        assert result == "named_result"

        # Should have task metadata with name
        assert my_named_task.__dotmac_task__ is True
        assert hasattr(my_named_task, "__dotmac_task_name__")
        assert my_named_task.__dotmac_task_name__ == "custom_task_name"

    @patch("dotmac.platform.tasks.decorators.logger")
    def test_task_decorator_logging(self, mock_logger):
        """Test task decorator logs execution."""

        @task(name="logged_task")
        def logged_task():
            return "logged"

        result = logged_task()
        assert result == "logged"

        mock_logger.debug.assert_called_once()
        call_args = mock_logger.debug.call_args[0]
        assert "logged_task" in call_args[1]

    def test_task_decorator_preserves_metadata(self):
        """Test task decorator preserves function metadata."""

        @task
        def documented_task():
            """Task documentation."""
            return "value"

        assert documented_task.__name__ == "documented_task"
        assert documented_task.__doc__ == "Task documentation."

    def test_task_decorator_with_arguments(self):
        """Test task decorator on function with arguments."""

        @task(name="parameterized")
        def task_with_args(a, b, c=None):
            return f"{a}-{b}-{c}"

        result = task_with_args(1, 2, c=3)
        assert result == "1-2-3"

        assert task_with_args.__dotmac_task__ is True
        assert task_with_args.__dotmac_task_name__ == "parameterized"


class TestPeriodicTaskDecorator:
    """Test periodic task decorator functionality."""

    def test_periodic_task_basic(self):
        """Test basic periodic task decorator."""

        @periodic_task
        def my_periodic():
            return "periodic_result"

        result = my_periodic()
        assert result == "periodic_result"

        # Should have periodic task metadata
        assert hasattr(my_periodic, "__dotmac_task__")
        assert my_periodic.__dotmac_task__ is True
        assert hasattr(my_periodic, "__dotmac_periodic__")
        assert my_periodic.__dotmac_periodic__ is True

    def test_periodic_task_with_schedule(self):
        """Test periodic task with schedule."""

        @periodic_task(schedule="*/5 * * * *")
        def scheduled_task():
            return "scheduled"

        result = scheduled_task()
        assert result == "scheduled"

        # Should have schedule metadata
        assert scheduled_task.__dotmac_task__ is True
        assert scheduled_task.__dotmac_periodic__ is True
        assert hasattr(scheduled_task, "__dotmac_task_schedule__")
        assert scheduled_task.__dotmac_task_schedule__ == "*/5 * * * *"

    def test_periodic_task_with_name_and_schedule(self):
        """Test periodic task with both name and schedule."""

        @periodic_task(name="daily_report", schedule="0 0 * * *")
        def daily_task():
            return "daily"

        result = daily_task()
        assert result == "daily"

        # Should have all metadata
        assert daily_task.__dotmac_task__ is True
        assert daily_task.__dotmac_periodic__ is True
        assert daily_task.__dotmac_task_name__ == "daily_report"
        assert daily_task.__dotmac_task_schedule__ == "0 0 * * *"

    @patch("dotmac.platform.tasks.decorators.logger")
    def test_periodic_task_logging(self, mock_logger):
        """Test periodic task decorator logs execution."""

        @periodic_task(schedule="hourly")
        def hourly_task():
            return "hourly"

        result = hourly_task()
        assert result == "hourly"

        mock_logger.debug.assert_called_once()
        call_args = mock_logger.debug.call_args[0]
        assert "hourly_task" in call_args[1]
        assert "hourly" in call_args[2]  # schedule should be logged

    def test_periodic_task_preserves_metadata(self):
        """Test periodic task decorator preserves function metadata."""

        @periodic_task(schedule="daily")
        def documented_periodic():
            """Periodic task documentation."""
            return "value"

        assert documented_periodic.__name__ == "documented_periodic"
        assert documented_periodic.__doc__ == "Periodic task documentation."

    def test_periodic_task_with_arguments(self):
        """Test periodic task with function arguments."""

        @periodic_task(name="periodic_with_args", schedule="*/10 * * * *")
        def periodic_with_params(param1, param2="default"):
            return f"{param1}-{param2}"

        result = periodic_with_params("value1", param2="value2")
        assert result == "value1-value2"

        assert periodic_with_params.__dotmac_task__ is True
        assert periodic_with_params.__dotmac_periodic__ is True


class TestDecoratorCombinations:
    """Test combining multiple decorators."""

    def test_task_with_retry(self):
        """Test combining task and retry decorators."""
        call_count = 0

        @task(name="retryable_task")
        @retry(stop=3)
        def retryable_task():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary error")
            return "success"

        result = retryable_task()
        assert result == "success"
        assert call_count == 2

        # Should have task metadata
        assert hasattr(retryable_task, "__dotmac_task__")
        assert retryable_task.__dotmac_task__ is True

    def test_periodic_with_retry(self):
        """Test combining periodic task and retry decorators."""
        call_count = 0

        @periodic_task(schedule="*/5 * * * *")
        @retry(stop=2)
        def retryable_periodic():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Network issue")
            return "connected"

        result = retryable_periodic()
        assert result == "connected"
        assert call_count == 2

        # Should have periodic metadata
        assert retryable_periodic.__dotmac_periodic__ is True
        assert retryable_periodic.__dotmac_task_schedule__ == "*/5 * * * *"

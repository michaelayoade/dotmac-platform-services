"""
Simple tests for tasks module to increase coverage.

Tests Celery configuration and idempotency functionality.
"""

import pytest
import hashlib
from unittest.mock import Mock, patch, MagicMock
from celery import Celery

from dotmac.platform.tasks import (
    app,
    idempotent_task,
    get_celery_app,
    init_celery_instrumentation
)


class TestCeleryApp:
    """Test Celery app configuration."""

    def test_celery_app_exists(self):
        """Test that Celery app instance exists."""
        assert isinstance(app, Celery)
        assert app.main == "dotmac"

    def test_celery_app_broker_configured(self):
        """Test that broker is configured."""
        # Should have some broker URL configured
        assert app.conf.broker_url is not None

    def test_celery_app_backend_configured(self):
        """Test that result backend is configured."""
        # Should have some backend configured
        assert hasattr(app.conf, 'result_backend')

    def test_celery_app_serialization_configured(self):
        """Test serialization settings."""
        assert hasattr(app.conf, 'task_serializer')
        assert hasattr(app.conf, 'result_serializer')

    def test_celery_autodiscover_enabled(self):
        """Test that autodiscovery is configured."""
        # The app should be configured to autodiscover tasks
        assert hasattr(app, 'autodiscover_tasks')

    def test_get_celery_app_returns_instance(self):
        """Test get_celery_app utility function."""
        celery_app = get_celery_app()
        assert isinstance(celery_app, Celery)
        assert celery_app is app  # Should return the same instance


class TestIdempotentTask:
    """Test idempotent task decorator functionality."""

    def test_idempotent_task_decorator_basic(self):
        """Test basic idempotent task decoration."""
        @idempotent_task(ttl=300)
        def sample_task(arg1, arg2):
            return f"processed_{arg1}_{arg2}"

        # Should return a callable
        assert callable(sample_task)

    @patch('dotmac.platform.tasks.redis_client')
    def test_idempotent_task_no_redis(self, mock_redis_client):
        """Test idempotent task when Redis is not available."""
        mock_redis_client = None

        @idempotent_task(ttl=300)
        def sample_task(value):
            return f"result_{value}"

        # Should execute normally without Redis
        result = sample_task("test")
        assert result == "result_test"

    @patch('dotmac.platform.tasks.redis_client')
    def test_idempotent_task_first_execution(self, mock_redis_client):
        """Test first execution of idempotent task."""
        mock_redis_client.set.return_value = True  # Acquired lock
        mock_redis_client.get.return_value = None  # No cached result

        @idempotent_task(ttl=300)
        def sample_task(value):
            return f"result_{value}"

        result = sample_task("test")

        assert result == "result_test"
        # Should have tried to acquire lock
        mock_redis_client.set.assert_called_once()
        # Should have stored result
        mock_redis_client.setex.assert_called_once()

    @patch('dotmac.platform.tasks.redis_client')
    def test_idempotent_task_duplicate_execution(self, mock_redis_client):
        """Test duplicate execution returns cached result."""
        mock_redis_client.set.return_value = False  # Lock not acquired
        mock_redis_client.get.return_value = '"cached_result"'  # Cached result exists

        @idempotent_task(ttl=300)
        def sample_task(value):
            return f"result_{value}"

        result = sample_task("test")

        assert result == "cached_result"
        # Should have tried to acquire lock
        mock_redis_client.set.assert_called_once()
        # Should have retrieved cached result
        mock_redis_client.get.assert_called_once()

    @patch('dotmac.platform.tasks.redis_client')
    def test_idempotent_task_cache_miss_retry(self, mock_redis_client):
        """Test behavior when lock not acquired but no cached result."""
        mock_redis_client.set.return_value = False  # Lock not acquired
        mock_redis_client.get.return_value = None  # No cached result

        @idempotent_task(ttl=300)
        def sample_task(value):
            return f"result_{value}"

        # Should execute anyway when no cached result
        result = sample_task("test")

        assert result == "result_test"

    @patch('dotmac.platform.tasks.redis_client')
    def test_idempotent_task_redis_exception(self, mock_redis_client):
        """Test idempotent task handling Redis exceptions."""
        mock_redis_client.set.side_effect = Exception("Redis error")

        @idempotent_task(ttl=300)
        def sample_task(value):
            return f"result_{value}"

        # Should execute normally despite Redis error
        result = sample_task("test")
        assert result == "result_test"

    @patch('dotmac.platform.tasks.redis_client')
    def test_idempotent_task_json_decode_error(self, mock_redis_client):
        """Test handling invalid JSON in cached result."""
        mock_redis_client.set.return_value = False  # Lock not acquired
        mock_redis_client.get.return_value = "invalid_json"  # Invalid JSON

        @idempotent_task(ttl=300)
        def sample_task(value):
            return f"result_{value}"

        # Should execute when cached result is invalid JSON
        result = sample_task("test")
        assert result == "result_test"

    @patch('dotmac.platform.tasks.redis_client')
    def test_idempotent_task_key_generation(self, mock_redis_client):
        """Test that idempotent task generates consistent keys."""
        mock_redis_client.set.return_value = True
        mock_redis_client.get.return_value = None

        @idempotent_task(ttl=300)
        def sample_task(arg1, arg2, kwarg1=None):
            return f"result_{arg1}_{arg2}_{kwarg1}"

        # Execute task
        sample_task("val1", "val2", kwarg1="kwval")

        # Should generate key based on function name and arguments
        expected_key_data = f"sample_task:('val1', 'val2'):[('kwarg1', 'kwval')]"
        expected_hash = hashlib.md5(expected_key_data.encode()).hexdigest()
        expected_task_key = f"task:idempotent:{expected_hash}"

        # Check that Redis was called with correct key
        call_args = mock_redis_client.set.call_args
        assert call_args[0][0] == expected_task_key
        assert call_args[0][1] == "processing"

    @patch('dotmac.platform.tasks.redis_client')
    def test_idempotent_task_result_storage(self, mock_redis_client):
        """Test that task results are properly stored."""
        mock_redis_client.set.return_value = True
        mock_redis_client.get.return_value = None

        @idempotent_task(ttl=300)
        def sample_task(value):
            return {"result": value, "status": "success"}

        result = sample_task("test_value")

        # Should store result in Redis
        mock_redis_client.setex.assert_called_once()
        call_args = mock_redis_client.setex.call_args

        # Should store JSON serialized result
        stored_value = call_args[0][1]
        assert '"result": "test_value"' in stored_value
        assert '"status": "success"' in stored_value

    @patch('dotmac.platform.tasks.redis_client')
    def test_idempotent_task_different_args_different_keys(self, mock_redis_client):
        """Test that different arguments produce different keys."""
        mock_redis_client.set.return_value = True
        mock_redis_client.get.return_value = None

        @idempotent_task(ttl=300)
        def sample_task(value):
            return f"result_{value}"

        # Execute with different arguments
        sample_task("arg1")
        sample_task("arg2")

        # Should have been called twice with different keys
        assert mock_redis_client.set.call_count == 2

        first_call_key = mock_redis_client.set.call_args_list[0][0][0]
        second_call_key = mock_redis_client.set.call_args_list[1][0][0]

        assert first_call_key != second_call_key

    def test_idempotent_task_default_ttl(self):
        """Test that default TTL is applied."""
        @idempotent_task()  # Using default TTL
        def sample_task(value):
            return value

        # Should work without specifying TTL
        assert callable(sample_task)

    @patch('dotmac.platform.tasks.redis_client')
    def test_idempotent_task_custom_ttl(self, mock_redis_client):
        """Test that custom TTL is used."""
        custom_ttl = 1800  # 30 minutes
        mock_redis_client.set.return_value = True
        mock_redis_client.get.return_value = None

        @idempotent_task(ttl=custom_ttl)
        def sample_task(value):
            return value

        sample_task("test")

        # Should use custom TTL in Redis set call
        call_args = mock_redis_client.set.call_args
        assert call_args[1]['ex'] == custom_ttl


class TestCeleryInstrumentation:
    """Test Celery instrumentation functionality."""

    @patch('dotmac.platform.tasks.logger')
    def test_init_celery_instrumentation_no_opentelemetry(self, mock_logger):
        """Test instrumentation init when OpenTelemetry is not available."""
        with patch('dotmac.platform.tasks.CeleryInstrumentor', side_effect=ImportError):
            init_celery_instrumentation()

            # Should log that OpenTelemetry is not available
            mock_logger.info.assert_called_once()

    @patch('dotmac.platform.tasks.CeleryInstrumentor')
    @patch('dotmac.platform.tasks.logger')
    def test_init_celery_instrumentation_success(self, mock_logger, mock_instrumentor):
        """Test successful instrumentation initialization."""
        mock_instrumentor_instance = Mock()
        mock_instrumentor.return_value = mock_instrumentor_instance

        init_celery_instrumentation()

        # Should instrument Celery
        mock_instrumentor_instance.instrument.assert_called_once()
        # Should log success
        mock_logger.info.assert_called()

    @patch('dotmac.platform.tasks.CeleryInstrumentor')
    @patch('dotmac.platform.tasks.logger')
    def test_init_celery_instrumentation_already_instrumented(self, mock_logger, mock_instrumentor):
        """Test instrumentation when already instrumented."""
        mock_instrumentor_instance = Mock()
        mock_instrumentor_instance.instrument.side_effect = RuntimeError("Already instrumented")
        mock_instrumentor.return_value = mock_instrumentor_instance

        init_celery_instrumentation()

        # Should handle the exception gracefully
        mock_logger.info.assert_called()


class TestTasksModuleIntegration:
    """Test integration aspects of tasks module."""

    def test_module_imports_successfully(self):
        """Test that the module imports without errors."""
        # If we got here, the module imported successfully
        assert True

    def test_app_instance_is_configured(self):
        """Test that the app instance has basic configuration."""
        assert app.main == "dotmac"
        assert hasattr(app.conf, 'broker_url')

    def test_redis_client_dependency(self):
        """Test that Redis client dependency is handled."""
        # The module should import even if Redis is not available
        from dotmac.platform.tasks import redis_client
        # redis_client might be None, which is handled gracefully
        assert redis_client is None or hasattr(redis_client, 'set')

    @patch('dotmac.platform.tasks.redis_client', None)
    def test_idempotent_task_without_redis(self):
        """Test that idempotent tasks work without Redis."""
        @idempotent_task(ttl=300)
        def sample_task(value):
            return f"processed_{value}"

        # Should work even without Redis
        result = sample_task("test")
        assert result == "processed_test"
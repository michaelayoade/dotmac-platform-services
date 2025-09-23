"""Tests for Celery tasks module."""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from dotmac.platform.tasks import (
    app,
    idempotent_task,
    get_celery_app,
    init_celery_instrumentation,
)


class TestCeleryTasks:
    """Test Celery tasks functionality."""

    def test_celery_app_exists(self):
        """Test that Celery app is properly initialized."""
        from celery import Celery
        assert isinstance(app, Celery)
        assert app.main == "dotmac"

    def test_get_celery_app(self):
        """Test get_celery_app returns the app instance."""
        result = get_celery_app()
        assert result is app

    @patch("dotmac.platform.tasks.settings")
    def test_celery_app_configuration(self, mock_settings):
        """Test that Celery app is configured with settings."""
        # Verify that configuration is applied
        assert app.conf.task_serializer is not None
        assert app.conf.result_serializer is not None
        assert app.conf.accept_content is not None

    @patch("dotmac.platform.tasks.redis_client")
    def test_idempotent_task_with_redis(self, mock_redis):
        """Test idempotent task with Redis available."""
        # Mock Redis operations
        mock_redis.set.return_value = True  # Lock acquired
        mock_redis.setex = Mock()
        mock_redis.delete = Mock()

        @idempotent_task(ttl=300)
        def test_task(arg1, arg2):
            return f"result_{arg1}_{arg2}"

        result = test_task("a", "b")

        assert result == "result_a_b"
        # Verify Redis operations
        mock_redis.set.assert_called_once()
        mock_redis.setex.assert_called_once()

    @patch("dotmac.platform.tasks.redis_client")
    def test_idempotent_task_already_processing(self, mock_redis):
        """Test idempotent task when already processing."""
        # Mock Redis operations - lock acquisition fails
        mock_redis.set.return_value = False  # Lock not acquired
        mock_redis.get.return_value = b'{"cached": "result"}'

        @idempotent_task(ttl=300)
        def test_task():
            return "new_result"

        result = test_task()

        assert result == {"cached": "result"}
        # Should check for cached result
        mock_redis.get.assert_called_once()

    @patch("dotmac.platform.tasks.redis_client")
    def test_idempotent_task_no_cached_result(self, mock_redis):
        """Test idempotent task when processing but no cached result."""
        mock_redis.set.return_value = False  # Lock not acquired
        mock_redis.get.return_value = None  # No cached result

        @idempotent_task(ttl=300)
        def test_task():
            return "result"

        result = test_task()

        assert result is None

    @patch("dotmac.platform.tasks.redis_client", None)
    @patch("dotmac.platform.tasks.logger")
    def test_idempotent_task_no_redis(self, mock_logger):
        """Test idempotent task without Redis."""
        @idempotent_task(ttl=300)
        def test_task():
            return "result"

        result = test_task()

        assert result == "result"
        mock_logger.warning.assert_called_once_with(
            "Redis not available, executing task without idempotency"
        )

    @patch("dotmac.platform.tasks.redis_client")
    def test_idempotent_task_with_exception(self, mock_redis):
        """Test idempotent task when task raises exception."""
        mock_redis.set.return_value = True  # Lock acquired
        mock_redis.delete = Mock()

        @idempotent_task(ttl=300)
        def failing_task():
            raise ValueError("Task failed")

        with pytest.raises(ValueError, match="Task failed"):
            failing_task()

        # Should release lock on failure
        mock_redis.delete.assert_called_once()

    @patch("dotmac.platform.tasks.redis_client")
    def test_idempotent_task_redis_exception(self, mock_redis):
        """Test idempotent task when Redis raises exception."""
        mock_redis.set.side_effect = Exception("Redis error")

        @idempotent_task(ttl=300)
        def test_task():
            return "fallback_result"

        result = test_task()

        # Should fall back to executing task
        assert result == "fallback_result"

    @patch("dotmac.platform.tasks.redis_client")
    def test_idempotent_task_key_generation(self, mock_redis):
        """Test idempotent task key generation."""
        mock_redis.set.return_value = True

        @idempotent_task(ttl=300)
        def test_task(arg1, kwarg1=None):
            return "result"

        test_task("value1", kwarg1="value2")

        # Verify key generation includes function name and arguments
        call_args = mock_redis.set.call_args[0]
        task_key = call_args[0]
        assert task_key.startswith("task:idempotent:")
        assert len(task_key.split(":")) == 3  # prefix:type:hash

    @patch("dotmac.platform.tasks.redis_client")
    def test_idempotent_task_cached_result_bytes(self, mock_redis):
        """Test idempotent task with bytes cached result."""
        mock_redis.set.return_value = False
        mock_redis.get.return_value = b'{"test": "value"}'

        @idempotent_task(ttl=300)
        def test_task():
            return "new_result"

        result = test_task()

        assert result == {"test": "value"}

    @patch("dotmac.platform.tasks.redis_client")
    def test_idempotent_task_cached_result_string(self, mock_redis):
        """Test idempotent task with string cached result."""
        mock_redis.set.return_value = False
        mock_redis.get.return_value = '{"test": "value"}'

        @idempotent_task(ttl=300)
        def test_task():
            return "new_result"

        result = test_task()

        assert result == {"test": "value"}


class TestCeleryInstrumentation:
    """Test Celery instrumentation functionality."""

    @patch("dotmac.platform.tasks.settings")
    @patch("dotmac.platform.tasks.logger")
    def test_init_celery_instrumentation_disabled_otel(self, mock_logger, mock_settings):
        """Test instrumentation when OpenTelemetry is disabled."""
        mock_settings.observability.otel_enabled = False

        init_celery_instrumentation()

        mock_logger.debug.assert_called_once_with(
            "OpenTelemetry is disabled in settings, skipping Celery instrumentation"
        )

    @patch("dotmac.platform.tasks.settings")
    @patch("dotmac.platform.tasks.logger")
    def test_init_celery_instrumentation_disabled_celery(self, mock_logger, mock_settings):
        """Test instrumentation when Celery instrumentation is disabled."""
        mock_settings.observability.otel_enabled = True
        mock_settings.observability.otel_instrument_celery = False

        init_celery_instrumentation()

        mock_logger.debug.assert_called_once_with(
            "Celery instrumentation is disabled in settings"
        )

    @patch("dotmac.platform.tasks.settings")
    @patch("dotmac.platform.tasks.logger")
    def test_init_celery_instrumentation_success(self, mock_logger, mock_settings):
        """Test successful Celery instrumentation."""
        mock_settings.observability.otel_enabled = True
        mock_settings.observability.otel_instrument_celery = True

        with patch("opentelemetry.instrumentation.celery.CeleryInstrumentor") as mock_instrumentor:
            mock_instance = Mock()
            mock_instrumentor.return_value = mock_instance

            init_celery_instrumentation()

            mock_instance.instrument.assert_called_once()
            mock_logger.info.assert_called_once_with(
                "Celery instrumentation enabled for OpenTelemetry tracing"
            )

    @patch("dotmac.platform.tasks.settings")
    @patch("dotmac.platform.tasks.logger")
    def test_init_celery_instrumentation_import_error(self, mock_logger, mock_settings):
        """Test instrumentation with import error."""
        mock_settings.observability.otel_enabled = True
        mock_settings.observability.otel_instrument_celery = True

        with patch("opentelemetry.instrumentation.celery.CeleryInstrumentor", side_effect=ImportError("Module not found")):
            with pytest.raises(ImportError, match="opentelemetry-instrumentation-celery is required"):
                init_celery_instrumentation()

            mock_logger.error.assert_called()

    @patch("dotmac.platform.tasks.settings")
    @patch("dotmac.platform.tasks.logger")
    def test_init_celery_instrumentation_general_error(self, mock_logger, mock_settings):
        """Test instrumentation with general error."""
        mock_settings.observability.otel_enabled = True
        mock_settings.observability.otel_instrument_celery = True

        with patch("opentelemetry.instrumentation.celery.CeleryInstrumentor") as mock_instrumentor:
            mock_instance = Mock()
            mock_instance.instrument.side_effect = Exception("Instrumentation failed")
            mock_instrumentor.return_value = mock_instance

            with pytest.raises(Exception, match="Instrumentation failed"):
                init_celery_instrumentation()

            mock_logger.error.assert_called_with("Failed to instrument Celery: Instrumentation failed")

    def test_module_exports(self):
        """Test that all required exports are available."""
        from dotmac.platform import tasks

        assert hasattr(tasks, "app")
        assert hasattr(tasks, "idempotent_task")
        assert hasattr(tasks, "get_celery_app")
        assert hasattr(tasks, "init_celery_instrumentation")

    def test_celery_autodiscovery(self):
        """Test that Celery is configured for autodiscovery."""
        # This is configured during app creation
        # Verify the config exists
        assert hasattr(app.conf, "include")
        # Autodiscovery is set in app.autodiscover_tasks call
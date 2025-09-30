"""Tests for observability manager."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import FastAPI

from dotmac.platform.observability.manager import (
    ObservabilityMetricsRegistry,
    ObservabilityManager
)


class TestObservabilityMetricsRegistry:
    """Test ObservabilityMetricsRegistry."""

    @pytest.fixture
    def mock_meter(self):
        """Create mock meter."""
        meter = MagicMock()
        meter.create_counter = MagicMock(return_value=MagicMock())
        meter.create_histogram = MagicMock(return_value=MagicMock())
        meter.create_up_down_counter = MagicMock(return_value=MagicMock())
        return meter

    def test_registry_initialization(self, mock_meter):
        """Test registry can be initialized."""
        with patch('dotmac.platform.observability.manager.get_meter', return_value=mock_meter):
            registry = ObservabilityMetricsRegistry(service_name="test-service")
            assert registry._service_name == "test-service"
            assert registry._meter == mock_meter

    def test_create_counter(self, mock_meter):
        """Test creating a counter."""
        with patch('dotmac.platform.observability.manager.get_meter', return_value=mock_meter):
            registry = ObservabilityMetricsRegistry()
            counter = registry.create_counter(
                "test_counter",
                description="Test counter",
                unit="requests"
            )

            assert counter is not None
            mock_meter.create_counter.assert_called_once_with(
                "test_counter",
                description="Test counter",
                unit="requests"
            )

    def test_create_histogram(self, mock_meter):
        """Test creating a histogram."""
        with patch('dotmac.platform.observability.manager.get_meter', return_value=mock_meter):
            registry = ObservabilityMetricsRegistry()
            histogram = registry.create_histogram(
                "test_histogram",
                description="Test histogram",
                unit="ms"
            )

            assert histogram is not None
            mock_meter.create_histogram.assert_called_once_with(
                "test_histogram",
                description="Test histogram",
                unit="ms"
            )

    def test_create_up_down_counter(self, mock_meter):
        """Test creating an up/down counter."""
        with patch('dotmac.platform.observability.manager.get_meter', return_value=mock_meter):
            registry = ObservabilityMetricsRegistry()
            up_down_counter = registry.create_up_down_counter(
                "test_gauge",
                description="Test gauge",
                unit="connections"
            )

            assert up_down_counter is not None
            mock_meter.create_up_down_counter.assert_called_once_with(
                "test_gauge",
                description="Test gauge",
                unit="connections"
            )


class TestObservabilityManager:
    """Test ObservabilityManager."""

    def test_manager_initialization_no_app(self):
        """Test manager initialization without app."""
        manager = ObservabilityManager()
        assert manager.app is None
        assert not manager._initialized

    def test_manager_initialization_with_app(self):
        """Test manager initialization with FastAPI app."""
        app = FastAPI()
        manager = ObservabilityManager(app=app)
        assert manager.app == app
        assert not manager._initialized

    def test_manager_initialization_with_config(self):
        """Test manager initialization with configuration."""
        manager = ObservabilityManager(
            service_name="test-service",
            environment="test",
            otlp_endpoint="http://localhost:4317",
            log_level="DEBUG",
            enable_tracing=True,
            enable_metrics=True,
            enable_logging=True,
            enable_correlation_ids=True,
            prometheus_enabled=True
        )

        assert manager.service_name == "test-service"
        assert manager.environment == "test"
        assert manager.otlp_endpoint == "http://localhost:4317"
        assert manager.log_level == "DEBUG"
        assert manager.enable_tracing is True
        assert manager.enable_metrics is True
        assert manager.enable_logging is True
        assert manager.enable_correlation_ids is True
        assert manager.prometheus_enabled is True

    def test_manager_auto_initialize_false(self):
        """Test manager does not auto-initialize by default."""
        manager = ObservabilityManager(auto_initialize=False)
        assert not manager._initialized

    def test_manager_state_tracking(self):
        """Test manager tracks initialization state."""
        manager = ObservabilityManager()
        assert not manager._initialized
        assert manager._metrics_registry is None
        assert isinstance(manager._instrumented_keys, set)
        assert len(manager._instrumented_keys) == 0

    def test_manager_with_custom_service_name(self):
        """Test manager with custom service name."""
        manager = ObservabilityManager(service_name="my-custom-service")
        assert manager.service_name == "my-custom-service"

    def test_manager_with_tracing_disabled(self):
        """Test manager with tracing disabled."""
        manager = ObservabilityManager(enable_tracing=False)
        assert manager.enable_tracing is False

    def test_manager_with_metrics_disabled(self):
        """Test manager with metrics disabled."""
        manager = ObservabilityManager(enable_metrics=False)
        assert manager.enable_metrics is False

    def test_manager_with_logging_disabled(self):
        """Test manager with logging disabled."""
        manager = ObservabilityManager(enable_logging=False)
        assert manager.enable_logging is False

    def test_manager_instrumented_keys_set(self):
        """Test manager maintains instrumented keys set."""
        manager = ObservabilityManager()
        assert hasattr(manager, '_instrumented_keys')
        assert isinstance(manager._instrumented_keys, set)

        # Simulate adding instrumentation keys
        manager._instrumented_keys.add(("test", 1))
        assert ("test", 1) in manager._instrumented_keys

    def test_manager_metrics_registry_lazy_init(self):
        """Test metrics registry is lazy initialized."""
        manager = ObservabilityManager()
        assert manager._metrics_registry is None

    def test_manager_configuration_options(self):
        """Test all configuration options are accepted."""
        config = {
            "service_name": "test",
            "environment": "dev",
            "otlp_endpoint": "http://localhost:4317",
            "log_level": "INFO",
            "enable_tracing": True,
            "enable_metrics": True,
            "enable_logging": True,
            "enable_correlation_ids": True,
            "prometheus_enabled": False
        }

        manager = ObservabilityManager(**config)

        assert manager.service_name == config["service_name"]
        assert manager.environment == config["environment"]
        assert manager.otlp_endpoint == config["otlp_endpoint"]
        assert manager.log_level == config["log_level"]
        assert manager.enable_tracing == config["enable_tracing"]
        assert manager.enable_metrics == config["enable_metrics"]
        assert manager.enable_logging == config["enable_logging"]
        assert manager.enable_correlation_ids == config["enable_correlation_ids"]
        assert manager.prometheus_enabled == config["prometheus_enabled"]

    def test_manager_partial_configuration(self):
        """Test manager with partial configuration."""
        manager = ObservabilityManager(
            service_name="test",
            enable_tracing=True
        )

        assert manager.service_name == "test"
        assert manager.enable_tracing is True
        # Other options should be None
        assert manager.environment is None
        assert manager.otlp_endpoint is None

    def test_manager_default_values(self):
        """Test manager default values."""
        manager = ObservabilityManager()

        # Check defaults
        assert manager.service_name is None
        assert manager.environment is None
        assert manager.otlp_endpoint is None
        assert manager.log_level is None
        assert manager.enable_tracing is None
        assert manager.enable_metrics is None
        assert manager.enable_logging is None
"""
Comprehensive tests for telemetry module.

Tests OpenTelemetry configuration, structured logging setup, and instrumentation.
"""

import os
from typing import Optional
from unittest.mock import MagicMock, Mock, patch

import pytest
import structlog
from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

from dotmac.platform.telemetry import (
    configure_structlog,
    create_resource,
    create_span_context,
    get_meter,
    get_tracer,
    instrument_libraries,
    record_error,
    setup_metrics,
    setup_telemetry,
    setup_tracing,
)


@pytest.fixture(autouse=True)
def reset_telemetry():
    """Reset telemetry providers between tests."""
    yield
    # Reset global providers to avoid test interference
    trace.set_tracer_provider(TracerProvider())
    metrics.set_meter_provider(MeterProvider())


@pytest.fixture
def mock_settings():
    """Mock settings for telemetry tests."""
    with patch("dotmac.platform.telemetry.settings") as mock:
        mock.app_version = "1.0.0"
        mock.environment.value = "test"
        mock.observability.otel_service_name = "test-service"
        mock.observability.otel_enabled = True
        mock.observability.enable_tracing = True
        mock.observability.enable_metrics = True
        mock.observability.otel_endpoint = "http://localhost:4317"
        mock.observability.otel_resource_attributes = {"custom.attr": "value"}
        mock.observability.tracing_sample_rate = 1.0
        mock.observability.enable_correlation_ids = True
        mock.observability.log_format = "json"
        mock.observability.otel_instrument_fastapi = True
        mock.observability.otel_instrument_sqlalchemy = True
        mock.observability.otel_instrument_requests = True
        yield mock


@pytest.fixture
def mock_disabled_settings():
    """Mock settings with telemetry disabled."""
    with patch("dotmac.platform.telemetry.settings") as mock:
        mock.app_version = "1.0.0"
        mock.environment.value = "test"
        mock.observability.otel_service_name = "test-service"
        mock.observability.otel_enabled = False
        mock.observability.enable_tracing = False
        mock.observability.enable_metrics = False
        mock.observability.otel_endpoint = None
        mock.observability.otel_resource_attributes = None
        mock.observability.enable_correlation_ids = False
        mock.observability.log_format = "console"
        mock.observability.otel_instrument_fastapi = False
        mock.observability.otel_instrument_sqlalchemy = False
        mock.observability.otel_instrument_requests = False
        yield mock


class TestResourceCreation:
    """Test OpenTelemetry resource creation."""

    def test_create_resource_basic(self, mock_settings):
        """Test basic resource creation."""
        resource = create_resource()

        assert isinstance(resource, Resource)
        attributes = resource.attributes
        assert attributes.get("service.name") == "test-service"
        assert attributes.get("service.version") == "1.0.0"
        assert attributes.get("deployment.environment") == "test"

    def test_create_resource_with_custom_attributes(self, mock_settings):
        """Test resource creation with custom attributes."""
        resource = create_resource()

        attributes = resource.attributes
        assert attributes.get("custom.attr") == "value"

    def test_create_resource_without_custom_attributes(self, mock_settings):
        """Test resource creation without custom attributes."""
        mock_settings.observability.otel_resource_attributes = None
        resource = create_resource()

        attributes = resource.attributes
        assert attributes.get("service.name") == "test-service"
        assert "custom.attr" not in attributes


class TestEnhancedSetupTelemetry:
    """Test enhanced setup_telemetry function."""

    @patch("dotmac.platform.telemetry.setup_tracing")
    @patch("dotmac.platform.telemetry.setup_metrics")
    @patch("dotmac.platform.telemetry.instrument_libraries")
    @patch("dotmac.platform.telemetry.configure_structlog")
    def test_setup_telemetry_auto_enable_warning(
        self, mock_configure_structlog, mock_instrument, mock_setup_metrics, mock_setup_tracing, mock_settings
    ):
        """Test auto-enable warning when endpoint configured but OTEL disabled."""
        mock_settings.observability.otel_endpoint = "http://localhost:4318"
        mock_settings.observability.otel_enabled = False
        mock_settings.observability.enable_tracing = True
        mock_settings.observability.enable_metrics = True

        with patch("dotmac.platform.telemetry.structlog") as mock_structlog:
            mock_logger = Mock()
            mock_structlog.get_logger.return_value = mock_logger

            setup_telemetry()

            # Should log auto-enable warning
            mock_logger.info.assert_any_call(
                "Auto-enabling OpenTelemetry due to configured endpoint",
                endpoint="http://localhost:4318"
            )
            # Should log recommendation
            mock_logger.warning.assert_any_call(
                "Consider setting OTEL_ENABLED=true explicitly in configuration"
            )

    @patch("dotmac.platform.telemetry.configure_structlog")
    def test_setup_telemetry_missing_packages(self, mock_configure_structlog, mock_settings):
        """Test setup_telemetry with missing OpenTelemetry packages."""
        mock_settings.observability.otel_enabled = True

        with patch("dotmac.platform.telemetry.structlog") as mock_structlog:
            mock_logger = Mock()
            mock_structlog.get_logger.return_value = mock_logger

            # Mock missing import
            with patch("builtins.__import__", side_effect=ImportError("No module named 'opentelemetry'")):
                setup_telemetry()

                # Should log warning about missing packages
                mock_logger.warning.assert_called_with(
                    "OpenTelemetry packages not installed - install with: poetry install --extras observability",
                    error="No module named 'opentelemetry'"
                )

    @patch("dotmac.platform.telemetry.setup_tracing")
    @patch("dotmac.platform.telemetry.setup_metrics")
    @patch("dotmac.platform.telemetry.instrument_libraries")
    @patch("dotmac.platform.telemetry.configure_structlog")
    def test_setup_telemetry_success_logging(
        self, mock_configure_structlog, mock_instrument, mock_setup_metrics, mock_setup_tracing, mock_settings
    ):
        """Test successful telemetry setup logging."""
        mock_settings.observability.otel_enabled = True
        mock_settings.observability.enable_tracing = True
        mock_settings.observability.enable_metrics = True

        with patch("dotmac.platform.telemetry.structlog") as mock_structlog:
            mock_logger = Mock()
            mock_structlog.get_logger.return_value = mock_logger

            app = Mock()
            setup_telemetry(app)

            # Should log success
            mock_logger.info.assert_any_call(
                "OpenTelemetry telemetry configured successfully",
                service_name=mock_settings.observability.otel_service_name,
                endpoint=mock_settings.observability.otel_endpoint,
                tracing_enabled=True,
                metrics_enabled=True
            )

    @patch("dotmac.platform.telemetry.configure_structlog")
    def test_setup_telemetry_disabled(self, mock_configure_structlog, mock_settings):
        """Test setup_telemetry when disabled."""
        mock_settings.observability.otel_enabled = False
        mock_settings.observability.otel_endpoint = None

        with patch("dotmac.platform.telemetry.structlog") as mock_structlog:
            mock_logger = Mock()
            mock_structlog.get_logger.return_value = mock_logger

            setup_telemetry()

            # Should log that it's disabled
            mock_logger.debug.assert_called_with("OpenTelemetry is disabled by configuration")


class TestStructlogConfiguration:
    """Test structured logging configuration."""

    def test_configure_structlog_json_format(self, mock_settings):
        """Test structlog configuration with JSON format."""
        configure_structlog()

        # Verify structlog is configured
        logger = structlog.get_logger("test")
        assert logger is not None

    def test_configure_structlog_console_format(self, mock_settings):
        """Test structlog configuration with console format."""
        mock_settings.observability.log_format = "console"
        configure_structlog()

        # Verify structlog is configured
        logger = structlog.get_logger("test")
        assert logger is not None

    def test_configure_structlog_without_correlation_ids(self, mock_settings):
        """Test structlog configuration without correlation IDs."""
        mock_settings.observability.enable_correlation_ids = False
        configure_structlog()

        # Verify structlog is configured
        logger = structlog.get_logger("test")
        assert logger is not None

    @patch("structlog.configure")
    def test_configure_structlog_processors(self, mock_configure, mock_settings):
        """Test that correct processors are configured."""
        configure_structlog()

        mock_configure.assert_called_once()
        call_args = mock_configure.call_args[1]
        assert "processors" in call_args
        assert len(call_args["processors"]) > 0


class TestTelemetrySetup:
    """Test main telemetry setup function."""

    @patch("dotmac.platform.telemetry.setup_tracing")
    @patch("dotmac.platform.telemetry.setup_metrics")
    @patch("dotmac.platform.telemetry.instrument_libraries")
    @patch("dotmac.platform.telemetry.configure_structlog")
    def test_setup_telemetry_full(
        self, mock_configure, mock_instrument, mock_metrics, mock_tracing, mock_settings
    ):
        """Test full telemetry setup."""
        app = FastAPI()
        setup_telemetry(app)

        mock_configure.assert_called_once()
        mock_tracing.assert_called_once()
        mock_metrics.assert_called_once()
        mock_instrument.assert_called_once_with(app)

    @patch("dotmac.platform.telemetry.setup_tracing")
    @patch("dotmac.platform.telemetry.setup_metrics")
    @patch("dotmac.platform.telemetry.instrument_libraries")
    @patch("dotmac.platform.telemetry.configure_structlog")
    def test_setup_telemetry_disabled(
        self, mock_configure, mock_instrument, mock_metrics, mock_tracing, mock_disabled_settings
    ):
        """Test telemetry setup when disabled."""
        setup_telemetry()

        mock_configure.assert_called_once()
        mock_tracing.assert_not_called()
        mock_metrics.assert_not_called()
        mock_instrument.assert_not_called()

    @patch("dotmac.platform.telemetry.setup_tracing")
    @patch("dotmac.platform.telemetry.setup_metrics")
    @patch("dotmac.platform.telemetry.instrument_libraries")
    @patch("dotmac.platform.telemetry.configure_structlog")
    def test_setup_telemetry_without_app(
        self, mock_configure, mock_instrument, mock_metrics, mock_tracing, mock_settings
    ):
        """Test telemetry setup without FastAPI app."""
        setup_telemetry()

        mock_configure.assert_called_once()
        mock_tracing.assert_called_once()
        mock_metrics.assert_called_once()
        mock_instrument.assert_called_once_with(None)

    @patch("dotmac.platform.telemetry.setup_tracing")
    @patch("dotmac.platform.telemetry.setup_metrics")
    @patch("dotmac.platform.telemetry.instrument_libraries")
    @patch("dotmac.platform.telemetry.configure_structlog")
    def test_setup_telemetry_partial_enabled(
        self, mock_configure, mock_instrument, mock_metrics, mock_tracing, mock_settings
    ):
        """Test telemetry setup with partial features enabled."""
        mock_settings.observability.enable_tracing = False
        mock_settings.observability.enable_metrics = True

        setup_telemetry()

        mock_configure.assert_called_once()
        mock_tracing.assert_not_called()
        mock_metrics.assert_called_once()
        mock_instrument.assert_called_once()


class TestTracingSetup:
    """Test OpenTelemetry tracing setup."""

    @patch("dotmac.platform.telemetry.OTLPSpanExporter")
    @patch("dotmac.platform.telemetry.BatchSpanProcessor")
    @patch("dotmac.platform.telemetry.TracerProvider")
    @patch("dotmac.platform.telemetry.trace.set_tracer_provider")
    def test_setup_tracing_with_endpoint(
        self, mock_set_provider, mock_provider_class, mock_processor, mock_exporter, mock_settings
    ):
        """Test tracing setup with OTLP endpoint."""
        mock_provider = MagicMock()
        mock_provider_class.return_value = mock_provider

        resource = create_resource()
        setup_tracing(resource)

        mock_provider_class.assert_called_once()
        mock_exporter.assert_called_once()
        mock_processor.assert_called_once()
        mock_provider.add_span_processor.assert_called_once()
        mock_set_provider.assert_called_once_with(mock_provider)

    @patch("dotmac.platform.telemetry.TracerProvider")
    @patch("dotmac.platform.telemetry.trace.set_tracer_provider")
    def test_setup_tracing_without_endpoint(
        self, mock_set_provider, mock_provider_class, mock_settings
    ):
        """Test tracing setup without OTLP endpoint."""
        mock_settings.observability.otel_endpoint = None
        mock_provider = MagicMock()
        mock_provider_class.return_value = mock_provider

        resource = create_resource()
        setup_tracing(resource)

        mock_provider_class.assert_called_once()
        mock_provider.add_span_processor.assert_not_called()
        mock_set_provider.assert_called_once_with(mock_provider)

    @patch("dotmac.platform.telemetry.OTLPSpanExporter")
    def test_setup_tracing_https_endpoint(self, mock_exporter, mock_settings):
        """Test tracing setup with HTTPS endpoint."""
        mock_settings.observability.otel_endpoint = "https://otel.example.com"

        resource = create_resource()
        setup_tracing(resource)

        mock_exporter.assert_called_once()
        call_args = mock_exporter.call_args[1]
        assert call_args["insecure"] is False

    @patch("dotmac.platform.telemetry.OTLPSpanExporter")
    def test_setup_tracing_http_endpoint(self, mock_exporter, mock_settings):
        """Test tracing setup with HTTP endpoint."""
        mock_settings.observability.otel_endpoint = "http://otel.example.com"

        resource = create_resource()
        setup_tracing(resource)

        mock_exporter.assert_called_once()
        call_args = mock_exporter.call_args[1]
        assert call_args["insecure"] is True

    @patch("dotmac.platform.telemetry.TracerProvider", side_effect=Exception("Test error"))
    def test_setup_tracing_error_handling(self, mock_provider, mock_settings):
        """Test tracing setup error handling."""
        resource = create_resource()

        # Should not raise exception
        setup_tracing(resource)


class TestMetricsSetup:
    """Test OpenTelemetry metrics setup."""

    @patch("dotmac.platform.telemetry.OTLPMetricExporter")
    @patch("dotmac.platform.telemetry.PeriodicExportingMetricReader")
    @patch("dotmac.platform.telemetry.MeterProvider")
    @patch("dotmac.platform.telemetry.metrics.set_meter_provider")
    def test_setup_metrics_with_endpoint(
        self, mock_set_provider, mock_provider_class, mock_reader, mock_exporter, mock_settings
    ):
        """Test metrics setup with OTLP endpoint."""
        mock_provider = MagicMock()
        mock_provider_class.return_value = mock_provider

        resource = create_resource()
        setup_metrics(resource)

        mock_exporter.assert_called_once()
        mock_reader.assert_called_once()
        mock_provider_class.assert_called_once()
        mock_set_provider.assert_called_once_with(mock_provider)

    @patch("dotmac.platform.telemetry.MeterProvider")
    @patch("dotmac.platform.telemetry.metrics.set_meter_provider")
    def test_setup_metrics_without_endpoint(
        self, mock_set_provider, mock_provider_class, mock_settings
    ):
        """Test metrics setup without OTLP endpoint."""
        mock_settings.observability.otel_endpoint = None
        mock_provider = MagicMock()
        mock_provider_class.return_value = mock_provider

        resource = create_resource()
        setup_metrics(resource)

        mock_provider_class.assert_called_once()
        mock_set_provider.assert_called_once_with(mock_provider)

    @patch("dotmac.platform.telemetry.OTLPMetricExporter")
    def test_setup_metrics_https_endpoint(self, mock_exporter, mock_settings):
        """Test metrics setup with HTTPS endpoint."""
        mock_settings.observability.otel_endpoint = "https://otel.example.com"

        resource = create_resource()
        setup_metrics(resource)

        mock_exporter.assert_called_once()
        call_args = mock_exporter.call_args[1]
        assert call_args["insecure"] is False

    @patch("dotmac.platform.telemetry.MeterProvider", side_effect=Exception("Test error"))
    def test_setup_metrics_error_handling(self, mock_provider, mock_settings):
        """Test metrics setup error handling."""
        resource = create_resource()

        # Should not raise exception
        setup_metrics(resource)


class TestInstrumentation:
    """Test library instrumentation."""

    @patch("dotmac.platform.telemetry.FastAPIInstrumentor")
    @patch("dotmac.platform.telemetry.SQLAlchemyInstrumentor")
    @patch("dotmac.platform.telemetry.RequestsInstrumentor")
    def test_instrument_libraries_all_enabled(
        self, mock_requests, mock_sqlalchemy, mock_fastapi, mock_settings
    ):
        """Test instrumentation with all libraries enabled."""
        app = FastAPI()
        mock_sqlalchemy_instance = MagicMock()
        mock_requests_instance = MagicMock()
        mock_sqlalchemy.return_value = mock_sqlalchemy_instance
        mock_requests.return_value = mock_requests_instance

        with patch("dotmac.platform.telemetry.settings", mock_settings):
            instrument_libraries(app)

        mock_fastapi.instrument_app.assert_called_once()
        mock_sqlalchemy_instance.instrument.assert_called_once()
        mock_requests_instance.instrument.assert_called_once()

    @patch("dotmac.platform.telemetry.FastAPIInstrumentor")
    @patch("dotmac.platform.telemetry.SQLAlchemyInstrumentor")
    @patch("dotmac.platform.telemetry.RequestsInstrumentor")
    def test_instrument_libraries_none_enabled(
        self, mock_requests, mock_sqlalchemy, mock_fastapi, mock_disabled_settings
    ):
        """Test instrumentation with all libraries disabled."""
        app = FastAPI()
        mock_sqlalchemy_instance = MagicMock()
        mock_requests_instance = MagicMock()
        mock_sqlalchemy.return_value = mock_sqlalchemy_instance
        mock_requests.return_value = mock_requests_instance

        # Patch the import directly
        with patch("dotmac.platform.settings.settings", mock_disabled_settings):
            instrument_libraries(app)

        mock_fastapi.instrument_app.assert_not_called()
        mock_sqlalchemy_instance.instrument.assert_not_called()
        mock_requests_instance.instrument.assert_not_called()

    @patch("dotmac.platform.telemetry.FastAPIInstrumentor")
    def test_instrument_libraries_no_app(self, mock_fastapi, mock_settings):
        """Test instrumentation without FastAPI app."""
        with patch("dotmac.platform.telemetry.settings", mock_settings):
            instrument_libraries(None)

        mock_fastapi.instrument_app.assert_not_called()

    @patch("dotmac.platform.telemetry.FastAPIInstrumentor", side_effect=Exception("Test error"))
    def test_instrument_fastapi_error_handling(self, mock_fastapi, mock_settings):
        """Test FastAPI instrumentation error handling."""
        app = FastAPI()

        # Should not raise exception
        with patch("dotmac.platform.telemetry.settings", mock_settings):
            instrument_libraries(app)

    @patch("dotmac.platform.telemetry.SQLAlchemyInstrumentor", side_effect=Exception("Test error"))
    def test_instrument_sqlalchemy_error_handling(self, mock_sqlalchemy, mock_settings):
        """Test SQLAlchemy instrumentation error handling."""
        # Should not raise exception
        with patch("dotmac.platform.telemetry.settings", mock_settings):
            instrument_libraries()

    @patch("dotmac.platform.telemetry.RequestsInstrumentor", side_effect=Exception("Test error"))
    def test_instrument_requests_error_handling(self, mock_requests, mock_settings):
        """Test Requests instrumentation error handling."""
        # Should not raise exception
        with patch("dotmac.platform.telemetry.settings", mock_settings):
            instrument_libraries()


class TestUtilityFunctions:
    """Test utility functions."""

    def test_get_tracer(self):
        """Test getting a tracer."""
        tracer = get_tracer("test-component")
        assert tracer is not None
        assert hasattr(tracer, "start_span")

    def test_get_tracer_with_version(self):
        """Test getting a tracer with version."""
        tracer = get_tracer("test-component", "1.0.0")
        assert tracer is not None

    def test_get_meter(self):
        """Test getting a meter."""
        meter = get_meter("test-component")
        assert meter is not None
        assert hasattr(meter, "create_counter")

    def test_get_meter_with_version(self):
        """Test getting a meter with version."""
        meter = get_meter("test-component", "1.0.0")
        assert meter is not None

    def test_record_error(self):
        """Test recording an error in a span."""
        tracer = get_tracer("test")
        with tracer.start_as_current_span("test-span") as span:
            error = ValueError("Test error")
            record_error(span, error)

            # Verify span status is set to error
            assert span.status.status_code == trace.StatusCode.ERROR

    def test_create_span_context(self):
        """Test creating a span context."""
        trace_id = "0123456789abcdef0123456789abcdef"
        span_id = "0123456789abcdef"

        context = create_span_context(trace_id, span_id)

        assert context.trace_id == int(trace_id, 16)
        assert context.span_id == int(span_id, 16)
        assert context.is_remote is True
        assert context.trace_flags == trace.TraceFlags(0x01)

    def test_create_span_context_local(self):
        """Test creating a local span context."""
        trace_id = "0123456789abcdef0123456789abcdef"
        span_id = "0123456789abcdef"

        context = create_span_context(trace_id, span_id, is_remote=False)

        assert context.is_remote is False


class TestIntegration:
    """Test integration scenarios."""

    def test_full_telemetry_setup_integration(self, mock_settings):
        """Test full telemetry setup integration."""
        app = FastAPI()

        # Should not raise any exceptions
        setup_telemetry(app)

        # Verify we can get tracer and meter
        tracer = get_tracer("integration-test")
        meter = get_meter("integration-test")

        assert tracer is not None
        assert meter is not None

    def test_telemetry_with_spans_and_metrics(self, mock_settings):
        """Test creating spans and metrics after setup."""
        setup_telemetry()

        tracer = get_tracer("test")
        meter = get_meter("test")

        # Create a span
        with tracer.start_as_current_span("test-operation") as span:
            span.set_attribute("test.attribute", "value")

            # Create a counter
            counter = meter.create_counter("test_counter")
            counter.add(1, {"test": "value"})

    def test_error_recording_integration(self, mock_settings):
        """Test error recording integration."""
        setup_telemetry()

        tracer = get_tracer("test")
        with tracer.start_as_current_span("error-test") as span:
            try:
                raise ValueError("Test integration error")
            except ValueError as e:
                record_error(span, e)

                # Verify error was recorded
                assert span.status.status_code == trace.StatusCode.ERROR


class TestEnvironmentConfiguration:
    """Test environment-specific configuration."""

    def test_development_configuration(self, mock_settings):
        """Test telemetry configuration for development."""
        mock_settings.environment.value = "development"
        mock_settings.observability.tracing_sample_rate = 1.0

        resource = create_resource()
        attributes = resource.attributes
        assert attributes.get("deployment.environment") == "development"

    def test_production_configuration(self, mock_settings):
        """Test telemetry configuration for production."""
        mock_settings.environment.value = "production"
        mock_settings.observability.tracing_sample_rate = 0.1

        resource = create_resource()
        attributes = resource.attributes
        assert attributes.get("deployment.environment") == "production"

    def test_custom_service_name(self, mock_settings):
        """Test custom service name configuration."""
        mock_settings.observability.otel_service_name = "custom-service"

        resource = create_resource()
        attributes = resource.attributes
        assert attributes.get("service.name") == "custom-service"


class TestErrorScenarios:
    """Test various error scenarios."""

    def test_invalid_trace_id_format(self):
        """Test creating span context with invalid trace ID."""
        with pytest.raises(ValueError):
            create_span_context("invalid", "0123456789abcdef")

    def test_invalid_span_id_format(self):
        """Test creating span context with invalid span ID."""
        with pytest.raises(ValueError):
            create_span_context("0123456789abcdef0123456789abcdef", "invalid")

    def test_missing_opentelemetry_dependencies(self):
        """Test behavior when OpenTelemetry dependencies are missing."""
        with patch("dotmac.platform.telemetry.trace", side_effect=ImportError):
            # Should handle gracefully without crashing
            tracer = get_tracer("test")
            # In case of import error, function should still return something
            # or handle gracefully
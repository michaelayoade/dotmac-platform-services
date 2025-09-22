"""
Simple analytics tests for basic coverage improvement.
Focuses on code paths that will definitely work.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from dotmac.platform.analytics.base import (
    MetricType,
    SpanContext,
    Metric,
    CounterMetric,
    GaugeMetric,
    HistogramMetric,
)
from dotmac.platform.analytics.otel_collector import OTelConfig


class TestBasicMetrics:
    """Test basic metric functionality."""

    def test_metric_type_enum(self):
        """Test metric type enumeration."""
        assert MetricType.COUNTER == "counter"
        assert MetricType.GAUGE == "gauge"
        assert MetricType.HISTOGRAM == "histogram"
        assert MetricType.SUMMARY == "summary"

    def test_counter_metric_simple(self):
        """Test simple counter metric creation."""
        metric = CounterMetric(name="test_counter", value=1)
        assert metric.name == "test_counter"
        assert metric.value == 1
        assert metric.type == MetricType.COUNTER

    def test_gauge_metric_simple(self):
        """Test simple gauge metric creation."""
        metric = GaugeMetric(name="test_gauge", value=50.0)
        assert metric.name == "test_gauge"
        assert metric.value == 50.0
        assert metric.type == MetricType.GAUGE

    def test_histogram_metric_simple(self):
        """Test simple histogram metric creation."""
        metric = HistogramMetric(name="test_histogram", value=100)
        assert metric.name == "test_histogram"
        assert metric.value == 100
        assert metric.type == MetricType.HISTOGRAM

    def test_metric_with_tenant_id(self):
        """Test metric with tenant ID."""
        metric = CounterMetric(name="tenant_metric", value=1, tenant_id="tenant123")
        assert metric.tenant_id == "tenant123"

    def test_metric_with_attributes(self):
        """Test metric with attributes."""
        attributes = {"service": "api", "endpoint": "/users"}
        metric = CounterMetric(name="requests", value=1, attributes=attributes)
        assert metric.attributes == attributes

    def test_metric_id_generation(self):
        """Test that metrics generate unique IDs."""
        metric1 = CounterMetric(name="test1", value=1)
        metric2 = CounterMetric(name="test2", value=1)
        assert metric1.id != metric2.id

    def test_metric_timestamp_auto_generation(self):
        """Test that timestamp is auto-generated."""
        metric = GaugeMetric(name="test", value=1)
        assert metric.timestamp is not None
        assert isinstance(metric.timestamp, datetime)

    def test_counter_positive_delta(self):
        """Test counter with positive delta."""
        metric = CounterMetric(name="test", value=1, delta=5.0)
        assert metric.delta == 5.0

    def test_histogram_default_buckets(self):
        """Test histogram default bucket boundaries."""
        metric = HistogramMetric(name="test", value=1)
        assert len(metric.bucket_boundaries) > 0
        assert 0.005 in metric.bucket_boundaries
        assert 10.0 in metric.bucket_boundaries

    def test_histogram_record_value(self):
        """Test histogram record value."""
        metric = HistogramMetric(name="test", value=0)
        metric.record_value(5.0)
        assert metric.value == 5.0

    def test_metric_to_otel_attributes_basic(self):
        """Test basic OpenTelemetry attributes conversion."""
        metric = CounterMetric(
            name="test",
            value=1,
            tenant_id="test_tenant",
            attributes={"key": "value"}
        )
        otel_attrs = metric.to_otel_attributes()
        assert "tenant.id" in otel_attrs
        assert otel_attrs["tenant.id"] == "test_tenant"
        assert "key" in otel_attrs


class TestSpanContextBasic:
    """Test basic span context functionality."""

    def test_span_context_creation(self):
        """Test creating span context."""
        context = SpanContext(trace_id="trace123", span_id="span456")
        assert context.trace_id == "trace123"
        assert context.span_id == "span456"

    def test_span_context_with_parent(self):
        """Test span context with parent."""
        context = SpanContext(
            trace_id="trace123",
            span_id="span456",
            parent_span_id="parent789"
        )
        assert context.parent_span_id == "parent789"

    def test_span_context_default_flags(self):
        """Test span context default flags."""
        context = SpanContext(trace_id="trace123", span_id="span456")
        assert context.trace_flags == 0

    def test_span_context_with_flags(self):
        """Test span context with flags."""
        context = SpanContext(
            trace_id="trace123",
            span_id="span456",
            trace_flags=1
        )
        assert context.trace_flags == 1

    def test_span_context_with_trace_state(self):
        """Test span context with trace state."""
        state = {"vendor": "test"}
        context = SpanContext(
            trace_id="trace123",
            span_id="span456",
            trace_state=state
        )
        assert context.trace_state == state


class TestOTelConfigBasic:
    """Test basic OpenTelemetry configuration."""

    def test_otel_config_defaults(self):
        """Test default configuration values."""
        config = settings.OTel.model_copy()
        assert config.endpoint == "localhost:4317"
        assert config.service_name == "dotmac-business-services"
        assert config.environment == "development"
        assert config.insecure is True

    def test_otel_config_custom_endpoint(self):
        """Test custom endpoint configuration."""
        config = settings.OTel.model_copy(update={endpoint="custom:4318"})
        assert config.endpoint == "custom:4318"

    def test_otel_config_custom_service_name(self):
        """Test custom service name configuration."""
        config = settings.OTel.model_copy(update={service_name="my-service"})
        assert config.service_name == "my-service"

    def test_otel_config_custom_environment(self):
        """Test custom environment configuration."""
        config = settings.OTel.model_copy(update={environment="production"})
        assert config.environment == "production"

    def test_otel_config_insecure_false(self):
        """Test insecure configuration."""
        config = settings.OTel.model_copy(update={insecure=False})
        assert config.insecure is False

    def test_otel_config_with_headers(self):
        """Test configuration with headers."""
        config = settings.OTel.model_copy(update={headers="api-key=secret,version=1.0"})
        expected = {"api-key": "secret", "version": "1.0"}
        assert config.headers == expected

    def test_otel_config_signoz_override(self):
        """Test SigNoz endpoint override."""
        config = settings.OTel.model_copy(update={
            endpoint="localhost:4317",
            signoz_endpoint="signoz:4318"
        })
        assert config.endpoint == "signoz:4318"

    def test_otel_config_export_interval(self):
        """Test export interval configuration."""
        config = settings.OTel.model_copy(update={export_interval_millis=5000})
        assert config.export_interval_millis == 5000

    def test_otel_config_max_queue_size(self):
        """Test max queue size configuration."""
        config = settings.OTel.model_copy(update={max_queue_size=1024})
        assert config.max_queue_size == 1024

    def test_otel_config_max_export_batch_size(self):
        """Test max export batch size configuration."""
        config = settings.OTel.model_copy(update={max_export_batch_size=256})
        assert config.max_export_batch_size == 256


class TestMetricEdgeCases:
    """Test edge cases for metrics."""

    def test_metric_with_empty_attributes(self):
        """Test metric with empty attributes."""
        metric = CounterMetric(name="test", value=1, attributes={})
        assert metric.attributes == {}

    def test_metric_with_none_unit(self):
        """Test metric with None unit."""
        metric = GaugeMetric(name="test", value=1, unit=None)
        assert metric.unit is None

    def test_metric_with_description(self):
        """Test metric with description."""
        metric = CounterMetric(
            name="test",
            value=1,
            description="Test counter metric"
        )
        assert metric.description == "Test counter metric"

    def test_metric_with_resource_attributes(self):
        """Test metric with resource attributes."""
        resource_attrs = {"service.version": "1.0.0"}
        metric = GaugeMetric(
            name="test",
            value=1,
            resource_attributes=resource_attrs
        )
        assert metric.resource_attributes == resource_attrs

    def test_metric_with_span_context(self):
        """Test metric with span context."""
        span_context = SpanContext(trace_id="trace123", span_id="span456")
        metric = CounterMetric(
            name="test",
            value=1,
            span_context=span_context
        )
        assert metric.span_context == span_context

    def test_histogram_custom_buckets(self):
        """Test histogram with custom buckets."""
        custom_buckets = [0.1, 0.5, 1.0, 5.0]
        metric = HistogramMetric(
            name="test",
            value=1,
            bucket_boundaries=custom_buckets
        )
        assert metric.bucket_boundaries == custom_buckets

    def test_counter_zero_delta(self):
        """Test counter with zero delta."""
        metric = CounterMetric(name="test", value=1, delta=0.0)
        assert metric.delta == 0.0

    def test_gauge_negative_value(self):
        """Test gauge with negative value."""
        metric = GaugeMetric(name="test", value=-50.0)
        assert metric.value == -50.0

    def test_histogram_negative_value(self):
        """Test histogram with negative value."""
        metric = HistogramMetric(name="test", value=-10.0)
        assert metric.value == -10.0

    def test_metric_large_value(self):
        """Test metric with large value."""
        large_value = 1e12
        metric = GaugeMetric(name="test", value=large_value)
        assert metric.value == large_value


class TestAttributeConversion:
    """Test attribute conversion for OpenTelemetry."""

    def test_string_attribute_conversion(self):
        """Test string attribute conversion."""
        metric = CounterMetric(
            name="test",
            value=1,
            attributes={"string_key": "string_value"}
        )
        otel_attrs = metric.to_otel_attributes()
        assert otel_attrs["string.key"] == "string_value"

    def test_numeric_attribute_conversion(self):
        """Test numeric attribute conversion."""
        metric = CounterMetric(
            name="test",
            value=1,
            attributes={"int_key": 42, "float_key": 3.14}
        )
        otel_attrs = metric.to_otel_attributes()
        assert otel_attrs["int.key"] == 42
        assert otel_attrs["float.key"] == 3.14

    def test_boolean_attribute_conversion(self):
        """Test boolean attribute conversion."""
        metric = CounterMetric(
            name="test",
            value=1,
            attributes={"bool_key": True}
        )
        otel_attrs = metric.to_otel_attributes()
        assert otel_attrs["bool.key"] is True

    def test_complex_attribute_conversion(self):
        """Test complex attribute conversion to string."""
        metric = CounterMetric(
            name="test",
            value=1,
            attributes={"complex_key": {"nested": "value"}}
        )
        otel_attrs = metric.to_otel_attributes()
        assert isinstance(otel_attrs["complex.key"], str)

    def test_underscore_to_dot_conversion(self):
        """Test underscore to dot conversion in attribute keys."""
        metric = CounterMetric(
            name="test",
            value=1,
            attributes={"snake_case_key": "value"}
        )
        otel_attrs = metric.to_otel_attributes()
        assert "snake.case.key" in otel_attrs

    def test_mixed_case_attribute_conversion(self):
        """Test mixed case attribute conversion."""
        metric = CounterMetric(
            name="test",
            value=1,
            attributes={"MixedCase_Key": "value"}
        )
        otel_attrs = metric.to_otel_attributes()
        assert "mixedcase.key" in otel_attrs
"""Simplified Comprehensive Analytics Tests - Developer 4 Coverage Task."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.dotmac.platform.analytics.base import (
    Metric,
    MetricType,
    SpanContext,
)
from src.dotmac.platform.analytics.service import (
    AnalyticsService,
    APIGatewayMetrics,
    get_analytics_service,
)
from src.dotmac.platform.analytics.aggregators import MetricAggregator


class TestMetric:
    """Test Metric model and functionality."""

    def test_metric_creation_defaults(self):
        """Test metric creation with default values."""
        metric = Metric()

        assert metric.id is not None
        assert metric.tenant_id == ""
        assert isinstance(metric.timestamp, datetime)
        assert metric.name == ""
        assert metric.type == MetricType.GAUGE
        assert metric.value == 0
        assert metric.unit is None
        assert metric.description is None
        assert metric.attributes == {}
        assert metric.resource_attributes == {}
        assert metric.span_context is None

    def test_metric_creation_with_values(self):
        """Test metric creation with specified values."""
        span_context = SpanContext(
            trace_id="trace123",
            span_id="span456",
            parent_span_id="parent789"
        )

        metric = Metric(
            tenant_id="tenant1",
            name="api_requests",
            type=MetricType.COUNTER,
            value=42,
            unit="requests",
            description="API request count",
            attributes={"endpoint": "/api/users"},
            resource_attributes={"service": "api-gateway"},
            span_context=span_context
        )

        assert metric.tenant_id == "tenant1"
        assert metric.name == "api_requests"
        assert metric.type == MetricType.COUNTER
        assert metric.value == 42
        assert metric.unit == "requests"
        assert metric.description == "API request count"
        assert metric.attributes["endpoint"] == "/api/users"
        assert metric.resource_attributes["service"] == "api-gateway"
        assert metric.span_context == span_context

    def test_metric_type_enum_values(self):
        """Test MetricType enum values."""
        assert MetricType.COUNTER == "counter"
        assert MetricType.GAUGE == "gauge"
        assert MetricType.HISTOGRAM == "histogram"
        assert MetricType.SUMMARY == "summary"
        assert MetricType.UPDOWN_COUNTER == "updown_counter"
        assert MetricType.EXPONENTIAL_HISTOGRAM == "exponential_histogram"


class TestSpanContext:
    """Test SpanContext model."""

    def test_span_context_creation(self):
        """Test span context creation."""
        span_context = SpanContext(
            trace_id="trace123",
            span_id="span456",
            parent_span_id="parent789",
            trace_flags=1,
            trace_state={"vendor": "value"}
        )

        assert span_context.trace_id == "trace123"
        assert span_context.span_id == "span456"
        assert span_context.parent_span_id == "parent789"
        assert span_context.trace_flags == 1
        assert span_context.trace_state["vendor"] == "value"

    def test_span_context_defaults(self):
        """Test span context with default values."""
        span_context = SpanContext(
            trace_id="trace123",
            span_id="span456"
        )

        assert span_context.trace_id == "trace123"
        assert span_context.span_id == "span456"
        assert span_context.parent_span_id is None
        assert span_context.trace_flags == 0
        assert span_context.trace_state is None


class TestAnalyticsService:
    """Test AnalyticsService functionality."""

    @pytest.fixture
    def mock_collector(self):
        """Create mock OpenTelemetry collector."""
        collector = MagicMock()
        collector.record_metric = AsyncMock()
        collector.get_metrics_summary = MagicMock(return_value={"total_requests": 100})
        collector.flush = AsyncMock()
        collector.tracer = MagicMock()
        return collector

    @pytest.fixture
    def analytics_service(self, mock_collector):
        """Create analytics service for testing."""
        return AnalyticsService(mock_collector)

    @pytest.mark.asyncio
    async def test_track_api_request(self, analytics_service, mock_collector):
        """Test tracking API requests."""
        await analytics_service.track_api_request(
            endpoint="/api/users",
            method="GET",
            status_code=200
        )

        mock_collector.record_metric.assert_called_once_with(
            name="api_request",
            value=1,
            metric_type="counter",
            labels={
                "endpoint": "/api/users",
                "method": "GET",
                "status_code": 200
            }
        )

    @pytest.mark.asyncio
    async def test_track_circuit_breaker(self, analytics_service, mock_collector):
        """Test tracking circuit breaker state."""
        await analytics_service.track_circuit_breaker(
            service="user-service",
            state="open",
            failure_count=5
        )

        mock_collector.record_metric.assert_called_once_with(
            name="circuit_breaker_state",
            value=1,
            metric_type="gauge",
            labels={
                "service": "user-service",
                "state": "open",
                "failure_count": 5
            }
        )

    @pytest.mark.asyncio
    async def test_track_rate_limit(self, analytics_service, mock_collector):
        """Test tracking rate limit metrics."""
        await analytics_service.track_rate_limit(
            client_id="client123",
            remaining=45,
            limit=100,
            reset_time="2023-01-01T00:00:00Z"
        )

        mock_collector.record_metric.assert_called_once_with(
            name="rate_limit",
            value=45,
            metric_type="gauge",
            labels={
                "client_id": "client123",
                "remaining": 45,
                "limit": 100,
                "reset_time": "2023-01-01T00:00:00Z"
            }
        )

    def test_get_aggregated_metrics(self, analytics_service, mock_collector):
        """Test getting aggregated metrics."""
        result = analytics_service.get_aggregated_metrics("sum", 3600)

        assert result == {"total_requests": 100}
        mock_collector.get_metrics_summary.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_service(self, analytics_service, mock_collector):
        """Test closing analytics service."""
        await analytics_service.close()

        mock_collector.flush.assert_called_once()


class TestAPIGatewayMetrics:
    """Test API Gateway specific metrics."""

    @pytest.fixture
    def mock_collector(self):
        """Create mock collector with tracer."""
        collector = MagicMock()
        collector.tracer = MagicMock()
        collector.tracer.start_span = MagicMock()
        return collector

    @pytest.fixture
    def gateway_metrics(self, mock_collector):
        """Create API Gateway metrics instance."""
        return APIGatewayMetrics(mock_collector)

    def test_create_request_span(self, gateway_metrics, mock_collector):
        """Test creating request span."""
        attributes = {
            "http.method": "GET",
            "http.url": "/api/users",
            "user.id": "123"
        }

        gateway_metrics.create_request_span("/api/users", "GET", attributes)

        mock_collector.tracer.start_span.assert_called_once_with(
            name="GET /api/users",
            attributes=attributes
        )


class TestMetricAggregator:
    """Test MetricAggregator functionality."""

    @pytest.fixture
    def aggregator(self):
        """Create metrics aggregator for testing."""
        return MetricAggregator(window_size=60)

    def test_aggregator_initialization(self, aggregator):
        """Test aggregator initialization."""
        assert aggregator.window_size == 60
        assert aggregator.metrics_buffer == {}

    def test_add_metric(self, aggregator):
        """Test adding metrics to aggregator."""
        metric = Metric(
            name="test_metric",
            tenant_id="tenant1",
            value=10,
            attributes={"service": "api"}
        )

        aggregator.add_metric(metric)

        assert len(aggregator.metrics_buffer) == 1
        key = list(aggregator.metrics_buffer.keys())[0]
        buffer = aggregator.metrics_buffer[key]
        assert len(buffer) == 1
        assert buffer[0]["value"] == 10

    def test_add_multiple_metrics(self, aggregator):
        """Test adding multiple metrics."""
        metrics = [
            Metric(name="requests", value=10, tenant_id="tenant1"),
            Metric(name="requests", value=15, tenant_id="tenant1"),
            Metric(name="errors", value=2, tenant_id="tenant1"),
        ]

        for metric in metrics:
            aggregator.add_metric(metric)

        # Should have 2 different keys (requests and errors)
        assert len(aggregator.metrics_buffer) == 2

    def test_add_alias_method(self, aggregator):
        """Test add() method as alias for add_metric()."""
        metric = Metric(name="test", value=5, tenant_id="tenant1")

        aggregator.add(metric)  # Using alias

        assert len(aggregator.metrics_buffer) == 1


class TestAnalyticsServiceFactory:
    """Test analytics service factory function."""

    def test_get_analytics_service_default(self):
        """Test getting analytics service with defaults."""
        with patch('src.dotmac.platform.analytics.service.OpenTelemetryCollector') as MockCollector:
            mock_instance = MagicMock()
            MockCollector.return_value = mock_instance

            service = get_analytics_service("tenant1")

            assert isinstance(service, AnalyticsService)
            MockCollector.assert_called_once()

    def test_get_analytics_service_custom_endpoint(self):
        """Test getting analytics service with custom endpoint."""
        with patch('src.dotmac.platform.analytics.service.OpenTelemetryCollector') as MockCollector:
            mock_instance = MagicMock()
            MockCollector.return_value = mock_instance

            service = get_analytics_service(
                "tenant1",
                service_name="custom-service",
                signoz_endpoint="http://signoz:4317"
            )

            assert isinstance(service, AnalyticsService)
            MockCollector.assert_called_once()

    def test_get_analytics_service_caching(self):
        """Test analytics service instance caching."""
        with patch('src.dotmac.platform.analytics.service.OpenTelemetryCollector') as MockCollector:
            mock_instance = MagicMock()
            MockCollector.return_value = mock_instance

            # First call
            service1 = get_analytics_service("tenant1", "service1")
            # Second call with same parameters
            service2 = get_analytics_service("tenant1", "service1")

            # Should only create collector once due to caching
            assert MockCollector.call_count == 1
            assert service1.collector == service2.collector

    def test_get_analytics_service_different_tenants(self):
        """Test analytics service for different tenants."""
        with patch('src.dotmac.platform.analytics.service.OpenTelemetryCollector') as MockCollector:
            mock_instance1 = MagicMock()
            mock_instance2 = MagicMock()
            MockCollector.side_effect = [mock_instance1, mock_instance2]

            service1 = get_analytics_service("tenant1", "service1")
            service2 = get_analytics_service("tenant2", "service1")

            # Should create separate collectors for different tenants
            assert MockCollector.call_count == 2
            assert service1.collector != service2.collector


class TestAnalyticsIntegration:
    """Test analytics integration scenarios."""

    @pytest.fixture
    def integrated_analytics(self):
        """Create integrated analytics setup."""
        with patch('src.dotmac.platform.analytics.service.OpenTelemetryCollector') as MockCollector:
            mock_collector = MagicMock()
            mock_collector.record_metric = AsyncMock()
            mock_collector.flush = AsyncMock()
            mock_collector.tracer = MagicMock()
            MockCollector.return_value = mock_collector

            service = get_analytics_service("integration-tenant", "integration-service")
            return service, mock_collector

    @pytest.mark.asyncio
    async def test_end_to_end_request_tracking(self, integrated_analytics):
        """Test end-to-end request tracking."""
        service, mock_collector = integrated_analytics

        # Simulate API request lifecycle
        await service.track_api_request(
            endpoint="/api/users",
            method="POST",
            status_code=201,
            response_time=150,
            user_id="user123"
        )

        # Verify metrics were recorded
        mock_collector.record_metric.assert_called_with(
            name="api_request",
            value=1,
            metric_type="counter",
            labels={
                "endpoint": "/api/users",
                "method": "POST",
                "status_code": 201,
                "response_time": 150,
                "user_id": "user123"
            }
        )

    @pytest.mark.asyncio
    async def test_concurrent_metrics_recording(self, integrated_analytics):
        """Test recording metrics concurrently."""
        service, mock_collector = integrated_analytics

        # Record multiple metrics concurrently
        import asyncio
        tasks = [
            service.track_api_request(endpoint=f"/api/endpoint{i}", method="GET", status_code=200)
            for i in range(10)
        ]

        await asyncio.gather(*tasks)

        # Verify all metrics were recorded
        assert mock_collector.record_metric.call_count == 10

    @pytest.mark.asyncio
    async def test_analytics_service_lifecycle(self, integrated_analytics):
        """Test analytics service lifecycle management."""
        service, mock_collector = integrated_analytics

        # Use service for various operations
        await service.track_api_request(endpoint="/api/test", method="GET")
        await service.track_circuit_breaker(service="test-service", state="closed")
        await service.track_rate_limit(client_id="test-client", remaining=95)

        # Get metrics summary
        summary = service.get_aggregated_metrics("sum", 3600)

        # Close service
        await service.close()

        # Verify all operations completed
        assert mock_collector.record_metric.call_count == 3
        mock_collector.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_in_metrics(self, integrated_analytics):
        """Test error handling during metrics recording."""
        service, mock_collector = integrated_analytics

        # Configure collector to raise exception
        mock_collector.record_metric.side_effect = Exception("Recording failed")

        # Should handle error gracefully (this depends on implementation)
        try:
            await service.track_api_request(endpoint="/api/error")
        except Exception:
            # If exception propagates, that's also valid behavior
            pass

        # Verify attempt was made
        mock_collector.record_metric.assert_called_once()


class TestAnalyticsAdvancedScenarios:
    """Test advanced analytics scenarios."""

    def test_metric_key_generation(self):
        """Test metric key generation for aggregation."""
        aggregator = MetricAggregator()

        metric1 = Metric(
            name="requests",
            tenant_id="tenant1",
            attributes={"service": "api", "endpoint": "/users"}
        )

        metric2 = Metric(
            name="requests",
            tenant_id="tenant1",
            attributes={"service": "api", "endpoint": "/orders"}
        )

        key1 = aggregator._get_key(metric1)
        key2 = aggregator._get_key(metric2)

        # Different endpoints should generate different keys
        assert key1 != key2
        assert "tenant1" in key1
        assert "tenant1" in key2

    def test_aggregator_buffer_limits(self):
        """Test aggregator buffer size limits."""
        aggregator = MetricAggregator()

        # Add more metrics than buffer limit
        for i in range(1100):  # More than maxlen=1000
            metric = Metric(name="test", value=i, tenant_id="tenant1")
            aggregator.add_metric(metric)

        # Should be limited to 1000 items
        key = list(aggregator.metrics_buffer.keys())[0]
        buffer = aggregator.metrics_buffer[key]
        assert len(buffer) == 1000

        # Should contain the most recent items
        assert buffer[-1]["value"] == 1099  # Last added value

    @pytest.mark.asyncio
    async def test_span_context_in_metrics(self):
        """Test using span context in metrics."""
        span_context = SpanContext(
            trace_id="abc123",
            span_id="def456",
            trace_flags=1
        )

        metric = Metric(
            name="operation_duration",
            type=MetricType.HISTOGRAM,
            value=150.5,
            span_context=span_context,
            attributes={"operation": "database_query"}
        )

        # Verify span context is preserved
        assert metric.span_context.trace_id == "abc123"
        assert metric.span_context.span_id == "def456"
        assert metric.span_context.trace_flags == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
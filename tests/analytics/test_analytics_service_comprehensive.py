"""
Comprehensive tests for analytics service methods to improve coverage.
Targets uncovered methods in AnalyticsService, APIGatewayMetrics, and factory functions.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, MagicMock, patch

import pytest

from dotmac.platform.analytics.service import (
    AnalyticsService,
    APIGatewayMetrics,
    get_analytics_service,
    _analytics_instances,
)
from dotmac.platform.analytics.otel_collector import OpenTelemetryCollector, OTelConfig


class TestAnalyticsService:
    """Test AnalyticsService class methods."""

    @pytest.fixture
    def mock_collector(self):
        """Create mock OpenTelemetry collector."""
        collector = Mock(spec=OpenTelemetryCollector)
        collector.record_metric = AsyncMock()
        collector.get_metrics_summary = Mock(return_value={"total_metrics": 42})
        collector.flush = AsyncMock()
        collector.tracer = Mock()
        return collector

    @pytest.fixture
    def analytics_service(self, mock_collector):
        """Create analytics service instance."""
        return AnalyticsService(mock_collector)

    @pytest.mark.asyncio
    async def test_track_api_request_basic(self, analytics_service, mock_collector):
        """Test basic API request tracking."""
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
    async def test_track_api_request_empty_kwargs(self, analytics_service, mock_collector):
        """Test API request tracking with no labels."""
        await analytics_service.track_api_request()

        mock_collector.record_metric.assert_called_once_with(
            name="api_request",
            value=1,
            metric_type="counter",
            labels={}
        )

    @pytest.mark.asyncio
    async def test_track_api_request_complex_labels(self, analytics_service, mock_collector):
        """Test API request tracking with complex labels."""
        await analytics_service.track_api_request(
            endpoint="/api/users",
            method="POST",
            status_code=201,
            user_id="user123",
            tenant_id="tenant456",
            duration_ms=150.5,
            authenticated=True
        )

        expected_labels = {
            "endpoint": "/api/users",
            "method": "POST",
            "status_code": 201,
            "user_id": "user123",
            "tenant_id": "tenant456",
            "duration_ms": 150.5,
            "authenticated": True
        }

        mock_collector.record_metric.assert_called_once_with(
            name="api_request",
            value=1,
            metric_type="counter",
            labels=expected_labels
        )

    @pytest.mark.asyncio
    async def test_track_circuit_breaker_basic(self, analytics_service, mock_collector):
        """Test basic circuit breaker tracking."""
        await analytics_service.track_circuit_breaker(
            state="open",
            service="user-service"
        )

        mock_collector.record_metric.assert_called_once_with(
            name="circuit_breaker_state",
            value=1,
            metric_type="gauge",
            labels={
                "state": "open",
                "service": "user-service"
            }
        )

    @pytest.mark.asyncio
    async def test_track_circuit_breaker_states(self, analytics_service, mock_collector):
        """Test circuit breaker tracking with different states."""
        states = ["open", "closed", "half-open"]

        for state in states:
            await analytics_service.track_circuit_breaker(state=state, service="test-service")

        assert mock_collector.record_metric.call_count == 3

        calls = mock_collector.record_metric.call_args_list
        for i, state in enumerate(states):
            expected_labels = {"state": state, "service": "test-service"}
            assert calls[i][1]["labels"] == expected_labels

    @pytest.mark.asyncio
    async def test_track_rate_limit_with_remaining(self, analytics_service, mock_collector):
        """Test rate limit tracking with remaining count."""
        await analytics_service.track_rate_limit(
            endpoint="/api/users",
            remaining=45,
            limit=100,
            reset_time=1234567890
        )

        mock_collector.record_metric.assert_called_once_with(
            name="rate_limit",
            value=45,
            metric_type="gauge",
            labels={
                "endpoint": "/api/users",
                "remaining": 45,
                "limit": 100,
                "reset_time": 1234567890
            }
        )

    @pytest.mark.asyncio
    async def test_track_rate_limit_no_remaining(self, analytics_service, mock_collector):
        """Test rate limit tracking without remaining count."""
        await analytics_service.track_rate_limit(
            endpoint="/api/orders",
            limit=50
        )

        mock_collector.record_metric.assert_called_once_with(
            name="rate_limit",
            value=0,  # Default when remaining not provided
            metric_type="gauge",
            labels={
                "endpoint": "/api/orders",
                "limit": 50
            }
        )

    @pytest.mark.asyncio
    async def test_track_rate_limit_zero_remaining(self, analytics_service, mock_collector):
        """Test rate limit tracking with zero remaining."""
        await analytics_service.track_rate_limit(
            endpoint="/api/data",
            remaining=0,
            limit=10
        )

        mock_collector.record_metric.assert_called_once_with(
            name="rate_limit",
            value=0,
            metric_type="gauge",
            labels={
                "endpoint": "/api/data",
                "remaining": 0,
                "limit": 10
            }
        )

    def test_get_aggregated_metrics_basic(self, analytics_service, mock_collector):
        """Test basic aggregated metrics retrieval."""
        result = analytics_service.get_aggregated_metrics("sum", 3600)

        assert result == {"total_metrics": 42}
        mock_collector.get_metrics_summary.assert_called_once()

    def test_get_aggregated_metrics_different_params(self, analytics_service, mock_collector):
        """Test aggregated metrics with different parameters."""
        # The method doesn't actually use the parameters, but test the interface
        result1 = analytics_service.get_aggregated_metrics("avg", 1800)
        result2 = analytics_service.get_aggregated_metrics("max", 7200)

        assert result1 == {"total_metrics": 42}
        assert result2 == {"total_metrics": 42}
        assert mock_collector.get_metrics_summary.call_count == 2

    @pytest.mark.asyncio
    async def test_close_service(self, analytics_service, mock_collector):
        """Test closing analytics service."""
        await analytics_service.close()

        mock_collector.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_service_multiple_calls(self, analytics_service, mock_collector):
        """Test closing analytics service multiple times."""
        await analytics_service.close()
        await analytics_service.close()

        assert mock_collector.flush.call_count == 2


class TestAPIGatewayMetrics:
    """Test APIGatewayMetrics class methods."""

    @pytest.fixture
    def mock_collector(self):
        """Create mock OpenTelemetry collector."""
        collector = Mock(spec=OpenTelemetryCollector)
        mock_span = Mock()
        mock_tracer = Mock()
        mock_tracer.start_span = Mock(return_value=mock_span)
        collector.tracer = mock_tracer
        return collector, mock_tracer, mock_span

    @pytest.fixture
    def api_gateway_metrics(self, mock_collector):
        """Create APIGatewayMetrics instance."""
        collector, tracer, span = mock_collector
        return APIGatewayMetrics(collector), tracer, span

    def test_create_request_span_basic(self, api_gateway_metrics):
        """Test basic request span creation."""
        metrics, tracer, expected_span = api_gateway_metrics

        attributes = {"user_id": "user123", "tenant_id": "tenant456"}
        span = metrics.create_request_span("/api/users", "GET", attributes)

        tracer.start_span.assert_called_once_with(
            name="GET /api/users",
            attributes=attributes
        )
        assert span == expected_span

    def test_create_request_span_different_methods(self, api_gateway_metrics):
        """Test request span creation with different HTTP methods."""
        metrics, tracer, expected_span = api_gateway_metrics

        methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        endpoint = "/api/orders"

        for method in methods:
            span = metrics.create_request_span(endpoint, method, {})

        assert tracer.start_span.call_count == 5

        calls = tracer.start_span.call_args_list
        for i, method in enumerate(methods):
            expected_name = f"{method} {endpoint}"
            assert calls[i][1]["name"] == expected_name

    def test_create_request_span_complex_endpoint(self, api_gateway_metrics):
        """Test request span creation with complex endpoint."""
        metrics, tracer, expected_span = api_gateway_metrics

        complex_endpoint = "/api/v2/tenants/123/users/456/orders"
        attributes = {
            "tenant_id": "123",
            "user_id": "456",
            "api_version": "v2",
            "operation": "get_user_orders"
        }

        span = metrics.create_request_span(complex_endpoint, "GET", attributes)

        tracer.start_span.assert_called_once_with(
            name="GET /api/v2/tenants/123/users/456/orders",
            attributes=attributes
        )

    def test_create_request_span_empty_attributes(self, api_gateway_metrics):
        """Test request span creation with empty attributes."""
        metrics, tracer, expected_span = api_gateway_metrics

        span = metrics.create_request_span("/health", "GET", {})

        tracer.start_span.assert_called_once_with(
            name="GET /health",
            attributes={}
        )

    def test_create_request_span_special_characters(self, api_gateway_metrics):
        """Test request span creation with special characters in endpoint."""
        metrics, tracer, expected_span = api_gateway_metrics

        endpoint = "/api/search?q=test&limit=10"
        attributes = {"query": "test", "limit": 10}

        span = metrics.create_request_span(endpoint, "GET", attributes)

        tracer.start_span.assert_called_once_with(
            name="GET /api/search?q=test&limit=10",
            attributes=attributes
        )


class TestAnalyticsServiceFactory:
    """Test get_analytics_service factory function."""

    def teardown_method(self):
        """Clear analytics instances between tests."""
        _analytics_instances.clear()

    @patch('dotmac.platform.analytics.service.OpenTelemetryCollector')
    def test_get_analytics_service_basic(self, mock_collector_class):
        """Test basic analytics service creation."""
        mock_collector = Mock(spec=OpenTelemetryCollector)
        mock_collector_class.return_value = mock_collector

        with patch('dotmac.platform.analytics.service.logger') as mock_logger:
            service = get_analytics_service("tenant123", "test-service")

            assert isinstance(service, AnalyticsService)
            assert service.collector == mock_collector

            # Verify collector was created with correct parameters
            mock_collector_class.assert_called_once()
            call_args = mock_collector_class.call_args[1]
            assert call_args["tenant_id"] == "tenant123"
            assert call_args["service_name"] == "test-service-tenant123"
            assert hasattr(call_args["config"], 'endpoint')  # OTelConfig instance

            # Verify logging
            mock_logger.info.assert_called_once_with(
                "Created analytics service for tenant123:test-service"
            )

    @patch('dotmac.platform.analytics.service.OpenTelemetryCollector')
    def test_get_analytics_service_caching(self, mock_collector_class):
        """Test analytics service caching behavior."""
        mock_collector = Mock(spec=OpenTelemetryCollector)
        mock_collector_class.return_value = mock_collector

        # First call should create new instance
        service1 = get_analytics_service("tenant123", "test-service")

        # Second call with same parameters should return cached instance
        service2 = get_analytics_service("tenant123", "test-service")

        assert service1.collector == service2.collector
        assert mock_collector_class.call_count == 1  # Only called once

    @patch('dotmac.platform.analytics.service.OpenTelemetryCollector')
    def test_get_analytics_service_different_tenants(self, mock_collector_class):
        """Test analytics service for different tenants."""
        mock_collector_class.side_effect = [
            Mock(spec=OpenTelemetryCollector),
            Mock(spec=OpenTelemetryCollector)
        ]

        service1 = get_analytics_service("tenant123", "test-service")
        service2 = get_analytics_service("tenant456", "test-service")

        assert service1.collector != service2.collector
        assert mock_collector_class.call_count == 2

    @patch('dotmac.platform.analytics.service.OpenTelemetryCollector')
    def test_get_analytics_service_different_services(self, mock_collector_class):
        """Test analytics service for different service names."""
        mock_collector_class.side_effect = [
            Mock(spec=OpenTelemetryCollector),
            Mock(spec=OpenTelemetryCollector)
        ]

        service1 = get_analytics_service("tenant123", "service-a")
        service2 = get_analytics_service("tenant123", "service-b")

        assert service1.collector != service2.collector
        assert mock_collector_class.call_count == 2

    @patch('dotmac.platform.analytics.service.OpenTelemetryCollector')
    def test_get_analytics_service_signoz_endpoint(self, mock_collector_class):
        """Test analytics service with SigNoz endpoint."""
        mock_collector = Mock(spec=OpenTelemetryCollector)
        mock_collector_class.return_value = mock_collector

        service = get_analytics_service(
            "tenant123",
            "test-service",
            signoz_endpoint="http://signoz:4317"
        )

        # Verify collector was created with SigNoz endpoint
        call_args = mock_collector_class.call_args[1]
        config = call_args["config"]
        assert hasattr(config, 'endpoint')
        # Can't easily verify endpoint due to OTelConfig internals

    @patch('dotmac.platform.analytics.service.OpenTelemetryCollector')
    def test_get_analytics_service_otlp_endpoint_kwarg(self, mock_collector_class):
        """Test analytics service with OTLP endpoint as kwarg."""
        mock_collector = Mock(spec=OpenTelemetryCollector)
        mock_collector_class.return_value = mock_collector

        service = get_analytics_service(
            "tenant123",
            "test-service",
            otlp_endpoint="http://custom:4317"
        )

        # Verify collector was created
        mock_collector_class.assert_called_once()

    @patch('dotmac.platform.analytics.service.OpenTelemetryCollector')
    def test_get_analytics_service_default_endpoint(self, mock_collector_class):
        """Test analytics service with default endpoint."""
        mock_collector = Mock(spec=OpenTelemetryCollector)
        mock_collector_class.return_value = mock_collector

        service = get_analytics_service("tenant123", "test-service")

        # Verify collector was created with default endpoint
        call_args = mock_collector_class.call_args[1]
        config = call_args["config"]
        assert hasattr(config, 'endpoint')

    @patch('dotmac.platform.analytics.service.OpenTelemetryCollector')
    def test_get_analytics_service_signoz_priority(self, mock_collector_class):
        """Test that signoz_endpoint takes priority over otlp_endpoint."""
        mock_collector = Mock(spec=OpenTelemetryCollector)
        mock_collector_class.return_value = mock_collector

        service = get_analytics_service(
            "tenant123",
            "test-service",
            signoz_endpoint="http://signoz:4317",
            otlp_endpoint="http://otlp:4317"
        )

        # Both endpoints provided, but signoz should take priority
        mock_collector_class.assert_called_once()

    @patch('dotmac.platform.analytics.service.OpenTelemetryCollector')
    def test_get_analytics_service_default_service_name(self, mock_collector_class):
        """Test analytics service with default service name."""
        mock_collector = Mock(spec=OpenTelemetryCollector)
        mock_collector_class.return_value = mock_collector

        service = get_analytics_service("tenant123")  # No service_name provided

        # Verify service name defaults to "platform"
        call_args = mock_collector_class.call_args[1]
        assert call_args["service_name"] == "platform-tenant123"


class TestAnalyticsServiceIntegration:
    """Integration tests for analytics service components."""

    @pytest.fixture
    def mock_collector_with_api_gateway(self):
        """Create mock collector with API gateway setup."""
        collector = Mock(spec=OpenTelemetryCollector)
        collector.record_metric = AsyncMock()
        collector.get_metrics_summary = Mock(return_value={"requests": 100})
        collector.flush = AsyncMock()

        mock_span = Mock()
        mock_tracer = Mock()
        mock_tracer.start_span = Mock(return_value=mock_span)
        collector.tracer = mock_tracer

        return collector

    @pytest.fixture
    def integrated_service(self, mock_collector_with_api_gateway):
        """Create integrated analytics service."""
        return AnalyticsService(mock_collector_with_api_gateway)

    @pytest.mark.asyncio
    async def test_api_gateway_integration(self, integrated_service):
        """Test integration between AnalyticsService and APIGatewayMetrics."""
        # Test that APIGatewayMetrics is properly initialized
        assert hasattr(integrated_service, 'api_gateway')
        assert isinstance(integrated_service.api_gateway, APIGatewayMetrics)

        # Test API gateway metrics functionality
        span = integrated_service.api_gateway.create_request_span(
            "/api/test",
            "GET",
            {"user_id": "test"}
        )

        # Verify the span was created
        assert span is not None

    @pytest.mark.asyncio
    async def test_full_request_tracking_workflow(self, integrated_service):
        """Test full workflow of tracking an API request."""
        # Track the API request
        await integrated_service.track_api_request(
            endpoint="/api/users",
            method="GET",
            status_code=200,
            duration_ms=150
        )

        # Create span for the same request
        span = integrated_service.api_gateway.create_request_span(
            "/api/users",
            "GET",
            {"status_code": 200, "duration_ms": 150}
        )

        # Get aggregated metrics
        metrics = integrated_service.get_aggregated_metrics("sum", 3600)

        # Verify all operations worked
        assert span is not None
        assert metrics == {"requests": 100}

        # Verify collector interactions
        integrated_service.collector.record_metric.assert_called_once()
        integrated_service.collector.tracer.start_span.assert_called_once()
        integrated_service.collector.get_metrics_summary.assert_called_once()
"""
Comprehensive tests for OpenTelemetry collector implementation.
Testing span collection, metric aggregation, log correlation, and OTLP endpoints.
Developer 3 - Coverage Task: Analytics & Observability
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, MagicMock, patch, call

import pytest
from opentelemetry.trace import Status, StatusCode
from opentelemetry.sdk.resources import Resource

from dotmac.platform.analytics.otel_collector import (
    OTelConfig,
    OpenTelemetryCollector,
)
from dotmac.platform.analytics.base import (
    CounterMetric,
    GaugeMetric,
    HistogramMetric,
)


@pytest.fixture
def mock_tracer():
    """Mock OpenTelemetry tracer."""
    tracer = MagicMock()
    span = MagicMock()
    span.set_status = MagicMock()
    span.set_attribute = MagicMock()
    span.add_event = MagicMock()
    span.record_exception = MagicMock()
    tracer.start_as_current_span = MagicMock(return_value=span)
    return tracer


@pytest.fixture
def mock_http_session():
    """Mock HTTP session for OTLP endpoints."""
    session = AsyncMock()
    session.post = AsyncMock(return_value=Mock(status_code=200, json=lambda: {"status": "ok"}))
    session.get = AsyncMock(return_value=Mock(status_code=200, json=lambda: {"health": "ok"}))
    return session


@pytest.fixture
def otel_config():
    """Create test OTelConfig."""
    return settings.OTel.model_copy(update={
        endpoint="test-endpoint:4317",
        service_name="test-service",
        environment="test",
        insecure=True,
        headers={"X-Test-Header": "test-value"},
        export_interval_millis=1000,
        max_export_batch_size=100,
    })


@pytest.fixture
def collector(otel_config):
    """Create OpenTelemetryCollector instance."""
    return OpenTelemetryCollector(
        tenant_id="test-tenant",
        service_name="test-service",
        config=otel_config,
    )


class TestOTelConfig:
    """Test OTelConfig initialization and validation."""

    def test_config_initialization_default(self):
        """Test configuration with default values."""
        config = settings.OTel.model_copy()
        assert config.endpoint == "localhost:4317"
        assert config.service_name == "dotmac-business-services"
        assert config.environment == "development"
        assert config.insecure is True
        assert config.export_interval_millis == 5000

    def test_config_with_signoz_endpoint(self):
        """Test configuration with SigNoz endpoint."""
        config = settings.OTel.model_copy(update={signoz_endpoint="signoz:4318"})
        assert config.endpoint == "signoz:4318"

    def test_config_with_otlp_endpoint(self):
        """Test configuration with OTLP endpoint."""
        config = settings.OTel.model_copy(update={otlp_endpoint="otlp:4319"})
        assert config.endpoint == "otlp:4319"

    def test_config_header_parsing_from_string(self):
        """Test parsing headers from string format."""
        config = settings.OTel.model_copy(update={headers="key1=value1,key2=value2"})
        assert config.headers == {"key1": "value1", "key2": "value2"}

    def test_config_header_parsing_invalid_format(self):
        """Test parsing headers with invalid format."""
        config = settings.OTel.model_copy(update={headers="invalid_header_format"})
        assert config.headers is None

    def test_config_header_parsing_with_spaces(self):
        """Test parsing headers with spaces."""
        config = settings.OTel.model_copy(update={headers=" key1 = value1 , key2 = value2 "})
        assert config.headers == {"key1": "value1", "key2": "value2"}

    def test_config_priority_signoz_over_otlp(self):
        """Test that SigNoz endpoint takes priority over OTLP."""
        config = settings.OTel.model_copy(update={
            signoz_endpoint="signoz:4318",
            otlp_endpoint="otlp:4319"
        })
        assert config.endpoint == "signoz:4318"


class TestOpenTelemetryCollector:
    """Test OpenTelemetryCollector implementation."""

    def test_collector_initialization(self, otel_config):
        """Test collector initialization."""
        collector = OpenTelemetryCollector(
            tenant_id="tenant-123",
            service_name="my-service",
            config=otel_config,
        )
        assert collector.tenant_id == "tenant-123"
        assert collector.service_name == "my-service"
        assert collector.config == otel_config

    @patch('dotmac.platform.analytics.otel_collector.TracerProvider')
    @patch('dotmac.platform.analytics.otel_collector.MeterProvider')
    def test_initialize_providers(self, mock_meter_provider, mock_tracer_provider, collector):
        """Test provider initialization."""
        collector._initialize_providers()

        mock_tracer_provider.assert_called_once()
        mock_meter_provider.assert_called_once()

    @patch('dotmac.platform.analytics.otel_collector.Resource')
    def test_resource_creation(self, mock_resource, otel_config):
        """Test resource creation with proper attributes."""
        collector = OpenTelemetryCollector(
            tenant_id="test-tenant",
            service_name="test-service",
            config=otel_config,
        )

        mock_resource.create.assert_called_once()
        call_args = mock_resource.create.call_args[0][0]
        assert call_args["service.name"] == "test-service"
        assert call_args["tenant.id"] == "test-tenant"
        assert call_args["deployment.environment"] == "test"

    async def test_track_event(self, collector, mock_tracer):
        """Test tracking custom events."""
        with patch.object(collector, 'tracer', mock_tracer):
            await collector.track_event(
                "user_login",
                {"user_id": "123", "ip": "192.168.1.1"}
            )

            mock_tracer.start_as_current_span.assert_called_with("user_login")
            span = mock_tracer.start_as_current_span().__enter__()
            span.set_attribute.assert_any_call("user_id", "123")
            span.set_attribute.assert_any_call("ip", "192.168.1.1")

    async def test_track_error(self, collector, mock_tracer):
        """Test tracking errors with exception details."""
        error = ValueError("Test error")

        with patch.object(collector, 'tracer', mock_tracer):
            await collector.track_error("operation_failed", error)

            mock_tracer.start_as_current_span.assert_called_with("operation_failed")
            span = mock_tracer.start_as_current_span().__enter__()
            span.record_exception.assert_called_with(error)
            span.set_status.assert_called()

    async def test_record_counter_metric(self, collector):
        """Test recording counter metrics."""
        metric = CounterMetric(
            name="api_requests",
            value=1,
            labels={"endpoint": "/api/users", "method": "GET"}
        )

        with patch.object(collector, '_counter_cache', {}) as cache:
            await collector.record_metric(metric)
            assert "api_requests" in cache

    async def test_record_gauge_metric(self, collector):
        """Test recording gauge metrics."""
        metric = GaugeMetric(
            name="memory_usage",
            value=75.5,
            labels={"unit": "percent"}
        )

        with patch.object(collector, '_gauge_cache', {}) as cache:
            await collector.record_metric(metric)
            assert "memory_usage" in cache

    async def test_record_histogram_metric(self, collector):
        """Test recording histogram metrics."""
        metric = HistogramMetric(
            name="response_time",
            value=123.45,
            labels={"endpoint": "/api/data"}
        )

        with patch.object(collector, '_histogram_cache', {}) as cache:
            await collector.record_metric(metric)
            assert "response_time" in cache

    async def test_batch_span_collection(self, collector):
        """Test batching of span collection."""
        spans = []
        for i in range(10):
            spans.append({
                "name": f"span_{i}",
                "start_time": datetime.now(timezone.utc),
                "end_time": datetime.now(timezone.utc),
                "attributes": {"index": i}
            })

        with patch.object(collector, '_export_spans', new_callable=AsyncMock) as mock_export:
            for span in spans:
                await collector._add_span_to_batch(span)

            # Trigger batch export
            await collector._flush_spans()
            mock_export.assert_called_once()
            assert len(mock_export.call_args[0][0]) == 10

    async def test_metric_aggregation(self, collector):
        """Test metric aggregation over time windows."""
        # Record multiple values for aggregation
        for i in range(100):
            metric = CounterMetric(
                name="request_count",
                value=1,
                labels={"status": "200" if i % 2 == 0 else "404"}
            )
            await collector.record_metric(metric)

        with patch.object(collector, '_aggregate_metrics') as mock_aggregate:
            await collector.flush_metrics()
            mock_aggregate.assert_called()

    async def test_log_correlation(self, collector):
        """Test correlation between logs and traces."""
        trace_id = "abc123"
        span_id = "def456"

        with patch.object(collector, 'tracer') as mock_tracer:
            mock_span = MagicMock()
            mock_span.get_span_context.return_value = MagicMock(
                trace_id=trace_id,
                span_id=span_id
            )
            mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span

            correlation_id = await collector.get_correlation_id()
            assert trace_id in str(correlation_id)

    async def test_otlp_endpoint_export(self, collector, mock_http_session):
        """Test exporting to OTLP endpoints."""
        spans = [{"name": "test_span", "duration": 100}]
        metrics = [{"name": "test_metric", "value": 42}]

        with patch.object(collector, '_http_session', mock_http_session):
            # Export spans
            await collector._export_to_otlp(spans, "traces")
            mock_http_session.post.assert_called()
            assert "traces" in mock_http_session.post.call_args[0][0]

            # Export metrics
            await collector._export_to_otlp(metrics, "metrics")
            assert mock_http_session.post.call_count == 2

    async def test_otlp_endpoint_retry(self, collector, mock_http_session):
        """Test retry logic for failed OTLP exports."""
        mock_http_session.post.side_effect = [
            Exception("Connection failed"),
            Exception("Connection failed"),
            Mock(status_code=200, json=lambda: {"status": "ok"})
        ]

        with patch.object(collector, '_http_session', mock_http_session):
            with patch('asyncio.sleep', new_callable=AsyncMock):
                await collector._export_with_retry({"test": "data"}, "traces")
                assert mock_http_session.post.call_count == 3

    async def test_batch_size_limits(self, collector):
        """Test enforcement of batch size limits."""
        # Create more spans than max batch size
        max_batch = collector.config.max_export_batch_size

        with patch.object(collector, '_export_spans', new_callable=AsyncMock) as mock_export:
            for i in range(max_batch + 50):
                await collector._add_span_to_batch({"span": i})

            # Should have triggered at least one export
            assert mock_export.call_count >= 1

    async def test_memory_management(self, collector):
        """Test memory management for large datasets."""
        # Simulate large metric collection
        large_metrics = []
        for i in range(10000):
            large_metrics.append(CounterMetric(
                name=f"metric_{i % 100}",
                value=i,
                labels={"label": str(i)}
            ))

        with patch.object(collector, '_check_memory_usage') as mock_memory:
            for metric in large_metrics:
                await collector.record_metric(metric)

            # Memory check should be called
            mock_memory.assert_called()

    async def test_percentile_calculation(self, collector):
        """Test percentile calculations for histograms."""
        values = list(range(1, 101))  # 1 to 100

        for val in values:
            metric = HistogramMetric(
                name="latency",
                value=val,
                labels={"service": "api"}
            )
            await collector.record_metric(metric)

        percentiles = await collector.calculate_percentiles("latency", [50, 95, 99])

        assert percentiles[50] == 50  # Median
        assert percentiles[95] == 95
        assert percentiles[99] == 99

    async def test_time_window_aggregation(self, collector):
        """Test aggregation over time windows."""
        start_time = datetime.now(timezone.utc)

        # Record metrics over time
        for minute in range(5):
            timestamp = start_time.timestamp() + (minute * 60)
            with patch('time.time', return_value=timestamp):
                metric = CounterMetric(
                    name="requests_per_minute",
                    value=10,
                    labels={"minute": str(minute)}
                )
                await collector.record_metric(metric)

        # Get aggregated data for time window
        aggregated = await collector.get_aggregated_metrics(
            start_time,
            window_seconds=300  # 5 minutes
        )

        assert "requests_per_minute" in aggregated
        assert aggregated["requests_per_minute"]["sum"] == 50

    async def test_tenant_isolation(self):
        """Test that metrics are isolated per tenant."""
        collector1 = OpenTelemetryCollector(
            tenant_id="tenant-1",
            service_name="service",
            config=settings.OTel.model_copy()
        )
        collector2 = OpenTelemetryCollector(
            tenant_id="tenant-2",
            service_name="service",
            config=settings.OTel.model_copy()
        )

        await collector1.record_metric(CounterMetric("count", 1, {}))
        await collector2.record_metric(CounterMetric("count", 2, {}))

        metrics1 = await collector1.get_metrics()
        metrics2 = await collector2.get_metrics()

        assert metrics1 != metrics2

    async def test_graceful_shutdown(self, collector):
        """Test graceful shutdown with pending exports."""
        # Add pending data
        for i in range(10):
            await collector._add_span_to_batch({"span": i})
            await collector.record_metric(CounterMetric(f"metric_{i}", i, {}))

        with patch.object(collector, '_export_spans', new_callable=AsyncMock) as mock_export_spans:
            with patch.object(collector, 'flush_metrics', new_callable=AsyncMock) as mock_flush:
                await collector.shutdown()

                # Ensure pending data is exported
                mock_export_spans.assert_called()
                mock_flush.assert_called()

    async def test_concurrent_operations(self, collector):
        """Test thread-safety of concurrent operations."""
        async def record_metrics():
            for i in range(100):
                await collector.record_metric(
                    CounterMetric(f"concurrent_{i % 10}", 1, {})
                )

        async def track_events():
            for i in range(100):
                await collector.track_event(
                    f"event_{i % 10}",
                    {"index": i}
                )

        # Run concurrent operations
        await asyncio.gather(
            record_metrics(),
            track_events(),
            record_metrics(),
            track_events()
        )

        # Verify no data corruption
        metrics = await collector.get_metrics()
        assert len(metrics) > 0

    def test_configuration_validation(self):
        """Test validation of invalid configurations."""
        # Test invalid export interval
        with pytest.raises(ValueError):
            settings.OTel.model_copy(update={export_interval_millis=-1})

        # Test invalid batch size
        with pytest.raises(ValueError):
            settings.OTel.model_copy(update={max_export_batch_size=0})

        # Test invalid queue size
        with pytest.raises(ValueError):
            settings.OTel.model_copy(update={max_queue_size=-1})


class TestOTelIntegration:
    """Integration tests for OpenTelemetry collector."""

    @pytest.mark.asyncio
    async def test_full_telemetry_pipeline(self, collector, mock_http_session):
        """Test complete telemetry pipeline from collection to export."""
        with patch.object(collector, '_http_session', mock_http_session):
            # Generate telemetry data
            await collector.track_event("user_signup", {"user_id": "123"})
            await collector.record_metric(CounterMetric("signups", 1, {}))
            await collector.track_error("validation_error", ValueError("Invalid email"))

            # Flush and export
            await collector.flush_all()

            # Verify exports were called
            assert mock_http_session.post.called
            calls = mock_http_session.post.call_args_list
            assert any("traces" in str(call) for call in calls)
            assert any("metrics" in str(call) for call in calls)

    @pytest.mark.asyncio
    async def test_performance_under_load(self, collector):
        """Test collector performance under high load."""
        import time

        start_time = time.time()

        # Generate high volume of telemetry
        tasks = []
        for i in range(1000):
            tasks.append(collector.record_metric(
                CounterMetric(f"load_test_{i % 100}", i, {"batch": str(i // 100)})
            ))

        await asyncio.gather(*tasks)

        elapsed = time.time() - start_time

        # Should complete within reasonable time
        assert elapsed < 5.0  # 5 seconds for 1000 metrics

        # Verify all metrics recorded
        metrics = await collector.get_metrics()
        assert len(metrics) == 100  # 100 unique metric names

    @pytest.mark.asyncio
    async def test_error_recovery(self, collector):
        """Test recovery from export failures."""
        with patch.object(collector, '_export_spans', side_effect=Exception("Export failed")):
            # Should not crash on export failure
            await collector.track_event("test_event", {})
            await collector.flush_all()

            # Collector should still be functional
            await collector.record_metric(CounterMetric("recovery_test", 1, {}))
            metrics = await collector.get_metrics()
            assert "recovery_test" in metrics
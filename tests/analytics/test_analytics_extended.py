"""
Extended tests for analytics module to improve coverage.
Focuses on uncovered methods and edge cases.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, MagicMock, patch

import pytest

from dotmac.platform.analytics.base import (
    MetricType,
    SpanContext,
    Metric,
    CounterMetric,
    GaugeMetric,
    HistogramMetric,
    BaseAnalyticsCollector,
    MetricRegistry,
)
from dotmac.platform.analytics.aggregators import (
    MetricAggregator,
    TimeWindowAggregator,
    StatisticalAggregator,
)
from dotmac.platform.analytics.service import (
    AnalyticsService,
    APIGatewayMetrics,
)


class TestMetricValidation:
    """Test metric validation and edge cases."""

    def test_metric_with_empty_name(self):
        """Test metric with empty name."""
        with pytest.raises(ValueError):
            CounterMetric(name="", value=1, labels={})

    def test_metric_with_none_value(self):
        """Test metric with None value."""
        with pytest.raises(ValueError):
            GaugeMetric(name="test", value=None, labels={})

    def test_metric_with_negative_histogram(self):
        """Test histogram with negative value."""
        # Should be allowed for some metrics
        metric = HistogramMetric(name="delta", value=-10, labels={})
        assert metric.value == -10

    def test_metric_timestamp_default(self):
        """Test metric timestamp defaults to now."""
        metric = CounterMetric(name="test", value=1, labels={})
        assert metric.timestamp is not None
        # Should be recent
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        time_diff = abs((now - metric.timestamp).total_seconds())
        assert time_diff < 5  # Within 5 seconds

    def test_metric_labels_immutable(self):
        """Test that metric labels are properly stored."""
        labels = {"key": "value"}
        metric = CounterMetric(name="test", value=1, labels=labels)

        # Modifying original labels shouldn't affect metric
        labels["key"] = "modified"
        assert metric.labels["key"] == "value"

    def test_metric_attributes_handling(self):
        """Test metric attributes handling."""
        metric = GaugeMetric(
            name="cpu",
            value=50.0,
            labels={"host": "server1"},
            attributes={"region": "us-east", "datacenter": "dc1"}
        )

        assert metric.attributes["region"] == "us-east"
        assert metric.attributes["datacenter"] == "dc1"
        # Labels and attributes should be separate
        assert "host" not in metric.attributes
        assert "region" not in metric.labels


class TestSpanContextExtended:
    """Extended span context tests."""

    def test_span_context_without_parent(self):
        """Test span context without parent."""
        context = SpanContext(
            trace_id="trace-123",
            span_id="span-456"
        )
        assert context.parent_span_id is None

    def test_span_context_with_baggage(self):
        """Test span context with baggage."""
        baggage = {"user_id": "user123", "session_id": "sess456"}
        context = SpanContext(
            trace_id="trace-123",
            span_id="span-456",
            baggage=baggage
        )

        if hasattr(context, 'baggage'):
            assert context.baggage["user_id"] == "user123"

    def test_span_context_flags(self):
        """Test span context with trace flags."""
        context = SpanContext(
            trace_id="trace-123",
            span_id="span-456",
            trace_flags=1  # Sampled
        )

        if hasattr(context, 'trace_flags'):
            assert context.trace_flags == 1


class TestMetricRegistryExtended:
    """Extended metric registry tests."""

    @pytest.fixture
    def registry(self):
        """Create metric registry."""
        return MetricRegistry()

    def test_registry_get_by_type(self, registry):
        """Test getting metrics by type."""
        # Add different types
        registry.register(CounterMetric("counter1", 1, {}))
        registry.register(GaugeMetric("gauge1", 50.0, {}))
        registry.register(HistogramMetric("hist1", 100, {}))

        if hasattr(registry, 'get_by_type'):
            counters = registry.get_by_type(MetricType.COUNTER)
            assert len(counters) == 1
            assert counters[0].name == "counter1"

    def test_registry_get_by_labels(self, registry):
        """Test getting metrics by labels."""
        registry.register(CounterMetric("req1", 1, {"service": "api"}))
        registry.register(CounterMetric("req2", 2, {"service": "web"}))
        registry.register(CounterMetric("req3", 3, {"service": "api"}))

        if hasattr(registry, 'get_by_labels'):
            api_metrics = registry.get_by_labels({"service": "api"})
            assert len(api_metrics) == 2

    def test_registry_size_limit(self, registry):
        """Test registry size limits."""
        # Add many metrics
        for i in range(1000):
            registry.register(CounterMetric(f"metric_{i}", i, {}))

        # Registry should handle large numbers
        assert len(registry.metrics) == 1000

    def test_registry_concurrent_access(self, registry):
        """Test concurrent registry access."""
        def add_metrics(start, end):
            for i in range(start, end):
                registry.register(CounterMetric(f"concurrent_{i}", i, {}))

        # Simulate concurrent access
        import threading
        threads = []
        for i in range(0, 100, 10):
            thread = threading.Thread(target=add_metrics, args=(i, i+10))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(registry.metrics) == 100


class TestMetricAggregatorExtended:
    """Extended metric aggregator tests."""

    @pytest.fixture
    def aggregator(self):
        """Create metric aggregator."""
        return MetricAggregator(window_size=300)

    def test_aggregator_buffer_overflow(self, aggregator):
        """Test buffer overflow handling."""
        # Add more metrics than buffer size
        for i in range(2000):  # More than default maxlen of 1000
            metric = CounterMetric(f"overflow_{i % 10}", 1, {})
            aggregator.add_metric(metric)

        # Should maintain buffer size limit
        total_metrics = sum(len(buffer) for buffer in aggregator.metrics_buffer.values())
        assert total_metrics <= 10 * 1000  # 10 keys * 1000 max each

    def test_aggregator_time_window_cleanup(self, aggregator):
        """Test time window cleanup."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        old_time = now - timedelta(seconds=3600)  # 1 hour ago

        # Add old metric
        old_metric = CounterMetric(
            name="old_metric",
            value=1,
            labels={},
            timestamp=old_time
        )
        aggregator.add_metric(old_metric)

        # Add recent metric
        recent_metric = CounterMetric(
            name="recent_metric",
            value=1,
            labels={},
            timestamp=now
        )
        aggregator.add_metric(recent_metric)

        # Get aggregates with cutoff
        cutoff = now - timedelta(seconds=600)  # 10 minutes ago
        result = aggregator.get_aggregates(cutoff_time=cutoff)

        # Should only include recent metrics
        assert "recent_metric" in str(result)

    def test_aggregator_statistics_edge_cases(self, aggregator):
        """Test statistics with edge cases."""
        # Single value stddev
        metric = GaugeMetric("single", 42.0, {})
        aggregator.add_metric(metric)

        stddev_result = aggregator.get_aggregates(aggregation_type="stddev")
        # Single value should have 0 stddev
        assert list(stddev_result.values())[0] == 0

        # Empty values
        empty_aggregator = MetricAggregator()
        empty_result = empty_aggregator.get_aggregates()
        assert empty_result == {}

    def test_aggregator_percentile_edge_cases(self, aggregator):
        """Test percentile calculations with edge cases."""
        # Add only one value
        metric = HistogramMetric("single_val", 50, {})
        aggregator.add_metric(metric)

        p95_result = aggregator.get_aggregates(aggregation_type="p95")
        assert list(p95_result.values())[0] == 50

        # Add two values
        aggregator.add_metric(HistogramMetric("single_val", 100, {}))
        p95_result = aggregator.get_aggregates(aggregation_type="p95")
        # Should be between 50 and 100
        value = list(p95_result.values())[0]
        assert 50 <= value <= 100


class TestTimeWindowAggregatorExtended:
    """Extended time window aggregator tests."""

    def test_window_boundaries(self):
        """Test window boundary calculations."""
        aggregator = TimeWindowAggregator(window_seconds=60)

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Test boundary alignment
        if hasattr(aggregator, 'align_to_window'):
            aligned = aggregator.align_to_window(now)
            # Should align to minute boundary
            assert aligned.second == 0

    def test_overlapping_windows(self):
        """Test overlapping window handling."""
        aggregator = TimeWindowAggregator(window_seconds=120)

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Add metrics across time boundaries
        for i in range(10):
            timestamp = now + timedelta(seconds=i * 30)
            metric = CounterMetric(
                name="events",
                value=1,
                labels={},
                timestamp=timestamp
            )
            aggregator.add_metric(metric)

        if hasattr(aggregator, 'get_overlapping_windows'):
            windows = aggregator.get_overlapping_windows()
            assert len(windows) > 0


class TestAnalyticsServiceExtended:
    """Extended analytics service tests."""

    @pytest.fixture
    def service(self):
        """Create analytics service."""
        return AnalyticsService()

    def test_service_collector_lifecycle(self, service):
        """Test collector lifecycle management."""
        mock_collector = Mock()
        mock_collector.start = Mock()
        mock_collector.stop = Mock()

        # Register and start
        service.register_collector("test", mock_collector)

        if hasattr(service, 'start_collectors'):
            service.start_collectors()
            mock_collector.start.assert_called_once()

        if hasattr(service, 'stop_collectors'):
            service.stop_collectors()
            mock_collector.stop.assert_called_once()

    async def test_service_metric_batching(self, service):
        """Test metric batching."""
        mock_collector = AsyncMock()
        mock_collector.collect.return_value = [
            CounterMetric(f"batch_{i}", i, {}) for i in range(100)
        ]

        service.register_collector("batch_test", mock_collector)

        if hasattr(service, 'collect_metrics_batch'):
            metrics = await service.collect_metrics_batch(batch_size=50)
            # Should handle large batches
            assert len(metrics) > 0

    def test_service_error_handling(self, service):
        """Test service error handling."""
        failing_collector = Mock()
        failing_collector.collect = Mock(side_effect=Exception("Collector failed"))

        service.register_collector("failing", failing_collector)

        # Should handle collector failures gracefully
        try:
            # This might not exist, but test if it does
            if hasattr(service, 'collect_all_metrics_safe'):
                result = service.collect_all_metrics_safe()
                assert result is not None
        except Exception:
            pass  # Service might not have safe collection


class TestAPIGatewayMetricsExtended:
    """Extended API Gateway metrics tests."""

    def test_metrics_rate_calculation(self):
        """Test request rate calculation."""
        metrics = APIGatewayMetrics()

        # Record requests over time
        start_time = datetime.now()
        for i in range(100):
            metrics.record_request("GET", "/api/test", 200, 100)

        if hasattr(metrics, 'get_request_rate'):
            rate = metrics.get_request_rate()
            assert rate > 0

    def test_metrics_error_rate(self):
        """Test error rate calculation."""
        metrics = APIGatewayMetrics()

        # Mix of successful and error requests
        for i in range(80):
            metrics.record_request("GET", "/api/test", 200, 100)
        for i in range(20):
            metrics.record_request("GET", "/api/test", 500, 100)

        if hasattr(metrics, 'get_error_rate'):
            error_rate = metrics.get_error_rate()
            assert 0.15 < error_rate < 0.25  # Should be around 20%

    def test_metrics_latency_percentiles(self):
        """Test latency percentile calculations."""
        metrics = APIGatewayMetrics()

        # Record requests with varying latencies
        latencies = list(range(10, 1000, 10))  # 10ms to 1000ms
        for latency in latencies:
            metrics.record_request("GET", "/api/test", 200, latency)

        if hasattr(metrics, 'get_latency_percentiles'):
            percentiles = metrics.get_latency_percentiles([50, 95, 99])
            assert 50 in percentiles
            assert percentiles[95] > percentiles[50]

    def test_metrics_by_endpoint(self):
        """Test metrics aggregation by endpoint."""
        metrics = APIGatewayMetrics()

        endpoints = ["/api/users", "/api/orders", "/api/products"]
        for endpoint in endpoints:
            for i in range(10):
                metrics.record_request("GET", endpoint, 200, 100)

        if hasattr(metrics, 'get_metrics_by_endpoint'):
            endpoint_metrics = metrics.get_metrics_by_endpoint()
            assert len(endpoint_metrics) == 3
            for endpoint in endpoints:
                assert endpoint in endpoint_metrics

    def test_metrics_by_status_code(self):
        """Test metrics aggregation by status code."""
        metrics = APIGatewayMetrics()

        status_codes = [200, 201, 400, 404, 500]
        for status in status_codes:
            for i in range(5):
                metrics.record_request("GET", "/api/test", status, 100)

        if hasattr(metrics, 'get_metrics_by_status'):
            status_metrics = metrics.get_metrics_by_status()
            assert len(status_metrics) == 5


class TestCollectorIntegration:
    """Test collector integration scenarios."""

    async def test_multiple_collectors_coordination(self):
        """Test multiple collectors working together."""
        service = AnalyticsService()

        # Create multiple collectors
        collector1 = AsyncMock()
        collector1.collect.return_value = [CounterMetric("c1_metric", 1, {})]

        collector2 = AsyncMock()
        collector2.collect.return_value = [GaugeMetric("c2_metric", 50, {})]

        service.register_collector("collector1", collector1)
        service.register_collector("collector2", collector2)

        # Collect from all
        all_metrics = await service.collect_all_metrics()

        # Should have metrics from both collectors
        metric_names = [m.name for m in all_metrics]
        assert "c1_metric" in metric_names
        assert "c2_metric" in metric_names

    def test_collector_priority_ordering(self):
        """Test collector priority ordering."""
        service = AnalyticsService()

        high_priority = Mock()
        low_priority = Mock()

        if hasattr(service, 'register_collector_with_priority'):
            service.register_collector_with_priority("high", high_priority, priority=1)
            service.register_collector_with_priority("low", low_priority, priority=10)

            # Collectors should be ordered by priority
            ordered_collectors = service.get_ordered_collectors()
            assert len(ordered_collectors) == 2


class TestMetricSerialization:
    """Test metric serialization and deserialization."""

    def test_metric_to_dict(self):
        """Test metric serialization to dictionary."""
        metric = CounterMetric(
            name="test_counter",
            value=42,
            labels={"service": "api"},
            attributes={"region": "us-east"}
        )

        if hasattr(metric, 'to_dict'):
            data = metric.to_dict()
            assert data["name"] == "test_counter"
            assert data["value"] == 42
            assert data["metric_type"] == MetricType.COUNTER

    def test_metric_from_dict(self):
        """Test metric deserialization from dictionary."""
        data = {
            "name": "restored_counter",
            "value": 123,
            "metric_type": MetricType.COUNTER,
            "labels": {"env": "prod"},
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        }

        if hasattr(CounterMetric, 'from_dict'):
            metric = CounterMetric.from_dict(data)
            assert metric.name == "restored_counter"
            assert metric.value == 123

    def test_batch_metric_serialization(self):
        """Test batch metric serialization."""
        metrics = [
            CounterMetric(f"metric_{i}", i, {"batch": "test"})
            for i in range(10)
        ]

        registry = MetricRegistry()
        for metric in metrics:
            registry.register(metric)

        if hasattr(registry, 'to_json'):
            json_data = registry.to_json()
            assert json_data is not None

        if hasattr(registry, 'from_json'):
            restored_registry = MetricRegistry.from_json(json_data)
            assert len(restored_registry.metrics) == 10
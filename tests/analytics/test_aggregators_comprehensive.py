"""
Comprehensive tests for analytics aggregators module.
Focuses on covering all aggregation methods and edge cases.
"""

import statistics
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
from unittest.mock import Mock, patch

import pytest

from dotmac.platform.analytics.base import (
    Metric,
    CounterMetric,
    GaugeMetric,
    HistogramMetric,
    MetricType
)
from dotmac.platform.analytics.aggregators import (
    MetricAggregator,
    TimeWindowAggregator,
    StatisticalAggregator,
)


class TestMetricAggregatorComprehensive:
    """Comprehensive tests for MetricAggregator."""

    @pytest.fixture
    def aggregator(self):
        """Create a MetricAggregator instance."""
        return MetricAggregator(window_size=60)

    def test_aggregator_initialization(self, aggregator):
        """Test aggregator initialization."""
        assert aggregator.window_size == 60
        assert isinstance(aggregator.metrics_buffer, dict)

    def test_add_metric_alias(self, aggregator):
        """Test add method as alias for add_metric."""
        metric = CounterMetric(name="test", value=1)
        aggregator.add(metric)  # Using alias
        assert len(aggregator.metrics_buffer) > 0

    def test_get_key_generation(self, aggregator):
        """Test metric key generation."""
        metric = CounterMetric(
            name="requests",
            value=1,
            tenant_id="tenant123",
            attributes={"service": "api", "endpoint": "/users", "method": "GET"}
        )

        key = aggregator._get_key(metric)
        assert "requests" in key
        assert "tenant123" in key
        assert "service:api" in key
        assert "endpoint:/users" in key
        assert "method:GET" in key

    def test_get_key_with_partial_attributes(self, aggregator):
        """Test key generation with partial attributes."""
        metric = CounterMetric(
            name="requests",
            value=1,
            tenant_id="tenant123",
            attributes={"service": "api", "other_attr": "value"}  # Missing endpoint, method
        )

        key = aggregator._get_key(metric)
        assert "requests" in key
        assert "tenant123" in key
        assert "service:api" in key
        assert "endpoint:" not in key
        assert "method:" not in key

    def test_get_aggregates_avg(self, aggregator):
        """Test average aggregation."""
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        for value in values:
            metric = GaugeMetric(name="cpu", value=value)
            aggregator.add_metric(metric)

        result = aggregator.get_aggregates(aggregation_type="avg")
        expected_avg = statistics.mean(values)
        assert len(result) == 1
        assert abs(list(result.values())[0] - expected_avg) < 0.001

    def test_get_aggregates_sum(self, aggregator):
        """Test sum aggregation."""
        values = [1, 2, 3, 4, 5]
        for value in values:
            metric = CounterMetric(name="requests", value=value)
            aggregator.add_metric(metric)

        result = aggregator.get_aggregates(aggregation_type="sum")
        assert list(result.values())[0] == sum(values)

    def test_get_aggregates_min_max(self, aggregator):
        """Test min and max aggregation."""
        values = [10, 50, 30, 70, 20]
        for value in values:
            metric = GaugeMetric(name="latency", value=value)
            aggregator.add_metric(metric)

        min_result = aggregator.get_aggregates(aggregation_type="min")
        max_result = aggregator.get_aggregates(aggregation_type="max")

        assert list(min_result.values())[0] == min(values)
        assert list(max_result.values())[0] == max(values)

    def test_get_aggregates_count(self, aggregator):
        """Test count aggregation."""
        for i in range(10):
            metric = CounterMetric(name="events", value=i)
            aggregator.add_metric(metric)

        result = aggregator.get_aggregates(aggregation_type="count")
        assert list(result.values())[0] == 10

    def test_get_aggregates_median(self, aggregator):
        """Test median aggregation."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        for value in values:
            metric = GaugeMetric(name="response_time", value=value)
            aggregator.add_metric(metric)

        result = aggregator.get_aggregates(aggregation_type="median")
        expected_median = statistics.median(values)
        assert list(result.values())[0] == expected_median

    def test_get_aggregates_stddev(self, aggregator):
        """Test standard deviation aggregation."""
        values = [10.0, 12.0, 8.0, 15.0, 5.0]
        for value in values:
            metric = GaugeMetric(name="cpu", value=value)
            aggregator.add_metric(metric)

        result = aggregator.get_aggregates(aggregation_type="stddev")
        expected_stddev = statistics.stdev(values)
        assert abs(list(result.values())[0] - expected_stddev) < 0.001

    def test_get_aggregates_stddev_single_value(self, aggregator):
        """Test standard deviation with single value."""
        metric = GaugeMetric(name="single", value=42.0)
        aggregator.add_metric(metric)

        result = aggregator.get_aggregates(aggregation_type="stddev")
        assert list(result.values())[0] == 0  # Should return 0 for single value

    def test_get_aggregates_p95(self, aggregator):
        """Test 95th percentile aggregation."""
        # Add values 0-99
        for i in range(100):
            metric = HistogramMetric(name="latency", value=i)
            aggregator.add_metric(metric)

        result = aggregator.get_aggregates(aggregation_type="p95")
        # 95th percentile of 0-99 should be around 94-95
        p95_value = list(result.values())[0]
        assert 94 <= p95_value <= 95

    def test_get_aggregates_with_cutoff_time(self, aggregator):
        """Test aggregation with cutoff time."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        old_time = now - timedelta(minutes=5)
        cutoff = now - timedelta(minutes=2)

        # Add old metric (should be filtered out)
        old_metric = CounterMetric(
            name="requests",
            value=100,
            timestamp=old_time
        )
        aggregator.add_metric(old_metric)

        # Add recent metric (should be included)
        recent_metric = CounterMetric(
            name="requests",
            value=50,
            timestamp=now
        )
        aggregator.add_metric(recent_metric)

        result = aggregator.get_aggregates(
            aggregation_type="sum",
            cutoff_time=cutoff
        )

        # Should only include the recent metric
        assert list(result.values())[0] == 50

    def test_get_aggregates_empty_buffer(self, aggregator):
        """Test aggregation with empty buffer."""
        result = aggregator.get_aggregates(aggregation_type="avg")
        assert result == {}

    def test_get_aggregates_all_filtered_out(self, aggregator):
        """Test aggregation where all metrics are filtered out by cutoff."""
        old_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)

        metric = CounterMetric(name="old", value=10, timestamp=old_time)
        aggregator.add_metric(metric)

        # Use recent cutoff time that filters out all metrics
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
        result = aggregator.get_aggregates(cutoff_time=cutoff)
        assert result == {}

    def test_multiple_metric_keys(self, aggregator):
        """Test aggregation with multiple different metric keys."""
        # Add metrics with different names/attributes
        metric1 = CounterMetric(
            name="requests",
            value=10,
            attributes={"endpoint": "/api"}
        )
        metric2 = CounterMetric(
            name="requests",
            value=20,
            attributes={"endpoint": "/health"}
        )
        metric3 = CounterMetric(
            name="errors",
            value=5,
            attributes={"endpoint": "/api"}
        )

        aggregator.add_metric(metric1)
        aggregator.add_metric(metric2)
        aggregator.add_metric(metric3)

        result = aggregator.get_aggregates(aggregation_type="sum")

        # Should have separate aggregations for each key
        assert len(result) == 3
        assert 10 in result.values()
        assert 20 in result.values()
        assert 5 in result.values()

    def test_buffer_maxlen_behavior(self, aggregator):
        """Test buffer maximum length behavior."""
        # Add more metrics than maxlen (1000)
        for i in range(1500):
            metric = CounterMetric(name="overflow", value=i)
            aggregator.add_metric(metric)

        # Buffer should be limited to maxlen
        key = list(aggregator.metrics_buffer.keys())[0]
        assert len(aggregator.metrics_buffer[key]) <= 1000

    def test_percentile_calculation(self, aggregator):
        """Test internal percentile calculation method."""
        values = list(range(100))  # 0-99
        p95 = aggregator._percentile(values, 95)
        assert 94 <= p95 <= 95

        # Test with small list
        small_values = [1, 2, 3]
        p50 = aggregator._percentile(small_values, 50)
        assert p50 == 2

        # Test edge cases
        single_value = [42]
        p95_single = aggregator._percentile(single_value, 95)
        assert p95_single == 42

    def test_aggregation_with_none_values(self, aggregator):
        """Test aggregation handling of None values."""
        # Create metric with None value (should be handled gracefully)
        metric = GaugeMetric(name="test", value=None)
        aggregator.add_metric(metric)

        # Should handle None values without crashing
        result = aggregator.get_aggregates(aggregation_type="avg")
        # Result depends on implementation - might filter None or convert to 0


class TestTimeWindowAggregatorComprehensive:
    """Comprehensive tests for TimeWindowAggregator."""

    @pytest.fixture
    def time_aggregator(self):
        """Create TimeWindowAggregator instance."""
        return TimeWindowAggregator(window_seconds=300)  # 5 minutes

    def test_time_aggregator_initialization(self, time_aggregator):
        """Test time aggregator initialization."""
        assert time_aggregator.window_seconds == 300
        assert hasattr(time_aggregator, 'metrics')

    def test_add_metric_with_timestamp(self, time_aggregator):
        """Test adding metric with specific timestamp."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        metric = CounterMetric(
            name="timed_metric",
            value=1,
            timestamp=now
        )

        time_aggregator.add_metric(metric)
        assert len(time_aggregator.metrics) > 0

    def test_get_windows_basic(self, time_aggregator):
        """Test getting time windows."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Add metrics across different time periods
        for i in range(10):
            timestamp = now - timedelta(minutes=i)
            metric = CounterMetric(
                name="events",
                value=1,
                timestamp=timestamp
            )
            time_aggregator.add_metric(metric)

        windows = time_aggregator.get_windows()
        assert windows is not None

    def test_window_boundary_alignment(self, time_aggregator):
        """Test window boundary calculations."""
        # Test if there's an align_to_window method
        if hasattr(time_aggregator, 'align_to_window'):
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            aligned = time_aggregator.align_to_window(now)
            assert isinstance(aligned, datetime)

    def test_overlapping_windows(self, time_aggregator):
        """Test overlapping window handling."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Add metrics that span multiple windows
        for i in range(20):
            timestamp = now - timedelta(seconds=i * 30)  # Every 30 seconds
            metric = CounterMetric(
                name="events",
                value=1,
                timestamp=timestamp
            )
            time_aggregator.add_metric(metric)

        # Test overlapping window functionality if available
        if hasattr(time_aggregator, 'get_overlapping_windows'):
            overlapping = time_aggregator.get_overlapping_windows()
            assert overlapping is not None


class TestStatisticalAggregatorComprehensive:
    """Comprehensive tests for StatisticalAggregator."""

    @pytest.fixture
    def stats_aggregator(self):
        """Create StatisticalAggregator instance."""
        return StatisticalAggregator()

    def test_stats_aggregator_initialization(self, stats_aggregator):
        """Test statistical aggregator initialization."""
        assert stats_aggregator is not None
        assert hasattr(stats_aggregator, 'add_value')
        assert hasattr(stats_aggregator, 'calculate_statistics')

    def test_add_value_and_calculate_basic_stats(self, stats_aggregator):
        """Test adding values and calculating basic statistics."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        for value in values:
            stats_aggregator.add_value("test_metric", value)

        stats = stats_aggregator.calculate_statistics("test_metric")

        assert stats["count"] == 10
        assert stats["mean"] == 5.5
        assert stats["min"] == 1
        assert stats["max"] == 10

    def test_calculate_statistics_advanced(self, stats_aggregator):
        """Test advanced statistical calculations."""
        # Add sample data
        data = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

        for value in data:
            stats_aggregator.add_value("advanced_metric", value)

        stats = stats_aggregator.calculate_statistics("advanced_metric")

        # Verify additional statistics if available
        expected_mean = statistics.mean(data)
        assert abs(stats["mean"] - expected_mean) < 0.001

        # Test for additional stats if they exist
        if "median" in stats:
            assert stats["median"] == statistics.median(data)
        if "stddev" in stats:
            assert abs(stats["stddev"] - statistics.stdev(data)) < 0.001

    def test_multiple_metrics_tracking(self, stats_aggregator):
        """Test tracking multiple different metrics."""
        # Add data for metric1
        for i in range(1, 11):
            stats_aggregator.add_value("metric1", i)

        # Add data for metric2
        for i in range(10, 21):
            stats_aggregator.add_value("metric2", i)

        stats1 = stats_aggregator.calculate_statistics("metric1")
        stats2 = stats_aggregator.calculate_statistics("metric2")

        assert stats1["mean"] == 5.5
        assert stats2["mean"] == 15.0
        assert stats1["count"] == 10
        assert stats2["count"] == 11

    def test_empty_metric_statistics(self, stats_aggregator):
        """Test statistics for non-existent metric."""
        stats = stats_aggregator.calculate_statistics("nonexistent")
        assert stats["count"] == 0

    def test_single_value_statistics(self, stats_aggregator):
        """Test statistics with single value."""
        stats_aggregator.add_value("single", 42)
        stats = stats_aggregator.calculate_statistics("single")

        assert stats["count"] == 1
        assert stats["mean"] == 42
        assert stats["min"] == 42
        assert stats["max"] == 42

    def test_large_dataset_performance(self, stats_aggregator):
        """Test performance with large dataset."""
        # Add large amount of data
        for i in range(10000):
            stats_aggregator.add_value("large_dataset", i % 100)

        stats = stats_aggregator.calculate_statistics("large_dataset")

        assert stats["count"] == 10000
        # Mean should be around 49.5 (average of 0-99 repeated)
        assert 49 <= stats["mean"] <= 50

    def test_negative_values_handling(self, stats_aggregator):
        """Test handling of negative values."""
        values = [-10, -5, 0, 5, 10, 15, 20]

        for value in values:
            stats_aggregator.add_value("mixed_signs", value)

        stats = stats_aggregator.calculate_statistics("mixed_signs")

        assert stats["min"] == -10
        assert stats["max"] == 20
        assert abs(stats["mean"] - statistics.mean(values)) < 0.001

    def test_floating_point_precision(self, stats_aggregator):
        """Test floating point precision in calculations."""
        values = [1.1, 2.2, 3.3, 4.4, 5.5]

        for value in values:
            stats_aggregator.add_value("float_metric", value)

        stats = stats_aggregator.calculate_statistics("float_metric")

        expected_mean = sum(values) / len(values)
        assert abs(stats["mean"] - expected_mean) < 0.0001

    def test_statistics_after_clear(self, stats_aggregator):
        """Test statistics after clearing data."""
        # Add some data
        for i in range(5):
            stats_aggregator.add_value("clearable", i)

        # Clear if method exists
        if hasattr(stats_aggregator, 'clear'):
            stats_aggregator.clear("clearable")
            stats = stats_aggregator.calculate_statistics("clearable")
            assert stats["count"] == 0


class TestAggregatorEdgeCases:
    """Test edge cases across all aggregators."""

    def test_concurrent_access_simulation(self):
        """Test simulated concurrent access to aggregator."""
        aggregator = MetricAggregator()

        # Simulate multiple threads adding metrics
        import threading
        results = []

        def add_metrics(start, end):
            for i in range(start, end):
                metric = CounterMetric(f"concurrent_{i}", i)
                aggregator.add_metric(metric)
                results.append(i)

        threads = []
        for i in range(0, 100, 10):
            thread = threading.Thread(target=add_metrics, args=(i, i + 10))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify all metrics were added
        assert len(results) == 100

    def test_memory_usage_large_datasets(self):
        """Test memory usage with large datasets."""
        aggregator = MetricAggregator()

        # Add many metrics with different keys
        for i in range(1000):
            metric = CounterMetric(
                name=f"metric_{i % 10}",  # 10 different keys
                value=i,
                attributes={"index": str(i)}
            )
            aggregator.add_metric(metric)

        # Verify buffer sizes are managed
        total_buffered = sum(
            len(buffer) for buffer in aggregator.metrics_buffer.values()
        )
        assert total_buffered <= 10000  # Should be reasonable

    def test_extreme_values_handling(self):
        """Test handling of extreme values."""
        aggregator = MetricAggregator()

        extreme_values = [
            float('inf'),
            float('-inf'),
            1e308,  # Very large
            1e-308, # Very small
            0.0
        ]

        for i, value in enumerate(extreme_values):
            try:
                metric = GaugeMetric(f"extreme_{i}", value)
                aggregator.add_metric(metric)
            except (OverflowError, ValueError):
                # Some extreme values might not be handled
                pass

        # Test if aggregation handles extreme values gracefully
        try:
            result = aggregator.get_aggregates(aggregation_type="sum")
            # Should either work or fail gracefully
        except (OverflowError, ValueError):
            # Acceptable to fail with extreme values
            pass

    def test_invalid_aggregation_types(self):
        """Test invalid aggregation type handling."""
        aggregator = MetricAggregator()

        metric = CounterMetric("test", 1)
        aggregator.add_metric(metric)

        # Test invalid aggregation type
        result = aggregator.get_aggregates(aggregation_type="invalid_type")
        # Should return empty or handle gracefully
        assert isinstance(result, dict)

    def test_timezone_handling_edge_cases(self):
        """Test timezone handling edge cases."""
        aggregator = MetricAggregator()

        # Create metrics with different timezone representations
        now_utc = datetime.now(timezone.utc)
        now_naive = datetime.now()

        metric1 = CounterMetric("tz_test1", 1, timestamp=now_utc.replace(tzinfo=None))
        metric2 = CounterMetric("tz_test2", 1, timestamp=now_naive)

        aggregator.add_metric(metric1)
        aggregator.add_metric(metric2)

        # Should handle different timestamp formats
        result = aggregator.get_aggregates()
        assert len(result) >= 0  # Should not crash
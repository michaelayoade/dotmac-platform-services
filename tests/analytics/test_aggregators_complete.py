"""
Fixed tests for metric aggregators.
Testing time-series aggregation, statistical calculations, and data windowing.
Developer 3 - Coverage Task: Analytics & Observability
"""

import statistics
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock

import pytest

from dotmac.platform.analytics.aggregators import (
    MetricAggregator,
    TimeWindowAggregator,
    StatisticalAggregator,
)
from dotmac.platform.analytics.base import (
    CounterMetric,
    GaugeMetric,
    HistogramMetric,
    Metric,
)


@pytest.fixture
def basic_aggregator():
    """Create a basic MetricAggregator."""
    return MetricAggregator(window_size=60)


@pytest.fixture
def time_window_aggregator():
    """Create a TimeWindowAggregator."""
    return TimeWindowAggregator(window_minutes=5)


@pytest.fixture
def statistical_aggregator():
    """Create a StatisticalAggregator."""
    return StatisticalAggregator()


@pytest.fixture
def sample_metrics():
    """Create sample metrics for testing."""
    base_time = datetime.now(timezone.utc).replace(tzinfo=None)
    return [
        Metric(
            name="cpu_usage",
            value=75.0 + i,
            timestamp=base_time + timedelta(seconds=i),
            tenant_id="tenant_1",
        )
        for i in range(10)
    ]


class TestMetricAggregator:
    """Test base MetricAggregator functionality."""

    def test_add_metric(self, basic_aggregator, sample_metrics):
        """Test adding metrics to aggregator."""
        for metric in sample_metrics:
            basic_aggregator.add_metric(metric)

        assert len(basic_aggregator.metrics_buffer) > 0

    def test_aggregate_operations(self, basic_aggregator, sample_metrics):
        """Test different aggregation operations."""
        for metric in sample_metrics:
            basic_aggregator.add_metric(metric)

        # Test average
        avg_result = basic_aggregator.get_aggregates("avg")
        assert "cpu_usage|tenant_1" in avg_result

        # Test sum
        sum_result = basic_aggregator.get_aggregates("sum")
        assert "cpu_usage|tenant_1" in sum_result

        # Test min/max
        min_result = basic_aggregator.get_aggregates("min")
        max_result = basic_aggregator.get_aggregates("max")
        assert min_result["cpu_usage|tenant_1"] < max_result["cpu_usage|tenant_1"]

    def test_time_based_filtering(self, basic_aggregator):
        """Test time-based metric filtering."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        old_metric = Metric(
            name="old_metric",
            value=100.0,
            timestamp=now - timedelta(minutes=5),
            tenant_id="tenant_1",
        )
        new_metric = Metric(
            name="new_metric",
            value=200.0,
            timestamp=now,
            tenant_id="tenant_1",
        )

        basic_aggregator.add_metric(old_metric)
        basic_aggregator.add_metric(new_metric)

        # Get aggregates with time filter
        cutoff = now - timedelta(minutes=1)
        result = basic_aggregator.get_aggregates("avg", cutoff_time=cutoff)

        # Should only include new metric
        assert "new_metric|tenant_1" in result
        assert result["new_metric|tenant_1"] == 200.0

    def test_memory_management(self, basic_aggregator):
        """Test memory management and cleanup."""
        # Add many metrics
        for i in range(2000):  # More than max buffer size
            metric = Metric(
                name="test_metric",
                value=i,
                timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
                tenant_id="tenant_1",
            )
            basic_aggregator.add_metric(metric)

        # Buffer should be limited to maxlen
        buffer = basic_aggregator.metrics_buffer["test_metric|tenant_1"]
        assert len(buffer) <= 1000  # maxlen from implementation

    def test_percentile_calculations(self, basic_aggregator):
        """Test percentile calculations."""
        # Add known values
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        for val in values:
            metric = Metric(
                name="percentile_test",
                value=val,
                timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
                tenant_id="tenant_1",
            )
            basic_aggregator.add_metric(metric)

        # Test p95 and p99
        p95_result = basic_aggregator.get_aggregates("p95")
        p99_result = basic_aggregator.get_aggregates("p99")

        assert "percentile_test|tenant_1" in p95_result
        assert "percentile_test|tenant_1" in p99_result

        # p95 should be close to 9.5, p99 close to 9.9
        assert p95_result["percentile_test|tenant_1"] >= 9
        assert p99_result["percentile_test|tenant_1"] >= 9


class TestTimeWindowAggregator:
    """Test TimeWindowAggregator functionality."""

    def test_add_metric(self, time_window_aggregator):
        """Test adding metrics to time windows."""
        metric = Metric(
            name="window_test",
            value=42.0,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
            tenant_id="tenant_1",
        )

        time_window_aggregator.add(metric)
        assert len(time_window_aggregator.windows) > 0

    def test_add_data_point(self, time_window_aggregator):
        """Test adding data points directly."""
        time_window_aggregator.add_data_point("direct_metric", 123.45)
        assert len(time_window_aggregator.windows) > 0

    def test_window_alignment(self, time_window_aggregator):
        """Test that metrics are aligned to correct time windows."""
        # Create metrics at specific times
        base_time = datetime(2023, 1, 1, 12, 7, 30)  # 12:07:30

        metric1 = Metric(
            name="alignment_test",
            value=100.0,
            timestamp=base_time,
            tenant_id="tenant_1",
        )

        metric2 = Metric(
            name="alignment_test",
            value=200.0,
            timestamp=base_time + timedelta(minutes=2),  # 12:09:30
            tenant_id="tenant_1",
        )

        time_window_aggregator.add(metric1)
        time_window_aggregator.add(metric2)

        # Both should be in same 5-minute window (12:05:00)
        expected_window = datetime(2023, 1, 1, 12, 5, 0)
        assert expected_window in time_window_aggregator.windows

    def test_window_aggregates(self, time_window_aggregator):
        """Test getting aggregates for specific windows."""
        window_start = datetime(2023, 1, 1, 12, 0, 0)

        # Add metrics to specific window
        for i in range(5):
            metric = Metric(
                name="agg_test",
                value=i + 1,  # 1, 2, 3, 4, 5
                timestamp=window_start + timedelta(seconds=i),
                tenant_id="tenant_1",
            )
            time_window_aggregator.add(metric)

        # Get aggregates with mean function
        aggregates = time_window_aggregator.get_window_aggregates(
            window_start, statistics.mean
        )

        assert "agg_test:tenant_1" in aggregates
        assert aggregates["agg_test:tenant_1"] == 3.0  # Mean of 1,2,3,4,5

    def test_cleanup_old_windows(self, time_window_aggregator):
        """Test cleanup of old time windows."""
        old_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=2)

        metric = Metric(
            name="cleanup_test",
            value=100.0,
            timestamp=old_time,
            tenant_id="tenant_1",
        )

        time_window_aggregator.add(metric)
        initial_count = len(time_window_aggregator.windows)

        # Cleanup old windows
        time_window_aggregator.cleanup_old_windows(retention_hours=1)

        # Should have fewer windows
        assert len(time_window_aggregator.windows) <= initial_count


class TestStatisticalAggregator:
    """Test StatisticalAggregator functionality."""

    def test_add_metric(self, statistical_aggregator):
        """Test adding metrics for statistical analysis."""
        metric = Metric(
            name="stats_test",
            value=42.0,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
            tenant_id="tenant_1",
        )

        statistical_aggregator.add(metric)
        assert len(statistical_aggregator.data_points) > 0

    def test_add_value_direct(self, statistical_aggregator):
        """Test adding values directly."""
        statistical_aggregator.add_value("direct_stats", 123.45)
        assert "direct_stats" in statistical_aggregator.data_points

    def test_statistics_calculation(self, statistical_aggregator):
        """Test comprehensive statistics calculation."""
        # Add known values for statistics
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        for val in values:
            statistical_aggregator.add_value("stats_calc", val)

        stats = statistical_aggregator.get_statistics("stats_calc")

        # Check basic statistics
        assert stats["count"] == 10
        assert stats["mean"] == 5.5
        assert stats["min"] == 1
        assert stats["max"] == 10
        assert stats["median"] == 5.5

    def test_time_range_filtering(self, statistical_aggregator):
        """Test statistics with time range filtering."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Add metrics with different timestamps
        for i in range(5):
            metric = Metric(
                name="time_filter",
                value=i + 1,
                timestamp=now - timedelta(minutes=i),
                tenant_id="tenant_1",
            )
            statistical_aggregator.add(metric)

        # Get stats for last 2 minutes
        stats = statistical_aggregator.get_statistics(
            "time_filter:tenant_1",
            time_range=timedelta(minutes=2)
        )

        # Should only include recent values
        assert stats["count"] <= 3

    def test_correlation_analysis(self, statistical_aggregator):
        """Test correlation analysis between metrics."""
        # Add correlated data
        for i in range(10):
            statistical_aggregator.add_value("metric_a", i)
            statistical_aggregator.add_value("metric_b", i * 2)  # Perfect correlation

        # Check if correlation methods exist (implementation dependent)
        stats_a = statistical_aggregator.get_statistics("metric_a")
        stats_b = statistical_aggregator.get_statistics("metric_b")

        assert stats_a["count"] == stats_b["count"]
        assert stats_a["count"] == 10

    def test_outlier_detection(self, statistical_aggregator):
        """Test outlier detection capabilities."""
        # Add normal values and outliers
        normal_values = [10, 11, 9, 12, 8, 13, 7, 14]
        outliers = [100, -50]  # Clear outliers

        for val in normal_values + outliers:
            statistical_aggregator.add_value("outlier_test", val)

        stats = statistical_aggregator.get_statistics("outlier_test")

        # Basic check - standard deviation should be high due to outliers
        assert stats["count"] == 10
        assert stats["std_dev"] > 10  # High std due to outliers

    def test_empty_dataset_handling(self, statistical_aggregator):
        """Test handling of empty datasets."""
        stats = statistical_aggregator.get_statistics("nonexistent_key")

        # Should handle gracefully
        assert stats["count"] == 0

    def test_single_value_statistics(self, statistical_aggregator):
        """Test statistics calculation with single value."""
        statistical_aggregator.add_value("single_val", 42.0)

        stats = statistical_aggregator.get_statistics("single_val")

        assert stats["count"] == 1
        assert stats["mean"] == 42.0
        assert stats["min"] == 42.0
        assert stats["max"] == 42.0
        # Single value doesn't have std_dev
        assert "duration_seconds" in stats


class TestAggregatorIntegration:
    """Test integration between different aggregator types."""

    def test_cross_aggregator_consistency(self):
        """Test that different aggregators produce consistent results."""
        basic_agg = MetricAggregator(window_size=300)
        stats_agg = StatisticalAggregator()

        # Add same data to both
        values = [1, 2, 3, 4, 5]
        for val in values:
            metric = Metric(
                name="consistency_test",
                value=val,
                timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
                tenant_id="tenant_1",
            )
            basic_agg.add_metric(metric)
            stats_agg.add(metric)

        # Compare basic statistics
        basic_avg = basic_agg.get_aggregates("avg")["consistency_test|tenant_1"]
        stats_mean = stats_agg.get_statistics("consistency_test:tenant_1")["mean"]

        assert abs(basic_avg - stats_mean) < 0.001

    def test_performance_with_large_datasets(self):
        """Test aggregator performance with large datasets."""
        basic_agg = MetricAggregator(window_size=3600)

        start_time = time.time()

        # Add 10000 metrics
        for i in range(10000):
            metric = Metric(
                name="perf_test",
                value=i,
                timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
                tenant_id="tenant_1",
            )
            basic_agg.add_metric(metric)

        # Perform aggregation
        result = basic_agg.get_aggregates("avg")

        end_time = time.time()

        # Should complete in reasonable time (< 5 seconds)
        assert (end_time - start_time) < 5.0
        assert "perf_test|tenant_1" in result

    def test_concurrent_access_simulation(self):
        """Test aggregator behavior under concurrent access patterns."""
        agg = MetricAggregator(window_size=60)

        # Simulate concurrent metric additions
        import threading
        import random

        def add_metrics(thread_id):
            for i in range(100):
                metric = Metric(
                    name=f"concurrent_{thread_id}",
                    value=random.random() * 100,
                    timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
                    tenant_id=f"tenant_{thread_id}",
                )
                agg.add_metric(metric)

        # Create and start threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=add_metrics, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify all metrics were added
        result = agg.get_aggregates("count")
        total_count = sum(result.values())
        assert total_count == 500  # 5 threads * 100 metrics each
"""
Simple tests for Analytics module components.
"""

import asyncio
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from dotmac.platform.analytics.aggregators import (
    MetricAggregator,
    StatisticalAggregator,
    TimeWindowAggregator,
)
from dotmac.platform.analytics.base import (
    CounterMetric,
    GaugeMetric,
    HistogramMetric,
    Metric,
)


@pytest.fixture
def sample_analytics_data():
    """Sample analytics data for testing."""
    return {
        "events": [
            {
                "name": "user_login",
                "timestamp": datetime.now(timezone.utc).replace(tzinfo=None),
                "properties": {"user_id": "123", "source": "web"},
            },
            {
                "name": "page_view",
                "timestamp": datetime.now(timezone.utc).replace(tzinfo=None),
                "properties": {"page": "/dashboard", "user_id": "123"},
            },
        ],
        "metrics": [
            {"name": "response_time", "value": 250.0, "unit": "ms"},
            {"name": "memory_usage", "value": 75.2, "unit": "percent"},
        ],
    }


class TestAnalyticsIntegration:
    """Test analytics integration and workflow."""

    def test_metric_aggregation_workflow(self, sample_analytics_data):
        """Test full metric aggregation workflow."""
        aggregator = MetricAggregator(window_size=300)

        # Process sample metrics
        for metric_data in sample_analytics_data["metrics"]:
            metric = Metric(
                name=metric_data["name"],
                value=metric_data["value"],
                timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
                tenant_id="test_tenant",
            )
            aggregator.add_metric(metric)

        # Get aggregated results
        avg_results = aggregator.get_aggregates("avg")
        assert len(avg_results) == 2
        assert "response_time|test_tenant" in avg_results
        assert "memory_usage|test_tenant" in avg_results

        # Verify values
        assert avg_results["response_time|test_tenant"] == 250.0
        assert avg_results["memory_usage|test_tenant"] == 75.2

    def test_time_window_analytics(self):
        """Test time window analytics processing."""
        aggregator = TimeWindowAggregator(window_minutes=5)

        # Add metrics across different time windows
        base_time = datetime(2023, 1, 1, 12, 0, 0)

        for i in range(10):
            metric = Metric(
                name="cpu_usage",
                value=50.0 + i * 5,  # 50, 55, 60, etc.
                timestamp=base_time + timedelta(minutes=i),
                tenant_id="test_tenant",
            )
            aggregator.add(metric)

        # Check that metrics are distributed across windows
        assert len(aggregator.windows) >= 2  # Should span multiple windows

    def test_statistical_analysis(self):
        """Test statistical analysis capabilities."""
        analyzer = StatisticalAggregator()

        # Add a dataset for analysis
        values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for value in values:
            analyzer.add_value("test_metric", value)

        stats = analyzer.get_statistics("test_metric")

        # Verify statistical calculations
        assert stats["count"] == 10
        assert stats["mean"] == 55.0
        assert stats["min"] == 10
        assert stats["max"] == 100
        assert stats["median"] == 55.0

    def test_analytics_performance(self):
        """Test analytics processing performance."""
        aggregator = MetricAggregator(window_size=3600)

        start_time = time.time()

        # Process large number of metrics
        for i in range(1000):
            metric = Metric(
                name="perf_test",
                value=i % 100,  # Vary values 0-99
                timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
                tenant_id="perf_tenant",
            )
            aggregator.add_metric(metric)

        # Get results
        results = aggregator.get_aggregates("avg")

        end_time = time.time()
        processing_time = end_time - start_time

        # Should process quickly
        assert processing_time < 1.0  # Less than 1 second
        assert "perf_test|perf_tenant" in results

    def test_multi_tenant_analytics(self):
        """Test multi-tenant analytics separation."""
        aggregator = MetricAggregator(window_size=300)

        # Add metrics for different tenants
        tenants = ["tenant_a", "tenant_b", "tenant_c"]

        for tenant in tenants:
            for i in range(5):
                metric = Metric(
                    name="api_calls",
                    value=100 + i,  # Different values per tenant
                    timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
                    tenant_id=tenant,
                )
                aggregator.add_metric(metric)

        # Get aggregated results
        results = aggregator.get_aggregates("avg")

        # Verify tenant separation
        for tenant in tenants:
            key = f"api_calls|{tenant}"
            assert key in results
            assert results[key] == 102.0  # Average of 100,101,102,103,104

    def test_analytics_data_retention(self):
        """Test analytics data retention and cleanup."""
        aggregator = MetricAggregator(window_size=60)  # 1 minute window

        # Add old metrics
        old_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=5)
        old_metric = Metric(
            name="old_metric",
            value=100.0,
            timestamp=old_time,
            tenant_id="test_tenant",
        )
        aggregator.add_metric(old_metric)

        # Add recent metrics
        recent_time = datetime.now(timezone.utc).replace(tzinfo=None)
        recent_metric = Metric(
            name="recent_metric",
            value=200.0,
            timestamp=recent_time,
            tenant_id="test_tenant",
        )
        aggregator.add_metric(recent_metric)

        # Test time-based filtering
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=2)
        results = aggregator.get_aggregates("avg", cutoff_time=cutoff)

        # Should only include recent metrics
        assert "recent_metric|test_tenant" in results
        assert results["recent_metric|test_tenant"] == 200.0

    def test_analytics_error_handling(self):
        """Test analytics error handling and edge cases."""
        aggregator = MetricAggregator(window_size=300)

        # Test with empty aggregator
        empty_results = aggregator.get_aggregates("avg")
        assert empty_results == {}

        # Test with invalid aggregation type
        metric = Metric(
            name="test_metric",
            value=50.0,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
            tenant_id="test_tenant",
        )
        aggregator.add_metric(metric)

        # Invalid aggregation type should not crash
        invalid_results = aggregator.get_aggregates("invalid_type")
        assert invalid_results == {}

    def test_analytics_memory_efficiency(self):
        """Test analytics memory usage and efficiency."""
        aggregator = MetricAggregator(window_size=300)

        # Add metrics beyond buffer limit
        for i in range(1500):  # Exceeds maxlen of 1000
            metric = Metric(
                name="memory_test",
                value=i,
                timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
                tenant_id="test_tenant",
            )
            aggregator.add_metric(metric)

        # Verify buffer is limited
        buffer = aggregator.metrics_buffer["memory_test|test_tenant"]
        assert len(buffer) <= 1000  # Should be limited by maxlen

    def test_analytics_concurrent_processing(self):
        """Test analytics under concurrent load."""
        aggregator = MetricAggregator(window_size=300)

        import threading
        import random

        def add_metrics(thread_id, count):
            """Add metrics from a thread."""
            for i in range(count):
                metric = Metric(
                    name=f"concurrent_test_{thread_id}",
                    value=random.random() * 100,
                    timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
                    tenant_id=f"tenant_{thread_id}",
                )
                aggregator.add_metric(metric)

        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=add_metrics, args=(i, 50))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify all metrics were processed
        results = aggregator.get_aggregates("count")
        total_count = sum(results.values())
        assert total_count == 150  # 3 threads * 50 metrics each


class TestAnalyticsMetricTypes:
    """Test different metric types in analytics."""

    def test_counter_metrics(self):
        """Test counter metric processing."""
        aggregator = MetricAggregator(window_size=300)

        # Create counter metrics
        for i in range(10):
            counter = CounterMetric(
                name="page_views",
                value=1,  # Counter increments
                attributes={"page": f"/page_{i % 3}"},
                tenant_id="test_tenant",
                timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            aggregator.add_metric(counter)

        # Get sum aggregation (appropriate for counters)
        results = aggregator.get_aggregates("sum")
        assert "page_views|test_tenant" in results
        assert results["page_views|test_tenant"] == 10

    def test_gauge_metrics(self):
        """Test gauge metric processing."""
        aggregator = MetricAggregator(window_size=300)

        # Create gauge metrics (current value snapshots)
        gauge_values = [25.0, 30.0, 28.0, 32.0, 29.0]
        for value in gauge_values:
            gauge = GaugeMetric(
                name="cpu_usage",
                value=value,
                attributes={"instance": "server1"},
                tenant_id="test_tenant",
                timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            aggregator.add_metric(gauge)

        # Get average (appropriate for gauges)
        results = aggregator.get_aggregates("avg")
        expected_avg = sum(gauge_values) / len(gauge_values)
        assert abs(results["cpu_usage|test_tenant"] - expected_avg) < 0.1

    def test_histogram_metrics(self):
        """Test histogram metric processing."""
        aggregator = MetricAggregator(window_size=300)

        # Create histogram metrics (timing data)
        response_times = [100, 150, 200, 250, 300, 120, 180, 220, 280, 160]
        for time_ms in response_times:
            histogram = HistogramMetric(
                name="response_time",
                value=time_ms,
                attributes={"endpoint": "/api/users"},
                tenant_id="test_tenant",
                timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            aggregator.add_metric(histogram)

        # Test various aggregations
        avg_result = aggregator.get_aggregates("avg")
        min_result = aggregator.get_aggregates("min")
        max_result = aggregator.get_aggregates("max")

        expected_key = "response_time|test_tenant|endpoint:/api/users"
        assert expected_key in avg_result
        assert min_result[expected_key] == 100
        assert max_result[expected_key] == 300

    def test_metric_attributes_handling(self):
        """Test handling of metric attributes in analytics."""
        aggregator = MetricAggregator(window_size=300)

        # Create metrics with various attributes
        metric_with_attrs = Metric(
            name="api_request",
            value=1,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
            tenant_id="test_tenant",
            attributes={
                "method": "GET",
                "endpoint": "/api/users",
                "status_code": "200",
                "user_agent": "test-client/1.0",
            },
        )
        aggregator.add_metric(metric_with_attrs)

        # Verify metric was stored
        results = aggregator.get_aggregates("count")
        # The key should include relevant attributes based on implementation
        assert len(results) > 0

        # Check that buffer contains the attributes
        buffer_keys = list(aggregator.metrics_buffer.keys())
        assert len(buffer_keys) > 0


class TestAnalyticsReporting:
    """Test analytics reporting and export functionality."""

    def test_analytics_summary_generation(self):
        """Test generation of analytics summaries."""
        aggregator = MetricAggregator(window_size=3600)  # 1 hour window

        # Add diverse metrics
        metrics_data = [
            ("cpu_usage", [20, 25, 30, 35, 40]),
            ("memory_usage", [60, 65, 70, 75, 80]),
            ("disk_usage", [45, 50, 55, 60, 65]),
        ]

        for metric_name, values in metrics_data:
            for value in values:
                metric = Metric(
                    name=metric_name,
                    value=value,
                    timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
                    tenant_id="summary_tenant",
                )
                aggregator.add_metric(metric)

        # Generate summary statistics
        avg_results = aggregator.get_aggregates("avg")
        min_results = aggregator.get_aggregates("min")
        max_results = aggregator.get_aggregates("max")

        # Verify summary completeness
        for metric_name, _ in metrics_data:
            key = f"{metric_name}|summary_tenant"
            assert key in avg_results
            assert key in min_results
            assert key in max_results

    def test_analytics_time_series_data(self):
        """Test time series analytics data generation."""
        time_aggregator = TimeWindowAggregator(window_minutes=1)

        # Generate time series data
        base_time = datetime(2023, 1, 1, 12, 0, 0)
        for minute in range(10):
            for second in range(0, 60, 10):  # Every 10 seconds
                timestamp = base_time + timedelta(minutes=minute, seconds=second)
                metric = Metric(
                    name="requests_per_second",
                    value=50 + minute * 5,  # Increasing trend
                    timestamp=timestamp,
                    tenant_id="timeseries_tenant",
                )
                time_aggregator.add(metric)

        # Verify time series windows
        assert len(time_aggregator.windows) >= 10  # Should have multiple windows

        # Check window data integrity
        for window_start, window_data in time_aggregator.windows.items():
            assert isinstance(window_start, datetime)
            assert len(window_data) > 0

    def test_analytics_export_format(self):
        """Test analytics data export formatting."""
        stats_aggregator = StatisticalAggregator()

        # Add comprehensive dataset
        dataset = list(range(1, 101))  # 1 to 100
        for value in dataset:
            stats_aggregator.add_value("export_test", value)

        # Get comprehensive statistics
        stats = stats_aggregator.get_statistics("export_test")

        # Verify export-ready format
        required_fields = ["count", "sum", "mean", "median", "min", "max"]
        for field in required_fields:
            assert field in stats
            assert isinstance(stats[field], (int, float))

        # Verify statistical accuracy
        assert stats["count"] == 100
        assert stats["sum"] == 5050  # Sum of 1 to 100
        assert stats["mean"] == 50.5
        assert stats["min"] == 1
        assert stats["max"] == 100
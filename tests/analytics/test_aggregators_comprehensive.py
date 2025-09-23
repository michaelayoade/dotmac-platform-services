"""
Comprehensive tests for analytics aggregators.

Tests all aggregation functionality including:
- Basic aggregations (sum, avg, min, max, count)
- Time-based aggregations
- Percentile calculations
- Group by operations
- Real-time aggregations
- Error handling
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dotmac.platform.analytics.aggregators import (
    AggregationEngine,
    AggregationType,
    MetricAggregator,
    RealTimeAggregator,
    TimeSeriesAggregator,
)


@pytest.fixture
def sample_events():
    """Generate sample event data."""
    now = datetime.now(timezone.utc)
    return [
        {
            "event_id": "evt1",
            "event_name": "login",
            "timestamp": now - timedelta(hours=2),
            "user_id": "user1",
            "properties": {"browser": "chrome", "country": "US"},
        },
        {
            "event_id": "evt2",
            "event_name": "logout",
            "timestamp": now - timedelta(hours=1),
            "user_id": "user1",
            "properties": {"browser": "chrome", "country": "US"},
        },
        {
            "event_id": "evt3",
            "event_name": "login",
            "timestamp": now - timedelta(minutes=30),
            "user_id": "user2",
            "properties": {"browser": "firefox", "country": "UK"},
        },
        {
            "event_id": "evt4",
            "event_name": "purchase",
            "timestamp": now - timedelta(minutes=15),
            "user_id": "user2",
            "properties": {"amount": 99.99, "product": "premium"},
        },
    ]


@pytest.fixture
def sample_metrics():
    """Generate sample metric data."""
    now = datetime.now(timezone.utc)
    return [
        {"metric_name": "api_latency", "value": 100.0, "timestamp": now - timedelta(hours=1)},
        {"metric_name": "api_latency", "value": 150.0, "timestamp": now - timedelta(minutes=45)},
        {"metric_name": "api_latency", "value": 200.0, "timestamp": now - timedelta(minutes=30)},
        {"metric_name": "api_latency", "value": 120.0, "timestamp": now - timedelta(minutes=15)},
        {"metric_name": "request_count", "value": 10.0, "timestamp": now - timedelta(hours=1)},
        {"metric_name": "request_count", "value": 15.0, "timestamp": now - timedelta(minutes=30)},
        {"metric_name": "request_count", "value": 20.0, "timestamp": now},
    ]


@pytest.fixture
def aggregation_engine():
    """Create aggregation engine instance."""
    return AggregationEngine()


@pytest.fixture
def metric_aggregator():
    """Create metric aggregator instance."""
    return MetricAggregator()


@pytest.fixture
def time_series_aggregator():
    """Create time series aggregator instance."""
    return TimeSeriesAggregator()


@pytest.fixture
def realtime_aggregator():
    """Create real-time aggregator instance."""
    return RealTimeAggregator()


class TestAggregationEngine:
    """Test AggregationEngine class."""

    def test_init_aggregation_engine(self, aggregation_engine):
        """Test aggregation engine initialization."""
        assert aggregation_engine is not None
        assert hasattr(aggregation_engine, "aggregate")

    async def test_aggregate_sum(self, aggregation_engine, sample_metrics):
        """Test sum aggregation."""
        result = await aggregation_engine.aggregate(
            data=sample_metrics,
            aggregation_type=AggregationType.SUM,
            field="value",
        )
        expected_sum = sum(m["value"] for m in sample_metrics)
        assert result == expected_sum

    async def test_aggregate_avg(self, aggregation_engine, sample_metrics):
        """Test average aggregation."""
        result = await aggregation_engine.aggregate(
            data=sample_metrics,
            aggregation_type=AggregationType.AVG,
            field="value",
        )
        expected_avg = sum(m["value"] for m in sample_metrics) / len(sample_metrics)
        assert result == pytest.approx(expected_avg)

    async def test_aggregate_min(self, aggregation_engine, sample_metrics):
        """Test minimum aggregation."""
        result = await aggregation_engine.aggregate(
            data=sample_metrics,
            aggregation_type=AggregationType.MIN,
            field="value",
        )
        expected_min = min(m["value"] for m in sample_metrics)
        assert result == expected_min

    async def test_aggregate_max(self, aggregation_engine, sample_metrics):
        """Test maximum aggregation."""
        result = await aggregation_engine.aggregate(
            data=sample_metrics,
            aggregation_type=AggregationType.MAX,
            field="value",
        )
        expected_max = max(m["value"] for m in sample_metrics)
        assert result == expected_max

    async def test_aggregate_count(self, aggregation_engine, sample_metrics):
        """Test count aggregation."""
        result = await aggregation_engine.aggregate(
            data=sample_metrics,
            aggregation_type=AggregationType.COUNT,
            field="value",
        )
        assert result == len(sample_metrics)

    async def test_aggregate_with_group_by(self, aggregation_engine, sample_metrics):
        """Test aggregation with group by."""
        result = await aggregation_engine.aggregate(
            data=sample_metrics,
            aggregation_type=AggregationType.SUM,
            field="value",
            group_by="metric_name",
        )
        assert "api_latency" in result
        assert "request_count" in result
        assert result["api_latency"] == 570.0  # 100 + 150 + 200 + 120
        assert result["request_count"] == 45.0  # 10 + 15 + 20

    async def test_aggregate_with_filters(self, aggregation_engine, sample_metrics):
        """Test aggregation with filters."""
        # Filter for api_latency metrics only
        filtered_data = [m for m in sample_metrics if m["metric_name"] == "api_latency"]
        result = await aggregation_engine.aggregate(
            data=filtered_data,
            aggregation_type=AggregationType.AVG,
            field="value",
        )
        expected_avg = sum(m["value"] for m in filtered_data) / len(filtered_data)
        assert result == pytest.approx(expected_avg)

    async def test_aggregate_empty_data(self, aggregation_engine):
        """Test aggregation with empty data."""
        result = await aggregation_engine.aggregate(
            data=[],
            aggregation_type=AggregationType.SUM,
            field="value",
        )
        assert result == 0

    async def test_aggregate_missing_field(self, aggregation_engine):
        """Test aggregation with missing field."""
        data = [{"name": "test", "other": 10}]
        result = await aggregation_engine.aggregate(
            data=data,
            aggregation_type=AggregationType.SUM,
            field="value",  # Field doesn't exist
        )
        assert result == 0


class TestMetricAggregator:
    """Test MetricAggregator class."""

    def test_init_metric_aggregator(self, metric_aggregator):
        """Test metric aggregator initialization."""
        assert metric_aggregator is not None
        assert hasattr(metric_aggregator, "aggregate_metrics")

    async def test_aggregate_metrics_basic(self, metric_aggregator, sample_metrics):
        """Test basic metric aggregation."""
        result = await metric_aggregator.aggregate_metrics(
            metrics=sample_metrics,
            aggregation_type="sum",
        )
        assert result is not None
        assert isinstance(result, (dict, float, int))

    async def test_aggregate_metrics_by_name(self, metric_aggregator, sample_metrics):
        """Test metric aggregation grouped by name."""
        result = await metric_aggregator.aggregate_metrics(
            metrics=sample_metrics,
            aggregation_type="avg",
            group_by="metric_name",
        )
        assert isinstance(result, dict)
        assert "api_latency" in result
        assert "request_count" in result

    async def test_percentile_calculation(self, metric_aggregator, sample_metrics):
        """Test percentile calculation."""
        # Get 50th percentile (median)
        api_metrics = [m for m in sample_metrics if m["metric_name"] == "api_latency"]
        result = await metric_aggregator.calculate_percentile(
            metrics=api_metrics,
            percentile=50,
            field="value",
        )
        # Median of [100, 150, 200, 120] = 135
        assert result == pytest.approx(135.0, rel=0.1)

    async def test_percentile_95(self, metric_aggregator, sample_metrics):
        """Test 95th percentile calculation."""
        api_metrics = [m for m in sample_metrics if m["metric_name"] == "api_latency"]
        result = await metric_aggregator.calculate_percentile(
            metrics=api_metrics,
            percentile=95,
            field="value",
        )
        # 95th percentile should be close to max value
        assert result >= 150.0

    async def test_percentile_99(self, metric_aggregator, sample_metrics):
        """Test 99th percentile calculation."""
        api_metrics = [m for m in sample_metrics if m["metric_name"] == "api_latency"]
        result = await metric_aggregator.calculate_percentile(
            metrics=api_metrics,
            percentile=99,
            field="value",
        )
        # 99th percentile should be very close to max
        assert result >= 190.0

    async def test_aggregate_metrics_with_time_range(self, metric_aggregator, sample_metrics):
        """Test metric aggregation with time range filter."""
        now = datetime.now(timezone.utc)
        recent_metrics = [
            m for m in sample_metrics
            if m["timestamp"] >= now - timedelta(minutes=30)
        ]
        result = await metric_aggregator.aggregate_metrics(
            metrics=recent_metrics,
            aggregation_type="count",
        )
        assert result == len(recent_metrics)


class TestTimeSeriesAggregator:
    """Test TimeSeriesAggregator class."""

    def test_init_time_series_aggregator(self, time_series_aggregator):
        """Test time series aggregator initialization."""
        assert time_series_aggregator is not None
        assert hasattr(time_series_aggregator, "aggregate_time_series")

    async def test_aggregate_by_hour(self, time_series_aggregator, sample_metrics):
        """Test time series aggregation by hour."""
        result = await time_series_aggregator.aggregate_time_series(
            data=sample_metrics,
            interval="hour",
            aggregation_type="count",
        )
        assert isinstance(result, list)
        # Should have at least 2 buckets (current hour and previous hour)
        assert len(result) >= 2

    async def test_aggregate_by_minute(self, time_series_aggregator, sample_metrics):
        """Test time series aggregation by minute."""
        result = await time_series_aggregator.aggregate_time_series(
            data=sample_metrics,
            interval="minute",
            aggregation_type="avg",
            field="value",
        )
        assert isinstance(result, list)
        # Each bucket should have timestamp and value
        if result:
            assert "timestamp" in result[0]
            assert "value" in result[0]

    async def test_aggregate_by_day(self, time_series_aggregator, sample_events):
        """Test time series aggregation by day."""
        result = await time_series_aggregator.aggregate_time_series(
            data=sample_events,
            interval="day",
            aggregation_type="count",
        )
        assert isinstance(result, list)
        # All sample events are within same day
        assert len(result) == 1

    async def test_fill_gaps_in_time_series(self, time_series_aggregator):
        """Test filling gaps in time series data."""
        now = datetime.now(timezone.utc)
        sparse_data = [
            {"timestamp": now - timedelta(hours=3), "value": 10},
            {"timestamp": now, "value": 20},
        ]
        result = await time_series_aggregator.aggregate_time_series(
            data=sparse_data,
            interval="hour",
            aggregation_type="sum",
            field="value",
            fill_gaps=True,
        )
        # Should have 4 buckets (0, -1, -2, -3 hours)
        assert len(result) == 4
        # Check that gaps are filled with 0
        zero_buckets = [b for b in result if b["value"] == 0]
        assert len(zero_buckets) == 2

    async def test_time_series_with_custom_aggregation(self, time_series_aggregator):
        """Test time series with custom aggregation function."""

        def custom_agg(values):
            """Custom aggregation: return range (max - min)."""
            if not values:
                return 0
            return max(values) - min(values)

        data = [
            {"timestamp": datetime.now(timezone.utc), "value": 10},
            {"timestamp": datetime.now(timezone.utc), "value": 20},
            {"timestamp": datetime.now(timezone.utc), "value": 15},
        ]

        with patch.object(time_series_aggregator, "custom_aggregation", custom_agg):
            result = await time_series_aggregator.aggregate_time_series(
                data=data,
                interval="hour",
                aggregation_type="custom",
                field="value",
            )
            if result:
                # Range should be 20 - 10 = 10
                assert result[0]["value"] == 10


class TestRealTimeAggregator:
    """Test RealTimeAggregator class."""

    def test_init_realtime_aggregator(self, realtime_aggregator):
        """Test real-time aggregator initialization."""
        assert realtime_aggregator is not None
        assert hasattr(realtime_aggregator, "add_data_point")
        assert hasattr(realtime_aggregator, "get_current_aggregation")

    async def test_add_data_point(self, realtime_aggregator):
        """Test adding data point to real-time aggregator."""
        data_point = {"metric": "latency", "value": 100.0, "timestamp": datetime.now(timezone.utc)}
        await realtime_aggregator.add_data_point(data_point)

        result = await realtime_aggregator.get_current_aggregation("latency")
        assert result is not None

    async def test_sliding_window_aggregation(self, realtime_aggregator):
        """Test sliding window aggregation."""
        now = datetime.now(timezone.utc)

        # Add data points over time
        for i in range(10):
            await realtime_aggregator.add_data_point({
                "metric": "requests",
                "value": i + 1,
                "timestamp": now - timedelta(seconds=i * 10),
            })

        # Get aggregation for last minute
        result = await realtime_aggregator.get_window_aggregation(
            metric="requests",
            window_seconds=60,
            aggregation_type="sum",
        )
        # Should sum values from last 60 seconds (6 data points)
        assert result > 0

    async def test_real_time_percentiles(self, realtime_aggregator):
        """Test real-time percentile tracking."""
        # Add many data points
        for i in range(100):
            await realtime_aggregator.add_data_point({
                "metric": "response_time",
                "value": i,
                "timestamp": datetime.now(timezone.utc),
            })

        # Get percentiles
        p50 = await realtime_aggregator.get_percentile("response_time", 50)
        p95 = await realtime_aggregator.get_percentile("response_time", 95)
        p99 = await realtime_aggregator.get_percentile("response_time", 99)

        assert p50 == pytest.approx(49.5, rel=0.1)
        assert p95 == pytest.approx(94.5, rel=0.1)
        assert p99 == pytest.approx(98.5, rel=0.1)

    async def test_concurrent_updates(self, realtime_aggregator):
        """Test concurrent updates to real-time aggregator."""

        async def add_points(start_value):
            for i in range(10):
                await realtime_aggregator.add_data_point({
                    "metric": "concurrent_test",
                    "value": start_value + i,
                    "timestamp": datetime.now(timezone.utc),
                })

        # Run multiple concurrent updates
        await asyncio.gather(
            add_points(0),
            add_points(100),
            add_points(200),
        )

        # Check final count
        result = await realtime_aggregator.get_current_aggregation("concurrent_test")
        assert result["count"] == 30

    async def test_expiry_of_old_data(self, realtime_aggregator):
        """Test that old data points are expired."""
        now = datetime.now(timezone.utc)

        # Add old data point
        await realtime_aggregator.add_data_point({
            "metric": "expiry_test",
            "value": 100,
            "timestamp": now - timedelta(hours=2),
        })

        # Add recent data point
        await realtime_aggregator.add_data_point({
            "metric": "expiry_test",
            "value": 200,
            "timestamp": now,
        })

        # Get aggregation for last hour
        result = await realtime_aggregator.get_window_aggregation(
            metric="expiry_test",
            window_seconds=3600,
            aggregation_type="sum",
        )
        # Should only include recent point
        assert result == 200


class TestEdgeCases:
    """Test edge cases and error handling."""

    async def test_aggregate_null_values(self, aggregation_engine):
        """Test aggregation with null values."""
        data = [
            {"value": 10},
            {"value": None},
            {"value": 20},
            {"value": None},
            {"value": 30},
        ]
        result = await aggregation_engine.aggregate(
            data=data,
            aggregation_type=AggregationType.SUM,
            field="value",
        )
        # Should skip None values
        assert result == 60

    async def test_aggregate_mixed_types(self, aggregation_engine):
        """Test aggregation with mixed data types."""
        data = [
            {"value": 10},
            {"value": "20"},  # String that can be converted
            {"value": 30.5},
            {"value": "invalid"},  # Invalid string
        ]
        result = await aggregation_engine.aggregate(
            data=data,
            aggregation_type=AggregationType.SUM,
            field="value",
        )
        # Should handle numeric strings and skip invalid
        assert result == 60.5

    async def test_divide_by_zero_in_average(self, aggregation_engine):
        """Test average calculation with no valid values."""
        data = [
            {"value": None},
            {"value": None},
        ]
        result = await aggregation_engine.aggregate(
            data=data,
            aggregation_type=AggregationType.AVG,
            field="value",
        )
        # Should return 0 or None for empty average
        assert result in (0, None)

    async def test_percentile_with_single_value(self, metric_aggregator):
        """Test percentile calculation with single value."""
        metrics = [{"value": 42.0}]
        result = await metric_aggregator.calculate_percentile(
            metrics=metrics,
            percentile=50,
            field="value",
        )
        # Any percentile of single value is that value
        assert result == 42.0

    async def test_percentile_with_empty_data(self, metric_aggregator):
        """Test percentile calculation with empty data."""
        result = await metric_aggregator.calculate_percentile(
            metrics=[],
            percentile=50,
            field="value",
        )
        # Should handle gracefully
        assert result in (0, None)

    async def test_time_series_with_unsorted_data(self, time_series_aggregator):
        """Test time series aggregation with unsorted timestamps."""
        now = datetime.now(timezone.utc)
        unsorted_data = [
            {"timestamp": now, "value": 30},
            {"timestamp": now - timedelta(hours=2), "value": 10},
            {"timestamp": now - timedelta(hours=1), "value": 20},
        ]
        result = await time_series_aggregator.aggregate_time_series(
            data=unsorted_data,
            interval="hour",
            aggregation_type="sum",
            field="value",
        )
        # Should handle unsorted data correctly
        assert len(result) == 3
        # Check values are aggregated correctly
        total = sum(bucket["value"] for bucket in result)
        assert total == 60
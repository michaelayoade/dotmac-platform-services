"""
Metric aggregation utilities for analytics processing.
"""

import statistics
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Deque, Tuple

from .base import Metric


class MetricAggregator:
    """Base aggregator for metrics."""

    def __init__(self, window_size: int = 60):
        """
        Initialize aggregator.

        Args:
            window_size: Time window in seconds for aggregation
        """
        self.window_size = window_size
        self.metrics_buffer: Dict[str, Deque[Dict[str, Any]]] = defaultdict(
            lambda: deque(maxlen=1000)
        )

    def add_metric(self, metric: Metric) -> None:
        """Add a metric to the aggregator."""
        key = self._get_key(metric)
        self.metrics_buffer[key].append(
            {
                "timestamp": metric.timestamp,
                "value": metric.value,
                "attributes": metric.attributes,
            }
        )

    def add(self, metric: Metric) -> None:
        """Add a metric to the aggregator (alias for add_metric)."""
        self.add_metric(metric)

    def _get_key(self, metric: Metric) -> str:
        """Generate aggregation key for a metric."""
        # Create key from metric name and important attributes
        key_parts = [metric.name, metric.tenant_id]

        # Add selected attributes to key
        for attr in ["service", "endpoint", "method"]:
            if attr in metric.attributes:
                key_parts.append(f"{attr}:{metric.attributes[attr]}")

        return "|".join(key_parts)

    def get_aggregates(
        self,
        aggregation_type: str = "avg",
        cutoff_time: Optional[datetime] = None,
    ) -> Dict[str, float]:
        """
        Get aggregated metrics.

        Args:
            aggregation_type: Type of aggregation (avg, sum, min, max, count)
            cutoff_time: Only consider metrics after this time

        Returns:
            Dictionary of aggregated values by key
        """
        if cutoff_time is None:
            cutoff_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
                seconds=self.window_size
            )

        aggregates = {}

        for key, buffer in self.metrics_buffer.items():
            # Filter by time
            values = [entry["value"] for entry in buffer if entry["timestamp"] >= cutoff_time]

            if not values:
                continue

            if aggregation_type == "avg":
                aggregates[key] = statistics.mean(values)
            elif aggregation_type == "sum":
                aggregates[key] = sum(values)
            elif aggregation_type == "min":
                aggregates[key] = min(values)
            elif aggregation_type == "max":
                aggregates[key] = max(values)
            elif aggregation_type == "count":
                aggregates[key] = len(values)
            elif aggregation_type == "median":
                aggregates[key] = statistics.median(values)
            elif aggregation_type == "stddev":
                aggregates[key] = statistics.stdev(values) if len(values) > 1 else 0
            elif aggregation_type == "p95":
                aggregates[key] = self._percentile(values, 95)
            elif aggregation_type == "p99":
                aggregates[key] = self._percentile(values, 99)

        return aggregates

    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value."""
        if not values:
            return 0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * (percentile / 100))
        return sorted_values[min(index, len(sorted_values) - 1)]

    def clear_old_metrics(self, retention_seconds: int = 3600) -> None:
        """Clear metrics older than retention period."""
        cutoff_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
            seconds=retention_seconds
        )

        for buffer in self.metrics_buffer.values():
            # Remove old entries
            while buffer and buffer[0]["timestamp"] < cutoff_time:
                buffer.popleft()


class TimeWindowAggregator:
    """Aggregator with fixed time windows."""

    def __init__(self, window_minutes: int = 5):
        """
        Initialize time window aggregator.

        Args:
            window_minutes: Size of time window in minutes
        """
        self.window_minutes = window_minutes
        self.windows: Dict[datetime, Dict[str, List[float]]] = defaultdict(
            lambda: defaultdict(list)
        )

    def add(self, metric: Metric) -> None:
        """Add metric to appropriate time window."""
        window_start = self._get_window_start(metric.timestamp)
        key = f"{metric.name}:{metric.tenant_id}"
        self.windows[window_start][key].append(metric.value)

    def add_data_point(
        self, metric_name: str, value: float, attributes: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a data point to the aggregator."""
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)
        window_start = self._get_window_start(current_time)
        key = metric_name
        self.windows[window_start][key].append(value)

    def _get_window_start(self, timestamp: datetime) -> datetime:
        """Get the start of the time window for a timestamp."""
        minutes = (timestamp.minute // self.window_minutes) * self.window_minutes
        return timestamp.replace(minute=minutes, second=0, microsecond=0)

    def get_window_aggregates(
        self,
        window_start: datetime,
        aggregation_fn: Callable[[List[float]], float] = statistics.mean,
    ) -> Dict[str, float]:
        """
        Get aggregates for a specific time window.

        Args:
            window_start: Start of the time window
            aggregation_fn: Function to aggregate values

        Returns:
            Aggregated values for the window
        """
        if window_start not in self.windows:
            return {}

        aggregates = {}
        for key, values in self.windows[window_start].items():
            if values:
                aggregates[key] = aggregation_fn(values)

        return aggregates

    def get_recent_windows(
        self,
        count: int = 12,
        aggregation_fn: Callable[[List[float]], float] = statistics.mean,
    ) -> List[Dict[str, Any]]:
        """
        Get aggregates for recent time windows.

        Args:
            count: Number of recent windows to return
            aggregation_fn: Aggregation function

        Returns:
            List of window aggregates with timestamps
        """
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)
        results = []

        for i in range(count):
            window_start = self._get_window_start(
                current_time - timedelta(minutes=i * self.window_minutes)
            )

            aggregates = self.get_window_aggregates(window_start, aggregation_fn)
            if aggregates:
                results.append(
                    {
                        "window_start": window_start.isoformat(),
                        "window_end": (
                            window_start + timedelta(minutes=self.window_minutes)
                        ).isoformat(),
                        "aggregates": aggregates,
                    }
                )

        return results

    def cleanup_old_windows(self, retention_hours: int = 24) -> None:
        """Remove old time windows beyond retention period."""
        cutoff_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
            hours=retention_hours
        )
        old_windows = [window for window in self.windows.keys() if window < cutoff_time]
        for window in old_windows:
            del self.windows[window]


class StatisticalAggregator:
    """Advanced statistical aggregation for metrics."""

    def __init__(self):
        """Initialize statistical aggregator."""
        self.data_points: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)

    def add(self, metric: Metric) -> None:
        """Add metric for statistical analysis."""
        key = f"{metric.name}:{metric.tenant_id}"
        self.data_points[key].append((metric.timestamp, metric.value))

    def add_value(self, metric_name: str, value: float) -> None:
        """Add a value for statistical analysis."""
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)
        self.data_points[metric_name].append((current_time, value))

    def get_statistics(self, key: str, time_range: Optional[timedelta] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive statistics for a metric.

        Args:
            key: Metric key
            time_range: Optional time range to consider

        Returns:
            Dictionary of statistical measures
        """
        if key not in self.data_points:
            return {"count": 0, "mean": 0.0, "median": 0.0, "std_dev": 0.0, "min": 0.0, "max": 0.0}

        # Filter by time range if specified
        values = self.data_points[key]
        if time_range:
            cutoff_time = datetime.now(timezone.utc).replace(tzinfo=None) - time_range
            values = [(ts, val) for ts, val in values if ts >= cutoff_time]

        if not values:
            return {"count": 0, "mean": 0.0, "median": 0.0, "std_dev": 0.0, "min": 0.0, "max": 0.0}

        # Extract just the numeric values
        nums = [val for _, val in values]

        stats = {
            "count": len(nums),
            "sum": sum(nums),
            "mean": statistics.mean(nums),
            "median": statistics.median(nums),
            "min": min(nums),
            "max": max(nums),
        }

        # Additional statistics for multiple values
        if len(nums) > 1:
            stats.update(
                {
                    "std_dev": statistics.stdev(nums),
                    "variance": statistics.variance(nums),
                }
            )

            # Calculate percentiles
            sorted_nums = sorted(nums)
            for p in [25, 50, 75, 90, 95, 99]:
                index = int(len(sorted_nums) * (p / 100))
                stats[f"p{p}"] = sorted_nums[min(index, len(sorted_nums) - 1)]

        # Time-based statistics
        timestamps = [ts for ts, _ in values]
        if timestamps:
            stats["first_seen"] = min(timestamps).isoformat()  # type: ignore
            stats["last_seen"] = max(timestamps).isoformat()  # type: ignore
            stats["duration_seconds"] = (max(timestamps) - min(timestamps)).total_seconds()  # type: ignore

        return stats

    def get_trend(
        self,
        key: str,
        window_size: int = 10,
    ) -> Dict[str, Any]:
        """
        Calculate trend information for a metric.

        Args:
            key: Metric key
            window_size: Number of points for moving average

        Returns:
            Trend information
        """
        if key not in self.data_points or len(self.data_points[key]) < 2:
            return {}

        values = self.data_points[key]
        sorted_values = sorted(values, key=lambda x: x[0])

        # Calculate moving average
        moving_avg: List[float] = []
        for i in range(len(sorted_values)):
            start_idx = max(0, i - window_size + 1)
            window_values = [val for _, val in sorted_values[start_idx : i + 1]]
            moving_avg.append(statistics.mean(window_values))

        # Determine trend direction
        if len(moving_avg) >= 2:
            recent_avg = statistics.mean(moving_avg[-window_size:])
            older_avg = statistics.mean(moving_avg[:window_size])
            trend_direction = "increasing" if recent_avg > older_avg else "decreasing"
            trend_percentage = ((recent_avg - older_avg) / older_avg * 100) if older_avg != 0 else 0
        else:
            trend_direction = "stable"
            trend_percentage = 0

        return {
            "direction": trend_direction,
            "percentage_change": trend_percentage,
            "moving_average": moving_avg[-1] if moving_avg else 0,
            "data_points": len(sorted_values),
        }

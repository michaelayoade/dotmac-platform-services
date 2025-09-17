"""
Metrics collection middleware for plugin execution.

Collects performance metrics, usage statistics, and operational data for plugin analysis.
"""


import statistics
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from ..core.plugin_base import BasePlugin

from dotmac.platform.observability.unified_logging import get_logger
class MetricType(Enum):
    """Types of metrics that can be collected."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATE = "rate"

@dataclass
class MetricPoint:
    """Single metric data point."""

    timestamp: float
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class MetricSeries:
    """Time series of metric points."""

    name: str
    metric_type: MetricType
    description: str
    points: deque = field(default_factory=lambda: deque(maxlen=1000))  # Keep last 1000 points
    labels: dict[str, str] = field(default_factory=dict)

    def add_point(
        self,
        value: float,
        labels: Optional[dict[str, str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Add a metric point."""
        point = MetricPoint(
            timestamp=time.time(),
            value=value,
            labels=labels or {},
            metadata=metadata or {},
        )
        self.points.append(point)

    def get_latest_value(self) -> Optional[float]:
        """Get the most recent metric value."""
        return self.points[-1].value if self.points else None

    def get_average(self, duration_seconds: Optional[float] = None) -> Optional[float]:
        """Get average value over specified duration."""
        if not self.points:
            return None

        if duration_seconds is None:
            # Average of all points
            return statistics.mean(point.value for point in self.points)

        # Average over time window
        cutoff_time = time.time() - duration_seconds
        recent_points = [point.value for point in self.points if point.timestamp >= cutoff_time]

        return statistics.mean(recent_points) if recent_points else None

    def get_percentile(
        self, percentile: float, duration_seconds: Optional[float] = None
    ) -> Optional[float]:
        """Get percentile value over specified duration."""
        if not self.points:
            return None

        if duration_seconds is None:
            values = [point.value for point in self.points]
        else:
            cutoff_time = time.time() - duration_seconds
            values = [point.value for point in self.points if point.timestamp >= cutoff_time]

        if not values:
            return None

        try:
            return statistics.quantiles(sorted(values), n=100)[int(percentile) - 1]
        except (IndexError, statistics.StatisticsError):
            return None

class PerformanceTimer:
    """Context manager for timing plugin operations."""

    def __init__(
        self,
        metrics_middleware: "MetricsMiddleware",
        metric_name: str,
        labels: Optional[dict[str, str]] = None,
    ):
        self.metrics_middleware = metrics_middleware
        self.metric_name = metric_name
        self.labels = labels or {}
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        if self.start_time is not None:
            duration = self.end_time - self.start_time
            self.metrics_middleware.record_timer(self.metric_name, duration, self.labels)

            # Record success/failure
            success = exc_type is None
            self.labels["status"] = "success" if success else "error"
            self.metrics_middleware.increment_counter(f"{self.metric_name}_total", self.labels)

    def get_duration(self) -> Optional[float]:
        """Get the measured duration."""
        if self.start_time is not None and self.end_time is not None:
            return self.end_time - self.start_time
        return None

class MetricsMiddleware:
    """
    Plugin metrics collection middleware.

    Collects performance, usage, and operational metrics for plugin analysis and monitoring.
    """

    def __init__(self, max_series: int = 1000, retention_hours: int = 24):
        self.max_series = max_series
        self.retention_hours = retention_hours

        # Metric storage
        self._metrics: dict[str, MetricSeries] = {}

        # Plugin-specific metrics
        self._plugin_metrics: dict[str, dict[str, MetricSeries]] = defaultdict(dict)

        # Event callbacks
        self._metric_callbacks: list[Callable[[str, MetricPoint], None]] = []

        # Statistics
        self._collection_stats = {
            "total_metrics_collected": 0,
            "unique_metrics": 0,
            "collection_errors": 0,
            "last_cleanup": time.time(),
        }

        self._logger = get_logger("plugins.metrics_middleware")

        # Initialize built-in metrics
        self._initialize_builtin_metrics()

    def _initialize_builtin_metrics(self) -> None:
        """Initialize built-in plugin metrics."""

        # Plugin execution metrics
        self.create_metric(
            "plugin_execution_time",
            MetricType.TIMER,
            "Plugin method execution time in seconds",
        )

        self.create_metric(
            "plugin_executions_total",
            MetricType.COUNTER,
            "Total number of plugin method executions",
        )

        self.create_metric(
            "plugin_errors_total",
            MetricType.COUNTER,
            "Total number of plugin execution errors",
        )

        self.create_metric(
            "plugin_active_requests",
            MetricType.GAUGE,
            "Number of currently executing plugin requests",
        )

        # Plugin lifecycle metrics
        self.create_metric(
            "plugin_initializations_total",
            MetricType.COUNTER,
            "Total number of plugin initializations",
        )

        self.create_metric(
            "plugin_shutdowns_total",
            MetricType.COUNTER,
            "Total number of plugin shutdowns",
        )

        # System metrics
        self.create_metric("plugins_loaded", MetricType.GAUGE, "Number of loaded plugins")

        self.create_metric("plugins_active", MetricType.GAUGE, "Number of active plugins")

    def create_metric(
        self,
        name: str,
        metric_type: MetricType,
        description: str,
        labels: Optional[dict[str, str]] = None,
    ) -> MetricSeries:
        """
        Create a new metric series.

        Args:
            name: Metric name
            metric_type: Type of metric
            description: Metric description
            labels: Default labels for the metric

        Returns:
            Created metric series
        """
        if name in self._metrics:
            self._logger.warning(f"Metric '{name}' already exists")
            return self._metrics[name]

        # Check limits
        if len(self._metrics) >= self.max_series:
            self._logger.warning(f"Maximum metric series limit ({self.max_series}) reached")
            return None

        metric = MetricSeries(
            name=name,
            metric_type=metric_type,
            description=description,
            labels=labels or {},
        )

        self._metrics[name] = metric
        self._collection_stats["unique_metrics"] = len(self._metrics)

        self._logger.debug(f"Created metric: {name} ({metric_type.value})")
        return metric

    def record_metric(
        self,
        name: str,
        value: float,
        labels: Optional[dict[str, str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Record a metric value.

        Args:
            name: Metric name
            value: Metric value
            labels: Optional labels
            metadata: Optional metadata
        """
        if name not in self._metrics:
            self._logger.warning(f"Metric '{name}' not found")
            return

        try:
            metric = self._metrics[name]
            metric.add_point(value, labels, metadata)

            self._collection_stats["total_metrics_collected"] += 1

            # Notify callbacks
            if metric.points:
                point = metric.points[-1]
                for callback in self._metric_callbacks:
                    try:
                        callback(name, point)
                    except Exception as e:
                        self._logger.error(f"Metric callback error: {e}")

        except Exception as e:
            self._collection_stats["collection_errors"] += 1
            self._logger.error(f"Error recording metric {name}: {e}")

    def increment_counter(
        self, name: str, labels: Optional[dict[str, str]] = None, increment: float = 1.0
    ) -> None:
        """Increment a counter metric."""
        if name in self._metrics and self._metrics[name].metric_type == MetricType.COUNTER:
            current_value = self._metrics[name].get_latest_value() or 0
            self.record_metric(name, current_value + increment, labels)
        else:
            self.record_metric(name, increment, labels)

    def set_gauge(self, name: str, value: float, labels: Optional[dict[str, str]] = None) -> None:
        """Set a gauge metric value."""
        self.record_metric(name, value, labels)

    def record_timer(
        self, name: str, duration: float, labels: Optional[dict[str, str]] = None
    ) -> None:
        """Record a timer metric."""
        self.record_metric(name, duration, labels, {"duration_seconds": duration})

    def record_histogram(
        self, name: str, value: float, labels: Optional[dict[str, str]] = None
    ) -> None:
        """Record a histogram metric."""
        self.record_metric(name, value, labels)

    # Plugin-specific metric recording

    def record_plugin_execution(
        self,
        plugin: BasePlugin,
        method_name: str,
        duration: float,
        success: bool,
        error_type: Optional[str] = None,
    ) -> None:
        """Record plugin execution metrics."""
        plugin_key = f"{plugin.domain}.{plugin.name}"

        labels = {
            "plugin": plugin_key,
            "domain": plugin.domain,
            "method": method_name,
            "status": "success" if success else "error",
        }

        if error_type:
            labels["error_type"] = error_type

        # Record execution time
        self.record_timer("plugin_execution_time", duration, labels)

        # Record execution count
        self.increment_counter("plugin_executions_total", labels)

        # Record errors
        if not success:
            self.increment_counter("plugin_errors_total", labels)

    def record_plugin_lifecycle(
        self,
        plugin: BasePlugin,
        event: str,  # "initialize", "shutdown", "activate", "deactivate"
        duration: Optional[float] = None,
        success: bool = True,
    ) -> None:
        """Record plugin lifecycle events."""
        plugin_key = f"{plugin.domain}.{plugin.name}"

        labels = {
            "plugin": plugin_key,
            "domain": plugin.domain,
            "event": event,
            "status": "success" if success else "error",
        }

        # Record lifecycle event
        metric_name = f"plugin_{event}_total"
        self.increment_counter(metric_name, labels)

        # Record duration if provided
        if duration is not None:
            duration_metric = f"plugin_{event}_time"
            self.record_timer(duration_metric, duration, labels)

    def update_plugin_counts(self, total_plugins: int, active_plugins: int) -> None:
        """Update plugin count gauges."""
        self.set_gauge("plugins_loaded", total_plugins)
        self.set_gauge("plugins_active", active_plugins)

    def record_active_request_start(self, plugin: BasePlugin, method_name: str) -> None:
        """Record the start of an active plugin request."""
        current_active = self.get_metric_value("plugin_active_requests") or 0
        self.set_gauge("plugin_active_requests", current_active + 1)

    def record_active_request_end(self, plugin: BasePlugin, method_name: str) -> None:
        """Record the end of an active plugin request."""
        current_active = self.get_metric_value("plugin_active_requests") or 0
        self.set_gauge("plugin_active_requests", max(0, current_active - 1))

    # Performance timer context manager

    def timer(self, metric_name: str, labels: Optional[dict[str, str]] = None) -> PerformanceTimer:
        """
        Create a performance timer context manager.

        Usage:
            with metrics_middleware.timer("my_operation"):
                # Code to time
                pass
        """
        return PerformanceTimer(self, metric_name, labels)

    def plugin_timer(self, plugin: BasePlugin, method_name: str) -> PerformanceTimer:
        """Create a timer specifically for plugin method execution."""
        labels = {
            "plugin": f"{plugin.domain}.{plugin.name}",
            "domain": plugin.domain,
            "method": method_name,
        }
        return PerformanceTimer(self, "plugin_execution_time", labels)

    # Metric retrieval and analysis

    def get_metric(self, name: str) -> Optional[MetricSeries]:
        """Get a metric series by name."""
        return self._metrics.get(name)

    def get_metric_value(self, name: str, default: Optional[float] = None) -> Optional[float]:
        """Get the latest value of a metric."""
        metric = self.get_metric(name)
        return metric.get_latest_value() if metric else default

    def get_metric_stats(
        self, name: str, duration_seconds: Optional[float] = None
    ) -> Optional[dict[str, Any]]:
        """Get statistical summary of a metric."""
        metric = self.get_metric(name)
        if not metric:
            return None

        cutoff_time = time.time() - duration_seconds if duration_seconds else None

        # Get values in time window
        if cutoff_time:
            values = [point.value for point in metric.points if point.timestamp >= cutoff_time]
        else:
            values = [point.value for point in metric.points]

        if not values:
            return None

        try:
            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
                "p50": metric.get_percentile(50, duration_seconds),
                "p95": metric.get_percentile(95, duration_seconds),
                "p99": metric.get_percentile(99, duration_seconds),
                "latest": metric.get_latest_value(),
            }
        except statistics.StatisticsError:
            return {
                "count": len(values),
                "min": min(values) if values else None,
                "max": max(values) if values else None,
                "latest": values[-1] if values else None,
            }

    def get_plugin_metrics(
        self, plugin_key: str, duration_seconds: Optional[float] = None
    ) -> dict[str, Any]:
        """Get all metrics for a specific plugin."""
        plugin_metrics = {}

        for name, metric in self._metrics.items():
            # Filter metrics for this plugin
            plugin_points = []
            cutoff_time = time.time() - duration_seconds if duration_seconds else None

            for point in metric.points:
                if cutoff_time and point.timestamp < cutoff_time:
                    continue

                if point.labels.get("plugin") == plugin_key:
                    plugin_points.append(point)

            if plugin_points:
                values = [point.value for point in plugin_points]
                plugin_metrics[name] = {
                    "count": len(values),
                    "total": sum(values),
                    "average": sum(values) / len(values),
                    "latest": values[-1] if values else None,
                }

        return plugin_metrics

    def get_top_plugins_by_metric(
        self,
        metric_name: str,
        limit: int = 10,
        duration_seconds: Optional[float] = None,
    ) -> list[dict[str, Any]]:
        """Get top plugins by metric value."""
        metric = self.get_metric(metric_name)
        if not metric:
            return []

        # Aggregate values by plugin
        plugin_values = defaultdict(list)
        cutoff_time = time.time() - duration_seconds if duration_seconds else None

        for point in metric.points:
            if cutoff_time and point.timestamp < cutoff_time:
                continue

            plugin_key = point.labels.get("plugin")
            if plugin_key:
                plugin_values[plugin_key].append(point.value)

        # Calculate totals and sort
        plugin_totals = []
        for plugin_key, values in plugin_values.items():
            total = sum(values)
            average = total / len(values)
            plugin_totals.append(
                {
                    "plugin": plugin_key,
                    "total": total,
                    "average": average,
                    "count": len(values),
                }
            )

        return sorted(plugin_totals, key=lambda x: x["total"], reverse=True)[:limit]

    # Event system

    def add_metric_callback(self, callback: Callable[[str, MetricPoint], None]) -> None:
        """Add callback for metric events."""
        self._metric_callbacks.append(callback)

    def remove_metric_callback(self, callback: Callable[[str, MetricPoint], None]) -> None:
        """Remove metric callback."""
        if callback in self._metric_callbacks:
            self._metric_callbacks.remove(callback)

    # Maintenance and cleanup

    def cleanup_old_metrics(self) -> None:
        """Clean up old metric points beyond retention period."""
        cutoff_time = time.time() - (self.retention_hours * 3600)

        for metric in self._metrics.values():
            # Remove old points
            while metric.points and metric.points[0].timestamp < cutoff_time:
                metric.points.popleft()

        self._collection_stats["last_cleanup"] = time.time()
        self._logger.debug("Cleaned up old metric points")

    def get_system_stats(self) -> dict[str, Any]:
        """Get metrics system statistics."""
        return {
            "total_metrics": len(self._metrics),
            "total_points_collected": self._collection_stats["total_metrics_collected"],
            "collection_errors": self._collection_stats["collection_errors"],
            "active_callbacks": len(self._metric_callbacks),
            "retention_hours": self.retention_hours,
            "max_series": self.max_series,
            "memory_usage": {
                "total_points": sum(len(m.points) for m in self._metrics.values()),
                "average_points_per_metric": sum(len(m.points) for m in self._metrics.values())
                / max(1, len(self._metrics)),
            },
            "last_cleanup": self._collection_stats["last_cleanup"],
        }

    def export_metrics(self, format: str = "json") -> str:
        """
        Export all metrics in specified format.

        Args:
            format: Export format ('json', 'prometheus', 'csv')

        Returns:
            Exported metrics as string
        """
        if format.lower() == "json":
            return self._export_json()
        elif format.lower() == "prometheus":
            return self._export_prometheus()
        elif format.lower() == "csv":
            return self._export_csv()
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _export_json(self) -> str:
        """Export metrics as JSON."""
        import json

        export_data = {"timestamp": time.time(), "metrics": {}}

        for name, metric in self._metrics.items():
            export_data["metrics"][name] = {
                "type": metric.metric_type.value,
                "description": metric.description,
                "points": [
                    {
                        "timestamp": point.timestamp,
                        "value": point.value,
                        "labels": point.labels,
                    }
                    for point in metric.points
                ],
            }

        return json.dumps(export_data, indent=2)

    def _export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []

        for name, metric in self._metrics.items():
            # Add help line
            lines.append(f"# HELP {name} {metric.description}")

            # Add type line
            prom_type = {
                MetricType.COUNTER: "counter",
                MetricType.GAUGE: "gauge",
                MetricType.HISTOGRAM: "histogram",
                MetricType.TIMER: "histogram",
            }.get(metric.metric_type, "gauge")

            lines.append(f"# TYPE {name} {prom_type}")

            # Add latest value
            latest_point = metric.points[-1] if metric.points else None
            if latest_point:
                labels_str = ",".join(f'{k}="{v}"' for k, v in latest_point.labels.items())
                labels_part = f"{{{labels_str}}}" if labels_str else ""
                lines.append(f"{name}{labels_part} {latest_point.value}")

        return "\n".join(lines)

    def _export_csv(self) -> str:
        """Export metrics as CSV."""
        lines = ["metric_name,timestamp,value,labels"]

        for name, metric in self._metrics.items():
            for point in metric.points:
                labels_str = ";".join(f"{k}={v}" for k, v in point.labels.items())
                lines.append(f'{name},{point.timestamp},{point.value},"{labels_str}"')

        return "\n".join(lines)

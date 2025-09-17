"""Observability and monitoring for dotmac-communications."""

import asyncio

import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from dotmac.platform.observability.unified_logging import get_logger

@dataclass
class MetricPoint:
    """Individual metric data point."""

    name: str
    value: float
    timestamp: datetime
    tags: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
        }

class MetricsCollector:
    """Collects and aggregates metrics."""

    def __init__(self, max_points: int = 10000):
        self.max_points = max_points
        self._metrics: dict[str, deque] = defaultdict(lambda: deque(maxlen=max_points))
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = defaultdict(float)
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.RLock()

    def counter(self, name: str, value: float = 1.0, tags: Optional[dict[str, str]] = None):
        """Increment a counter metric."""
        with self._lock:
            key = f"{name}:{tags}" if tags else name
            self._counters[key] += value

            point = MetricPoint(
                name=name,
                value=self._counters[key],
                timestamp=datetime.now(timezone.utc),
                tags=tags or {},
            )
            self._metrics[name].append(point)

    def gauge(self, name: str, value: float, tags: Optional[dict[str, str]] = None):
        """Set a gauge metric."""
        with self._lock:
            key = f"{name}:{tags}" if tags else name
            self._gauges[key] = value

            point = MetricPoint(
                name=name, value=value, timestamp=datetime.now(timezone.utc), tags=tags or {}
            )
            self._metrics[name].append(point)

    def histogram(self, name: str, value: float, tags: Optional[dict[str, str]] = None):
        """Record a histogram value."""
        with self._lock:
            key = f"{name}:{tags}" if tags else name
            self._histograms[key].append(value)

            # Keep only recent values (last 1000)
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-1000:]

            point = MetricPoint(
                name=name, value=value, timestamp=datetime.now(timezone.utc), tags=tags or {}
            )
            self._metrics[name].append(point)

    def timer(self, name: str, tags: Optional[dict[str, str]] = None):
        """Context manager for timing operations."""
        return TimerContext(self, name, tags)

    def get_metrics(
        self, name: Optional[str] = None, since: Optional[datetime] = None
    ) -> dict[str, list[dict[str, Any]]]:
        """Get collected metrics."""
        with self._lock:
            result = {}

            metrics_to_process = [name] if name else self._metrics.keys()

            for metric_name in metrics_to_process:
                if metric_name in self._metrics:
                    points = list(self._metrics[metric_name])

                    if since:
                        points = [p for p in points if p.timestamp >= since]

                    result[metric_name] = [p.to_dict() for p in points]

            return result

    def get_summary(self) -> dict[str, Any]:
        """Get metrics summary."""
        with self._lock:
            summary = {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {},
                "total_metrics": sum(len(points) for points in self._metrics.values()),
            }

            # Calculate histogram stats
            for key, values in self._histograms.items():
                if values:
                    summary["histograms"][key] = {
                        "count": len(values),
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values),
                        "p50": sorted(values)[len(values) // 2] if values else 0,
                        "p95": (
                            sorted(values)[int(len(values) * 0.95)]
                            if len(values) > 1
                            else (values[0] if values else 0)
                        ),
                        "p99": (
                            sorted(values)[int(len(values) * 0.99)]
                            if len(values) > 1
                            else (values[0] if values else 0)
                        ),
                    }

            return summary

class TimerContext:
    """Context manager for timing operations."""

    def __init__(
        self, collector: MetricsCollector, name: str, tags: Optional[dict[str, str]] = None
    ):
        self.collector = collector
        self.name = name
        self.tags = tags
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.collector.histogram(f"{self.name}_duration", duration, self.tags)

            # Also count the operation
            status = "error" if exc_type else "success"
            tags = {**(self.tags or {}), "status": status}
            self.collector.counter(f"{self.name}_count", 1.0, tags)

@asynccontextmanager
async def async_timer(
    collector: MetricsCollector, name: str, tags: Optional[dict[str, str]] = None
):
    """Async context manager for timing operations."""
    start_time = time.time()
    error_occurred = False

    try:
        yield
    except Exception:
        error_occurred = True
        raise
    finally:
        duration = time.time() - start_time
        collector.histogram(f"{name}_duration", duration, tags)

        # Count the operation
        status = "error" if error_occurred else "success"
        operation_tags = {**(tags or {}), "status": status}
        collector.counter(f"{name}_count", 1.0, operation_tags)

# Health checking
@dataclass
class HealthCheck:
    """Individual health check."""

    name: str
    check_func: Callable[[], bool]
    description: str = ""
    timeout: float = 5.0
    required: bool = True

class HealthMonitor:
    """Monitors service health."""

    def __init__(self):
        self._checks: dict[str, HealthCheck] = {}
        self._last_results: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()

    def add_check(self, check: HealthCheck):
        """Add a health check."""
        with self._lock:
            self._checks[check.name] = check

    def remove_check(self, name: str):
        """Remove a health check."""
        with self._lock:
            self._checks.pop(name, None)
            self._last_results.pop(name, None)

    async def run_checks(self) -> dict[str, Any]:
        """Run all health checks."""
        results = {}
        overall_healthy = True

        for name, check in self._checks.items():
            try:
                # Run check with timeout
                start_time = time.time()

                if asyncio.iscoroutinefunction(check.check_func):
                    healthy = await asyncio.wait_for(check.check_func(), timeout=check.timeout)
                else:
                    healthy = await asyncio.get_event_loop().run_in_executor(None, check.check_func)

                duration = time.time() - start_time

                results[name] = {
                    "healthy": bool(healthy),
                    "duration": duration,
                    "description": check.description,
                    "required": check.required,
                    "error": None,
                }

                if check.required and not healthy:
                    overall_healthy = False

            except asyncio.TimeoutError:
                results[name] = {
                    "healthy": False,
                    "duration": check.timeout,
                    "description": check.description,
                    "required": check.required,
                    "error": f"Timeout after {check.timeout}s",
                }
                if check.required:
                    overall_healthy = False

            except Exception as e:
                results[name] = {
                    "healthy": False,
                    "duration": 0,
                    "description": check.description,
                    "required": check.required,
                    "error": str(e),
                }
                if check.required:
                    overall_healthy = False

        # Update last results
        with self._lock:
            self._last_results = results

        return {
            "healthy": overall_healthy,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": results,
        }

    def get_last_results(self) -> dict[str, Any]:
        """Get last health check results."""
        with self._lock:
            return self._last_results.copy()

# Communications-specific observability
class CommunicationsObservability:
    """Observability for communications services."""

    def __init__(self):
        self.metrics = MetricsCollector()
        self.health = HealthMonitor()
        self.logger = get_logger(__name__)

        # Add default health checks
        self._setup_default_health_checks()

    def _setup_default_health_checks(self):
        """Setup default health checks."""

        def memory_check():
            """Check memory usage."""
            try:
                import psutil

                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                return memory_mb < 1000  # Less than 1GB
            except ImportError:
                return True  # Skip if psutil not available

        def thread_count_check():
            """Check thread count."""
            try:
                import threading
                return threading.active_count() < 100
            except Exception:
                return True

        self.health.add_check(
            HealthCheck(
                name="memory_usage",
                check_func=memory_check,
                description="Memory usage is within limits",
                required=False,
            )
        )

        self.health.add_check(
            HealthCheck(
                name="thread_count",
                check_func=thread_count_check,
                description="Thread count is reasonable",
                required=False,
            )
        )

    # Notification metrics
    def record_notification_sent(
        self, channel: str, success: bool = True, duration: Optional[float] = None
    ):
        """Record notification metrics."""
        tags = {"channel": channel, "status": "success" if success else "error"}

        self.metrics.counter("notifications_sent", 1.0, tags)

        if duration:
            self.metrics.histogram("notification_duration", duration, {"channel": channel})

    def record_notification_delivery(self, channel: str, delivered: bool = True):
        """Record delivery confirmation."""
        tags = {"channel": channel, "delivered": "yes" if delivered else "no"}
        self.metrics.counter("notifications_delivered", 1.0, tags)

    # WebSocket metrics
    def record_websocket_connection(self, tenant_id: Optional[str] = None, connected: bool = True):
        """Record WebSocket connection metrics."""
        tags = {
            "tenant_id": tenant_id or "unknown",
            "action": "connect" if connected else "disconnect",
        }
        self.metrics.counter("websocket_connections", 1.0, tags)

    def record_websocket_message(self, channel: str, size_bytes: int, success: bool = True):
        """Record WebSocket message metrics."""
        tags = {"channel": channel, "status": "success" if success else "error"}

        self.metrics.counter("websocket_messages", 1.0, tags)
        self.metrics.histogram("websocket_message_size", size_bytes, {"channel": channel})

    # Event metrics
    def record_event_published(
        self, topic: str, success: bool = True, duration: Optional[float] = None
    ):
        """Record event publishing metrics."""
        tags = {"topic": topic, "status": "success" if success else "error"}

        self.metrics.counter("events_published", 1.0, tags)

        if duration:
            self.metrics.histogram("event_publish_duration", duration, {"topic": topic})

    def record_event_processed(
        self, topic: str, success: bool = True, duration: Optional[float] = None
    ):
        """Record event processing metrics."""
        tags = {"topic": topic, "status": "success" if success else "error"}

        self.metrics.counter("events_processed", 1.0, tags)

        if duration:
            self.metrics.histogram("event_process_duration", duration, {"topic": topic})

    # Resource metrics
    def update_connection_count(self, service: str, count: int):
        """Update active connection count."""
        self.metrics.gauge(f"{service}_active_connections", count, {"service": service})

    def update_queue_size(self, queue_name: str, size: int):
        """Update queue size."""
        self.metrics.gauge("queue_size", size, {"queue": queue_name})

    # Error tracking
    def record_error(self, service: str, error_type: str, error_msg: Optional[str] = None):
        """Record service errors."""
        tags = {"service": service, "error_type": error_type}

        self.metrics.counter("service_errors", 1.0, tags)

        # Log error
        self.logger.error(
            f"Service error in {service}",
            extra={
                "service": service,
                "error_type": error_type,
                "error_message": error_msg,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    # Health check helpers
    def add_service_health_check(self, service_name: str, check_func: Callable[[], bool]):
        """Add health check for a service."""
        check = HealthCheck(
            name=f"{service_name}_health",
            check_func=check_func,
            description=f"{service_name} service is healthy",
            required=True,
        )
        self.health.add_check(check)

    async def get_health_status(self) -> dict[str, Any]:
        """Get overall health status."""
        return await self.health.run_checks()

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get metrics summary."""
        return self.metrics.get_summary()

    # Context managers for automatic instrumentation
    def time_operation(self, operation_name: str, service: str):
        """Timer context for operations."""
        return self.metrics.timer(f"{service}_{operation_name}", {"service": service})

    async def async_time_operation(self, operation_name: str, service: str):
        """Async timer context for operations."""
        return async_timer(self.metrics, f"{service}_{operation_name}", {"service": service})

# Global observability instance
_observability_instance: Optional[CommunicationsObservability] = None

def get_observability() -> CommunicationsObservability:
    """Get global observability instance."""
    global _observability_instance
    if _observability_instance is None:
        _observability_instance = CommunicationsObservability()

    return _observability_instance

def set_observability(observability: CommunicationsObservability):
    """Set global observability instance."""
    global _observability_instance
    _observability_instance = observability

# Decorators for automatic instrumentation
def instrument_async(operation_name: str, service: str = "communications"):
    """Decorator to instrument async functions."""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            obs = get_observability()
            async with obs.async_time_operation(operation_name, service):
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    obs.record_error(service, type(e).__name__, str(e))
                    raise

        return wrapper

    return decorator

def instrument_sync(operation_name: str, service: str = "communications"):
    """Decorator to instrument sync functions."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            obs = get_observability()
            with obs.time_operation(operation_name, service):
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    obs.record_error(service, type(e).__name__, str(e))
                    raise

        return wrapper

    return decorator

# Export public interface
__all__ = [
    "CommunicationsObservability",
    "MetricsCollector",
    "HealthMonitor",
    "HealthCheck",
    "get_observability",
    "set_observability",
    "instrument_async",
    "instrument_sync",
    "async_timer",
]

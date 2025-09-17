"""
Metrics collection for WebSocket gateway.
"""

import json

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Optional

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

@dataclass
class MetricValue:
    """A single metric value with timestamp."""

    value: float
    timestamp: float = field(default_factory=time.time)
    labels: dict[str, str] = field(default_factory=dict)

class Counter:
    """Thread-safe counter metric."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._values: dict[str, float] = defaultdict(float)
        self._lock = Lock()

    def increment(self, labels: Optional[dict[str, str]] = None, amount: float = 1.0):
        """Increment counter."""
        key = self._labels_to_key(labels or {})

        with self._lock:
            self._values[key] += amount

    def get_value(self, labels: Optional[dict[str, str]] = None) -> float:
        """Get counter value."""
        key = self._labels_to_key(labels or {})

        with self._lock:
            return self._values.get(key, 0.0)

    def get_all_values(self) -> dict[str, float]:
        """Get all counter values."""
        with self._lock:
            return dict(self._values)

    def reset(self, labels: Optional[dict[str, str]] = None):
        """Reset counter."""
        if labels:
            key = self._labels_to_key(labels)
            with self._lock:
                self._values.pop(key, None)
        else:
            with self._lock:
                self._values.clear()

    def _labels_to_key(self, labels: dict[str, str]) -> str:
        """Convert labels to string key."""
        if not labels:
            return ""
        return json.dumps(sorted(labels.items()))

class Gauge:
    """Thread-safe gauge metric."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._values: dict[str, float] = defaultdict(float)
        self._lock = Lock()

    def set_value(self, value: float, labels: Optional[dict[str, str]] = None):
        """Set gauge value."""
        key = self._labels_to_key(labels or {})

        with self._lock:
            self._values[key] = value

    def increment(self, labels: Optional[dict[str, str]] = None, amount: float = 1.0):
        """Increment gauge."""
        key = self._labels_to_key(labels or {})

        with self._lock:
            self._values[key] += amount

    def decrement(self, labels: Optional[dict[str, str]] = None, amount: float = 1.0):
        """Decrement gauge."""
        key = self._labels_to_key(labels or {})

        with self._lock:
            self._values[key] -= amount

    def get_value(self, labels: Optional[dict[str, str]] = None) -> float:
        """Get gauge value."""
        key = self._labels_to_key(labels or {})

        with self._lock:
            return self._values.get(key, 0.0)

    def get_all_values(self) -> dict[str, float]:
        """Get all gauge values."""
        with self._lock:
            return dict(self._values)

    def _labels_to_key(self, labels: dict[str, str]) -> str:
        """Convert labels to string key."""
        if not labels:
            return ""
        return json.dumps(sorted(labels.items()))

class Histogram:
    """Thread-safe histogram metric."""

    def __init__(self, name: str, description: str = "", buckets: Optional[list[float]] = None):
        self.name = name
        self.description = description
        self.buckets = buckets or [0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]

        self._counts: dict[str, dict[float, int]] = defaultdict(lambda: defaultdict(int))
        self._sums: dict[str, float] = defaultdict(float)
        self._total_counts: dict[str, int] = defaultdict(int)
        self._lock = Lock()

    def observe(self, value: float, labels: Optional[dict[str, str]] = None):
        """Record an observation."""
        key = self._labels_to_key(labels or {})

        with self._lock:
            self._sums[key] += value
            self._total_counts[key] += 1

            # Update bucket counts
            for bucket in self.buckets:
                if value <= bucket:
                    self._counts[key][bucket] += 1

    def get_bucket_counts(self, labels: Optional[dict[str, str]] = None) -> dict[float, int]:
        """Get histogram bucket counts."""
        key = self._labels_to_key(labels or {})

        with self._lock:
            return dict(self._counts[key])

    def get_sum(self, labels: Optional[dict[str, str]] = None) -> float:
        """Get sum of all observations."""
        key = self._labels_to_key(labels or {})

        with self._lock:
            return self._sums[key]

    def get_count(self, labels: Optional[dict[str, str]] = None) -> int:
        """Get total number of observations."""
        key = self._labels_to_key(labels or {})

        with self._lock:
            return self._total_counts[key]

    def get_average(self, labels: Optional[dict[str, str]] = None) -> float:
        """Get average of all observations."""
        key = self._labels_to_key(labels or {})

        with self._lock:
            total = self._total_counts[key]
            if total == 0:
                return 0.0
            return self._sums[key] / total

    def _labels_to_key(self, labels: dict[str, str]) -> str:
        """Convert labels to string key."""
        if not labels:
            return ""
        return json.dumps(sorted(labels.items()))

class WebSocketMetrics:
    """Metrics collection for WebSocket gateway."""

    def __init__(self, gateway):
        self.gateway = gateway

        # Connection metrics
        self.connections_total = Counter(
            "websocket_connections_total", "Total number of WebSocket connections"
        )

        self.connections_current = Gauge(
            "websocket_connections_current", "Current number of WebSocket connections"
        )

        self.connection_duration = Histogram(
            "websocket_connection_duration_seconds",
            "Duration of WebSocket connections",
            buckets=[0.1, 1, 10, 30, 60, 300, 600, 1800, 3600],
        )

        # Message metrics
        self.messages_received_total = Counter(
            "websocket_messages_received_total", "Total number of messages received"
        )

        self.messages_sent_total = Counter(
            "websocket_messages_sent_total", "Total number of messages sent"
        )

        self.message_size = Histogram(
            "websocket_message_size_bytes",
            "Size of WebSocket messages in bytes",
            buckets=[64, 256, 1024, 4096, 16384, 65536, 262144],
        )

        # Authentication metrics
        self.authentication_attempts_total = Counter(
            "websocket_authentication_attempts_total", "Total number of authentication attempts"
        )

        self.authentication_duration = Histogram(
            "websocket_authentication_duration_seconds", "Duration of authentication attempts"
        )

        # Channel metrics
        self.channel_subscriptions_total = Counter(
            "websocket_channel_subscriptions_total", "Total number of channel subscriptions"
        )

        self.channels_current = Gauge(
            "websocket_channels_current", "Current number of active channels"
        )

        self.channel_subscribers = Gauge(
            "websocket_channel_subscribers", "Number of subscribers per channel"
        )

        # Broadcast metrics
        self.broadcasts_total = Counter("websocket_broadcasts_total", "Total number of broadcasts")

        self.broadcast_duration = Histogram(
            "websocket_broadcast_duration_seconds", "Duration of broadcast operations"
        )

        # Error metrics
        self.errors_total = Counter("websocket_errors_total", "Total number of errors")

        # Rate limiting metrics
        self.rate_limit_hits_total = Counter(
            "websocket_rate_limit_hits_total", "Total number of rate limit hits"
        )

        # Resource metrics
        self.memory_usage = Gauge("websocket_memory_usage_bytes", "Memory usage in bytes")

        # Business metrics
        self.active_sessions_by_tenant = Gauge(
            "websocket_active_sessions_by_tenant", "Number of active sessions per tenant"
        )

        self.message_throughput = Gauge(
            "websocket_message_throughput_per_second", "Message throughput per second"
        )

        # Throughput tracking
        self._message_timestamps = deque(maxlen=1000)

    def record_connection(self, session):
        """Record a new connection."""
        labels = {
            "tenant_id": session.tenant_id or "default",
            "ip_address": session.metadata.ip_address or "unknown",
        }

        self.connections_total.increment(labels)
        self.connections_current.increment(labels)

        # Update tenant session count
        tenant_labels = {"tenant_id": session.tenant_id or "default"}
        self.active_sessions_by_tenant.increment(tenant_labels)

    def record_disconnection(self, session):
        """Record a disconnection."""
        labels = {"tenant_id": session.tenant_id or "default"}

        self.connections_current.decrement(labels)

        # Record connection duration
        duration = time.time() - session.metadata.connected_at
        self.connection_duration.observe(duration, labels)

        # Update tenant session count
        tenant_labels = {"tenant_id": session.tenant_id or "default"}
        self.active_sessions_by_tenant.decrement(tenant_labels)

    def record_authentication_attempt(self, session, auth_result, duration: float):
        """Record authentication attempt."""
        labels = {
            "success": str(auth_result.success).lower(),
            "method": auth_result.auth_method or "unknown",
            "tenant_id": session.tenant_id or "default",
        }

        self.authentication_attempts_total.increment(labels)
        self.authentication_duration.observe(duration, labels)

    def record_message_received(self, session, message_size: int):
        """Record a received message."""
        labels = {
            "tenant_id": session.tenant_id or "default",
            "authenticated": str(session.is_authenticated).lower(),
        }

        self.messages_received_total.increment(labels)
        self.message_size.observe(message_size, {**labels, "direction": "received"})

        # Update throughput tracking
        self._message_timestamps.append(time.time())
        self._update_throughput()

    def record_message_sent(self, session, message_type: str, message_size: int):
        """Record a sent message."""
        labels = {"message_type": message_type, "tenant_id": session.tenant_id or "default"}

        self.messages_sent_total.increment(labels)
        self.message_size.observe(message_size, {**labels, "direction": "sent"})

        # Update throughput tracking
        self._message_timestamps.append(time.time())
        self._update_throughput()

    def record_channel_subscription(self, session, channel_name: str):
        """Record channel subscription."""
        labels = {"channel": channel_name, "tenant_id": session.tenant_id or "default"}

        self.channel_subscriptions_total.increment(labels)

    def record_broadcast(
        self, channel_name: str, message_type: str, subscriber_count: int, duration: float
    ):
        """Record broadcast operation."""
        labels = {"channel": channel_name, "message_type": message_type}

        self.broadcasts_total.increment(labels)
        self.broadcast_duration.observe(duration, labels)

    def record_error(self, session, error: Exception, error_type: str):
        """Record an error."""
        labels = {
            "error_type": error_type,
            "tenant_id": session.tenant_id if session else "unknown",
        }

        self.errors_total.increment(labels)

    def record_rate_limit_hit(self, session, limit_type: str):
        """Record rate limit hit."""
        labels = {
            "limit_type": limit_type,
            "tenant_id": session.tenant_id if session else "unknown",
        }

        self.rate_limit_hits_total.increment(labels)

    def update_channel_metrics(self, channel_stats: dict[str, Any]):
        """Update channel-related metrics."""
        total_channels = channel_stats.get("total_channels", 0)
        self.channels_current.set_value(total_channels)

        # Update per-channel subscriber counts
        channels = channel_stats.get("channels", {})
        for channel_name, info in channels.items():
            subscriber_count = info.get("subscribers", 0)
            labels = {"channel": channel_name}
            self.channel_subscribers.set_value(subscriber_count, labels)

    def update_memory_usage(self, memory_bytes: int):
        """Update memory usage metric."""
        self.memory_usage.set_value(memory_bytes)

    def _update_throughput(self):
        """Update message throughput calculation."""
        current_time = time.time()

        # Count messages in last second
        one_second_ago = current_time - 1.0
        recent_messages = sum(1 for ts in self._message_timestamps if ts >= one_second_ago)

        self.message_throughput.set_value(recent_messages)

    def get_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format."""
        metrics = []

        # Helper function to format metric
        def format_metric(
            metric_name: str, metric_type: str, description: str, values: dict[str, float]
        ):
            lines = []
            lines.append(f"# HELP {metric_name} {description}")
            lines.append(f"# TYPE {metric_name} {metric_type}")

            for labels_key, value in values.items():
                if labels_key:
                    # Parse labels back from JSON
                    labels = json.loads(labels_key) if labels_key else []
                    labels_str = ",".join(f'{k}="{v}"' for k, v in labels)
                    lines.append(f"{metric_name}{{{labels_str}}} {value}")
                else:
                    lines.append(f"{metric_name} {value}")

            return "\n".join(lines)

        # Export counters
        for counter in [
            self.connections_total,
            self.messages_received_total,
            self.messages_sent_total,
            self.authentication_attempts_total,
            self.channel_subscriptions_total,
            self.broadcasts_total,
            self.errors_total,
            self.rate_limit_hits_total,
        ]:
            metrics.append(
                format_metric(
                    counter.name, "counter", counter.description, counter.get_all_values()
                )
            )

        # Export gauges
        for gauge in [
            self.connections_current,
            self.channels_current,
            self.channel_subscribers,
            self.memory_usage,
            self.active_sessions_by_tenant,
            self.message_throughput,
        ]:
            metrics.append(
                format_metric(gauge.name, "gauge", gauge.description, gauge.get_all_values())
            )

        # Export histograms (simplified - just count and sum)
        for histogram in [
            self.connection_duration,
            self.message_size,
            self.authentication_duration,
            self.broadcast_duration,
        ]:
            # Total count
            count_values = {
                labels: histogram.get_count(json.loads(labels) if labels else None)
                for labels in histogram._total_counts.keys()
            }
            metrics.append(
                format_metric(
                    f"{histogram.name}_count",
                    "counter",
                    f"{histogram.description} (count)",
                    count_values,
                )
            )

            # Total sum
            sum_values = {
                labels: histogram.get_sum(json.loads(labels) if labels else None)
                for labels in histogram._sums.keys()
            }
            metrics.append(
                format_metric(
                    f"{histogram.name}_sum", "counter", f"{histogram.description} (sum)", sum_values
                )
            )

        return "\n\n".join(metrics) + "\n"

    def get_all_metrics(self) -> dict[str, Any]:
        """Get all metrics as a dictionary."""
        return {
            "counters": {
                "connections_total": self.connections_total.get_all_values(),
                "messages_received_total": self.messages_received_total.get_all_values(),
                "messages_sent_total": self.messages_sent_total.get_all_values(),
                "authentication_attempts_total": self.authentication_attempts_total.get_all_values(),
                "channel_subscriptions_total": self.channel_subscriptions_total.get_all_values(),
                "broadcasts_total": self.broadcasts_total.get_all_values(),
                "errors_total": self.errors_total.get_all_values(),
                "rate_limit_hits_total": self.rate_limit_hits_total.get_all_values(),
            },
            "gauges": {
                "connections_current": self.connections_current.get_all_values(),
                "channels_current": self.channels_current.get_all_values(),
                "channel_subscribers": self.channel_subscribers.get_all_values(),
                "memory_usage": self.memory_usage.get_all_values(),
                "active_sessions_by_tenant": self.active_sessions_by_tenant.get_all_values(),
                "message_throughput": self.message_throughput.get_all_values(),
            },
            "histograms": {
                "connection_duration": {
                    "counts": {
                        labels: self.connection_duration.get_count(
                            json.loads(labels) if labels else None
                        )
                        for labels in self.connection_duration._total_counts.keys()
                    },
                    "sums": {
                        labels: self.connection_duration.get_sum(
                            json.loads(labels) if labels else None
                        )
                        for labels in self.connection_duration._sums.keys()
                    },
                    "averages": {
                        labels: self.connection_duration.get_average(
                            json.loads(labels) if labels else None
                        )
                        for labels in self.connection_duration._total_counts.keys()
                    },
                },
                "message_size": {
                    "counts": {
                        labels: self.message_size.get_count(json.loads(labels) if labels else None)
                        for labels in self.message_size._total_counts.keys()
                    },
                    "averages": {
                        labels: self.message_size.get_average(
                            json.loads(labels) if labels else None
                        )
                        for labels in self.message_size._total_counts.keys()
                    },
                },
            },
        }

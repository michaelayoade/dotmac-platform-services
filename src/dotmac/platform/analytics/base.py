"""
Base classes for unified analytics with OpenTelemetry support.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol
from uuid import UUID, uuid4


class MetricType(str, Enum):
    """Types of metrics supported."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    UPDOWN_COUNTER = "updown_counter"
    EXPONENTIAL_HISTOGRAM = "exponential_histogram"


@dataclass
class SpanContext:
    """OpenTelemetry span context for distributed tracing."""

    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    trace_flags: int = 0
    trace_state: Optional[Dict[str, str]] = None


@dataclass
class Metric:
    """Base metric class for all analytics data."""

    id: UUID = field(default_factory=uuid4)
    tenant_id: str = field(default="")
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    name: str = field(default="")
    type: MetricType = field(default=MetricType.GAUGE)
    value: Any = field(default=0)
    unit: Optional[str] = None
    description: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    resource_attributes: Dict[str, Any] = field(default_factory=dict)
    span_context: Optional[SpanContext] = None

    def to_otel_attributes(self) -> Dict[str, Any]:
        """Convert to OpenTelemetry attributes format."""
        attrs = {
            "tenant.id": self.tenant_id,
            "metric.id": str(self.id),
        }

        # Add custom attributes
        for key, value in self.attributes.items():
            # OpenTelemetry attribute naming convention
            otel_key = key.replace("_", ".").lower()
            if isinstance(value, (str, int, float, bool)):
                attrs[otel_key] = value
            else:
                attrs[otel_key] = str(value)

        return attrs


@dataclass
class CounterMetric(Metric):
    """Counter metric for monotonically increasing values."""

    type: MetricType = field(default=MetricType.COUNTER, init=False)
    delta: float = 1.0

    def __post_init__(self):
        """Ensure positive delta for counter."""
        if self.delta < 0:
            raise ValueError("Counter delta must be non-negative")


@dataclass
class GaugeMetric(Metric):
    """Gauge metric for point-in-time measurements."""

    type: MetricType = field(default=MetricType.GAUGE, init=False)


@dataclass
class HistogramMetric(Metric):
    """Histogram metric for value distributions."""

    type: MetricType = field(default=MetricType.HISTOGRAM, init=False)
    bucket_boundaries: List[float] = field(
        default_factory=lambda: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
    )

    def record_value(self, value: float):
        """Record a value in the histogram."""
        self.value = value


class AnalyticsCollector(Protocol):
    """Protocol for analytics collectors."""

    async def collect(self, metric: Metric) -> None:
        """Collect a single metric."""
        ...

    async def collect_batch(self, metrics: List[Metric]) -> None:
        """Collect multiple metrics in batch."""
        ...

    async def flush(self) -> None:
        """Flush any pending metrics."""
        ...

    async def close(self) -> None:
        """Close the collector and release resources."""
        ...


class BaseAnalyticsCollector(ABC):
    """Abstract base class for analytics collectors."""

    def __init__(self, tenant_id: str, service_name: str):
        """
        Initialize the collector.

        Args:
            tenant_id: Tenant identifier
            service_name: Name of the service generating metrics
        """
        self.tenant_id = tenant_id
        self.service_name = service_name
        self.pending_metrics: List[Metric] = []
        self.batch_size = 100

    @abstractmethod
    async def collect(self, metric: Metric) -> None:
        """Collect a single metric."""
        pass

    @abstractmethod
    async def collect_batch(self, metrics: List[Metric]) -> None:
        """Collect multiple metrics in batch."""
        pass

    async def flush(self) -> None:
        """Flush pending metrics."""
        if self.pending_metrics:
            await self.collect_batch(self.pending_metrics)
            self.pending_metrics.clear()

    async def close(self) -> None:
        """Close the collector."""
        await self.flush()

    def _enrich_metric(self, metric: Metric) -> Metric:
        """
        Enrich metric with collector context.

        Args:
            metric: Metric to enrich

        Returns:
            Enriched metric
        """
        # Add tenant if not set
        if not metric.tenant_id:
            metric.tenant_id = self.tenant_id

        # Add service name to resource attributes
        metric.resource_attributes["service.name"] = self.service_name
        metric.resource_attributes["tenant.id"] = self.tenant_id

        return metric


class MetricRegistry:
    """Registry for metric definitions and metadata."""

    def __init__(self):
        """Initialize the registry."""
        self._metrics: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: str,
        type: MetricType,
        unit: Optional[str] = None,
        description: Optional[str] = None,
        attributes: Optional[List[str]] = None,
    ) -> None:
        """
        Register a metric definition.

        Args:
            name: Metric name
            type: Metric type
            unit: Unit of measurement
            description: Metric description
            attributes: Expected attributes
        """
        self._metrics[name] = {
            "type": type,
            "unit": unit,
            "description": description,
            "attributes": attributes or [],
        }

    def get(self, name: str) -> Optional[Dict[str, Any]]:
        """Get metric definition."""
        return self._metrics.get(name)

    def validate(self, metric: Metric) -> bool:
        """
        Validate a metric against its definition.

        Args:
            metric: Metric to validate

        Returns:
            True if valid, False otherwise
        """
        definition = self.get(metric.name)
        if not definition:
            return True  # Allow unregistered metrics

        # Validate type
        if metric.type != definition["type"]:
            return False

        # Validate required attributes
        required_attrs = set(definition["attributes"])
        actual_attrs = set(metric.attributes.keys())

        return required_attrs.issubset(actual_attrs)

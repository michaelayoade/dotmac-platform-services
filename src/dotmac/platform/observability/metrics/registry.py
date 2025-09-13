"""
Metrics registry abstraction over OpenTelemetry (SigNoz-compatible).
"""

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from opentelemetry import metrics as otel_metrics
    from opentelemetry.sdk.metrics import Meter

# Runtime availability check
_otel_available = False
try:
    from opentelemetry import metrics as otel_metrics
    from opentelemetry.sdk.metrics import Meter

    _otel_available = True
except ImportError:
    Meter = Any  # type: ignore[misc,assignment]
    otel_metrics = Any  # type: ignore[misc,assignment]

CollectorRegistry = Any  # legacy collector type placeholder

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Supported metric types."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    UP_DOWN_COUNTER = "up_down_counter"
    SUMMARY = "summary"


@dataclass
class MetricDefinition:
    """Definition of a metric for registration."""

    name: str
    type: MetricType | str
    description: str
    labels: list[str] | None = None
    buckets: Sequence[float] | None = None
    unit: str | None = None

    def __post_init__(self) -> None:
        """Validate metric definition."""
        if (self.type == MetricType.HISTOGRAM or self.type == "histogram") and self.buckets is None:
            # Default histogram buckets
            self.buckets = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

        # Ensure labels is not None
        if self.labels is None:
            self.labels = []


@dataclass
class MetricInstrument:
    """Wrapper around metric instruments from different backends."""

    definition: MetricDefinition
    otel_instrument: Any | None = None

    def record(self, value: int | float, labels: dict[str, str] | None = None) -> None:
        """Record a value for this metric."""
        labels = labels or {}

        try:
            # Record to OpenTelemetry
            if self.otel_instrument:
                if self.definition.type in (MetricType.COUNTER, MetricType.UP_DOWN_COUNTER):
                    self.otel_instrument.add(value, labels)
                elif self.definition.type == MetricType.GAUGE:
                    self.otel_instrument.set(value, labels)
                elif self.definition.type == MetricType.HISTOGRAM:
                    self.otel_instrument.record(value, labels)

            # legacy backend support removed

        except Exception as e:
            logger.error(f"Failed to record metric {self.definition.name}: {e}")


class MetricsRegistry:
    """Unified metrics registry using OpenTelemetry instruments."""

    def __init__(
        self,
        service_name: str,
        enable_prometheus: bool = False,
        prometheus_registry: Optional["CollectorRegistry"] = None,
    ) -> None:
        self.service_name = service_name
        self.enable_prometheus = False
        self._metrics: dict[str, MetricInstrument] = {}
        self._otel_meter: Meter | None = None

        # Prometheus registry removed
        self._prometheus_registry = None

        logger.info(f"Metrics registry initialized for {service_name}")

    def set_otel_meter(self, meter: Meter | None) -> None:
        """Set the OpenTelemetry meter for this registry."""
        self._otel_meter = meter

        # Re-register all metrics with the new meter
        if meter and _otel_available:
            for metric_name, metric_instrument in self._metrics.items():
                try:
                    otel_instrument = self._create_otel_instrument(
                        metric_instrument.definition, meter
                    )
                    metric_instrument.otel_instrument = otel_instrument
                except Exception as e:
                    logger.error(f"Failed to re-register OTEL metric {metric_name}: {e}")

    def register_metric(self, definition: MetricDefinition) -> bool:
        """
        Register a metric with the registry.

        Args:
            definition: Metric definition

        Returns:
            True if successful, False otherwise
        """
        if definition.name in self._metrics:
            logger.warning(f"Metric {definition.name} already registered")
            return False

        try:
            # Create OpenTelemetry instrument
            otel_instrument = None
            if self._otel_meter and _otel_available:
                otel_instrument = self._create_otel_instrument(definition, self._otel_meter)

            # Create wrapper
            instrument = MetricInstrument(
                definition=definition,
                otel_instrument=otel_instrument,
            )

            self._metrics[definition.name] = instrument
            logger.debug(f"Registered metric: {definition.name} ({definition.type})")
            return True

        except Exception as e:
            logger.error(f"Failed to register metric {definition.name}: {e}")
            return False

    def get_metric(self, name: str) -> MetricInstrument | None:
        """Get a registered metric by name."""
        return self._metrics.get(name)

    # Compatibility wrappers expected by tests
    def register(self, *args, **kwargs) -> bool:  # flexible signature
        if args and isinstance(args[0], MetricDefinition):
            definition = args[0]
            return self.register_metric(definition)
        if "definition" in kwargs and isinstance(kwargs["definition"], MetricDefinition):
            definition = kwargs["definition"]
            # Optional name kw
            if "name" in kwargs and kwargs["name"]:
                definition.name = kwargs["name"]
            return self.register_metric(definition)
        # Legacy signature: (name, definition)
        if len(args) == 2 and isinstance(args[1], MetricDefinition):
            definition = args[1]
            definition.name = args[0]
            return self.register_metric(definition)
        raise TypeError("register() expects a MetricDefinition")

    def get(self, name: str) -> MetricDefinition | None:
        inst = self.get_metric(name)
        return inst.definition if inst else None

    def record_metric(
        self,
        name: str,
        value: int | float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """
        Record a value for a metric.

        Args:
            name: Metric name
            value: Value to record
            labels: Optional labels
        """
        metric = self.get_metric(name)
        if metric:
            metric.record(value, labels)
        else:
            logger.warning(f"Metric {name} not found in registry")

    def increment_counter(
        self,
        name: str,
        value: int | float = 1,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Increment a counter metric."""
        self.record_metric(name, value, labels)

    def set_gauge(
        self,
        name: str,
        value: int | float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Set a gauge metric value."""
        self.record_metric(name, value, labels)

    def observe_histogram(
        self,
        name: str,
        value: int | float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Observe a histogram metric."""
        self.record_metric(name, value, labels)

    # Prometheus exposition helpers removed

    def list_metrics(self) -> list[str]:
        """List all registered metric names."""
        return list(self._metrics.keys())

    def get_metrics_info(self) -> dict[str, dict[str, Any]]:
        """Get information about all registered metrics."""
        return {
            name: {
                "type": instrument.definition.type.value,
                "description": instrument.definition.description,
                "labels": instrument.definition.labels,
                "unit": instrument.definition.unit,
            }
            for name, instrument in self._metrics.items()
        }

    def _create_otel_instrument(self, definition: MetricDefinition, meter: Meter) -> Any:
        """Create OpenTelemetry instrument."""
        kwargs = {
            "name": definition.name,
            "description": definition.description,
        }
        if definition.unit:
            kwargs["unit"] = definition.unit

        if definition.type == MetricType.COUNTER:
            return meter.create_counter(**kwargs)
        if definition.type == MetricType.UP_DOWN_COUNTER:
            return meter.create_up_down_counter(**kwargs)
        if definition.type == MetricType.GAUGE:
            return meter.create_gauge(**kwargs)
        if definition.type == MetricType.HISTOGRAM:
            return meter.create_histogram(**kwargs)
        raise ValueError(f"Unsupported OTEL metric type: {definition.type}")

    # Prometheus instrument creation removed


def initialize_metrics_registry(
    service_name: str,
) -> MetricsRegistry:
    """
    Initialize a metrics registry.

    Args:
        service_name: Name of the service

    Returns:
        Configured MetricsRegistry
    """
    registry = MetricsRegistry(
        service_name=service_name,
    )

    # Register default system metrics
    _register_default_metrics(registry)

    return registry


def _register_default_metrics(registry: MetricsRegistry) -> None:
    """Register default system metrics."""
    default_metrics = [
        MetricDefinition(
            name="http_requests_total",
            type=MetricType.COUNTER,
            description="Total HTTP requests",
            labels=["method", "endpoint", "status_code"],
        ),
        MetricDefinition(
            name="http_request_duration_seconds",
            type=MetricType.HISTOGRAM,
            description="HTTP request duration in seconds",
            labels=["method", "endpoint"],
            unit="s",
        ),
        MetricDefinition(
            name="system_memory_usage_bytes",
            type=MetricType.GAUGE,
            description="Current memory usage in bytes",
            unit="byte",
        ),
        MetricDefinition(
            name="system_cpu_usage_percent",
            type=MetricType.GAUGE,
            description="Current CPU usage percentage",
            unit="percent",
        ),
        MetricDefinition(
            name="database_connections_active",
            type=MetricType.GAUGE,
            description="Active database connections",
        ),
        MetricDefinition(
            name="database_query_duration_seconds",
            type=MetricType.HISTOGRAM,
            description="Database query duration in seconds",
            labels=["operation", "table"],
            unit="s",
        ),
    ]

    for metric_def in default_metrics:
        registry.register_metric(metric_def)

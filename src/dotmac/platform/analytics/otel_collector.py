"""
OpenTelemetry collector implementation for SigNoz integration.
"""


from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from opentelemetry import metrics, trace
from opentelemetry.trace import Tracer
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.metrics import CallbackOptions, Observation
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode

from .base import (
    BaseAnalyticsCollector,
    CounterMetric,
    GaugeMetric,
    HistogramMetric,
    Metric,
)
from dotmac.platform.observability.unified_logging import get_logger

logger = get_logger(__name__)

@dataclass
class OTelConfig:
    """OpenTelemetry configuration for SigNoz."""

    endpoint: str = "localhost:4317"
    service_name: str = "dotmac-business-services"
    environment: str = "development"
    insecure: bool = True
    headers: Optional[Dict[str, str]] = None
    export_interval_millis: int = 5000
    max_export_batch_size: int = 512
    max_queue_size: int = 2048

class OpenTelemetryCollector(BaseAnalyticsCollector):
    """
    OpenTelemetry collector for sending metrics and traces to SigNoz.
    """

    def __init__(
        self,
        tenant_id: str,
        service_name: str,
        config: OTelConfig,
    ):
        """
        Initialize OpenTelemetry collector.

        Args:
            tenant_id: Tenant identifier
            service_name: Service name for identification
            config: OpenTelemetry configuration
        """
        super().__init__(tenant_id, service_name)
        self.config = config

        # Initialize resource attributes
        resource = Resource.create(
            {
                "service.name": service_name,
                "service.namespace": "dotmac",
                "service.version": "1.0.0",
                "deployment.environment": config.environment,
                "tenant.id": tenant_id,
            }
        )

        # Initialize metrics
        self._init_metrics(resource)

        # Initialize tracing
        self._init_tracing(resource)

        # Metric instruments cache
        self._counters: Dict[str, Any] = {}
        self._gauges: Dict[str, Any] = {}
        self._histograms: Dict[str, Any] = {}
        self._updown_counters: Dict[str, Any] = {}

    def _init_metrics(self, resource: Resource) -> None:
        """Initialize OpenTelemetry metrics."""
        # Create OTLP metric exporter for SigNoz
        metric_exporter = OTLPMetricExporter(
            endpoint=self.config.endpoint,
            insecure=self.config.insecure,
            headers=self.config.headers,
        )

        # Create metric reader
        metric_reader = PeriodicExportingMetricReader(
            exporter=metric_exporter,
            export_interval_millis=self.config.export_interval_millis,
        )

        # Set up meter provider
        provider = MeterProvider(
            resource=resource,
            metric_readers=[metric_reader],
        )
        metrics.set_meter_provider(provider)

        # Get meter for this service
        self.meter = metrics.get_meter(
            name=self.service_name,
            version="1.0.0",
        )

    def _init_tracing(self, resource: Resource) -> None:
        """Initialize OpenTelemetry tracing."""
        # Create OTLP span exporter for SigNoz
        span_exporter = OTLPSpanExporter(
            endpoint=self.config.endpoint,
            insecure=self.config.insecure,
            headers=self.config.headers,
        )

        # Create tracer provider
        provider = TracerProvider(resource=resource)

        # Add span processor
        span_processor = BatchSpanProcessor(
            span_exporter,
            max_queue_size=self.config.max_queue_size,
            max_export_batch_size=self.config.max_export_batch_size,
        )
        provider.add_span_processor(span_processor)

        # Set global tracer provider
        trace.set_tracer_provider(provider)

        # Get tracer for this service
        self.tracer: Tracer = trace.get_tracer(
            instrumenting_module_name=self.service_name,
            instrumenting_library_version="1.0.0",
        )

    def _get_or_create_counter(self, metric: CounterMetric) -> Any:
        """Get or create a counter instrument."""
        if metric.name not in self._counters:
            self._counters[metric.name] = self.meter.create_counter(
                name=metric.name,
                unit=metric.unit or "1",
                description=metric.description or f"Counter for {metric.name}",
            )
        return self._counters[metric.name]

    def _get_or_create_gauge(self, metric: GaugeMetric) -> Any:
        """Get or create a gauge instrument."""
        if metric.name not in self._gauges:
            # Store gauge values for async callback
            if metric.name not in self._gauge_values:
                self._gauge_values = {}
            self._gauge_values[metric.name] = {}

            def gauge_callback(options: CallbackOptions) -> List[Observation]:
                """Callback for observable gauge."""
                observations = []
                for attrs_key, value in self._gauge_values.get(metric.name, {}).items():
                    observations.append(Observation(value=value, attributes=dict(attrs_key)))
                return observations

            self._gauges[metric.name] = self.meter.create_observable_gauge(
                name=metric.name,
                callbacks=[gauge_callback],
                unit=metric.unit or "1",
                description=metric.description or f"Gauge for {metric.name}",
            )
        return self._gauges[metric.name]

    def _get_or_create_histogram(self, metric: HistogramMetric) -> Any:
        """Get or create a histogram instrument."""
        if metric.name not in self._histograms:
            self._histograms[metric.name] = self.meter.create_histogram(
                name=metric.name,
                unit=metric.unit or "1",
                description=metric.description or f"Histogram for {metric.name}",
            )
        return self._histograms[metric.name]

    async def collect(self, metric: Metric) -> None:
        """
        Collect a single metric and send to SigNoz.

        Args:
            metric: Metric to collect
        """
        # Enrich metric with context
        metric = self._enrich_metric(metric)

        # Convert to OpenTelemetry attributes
        attributes = metric.to_otel_attributes()

        try:
            if isinstance(metric, CounterMetric):
                counter = self._get_or_create_counter(metric)
                counter.add(metric.delta, attributes)

            elif isinstance(metric, GaugeMetric):
                # Store value for async callback
                attrs_key = tuple(sorted(attributes.items()))
                if metric.name not in self._gauge_values:
                    self._gauge_values = {}
                self._gauge_values[metric.name][attrs_key] = metric.value

            elif isinstance(metric, HistogramMetric):
                histogram = self._get_or_create_histogram(metric)
                histogram.record(metric.value, attributes)

            else:
                logger.warning(f"Unsupported metric type: {metric.type}")

        except Exception as e:
            logger.error(f"Failed to collect metric {metric.name}: {e}")

    async def collect_batch(self, metrics: List[Metric]) -> None:
        """
        Collect multiple metrics in batch.

        Args:
            metrics: List of metrics to collect
        """
        for metric in metrics:
            await self.collect(metric)

    def create_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        kind: trace.SpanKind = trace.SpanKind.INTERNAL,
    ) -> trace.Span:
        """
        Create a new span for distributed tracing.

        Args:
            name: Span name
            attributes: Span attributes
            kind: Span kind

        Returns:
            OpenTelemetry span
        """
        span = self.tracer.start_span(
            name=name,
            attributes=attributes or {},
            kind=kind,
        )
        return span

    def record_exception(self, span: trace.Span, exception: Exception) -> None:
        """
        Record an exception in a span.

        Args:
            span: Current span
            exception: Exception to record
        """
        span.record_exception(exception)
        span.set_status(Status(StatusCode.ERROR, str(exception)))

    async def close(self) -> None:
        """Close the collector and flush pending data."""
        await self.flush()

        # Shutdown providers
        if hasattr(self, "meter"):
            metrics.get_meter_provider().shutdown()

        if hasattr(self, "tracer"):
            trace.get_tracer_provider().shutdown()

def create_otel_collector(
    tenant_id: str,
    service_name: str = "dotmac-business",
    endpoint: Optional[str] = None,
    environment: Optional[str] = None,
) -> OpenTelemetryCollector:
    """
    Create an OpenTelemetry collector with default configuration.

    Args:
        tenant_id: Tenant identifier
        service_name: Service name
        endpoint: SigNoz endpoint (default: localhost:4317)
        environment: Environment name (default: development)

    Returns:
        Configured OpenTelemetryCollector
    """
    config = OTelConfig(
        endpoint=endpoint or "localhost:4317",
        service_name=service_name,
        environment=environment or "development",
    )

    return OpenTelemetryCollector(
        tenant_id=tenant_id,
        service_name=service_name,
        config=config,
    )

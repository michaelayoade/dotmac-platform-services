"""
OpenTelemetry bootstrap and initialization.
"""

import logging
import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from .config import ExporterConfig, ExporterType, OTelConfig

if TYPE_CHECKING:
    from opentelemetry import metrics, trace
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
        OTLPMetricExporter as GRPCMetricsExporter,
    )
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
        OTLPSpanExporter as GRPCTraceExporter,
    )
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
        OTLPMetricExporter as HTTPMetricsExporter,
    )
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
        OTLPSpanExporter as HTTPTraceExporter,
    )
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import (
        ConsoleMetricExporter,
        PeriodicExportingMetricReader,
    )
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
        SpanExporter,
    )
    from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

# Runtime availability check
_otel_available = False
# Public alias for tests to monkeypatch
OTEL_AVAILABLE = False
try:
    from opentelemetry import metrics, trace
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
        OTLPMetricExporter as GRPCMetricsExporter,
    )
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
        OTLPSpanExporter as GRPCTraceExporter,
    )
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
        OTLPMetricExporter as HTTPMetricsExporter,
    )
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
        OTLPSpanExporter as HTTPTraceExporter,
    )
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import (
        ConsoleMetricExporter,
        PeriodicExportingMetricReader,
    )
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
        SpanExporter,
    )
    from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

    _otel_available = True
    OTEL_AVAILABLE = True
except ImportError:
    # Type stubs for when OTEL is not available
    TracerProvider = Any  # type: ignore[misc,assignment]
    MeterProvider = Any  # type: ignore[misc,assignment]
    trace = Any  # type: ignore[misc,assignment]
    metrics = Any  # type: ignore[misc,assignment]

logger = logging.getLogger(__name__)


@dataclass
class OTelBootstrap:
    """OpenTelemetry bootstrap result containing initialized providers and utilities."""

    tracer_provider: Optional[Any]  # TracerProvider when available
    meter_provider: Optional[Any]  # MeterProvider when available
    tracer: Any | None
    meter: Any | None
    exporters: dict[str, list[Any]]
    config: OTelConfig

    @property
    def is_initialized(self) -> bool:
        """Check if OpenTelemetry was successfully initialized."""
        return self.tracer_provider is not None and self.meter_provider is not None


def initialize_otel(config: OTelConfig) -> OTelBootstrap:
    """
    Initialize OpenTelemetry with the provided configuration.

    Args:
        config: OpenTelemetry configuration

    Returns:
        OTelBootstrap with initialized providers and utilities

    Raises:
        RuntimeError: If OTEL extras are not installed and initialization is attempted
    """
    # Honor explicit override from tests via OTEL_AVAILABLE
    if not OTEL_AVAILABLE:
        if config.enable_tracing or config.enable_metrics:
            warnings.warn(
                "OpenTelemetry extras not installed. Install with: pip install 'dotmac-observability[otel]'",
                UserWarning,
                stacklevel=2,
            )

        return OTelBootstrap(
            tracer_provider=None,
            meter_provider=None,
            tracer=None,
            meter=None,
            exporters={},
            config=config,
        )

    logger.info(f"Initializing OpenTelemetry for service: {config.service_name}")

    exporters: dict[str, list[Any]] = {
        "tracing": [],
        "metrics": [],
    }

    # Initialize tracing
    tracer_provider = None
    tracer = None
    if config.enable_tracing and config.tracing_exporters:
        tracer_provider, tracing_exporters = _initialize_tracing(config)
        tracer = trace.get_tracer(config.service_name, config.service_version)
        exporters["tracing"] = tracing_exporters

    # Initialize metrics
    meter_provider = None
    meter = None
    if config.enable_metrics and config.metrics_exporters:
        meter_provider, metrics_exporters = _initialize_metrics(config)
        meter = metrics.get_meter(config.service_name, config.service_version)
        exporters["metrics"] = metrics_exporters

    bootstrap = OTelBootstrap(
        tracer_provider=tracer_provider,
        meter_provider=meter_provider,
        tracer=tracer,
        meter=meter,
        exporters=exporters,
        config=config,
    )

    logger.info(f"OpenTelemetry initialized successfully for {config.service_name}")
    return bootstrap


def _initialize_tracing(config: OTelConfig) -> tuple["TracerProvider", list[Any]]:
    """Initialize tracing with configured exporters."""
    if not _otel_available:
        raise RuntimeError("OpenTelemetry not available")

    # Create resource
    resource = config.get_resource()

    # Create sampler
    sampler = TraceIdRatioBased(config.trace_sampler_ratio)

    # Create tracer provider
    tracer_provider = TracerProvider(resource=resource, sampler=sampler)

    # Add span processors with exporters
    exporters = []
    for exporter_config in config.tracing_exporters:
        try:
            exporter = _create_trace_exporter(exporter_config)
            processor = BatchSpanProcessor(
                exporter,
                max_export_batch_size=config.max_export_batch_size,
                max_queue_size=config.max_queue_size,
                export_timeout_millis=config.export_timeout,
            )
            tracer_provider.add_span_processor(processor)
            exporters.append(exporter)
            logger.debug(f"Added trace exporter: {exporter_config.type}")
        except Exception as e:
            logger.error(f"Failed to create trace exporter {exporter_config.type}: {e}")

    # Set as global tracer provider
    trace.set_tracer_provider(tracer_provider)

    return tracer_provider, exporters


def _initialize_metrics(config: OTelConfig) -> tuple["MeterProvider", list[Any]]:
    """Initialize metrics with configured exporters."""
    if not _otel_available:
        raise RuntimeError("OpenTelemetry not available")

    # Create resource
    resource = config.get_resource()

    # Create metric readers
    readers = []
    exporters = []

    for exporter_config in config.metrics_exporters:
        try:
            exporter = _create_metric_exporter(exporter_config)
            reader = PeriodicExportingMetricReader(
                exporter,
                export_interval_millis=30000,  # 30 seconds
            )
            readers.append(reader)
            exporters.append(exporter)
            logger.debug(f"Added metric exporter: {exporter_config.type}")
        except Exception as e:
            logger.error(f"Failed to create metric exporter {exporter_config.type}: {e}")

    # Create meter provider
    meter_provider = MeterProvider(resource=resource, metric_readers=readers)

    # Set as global meter provider
    metrics.set_meter_provider(meter_provider)

    return meter_provider, exporters


def _create_trace_exporter(config: ExporterConfig) -> "SpanExporter":
    """Create a trace exporter from configuration."""
    if not _otel_available:
        raise RuntimeError("OpenTelemetry not available")

    if config.type == ExporterType.CONSOLE:
        return ConsoleSpanExporter()

    if config.type == ExporterType.OTLP_HTTP:
        return HTTPTraceExporter(
            endpoint=config.endpoint,
            headers=config.headers,
            timeout=config.timeout,
            compression=config.compression,
        )

    if config.type == ExporterType.OTLP_GRPC:
        return GRPCTraceExporter(
            endpoint=config.endpoint,
            headers=config.headers,
            timeout=config.timeout,
            compression=config.compression,
        )

    raise ValueError(f"Unsupported trace exporter type: {config.type}")


def _create_metric_exporter(config: ExporterConfig) -> Any:
    """Create a metric exporter from configuration."""
    if not _otel_available:
        raise RuntimeError("OpenTelemetry not available")

    if config.type == ExporterType.CONSOLE:
        return ConsoleMetricExporter()

    if config.type == ExporterType.OTLP_HTTP:
        return HTTPMetricsExporter(
            endpoint=config.endpoint,
            headers=config.headers,
            timeout=config.timeout,
            compression=config.compression,
        )

    if config.type == ExporterType.OTLP_GRPC:
        return GRPCMetricsExporter(
            endpoint=config.endpoint,
            headers=config.headers,
            timeout=config.timeout,
            compression=config.compression,
        )

    raise ValueError(f"Unsupported metric exporter type: {config.type}")


def shutdown_otel(bootstrap: OTelBootstrap) -> None:
    """
    Shutdown OpenTelemetry providers and flush remaining data.

    Args:
        bootstrap: The bootstrap object to shutdown
    """
    if not _otel_available or not bootstrap.is_initialized:
        return

    logger.info("Shutting down OpenTelemetry")

    # Shutdown tracer provider
    if bootstrap.tracer_provider:
        try:
            bootstrap.tracer_provider.shutdown()
        except Exception as e:
            logger.error(f"Error shutting down tracer provider: {e}")

    # Shutdown meter provider
    if bootstrap.meter_provider:
        try:
            bootstrap.meter_provider.shutdown()
        except Exception as e:
            logger.error(f"Error shutting down meter provider: {e}")


def get_current_span_context() -> dict[str, str] | None:
    """
    Get current span context for correlation.

    Returns:
        Dictionary with trace_id and span_id if available
    """
    if not OTEL_AVAILABLE:
        return None

    try:
        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            span_context = current_span.get_span_context()
            return {
                "trace_id": format(span_context.trace_id, "032x"),
                "span_id": format(span_context.span_id, "016x"),
                "trace_flags": format(span_context.trace_flags, "02x"),
            }
    except Exception as e:
        logger.debug(f"Failed to get span context: {e}")

    return None


def create_child_span(name: str, attributes: dict[str, Any] | None = None) -> Any:
    """
    Create a child span with the given name and attributes.

    Args:
        name: Span name
        attributes: Span attributes

    Returns:
        Span object or None if tracing not available
    """
    if not OTEL_AVAILABLE:
        return None

    try:
        tracer = trace.get_tracer(__name__)
        return tracer.start_span(name, attributes=attributes)
    except Exception as e:
        logger.debug(f"Failed to create span: {e}")
        return None

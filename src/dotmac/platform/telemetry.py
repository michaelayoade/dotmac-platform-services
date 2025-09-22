"""
Simple telemetry setup using OpenTelemetry directly.

No wrappers, just standard OpenTelemetry configuration.
"""

from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from fastapi import FastAPI
from dotmac.platform.settings import settings


def setup_telemetry(app: FastAPI | None = None) -> None:
    """
    Setup OpenTelemetry tracing and metrics.

    Uses settings from centralized configuration.
    """
    if not settings.observability.otel_enabled:
        return

    # Setup tracing
    if settings.observability.enable_tracing:
        tracer_provider = TracerProvider()

        if settings.observability.otel_endpoint:
            try:
                # Export to OTLP endpoint
                otlp_exporter = OTLPSpanExporter(
                    endpoint=settings.observability.otel_endpoint,
                    insecure=True  # Use settings to determine this
                )
                span_processor = BatchSpanProcessor(otlp_exporter)
                tracer_provider.add_span_processor(span_processor)
            except Exception as e:
                print(f"Failed to setup OTLP span exporter: {e}")
                # Continue without exporter
                pass

        trace.set_tracer_provider(tracer_provider)

    # Setup metrics
    if settings.observability.enable_metrics:
        if settings.observability.otel_endpoint:
            try:
                metric_reader = PeriodicExportingMetricReader(
                    exporter=OTLPMetricExporter(
                        endpoint=settings.observability.otel_endpoint,
                        insecure=True
                    ),
                    export_interval_millis=30000  # 30 seconds
                )
                meter_provider = MeterProvider(metric_readers=[metric_reader])
                metrics.set_meter_provider(meter_provider)
            except Exception as e:
                print(f"Failed to setup OTLP metric exporter: {e}")
                # Continue without exporter
                pass

    # Auto-instrument libraries
    if app:
        FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument()
    RequestsInstrumentor().instrument()


def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer for the given component name."""
    return trace.get_tracer(name)


def get_meter(name: str) -> metrics.Meter:
    """Get a meter for the given component name."""
    return metrics.get_meter(name)


# Convenience exports for direct use
tracer = get_tracer(__name__)
meter = get_meter(__name__)
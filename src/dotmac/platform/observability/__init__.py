"""Observability entry point bridging to the telemetry helpers."""

from .manager import ObservabilityManager, ObservabilityMetricsRegistry, add_observability_middleware
from dotmac.platform.telemetry import (
    configure_structlog,
    create_span_context,
    get_meter,
    get_tracer,
    record_error,
    setup_telemetry,
)

__all__ = [
    "ObservabilityManager",
    "ObservabilityMetricsRegistry",
    "add_observability_middleware",
    "configure_structlog",
    "setup_telemetry",
    "get_tracer",
    "get_meter",
    "record_error",
    "create_span_context",
]


"""
Mock OpenTelemetry Fixtures for Testing
Provides OpenTelemetry tracing, metrics, and logging mocks.
"""

from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional, Union
from unittest.mock import Mock
from uuid import uuid4

import pytest


class MockSpan:
    """Mock OpenTelemetry span for tracing."""

    def __init__(
        self,
        name: str,
        context: Optional["MockSpanContext"] = None,
        kind: str = "INTERNAL",
        attributes: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.span_id = uuid4().hex[:16]
        self.trace_id = context.trace_id if context else uuid4().hex[:32]
        self.parent_span_id = context.span_id if context else None
        self.kind = kind
        self.attributes = attributes or {}
        self.events: List[Dict[str, Any]] = []
        self.status = {"status_code": "UNSET", "description": None}
        self.start_time = datetime.now(UTC)
        self.end_time = None
        self.is_recording = True
        self.context = context or MockSpanContext(self.trace_id, self.span_id)

    def set_attribute(self, key: str, value: Any):
        """Set span attribute."""
        if self.is_recording:
            self.attributes[key] = value

    def set_attributes(self, attributes: Dict[str, Any]):
        """Set multiple span attributes."""
        if self.is_recording:
            self.attributes.update(attributes)

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add event to span."""
        if self.is_recording:
            self.events.append({
                "name": name,
                "timestamp": datetime.now(UTC),
                "attributes": attributes or {}
            })

    def set_status(self, code: str, description: Optional[str] = None):
        """Set span status."""
        if self.is_recording:
            self.status = {"status_code": code, "description": description}

    def record_exception(self, exception: Exception):
        """Record exception in span."""
        if self.is_recording:
            self.add_event(
                "exception",
                {
                    "exception.type": type(exception).__name__,
                    "exception.message": str(exception),
                }
            )
            self.set_status("ERROR", str(exception))

    def end(self):
        """End the span."""
        if self.is_recording:
            self.end_time = datetime.now(UTC)
            self.is_recording = False

    def get_span_context(self) -> "MockSpanContext":
        """Get span context."""
        return self.context


class MockSpanContext:
    """Mock span context for trace propagation."""

    def __init__(self, trace_id: str, span_id: str):
        self.trace_id = trace_id
        self.span_id = span_id
        self.trace_flags = 1
        self.trace_state = {}
        self.is_valid = True

    @property
    def is_remote(self) -> bool:
        return False


class MockTracer:
    """Mock OpenTelemetry tracer."""

    def __init__(self, name: str = "test-tracer"):
        self.name = name
        self.spans: List[MockSpan] = []
        self.current_span: Optional[MockSpan] = None

    def start_span(
        self,
        name: str,
        context: Optional[MockSpanContext] = None,
        kind: str = "INTERNAL",
        attributes: Optional[Dict[str, Any]] = None
    ) -> MockSpan:
        """Start a new span."""
        span = MockSpan(name, context, kind, attributes)
        self.spans.append(span)
        return span

    @contextmanager
    def start_as_current_span(
        self,
        name: str,
        context: Optional[MockSpanContext] = None,
        kind: str = "INTERNAL",
        attributes: Optional[Dict[str, Any]] = None,
        end_on_exit: bool = True
    ):
        """Start span as current span context manager."""
        parent_context = self.current_span.get_span_context() if self.current_span else context
        span = self.start_span(name, parent_context, kind, attributes)
        previous_span = self.current_span
        self.current_span = span

        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            raise
        finally:
            if end_on_exit:
                span.end()
            self.current_span = previous_span

    def get_current_span(self) -> Optional[MockSpan]:
        """Get current active span."""
        return self.current_span


class MockMeter:
    """Mock OpenTelemetry meter for metrics."""

    def __init__(self, name: str = "test-meter"):
        self.name = name
        self.counters: Dict[str, "MockCounter"] = {}
        self.histograms: Dict[str, "MockHistogram"] = {}
        self.gauges: Dict[str, "MockGauge"] = {}
        self.up_down_counters: Dict[str, "MockUpDownCounter"] = {}

    def create_counter(
        self,
        name: str,
        description: str = "",
        unit: str = "1"
    ) -> "MockCounter":
        """Create a counter metric."""
        if name not in self.counters:
            self.counters[name] = MockCounter(name, description, unit)
        return self.counters[name]

    def create_histogram(
        self,
        name: str,
        description: str = "",
        unit: str = "1"
    ) -> "MockHistogram":
        """Create a histogram metric."""
        if name not in self.histograms:
            self.histograms[name] = MockHistogram(name, description, unit)
        return self.histograms[name]

    def create_gauge(
        self,
        name: str,
        description: str = "",
        unit: str = "1"
    ) -> "MockGauge":
        """Create a gauge metric."""
        if name not in self.gauges:
            self.gauges[name] = MockGauge(name, description, unit)
        return self.gauges[name]

    def create_up_down_counter(
        self,
        name: str,
        description: str = "",
        unit: str = "1"
    ) -> "MockUpDownCounter":
        """Create an up-down counter metric."""
        if name not in self.up_down_counters:
            self.up_down_counters[name] = MockUpDownCounter(name, description, unit)
        return self.up_down_counters[name]


class MockCounter:
    """Mock counter metric."""

    def __init__(self, name: str, description: str = "", unit: str = "1"):
        self.name = name
        self.description = description
        self.unit = unit
        self.measurements: List[Dict[str, Any]] = []
        self.value = 0

    def add(self, amount: Union[int, float], attributes: Optional[Dict[str, Any]] = None):
        """Add to counter."""
        self.value += amount
        self.measurements.append({
            "value": amount,
            "attributes": attributes or {},
            "timestamp": datetime.now(UTC)
        })


class MockHistogram:
    """Mock histogram metric."""

    def __init__(self, name: str, description: str = "", unit: str = "1"):
        self.name = name
        self.description = description
        self.unit = unit
        self.measurements: List[Dict[str, Any]] = []
        self.values: List[float] = []

    def record(self, value: Union[int, float], attributes: Optional[Dict[str, Any]] = None):
        """Record value in histogram."""
        self.values.append(float(value))
        self.measurements.append({
            "value": value,
            "attributes": attributes or {},
            "timestamp": datetime.now(UTC)
        })


class MockGauge:
    """Mock gauge metric."""

    def __init__(self, name: str, description: str = "", unit: str = "1"):
        self.name = name
        self.description = description
        self.unit = unit
        self.measurements: List[Dict[str, Any]] = []
        self.value = 0

    def set(self, value: Union[int, float], attributes: Optional[Dict[str, Any]] = None):
        """Set gauge value."""
        self.value = value
        self.measurements.append({
            "value": value,
            "attributes": attributes or {},
            "timestamp": datetime.now(UTC)
        })


class MockUpDownCounter:
    """Mock up-down counter metric."""

    def __init__(self, name: str, description: str = "", unit: str = "1"):
        self.name = name
        self.description = description
        self.unit = unit
        self.measurements: List[Dict[str, Any]] = []
        self.value = 0

    def add(self, amount: Union[int, float], attributes: Optional[Dict[str, Any]] = None):
        """Add to up-down counter (can be negative)."""
        self.value += amount
        self.measurements.append({
            "value": amount,
            "attributes": attributes or {},
            "timestamp": datetime.now(UTC)
        })


class MockLogger:
    """Mock structured logger for OpenTelemetry logging."""

    def __init__(self, name: str = "test-logger"):
        self.name = name
        self.records: List[Dict[str, Any]] = []
        self.level = "INFO"

    def _log(
        self,
        level: str,
        message: str,
        attributes: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Exception] = None
    ):
        """Internal log method."""
        record = {
            "timestamp": datetime.now(UTC),
            "level": level,
            "message": message,
            "attributes": attributes or {},
            "logger_name": self.name,
        }

        if exc_info:
            record["exception"] = {
                "type": type(exc_info).__name__,
                "message": str(exc_info),
            }

        self.records.append(record)

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log("DEBUG", message, kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log("INFO", message, kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log("WARNING", message, kwargs)

    def error(self, message: str, exc_info: Optional[Exception] = None, **kwargs):
        """Log error message."""
        self._log("ERROR", message, kwargs, exc_info)

    def critical(self, message: str, exc_info: Optional[Exception] = None, **kwargs):
        """Log critical message."""
        self._log("CRITICAL", message, kwargs, exc_info)


class MockTracerProvider:
    """Mock OpenTelemetry tracer provider."""

    def __init__(self):
        self.tracers: Dict[str, MockTracer] = {}
        self.resource = {
            "service.name": "test-service",
            "service.version": "1.0.0",
            "deployment.environment": "test",
        }

    def get_tracer(
        self,
        name: str,
        version: Optional[str] = None,
        schema_url: Optional[str] = None
    ) -> MockTracer:
        """Get or create tracer."""
        if name not in self.tracers:
            self.tracers[name] = MockTracer(name)
        return self.tracers[name]


class MockMeterProvider:
    """Mock OpenTelemetry meter provider."""

    def __init__(self):
        self.meters: Dict[str, MockMeter] = {}
        self.resource = {
            "service.name": "test-service",
            "service.version": "1.0.0",
        }

    def get_meter(
        self,
        name: str,
        version: Optional[str] = None,
        schema_url: Optional[str] = None
    ) -> MockMeter:
        """Get or create meter."""
        if name not in self.meters:
            self.meters[name] = MockMeter(name)
        return self.meters[name]


class MockLoggerProvider:
    """Mock OpenTelemetry logger provider."""

    def __init__(self):
        self.loggers: Dict[str, MockLogger] = {}

    def get_logger(
        self,
        name: str,
        version: Optional[str] = None,
        schema_url: Optional[str] = None
    ) -> MockLogger:
        """Get or create logger."""
        if name not in self.loggers:
            self.loggers[name] = MockLogger(name)
        return self.loggers[name]


class MockOTLPExporter:
    """Mock OTLP exporter for telemetry data."""

    def __init__(self, endpoint: str = "http://localhost:4317"):
        self.endpoint = endpoint
        self.exported_spans: List[MockSpan] = []
        self.exported_metrics: List[Dict[str, Any]] = []
        self.exported_logs: List[Dict[str, Any]] = []

    def export_spans(self, spans: List[MockSpan]) -> bool:
        """Export spans."""
        self.exported_spans.extend(spans)
        return True

    def export_metrics(self, metrics: List[Dict[str, Any]]) -> bool:
        """Export metrics."""
        self.exported_metrics.extend(metrics)
        return True

    def export_logs(self, logs: List[Dict[str, Any]]) -> bool:
        """Export logs."""
        self.exported_logs.extend(logs)
        return True

    def shutdown(self) -> bool:
        """Shutdown exporter."""
        return True


class MockBaggage:
    """Mock baggage for context propagation."""

    def __init__(self):
        self.items: Dict[str, str] = {}

    def set(self, key: str, value: str):
        """Set baggage item."""
        self.items[key] = value

    def get(self, key: str) -> Optional[str]:
        """Get baggage item."""
        return self.items.get(key)

    def remove(self, key: str):
        """Remove baggage item."""
        if key in self.items:
            del self.items[key]

    def clear(self):
        """Clear all baggage items."""
        self.items.clear()


@pytest.fixture
def mock_tracer():
    """Fixture providing a mock tracer."""
    return MockTracer()


@pytest.fixture
def mock_meter():
    """Fixture providing a mock meter."""
    return MockMeter()


@pytest.fixture
def mock_logger():
    """Fixture providing a mock logger."""
    return MockLogger()


@pytest.fixture
def mock_tracer_provider():
    """Fixture providing a mock tracer provider."""
    return MockTracerProvider()


@pytest.fixture
def mock_meter_provider():
    """Fixture providing a mock meter provider."""
    return MockMeterProvider()


@pytest.fixture
def mock_otel_exporter():
    """Fixture providing a mock OTLP exporter."""
    return MockOTLPExporter()


@pytest.fixture
def mock_otel_setup():
    """Fixture providing complete OpenTelemetry mock setup."""
    tracer_provider = MockTracerProvider()
    meter_provider = MockMeterProvider()
    logger_provider = MockLoggerProvider()
    exporter = MockOTLPExporter()

    return {
        "tracer_provider": tracer_provider,
        "meter_provider": meter_provider,
        "logger_provider": logger_provider,
        "exporter": exporter,
        "tracer": tracer_provider.get_tracer("test"),
        "meter": meter_provider.get_meter("test"),
        "logger": logger_provider.get_logger("test"),
    }
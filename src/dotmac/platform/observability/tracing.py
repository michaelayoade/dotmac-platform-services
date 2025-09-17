"""
Production-ready distributed tracing for dotmac platform services.

Supports:
- OpenTelemetry integration
- Database and HTTP instrumentation
- Custom span creation and context propagation
- Performance metrics correlation
- Multi-tenant trace isolation
"""

import json

import random
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from dotmac.platform.observability.unified_logging import get_logger
try:
    from opentelemetry import trace

    # Zipkin exporter removed; use OTLP via bootstrap
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    _opentelemetry_available = True
except ImportError:
    _opentelemetry_available = False
    # Provide minimal fallback implementations
    trace = None  # type: ignore
    Resource = None  # type: ignore
    TracerProvider = None  # type: ignore
    BatchSpanProcessor = None  # type: ignore
    RequestsInstrumentor = None  # type: ignore
    SQLAlchemyInstrumentor = None  # type: ignore

from .config import ObservabilityConfig

class SamplingDecision(Enum):
    """Sampling decision enumeration."""

    NOT_RECORD = "not_record"
    RECORD = "record"
    RECORD_AND_SAMPLED = "record_and_sampled"

class SpanKind(str, Enum):
    """Minimal span kind enum for tests."""

    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"

class SpanStatus(str, Enum):
    """Minimal span status enum for tests."""

    UNSET = "unset"
    OK = "ok"
    ERROR = "error"

@dataclass
class SamplingResult:
    """Result of sampling decision."""

    decision: SamplingDecision
    attributes: dict[str, Any] | None = None
    trace_state: str | None = None

class SamplingStrategy(ABC):
    """Abstract base class for sampling strategies."""

    @abstractmethod
    def should_sample(
        self,
        trace_id: str,
        span_name: str,
        parent_span: Optional["Span"] = None,
        attributes: dict[str, Any] | None = None,
    ) -> SamplingResult:
        """Determine if span should be sampled."""

class AlwaysSampleStrategy(SamplingStrategy):
    """Always sample all traces."""

    def should_sample(
        self,
        trace_id: str,
        span_name: str,
        parent_span: Optional["Span"] = None,
        attributes: dict[str, Any] | None = None,
    ) -> SamplingResult:
        return SamplingResult(SamplingDecision.RECORD_AND_SAMPLED)

class NeverSampleStrategy(SamplingStrategy):
    """Never sample any traces."""

    def should_sample(
        self,
        trace_id: str,
        span_name: str,
        parent_span: Optional["Span"] = None,
        attributes: dict[str, Any] | None = None,
    ) -> SamplingResult:
        return SamplingResult(SamplingDecision.NOT_RECORD)

class ProbabilitySampleStrategy(SamplingStrategy):
    """Probability-based sampling strategy."""

    def __init__(self, sample_rate: float = 0.1) -> None:
        self.sample_rate = max(0.0, min(1.0, sample_rate))

    def should_sample(
        self,
        trace_id: str,
        span_name: str,
        parent_span: Optional["Span"] = None,
        attributes: dict[str, Any] | None = None,
    ) -> SamplingResult:
        # Use trace_id for deterministic sampling
        trace_hash = hash(trace_id) % 1000000
        threshold = int(self.sample_rate * 1000000)

        if trace_hash < threshold:
            return SamplingResult(SamplingDecision.RECORD_AND_SAMPLED)
        return SamplingResult(SamplingDecision.NOT_RECORD)

class RateLimitingSampleStrategy(SamplingStrategy):
    """Rate-limiting sampling strategy."""

    def __init__(self, max_traces_per_second: int = 100) -> None:
        self.max_traces_per_second = max_traces_per_second
        self._token_bucket = max_traces_per_second
        self._last_refill = time.time()
        self._lock = threading.Lock()

    def should_sample(
        self,
        trace_id: str,
        span_name: str,
        parent_span: Optional["Span"] = None,
        attributes: dict[str, Any] | None = None,
    ) -> SamplingResult:
        with self._lock:
            now = time.time()

            # Refill tokens
            time_elapsed = now - self._last_refill
            tokens_to_add = int(time_elapsed * self.max_traces_per_second)
            self._token_bucket = min(self.max_traces_per_second, self._token_bucket + tokens_to_add)
            self._last_refill = now

            # Check if we have tokens
            if self._token_bucket > 0:
                self._token_bucket -= 1
                return SamplingResult(SamplingDecision.RECORD_AND_SAMPLED)

            return SamplingResult(SamplingDecision.NOT_RECORD)

class AdaptiveSampleStrategy(SamplingStrategy):
    """Adaptive sampling based on span attributes."""

    def __init__(
        self,
        default_rate: float = 0.1,
        error_rate: float = 1.0,
        slow_rate: float = 0.5,
        slow_threshold_ms: float = 1000,
        service_rates: dict[str, float] | None = None,
        operation_rates: dict[str, float] | None = None,
    ) -> None:
        self.default_rate = default_rate
        self.error_rate = error_rate
        self.slow_rate = slow_rate
        self.slow_threshold_ms = slow_threshold_ms
        self.service_rates = service_rates or {}
        self.operation_rates = operation_rates or {}

    def should_sample(
        self,
        trace_id: str,
        span_name: str,
        parent_span: Optional["Span"] = None,
        attributes: dict[str, Any] | None = None,
    ) -> SamplingResult:
        attributes = attributes or {}

        # Always sample errors
        if attributes.get("error") or (parent_span and parent_span.error):
            return SamplingResult(SamplingDecision.RECORD_AND_SAMPLED)

        # Sample slow operations at higher rate
        duration_ms = attributes.get("duration_ms", 0)
        if duration_ms > self.slow_threshold_ms and random.random() < self.slow_rate:
            return SamplingResult(SamplingDecision.RECORD_AND_SAMPLED)

        # Service-specific rates
        service_name = attributes.get("service.name")
        if service_name in self.service_rates:
            if random.random() < self.service_rates[service_name]:
                return SamplingResult(SamplingDecision.RECORD_AND_SAMPLED)

        # Operation-specific rates
        if span_name in self.operation_rates:
            if random.random() < self.operation_rates[span_name]:
                return SamplingResult(SamplingDecision.RECORD_AND_SAMPLED)

        # Default rate
        if random.random() < self.default_rate:
            return SamplingResult(SamplingDecision.RECORD_AND_SAMPLED)

        return SamplingResult(SamplingDecision.NOT_RECORD)

# ---------------------------------------------------------------------------
# Minimal decorator for unit tests
# ---------------------------------------------------------------------------

def trace_operation(operation_name: str):
    """Lightweight decorator that tags a function with an operation name.

    For tests, it simply returns a passthrough wrapper.
    """

    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    return decorator

class SpanProcessor(ABC):
    """Abstract span processor for custom span processing."""

    @abstractmethod
    def on_start(self, span: "Span", parent_context: dict[str, Any] | None = None):
        """Called when span starts."""

    @abstractmethod
    def on_end(self, span: "Span"):
        """Called when span ends."""

    def shutdown(self) -> None:
        """Shutdown the processor."""

class BatchSpanProcessor(SpanProcessor):
    """Batch span processor for efficient span processing."""

    def __init__(
        self,
        span_exporter: "SpanExporter",
        max_queue_size: int = 2048,
        schedule_delay_millis: int = 5000,
        max_export_batch_size: int = 512,
        export_timeout_millis: int = 30000,
    ) -> None:
        self.span_exporter = span_exporter
        self.max_queue_size = max_queue_size
        self.schedule_delay_millis = schedule_delay_millis
        self.max_export_batch_size = max_export_batch_size
        self.export_timeout_millis = export_timeout_millis

        self._queue: list[Span] = []
        self._lock = threading.Lock()
        self._worker_thread: threading.Thread | None = None
        self._shutdown_event = threading.Event()

        self._start_worker()

    def on_start(self, span: "Span", parent_context: dict[str, Any] | None = None) -> None:
        """Called when span starts."""
        # No-op for batch processor

    def on_end(self, span: "Span") -> None:
        """Called when span ends."""
        with self._lock:
            if len(self._queue) < self.max_queue_size:
                self._queue.append(span)

    def _start_worker(self) -> None:
        """Start the background worker thread."""
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()

    def _worker(self) -> None:
        """Background worker to export spans."""
        while not self._shutdown_event.is_set():
            try:
                spans_to_export = []

                with self._lock:
                    if self._queue:
                        spans_to_export = self._queue[: self.max_export_batch_size]
                        self._queue = self._queue[self.max_export_batch_size :]

                if spans_to_export:
                    self.span_exporter.export(spans_to_export)

                # Wait for next batch
                self._shutdown_event.wait(self.schedule_delay_millis / 1000.0)

            except Exception as e:
                logger = get_logger(__name__)
                logger.error(
                    "Error in span processor worker: %s",
                    e,
                    exc_info=True,
                    extra={"component": "span_processor", "error_type": type(e).__name__},
                )

    def shutdown(self) -> None:
        """Shutdown the processor."""
        self._shutdown_event.set()

        # Export remaining spans
        with self._lock:
            if self._queue:
                self.span_exporter.export(self._queue)
                self._queue.clear()

        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)

        self.span_exporter.shutdown()

class FilteringSpanProcessor(SpanProcessor):
    """Span processor that filters spans based on criteria."""

    def __init__(
        self, downstream_processor: SpanProcessor, filter_func: Callable[["Span"], bool]
    ) -> None:
        self.downstream_processor = downstream_processor
        self.filter_func = filter_func

    def on_start(self, span: "Span", parent_context: dict[str, Any] | None = None) -> None:
        """Called when span starts."""
        if self.filter_func(span):
            self.downstream_processor.on_start(span, parent_context)

    def on_end(self, span: "Span") -> None:
        """Called when span ends."""
        if self.filter_func(span):
            self.downstream_processor.on_end(span)

    def shutdown(self) -> None:
        """Shutdown the processor."""
        self.downstream_processor.shutdown()

class SpanExporter(ABC):
    """Abstract span exporter."""

    @abstractmethod
    def export(self, spans: list["Span"]) -> bool:
        """Export spans."""

    def shutdown(self) -> None:
        """Shutdown the exporter (no-op by default)."""
        return None

class ConsoleSpanExporter(SpanExporter):
    """Console span exporter for debugging."""

    def export(self, spans: list["Span"]) -> bool:
        """Export spans to console."""
        logger = get_logger(__name__)
        for span in spans:
            logger.info(
                "Span exported: %s [%s:%s] - %.2fms",
                span.name,
                span.trace_id,
                span.span_id,
                span.duration_ms,
                extra={
                    "span_name": span.name,
                    "trace_id": span.trace_id,
                    "span_id": span.span_id,
                    "duration_ms": span.duration_ms,
                    "attributes": span.attributes if span.attributes else None,
                    "events_count": len(span.events) if span.events else 0,
                    "component": "console_exporter",
                },
            )
        return True

class CustomJSONSpanExporter(SpanExporter):
    """Custom JSON span exporter."""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self._lock = threading.Lock()

    def export(self, spans: list["Span"]) -> bool:
        """Export spans to JSON file."""
        try:
            with self._lock, open(self.file_path, "a") as f:
                for span in spans:
                    span_data = {
                        "trace_id": span.trace_id,
                        "span_id": span.span_id,
                        "name": span.name,
                        "start_time": span.start_time,
                        "end_time": span.end_time,
                        "duration_ms": span.duration_ms,
                        "attributes": span.attributes,
                        "events": span.events,
                        "status": span.status,
                        "error": str(span.error) if span.error else None,
                    }
                    f.write(json.dumps(span_data) + "\n")
            return True
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(
                "Failed to export spans to JSON file: %s",
                e,
                exc_info=True,
                extra={"component": "json_exporter", "file_path": self.file_path},
            )
            return False

class TraceCorrelator:
    """
    Utilities for trace correlation and context propagation.
    """

    def __init__(self) -> None:
        self._trace_contexts: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create_trace_context(
        self,
        correlation_id: str,
        tenant_id: str | None = None,
        user_id: str | None = None,
        additional_context: dict[str, Any] | None = None,
    ) -> str:
        """Create trace context and return trace ID."""
        trace_id = str(uuid4())

        with self._lock:
            self._trace_contexts[trace_id] = {
                "correlation_id": correlation_id,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "created_at": time.time(),
                **(additional_context or {}),
            }

        return trace_id

    def get_trace_context(self, trace_id: str) -> dict[str, Any] | None:
        """Get trace context by trace ID."""
        with self._lock:
            return self._trace_contexts.get(trace_id)

    def correlate_spans(self, parent_span: "Span", child_span: "Span") -> None:
        """Correlate child span with parent span."""
        child_span.trace_id = parent_span.trace_id
        child_span.set_attribute("parent.span_id", parent_span.span_id)

        # Propagate context
        if parent_span.trace_id in self._trace_contexts:
            context = self._trace_contexts[parent_span.trace_id]

            if context.get("tenant_id"):
                child_span.set_attribute("tenant.id", context["tenant_id"])
            if context.get("user_id"):
                child_span.set_attribute("user.id", context["user_id"])
            if context.get("correlation_id"):
                child_span.set_attribute("correlation_id", context["correlation_id"])

    def extract_trace_headers(self, headers: dict[str, str]) -> dict[str, Any] | None:
        """Extract trace context from HTTP headers."""
        trace_id = headers.get("X-Trace-ID")
        if not trace_id:
            return None

        return {
            "trace_id": trace_id,
            "span_id": headers.get("X-Span-ID"),
            "correlation_id": headers.get("X-Correlation-ID"),
            "tenant_id": headers.get("X-Tenant-ID"),
            "user_id": headers.get("X-User-ID"),
        }

    def inject_trace_headers(self, span: "Span") -> dict[str, str]:
        """Inject trace context into HTTP headers."""
        headers = {
            "X-Trace-ID": span.trace_id,
            "X-Span-ID": span.span_id,
        }

        # Add context from trace
        if span.trace_id in self._trace_contexts:
            context = self._trace_contexts[span.trace_id]

            if context.get("correlation_id"):
                headers["X-Correlation-ID"] = context["correlation_id"]
            if context.get("tenant_id"):
                headers["X-Tenant-ID"] = context["tenant_id"]
            if context.get("user_id"):
                headers["X-User-ID"] = context["user_id"]

        return headers

    def cleanup_old_contexts(self, max_age_seconds: int = 3600) -> None:
        """Clean up old trace contexts."""
        current_time = time.time()

        with self._lock:
            to_remove = []
            for trace_id, context in self._trace_contexts.items():
                if current_time - context.get("created_at", 0) > max_age_seconds:
                    to_remove.append(trace_id)

            for trace_id in to_remove:
                del self._trace_contexts[trace_id]

class Span:
    """
    Tracing span wrapper with fallback implementation.
    """

    def __init__(
        self,
        name: str,
        tracer: Optional["Tracer"] = None,
        parent_span: Optional["Span"] = None,
        trace_id: str | None = None,
    ) -> None:
        self.name = name
        self.tracer = tracer
        self.parent_span = parent_span
        self.trace_id = trace_id or str(uuid4())
        self.span_id = str(uuid4())
        self.start_time = time.time()
        self.end_time: float | None = None
        self.attributes: dict[str, Any] = {}
        self.events: list[dict[str, Any]] = []
        self.status = "ok"
        self.error: Exception | None = None

        # OpenTelemetry span if available
        self._otel_span = None
        if _opentelemetry_available and tracer and tracer.otel_tracer:
            self._otel_span = tracer.otel_tracer.start_span(name)

    def set_attribute(self, key: str, value: Any) -> None:
        """Set span attribute."""
        self.attributes[key] = value
        if self._otel_span:
            self._otel_span.set_attribute(key, value)

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        """Add event to span."""
        event = {"name": name, "timestamp": time.time(), "attributes": attributes or {}}
        self.events.append(event)
        if self._otel_span:
            self._otel_span.add_event(name, attributes)

    def set_status(self, status: str, description: str | None = None) -> None:
        """Set span status."""
        self.status = status
        if self._otel_span and _opentelemetry_available and trace:
            if status == "error":
                self._otel_span.set_status(trace.Status(trace.StatusCode.ERROR, description))
            else:
                self._otel_span.set_status(trace.Status(trace.StatusCode.OK, description))

    def record_exception(self, exception: Exception) -> None:
        """Record exception in span."""
        self.error = exception
        self.set_status("error", str(exception))
        if self._otel_span:
            self._otel_span.record_exception(exception)

    def finish(self) -> None:
        """Finish the span."""
        self.end_time = time.time()
        if self._otel_span:
            self._otel_span.end()

        # Notify span processors if tracer is available
        if self.tracer:
            for processor in self.tracer.span_processors:
                try:
                    processor.on_end(self)
                except Exception as e:
                    logger = get_logger(__name__)
                    logger.error(
                        "Error in span processor on_end: %s",
                        e,
                        exc_info=True,
                        extra={"component": "span_processor", "span_name": self.name},
                    )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.record_exception(exc_val)
        self.finish()
        return False

    @property
    def duration_ms(self) -> float:
        """Get span duration in milliseconds."""
        end_time = self.end_time or time.time()
        return (end_time - self.start_time) * 1000

class Tracer:
    """
    Distributed tracer with OpenTelemetry integration.
    Enhanced with sampling strategies and span processors.
    """

    def __init__(
        self,
        service_name: str,
        config: ObservabilityConfig | None = None,
        tenant_id: str | None = None,
        sampling_strategy: SamplingStrategy | None = None,
        span_processors: list[SpanProcessor] | None = None,
        trace_correlator: TraceCorrelator | None = None,
    ) -> None:
        self.service_name = service_name
        self.config = config or ObservabilityConfig()
        self.tenant_id = tenant_id
        self.sampling_strategy = sampling_strategy or ProbabilitySampleStrategy(0.1)
        self.span_processors = span_processors or []
        self.trace_correlator = trace_correlator or TraceCorrelator()

        # OpenTelemetry tracer
        self._otel_tracer = None
        if _opentelemetry_available and self.config.enable_tracing:
            self._setup_opentelemetry()

    def _setup_opentelemetry(self) -> None:
        """Set up OpenTelemetry tracing."""
        if not Resource:
            return
        resource = Resource.create(
            {
                "service.name": self.service_name,
                "service.version": "1.0.0",
            }
        )

        if self.tenant_id:
            resource = resource.merge(Resource.create({"tenant.id": self.tenant_id}))

        provider = TracerProvider(resource=resource)

        # Add exporters based on configuration
        # Exporters are configured via platform bootstrap (OTLP)

        trace.set_tracer_provider(provider)
        self._otel_tracer = trace.get_tracer(self.service_name)

    @property
    def otel_tracer(self) -> Any:
        """Get the OpenTelemetry tracer instance."""
        return self._otel_tracer

    def start_span(
        self,
        name: str,
        parent_span: Span | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Span:
        """Start a new span with sampling and processing."""
        # Create span
        span = Span(
            name=name,
            tracer=self,
            parent_span=parent_span,
            trace_id=parent_span.trace_id if parent_span else None,
        )

        # Apply sampling decision
        sampling_result = self.sampling_strategy.should_sample(
            trace_id=span.trace_id, span_name=name, parent_span=parent_span, attributes=attributes
        )

        # Set sampling attributes
        if sampling_result.attributes:
            for key, value in sampling_result.attributes.items():
                span.set_attribute(key, value)

        # Apply provided attributes
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)

        # Add tenant context if available
        if self.tenant_id:
            span.set_attribute("tenant.id", self.tenant_id)

        # Set sampling decision
        span.set_attribute("sampling.decision", sampling_result.decision.value)

        # Correlate with parent if available
        if parent_span:
            self.trace_correlator.correlate_spans(parent_span, span)

        # Notify span processors
        for processor in self.span_processors:
            try:
                processor.on_start(span)
            except Exception as e:
                logger = get_logger(__name__)
                logger.error(
                    "Error in span processor on_start: %s",
                    e,
                    exc_info=True,
                    extra={"component": "span_processor", "span_name": span.name},
                )

        return span

    @contextmanager
    def trace(self, name: str, attributes: dict[str, Any] | None = None):
        """Context manager for tracing operations."""
        span = self.start_span(name, attributes=attributes)
        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            raise
        finally:
            span.finish()

class TracingManager:
    """
    Central tracing manager for the platform.
    Enhanced with sampling strategies and span processors.
    """

    def __init__(
        self,
        config: ObservabilityConfig | None = None,
        default_sampling_strategy: SamplingStrategy | None = None,
        span_processors: list[SpanProcessor] | None = None,
    ) -> None:
        self.config = config or ObservabilityConfig()
        self.default_sampling_strategy = default_sampling_strategy or ProbabilitySampleStrategy(0.1)
        self.span_processors = span_processors or []
        self.trace_correlator = TraceCorrelator()
        self._tracers: dict[str, Tracer] = {}

        # Set up auto-instrumentation
        if _opentelemetry_available and self.config.enable_auto_instrumentation:
            self._setup_auto_instrumentation()

    def _setup_auto_instrumentation(self) -> None:
        """Set up automatic instrumentation."""
        # HTTP requests instrumentation
        RequestsInstrumentor().instrument()

        # SQLAlchemy instrumentation
        SQLAlchemyInstrumentor().instrument()

    def get_tracer(
        self,
        service_name: str,
        tenant_id: str | None = None,
        sampling_strategy: SamplingStrategy | None = None,
    ) -> Tracer:
        """Get or create a tracer for a service."""
        cache_key = f"{service_name}:{tenant_id}"

        if cache_key not in self._tracers:
            self._tracers[cache_key] = Tracer(
                service_name=service_name,
                config=self.config,
                tenant_id=tenant_id,
                sampling_strategy=sampling_strategy or self.default_sampling_strategy,
                span_processors=self.span_processors.copy(),
                trace_correlator=self.trace_correlator,
            )

        return self._tracers[cache_key]

    def add_span_processor(self, processor: SpanProcessor) -> None:
        """Add a span processor to all tracers."""
        self.span_processors.append(processor)

        # Add to existing tracers
        for tracer in self._tracers.values():
            tracer.span_processors.append(processor)

    def set_sampling_strategy(self, strategy: SamplingStrategy) -> None:
        """Set default sampling strategy."""
        self.default_sampling_strategy = strategy

    def create_trace_context(
        self,
        correlation_id: str,
        tenant_id: str | None = None,
        user_id: str | None = None,
        **additional_context,
    ) -> str:
        """Create trace context."""
        return self.trace_correlator.create_trace_context(
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            user_id=user_id,
            additional_context=additional_context,
        )

    def correlate_spans(self, parent_span: Span, child_span: Span) -> None:
        """Correlate child span with parent."""
        self.trace_correlator.correlate_spans(parent_span, child_span)

    def extract_trace_context(self, headers: dict[str, str]) -> dict[str, Any] | None:
        """Extract trace context from headers."""
        return self.trace_correlator.extract_trace_headers(headers)

    def inject_trace_headers(self, span: Span) -> dict[str, str]:
        """Inject trace context into headers."""
        return self.trace_correlator.inject_trace_headers(span)

    def shutdown(self) -> None:
        """Shutdown all span processors."""
        for processor in self.span_processors:
            processor.shutdown()

    def trace_database_operation(
        self, operation: str, table: str, query: str | None = None
    ) -> Span:
        """Create a database operation span."""
        tracer = self.get_tracer("database")
        span = tracer.start_span(f"db.{operation}")

        span.set_attribute("db.operation", operation)
        span.set_attribute("db.table", table)
        if query:
            span.set_attribute("db.statement", query)

        return span

    def trace_http_request(self, method: str, url: str, status_code: int | None = None) -> Span:
        """Create an HTTP request span."""
        tracer = self.get_tracer("http")
        span = tracer.start_span(f"http.{method.lower()}")

        span.set_attribute("http.method", method)
        span.set_attribute("http.url", url)
        if status_code:
            span.set_attribute("http.status_code", status_code)

        return span

    def trace_business_operation(
        self, service: str, operation: str, tenant_id: str | None = None
    ) -> Span:
        """Create a business operation span."""
        tracer = self.get_tracer(service, tenant_id)
        span = tracer.start_span(operation)

        span.set_attribute("operation.type", "business")
        span.set_attribute("service.name", service)

        return span

class PerformanceTracer:
    """
    Specialized tracer for performance monitoring.
    """

    def __init__(self, manager: TracingManager) -> None:
        self.manager = manager
        self.tracer = manager.get_tracer("performance")

    @contextmanager
    def trace_performance(self, operation: str, **attributes):
        """Trace operation performance."""
        with self.tracer.trace(f"perf.{operation}", attributes=attributes) as span:
            start_time = time.time()

            try:
                yield span
            finally:
                duration_ms = (time.time() - start_time) * 1000
                span.set_attribute("performance.duration_ms", duration_ms)

                # Add performance thresholds
                if duration_ms > 1000:
                    span.set_attribute("performance.slow", True)
                    span.add_event(
                        "slow_operation", {"threshold_ms": 1000, "actual_ms": duration_ms}
                    )

    def trace_cache_operation(self, operation: str, key: str, hit: bool) -> None:
        """Trace cache operations."""
        with self.tracer.trace(f"cache.{operation}") as span:
            span.set_attribute("cache.key", key)
            span.set_attribute("cache.hit", hit)
            span.set_attribute("cache.operation", operation)

# Factory functions
def create_tracer(service_name: str, **kwargs) -> Tracer:
    """Create a tracer."""
    return Tracer(service_name, **kwargs)

def create_tracing_manager(**kwargs) -> TracingManager:
    """Create a tracing manager."""
    return TracingManager(**kwargs)

def create_performance_tracer(manager: TracingManager) -> PerformanceTracer:
    """Create a performance tracer."""
    return PerformanceTracer(manager)

# Sampling strategy factories
def create_probability_sampler(sample_rate: float = 0.1) -> ProbabilitySampleStrategy:
    """Create probability sampling strategy."""
    return ProbabilitySampleStrategy(sample_rate)

def create_rate_limiting_sampler(max_traces_per_second: int = 100) -> RateLimitingSampleStrategy:
    """Create rate limiting sampling strategy."""
    return RateLimitingSampleStrategy(max_traces_per_second)

def create_adaptive_sampler(**kwargs) -> AdaptiveSampleStrategy:
    """Create adaptive sampling strategy."""
    return AdaptiveSampleStrategy(**kwargs)

# Span processor factories
def create_batch_processor(span_exporter: SpanExporter, **kwargs) -> BatchSpanProcessor:
    """Create batch span processor."""
    return BatchSpanProcessor(span_exporter, **kwargs)

def create_filtering_processor(
    downstream_processor: SpanProcessor, filter_func: Callable[[Span], bool]
) -> FilteringSpanProcessor:
    """Create filtering span processor."""
    return FilteringSpanProcessor(downstream_processor, filter_func)

# Span exporter factories
def create_console_exporter() -> ConsoleSpanExporter:
    """Create console span exporter."""
    return ConsoleSpanExporter()

def create_json_file_exporter(file_path: str) -> CustomJSONSpanExporter:
    """Create JSON file span exporter."""
    return CustomJSONSpanExporter(file_path)

# Trace correlator factory
def create_trace_correlator() -> TraceCorrelator:
    """Create trace correlator."""
    return TraceCorrelator()

# Decorator for automatic tracing
def trace_method(operation_name: str | None = None):
    """Decorator to automatically trace method calls."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"

            # Try to get tracer from self if available
            tracer = None
            if args and hasattr(args[0], "_tracer"):
                tracer = args[0]._tracer
            else:
                # Create default tracer
                manager = TracingManager()
                tracer = manager.get_tracer("default")

            with tracer.trace(name) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("result.success", True)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_attribute("result.success", False)
                    raise

        return wrapper

    return decorator

class TraceExporter:
    """
    Configurable trace exporter supporting multiple backends.

    Simple no-op exporter placeholder; OTLP is configured via bootstrap.
    """

    def __init__(
        self,
        exporter_type: str = "none",
        endpoint: str | None = None,
        service_name: str = "dotmac-service",
        **kwargs,
    ) -> None:
        self.exporter_type = exporter_type.lower()
        self.endpoint = endpoint
        self.service_name = service_name
        self.kwargs = kwargs
        self._exporter = None
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the trace exporter."""
        if self._initialized:
            return

        if not _opentelemetry_available:
            self._exporter = NoOpTraceExporter()
            self._initialized = True
            return

        try:
            # No-op exporter; tracing export handled via bootstrap
            self._exporter = NoOpTraceExporter()

            self._initialized = True
        except Exception:
            # Fallback to no-op exporter
            self._exporter = NoOpTraceExporter()
            self._initialized = True

    def export(self, spans: list[Any]) -> None:
        """Export spans to configured backend."""
        if not self._initialized:
            self.initialize()

        if hasattr(self._exporter, "export"):
            self._exporter.export(spans)

class NoOpTraceExporter:
    """No-op trace exporter for fallback scenarios."""

    def export(self, spans: list[Any]) -> None:
        """No-op export method."""

# Stub functions for architectural validation
def get_tracer(name="default") -> None:
    """Get a tracer instance. Stub implementation."""

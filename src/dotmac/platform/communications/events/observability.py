"""Observability hooks and integration for event bus."""


import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Optional

from .message import Event
from dotmac.platform.observability.unified_logging import get_logger

__all__ = [
    "EventObservability",
    "ObservabilityHooks",
    "ObservabilityMetrics",
    "create_default_hooks",
    "create_dotmac_observability_hooks",
    "no_op_hooks",
]

logger = get_logger(__name__)

class EventObservability:
    """
    Event observability integration facade.

    Provides a unified interface for event bus observability features including
    metrics collection, logging, tracing, and integration with monitoring systems.
    """

    def __init__(self, hooks: Optional["ObservabilityHooks"] = None):
        """
        Initialize event observability.

        Args:
            hooks: Custom observability hooks, defaults to basic hooks
        """
        self.hooks = hooks
        self._metrics_collector: Optional["MetricsCollector"] = None

    def get_metrics(self) -> "ObservabilityMetrics":
        """Get current observability metrics."""
        if self._metrics_collector:
            return self._metrics_collector.get_metrics()
        # Lazy initialization after classes are defined
        if not self._metrics_collector:
            self._metrics_collector = MetricsCollector()
        return self._metrics_collector.get_metrics()

    def reset_metrics(self) -> None:
        """Reset observability metrics."""
        if self._metrics_collector:
            self._metrics_collector.reset_metrics()

# Hook function types
OnPublishHook = Callable[[Event, str, float], Awaitable[None]]
OnConsumeHook = Callable[[Event, str, float], Awaitable[None]]
OnRetryHook = Callable[[Event, int, Exception, str], Awaitable[None]]
OnDLQHook = Callable[[Event, Exception, str], Awaitable[None]]
OnErrorHook = Callable[[Event, Exception, str, str], Awaitable[None]]

@dataclass
class ObservabilityMetrics:
    """Metrics collected by observability hooks."""

    events_published: int = 0
    events_consumed: int = 0
    events_retried: int = 0
    events_dlq: int = 0
    events_errored: int = 0

    publish_duration_total: float = 0.0
    consume_duration_total: float = 0.0

    def reset(self) -> None:
        """Reset all metrics to zero."""
        self.events_published = 0
        self.events_consumed = 0
        self.events_retried = 0
        self.events_dlq = 0
        self.events_errored = 0
        self.publish_duration_total = 0.0
        self.consume_duration_total = 0.0

class ObservabilityHooks:
    """
    Container for observability hooks.

    These hooks are called at various points in the event lifecycle
    to enable monitoring, metrics collection, and tracing.
    """

    def __init__(
        self,
        on_publish: Optional[OnPublishHook] = None,
        on_consume: Optional[OnConsumeHook] = None,
        on_retry: Optional[OnRetryHook] = None,
        on_dlq: Optional[OnDLQHook] = None,
        on_error: Optional[OnErrorHook] = None,
    ):
        """
        Initialize observability hooks.

        Args:
            on_publish: Called when an event is published
            on_consume: Called when an event is consumed successfully
            on_retry: Called when an event processing is retried
            on_dlq: Called when an event is sent to DLQ
            on_error: Called when any error occurs
        """
        self.on_publish = on_publish or self._no_op_publish
        self.on_consume = on_consume or self._no_op_consume
        self.on_retry = on_retry or self._no_op_retry
        self.on_dlq = on_dlq or self._no_op_dlq
        self.on_error = on_error or self._no_op_error

    # No-op implementations
    async def _no_op_publish(self, event: Event, adapter_name: str, duration: float) -> None:
        pass

    async def _no_op_consume(self, event: Event, adapter_name: str, duration: float) -> None:
        pass

    async def _no_op_retry(
        self, event: Event, retry_count: int, error: Exception, adapter_name: str
    ) -> None:
        pass

    async def _no_op_dlq(self, event: Event, error: Exception, adapter_name: str) -> None:
        pass

    async def _no_op_error(
        self, event: Event, error: Exception, operation: str, adapter_name: str
    ) -> None:
        pass

class MetricsCollector:
    """Simple metrics collector for event bus operations."""

    def __init__(self):
        self.metrics = ObservabilityMetrics()
        self._logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    async def on_publish(self, event: Event, adapter_name: str, duration: float) -> None:
        """Handle publish event."""
        self.metrics.events_published += 1
        self.metrics.publish_duration_total += duration

        self._logger.debug(
            f"Event published: topic={event.topic}, adapter={adapter_name}, "
            f"duration={duration:.3f}s, id={event.id}"
        )

    async def on_consume(self, event: Event, adapter_name: str, duration: float) -> None:
        """Handle consume event."""
        self.metrics.events_consumed += 1
        self.metrics.consume_duration_total += duration

        self._logger.debug(
            f"Event consumed: topic={event.topic}, adapter={adapter_name}, "
            f"duration={duration:.3f}s, id={event.id}"
        )

    async def on_retry(
        self, event: Event, retry_count: int, error: Exception, adapter_name: str
    ) -> None:
        """Handle retry event."""
        self.metrics.events_retried += 1

        self._logger.warning(
            f"Event retry: topic={event.topic}, adapter={adapter_name}, "
            f"retry_count={retry_count}, error={error}, id={event.id}"
        )

    async def on_dlq(self, event: Event, error: Exception, adapter_name: str) -> None:
        """Handle DLQ event."""
        self.metrics.events_dlq += 1

        self._logger.error(
            f"Event sent to DLQ: topic={event.topic}, adapter={adapter_name}, "
            f"error={error}, id={event.id}"
        )

    async def on_error(
        self, event: Event, error: Exception, operation: str, adapter_name: str
    ) -> None:
        """Handle error event."""
        self.metrics.events_errored += 1

        self._logger.error(
            f"Event error: topic={event.topic}, adapter={adapter_name}, "
            f"operation={operation}, error={error}, id={event.id}"
        )

    def get_metrics(self) -> ObservabilityMetrics:
        """Get current metrics."""
        return self.metrics

    def reset_metrics(self) -> None:
        """Reset metrics."""
        self.metrics.reset()

def create_default_hooks() -> ObservabilityHooks:
    """Create default observability hooks with basic logging and metrics."""
    collector = MetricsCollector()

    return ObservabilityHooks(
        on_publish=collector.on_publish,
        on_consume=collector.on_consume,
        on_retry=collector.on_retry,
        on_dlq=collector.on_dlq,
        on_error=collector.on_error,
    )

def create_dotmac_observability_hooks(
    metrics_registry: Optional[Any] = None,
    tenant_metrics: Optional[Any] = None,
) -> ObservabilityHooks:
    """
    Create observability hooks that integrate with dotmac.platform.observability.

    This function creates hooks that record metrics using the DotMac
    observability package if it's available.

    Args:
        metrics_registry: MetricsRegistry from dotmac.platform.observability
        tenant_metrics: TenantMetrics from dotmac.platform.observability

    Returns:
        Configured observability hooks
    """
    try:
        # Try to import from dotmac platform package
        from dotmac.platform.observability import TenantContext
    except ImportError:
        # Fall back to default hooks if not available
        logger.warning(
            "dotmac.platform.observability not available, using default hooks. "
            "Install with: pip install 'dotmac-platform-services[observability]'"
        )
        return create_default_hooks()

    class DotMacObservabilityCollector:
        """Observability collector that integrates with dotmac.platform.observability."""

        def __init__(self, metrics_registry: Any, tenant_metrics: Any):
            self.metrics_registry = metrics_registry
            self.tenant_metrics = tenant_metrics

        async def on_publish(self, event: Event, adapter_name: str, duration: float) -> None:
            """Record publish metrics."""
            if self.metrics_registry:
                # Record system metrics
                self.metrics_registry.increment_counter(
                    "events_published_total",
                    1,
                    {
                        "adapter": adapter_name,
                        "topic": event.topic,
                    },
                )

                self.metrics_registry.observe_histogram(
                    "event_publish_duration_seconds",
                    duration,
                    {
                        "adapter": adapter_name,
                        "topic": event.topic,
                    },
                )

            if self.tenant_metrics and event.tenant_id:
                # Record tenant metrics
                context = TenantContext(
                    tenant_id=event.tenant_id,
                    service="event-bus",
                    additional_labels={"adapter": adapter_name, "topic": event.topic},
                )

                # This would be a custom business metric for event publishing
                self.tenant_metrics.record_business_metric("event_publish_success_rate", 1, context)

        async def on_consume(self, event: Event, adapter_name: str, duration: float) -> None:
            """Record consume metrics."""
            if self.metrics_registry:
                # Record system metrics
                self.metrics_registry.increment_counter(
                    "events_consumed_total",
                    1,
                    {
                        "adapter": adapter_name,
                        "topic": event.topic,
                    },
                )

                self.metrics_registry.observe_histogram(
                    "event_consume_duration_seconds",
                    duration,
                    {
                        "adapter": adapter_name,
                        "topic": event.topic,
                    },
                )

            if self.tenant_metrics and event.tenant_id:
                # Record tenant metrics
                context = TenantContext(
                    tenant_id=event.tenant_id,
                    service="event-bus",
                    additional_labels={"adapter": adapter_name, "topic": event.topic},
                )

                self.tenant_metrics.record_business_metric("event_consume_success_rate", 1, context)

        async def on_retry(
            self, event: Event, retry_count: int, error: Exception, adapter_name: str
        ) -> None:
            """Record retry metrics."""
            if self.metrics_registry:
                self.metrics_registry.increment_counter(
                    "events_retried_total",
                    1,
                    {
                        "adapter": adapter_name,
                        "topic": event.topic,
                        "error_type": type(error).__name__,
                    },
                )

        async def on_dlq(self, event: Event, error: Exception, adapter_name: str) -> None:
            """Record DLQ metrics."""
            if self.metrics_registry:
                self.metrics_registry.increment_counter(
                    "events_dlq_total",
                    1,
                    {
                        "adapter": adapter_name,
                        "topic": event.topic,
                        "error_type": type(error).__name__,
                    },
                )

            if self.tenant_metrics and event.tenant_id:
                # Record failure in business metrics
                context = TenantContext(
                    tenant_id=event.tenant_id,
                    service="event-bus",
                    additional_labels={"adapter": adapter_name, "topic": event.topic},
                )

                self.tenant_metrics.record_business_metric("event_publish_success_rate", 0, context)
                self.tenant_metrics.record_business_metric("event_consume_success_rate", 0, context)

        async def on_error(
            self, event: Event, error: Exception, operation: str, adapter_name: str
        ) -> None:
            """Record error metrics."""
            if self.metrics_registry:
                self.metrics_registry.increment_counter(
                    "events_error_total",
                    1,
                    {
                        "adapter": adapter_name,
                        "topic": event.topic,
                        "operation": operation,
                        "error_type": type(error).__name__,
                    },
                )

    collector = DotMacObservabilityCollector(metrics_registry, tenant_metrics)

    return ObservabilityHooks(
        on_publish=collector.on_publish,
        on_consume=collector.on_consume,
        on_retry=collector.on_retry,
        on_dlq=collector.on_dlq,
        on_error=collector.on_error,
    )

# Global no-op hooks instance
no_op_hooks = ObservabilityHooks()

# Utility functions for timing operations

class Timer:
    """Context manager for timing operations."""

    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.duration: float = 0.0

    def __enter__(self) -> "Timer":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.end_time = time.perf_counter()
        if self.start_time is not None:
            self.duration = self.end_time - self.start_time

async def time_async_operation(operation: Callable[[], Awaitable[Any]]) -> tuple[Any, float]:
    """
    Time an async operation and return result and duration.

    Args:
        operation: Async operation to time

    Returns:
        Tuple of (result, duration_seconds)
    """
    with Timer() as timer:
        result = await operation()

    return result, timer.duration

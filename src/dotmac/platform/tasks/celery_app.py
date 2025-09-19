from datetime import UTC
"""
Celery application configuration and initialization.

This module sets up Celery with RabbitMQ as the message broker
and Redis as the result backend, with full observability integration.
"""

from dotmac.platform.observability.unified_logging import get_logger
import os
import time
from typing import Any

from celery import Celery, Task
from celery.signals import (
    task_failure,
    task_postrun,
    task_prerun,
    task_retry,
    task_success,
    worker_ready,
)
from kombu import Exchange, Queue

# OpenTelemetry instrumentation
try:
    from opentelemetry import trace
    from opentelemetry.instrumentation.celery import CeleryInstrumentor

    OTEL_ENABLED = True
    tracer = trace.get_tracer(__name__)
except ImportError:  # pragma: no cover - optional dependency
    OTEL_ENABLED = False
    tracer = None

try:
    from dotmac.platform.observability import (
        MetricDefinition,
        MetricType,
        ObservabilityManager,
    )
    OBS_SUPPORTED = True
except Exception:  # pragma: no cover - observability optional in tests
    MetricDefinition = MetricType = ObservabilityManager = None  # type: ignore
    OBS_SUPPORTED = False

logger = get_logger(__name__)

_metrics_registry = None

def _get_metrics_registry():
    """Initialise (once) a metrics registry for Celery instrumentation."""

    global _metrics_registry
    if _metrics_registry is not None or not OBS_SUPPORTED:
        return _metrics_registry

    try:
        mgr = ObservabilityManager(
            service_name=os.getenv("CELERY_SERVICE_NAME", "dotmac-celery-worker"),
            environment=os.getenv("ENVIRONMENT", "development"),
            enable_logging=False,
            enable_tracing=False,
            enable_metrics=True,
            enable_performance=False,
        )
        mgr.initialize()
        registry = mgr.get_metrics_registry()
        if registry:
            # Register commonly used metrics
            registry.register_metric(
                MetricDefinition(
                    name="celery_task_started_total",
                    description="Number of Celery tasks started",
                    type=MetricType.COUNTER,
                    unit="1",
                )
            )
            registry.register_metric(
                MetricDefinition(
                    name="celery_task_completed_total",
                    description="Number of Celery tasks completed successfully",
                    type=MetricType.COUNTER,
                    unit="1",
                )
            )
            registry.register_metric(
                MetricDefinition(
                    name="celery_task_failed_total",
                    description="Number of Celery tasks that failed",
                    type=MetricType.COUNTER,
                    unit="1",
                )
            )
            registry.register_metric(
                MetricDefinition(
                    name="celery_task_retried_total",
                    description="Number of Celery task retries",
                    type=MetricType.COUNTER,
                    unit="1",
                )
            )
            registry.register_metric(
                MetricDefinition(
                    name="celery_task_duration_ms",
                    description="Histogram of Celery task execution time in milliseconds",
                    type=MetricType.HISTOGRAM,
                    unit="ms",
                )
            )
        _metrics_registry = registry
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Celery metrics registry unavailable: %s", exc)
        _metrics_registry = None

    return _metrics_registry

def _record_metric(
    metric_name: str, value: float = 1.0, labels: dict[str, str] | None = None
) -> None:
    registry = _get_metrics_registry()
    if not registry:
        return
    if metric_name == "celery_task_duration_ms":
        registry.observe_histogram(metric_name, value, labels=labels)
    else:
        registry.increment_counter(metric_name, value, labels=labels)

class CeleryConfig:
    """Celery configuration."""

    # Broker settings
    broker_url = os.getenv("CELERY_BROKER_URL", "amqp://admin:admin@localhost:5672//")
    result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

    # Task settings
    task_serializer = "json"
    task_track_started = True
    task_time_limit = 30 * 60  # 30 minutes
    task_soft_time_limit = 25 * 60  # 25 minutes
    task_acks_late = True
    task_reject_on_worker_lost = True

    # Result settings
    result_serializer = "json"
    result_expires = 3600  # 1 hour
    result_compression = "gzip"

    # Worker settings
    worker_prefetch_multiplier = 4
    worker_max_tasks_per_child = 1000
    worker_disable_rate_limits = False
    worker_send_task_events = True

    # Timezone
    timezone = "UTC"
    enable_utc = True

    # Routing
    task_default_queue = "default"
    task_default_exchange = "default"
    task_default_exchange_type = "direct"
    task_default_routing_key = "default"

    # Queue definitions
    task_queues = (
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("high_priority", Exchange("high_priority"), routing_key="high_priority"),
        Queue("low_priority", Exchange("low_priority"), routing_key="low_priority"),
        Queue("email", Exchange("email"), routing_key="email"),
        Queue("search", Exchange("search"), routing_key="search"),
        Queue("storage", Exchange("storage"), routing_key="storage"),
        Queue("analytics", Exchange("analytics"), routing_key="analytics"),
    )

    # Route specific tasks to specific queues
    task_routes = {
        "dotmac.platform.tasks.email.*": {"queue": "email"},
        "dotmac.platform.tasks.search.*": {"queue": "search"},
        "dotmac.platform.tasks.storage.*": {"queue": "storage"},
        "dotmac.platform.tasks.analytics.*": {"queue": "analytics"},
    }

    # Beat schedule for periodic tasks
    beat_schedule = {
        "cleanup-expired-sessions": {
            "task": "dotmac.platform.tasks.auth_tasks.cleanup_expired_sessions",
            "schedule": 3600.0,  # Every hour
        },
        "rotate-secrets": {
            "task": "dotmac.platform.tasks.secrets_tasks.check_and_rotate_secrets",
            "schedule": 86400.0,  # Daily
        },
        "sync-search-index": {
            "task": "dotmac.platform.tasks.search_tasks.sync_search_index",
            "schedule": 300.0,  # Every 5 minutes
        },
        "collect-metrics": {
            "task": "dotmac.platform.tasks.monitoring_tasks.collect_system_metrics",
            "schedule": 60.0,  # Every minute
        },
    }

    # Celery beat settings
    beat_scheduler = "celery.beat:PersistentScheduler"
    beat_schedule_filename = "celerybeat-schedule"

    # Error handling
    task_annotations = {
        "*": {
            "rate_limit": "10/s",
            "max_retries": 3,
            "default_retry_delay": 60,
        }
    }

# Create Celery app
app = Celery("dotmac.platform.tasks")
app.config_from_object(CeleryConfig)

if OTEL_ENABLED:  # pragma: no cover - instrumentation side effect
    try:
        CeleryInstrumentor().instrument()
        logger.info("Celery OpenTelemetry instrumentation enabled")
    except Exception as exc:
        logger.warning("Failed to instrument Celery with OpenTelemetry: %s", exc)

# Auto-discover tasks from all platform modules
app.autodiscover_tasks(
    [
        "dotmac.platform.tasks",
        "dotmac.platform.auth",
        "dotmac.platform.secrets",
        "dotmac.platform.communications",
        "dotmac.platform.search",
        "dotmac.platform.file_storage",
        "dotmac.platform.analytics",
        "dotmac.platform.workflow_engines",
    ]
)

# Custom Task class with observability
class ObservableTask(Task):
    """Task with built-in observability."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Execute task with tracing."""
        if OTEL_ENABLED and tracer:
            with tracer.start_as_current_span(
                f"celery.task.{self.name}",
                attributes={
                    "celery.task.name": self.name,
                    "celery.task.id": self.request.id if self.request else None,
                    "celery.task.queue": self.request.routing_key if self.request else None,
                },
            ) as span:
                try:
                    result = super().__call__(*args, **kwargs)
                    span.set_attribute("celery.task.status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("celery.task.status", "failure")
                    span.set_attribute("celery.task.error", str(e))
                    raise
        else:
            return super().__call__(*args, **kwargs)

# Set custom task class
app.Task = ObservableTask

# Signal handlers for monitoring
@task_prerun.connect
def task_prerun_handler(
    sender: Any = None, task_id: str = None, task: Task = None, **kwargs: Any
) -> None:
    """Log task start."""
    import structlog

    logger = get_logger(__name__)
    logger.info(
        "task_started",
        task_name=task.name if task else None,
        task_id=task_id,
    )

    if task and hasattr(task, "request"):
        try:
            task.request._dotmac_start_time = time.perf_counter()
        except Exception:  # pragma: no cover - defensive
            pass

    labels = {
        "task": (task.name if task else getattr(sender, "name", "unknown")) or "unknown",
        "queue": (getattr(getattr(task, "request", None), "delivery_info", {}) or {}).get(
            "routing_key", "default"
        ),
    }
    _record_metric("celery_task_started_total", labels=labels)

@task_postrun.connect
def task_postrun_handler(
    sender: Any = None,
    task_id: str = None,
    task: Task = None,
    state: str = None,
    **kwargs: Any,
) -> None:
    """Log task completion."""
    import structlog

    logger = get_logger(__name__)
    logger.info(
        "task_completed",
        task_name=task.name if task else None,
        task_id=task_id,
        state=state,
    )

    labels = {
        "task": (task.name if task else getattr(sender, "name", "unknown")) or "unknown",
        "queue": (getattr(getattr(task, "request", None), "delivery_info", {}) or {}).get(
            "routing_key", "default"
        ),
        "state": state or "unknown",
    }

    if task and hasattr(task, "request"):
        start_time = getattr(task.request, "_dotmac_start_time", None)
        if isinstance(start_time, float):
            duration_ms = (time.perf_counter() - start_time) * 1000
            _record_metric(
                "celery_task_duration_ms",
                value=duration_ms,
                labels={k: v for k, v in labels.items() if k != "state"},
            )

@task_success.connect
def task_success_handler(sender: Any = None, result: Any = None, **kwargs: Any) -> None:
    """Track successful task execution."""
    delivery_info = getattr(getattr(sender, "request", None), "delivery_info", {}) or {}
    labels = {
        "task": sender.name if sender else "unknown",
        "queue": delivery_info.get("routing_key", "default"),
    }
    _record_metric("celery_task_completed_total", labels=labels)

@task_failure.connect
def task_failure_handler(
    sender: Any = None,
    task_id: str = None,
    exception: Exception = None,
    traceback: Any = None,
    **kwargs: Any,
) -> None:
    """Track and log task failures."""
    import structlog

    logger = get_logger(__name__)
    logger.error(
        "task_failed",
        task_name=sender.name if sender else None,
        task_id=task_id,
        error=str(exception),
    )
    delivery_info = getattr(getattr(sender, "request", None), "delivery_info", {}) or {}
    labels = {
        "task": sender.name if sender else "unknown",
        "queue": delivery_info.get("routing_key", "default"),
        "error": type(exception).__name__ if exception else "unknown",
    }
    _record_metric("celery_task_failed_total", labels=labels)

@task_retry.connect
def task_retry_handler(
    sender: Any = None,
    reason: Any = None,
    request: Any = None,
    **kwargs: Any,
) -> None:
    """Track task retries."""
    import structlog

    logger = get_logger(__name__)
    logger.warning(
        "task_retry",
        task_name=sender.name if sender else None,
        task_id=request.id if request else None,
        reason=str(reason),
        retry_count=request.retries if request else 0,
    )

    delivery_info = getattr(request, "delivery_info", {}) or {}
    labels = {
        "task": sender.name if sender else "unknown",
        "queue": delivery_info.get("routing_key", "default"),
    }
    _record_metric("celery_task_retried_total", labels=labels)

@worker_ready.connect
def worker_ready_handler(sender: Any = None, **kwargs: Any) -> None:
    """Initialize worker with instrumentation."""
    import structlog

    logger = get_logger(__name__)
    logger.info("celery_worker_ready", hostname=sender.hostname if sender else None)

    # Ensure metrics registry is initialised
    _get_metrics_registry()

# Health check task
@app.task(name="dotmac.platform.tasks.health_check")
def health_check() -> dict[str, Any]:
    """Health check task for monitoring."""
    return {
        "status": "healthy",
        "service": "celery-worker",
        "timestamp": __import__("datetime").datetime.now(UTC).isoformat(),
    }

if __name__ == "__main__":
    app.start()
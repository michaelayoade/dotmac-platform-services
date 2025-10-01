"""
Celery application configuration with automatic OpenTelemetry instrumentation.

This module provides a properly configured Celery instance that automatically
enables tracing and metrics when the application starts.
"""

from celery import Celery
from kombu import Queue

from dotmac.platform.settings import settings
from dotmac.platform.tasks import init_celery_instrumentation

# Create Celery application
celery_app = Celery(
    "dotmac_platform",
    broker=settings.celery.broker_url,
    backend=settings.celery.result_backend,
    include=["dotmac.platform.tasks"]  # Auto-discover task modules
)

# Configure Celery settings
celery_app.conf.update(
    # Task routing
    task_routes={
        "dotmac.platform.tasks.*": {"queue": "default"},
    },

    # Queue configuration
    task_default_queue="default",
    task_queues=(
        Queue("default", routing_key="default"),
        Queue("high_priority", routing_key="high_priority"),
        Queue("low_priority", routing_key="low_priority"),
    ),

    # Task execution settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task result settings
    result_expires=3600,  # 1 hour
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes

    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,

    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)


# Auto-initialize OpenTelemetry instrumentation when worker starts
@celery_app.on_after_configure.connect
def setup_celery_instrumentation(sender, **kwargs):
    """Setup OpenTelemetry instrumentation for Celery workers."""
    try:
        init_celery_instrumentation()
    except Exception as e:
        # Log error but don't fail worker startup
        import structlog
        logger = structlog.get_logger(__name__)
        logger.warning(
            "celery.instrumentation.failed",
            error=str(e),
            message="Celery worker started without OpenTelemetry instrumentation"
        )


# Log worker startup
@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    """Configure any periodic tasks here."""
    import structlog
    logger = structlog.get_logger(__name__)
    logger.info(
        "celery.worker.configured",
        broker=settings.celery.broker_url,
        backend=settings.celery.result_backend,
        queues=["default", "high_priority", "low_priority"]
    )


if __name__ == "__main__":
    # For running worker directly: python -m dotmac.platform.celery_app worker
    celery_app.start()
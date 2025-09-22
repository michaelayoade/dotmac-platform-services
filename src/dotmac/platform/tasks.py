"""
Use Celery directly - no custom wrappers.

Standard Celery setup with Redis for idempotency.

Example usage:
    from celery import current_app
    from dotmac.platform.tasks import app, idempotent_task

    @app.task
    def my_task(arg1, arg2):
        return f"Processed {arg1} and {arg2}"

    # Or with idempotency
    @idempotent_task(ttl=3600)
    def unique_task(data):
        return process_data(data)
"""

from celery import Celery
from functools import wraps
import hashlib
import json
from dotmac.platform.settings import settings
from dotmac.platform.caching import redis_client

# Create Celery app with settings
app = Celery(
    'dotmac',
    broker=settings.celery.broker_url,
    backend=settings.celery.result_backend
)

# Configure Celery
app.conf.update(
    task_serializer=settings.celery.task_serializer,
    result_serializer=settings.celery.result_serializer,
    accept_content=settings.celery.accept_content,
    timezone=settings.celery.timezone,
    enable_utc=settings.celery.enable_utc,
    worker_concurrency=settings.celery.worker_concurrency,
    worker_prefetch_multiplier=settings.celery.worker_prefetch_multiplier,
    worker_max_tasks_per_child=settings.celery.worker_max_tasks_per_child,
    task_soft_time_limit=settings.celery.task_soft_time_limit,
    task_time_limit=settings.celery.task_time_limit,
    # Built-in retry configuration
    task_autoretry_for=(Exception,),
    task_retry_kwargs={'max_retries': 3, 'countdown': 5},
)

# Auto-discover tasks in the platform modules
app.autodiscover_tasks(['dotmac.platform'])


def idempotent_task(ttl: int = 3600):
    """
    Redis-native idempotency decorator.

    Uses Redis SETNX + TTL for deduplication.
    Replaces 305 lines of custom code.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Simple key generation
            key_data = f"{func.__name__}:{args}:{sorted(kwargs.items())}"
            key = f"task:{hashlib.md5(key_data.encode()).hexdigest()}"

            if not redis_client:
                return func(*args, **kwargs)

            # Redis SETNX with TTL - atomic operation
            if redis_client.set(key, "1", nx=True, ex=ttl):
                try:
                    result = func(*args, **kwargs)
                    redis_client.setex(f"{key}:result", ttl, json.dumps(result))
                    return result
                except Exception:
                    redis_client.delete(key)  # Allow retry on failure
                    raise

            # Return cached result or None if still processing
            cached = redis_client.get(f"{key}:result")
            return json.loads(cached) if cached else None

        return wrapper
    return decorator


# Alternative: celery-once package
# from celery_once import QueueOnce
# @app.task(base=QueueOnce)
# def deduplicated_task(param): ...


# Export for direct use
__all__ = ['app', 'idempotent_task']
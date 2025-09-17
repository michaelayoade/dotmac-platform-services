"""
Lightweight task decorators for DotMac services.

These decorators provide a stable import path (dotmac.tasks.decorators) used by
management and other packages without imposing a specific task runner.

If optional dependencies like 'tenacity' are installed, retry behavior is
enhanced automatically. Otherwise, safe no-op fallbacks are provided.
"""

from __future__ import annotations

import functools

from collections.abc import Callable
from typing import Any

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

try:  # Optional retry support
    from tenacity import retry as _retry
    from tenacity import stop_after_attempt as _stop_after_attempt

    def retry(*r_args: Any, **r_kwargs: Any):  # type: ignore[misc]
        # Normalize primitive stop values to a proper tenacity strategy
        stop = r_kwargs.get("stop")
        if isinstance(stop, int):
            r_kwargs["stop"] = _stop_after_attempt(stop)
        # Ensure original exception is re-raised after retries to match tests
        r_kwargs.setdefault("reraise", True)
        return _retry(*r_args, **r_kwargs)

except Exception:  # pragma: no cover - fallback

    def retry(*r_args: Any, **r_kwargs: Any):  # type: ignore[misc]
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any):
                tries = int(r_kwargs.get("stop", 1)) or 1
                last_exc: BaseException | None = None
                for _ in range(max(1, tries)):
                    try:
                        return func(*args, **kwargs)
                    except BaseException as e:  # noqa: BLE001
                        last_exc = e
                        logger.warning("retry(): attempt failed: %s", e)
                if last_exc:
                    raise last_exc
                return None

            return wrapper

        # Called as @retry without params
        if r_args and callable(r_args[0]) and not r_kwargs:
            return decorator(r_args[0])
        return decorator

def task(_func: Callable[..., Any] | None = None, *, name: str | None = None):
    """Generic task decorator (no runtime binding).

    Attaches metadata for schedulers/runners to pick up dynamically.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        func.__dotmac_task__ = True
        if name:
            func.__dotmac_task_name__ = name

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            logger.debug("task(): running %s", getattr(func, "__name__", str(func)))
            return func(*args, **kwargs)

        return wrapper

    if _func is not None:
        return decorator(_func)
    return decorator

def periodic_task(
    _func: Callable[..., Any] | None = None,
    *,
    schedule: str | None = None,
    name: str | None = None,
):
    """Periodic task decorator.

    - schedule: cron or human string (interpreted by the chosen runner)
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        func.__dotmac_task__ = True
        func.__dotmac_periodic__ = True
        if name:
            func.__dotmac_task_name__ = name
        if schedule:
            func.__dotmac_task_schedule__ = schedule

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            logger.debug(
                "periodic_task(): running %s (schedule=%s)",
                getattr(func, "__name__", str(func)),
                schedule,
            )
            return func(*args, **kwargs)

        return wrapper

    if _func is not None:
        return decorator(_func)
    return decorator

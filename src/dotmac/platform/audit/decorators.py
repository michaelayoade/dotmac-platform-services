"""
Decorators for audit logging.
"""

import asyncio
import functools
from collections.abc import Callable
from typing import Any, Optional

import structlog

from .logger import get_audit_logger
from .models import AuditActor, AuditEventType, AuditOutcome, AuditResource, AuditSeverity

logger = structlog.get_logger(__name__)


def log_security_event(
    event_type: AuditEventType,
    message: Optional[str] = None,
    severity: AuditSeverity = AuditSeverity.MEDIUM,
    resource_type: str = "function",
) -> Callable:
    """
    Decorator to automatically log security events for function calls.

    Args:
        event_type: Type of security event
        message: Custom message (optional, will use function name if not provided)
        severity: Event severity level
        resource_type: Type of resource being accessed
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            audit_logger = get_audit_logger()
            if not audit_logger:
                logger.warning("No audit logger available, skipping security event logging")
                return await func(*args, **kwargs)

            # Create resource
            resource = AuditResource(
                resource_type=resource_type,
                resource_id=func.__name__,
                resource_name=f"{func.__module__}.{func.__name__}",
            )

            # Extract user context if available
            actor = None
            for arg in args:
                if hasattr(arg, "user") and arg.user:
                    actor = AuditActor(
                        actor_id=str(arg.user.id),
                        actor_type="user",
                        tenant_id=getattr(arg.user, "tenant_id", None),
                    )
                    break

            outcome = AuditOutcome.SUCCESS
            error_message = None

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                outcome = AuditOutcome.FAILURE
                error_message = str(e)
                raise
            finally:
                # Log security event
                event_message = message or f"Function {func.__name__} executed"
                if error_message:
                    event_message += f" with error: {error_message}"

                try:
                    await audit_logger.log_security_event(
                        event_type=event_type,
                        message=event_message,
                        actor_id=actor.actor_id if actor else None,
                        resource_id=resource.resource_id,
                        severity=severity,
                        outcome=outcome,
                    )
                except Exception as e:
                    logger.error("Failed to log security event", error=str(e))

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            audit_logger = get_audit_logger()
            if not audit_logger:
                logger.warning("No audit logger available, skipping security event logging")
                return func(*args, **kwargs)

            # Create resource
            resource = AuditResource(
                resource_type=resource_type,
                resource_id=func.__name__,
                resource_name=f"{func.__module__}.{func.__name__}",
            )

            # Extract user context if available
            actor = None
            for arg in args:
                if hasattr(arg, "user") and arg.user:
                    actor = AuditActor(
                        actor_id=str(arg.user.id),
                        actor_type="user",
                        tenant_id=getattr(arg.user, "tenant_id", None),
                    )
                    break

            outcome = AuditOutcome.SUCCESS
            error_message = None

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                outcome = AuditOutcome.FAILURE
                error_message = str(e)
                raise
            finally:
                # Log security event asynchronously
                event_message = message or f"Function {func.__name__} executed"
                if error_message:
                    event_message += f" with error: {error_message}"

                try:
                    # Run async logging in background
                    asyncio.create_task(
                        audit_logger.log_security_event(
                            event_type=event_type,
                            message=event_message,
                            actor_id=actor.actor_id if actor else None,
                            resource_id=resource.resource_id,
                            severity=severity,
                            outcome=outcome,
                        )
                    )
                except Exception as e:
                    logger.error("Failed to log security event", error=str(e))

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

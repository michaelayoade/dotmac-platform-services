"""
Access control decorators for securing functions and endpoints.
"""

import asyncio
import functools
from collections.abc import Callable
from typing import Any, Optional

import structlog
from fastapi import HTTPException, Request, status

from .manager import AccessControlManager
from .models import AccessRequest, ActionType, ResourceType

logger = structlog.get_logger(__name__)


def require_permission(
    resource_type: ResourceType,
    action: ActionType,
    resource_id: Optional[str] = None,
    manager: Optional[AccessControlManager] = None,
) -> Callable:
    """
    Decorator to require specific permission for function access.

    Args:
        resource_type: Type of resource being accessed
        action: Action being performed
        resource_id: Specific resource ID (optional)
        manager: Access control manager instance
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Extract request and user info from FastAPI context
            request: Optional[Request] = None
            user_id: Optional[str] = None

            # Look for Request object in args/kwargs
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                for value in kwargs.values():
                    if isinstance(value, Request):
                        request = value
                        break

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request context not available for permission check",
                )

            # Extract user from request state
            user = getattr(request.state, "user", None)
            if not user:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

            user_id = getattr(user, "id", None) or str(user)

            # Create access request
            access_request = AccessRequest(
                subject_type="user",
                subject_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id or "*",
                action=action,
                context={
                    "endpoint": func.__name__,
                    "method": request.method,
                    "path": str(request.url.path),
                },
            )

            # Check permission
            if manager:
                decision = await manager.check_permission(access_request)

                if decision.decision != "allow":
                    logger.warning(
                        "Access denied",
                        user_id=user_id,
                        resource_type=resource_type.value,
                        action=action.value,
                        reason=decision.reason,
                    )

                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN, detail=f"Access denied: {decision.reason}"
                    )

            # Continue with function execution
            return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

        return wrapper

    return decorator


async def check_access(
    user_id: str,
    resource_type: ResourceType,
    action: ActionType,
    resource_id: Optional[str] = None,
    context: Optional[dict[str, Any]] = None,
    manager: Optional[AccessControlManager] = None,
) -> bool:
    """
    Check if user has access to perform action on resource.

    Args:
        user_id: ID of the user
        resource_type: Type of resource
        action: Action to perform
        resource_id: Specific resource ID
        context: Additional context
        manager: Access control manager

    Returns:
        True if access is allowed, False otherwise
    """

    if not manager:
        logger.warning("No access control manager provided, allowing access")
        return True

    access_request = AccessRequest(
        subject_type="user",
        subject_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id or "*",
        action=action,
        context=context or {},
    )

    decision = await manager.check_permission(access_request)
    return decision.decision == "allow"

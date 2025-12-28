"""
Authentication dependencies for FastAPI routes.

These can be used to protect endpoints that require authentication.
"""

from typing import Any

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

from dotmac.platform.auth.core import UserInfo, get_current_user, get_current_user_optional

logger = structlog.get_logger(__name__)

# Security scheme for bearer token
security = HTTPBearer(auto_error=False)


async def require_auth(user: UserInfo = Depends(get_current_user)) -> UserInfo:
    """Require authentication."""
    return user


async def require_user(user: UserInfo = Depends(get_current_user)) -> UserInfo:
    """Backward-compatible alias for authenticated user requirement."""
    return user


def require_admin(user: UserInfo = Depends(get_current_user)) -> UserInfo:
    """Require admin role."""
    if "admin" not in user.roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def require_scopes(*scopes: str) -> Any:
    """Require specific scopes/permissions."""

    def check_scopes(user: UserInfo = Depends(get_current_user)) -> UserInfo:
        if not any(scope in user.permissions for scope in scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return user

    return check_scopes


def require_roles(*roles: str) -> Any:
    """Require specific roles."""

    def check_roles(user: UserInfo = Depends(get_current_user)) -> UserInfo:
        if not any(role in user.roles for role in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role permissions"
            )
        return user

    return check_roles


# Alias for backward compatibility
CurrentUser = UserInfo


async def require_active_subscription(
    user: UserInfo = Depends(get_current_user),
) -> UserInfo:
    """
    Require an active subscription for subscription-gated endpoints.

    USE SPARINGLY - Only apply to:
    - Premium features
    - API rate limit increases
    - Add-on services
    - Subscription-gated functionality

    DO NOT apply to:
    - Admin routes (/api/v1/admin/*)
    - Health/status endpoints
    - Billing management (users must be able to pay!)
    - Support/ticketing
    - Basic read-only operations

    This dependency checks if the user's tenant has a suspended subscription
    due to non-payment and returns HTTP 402 Payment Required if so.

    Platform admins (users without tenant_id) bypass this check.
    """
    from dotmac.platform.billing.subscriptions.models import SubscriptionStatus
    from dotmac.platform.billing.subscriptions.service import SubscriptionService
    from dotmac.platform.database import get_async_session_context

    # Platform admins bypass subscription check
    if not user.tenant_id:
        return user

    try:
        async with get_async_session_context() as session:
            service = SubscriptionService(session)
            subscription = await service.get_tenant_subscription(user.tenant_id)

            if subscription and subscription.status == SubscriptionStatus.PAUSED:
                # Check if paused due to grace period expiration
                is_payment_issue = subscription.metadata.get("pause_reason") == "grace_period_expired"

                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail={
                        "error": "subscription_suspended",
                        "message": (
                            "Your subscription is suspended due to non-payment. "
                            "Please update your payment method to restore access."
                        ),
                        "grace_period_expired": is_payment_issue,
                        "billing_url": "/portal/billing",
                        "subscription_status": subscription.status.value,
                    },
                )

    except HTTPException:
        # Re-raise HTTP exceptions (402)
        raise
    except Exception as e:
        # Log but don't block on subscription check failures
        # This ensures the system degrades gracefully
        logger.warning(
            "subscription.check.failed",
            tenant_id=user.tenant_id,
            error=str(e),
        )

    return user


__all__ = [
    "require_auth",
    "require_user",
    "require_admin",
    "require_scopes",
    "require_roles",
    "require_active_subscription",
    "get_current_user",
    "get_current_user_optional",
    "security",
    "CurrentUser",
    "UserInfo",
]

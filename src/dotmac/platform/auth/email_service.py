"""Auth email utilities using Jinja2 templates.

This module provides auth-related email sending functionality.
Templates are rendered using the TenantAwareTemplateService with Jinja2.
"""

from __future__ import annotations

import secrets
import inspect

import structlog

from dotmac.platform.core.caching import get_redis

from ..communications.template_context import TemplateContextBuilder
from ..communications.template_service import (
    BrandingConfig,
    get_tenant_template_service,
)
from ..settings import settings

logger = structlog.get_logger(__name__)


async def send_welcome_email(
    email: str,
    user_name: str,
    branding: BrandingConfig | None = None,
) -> bool:
    """
    Send welcome email to new user using Jinja2 templates.

    Args:
        email: User email address
        user_name: User's display name
        branding: Optional branding configuration for customization

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        from ..communications.email_service import EmailMessage, get_email_service

        app_name = getattr(settings, "app_name", "DotMac Platform")

        template_service = get_tenant_template_service()
        context = TemplateContextBuilder.welcome(
            user_name=user_name,
            email=email,
            app_name=app_name,
        )
        rendered = await template_service.render_email(
            template_key="email.auth.welcome",
            context=context,
            branding=branding,
        )

        message = EmailMessage(
            to=[email],
            subject=rendered.subject,
            text_body=rendered.text_body,
            html_body=rendered.html_body,
        )

        service = get_email_service()
        response = await service.send_email(message)
        return response.status == "sent"

    except Exception as e:
        logger.error("Failed to send welcome email", email=email, error=str(e))
        return False


async def send_password_reset_email(
    email: str,
    user_name: str,
    branding: BrandingConfig | None = None,
) -> tuple[bool, str | None]:
    """
    Send password reset email using Jinja2 templates.

    Args:
        email: User email address
        user_name: User's display name
        branding: Optional branding configuration for customization

    Returns:
        Tuple of (success, reset_token)
    """
    try:
        app_name = getattr(settings, "app_name", "DotMac Platform")

        # Generate reset token
        reset_token = secrets.token_urlsafe(32)

        # Store token in Redis with 1 hour expiry
        redis_client = get_redis()
        token_key = f"password_reset:{reset_token}"
        if redis_client is None:
            logger.warning("Password reset email skipped: Redis unavailable", email=email)
            return False, None
        redis_client.setex(token_key, 3600, email)  # 1 hour expiry

        # Create reset link using centralized frontend URL
        frontend_url = getattr(
            getattr(settings, "external_services", None),
            "frontend_admin_url",
            "https://localhost:3001",
        )
        reset_link = f"{frontend_url}/reset-password?token={reset_token}"

        from ..communications.email_service import EmailMessage, get_email_service

        template_service = get_tenant_template_service()
        context = TemplateContextBuilder.password_reset(
            user_name=user_name,
            reset_link=reset_link,
            expiry_hours=1,
            app_name=app_name,
        )
        rendered = await template_service.render_email(
            template_key="email.auth.password_reset",
            context=context,
            branding=branding,
        )

        message = EmailMessage(
            to=[email],
            subject=rendered.subject,
            text_body=rendered.text_body,
            html_body=rendered.html_body,
        )

        service = get_email_service()
        response = await service.send_email(message)
        success = response.status == "sent"
        return success, reset_token if success else None

    except Exception as e:
        logger.error("Failed to send password reset email", email=email, error=str(e))
        return False, None


async def verify_reset_token(token: str) -> str | None:
    """
    Verify password reset token and return associated email.

    Args:
        token: Reset token to verify

    Returns:
        Email address if token is valid, None otherwise
    """
    try:
        redis_client = get_redis()
        if redis_client is None:
            logger.warning("Password reset token verification skipped: Redis unavailable")
            return None

        token_key = f"password_reset:{token}"
        email = redis_client.get(token_key)
        if inspect.isawaitable(email):
            email = await email

        if email:
            # Token is valid, delete it (one-time use)
            delete_result = redis_client.delete(token_key)
            if inspect.isawaitable(delete_result):
                await delete_result
            return email.decode("utf-8") if isinstance(email, bytes) else email

        return None

    except Exception as e:
        logger.error("Failed to verify reset token", token=token[:10], error=str(e))
        return None


async def send_verification_email(
    email: str,
    user_name: str,
    verification_url: str,
    branding: BrandingConfig | None = None,
) -> bool:
    """
    Send email verification link using Jinja2 templates.

    Args:
        email: User email address
        user_name: User's display name
        verification_url: URL containing verification token
        branding: Optional branding configuration for customization

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        app_name = getattr(settings, "app_name", "DotMac Platform")

        from ..communications.email_service import EmailMessage, get_email_service

        template_service = get_tenant_template_service()
        context = TemplateContextBuilder.verification(
            user_name=user_name,
            verification_url=verification_url,
            expiry_hours=24,
            app_name=app_name,
        )
        rendered = await template_service.render_email(
            template_key="email.auth.verification",
            context=context,
            branding=branding,
        )

        message = EmailMessage(
            to=[email],
            subject=rendered.subject,
            text_body=rendered.text_body,
            html_body=rendered.html_body,
        )

        service = get_email_service()
        response = await service.send_email(message)
        return response.status == "sent"

    except Exception as e:
        logger.error("Failed to send verification email", email=email, error=str(e))
        return False


async def send_password_reset_success_email(
    email: str,
    user_name: str,
    branding: BrandingConfig | None = None,
) -> bool:
    """
    Send password reset success confirmation email using Jinja2 templates.

    Args:
        email: User email address
        user_name: User's display name
        branding: Optional branding configuration for customization

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        app_name = getattr(settings, "app_name", "DotMac Platform")

        from ..communications.email_service import EmailMessage, get_email_service

        template_service = get_tenant_template_service()
        context = TemplateContextBuilder.password_reset_success(
            user_name=user_name,
            app_name=app_name,
        )
        rendered = await template_service.render_email(
            template_key="email.auth.password_reset_success",
            context=context,
            branding=branding,
        )

        message = EmailMessage(
            to=[email],
            subject=rendered.subject,
            text_body=rendered.text_body,
            html_body=rendered.html_body,
        )

        service = get_email_service()
        response = await service.send_email(message)
        return response.status == "sent"

    except Exception as e:
        logger.error("Failed to send password reset success email", email=email, error=str(e))
        return False


# Export functions for use by auth router
__all__ = [
    "send_welcome_email",
    "send_password_reset_email",
    "send_verification_email",
    "verify_reset_token",
    "send_password_reset_success_email",
    "get_auth_email_service",
]


class AuthEmailServiceFacade:
    """Lightweight facade retaining the old service-like interface for tests."""

    async def send_welcome_email(self, email: str, user_name: str) -> bool:
        return await send_welcome_email(email, user_name)

    async def send_password_reset_email(
        self, email: str, user_name: str
    ) -> tuple[bool, str | None]:
        return await send_password_reset_email(email, user_name)

    async def send_verification_email(
        self, email: str, user_name: str, verification_url: str
    ) -> bool:
        return await send_verification_email(email, user_name, verification_url)

    async def verify_reset_token(self, token: str) -> str | None:
        return await verify_reset_token(token)

    async def send_password_reset_success_email(self, email: str, user_name: str) -> bool:
        return await send_password_reset_success_email(email, user_name)


def get_auth_email_service() -> AuthEmailServiceFacade:
    """Provide a facade compatible with legacy dependency expectations."""

    return AuthEmailServiceFacade()

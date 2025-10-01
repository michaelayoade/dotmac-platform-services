"""Simplified auth email utilities using communications module directly."""

import secrets
from typing import Optional, Tuple

import structlog

from ..caching import get_redis
from ..settings import settings

logger = structlog.get_logger(__name__)


async def send_welcome_email(email: str, user_name: str) -> bool:
    """
    Send welcome email to new user using communications module.

    Args:
        email: User email address
        user_name: User's display name

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        from ..communications.email_service import EmailMessage, get_email_service

        app_name = getattr(settings, 'app_name', 'DotMac Platform')
        subject = f"Welcome to {app_name}!"

        content = f"""
Hi {user_name},

Welcome to {app_name}! Your account has been successfully created.

Your registered email: {email}

To get started:
1. Complete your profile
2. Explore our features
3. Configure your settings

If you didn't create this account, please contact support immediately.

Best regards,
The {app_name} Team
""".strip()

        # Create message
        message = EmailMessage(
            to=[email],
            subject=subject,
            text_body=content,
            html_body=content.replace('\n', '<br>')
        )

        # Send using async communications service
        service = get_email_service()
        response = await service.send_email(message)
        return response.status == "sent"

    except Exception as e:
        logger.error("Failed to send welcome email", email=email, error=str(e))
        return False


async def send_password_reset_email(email: str, user_name: str) -> Tuple[bool, Optional[str]]:
    """
    Send password reset email using communications module.

    Args:
        email: User email address
        user_name: User's display name

    Returns:
        Tuple of (success, reset_token)
    """
    try:
        app_name = getattr(settings, 'app_name', 'DotMac Platform')

        # Generate reset token
        reset_token = secrets.token_urlsafe(32)

        # Store token in Redis with 1 hour expiry
        redis = get_redis()
        token_key = f"password_reset:{reset_token}"
        redis.setex(token_key, 3600, email)  # 1 hour expiry

        # Create reset link (placeholder - should be actual frontend URL)
        reset_link = f"https://localhost:3001/reset-password?token={reset_token}"

        subject = f"Reset Your Password - {app_name}"

        content = f"""
Hi {user_name},

We received a request to reset your password for your {app_name} account.

Click the link below to reset your password:
{reset_link}

This link will expire in 1 hour.

If you didn't request a password reset, you can safely ignore this email.

Best regards,
The {app_name} Team
""".strip()

        from ..communications.email_service import EmailMessage, get_email_service

        # Create message
        message = EmailMessage(
            to=[email],
            subject=subject,
            text_body=content,
            html_body=content.replace('\n', '<br>')
        )

        # Send using async communications service
        service = get_email_service()
        response = await service.send_email(message)
        success = response.status == "sent"
        return success, reset_token if success else None

    except Exception as e:
        logger.error("Failed to send password reset email", email=email, error=str(e))
        return False, None


def verify_reset_token(token: str) -> Optional[str]:
    """
    Verify password reset token and return associated email.

    Args:
        token: Reset token to verify

    Returns:
        Email address if token is valid, None otherwise
    """
    try:
        redis = get_redis()
        token_key = f"password_reset:{token}"
        email = redis.get(token_key)

        if email:
            # Token is valid, delete it (one-time use)
            redis.delete(token_key)
            return email.decode('utf-8') if isinstance(email, bytes) else email

        return None

    except Exception as e:
        logger.error("Failed to verify reset token", token=token[:10], error=str(e))
        return None


async def send_password_reset_success_email(email: str, user_name: str) -> bool:
    """
    Send password reset success confirmation email using communications module.

    Args:
        email: User email address
        user_name: User's display name

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        app_name = getattr(settings, 'app_name', 'DotMac Platform')
        subject = f"Your Password Has Been Reset - {app_name}"

        content = f"""
Hi {user_name},

Your password has been successfully reset.

If you didn't make this change, please contact our support team immediately.

For security reasons, we recommend:
- Using a strong, unique password
- Enabling two-factor authentication
- Regularly reviewing your account activity

Best regards,
The {app_name} Team
""".strip()

        from ..communications.email_service import EmailMessage, get_email_service

        # Create message
        message = EmailMessage(
            to=[email],
            subject=subject,
            text_body=content,
            html_body=content.replace('\n', '<br>')
        )

        # Send using async communications service
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
    ) -> Tuple[bool, Optional[str]]:
        return await send_password_reset_email(email, user_name)

    def verify_reset_token(self, token: str) -> Optional[str]:
        return verify_reset_token(token)

    async def send_password_reset_success_email(self, email: str, user_name: str) -> bool:
        return await send_password_reset_success_email(email, user_name)


def get_auth_email_service() -> AuthEmailServiceFacade:
    """Provide a facade compatible with legacy dependency expectations."""

    return AuthEmailServiceFacade()

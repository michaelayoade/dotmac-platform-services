"""Email service for authentication-related notifications."""

import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import structlog
from cryptography.fernet import Fernet
from pydantic import BaseModel, EmailStr

from ..caching import get_redis
from ..communications import (
    NotificationRequest,
    NotificationResponse,
    NotificationStatus,
    NotificationTemplate,
    NotificationType,
    get_notification_service,
)
from ..settings import settings

logger = structlog.get_logger(__name__)


class EmailTemplates:
    """Email templates for authentication."""

    REGISTRATION_WELCOME = NotificationTemplate(
        id="auth_registration_welcome",
        name="Registration Welcome",
        type=NotificationType.EMAIL,
        subject_template="Welcome to {{app_name}}!",
        content_template="""
Hi {{user_name}},

Welcome to {{app_name}}! Your account has been successfully created.

Your registered email: {{user_email}}

To get started:
1. Complete your profile
2. Explore our features
3. Configure your settings

If you didn't create this account, please contact support immediately.

Best regards,
The {{app_name}} Team
        """.strip(),
    )

    PASSWORD_RESET = NotificationTemplate(
        id="auth_password_reset",
        name="Password Reset",
        type=NotificationType.EMAIL,
        subject_template="Reset Your Password - {{app_name}}",
        content_template="""
Hi {{user_name}},

We received a request to reset your password for your {{app_name}} account.

Click the link below to reset your password:
{{reset_link}}

This link will expire in {{expiry_hours}} hours.

If you didn't request a password reset, you can safely ignore this email.

Best regards,
The {{app_name}} Team
        """.strip(),
    )

    PASSWORD_RESET_SUCCESS = NotificationTemplate(
        id="auth_password_reset_success",
        name="Password Reset Success",
        type=NotificationType.EMAIL,
        subject_template="Your Password Has Been Reset - {{app_name}}",
        content_template="""
Hi {{user_name}},

Your password has been successfully reset.

If you didn't make this change, please contact our support team immediately.

For security reasons, we recommend:
- Using a strong, unique password
- Enabling two-factor authentication
- Regularly reviewing your account activity

Best regards,
The {{app_name}} Team
        """.strip(),
    )

    EMAIL_VERIFICATION = NotificationTemplate(
        id="auth_email_verification",
        name="Email Verification",
        type=NotificationType.EMAIL,
        subject_template="Verify Your Email - {{app_name}}",
        content_template="""
Hi {{user_name}},

Please verify your email address to complete your registration.

Click the link below to verify your email:
{{verification_link}}

Or enter this code: {{verification_code}}

This link will expire in {{expiry_hours}} hours.

Best regards,
The {{app_name}} Team
        """.strip(),
    )

    LOGIN_ALERT = NotificationTemplate(
        id="auth_login_alert",
        name="Login Alert",
        type=NotificationType.EMAIL,
        subject_template="New Login to Your Account - {{app_name}}",
        content_template="""
Hi {{user_name}},

We detected a new login to your account:

Time: {{login_time}}
Location: {{login_location}}
Device: {{login_device}}
IP Address: {{login_ip}}

If this was you, no action is needed.

If this wasn't you, please:
1. Change your password immediately
2. Review your recent account activity
3. Contact support if you notice any unauthorized access

Best regards,
The {{app_name}} Team
        """.strip(),
    )


class PasswordResetToken(BaseModel):
    """Password reset token model."""

    token: str
    email: EmailStr
    expires_at: datetime
    used: bool = False


class SecureTokenStorage:
    """Secure distributed storage for password reset tokens using Redis and encryption."""

    def __init__(self):
        """Initialize secure token storage with encryption key."""
        # Get or generate encryption key
        self._init_encryption()
        self._token_prefix = "password_reset:"
        self._token_ttl = 3600  # 1 hour TTL for tokens
        self._redis_client = None
        self._fallback_store: Dict[str, dict] = {}

    def _init_encryption(self):
        """Initialize Fernet encryption with a secure key."""
        # In production, this should come from a secure key management system
        # For now, we'll use a key from environment or generate one
        import os
        encryption_key = os.environ.get("AUTH__RESET_TOKEN_ENCRYPTION_KEY")

        if not encryption_key:
            # Generate a new key if not configured
            encryption_key = Fernet.generate_key()
            logger.warning(
                "No encryption key configured for reset tokens. "
                "Generated temporary key - configure AUTH__RESET_TOKEN_ENCRYPTION_KEY in production"
            )
        else:
            encryption_key = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key

        self._fernet = Fernet(encryption_key)

    def _hash_token(self, token: str) -> str:
        """Create a secure hash of the token for use as Redis key."""
        return hashlib.sha256(token.encode()).hexdigest()

    def _encrypt_data(self, data: dict) -> bytes:
        """Encrypt sensitive token data."""
        json_data = json.dumps(data, default=str)
        return self._fernet.encrypt(json_data.encode())

    def _decrypt_data(self, encrypted_data: bytes) -> dict:
        """Decrypt token data."""
        try:
            decrypted = self._fernet.decrypt(encrypted_data)
            return json.loads(decrypted.decode())
        except Exception as e:
            logger.error("Failed to decrypt token data", error=str(e))
            return None

    def store_token(self, token: str, email: str, expires_at: datetime) -> bool:
        """
        Store password reset token in Redis with encryption.

        Args:
            token: The reset token
            email: User's email address
            expires_at: Token expiration time

        Returns:
            True if stored successfully, False otherwise
        """
        if not self._redis_client:
            self._redis_client = get_redis()

        try:
            # Create token data
            token_data = {
                "email": email,
                "expires_at": expires_at.isoformat(),
                "used": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }

            token_key = f"{self._token_prefix}{self._hash_token(token)}"
            ttl = int((expires_at - datetime.now(timezone.utc)).total_seconds())

            if ttl <= 0:
                logger.warning("Token already expired, not storing", email=email)
                return False

            if self._redis_client:
                encrypted_data = self._encrypt_data(token_data)
                self._redis_client.setex(token_key, ttl, encrypted_data)
                logger.info(
                    "Stored password reset token",
                    email=email,
                    ttl_seconds=ttl
                )
            else:
                # Fallback to in-memory storage for testing environments
                self._fallback_store[token_key] = {
                    "data": token_data,
                    "expires_at": expires_at,
                }
                logger.info(
                    "Stored password reset token in fallback store",
                    email=email,
                    ttl_seconds=ttl
                )
            return True

        except Exception as e:
            logger.error("Failed to store reset token", error=str(e))
            return False

    def get_token(self, token: str) -> Optional[PasswordResetToken]:
        """
        Retrieve and decrypt password reset token from Redis.

        Args:
            token: The reset token to retrieve

        Returns:
            PasswordResetToken if valid, None otherwise
        """
        if not self._redis_client:
            self._redis_client = get_redis()

        try:
            token_key = f"{self._token_prefix}{self._hash_token(token)}"

            if self._redis_client:
                encrypted_data = self._redis_client.get(token_key)

                if not encrypted_data:
                    logger.debug("Token not found", token_hash=self._hash_token(token)[:8])
                    return None

                token_data = self._decrypt_data(encrypted_data)
                if not token_data:
                    return None

                expires_at = datetime.fromisoformat(token_data["expires_at"])
            else:
                fallback_entry = self._fallback_store.get(token_key)
                if not fallback_entry:
                    logger.debug("Fallback token not found", token_hash=self._hash_token(token)[:8])
                    return None
                token_data = fallback_entry["data"]
                expires_at = fallback_entry["expires_at"]

            if expires_at < datetime.now(timezone.utc):
                logger.info("Token expired", email=token_data.get("email"))
                self.invalidate_token(token)
                return None

            return PasswordResetToken(
                token=token,
                email=token_data["email"],
                expires_at=expires_at,
                used=token_data.get("used", False)
            )

        except Exception as e:
            logger.error("Failed to retrieve reset token", error=str(e))
            return None

    def invalidate_token(self, token: str) -> bool:
        """
        Invalidate a password reset token.

        Args:
            token: The token to invalidate

        Returns:
            True if invalidated, False otherwise
        """
        if not self._redis_client:
            self._redis_client = get_redis()

        try:
            token_key = f"{self._token_prefix}{self._hash_token(token)}"
            if self._redis_client:
                result = self._redis_client.delete(token_key)
            else:
                result = 1 if self._fallback_store.pop(token_key, None) else 0
            logger.info("Invalidated reset token", success=bool(result))
            return bool(result)

        except Exception as e:
            logger.error("Failed to invalidate token", error=str(e))
            return False

    def mark_token_used(self, token: str) -> bool:
        """
        Mark a token as used without deleting it (for audit).

        Args:
            token: The token to mark as used

        Returns:
            True if marked successfully, False otherwise
        """
        token_data = self.get_token(token)
        if not token_data:
            return False

        if not self._redis_client:
            self._redis_client = get_redis()

        try:
            updated_data = {
                "email": token_data.email,
                "expires_at": token_data.expires_at.isoformat(),
                "used": True,
                "used_at": datetime.now(timezone.utc).isoformat()
            }

            token_key = f"{self._token_prefix}{self._hash_token(token)}"

            if self._redis_client:
                encrypted_data = self._encrypt_data(updated_data)
                # Keep for audit with short TTL (1 day)
                self._redis_client.setex(token_key, 86400, encrypted_data)
            else:
                self._fallback_store[token_key] = {
                    "data": {
                        "email": token_data.email,
                        "expires_at": token_data.expires_at.isoformat(),
                        "used": True,
                        "used_at": datetime.now(timezone.utc).isoformat()
                    },
                    "expires_at": token_data.expires_at,
                }

            logger.info("Marked token as used", email=token_data.email)
            return True

        except Exception as e:
            logger.error("Failed to mark token as used", error=str(e))
            return False


class AuthEmailService:
    """Email service for authentication-related emails."""

    def __init__(self, app_name: str = "DotMac Platform", base_url: str = "http://localhost:3000"):
        self.app_name = app_name
        self.base_url = base_url
        self.notification_service = get_notification_service()
        # Use secure distributed storage instead of in-memory
        self.token_storage = SecureTokenStorage()
        # Keep verification codes in memory for now (less critical, shorter lived)
        self._verification_codes: Dict[str, str] = {}
        self._initialize_templates()

    def _initialize_templates(self):
        """Initialize email templates."""
        self.notification_service.add_template(EmailTemplates.REGISTRATION_WELCOME)
        self.notification_service.add_template(EmailTemplates.PASSWORD_RESET)
        self.notification_service.add_template(EmailTemplates.PASSWORD_RESET_SUCCESS)
        self.notification_service.add_template(EmailTemplates.EMAIL_VERIFICATION)
        self.notification_service.add_template(EmailTemplates.LOGIN_ALERT)
        logger.info("Initialized auth email templates")

    def send_welcome_email(
        self, email: str, user_name: Optional[str] = None
    ) -> NotificationResponse:
        """Send welcome email after registration."""
        template_data = {
            "app_name": self.app_name,
            "user_name": user_name or email.split("@")[0],
            "user_email": email,
        }

        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient=email,
            subject=f"Welcome to {self.app_name}!",
            content=self._render_template(EmailTemplates.REGISTRATION_WELCOME.content_template, template_data),
            template_id=EmailTemplates.REGISTRATION_WELCOME.id,
            template_data=template_data,
        )

        response = self.notification_service.send(request)
        logger.info(
            "Sent welcome email",
            email=email,
            status=response.status,
            notification_id=response.id,
        )
        return response

    def send_password_reset_email(
        self, email: str, user_name: Optional[str] = None
    ) -> tuple[NotificationResponse, str]:
        """Send password reset email and return reset token."""
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        # Store token using secure storage
        stored = self.token_storage.store_token(
            token=reset_token,
            email=email,
            expires_at=expires_at
        )

        if not stored:
            raise RuntimeError("Failed to store reset token")

        # Create reset link
        reset_link = f"{self.base_url}/reset-password?token={reset_token}"

        template_data = {
            "app_name": self.app_name,
            "user_name": user_name or email.split("@")[0],
            "reset_link": reset_link,
            "expiry_hours": 1,
        }

        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient=email,
            subject=f"Reset Your Password - {self.app_name}",
            content=self._render_template(EmailTemplates.PASSWORD_RESET.content_template, template_data),
            template_id=EmailTemplates.PASSWORD_RESET.id,
            template_data=template_data,
        )

        response = self.notification_service.send(request)
        logger.info(
            "Sent password reset email",
            email=email,
            status=response.status,
            notification_id=response.id,
        )
        return response, reset_token

    def verify_reset_token(self, token: str) -> Optional[str]:
        """Verify password reset token and return email if valid."""
        token_data = self.token_storage.get_token(token)

        if not token_data:
            logger.warning("Invalid reset token", token=token[:8])
            return None

        if token_data.used:
            logger.warning("Reset token already used", token=token[:8])
            return None

        if datetime.now(timezone.utc) > token_data.expires_at:
            logger.warning("Reset token expired", token=token[:8])
            # Invalidate expired token
            self.token_storage.invalidate_token(token)
            return None

        # Mark token as used
        self.token_storage.mark_token_used(token)
        return token_data.email

    def send_password_reset_success_email(
        self, email: str, user_name: Optional[str] = None
    ) -> NotificationResponse:
        """Send email confirming password reset."""
        template_data = {
            "app_name": self.app_name,
            "user_name": user_name or email.split("@")[0],
        }

        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient=email,
            subject=f"Your Password Has Been Reset - {self.app_name}",
            content=self._render_template(EmailTemplates.PASSWORD_RESET_SUCCESS.content_template, template_data),
            template_id=EmailTemplates.PASSWORD_RESET_SUCCESS.id,
            template_data=template_data,
        )

        response = self.notification_service.send(request)
        logger.info(
            "Sent password reset success email",
            email=email,
            status=response.status,
            notification_id=response.id,
        )
        return response

    def send_email_verification(
        self, email: str, user_name: Optional[str] = None
    ) -> tuple[NotificationResponse, str]:
        """Send email verification and return verification code."""
        # Generate verification code
        verification_code = "".join([str(secrets.randbelow(10)) for _ in range(6)])
        self._verification_codes[email] = verification_code

        # Create verification link
        verification_link = f"{self.base_url}/verify-email?email={email}&code={verification_code}"

        template_data = {
            "app_name": self.app_name,
            "user_name": user_name or email.split("@")[0],
            "verification_link": verification_link,
            "verification_code": verification_code,
            "expiry_hours": 24,
        }

        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient=email,
            subject=f"Verify Your Email - {self.app_name}",
            content=self._render_template(EmailTemplates.EMAIL_VERIFICATION.content_template, template_data),
            template_id=EmailTemplates.EMAIL_VERIFICATION.id,
            template_data=template_data,
        )

        response = self.notification_service.send(request)
        logger.info(
            "Sent email verification",
            email=email,
            status=response.status,
            notification_id=response.id,
        )
        return response, verification_code

    def verify_email_code(self, email: str, code: str) -> bool:
        """Verify email verification code."""
        stored_code = self._verification_codes.get(email)
        if stored_code and stored_code == code:
            del self._verification_codes[email]  # Remove after successful verification
            return True
        return False

    def send_login_alert(
        self,
        email: str,
        user_name: Optional[str] = None,
        login_ip: str = "Unknown",
        login_device: str = "Unknown",
        login_location: str = "Unknown",
    ) -> NotificationResponse:
        """Send login alert email."""
        template_data = {
            "app_name": self.app_name,
            "user_name": user_name or email.split("@")[0],
            "login_time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "login_location": login_location,
            "login_device": login_device,
            "login_ip": login_ip,
        }

        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient=email,
            subject=f"New Login to Your Account - {self.app_name}",
            content=self._render_template(EmailTemplates.LOGIN_ALERT.content_template, template_data),
            template_id=EmailTemplates.LOGIN_ALERT.id,
            template_data=template_data,
        )

        response = self.notification_service.send(request)
        logger.info(
            "Sent login alert",
            email=email,
            status=response.status,
            notification_id=response.id,
        )
        return response

    def _render_template(self, template: str, data: Dict[str, any]) -> str:
        """Simple template rendering."""
        result = template
        for key, value in data.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result


# Global instance
_auth_email_service: Optional[AuthEmailService] = None


def get_auth_email_service(
    app_name: str = "DotMac Platform", base_url: str = "http://localhost:3000"
) -> AuthEmailService:
    """Get or create the global auth email service."""
    global _auth_email_service
    if _auth_email_service is None:
        _auth_email_service = AuthEmailService(app_name, base_url)
    return _auth_email_service

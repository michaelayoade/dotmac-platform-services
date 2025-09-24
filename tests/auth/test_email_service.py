"""Comprehensive tests for auth email service."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, call
from dotmac.platform.auth.email_service import (
    AuthEmailService,
    EmailTemplates,
    PasswordResetToken,
    get_auth_email_service,
)
from dotmac.platform.communications import (
    NotificationRequest,
    NotificationResponse,
    NotificationStatus,
    NotificationType,
)


@pytest.fixture
def mock_notification_service():
    """Create mock notification service."""
    service = MagicMock()
    service.send.return_value = NotificationResponse(
        id="test-notification-id",
        status=NotificationStatus.SENT,
        message="Email sent successfully",
        metadata={"timestamp": datetime.now(timezone.utc).isoformat()}
    )
    service.add_template = MagicMock()
    return service


@pytest.fixture
def auth_email_service(mock_notification_service):
    """Create auth email service with mocked dependencies."""
    with patch('dotmac.platform.auth.email_service.get_notification_service',
               return_value=mock_notification_service):
        service = AuthEmailService(
            app_name="TestApp",
            base_url="http://test.example.com"
        )
    return service


class TestAuthEmailService:
    """Test AuthEmailService class."""

    def test_initialization(self, mock_notification_service):
        """Test service initialization."""
        with patch('dotmac.platform.auth.email_service.get_notification_service',
                   return_value=mock_notification_service):
            service = AuthEmailService(
                app_name="TestApp",
                base_url="http://test.example.com"
            )

        assert service.app_name == "TestApp"
        assert service.base_url == "http://test.example.com"
        assert service.notification_service == mock_notification_service

        # Verify templates were initialized
        assert mock_notification_service.add_template.call_count == 5
        mock_notification_service.add_template.assert_any_call(
            EmailTemplates.REGISTRATION_WELCOME
        )
        mock_notification_service.add_template.assert_any_call(
            EmailTemplates.PASSWORD_RESET
        )

    def test_send_welcome_email(self, auth_email_service, mock_notification_service):
        """Test sending welcome email."""
        response = auth_email_service.send_welcome_email(
            email="user@example.com",
            user_name="John Doe"
        )

        assert response.id == "test-notification-id"
        assert response.status == NotificationStatus.SENT

        # Verify notification service was called
        mock_notification_service.send.assert_called_once()
        call_args = mock_notification_service.send.call_args[0][0]
        assert isinstance(call_args, NotificationRequest)
        assert call_args.recipient == "user@example.com"
        assert call_args.type == NotificationType.EMAIL
        assert "Welcome to TestApp!" in call_args.subject
        assert "John Doe" in call_args.content
        assert "user@example.com" in call_args.content

    def test_send_welcome_email_without_name(self, auth_email_service, mock_notification_service):
        """Test sending welcome email without user name."""
        response = auth_email_service.send_welcome_email(
            email="user@example.com"
        )

        assert response.status == NotificationStatus.SENT

        call_args = mock_notification_service.send.call_args[0][0]
        assert "user" in call_args.content  # Should use email prefix

    def test_send_password_reset_email(self, auth_email_service, mock_notification_service):
        """Test sending password reset email."""
        response, reset_token = auth_email_service.send_password_reset_email(
            email="user@example.com",
            user_name="John Doe"
        )

        assert response.status == NotificationStatus.SENT
        assert reset_token is not None
        assert len(reset_token) > 0

        # Verify token was stored
        assert reset_token in auth_email_service._reset_tokens
        token_data = auth_email_service._reset_tokens[reset_token]
        assert token_data.email == "user@example.com"
        assert not token_data.used
        assert token_data.expires_at > datetime.now(timezone.utc)

        # Verify email content
        call_args = mock_notification_service.send.call_args[0][0]
        assert "Reset Your Password" in call_args.subject
        assert reset_token in call_args.content
        assert "http://test.example.com/reset-password?token=" in call_args.content

    def test_verify_reset_token_success(self, auth_email_service):
        """Test successful reset token verification."""
        # Create a token
        _, reset_token = auth_email_service.send_password_reset_email(
            email="user@example.com",
            user_name="John Doe"
        )

        # Verify token
        email = auth_email_service.verify_reset_token(reset_token)
        assert email == "user@example.com"

        # Token should be marked as used
        assert auth_email_service._reset_tokens[reset_token].used

    def test_verify_reset_token_invalid(self, auth_email_service):
        """Test invalid reset token verification."""
        email = auth_email_service.verify_reset_token("invalid-token")
        assert email is None

    def test_verify_reset_token_already_used(self, auth_email_service):
        """Test verification of already used token."""
        # Create and use a token
        _, reset_token = auth_email_service.send_password_reset_email(
            email="user@example.com",
            user_name="John Doe"
        )

        # First verification should succeed
        email = auth_email_service.verify_reset_token(reset_token)
        assert email == "user@example.com"

        # Second verification should fail
        email = auth_email_service.verify_reset_token(reset_token)
        assert email is None

    def test_verify_reset_token_expired(self, auth_email_service):
        """Test verification of expired token."""
        # Create a token
        _, reset_token = auth_email_service.send_password_reset_email(
            email="user@example.com",
            user_name="John Doe"
        )

        # Manually set expiration to past
        auth_email_service._reset_tokens[reset_token].expires_at = datetime.now(timezone.utc) - timedelta(hours=1)

        # Verification should fail
        email = auth_email_service.verify_reset_token(reset_token)
        assert email is None

    def test_send_password_reset_success_email(self, auth_email_service, mock_notification_service):
        """Test sending password reset success email."""
        response = auth_email_service.send_password_reset_success_email(
            email="user@example.com",
            user_name="John Doe"
        )

        assert response.status == NotificationStatus.SENT

        call_args = mock_notification_service.send.call_args[0][0]
        assert "Your Password Has Been Reset" in call_args.subject
        assert "John Doe" in call_args.content
        assert "successfully reset" in call_args.content

    def test_send_email_verification(self, auth_email_service, mock_notification_service):
        """Test sending email verification."""
        response, verification_code = auth_email_service.send_email_verification(
            email="user@example.com",
            user_name="John Doe"
        )

        assert response.status == NotificationStatus.SENT
        assert verification_code is not None
        assert len(verification_code) == 6  # Should be 6 digits
        assert verification_code.isdigit()

        # Verify code was stored
        assert auth_email_service._verification_codes["user@example.com"] == verification_code

        # Verify email content
        call_args = mock_notification_service.send.call_args[0][0]
        assert "Verify Your Email" in call_args.subject
        assert verification_code in call_args.content
        assert "http://test.example.com/verify-email?email=user@example.com&code=" in call_args.content

    def test_verify_email_code_success(self, auth_email_service):
        """Test successful email code verification."""
        # Send verification email
        _, verification_code = auth_email_service.send_email_verification(
            email="user@example.com",
            user_name="John Doe"
        )

        # Verify code
        result = auth_email_service.verify_email_code("user@example.com", verification_code)
        assert result is True

        # Code should be removed after successful verification
        assert "user@example.com" not in auth_email_service._verification_codes

    def test_verify_email_code_invalid(self, auth_email_service):
        """Test invalid email code verification."""
        # Send verification email
        _, verification_code = auth_email_service.send_email_verification(
            email="user@example.com",
            user_name="John Doe"
        )

        # Try invalid code
        result = auth_email_service.verify_email_code("user@example.com", "000000")
        assert result is False

        # Code should still be stored
        assert "user@example.com" in auth_email_service._verification_codes

    def test_verify_email_code_no_code(self, auth_email_service):
        """Test verification when no code exists."""
        result = auth_email_service.verify_email_code("nonexistent@example.com", "123456")
        assert result is False

    def test_send_login_alert(self, auth_email_service, mock_notification_service):
        """Test sending login alert."""
        response = auth_email_service.send_login_alert(
            email="user@example.com",
            user_name="John Doe",
            login_ip="192.168.1.1",
            login_device="Chrome on Windows",
            login_location="New York, USA"
        )

        assert response.status == NotificationStatus.SENT

        call_args = mock_notification_service.send.call_args[0][0]
        assert "New Login to Your Account" in call_args.subject
        assert "192.168.1.1" in call_args.content
        assert "Chrome on Windows" in call_args.content
        assert "New York, USA" in call_args.content

    def test_send_login_alert_with_defaults(self, auth_email_service, mock_notification_service):
        """Test sending login alert with default values."""
        response = auth_email_service.send_login_alert(
            email="user@example.com"
        )

        assert response.status == NotificationStatus.SENT

        call_args = mock_notification_service.send.call_args[0][0]
        assert "Unknown" in call_args.content  # Default values

    def test_render_template(self, auth_email_service):
        """Test template rendering."""
        template = "Hello {{name}}, your email is {{email}}."
        data = {"name": "John Doe", "email": "john@example.com"}

        result = auth_email_service._render_template(template, data)
        assert result == "Hello John Doe, your email is john@example.com."

    def test_render_template_with_missing_values(self, auth_email_service):
        """Test template rendering with missing values."""
        template = "Hello {{name}}, {{missing}} value."
        data = {"name": "John Doe"}

        result = auth_email_service._render_template(template, data)
        assert result == "Hello John Doe, {{missing}} value."


class TestGetAuthEmailService:
    """Test get_auth_email_service function."""

    def test_singleton_pattern(self):
        """Test that get_auth_email_service returns singleton."""
        with patch('dotmac.platform.auth.email_service.get_notification_service'):
            service1 = get_auth_email_service()
            service2 = get_auth_email_service()

            assert service1 is service2

    def test_custom_parameters(self):
        """Test get_auth_email_service with custom parameters."""
        # Reset global instance
        import dotmac.platform.auth.email_service
        dotmac.platform.auth.email_service._auth_email_service = None

        with patch('dotmac.platform.auth.email_service.get_notification_service'):
            service = get_auth_email_service(
                app_name="CustomApp",
                base_url="https://custom.example.com"
            )

            assert service.app_name == "CustomApp"
            assert service.base_url == "https://custom.example.com"


class TestEmailTemplates:
    """Test email template definitions."""

    def test_registration_welcome_template(self):
        """Test registration welcome template structure."""
        template = EmailTemplates.REGISTRATION_WELCOME
        assert template.id == "auth_registration_welcome"
        assert template.type == NotificationType.EMAIL
        assert "Welcome to {{app_name}}" in template.subject_template
        assert "{{user_name}}" in template.content_template
        assert "{{user_email}}" in template.content_template

    def test_password_reset_template(self):
        """Test password reset template structure."""
        template = EmailTemplates.PASSWORD_RESET
        assert template.id == "auth_password_reset"
        assert template.type == NotificationType.EMAIL
        assert "Reset Your Password" in template.subject_template
        assert "{{reset_link}}" in template.content_template
        assert "{{expiry_hours}}" in template.content_template

    def test_password_reset_success_template(self):
        """Test password reset success template structure."""
        template = EmailTemplates.PASSWORD_RESET_SUCCESS
        assert template.id == "auth_password_reset_success"
        assert "Password Has Been Reset" in template.subject_template
        assert "successfully reset" in template.content_template

    def test_email_verification_template(self):
        """Test email verification template structure."""
        template = EmailTemplates.EMAIL_VERIFICATION
        assert template.id == "auth_email_verification"
        assert "Verify Your Email" in template.subject_template
        assert "{{verification_link}}" in template.content_template
        assert "{{verification_code}}" in template.content_template

    def test_login_alert_template(self):
        """Test login alert template structure."""
        template = EmailTemplates.LOGIN_ALERT
        assert template.id == "auth_login_alert"
        assert "New Login" in template.subject_template
        assert "{{login_time}}" in template.content_template
        assert "{{login_location}}" in template.content_template
        assert "{{login_device}}" in template.content_template
        assert "{{login_ip}}" in template.content_template


class TestPasswordResetToken:
    """Test PasswordResetToken model."""

    def test_password_reset_token_creation(self):
        """Test creating password reset token."""
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        token = PasswordResetToken(
            token="test-token",
            email="test@example.com",
            expires_at=expires,
            used=False
        )

        assert token.token == "test-token"
        assert token.email == "test@example.com"
        assert token.expires_at == expires
        assert token.used is False

    def test_password_reset_token_defaults(self):
        """Test password reset token default values."""
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        token = PasswordResetToken(
            token="test-token",
            email="test@example.com",
            expires_at=expires
        )

        assert token.used is False  # Default value
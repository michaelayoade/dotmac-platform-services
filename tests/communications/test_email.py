"""Tests for email service."""

import smtplib
from unittest.mock import MagicMock, Mock, patch

import pytest

from dotmac.platform.communications.config import SMTPConfig
from dotmac.platform.communications.email import EmailMessage, EmailService


class TestEmailMessage:
    """Test EmailMessage model."""

    def test_email_message_creation(self):
        """Test creating email message."""
        msg = EmailMessage(
            to="user@example.com",
            subject="Test Subject",
            body="Test Body",
        )
        assert msg.to == ["user@example.com"]
        assert msg.subject == "Test Subject"
        assert msg.body == "Test Body"
        assert msg.is_html is False

    def test_email_message_multiple_recipients(self):
        """Test email with multiple recipients."""
        msg = EmailMessage(
            to=["user1@example.com", "user2@example.com"],
            subject="Test",
            body="Body",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
        )
        assert len(msg.to) == 2
        assert len(msg.cc) == 1
        assert len(msg.bcc) == 1

    def test_email_message_html(self):
        """Test HTML email message."""
        msg = EmailMessage(
            to="user@example.com",
            subject="HTML Test",
            body="<h1>Hello</h1>",
            is_html=True,
        )
        assert msg.is_html is True

    def test_email_message_validation(self):
        """Test email message validation."""
        # To field is required
        with pytest.raises(ValueError):
            EmailMessage(subject="Test", body="Body")

        # Subject is required
        with pytest.raises(ValueError):
            EmailMessage(to="user@example.com", body="Body")

        # Body is required
        with pytest.raises(ValueError):
            EmailMessage(to="user@example.com", subject="Test")


class TestEmailService:
    """Test EmailService functionality."""

    @pytest.fixture
    def smtp_config(self):
        """Create test SMTP configuration."""
        return SMTPConfig(
            host="smtp.example.com",
            port=587,
            username="test@example.com",
            password="password",
            use_tls=True,
            from_email="noreply@example.com",
            from_name="Test App",
        )

    @pytest.fixture
    def email_service(self, smtp_config):
        """Create email service."""
        return EmailService(smtp_config)

    @pytest.fixture
    def email_message(self):
        """Create test email message."""
        return EmailMessage(
            to="recipient@example.com",
            subject="Test Email",
            body="This is a test email.",
        )

    @patch("smtplib.SMTP")
    def test_send_email_success(self, mock_smtp_class, email_service, email_message):
        """Test successful email sending."""
        # Setup mock
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp

        # Send email
        result = email_service.send(email_message)

        # Verify
        assert result is True
        mock_smtp_class.assert_called_once_with(
            "smtp.example.com", 587, timeout=30
        )
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("test@example.com", "password")
        mock_smtp.send_message.assert_called_once()
        mock_smtp.quit.assert_called_once()

    @patch("smtplib.SMTP_SSL")
    def test_send_email_ssl(self, mock_smtp_ssl_class, email_message):
        """Test sending email with SSL."""
        # Create SSL config
        config = SMTPConfig(
            host="smtp.example.com",
            port=465,
            use_ssl=True,
            use_tls=False,
            from_email="noreply@example.com",
        )
        service = EmailService(config)

        # Setup mock
        mock_smtp = MagicMock()
        mock_smtp_ssl_class.return_value = mock_smtp

        # Send email
        result = service.send(email_message)

        # Verify
        assert result is True
        mock_smtp_ssl_class.assert_called_once_with(
            "smtp.example.com", 465, timeout=30
        )
        mock_smtp.send_message.assert_called_once()

    @patch("smtplib.SMTP")
    def test_send_email_no_auth(self, mock_smtp_class, email_message):
        """Test sending email without authentication."""
        # Create config without auth
        config = SMTPConfig(
            host="localhost",
            port=25,
            use_tls=False,
            from_email="noreply@example.com",
        )
        service = EmailService(config)

        # Setup mock
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp

        # Send email
        result = service.send(email_message)

        # Verify
        assert result is True
        mock_smtp.login.assert_not_called()
        mock_smtp.send_message.assert_called_once()

    @patch("smtplib.SMTP")
    def test_send_email_with_cc_bcc(self, mock_smtp_class, email_service):
        """Test sending email with CC and BCC."""
        # Create message with CC and BCC
        message = EmailMessage(
            to="recipient@example.com",
            subject="Test",
            body="Body",
            cc=["cc1@example.com", "cc2@example.com"],
            bcc=["bcc@example.com"],
        )

        # Setup mock
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp

        # Send email
        result = email_service.send(message)

        # Verify
        assert result is True
        # Check that all recipients are included
        call_args = mock_smtp.send_message.call_args
        to_addrs = call_args[1]["to_addrs"]
        assert "recipient@example.com" in to_addrs
        assert "cc1@example.com" in to_addrs
        assert "cc2@example.com" in to_addrs
        assert "bcc@example.com" in to_addrs

    @patch("smtplib.SMTP")
    def test_send_email_smtp_error(self, mock_smtp_class, email_service, email_message):
        """Test email sending with SMTP error."""
        # Setup mock to raise exception
        mock_smtp = MagicMock()
        mock_smtp.send_message.side_effect = smtplib.SMTPException("SMTP Error")
        mock_smtp_class.return_value = mock_smtp

        # Send email
        result = email_service.send(email_message)

        # Verify
        assert result is False

    @patch("smtplib.SMTP")
    def test_send_email_connection_error(self, mock_smtp_class, email_service, email_message):
        """Test email sending with connection error."""
        # Setup mock to raise exception
        mock_smtp_class.side_effect = ConnectionError("Connection failed")

        # Send email
        result = email_service.send(email_message)

        # Verify
        assert result is False

    @pytest.mark.asyncio
    @patch("smtplib.SMTP")
    async def test_send_async(self, mock_smtp_class, email_service, email_message):
        """Test async email sending."""
        # Setup mock
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp

        # Send email asynchronously
        result = await email_service.send_async(email_message)

        # Verify
        assert result is True
        mock_smtp.send_message.assert_called_once()

    @patch("smtplib.SMTP")
    def test_send_template(self, mock_smtp_class, email_service):
        """Test sending template email."""
        # Setup mock
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp

        # Send template
        result = email_service.send_template(
            to="user@example.com",
            template_name="welcome",
            context={"name": "John", "code": "12345"},
            subject="Welcome!",
        )

        # Verify
        assert result is True
        mock_smtp.send_message.assert_called_once()

    @patch("smtplib.SMTP")
    def test_test_connection_success(self, mock_smtp_class, email_service):
        """Test SMTP connection test - success."""
        # Setup mock
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp

        # Test connection
        result = email_service.test_connection()

        # Verify
        assert result is True
        mock_smtp.quit.assert_called_once()

    @patch("smtplib.SMTP")
    def test_test_connection_failure(self, mock_smtp_class, email_service):
        """Test SMTP connection test - failure."""
        # Setup mock to raise exception
        mock_smtp_class.side_effect = ConnectionError("Connection failed")

        # Test connection
        result = email_service.test_connection()

        # Verify
        assert result is False
"""Tests for EmailService."""

import smtplib
from unittest.mock import MagicMock, Mock, patch

import pytest
from dotmac.platform.communications.config import SMTPConfig
from dotmac.platform.communications.email import EmailMessage, EmailService


class TestEmailMessage:
    """Test EmailMessage model."""

    def test_email_message_creation(self):
        """Test creating an email message."""
        msg = EmailMessage(
            to="user@example.com",
            subject="Test Subject",
            body="Test Body",
        )
        assert msg.to == ["user@example.com"]
        assert msg.subject == "Test Subject"
        assert msg.body == "Test Body"
        assert msg.is_html is False

    def test_email_message_with_multiple_recipients(self):
        """Test email with multiple recipients."""
        msg = EmailMessage(
            to=["user1@example.com", "user2@example.com"],
            subject="Test",
            body="Body",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
        )
        assert len(msg.to) == 2
        assert msg.cc == ["cc@example.com"]
        assert msg.bcc == ["bcc@example.com"]

    def test_email_message_html(self):
        """Test HTML email message."""
        msg = EmailMessage(
            to="user@example.com",
            subject="HTML Test",
            body="<h1>Test</h1>",
            is_html=True,
        )
        assert msg.is_html is True

    def test_email_message_with_headers(self):
        """Test email with custom headers."""
        msg = EmailMessage(
            to="user@example.com",
            subject="Test",
            body="Body",
            headers={"X-Custom": "Value"},
        )
        assert msg.headers == {"X-Custom": "Value"}


class TestEmailService:
    """Test EmailService."""

    @pytest.fixture
    def smtp_config(self):
        """Create test SMTP config."""
        return SMTPConfig(
            host="smtp.example.com",
            port=587,
            from_email="sender@example.com",
            from_name="Test Sender",
            username="testuser",
            password="testpass",
            use_tls=True,
        )

    @pytest.fixture
    def email_service(self, smtp_config):
        """Create test email service."""
        return EmailService(smtp_config)

    def test_email_service_creation(self, email_service, smtp_config):
        """Test creating email service."""
        assert email_service.config == smtp_config

    @patch("smtplib.SMTP")
    def test_send_email(self, mock_smtp, email_service):
        """Test sending an email."""
        # Setup mock
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server

        # Create and send email
        msg = EmailMessage(
            to="recipient@example.com",
            subject="Test Email",
            body="Test content",
        )

        result = email_service.send(msg)

        # Verify
        assert result is True
        mock_smtp.assert_called_once_with("smtp.example.com", 587, timeout=30)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("testuser", "testpass")
        mock_server.send_message.assert_called_once()
        mock_server.quit.assert_called_once()

    @patch("smtplib.SMTP_SSL")
    def test_send_email_ssl(self, mock_smtp_ssl, smtp_config):
        """Test sending email with SSL."""
        # Create SSL config
        smtp_config.use_ssl = True
        smtp_config.use_tls = False
        smtp_config.port = 465
        service = EmailService(smtp_config)

        # Setup mock
        mock_server = MagicMock()
        mock_smtp_ssl.return_value = mock_server

        # Send email
        msg = EmailMessage(
            to="recipient@example.com",
            subject="SSL Test",
            body="Content",
        )

        result = service.send(msg)

        # Verify
        assert result is True
        mock_smtp_ssl.assert_called_once_with("smtp.example.com", 465, timeout=30)
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()

    @patch("smtplib.SMTP")
    def test_send_email_failure(self, mock_smtp, email_service):
        """Test email sending failure."""
        # Setup mock to raise exception
        mock_smtp.side_effect = smtplib.SMTPException("Connection failed")

        # Send email
        msg = EmailMessage(
            to="recipient@example.com",
            subject="Test",
            body="Content",
        )

        result = email_service.send(msg)

        # Verify failure
        assert result is False

    def test_send_email_helper(self, email_service):
        """Test send_email helper method."""
        with patch.object(email_service, "send") as mock_send:
            mock_send.return_value = True

            result = email_service.send_email(
                to="recipient@example.com",
                subject="Test",
                message="Content",
                is_html=False,
                cc=["cc@example.com"],
            )

            assert result is True
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][0]
            assert call_args.to == ["recipient@example.com"]
            assert call_args.subject == "Test"
            assert call_args.body == "Content"
            assert call_args.cc == ["cc@example.com"]

    def test_send_template(self, email_service):
        """Test send_template method."""
        with patch.object(email_service, "send") as mock_send:
            mock_send.return_value = True

            result = email_service.send_template(
                template_name="welcome",
                to="user@example.com",
                subject="Welcome",
                context={"name": "John", "id": "123"},
            )

            assert result is True
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][0]
            assert "Template: welcome" in call_args.body
            assert "name: John" in call_args.body
            assert "id: 123" in call_args.body

    @patch("smtplib.SMTP")
    def test_test_connection_success(self, mock_smtp, email_service):
        """Test connection testing success."""
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server

        result = email_service.test_connection()

        assert result is True
        mock_server.quit.assert_called_once()

    @patch("smtplib.SMTP")
    def test_test_connection_failure(self, mock_smtp, email_service):
        """Test connection testing failure."""
        mock_smtp.side_effect = Exception("Connection failed")

        result = email_service.test_connection()

        assert result is False

    @pytest.mark.asyncio
    async def test_send_async(self, email_service):
        """Test async email sending."""
        with patch.object(email_service, "send") as mock_send:
            mock_send.return_value = True

            msg = EmailMessage(
                to="recipient@example.com",
                subject="Async Test",
                body="Content",
            )

            result = await email_service.send_async(msg)

            assert result is True
            mock_send.assert_called_once_with(msg)

    def test_get_all_recipients(self, email_service):
        """Test getting all recipients."""
        msg = EmailMessage(
            to=["user1@example.com", "user2@example.com"],
            subject="Test",
            body="Body",
            cc=["cc@example.com"],
            bcc=["bcc1@example.com", "bcc2@example.com"],
        )

        recipients = email_service._get_all_recipients(msg)

        assert len(recipients) == 5
        assert "user1@example.com" in recipients
        assert "user2@example.com" in recipients
        assert "cc@example.com" in recipients
        assert "bcc1@example.com" in recipients
        assert "bcc2@example.com" in recipients

    def test_create_message(self, email_service):
        """Test message creation."""
        msg = EmailMessage(
            to="recipient@example.com",
            subject="Test Subject",
            body="Test Body",
            reply_to="reply@example.com",
            headers={"X-Priority": "1"},
        )

        mime_msg = email_service._create_message(msg)

        assert mime_msg["To"] == "recipient@example.com"
        assert mime_msg["Subject"] == "Test Subject"
        assert mime_msg["From"] == "Test Sender <sender@example.com>"
        assert mime_msg["Reply-To"] == "reply@example.com"
        assert mime_msg["X-Priority"] == "1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
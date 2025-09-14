"""Generic email service using SMTP."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from pydantic import BaseModel, Field, field_validator

from .config import SMTPConfig

logger = logging.getLogger(__name__)


class EmailMessage(BaseModel):
    """Email message model."""

    to: list[str] | str = Field(..., description="Recipient email address(es)")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body (plain text or HTML)")
    cc: list[str] | None = Field(None, description="CC recipients")
    bcc: list[str] | None = Field(None, description="BCC recipients")
    reply_to: str | None = Field(None, description="Reply-to address")
    is_html: bool = Field(False, description="Whether body is HTML")
    headers: dict[str, str] = Field(default_factory=dict, description="Additional headers")
    attachments: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of attachments (not implemented in basic version)",
    )

    @field_validator("to")
    @classmethod
    def validate_to(cls, v: list[str] | str) -> list[str]:
        """Ensure 'to' is always a list."""
        if isinstance(v, str):
            return [v]
        return v

    @field_validator("cc", "bcc")
    @classmethod
    def validate_cc_bcc(cls, v: list[str] | None) -> list[str] | None:
        """Validate CC/BCC fields."""
        if v is not None and len(v) == 0:
            return None
        return v


class EmailService:
    """
    Generic SMTP email service.

    No vendor dependencies, just standard SMTP.
    """

    def __init__(self, config: SMTPConfig):
        """
        Initialize email service.

        Args:
            config: SMTP configuration
        """
        self.config = config

    def _create_message(self, email: EmailMessage) -> MIMEMultipart:
        """Create MIME message from email model."""
        msg = MIMEMultipart("alternative" if email.is_html else "mixed")

        # Set sender
        if self.config.from_name:
            msg["From"] = f"{self.config.from_name} <{self.config.from_email}>"
        else:
            msg["From"] = self.config.from_email

        # Set recipients
        msg["To"] = ", ".join(email.to)
        msg["Subject"] = email.subject

        if email.cc:
            msg["Cc"] = ", ".join(email.cc)

        if email.reply_to:
            msg["Reply-To"] = email.reply_to

        # Add custom headers
        for header, value in email.headers.items():
            msg[header] = value

        # Add body
        if email.is_html:
            msg.attach(MIMEText(email.body, "html"))
        else:
            msg.attach(MIMEText(email.body, "plain"))

        return msg

    def _get_all_recipients(self, email: EmailMessage) -> list[str]:
        """Get all recipients (to, cc, bcc)."""
        recipients = email.to.copy()
        if email.cc:
            recipients.extend(email.cc)
        if email.bcc:
            recipients.extend(email.bcc)
        return recipients

    def send(self, email: EmailMessage) -> bool:
        """
        Send email via SMTP.

        Args:
            email: Email message to send

        Returns:
            True if sent successfully
        """
        try:
            msg = self._create_message(email)
            recipients = self._get_all_recipients(email)

            # Connect to SMTP server
            if self.config.use_ssl:
                server = smtplib.SMTP_SSL(
                    self.config.host,
                    self.config.port,
                    timeout=self.config.timeout,
                )
            else:
                server = smtplib.SMTP(
                    self.config.host,
                    self.config.port,
                    timeout=self.config.timeout,
                )

                if self.config.use_tls:
                    server.starttls()

            # Authenticate if credentials provided
            if self.config.username and self.config.password:
                server.login(self.config.username, self.config.password)

            # Send email
            server.send_message(msg, to_addrs=recipients)
            server.quit()

            logger.info(
                "Email sent successfully to %s with subject: %s",
                ", ".join(email.to),
                email.subject,
            )
            return True

        except smtplib.SMTPException as e:
            logger.error("SMTP error sending email: %s", str(e))
            return False
        except Exception as e:
            logger.error("Error sending email: %s", str(e))
            return False

    async def send_async(self, email: EmailMessage) -> bool:
        """
        Send email asynchronously.

        Note: This is a wrapper that runs the sync send in an executor.
        For true async, consider using aiosmtplib.

        Args:
            email: Email message to send

        Returns:
            True if sent successfully
        """
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.send, email)

    def send_template(
        self,
        to: str | list[str],
        template_name: str,
        context: dict[str, Any],
        subject: str | None = None,
    ) -> bool:
        """
        Send email using a template.

        This is a simplified version. In production, you'd integrate
        with a template engine like Jinja2.

        Args:
            to: Recipient(s)
            template_name: Template identifier
            context: Template context variables
            subject: Email subject (can be in template)

        Returns:
            True if sent successfully
        """
        # Simple template rendering (you'd use Jinja2 in production)
        body = f"Template: {template_name}\n"
        for key, value in context.items():
            body += f"{key}: {value}\n"

        email = EmailMessage(
            to=to,
            subject=subject or f"Message from {template_name}",
            body=body,
            is_html=False,
        )

        return self.send(email)

    # Compatibility helper matching common notification interfaces in tests
    def send_email(
        self,
        to: str | list[str],
        subject: str,
        message: str,
        *,
        is_html: bool = False,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        reply_to: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> bool:
        email = EmailMessage(
            to=to,
            subject=subject,
            body=message,
            is_html=is_html,
            cc=cc,
            bcc=bcc,
            reply_to=reply_to,
            headers=headers or {},
        )
        return self.send(email)

    def test_connection(self) -> bool:
        """
        Test SMTP connection.

        Returns:
            True if connection successful
        """
        try:
            if self.config.use_ssl:
                server = smtplib.SMTP_SSL(
                    self.config.host,
                    self.config.port,
                    timeout=self.config.timeout,
                )
            else:
                server = smtplib.SMTP(
                    self.config.host,
                    self.config.port,
                    timeout=self.config.timeout,
                )

                if self.config.use_tls:
                    server.starttls()

            # Test authentication if configured
            if self.config.username and self.config.password:
                server.login(self.config.username, self.config.password)

            server.quit()
            logger.info("SMTP connection test successful")
            return True

        except Exception as e:
            logger.error("SMTP connection test failed: %s", str(e))
            return False

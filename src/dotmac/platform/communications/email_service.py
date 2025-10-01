"""
Email service using standard libraries.

Provides email functionality using standard smtplib.
"""

import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional
from uuid import uuid4

import structlog
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


class EmailMessage(BaseModel):
    """Email message model."""

    to: List[EmailStr] = Field(..., description="Recipient email addresses")
    subject: str = Field(..., min_length=1, description="Email subject")
    text_body: Optional[str] = Field(None, description="Plain text body")
    html_body: Optional[str] = Field(None, description="HTML body")
    from_email: Optional[EmailStr] = Field(None, description="Sender email")
    from_name: Optional[str] = Field(None, description="Sender name")
    reply_to: Optional[EmailStr] = Field(None, description="Reply-to address")
    cc: Optional[List[EmailStr]] = Field(default_factory=list, description="CC recipients")
    bcc: Optional[List[EmailStr]] = Field(default_factory=list, description="BCC recipients")

    model_config = {
        "str_strip_whitespace": True,
        "validate_assignment": True,
        "extra": "forbid"
    }


class EmailResponse(BaseModel):
    """Email sending response."""

    id: str = Field(..., description="Unique message ID")
    status: str = Field(..., description="Delivery status")
    message: str = Field(..., description="Status message")
    sent_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    recipients_count: int = Field(..., description="Number of recipients")


class EmailService:
    """Email service using standard SMTP."""

    def __init__(
        self,
        smtp_host: str = "localhost",
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        use_tls: bool = True,
        default_from: str = "noreply@dotmac.com",
        tenant_id: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.use_tls = use_tls
        self.default_from = default_from
        self.tenant_id = tenant_id
        self.db = db

        logger.info(
            "Email service initialized",
            host=smtp_host,
            port=smtp_port,
            use_tls=use_tls
        )

    async def send_email(self, message: EmailMessage, tenant_id: Optional[str] = None, db: Optional[AsyncSession] = None) -> EmailResponse:
        """Send a single email message."""
        message_id = f"email_{uuid4().hex[:8]}"

        try:
            # Create MIME message
            msg = self._create_mime_message(message, message_id)

            # Send via SMTP
            await self._send_smtp(msg, message)

            response = EmailResponse(
                id=message_id,
                status="sent",
                message="Email sent successfully",
                recipients_count=len(message.to) + len(message.cc) + len(message.bcc)
            )

            logger.info(
                "Email sent successfully",
                message_id=message_id,
                recipients=len(message.to),
                subject=message.subject
            )

            # Publish webhook event if DB session provided
            if db or self.db:
                try:
                    from dotmac.platform.webhooks.events import get_event_bus
                    from dotmac.platform.webhooks.models import WebhookEvent

                    await get_event_bus().publish(
                        event_type=WebhookEvent.EMAIL_SENT.value,
                        event_data={
                            "message_id": message_id,
                            "to": [str(email) for email in message.to],
                            "subject": message.subject,
                            "from_email": str(message.from_email) if message.from_email else self.default_from,
                            "recipients_count": response.recipients_count,
                            "sent_at": response.sent_at.isoformat(),
                        },
                        tenant_id=tenant_id or self.tenant_id or "system",
                        db=db or self.db,
                    )
                except Exception as e:
                    logger.warning("Failed to publish email.sent event", error=str(e))

            return response

        except Exception as e:
            logger.error(
                "Failed to send email",
                message_id=message_id,
                error=str(e),
                subject=message.subject
            )

            response = EmailResponse(
                id=message_id,
                status="failed",
                message=f"Failed to send email: {str(e)}",
                recipients_count=len(message.to) + len(message.cc) + len(message.bcc)
            )

            # Publish webhook event for failed email if DB session provided
            if db or self.db:
                try:
                    from dotmac.platform.webhooks.events import get_event_bus
                    from dotmac.platform.webhooks.models import WebhookEvent

                    await get_event_bus().publish(
                        event_type=WebhookEvent.EMAIL_FAILED.value,
                        event_data={
                            "message_id": message_id,
                            "to": [str(email) for email in message.to],
                            "subject": message.subject,
                            "from_email": str(message.from_email) if message.from_email else self.default_from,
                            "recipients_count": response.recipients_count,
                            "error": str(e),
                        },
                        tenant_id=tenant_id or self.tenant_id or "system",
                        db=db or self.db,
                    )
                except Exception as webhook_error:
                    logger.warning("Failed to publish email.failed event", error=str(webhook_error))

            return response

    def _create_mime_message(self, message: EmailMessage, message_id: str) -> MIMEMultipart:
        """Create MIME message from EmailMessage."""
        msg = MIMEMultipart('alternative')

        # Headers
        msg['Subject'] = message.subject
        msg['From'] = self._format_from_address(message.from_email, message.from_name)
        msg['To'] = ', '.join(str(email) for email in message.to)
        msg['Message-ID'] = f"<{message_id}@dotmac.com>"
        msg['Date'] = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S %z')

        if message.cc:
            msg['Cc'] = ', '.join(str(email) for email in message.cc)

        if message.reply_to:
            msg['Reply-To'] = str(message.reply_to)

        # Body parts
        if message.text_body:
            text_part = MIMEText(message.text_body, 'plain', 'utf-8')
            msg.attach(text_part)

        if message.html_body:
            html_part = MIMEText(message.html_body, 'html', 'utf-8')
            msg.attach(html_part)

        # If no body provided, add minimal text
        if not message.text_body and not message.html_body:
            msg.attach(MIMEText("", 'plain'))

        return msg

    def _format_from_address(self, from_email: Optional[EmailStr], from_name: Optional[str]) -> str:
        """Format the From header address."""
        email = str(from_email) if from_email else self.default_from

        if from_name:
            return f'"{from_name}" <{email}>'
        return email

    async def _send_smtp(self, msg: MIMEMultipart, message: EmailMessage) -> None:
        """Send message via SMTP."""
        # Get all recipients
        all_recipients = []
        all_recipients.extend(str(email) for email in message.to)
        all_recipients.extend(str(email) for email in message.cc)
        all_recipients.extend(str(email) for email in message.bcc)

        # Connect and send
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            if self.use_tls:
                server.starttls()

            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)

            server.send_message(msg, to_addrs=all_recipients)

    async def send_bulk_emails(self, messages: List[EmailMessage]) -> List[EmailResponse]:
        """Send multiple emails (simplified bulk processing)."""
        responses = []

        logger.info("Starting bulk email send", count=len(messages))

        for i, message in enumerate(messages):
            try:
                response = await self.send_email(message)
                responses.append(response)

                # Log progress every 10 emails
                if (i + 1) % 10 == 0:
                    logger.info(f"Bulk email progress: {i + 1}/{len(messages)}")

            except Exception as e:
                logger.error(
                    "Bulk email failed for message",
                    index=i,
                    error=str(e),
                    subject=message.subject
                )
                responses.append(EmailResponse(
                    id=f"bulk_{i}_{uuid4().hex[:4]}",
                    status="failed",
                    message=f"Bulk send failed: {str(e)}",
                    recipients_count=len(message.to)
                ))

        success_count = sum(1 for r in responses if r.status == "sent")
        logger.info(
            "Bulk email completed",
            total=len(messages),
            success=success_count,
            failed=len(messages) - success_count
        )

        return responses


# Global service instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create the global email service."""
    global _email_service
    if _email_service is None:
        # Load from settings in production
        _email_service = EmailService()
    return _email_service


async def send_email(
    to: List[str],
    subject: str,
    text_body: Optional[str] = None,
    html_body: Optional[str] = None,
    from_email: Optional[str] = None
) -> EmailResponse:
    """Convenience function for sending simple emails."""
    service = get_email_service()

    message = EmailMessage(
        to=to,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        from_email=from_email
    )

    return await service.send_email(message)
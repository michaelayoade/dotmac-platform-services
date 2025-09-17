from dotmac.platform.observability.unified_logging import get_logger

"""
Email-related Celery tasks using SendGrid.

This module provides async email sending capabilities
with templates, attachments, and retry logic.
"""

import os
from typing import Any

from celery import shared_task
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Attachment,
    FileContent,
    FileName,
    FileType,
    Mail,
    Personalization,
    To,
)

import structlog

logger = get_logger(__name__)

@shared_task(
    name="dotmac.platform.tasks.email.send_email",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="email",
)
def send_email(
    self,
    to_email: str | list[str],
    subject: str,
    html_content: str,
    from_email: str | None = None,
    text_content: str | None = None,
    attachments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Send email via SendGrid.

    Args:
        to_email: Recipient email(s)
        subject: Email subject
        html_content: HTML email body
        from_email: Sender email (defaults to env var)
        text_content: Plain text fallback
        attachments: List of attachment dicts with keys:
            - content: Base64 encoded file content
            - filename: Name of the file
            - type: MIME type

    Returns:
        Result dict with status and message_id
    """
    try:
        sg_api_key = os.getenv("SENDGRID_API_KEY")
        if not sg_api_key:
            raise ValueError("SENDGRID_API_KEY not configured")

        sg = SendGridAPIClient(sg_api_key)

        # Default from email
        if not from_email:
            from_email = os.getenv("DEFAULT_FROM_EMAIL", "noreply@dotmac.com")

        # Create mail object
        message = Mail(
            from_email=from_email,
            to_emails=to_email if isinstance(to_email, list) else [to_email],
            subject=subject,
            html_content=html_content,
        )

        if text_content:
            message.plain_text_content = text_content

        # Add attachments
        if attachments:
            for att in attachments:
                attachment = Attachment(
                    FileContent(att["content"]),
                    FileName(att["filename"]),
                    FileType(att.get("type", "application/octet-stream")),
                )
                message.add_attachment(attachment)

        # Send email
        response = sg.send(message)

        logger.info(
            "email_sent",
            to=to_email,
            subject=subject,
            status_code=response.status_code,
            task_id=self.request.id,
        )

        return {
            "success": True,
            "status_code": response.status_code,
            "message_id": response.headers.get("X-Message-Id"),
            "to": to_email,
        }

    except Exception as e:
        logger.error(
            "email_send_failed",
            to=to_email,
            subject=subject,
            error=str(e),
            task_id=self.request.id,
        )

        # Retry on failure
        raise self.retry(exc=e)

@shared_task(
    name="dotmac.platform.tasks.email.send_template_email",
    bind=True,
    max_retries=3,
    queue="email",
)
def send_template_email(
    self,
    to_email: str | list[str],
    template_id: str,
    template_data: dict[str, Any] | None = None,
    from_email: str | None = None,
) -> dict[str, Any]:
    """
    Send email using SendGrid dynamic template.

    Args:
        to_email: Recipient email(s)
        template_id: SendGrid template ID
        template_data: Template substitution data
        from_email: Sender email

    Returns:
        Result dict with status
    """
    try:
        sg_api_key = os.getenv("SENDGRID_API_KEY")
        if not sg_api_key:
            raise ValueError("SENDGRID_API_KEY not configured")

        sg = SendGridAPIClient(sg_api_key)

        if not from_email:
            from_email = os.getenv("DEFAULT_FROM_EMAIL", "noreply@dotmac.com")

        message = Mail(from_email=from_email)
        message.template_id = template_id

        # Handle multiple recipients
        if isinstance(to_email, str):
            to_email = [to_email]

        for email in to_email:
            personalization = Personalization()
            personalization.add_to(To(email))

            if template_data:
                for key, value in template_data.items():
                    personalization.dynamic_template_data[key] = value

            message.add_personalization(personalization)

        response = sg.send(message)

        logger.info(
            "template_email_sent",
            template_id=template_id,
            to=to_email,
            status_code=response.status_code,
            task_id=self.request.id,
        )

        return {
            "success": True,
            "status_code": response.status_code,
            "template_id": template_id,
            "to": to_email,
        }

    except Exception as e:
        logger.error(
            "template_email_failed",
            template_id=template_id,
            to=to_email,
            error=str(e),
            task_id=self.request.id,
        )
        raise self.retry(exc=e)

@shared_task(
    name="dotmac.platform.tasks.email.send_bulk_email",
    bind=True,
    queue="email",
)
def send_bulk_email(
    self,
    recipients: list[dict[str, Any]],
    subject: str,
    html_content: str,
    from_email: str | None = None,
    batch_size: int = 100,
) -> dict[str, Any]:
    """
    Send bulk personalized emails.

    Args:
        recipients: List of dicts with 'email' and optional 'data' keys
        subject: Email subject (can contain substitutions)
        html_content: HTML template with substitutions
        from_email: Sender email
        batch_size: Number of emails per batch

    Returns:
        Summary of sent emails
    """
    try:
        sg_api_key = os.getenv("SENDGRID_API_KEY")
        if not sg_api_key:
            raise ValueError("SENDGRID_API_KEY not configured")

        sg = SendGridAPIClient(sg_api_key)

        if not from_email:
            from_email = os.getenv("DEFAULT_FROM_EMAIL", "noreply@dotmac.com")

        sent_count = 0
        failed_count = 0

        # Process in batches
        for i in range(0, len(recipients), batch_size):
            batch = recipients[i : i + batch_size]

            message = Mail()
            message.from_email = from_email
            message.subject = subject
            message.html_content = html_content

            # Add personalizations for each recipient
            for recipient in batch:
                personalization = Personalization()
                personalization.add_to(To(recipient["email"]))

                # Add substitution data if provided
                if "data" in recipient:
                    for key, value in recipient["data"].items():
                        personalization.add_substitution(f"{{{key}}}", str(value))

                message.add_personalization(personalization)

            try:
                response = sg.send(message)
                sent_count += len(batch)

                logger.info(
                    "bulk_email_batch_sent",
                    batch_size=len(batch),
                    status_code=response.status_code,
                    task_id=self.request.id,
                )
            except Exception as batch_error:
                failed_count += len(batch)
                logger.error(
                    "bulk_email_batch_failed",
                    batch_size=len(batch),
                    error=str(batch_error),
                    task_id=self.request.id,
                )

        return {
            "success": True,
            "sent_count": sent_count,
            "failed_count": failed_count,
            "total": len(recipients),
        }

    except Exception as e:
        logger.error(
            "bulk_email_failed",
            error=str(e),
            task_id=self.request.id,
        )
        raise

@shared_task(
    name="dotmac.platform.tasks.email.send_welcome_email",
    bind=True,
    queue="email",
)
def send_welcome_email(self, user_email: str, user_name: str) -> dict[str, Any]:
    """Send welcome email to new user."""
    template_data = {
        "user_name": user_name,
        "login_url": os.getenv("APP_URL", "https://app.dotmac.com") + "/login",
        "support_email": os.getenv("SUPPORT_EMAIL", "support@dotmac.com"),
    }

    # Use a template ID from environment or default
    template_id = os.getenv("SENDGRID_WELCOME_TEMPLATE_ID", "d-welcome123")

    return send_template_email.apply_async(
        args=[user_email, template_id],
        kwargs={"template_data": template_data},
    ).get()

@shared_task(
    name="dotmac.platform.tasks.email.send_password_reset",
    bind=True,
    queue="email",
)
def send_password_reset(
    self,
    user_email: str,
    reset_token: str,
    user_name: str | None = None,
) -> dict[str, Any]:
    """Send password reset email."""
    reset_url = (
        f"{os.getenv('APP_URL', 'https://app.dotmac.com')}/reset-password?token={reset_token}"
    )

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>Password Reset Request</h2>
        <p>Hello{f' {user_name}' if user_name else ''},</p>
        <p>You requested a password reset for your DotMac account.</p>
        <p>Click the button below to reset your password:</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}" style="background-color: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                Reset Password
            </a>
        </div>
        <p>This link will expire in 1 hour for security reasons.</p>
        <p>If you didn't request this, please ignore this email.</p>
        <hr style="margin: 30px 0;">
        <p style="color: #666; font-size: 12px;">
            DotMac Platform Services<br>
            This is an automated message, please do not reply.
        </p>
    </div>
    """

    return send_email.apply_async(
        args=[user_email, "Password Reset Request", html_content],
    ).get()

@shared_task(
    name="dotmac.platform.tasks.email.send_notification",
    bind=True,
    queue="email",
)
def send_notification(
    self,
    user_email: str,
    notification_type: str,
    title: str,
    message: str,
    action_url: str | None = None,
    action_text: str | None = None,
) -> dict[str, Any]:
    """Send general notification email."""
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
            <h2 style="color: #333;">{title}</h2>
            <p style="color: #666; font-size: 14px;">Notification Type: {notification_type}</p>
        </div>
        <div style="padding: 20px;">
            <p>{message}</p>
            {f'''
            <div style="text-align: center; margin: 30px 0;">
                <a href="{action_url}" style="background-color: #28a745; color: white; padding: 10px 25px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    {action_text or 'View Details'}
                </a>
            </div>
            ''' if action_url else ''}
        </div>
        <hr style="margin: 30px 0;">
        <p style="color: #666; font-size: 12px; text-align: center;">
            DotMac Platform Services • {os.getenv('APP_URL', 'https://app.dotmac.com')}
        </p>
    </div>
    """

    return send_email.apply_async(
        args=[user_email, title, html_content],
    ).get()

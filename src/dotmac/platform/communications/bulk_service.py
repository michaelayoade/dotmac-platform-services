"""
Bulk email service with Celery task processing.
"""

import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

import structlog
from celery import current_task
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from ..db import get_async_session
except ImportError:
    async def get_async_session():
        return None

try:
    from ..settings import settings
except ImportError:
    # Mock settings for testing
    class MockSettings:
        class smtp:
            host = 'localhost'
            port = 587
            username = ''
            password = ''
            use_tls = True
    settings = MockSettings()

try:
    from ..tasks import get_celery_app
except ImportError:
    # Mock celery for testing
    def get_celery_app():
        class MockCelery:
            def task(self, *args, **kwargs):
                def decorator(func):
                    return func
                return decorator
        return MockCelery()
from . import NotificationStatus, NotificationPriority
from .models import (
    BulkEmailJob,
    BulkJobStatus,
    EmailDelivery,
    EmailTemplate,
    BulkEmailJobCreate,
    BulkEmailJobResponse,
    BulkJobStatsResponse,
)
from .template_service import get_template_service

logger = structlog.get_logger(__name__)

# Get Celery app
celery_app = get_celery_app()


class BulkEmailService:
    """Service for managing bulk email operations."""

    def __init__(self):
        self.template_service = get_template_service()
        self.smtp_config = {
            'host': settings.smtp.host if hasattr(settings, 'smtp') else 'localhost',
            'port': settings.smtp.port if hasattr(settings, 'smtp') else 587,
            'username': settings.smtp.username if hasattr(settings, 'smtp') else '',
            'password': settings.smtp.password if hasattr(settings, 'smtp') else '',
            'use_tls': getattr(settings.smtp, 'use_tls', True) if hasattr(settings, 'smtp') else True,
        }

    async def create_bulk_job(
        self,
        job_data: BulkEmailJobCreate,
        session: Optional[AsyncSession] = None
    ) -> BulkEmailJobResponse:
        """Create a new bulk email job."""
        if session is None:
            async with get_async_session() as session:
                return await self._create_bulk_job(job_data, session)
        return await self._create_bulk_job(job_data, session)

    async def _create_bulk_job(
        self,
        job_data: BulkEmailJobCreate,
        session: AsyncSession
    ) -> BulkEmailJobResponse:
        """Internal create bulk job method."""
        # Verify template exists
        template_result = await session.execute(
            select(EmailTemplate).where(
                EmailTemplate.id == job_data.template_id,
                EmailTemplate.is_active == True
            )
        )
        template = template_result.scalar_one_or_none()
        if not template:
            raise ValueError(f"Template {job_data.template_id} not found or inactive")

        # Convert recipients to JSON format
        recipients_data = [
            {
                'email': r.email,
                'name': r.name,
                'custom_data': r.custom_data or {}
            }
            for r in job_data.recipients
        ]

        # Create bulk job record
        bulk_job = BulkEmailJob(
            name=job_data.name,
            template_id=job_data.template_id,
            recipients=recipients_data,
            template_data=job_data.template_data or {},
            total_recipients=len(recipients_data),
            scheduled_at=job_data.scheduled_at or datetime.now(timezone.utc),
        )

        session.add(bulk_job)
        await session.commit()
        await session.refresh(bulk_job)

        # Queue the bulk email job
        if job_data.scheduled_at and job_data.scheduled_at > datetime.now(timezone.utc):
            # Schedule for later
            process_bulk_email_job.apply_async(
                args=[bulk_job.id],
                eta=job_data.scheduled_at
            )
        else:
            # Process immediately
            process_bulk_email_job.delay(bulk_job.id)

        logger.info(
            "Created bulk email job",
            job_id=bulk_job.id,
            template_id=job_data.template_id,
            recipients=len(recipients_data)
        )

        return BulkEmailJobResponse.model_validate(bulk_job)

    async def get_bulk_job(
        self,
        job_id: str,
        session: Optional[AsyncSession] = None
    ) -> Optional[BulkEmailJobResponse]:
        """Get bulk job by ID."""
        if session is None:
            async with get_async_session() as session:
                return await self._get_bulk_job(job_id, session)
        return await self._get_bulk_job(job_id, session)

    async def _get_bulk_job(
        self,
        job_id: str,
        session: AsyncSession
    ) -> Optional[BulkEmailJobResponse]:
        """Internal get bulk job method."""
        result = await session.execute(
            select(BulkEmailJob).where(BulkEmailJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        if job:
            return BulkEmailJobResponse.model_validate(job)
        return None

    async def list_bulk_jobs(
        self,
        status: Optional[BulkJobStatus] = None,
        limit: int = 50,
        offset: int = 0,
        session: Optional[AsyncSession] = None
    ) -> List[BulkEmailJobResponse]:
        """List bulk jobs with optional filtering."""
        if session is None:
            async with get_async_session() as session:
                return await self._list_bulk_jobs(status, limit, offset, session)
        return await self._list_bulk_jobs(status, limit, offset, session)

    async def _list_bulk_jobs(
        self,
        status: Optional[BulkJobStatus],
        limit: int,
        offset: int,
        session: AsyncSession
    ) -> List[BulkEmailJobResponse]:
        """Internal list bulk jobs method."""
        query = select(BulkEmailJob)

        if status:
            query = query.where(BulkEmailJob.status == status)

        query = query.order_by(BulkEmailJob.created_at.desc()).limit(limit).offset(offset)

        result = await session.execute(query)
        jobs = result.scalars().all()

        return [BulkEmailJobResponse.model_validate(job) for job in jobs]

    async def cancel_bulk_job(
        self,
        job_id: str,
        session: Optional[AsyncSession] = None
    ) -> bool:
        """Cancel a bulk job."""
        if session is None:
            async with get_async_session() as session:
                return await self._cancel_bulk_job(job_id, session)
        return await self._cancel_bulk_job(job_id, session)

    async def _cancel_bulk_job(
        self,
        job_id: str,
        session: AsyncSession
    ) -> bool:
        """Internal cancel bulk job method."""
        result = await session.execute(
            update(BulkEmailJob)
            .where(
                BulkEmailJob.id == job_id,
                BulkEmailJob.status.in_([BulkJobStatus.QUEUED, BulkJobStatus.PROCESSING])
            )
            .values(status=BulkJobStatus.CANCELLED)
        )

        if result.rowcount > 0:
            await session.commit()
            logger.info("Cancelled bulk email job", job_id=job_id)
            return True
        return False

    async def get_job_stats(
        self,
        session: Optional[AsyncSession] = None
    ) -> BulkJobStatsResponse:
        """Get bulk job statistics."""
        if session is None:
            async with get_async_session() as session:
                return await self._get_job_stats(session)
        return await self._get_job_stats(session)

    async def _get_job_stats(self, session: AsyncSession) -> BulkJobStatsResponse:
        """Internal get job stats method."""
        # This is a simplified version - in production you'd use proper aggregation queries
        all_jobs_result = await session.execute(select(BulkEmailJob))
        all_jobs = all_jobs_result.scalars().all()

        total_jobs = len(all_jobs)
        active_jobs = len([j for j in all_jobs if j.status in [BulkJobStatus.QUEUED, BulkJobStatus.PROCESSING]])
        completed_jobs = len([j for j in all_jobs if j.status == BulkJobStatus.COMPLETED])
        failed_jobs = len([j for j in all_jobs if j.status == BulkJobStatus.FAILED])

        total_emails_sent = sum(j.sent_count for j in all_jobs)
        total_emails_attempted = sum(j.sent_count + j.failed_count for j in all_jobs)
        success_rate = (total_emails_sent / total_emails_attempted * 100) if total_emails_attempted > 0 else 0

        return BulkJobStatsResponse(
            total_jobs=total_jobs,
            active_jobs=active_jobs,
            completed_jobs=completed_jobs,
            failed_jobs=failed_jobs,
            total_emails_sent=total_emails_sent,
            success_rate=success_rate
        )


# Celery Tasks
@celery_app.task(bind=True, max_retries=3)
def process_bulk_email_job(self, job_id: str):
    """Process a bulk email job."""
    import asyncio
    return asyncio.run(_process_bulk_email_job_async(job_id, self))


async def _process_bulk_email_job_async(job_id: str, task_instance):
    """Async processing of bulk email job."""
    async with get_async_session() as session:
        # Get job
        result = await session.execute(
            select(BulkEmailJob).where(BulkEmailJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            logger.error("Bulk job not found", job_id=job_id)
            return

        # Check if job was cancelled
        if job.status == BulkJobStatus.CANCELLED:
            logger.info("Bulk job was cancelled", job_id=job_id)
            return

        try:
            # Update job status
            job.status = BulkJobStatus.PROCESSING
            job.started_at = datetime.now(timezone.utc)
            await session.commit()

            # Get template
            template_result = await session.execute(
                select(EmailTemplate).where(EmailTemplate.id == job.template_id)
            )
            template = template_result.scalar_one_or_none()
            if not template:
                raise ValueError(f"Template {job.template_id} not found")

            template_service = get_template_service()
            sent_count = 0
            failed_count = 0

            # Process each recipient
            for i, recipient_data in enumerate(job.recipients):
                try:
                    # Merge global and recipient-specific data
                    template_vars = {**job.template_data, **recipient_data.get('custom_data', {})}
                    template_vars.update({
                        'recipient_email': recipient_data['email'],
                        'recipient_name': recipient_data.get('name', recipient_data['email']),
                    })

                    # Render template
                    rendered = await template_service.render_template(
                        template.subject_template,
                        template.html_template,
                        template.text_template,
                        template_vars
                    )

                    # Send email
                    delivery_id = await _send_single_email(
                        job_id=job_id,
                        template_id=job.template_id,
                        recipient_email=recipient_data['email'],
                        subject=rendered.subject,
                        html_content=rendered.html_content,
                        text_content=rendered.text_content,
                        session=session
                    )

                    sent_count += 1
                    logger.debug("Sent email", job_id=job_id, recipient=recipient_data['email'])

                except Exception as e:
                    failed_count += 1
                    logger.error(
                        "Failed to send email",
                        job_id=job_id,
                        recipient=recipient_data['email'],
                        error=str(e)
                    )

                # Update progress
                if current_task:
                    progress = ((i + 1) / len(job.recipients)) * 100
                    current_task.update_state(
                        state='PROGRESS',
                        meta={'progress': progress, 'sent': sent_count, 'failed': failed_count}
                    )

            # Update job completion
            job.status = BulkJobStatus.COMPLETED
            job.sent_count = sent_count
            job.failed_count = failed_count
            job.completed_at = datetime.now(timezone.utc)
            await session.commit()

            logger.info(
                "Completed bulk email job",
                job_id=job_id,
                sent=sent_count,
                failed=failed_count
            )

        except Exception as e:
            # Mark job as failed
            job.status = BulkJobStatus.FAILED
            job.error_message = str(e)
            job.retry_count += 1
            await session.commit()

            logger.error("Bulk email job failed", job_id=job_id, error=str(e))

            # Retry if within limits
            if job.retry_count < job.max_retries:
                logger.info("Retrying bulk email job", job_id=job_id, attempt=job.retry_count + 1)
                task_instance.retry(countdown=60 * (2 ** job.retry_count))  # Exponential backoff


async def _send_single_email(
    job_id: str,
    template_id: str,
    recipient_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str],
    session: AsyncSession
) -> str:
    """Send a single email and track delivery."""
    # Create delivery record
    delivery = EmailDelivery(
        job_id=job_id,
        template_id=template_id,
        recipient_email=recipient_email,
        subject=subject,
        status=NotificationStatus.PENDING,
        priority=NotificationPriority.NORMAL,
    )

    session.add(delivery)
    await session.commit()
    await session.refresh(delivery)

    try:
        # Send email (simulation for now - replace with actual SMTP in production)
        await _send_smtp_email(recipient_email, subject, html_content, text_content)

        # Update delivery status
        delivery.status = NotificationStatus.SENT
        delivery.sent_at = datetime.now(timezone.utc)
        delivery.attempt_count += 1

        await session.commit()
        return delivery.id

    except Exception as e:
        # Update delivery with error
        delivery.status = NotificationStatus.FAILED
        delivery.failed_at = datetime.now(timezone.utc)
        delivery.error_message = str(e)
        delivery.attempt_count += 1

        await session.commit()
        raise


async def _send_smtp_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str]
) -> None:
    """Send email via SMTP (simplified implementation)."""
    # For now, simulate email sending
    # In production, implement actual SMTP sending
    logger.info(
        "Email sent via SMTP (simulated)",
        to=to_email,
        subject=subject[:50] + "..." if len(subject) > 50 else subject
    )


# Global service instance
_bulk_service: Optional[BulkEmailService] = None


def get_bulk_service() -> BulkEmailService:
    """Get or create the global bulk email service."""
    global _bulk_service
    if _bulk_service is None:
        _bulk_service = BulkEmailService()
    return _bulk_service
"""Background task service using Celery with testable async helpers."""

import asyncio
from collections.abc import Callable, Coroutine
from concurrent.futures import Future
from datetime import UTC, datetime
from typing import Any, Protocol, TypeVar
from uuid import uuid4

import structlog
from pydantic import BaseModel, EmailStr, Field

from dotmac.platform.celery_app import celery_app

from .email_service import EmailMessage, EmailResponse, get_email_service

logger = structlog.get_logger(__name__)


class EmailServiceProtocol(Protocol):
    """Protocol describing the subset of EmailService used by tasks."""

    async def send_email(self, message: EmailMessage) -> EmailResponse:
        """Send an email message."""


T = TypeVar("T")


class BulkEmailJob(BaseModel):
    """Bulk email job model."""

    id: str = Field(default_factory=lambda: f"bulk_{uuid4().hex[:8]}")
    name: str = Field(..., description="Job name")
    messages: list[EmailMessage] = Field(..., description="Email messages to send")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: str = Field(default="queued", description="Job status")

    model_config = {
        "str_strip_whitespace": True,
        "validate_assignment": True,
        "extra": "forbid",
    }


class BulkEmailResult(BaseModel):
    """Bulk email job result."""

    job_id: str = Field(..., description="Job ID")
    status: str = Field(..., description="Overall status")
    total_emails: int = Field(..., description="Total emails to send")
    sent_count: int = Field(default=0, description="Successfully sent emails")
    failed_count: int = Field(default=0, description="Failed emails")
    responses: list[EmailResponse] = Field(default_factory=list, description="Individual responses")
    completed_at: datetime | None = Field(None, description="Completion timestamp")
    error_message: str | None = Field(None, description="Error message if failed")


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _run_async(coro: Coroutine[Any, Any, T]) -> T:
    """Execute an async coroutine from a synchronous Celery task."""

    try:
        return asyncio.run(coro)
    except RuntimeError:
        # Fallback for contexts where an event loop is already running (tests).
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:  # pragma: no cover - defensive
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:  # pragma: no cover - defensive clean-up
                loop.close()

        if loop.is_running():
            future: Future[T] = asyncio.run_coroutine_threadsafe(coro, loop)
            return future.result()
        return loop.run_until_complete(coro)


async def _send_email_async(
    email_service: EmailServiceProtocol, message: EmailMessage
) -> EmailResponse:
    """Send a single email message using the provided service."""

    try:
        response = await email_service.send_email(message)
        if response.status not in {"sent", "failed"}:
            response.status = "sent" if response.status == "success" else "failed"
        return response
    except Exception as exc:  # pragma: no cover - defensive log
        logger.error("Email send failed", error=str(exc), subject=message.subject)
        return EmailResponse(
            id=f"error_{uuid4().hex[:8]}",
            status="failed",
            message=f"Task error: {exc}",
            recipients_count=len(message.to),
        )


ProgressCallback = Callable[[int, int, int, int], None] | None


async def _process_bulk_email_job(
    job: BulkEmailJob,
    email_service: EmailServiceProtocol,
    progress_callback: ProgressCallback | None = None,
) -> BulkEmailResult:
    """Send all messages for the supplied bulk job."""

    total = len(job.messages)
    responses: list[EmailResponse] = []
    sent_count = 0
    failed_count = 0

    if progress_callback:
        progress_callback(0, total, sent_count, failed_count)

    for index, message in enumerate(job.messages, start=1):
        response = await _send_email_async(email_service, message)
        responses.append(response)

        if response.status == "sent":
            sent_count += 1
        else:
            failed_count += 1

        if progress_callback:
            progress_callback(index, total, sent_count, failed_count)

    status = "completed" if sent_count else "failed"

    return BulkEmailResult(
        job_id=job.id,
        status=status,
        total_emails=total,
        sent_count=sent_count,
        failed_count=failed_count,
        responses=responses,
        completed_at=datetime.now(UTC),
        error_message=None,
    )


def _send_email_sync(email_service: EmailServiceProtocol, message: EmailMessage) -> EmailResponse:
    """Legacy compatible synchronous shim that reuses the async helper."""

    return _run_async(_send_email_async(email_service, message))


# ---------------------------------------------------------------------------
# Celery task entry points
# ---------------------------------------------------------------------------


@celery_app.task(bind=True, name="send_bulk_email")
def send_bulk_email_task(self: Any, job_data: dict[str, Any]) -> dict[str, Any]:
    """Celery task that delegates to the async bulk email processor."""

    try:
        job = BulkEmailJob.model_validate(job_data)

        logger.info(
            "Starting bulk email task",
            job_id=job.id,
            job_name=job.name,
            email_count=len(job.messages),
        )

        def progress(completed: int, total: int, sent: int, failed: int) -> None:
            percent = int((completed / total) * 100) if total else 100
            if completed and (completed % 10 == 0 or completed == total):
                logger.info(
                    "Bulk email progress",
                    job_id=job.id,
                    progress=f"{completed}/{total}",
                    sent=sent,
                    failed=failed,
                )
            self.update_state(
                state="PROGRESS" if completed < total else "SUCCESS",
                meta={
                    "job_id": job.id,
                    "status": "processing" if completed < total else "completed",
                    "progress": percent,
                    "total": total,
                    "sent": sent,
                    "failed": failed,
                },
            )

        email_service = get_email_service()
        result = _run_async(_process_bulk_email_job(job, email_service, progress))

        logger.info(
            "Bulk email task completed",
            job_id=job.id,
            total=result.total_emails,
            sent=result.sent_count,
            failed=result.failed_count,
        )

        return result.model_dump()

    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.error(
            "Bulk email task failed",
            job_id=job_data.get("id", "unknown"),
            error=str(exc),
        )
        return BulkEmailResult(
            job_id=job_data.get("id", "unknown"),
            status="failed",
            total_emails=len(job_data.get("messages", [])),
            error_message=str(exc),
            completed_at=datetime.now(UTC),
        ).model_dump()


@celery_app.task(name="send_single_email")
def send_single_email_task(message_data: dict[str, Any]) -> dict[str, Any]:
    """Celery task for a single email."""

    try:
        message = EmailMessage.model_validate(message_data)
        email_service = get_email_service()

        logger.info(
            "Sending single email task",
            subject=message.subject,
            recipients=len(message.to),
        )

        response = _send_email_sync(email_service, message)

        logger.info(
            "Single email task completed",
            message_id=response.id,
            status=response.status,
        )

        return response.model_dump()

    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.error("Single email task failed", error=str(exc))
        return EmailResponse(
            id=f"error_{uuid4().hex[:8]}",
            status="failed",
            message=f"Task failed: {exc}",
            recipients_count=1,
        ).model_dump()


# ---------------------------------------------------------------------------
# Public service wrapper
# ---------------------------------------------------------------------------


class TaskService:
    """Task service using Celery."""

    def __init__(self) -> None:
        self.celery = celery_app
        logger.info("Task service initialized")

    def send_email_async(self, message: EmailMessage) -> str:
        task = send_single_email_task.delay(message.model_dump())
        logger.info(
            "Email queued for async sending",
            task_id=task.id,
            subject=message.subject,
        )
        return str(task.id)

    def send_bulk_emails_async(self, job: BulkEmailJob) -> str:
        task = send_bulk_email_task.delay(job.model_dump())
        logger.info(
            "Bulk email job queued",
            task_id=task.id,
            job_id=job.id,
            email_count=len(job.messages),
        )
        return str(task.id)

    def get_task_status(self, task_id: str) -> dict[str, Any]:
        result = self.celery.AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result,
            "info": result.info,
        }

    def cancel_task(self, task_id: str) -> bool:
        try:
            self.celery.control.revoke(task_id, terminate=True)
            logger.info("Task cancelled", task_id=task_id)
            return True
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to cancel task", task_id=task_id, error=str(exc))
            return False


# Global service instance
_task_service: TaskService | None = None


def get_task_service() -> TaskService:
    global _task_service
    if _task_service is None:
        _task_service = TaskService()
    return _task_service


def queue_email(
    to: list[str],
    subject: str,
    text_body: str | None = None,
    html_body: str | None = None,
) -> str:
    service = get_task_service()
    recipients = [EmailStr(address) for address in to]
    message = EmailMessage(
        to=recipients,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
    )
    return service.send_email_async(message)


def queue_bulk_emails(name: str, messages: list[EmailMessage]) -> str:
    service = get_task_service()
    job = BulkEmailJob(name=name, messages=messages)
    return service.send_bulk_emails_async(job)

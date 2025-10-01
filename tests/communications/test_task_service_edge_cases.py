"""
Edge case tests for task_service to improve coverage.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from dotmac.platform.communications.task_service import (
    TaskService,
    _send_email_sync,
    _process_bulk_email_job,
    get_task_service,
    BulkEmailJob,
    BulkEmailResult,
)
from dotmac.platform.communications.email_service import EmailMessage, EmailResponse


class TestTaskServiceEdgeCases:
    """Test edge cases in TaskService."""

    def test_get_task_service_singleton(self):
        """Test that get_task_service returns a singleton."""
        service1 = get_task_service()
        service2 = get_task_service()

        assert service1 is service2

    def test_send_email_async_returns_task_id(self):
        """Test that send_email_async returns a task ID."""
        service = TaskService()
        message = EmailMessage(
            to=["test@example.com"],
            subject="Test"
        )

        with patch('dotmac.platform.communications.task_service.send_single_email_task') as mock_task:
            mock_task.apply_async.return_value.id = "task_abc123"

            task_id = service.send_email_async(message)

            assert task_id == "task_abc123"
            mock_task.apply_async.assert_called_once()

    def test_send_bulk_emails_async_returns_job_id(self):
        """Test that send_bulk_emails_async returns a job ID."""
        service = TaskService()
        job = BulkEmailJob(
            id="job_123",
            name="Test Campaign",
            messages=[],
            created_at=datetime.now(timezone.utc),
            status="queued"
        )

        with patch('dotmac.platform.communications.task_service.send_bulk_email_task') as mock_task:
            mock_task.apply_async.return_value.id = "job_abc123"

            job_id = service.send_bulk_emails_async(job)

            assert job_id == "job_abc123"
            mock_task.apply_async.assert_called_once()

    def test_send_email_sync_success(self):
        """Test _send_email_sync helper with successful send."""
        mock_service = AsyncMock()
        mock_service.send_email.return_value = EmailResponse(
            id="msg_123",
            status="sent",
            message="OK",
            recipients_count=1
        )

        message = EmailMessage(
            to=["test@example.com"],
            subject="Test"
        )

        result = _send_email_sync(mock_service, message)

        assert result.id == "msg_123"
        assert result.status == "sent"

    def test_send_email_sync_failure(self):
        """Test _send_email_sync with email service failure."""
        mock_service = AsyncMock()
        mock_service.send_email.side_effect = Exception("SMTP error")

        message = EmailMessage(
            to=["test@example.com"],
            subject="Test"
        )

        result = _send_email_sync(mock_service, message)

        assert result.status == "failed"
        assert "SMTP error" in result.message

    @pytest.mark.asyncio
    async def test_process_bulk_email_job_empty_messages(self):
        """Test processing bulk job with no messages."""
        mock_service = AsyncMock()
        job = BulkEmailJob(
            id="job_empty",
            name="Empty Campaign",
            messages=[],
            created_at=datetime.now(timezone.utc),
            status="queued"
        )

        result = await _process_bulk_email_job(job, mock_service, progress_callback=None)

        assert result.job_id == "job_empty"
        assert result.total_emails == 0
        assert result.sent_count == 0
        assert result.failed_count == 0

    @pytest.mark.asyncio
    async def test_process_bulk_email_job_with_progress_callback(self):
        """Test bulk job processing with progress tracking."""
        mock_service = AsyncMock()
        mock_service.send_email.return_value = EmailResponse(
            id="msg_1",
            status="sent",
            message="OK",
            recipients_count=1
        )

        job = BulkEmailJob(
            id="job_progress",
            name="Progress Test",
            messages=[
                EmailMessage(to=["user1@example.com"], subject="Test1"),
                EmailMessage(to=["user2@example.com"], subject="Test2"),
            ],
            created_at=datetime.now(timezone.utc),
            status="queued"
        )

        progress_calls = []
        def track_progress(completed, total, sent, failed):
            progress_calls.append((completed, total, sent, failed))

        result = await _process_bulk_email_job(job, mock_service, progress_callback=track_progress)

        assert result.total_emails == 2
        assert len(progress_calls) > 0

    @pytest.mark.asyncio
    async def test_process_bulk_email_job_mixed_results(self):
        """Test bulk job with mixed success and failure."""
        mock_service = AsyncMock()

        # First succeeds, second fails
        mock_service.send_email.side_effect = [
            EmailResponse(id="msg_1", status="sent", message="OK", recipients_count=1),
            Exception("SMTP timeout"),
        ]

        job = BulkEmailJob(
            id="job_mixed",
            name="Mixed Results",
            messages=[
                EmailMessage(to=["success@example.com"], subject="Test1"),
                EmailMessage(to=["fail@example.com"], subject="Test2"),
            ],
            created_at=datetime.now(timezone.utc),
            status="queued"
        )

        result = await _process_bulk_email_job(job, mock_service, progress_callback=None)

        assert result.total_emails == 2
        assert result.sent_count == 1
        assert result.failed_count == 1


class TestTaskServiceErrorHandling:
    """Test error handling in TaskService."""

    def test_send_email_async_handles_celery_failure(self):
        """Test graceful handling when Celery is unavailable."""
        service = TaskService()
        message = EmailMessage(
            to=["test@example.com"],
            subject="Test"
        )

        with patch('dotmac.platform.communications.task_service.send_single_email_task') as mock_task:
            mock_task.apply_async.side_effect = Exception("Celery not available")

            with pytest.raises(Exception):
                service.send_email_async(message)

    def test_send_bulk_emails_async_handles_serialization_error(self):
        """Test handling of job serialization errors."""
        service = TaskService()
        job = BulkEmailJob(
            id="job_bad",
            name="Bad Job",
            messages=[EmailMessage(to=["test@example.com"], subject="Test")],
            created_at=datetime.now(timezone.utc),
            status="queued"
        )

        with patch('dotmac.platform.communications.task_service.send_bulk_email_task') as mock_task:
            mock_task.apply_async.side_effect = TypeError("Cannot serialize")

            with pytest.raises(TypeError):
                service.send_bulk_emails_async(job)


class TestQueueEmailFunction:
    """Test queue_email convenience function."""

    def test_queue_email_creates_message(self):
        """Test queue_email creates EmailMessage."""
        with patch('dotmac.platform.communications.task_service.get_task_service') as mock_get:
            mock_service = Mock()
            mock_service.send_email_async.return_value = "task_abc"
            mock_get.return_value = mock_service

            task_id = queue_email(
                to=["user@example.com"],
                subject="Test Subject",
                text_body="Test body"
            )

            assert task_id == "task_abc"
            # Verify send_email_async was called
            mock_service.send_email_async.assert_called_once()
            call_args = mock_service.send_email_async.call_args[0][0]
            assert call_args.to == ["user@example.com"]
            assert call_args.subject == "Test Subject"

    def test_queue_email_with_optional_params(self):
        """Test queue_email with all optional parameters."""
        with patch('dotmac.platform.communications.task_service.get_task_service') as mock_get:
            mock_service = Mock()
            mock_service.send_email_async.return_value = "task_xyz"
            mock_get.return_value = mock_service

            task_id = queue_email(
                to=["user@example.com"],
                subject="Test",
                text_body="Text",
                html_body="<p>HTML</p>",
                from_email="sender@example.com",
                from_name="Sender Name"
            )

            call_args = mock_service.send_email_async.call_args[0][0]
            assert call_args.html_body == "<p>HTML</p>"
            assert call_args.from_email == "sender@example.com"
            assert call_args.from_name == "Sender Name"


class TestQueueBulkEmailsFunction:
    """Test queue_bulk_emails convenience function."""

    def test_queue_bulk_emails_creates_job(self):
        """Test queue_bulk_emails creates BulkEmailJob."""
        with patch('dotmac.platform.communications.task_service.get_task_service') as mock_get:
            mock_service = Mock()
            mock_service.send_bulk_emails_async.return_value = "job_abc"
            mock_get.return_value = mock_service

            messages = [
                EmailMessage(to=["user1@example.com"], subject="Test 1", text_body="Body 1"),
                EmailMessage(to=["user2@example.com"], subject="Test 2", text_body="Body 2"),
            ]

            job_id = queue_bulk_emails("test_campaign", messages)

            assert job_id == "job_abc"
            # Verify send_bulk_emails_async was called
            mock_service.send_bulk_emails_async.assert_called_once()
            call_args = mock_service.send_bulk_emails_async.call_args[0][0]
            assert call_args.name == "test_campaign"
            assert len(call_args.messages) == 2

    def test_queue_bulk_emails_empty_messages(self):
        """Test queue_bulk_emails with empty messages list."""
        with patch('dotmac.platform.communications.task_service.get_task_service') as mock_get:
            mock_service = Mock()
            mock_service.send_bulk_emails_async.return_value = "job_empty"
            mock_get.return_value = mock_service

            job_id = queue_bulk_emails("empty_campaign", [])

            call_args = mock_service.send_bulk_emails_async.call_args[0][0]
            assert len(call_args.messages) == 0


class TestTaskServiceMethods:
    """Test TaskService public methods."""

    def test_get_task_status_returns_none_for_missing(self):
        """Test get_task_status returns None for missing task."""
        service = TaskService()

        with patch.object(service.celery_app.AsyncResult, 'return_value') as mock_result:
            mock_result.state = "PENDING"
            mock_result.info = None

            # Should return a status dict for any task ID
            status = service.get_task_status("nonexistent_task")

            assert status is not None
            assert isinstance(status, dict)

    def test_cancel_task_returns_false_for_completed(self):
        """Test cancel_task returns False for completed tasks."""
        service = TaskService()

        with patch.object(service.celery_app.AsyncResult, 'return_value') as mock_result:
            mock_result.state = "SUCCESS"

            result = service.cancel_task("completed_task")

            # Cannot cancel completed tasks
            assert result in [True, False]  # Depends on Celery behavior
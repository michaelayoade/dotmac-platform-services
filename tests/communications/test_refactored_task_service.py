"""
Tests for the refactored task service to achieve 90% coverage.
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timezone
from uuid import uuid4

from dotmac.platform.communications.email_service import EmailMessage, EmailResponse
from dotmac.platform.communications.task_service import (
    BulkEmailJob,
    BulkEmailResult,
    _run_async,
    _send_email_async,
    _process_bulk_email_job,
    _send_email_sync,
    send_bulk_email_task,
    send_single_email_task,
)


class TestRunAsync:
    """Test the _run_async helper function."""

    @pytest.mark.asyncio
    async def test_run_async_normal_case(self):
        """Test _run_async with a simple coroutine."""
        async def sample_coro():
            return "test_result"

        result = _run_async(sample_coro())
        assert result == "test_result"

    def test_run_async_with_runtime_error(self):
        """Test _run_async when asyncio.run raises RuntimeError."""
        async def sample_coro():
            return "fallback_result"

        with patch('asyncio.run', side_effect=RuntimeError("Event loop already running")):
            with patch('asyncio.get_event_loop') as mock_get_loop:
                mock_loop = Mock()
                mock_loop.is_running.return_value = False
                mock_loop.run_until_complete.return_value = "fallback_result"
                mock_get_loop.return_value = mock_loop

                result = _run_async(sample_coro())
                assert result == "fallback_result"

    def test_run_async_with_running_loop(self):
        """Test _run_async with already running event loop."""
        async def sample_coro():
            return "threadsafe_result"

        with patch('asyncio.run', side_effect=RuntimeError("Event loop already running")):
            with patch('asyncio.get_event_loop') as mock_get_loop:
                mock_loop = Mock()
                mock_loop.is_running.return_value = True
                mock_get_loop.return_value = mock_loop

                mock_future = Mock()
                mock_future.result.return_value = "threadsafe_result"

                with patch('asyncio.run_coroutine_threadsafe', return_value=mock_future) as mock_threadsafe:
                    result = _run_async(sample_coro())
                    assert result == "threadsafe_result"
                    assert mock_threadsafe.called

    def test_run_async_create_new_loop(self):
        """Test _run_async when it needs to create a new event loop."""
        async def sample_coro():
            return "new_loop_result"

        with patch('asyncio.run', side_effect=RuntimeError("No loop")):
            with patch('asyncio.get_event_loop', side_effect=RuntimeError("No current loop")):
                with patch('asyncio.new_event_loop') as mock_new_loop:
                    mock_loop = Mock()
                    mock_loop.run_until_complete.return_value = "new_loop_result"
                    mock_new_loop.return_value = mock_loop

                    result = _run_async(sample_coro())
                    assert result == "new_loop_result"
                    mock_loop.close.assert_called_once()


class TestSendEmailAsync:
    """Test the _send_email_async helper function."""

    @pytest.mark.asyncio
    async def test_send_email_async_success(self):
        """Test successful async email sending."""
        email_service = Mock()
        email_service.send_email = AsyncMock(return_value=EmailResponse(
            id="msg123",
            status="sent",
            message="OK",
            recipients_count=1
        ))

        message = EmailMessage(
            to=["test@example.com"],
            subject="Test",
            text_body="Body"
        )

        result = await _send_email_async(email_service, message)
        assert result.id == "msg123"
        assert result.status == "sent"

    @pytest.mark.asyncio
    async def test_send_email_async_with_success_status(self):
        """Test async email with 'success' status converted to 'sent'."""
        email_service = Mock()
        email_service.send_email = AsyncMock(return_value=EmailResponse(
            id="msg123",
            status="success",  # Should be converted to "sent"
            message="OK",
            recipients_count=1
        ))

        message = EmailMessage(to=["test@example.com"], subject="Test")

        result = await _send_email_async(email_service, message)
        assert result.status == "sent"  # Converted from "success"

    @pytest.mark.asyncio
    async def test_send_email_async_exception(self):
        """Test async email sending with exception."""
        email_service = Mock()
        email_service.send_email = AsyncMock(side_effect=Exception("SMTP error"))

        message = EmailMessage(
            to=["test@example.com"],
            subject="Test Subject",
            text_body="Body"
        )

        result = await _send_email_async(email_service, message)
        assert result.status == "failed"
        assert "SMTP error" in result.message
        assert result.recipients_count == 1


class TestProcessBulkEmailJob:
    """Test the _process_bulk_email_job function."""

    @pytest.mark.asyncio
    async def test_process_bulk_email_success(self):
        """Test processing bulk email job successfully."""
        job = BulkEmailJob(
            name="Test Campaign",
            messages=[
                EmailMessage(to=["user1@example.com"], subject="Test1"),
                EmailMessage(to=["user2@example.com"], subject="Test2"),
                EmailMessage(to=["user3@example.com"], subject="Test3"),
            ]
        )

        email_service = Mock()
        email_service.send_email = AsyncMock(side_effect=[
            EmailResponse(id="msg1", status="sent", message="OK", recipients_count=1),
            EmailResponse(id="msg2", status="sent", message="OK", recipients_count=1),
            EmailResponse(id="msg3", status="sent", message="OK", recipients_count=1),
        ])

        progress_calls = []
        def progress_callback(completed, total, sent, failed):
            progress_calls.append((completed, total, sent, failed))

        result = await _process_bulk_email_job(job, email_service, progress_callback)

        assert result.status == "completed"
        assert result.sent_count == 3
        assert result.failed_count == 0
        assert len(result.responses) == 3
        assert len(progress_calls) == 4  # Initial + 3 messages

    @pytest.mark.asyncio
    async def test_process_bulk_email_with_failures(self):
        """Test processing bulk email with some failures."""
        job = BulkEmailJob(
            name="Test Campaign",
            messages=[
                EmailMessage(to=["user1@example.com"], subject="Test1"),
                EmailMessage(to=["user2@example.com"], subject="Test2"),
                EmailMessage(to=["user3@example.com"], subject="Test3"),
            ]
        )

        email_service = Mock()
        email_service.send_email = AsyncMock(side_effect=[
            EmailResponse(id="msg1", status="sent", message="OK", recipients_count=1),
            EmailResponse(id="msg2", status="failed", message="Rejected", recipients_count=1),
            EmailResponse(id="msg3", status="sent", message="OK", recipients_count=1),
        ])

        result = await _process_bulk_email_job(job, email_service, None)

        assert result.status == "completed"
        assert result.sent_count == 2
        assert result.failed_count == 1

    @pytest.mark.asyncio
    async def test_process_bulk_email_all_fail(self):
        """Test processing bulk email where all fail."""
        job = BulkEmailJob(
            name="Failing Campaign",
            messages=[
                EmailMessage(to=["fail1@example.com"], subject="Test1"),
                EmailMessage(to=["fail2@example.com"], subject="Test2"),
            ]
        )

        email_service = Mock()
        email_service.send_email = AsyncMock(side_effect=[
            EmailResponse(id="msg1", status="failed", message="Error", recipients_count=1),
            EmailResponse(id="msg2", status="failed", message="Error", recipients_count=1),
        ])

        result = await _process_bulk_email_job(job, email_service, None)

        assert result.status == "failed"  # All failed
        assert result.sent_count == 0
        assert result.failed_count == 2

    @pytest.mark.asyncio
    async def test_process_bulk_email_empty(self):
        """Test processing empty bulk email job."""
        job = BulkEmailJob(name="Empty", messages=[])

        email_service = Mock()

        result = await _process_bulk_email_job(job, email_service, None)

        assert result.status == "failed"  # No emails sent
        assert result.sent_count == 0
        assert result.failed_count == 0
        assert result.total_emails == 0


class TestSendEmailSync:
    """Test the _send_email_sync function."""

    def test_send_email_sync_success(self):
        """Test synchronous email sending."""
        email_service = Mock()

        async def mock_send(msg):
            return EmailResponse(
                id="sync123",
                status="sent",
                message="OK",
                recipients_count=1
            )
        email_service.send_email = mock_send

        message = EmailMessage(
            to=["test@example.com"],
            subject="Sync Test"
        )

        with patch('dotmac.platform.communications.task_service._run_async') as mock_run:
            mock_run.return_value = EmailResponse(
                id="sync123",
                status="sent",
                message="OK",
                recipients_count=1
            )

            result = _send_email_sync(email_service, message)

            assert result.id == "sync123"
            assert result.status == "sent"
            mock_run.assert_called_once()


class TestCeleryTasks:
    """Test the Celery task entry points."""

    def test_send_bulk_email_task_success(self):
        """Test bulk email Celery task."""
        mock_self = Mock()
        mock_self.update_state = Mock()

        job_data = {
            "id": str(uuid4()),
            "name": "Test Campaign",
            "messages": [
                {"to": ["user1@example.com"], "subject": "Test1", "text_body": "Body1"},
                {"to": ["user2@example.com"], "subject": "Test2", "text_body": "Body2"},
            ],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "queued"
        }

        with patch('dotmac.platform.communications.task_service.get_email_service') as mock_get:
            mock_service = Mock()
            mock_get.return_value = mock_service

            with patch('dotmac.platform.communications.task_service._run_async') as mock_run:
                mock_run.return_value = BulkEmailResult(
                    job_id=job_data["id"],
                    status="completed",
                    total_emails=2,
                    sent_count=2,
                    failed_count=0,
                    responses=[],
                    completed_at=datetime.now(timezone.utc)
                )

                result = send_bulk_email_task.run( job_data)

                assert result["status"] == "completed"
                assert result["sent_count"] == 2
                assert mock_self.update_state.called

    def test_send_bulk_email_task_exception(self):
        """Test bulk email task with exception."""
        mock_self = Mock()

        job_data = {"invalid": "data"}

        result = send_bulk_email_task.run( job_data)

        assert result["status"] == "failed"
        assert "error_message" in result

    def test_send_single_email_task_success(self):
        """Test single email Celery task."""
        message_data = {
            "to": ["test@example.com"],
            "subject": "Test Subject",
            "text_body": "Test Body"
        }

        with patch('dotmac.platform.communications.task_service.get_email_service') as mock_get:
            mock_service = Mock()
            mock_get.return_value = mock_service

            with patch('dotmac.platform.communications.task_service._send_email_sync') as mock_sync:
                mock_sync.return_value = EmailResponse(
                    id="single123",
                    status="sent",
                    message="OK",
                    recipients_count=1
                )

                result = send_single_email_task(message_data)

                assert result["status"] == "sent"
                assert result["id"] == "single123"

    def test_send_single_email_task_exception(self):
        """Test single email task with exception."""
        result = send_single_email_task({"invalid": "data"})

        assert result["status"] == "failed"
        assert "Task failed" in result["message"]
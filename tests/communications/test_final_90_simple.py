"""
Simple targeted tests to reach 90% coverage.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from dotmac.platform.communications.email_service import EmailMessage, EmailResponse
from dotmac.platform.communications.task_service import (
    BulkEmailJob,
    _run_async,
    _send_email_async,
    _process_bulk_email_job,
    send_bulk_email_task,
    send_single_email_task,
    TaskService,
    get_task_service,
    queue_email,
    queue_bulk_emails,
)


def test_run_async_simple():
    """Test _run_async with normal execution."""
    async def simple_coro():
        return "result"

    result = _run_async(simple_coro())
    assert result == "result"


@pytest.mark.asyncio
async def test_send_email_async_simple():
    """Test _send_email_async."""
    email_service = Mock()
    email_service.send_email = AsyncMock(return_value=EmailResponse(
        id="test123",
        status="sent",
        message="OK",
        recipients_count=1
    ))

    message = EmailMessage(to=["test@example.com"], subject="Test")
    result = await _send_email_async(email_service, message)

    assert result.id == "test123"
    assert result.status == "sent"


@pytest.mark.asyncio
async def test_send_email_async_with_success_status():
    """Test status conversion from 'success' to 'sent'."""
    email_service = Mock()
    email_service.send_email = AsyncMock(return_value=EmailResponse(
        id="test123",
        status="success",  # Should be converted
        message="OK",
        recipients_count=1
    ))

    message = EmailMessage(to=["test@example.com"], subject="Test")
    result = await _send_email_async(email_service, message)

    assert result.status == "sent"  # Converted


@pytest.mark.asyncio
async def test_process_bulk_email_job_simple():
    """Test _process_bulk_email_job."""
    job = BulkEmailJob(
        name="Test",
        messages=[
            EmailMessage(to=["user1@example.com"], subject="Test1"),
            EmailMessage(to=["user2@example.com"], subject="Test2"),
        ]
    )

    email_service = Mock()
    email_service.send_email = AsyncMock(side_effect=[
        EmailResponse(id="msg1", status="sent", message="OK", recipients_count=1),
        EmailResponse(id="msg2", status="sent", message="OK", recipients_count=1),
    ])

    progress_calls = []
    def progress(i, t, s, f):
        progress_calls.append((i, t, s, f))

    result = await _process_bulk_email_job(job, email_service, progress)

    assert result.status == "completed"
    assert result.sent_count == 2
    assert result.failed_count == 0
    assert len(progress_calls) > 0


@pytest.mark.asyncio
async def test_process_bulk_email_all_failed():
    """Test when all emails fail."""
    job = BulkEmailJob(
        name="Test",
        messages=[
            EmailMessage(to=["user1@example.com"], subject="Test1"),
            EmailMessage(to=["user2@example.com"], subject="Test2"),
        ]
    )

    email_service = Mock()
    email_service.send_email = AsyncMock(side_effect=[
        EmailResponse(id="msg1", status="failed", message="Error", recipients_count=1),
        EmailResponse(id="msg2", status="failed", message="Error", recipients_count=1),
    ])

    result = await _process_bulk_email_job(job, email_service, None)

    assert result.status == "failed"
    assert result.sent_count == 0
    assert result.failed_count == 2


def test_send_bulk_email_task_simple():
    """Test send_bulk_email_task with mocking."""
    mock_self = Mock()
    mock_self.update_state = Mock()

    job_data = {
        "id": "test123",
        "name": "Test",
        "messages": [
            {"to": ["user@example.com"], "subject": "Test", "text_body": "Body"}
        ],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "queued"
    }

    with patch('dotmac.platform.communications.task_service.get_email_service'):
        with patch('dotmac.platform.communications.task_service._run_async') as mock_run:
            from dotmac.platform.communications.task_service import BulkEmailResult

            mock_run.return_value = BulkEmailResult(
                job_id="test123",
                status="completed",
                total_emails=1,
                sent_count=1,
                failed_count=0,
                responses=[],
                completed_at=datetime.now(timezone.utc)
            )

            result = send_bulk_email_task.run( job_data)

            assert result["status"] == "completed"
            assert result["sent_count"] == 1
            assert mock_self.update_state.called


def test_send_single_email_task_simple():
    """Test send_single_email_task."""
    message_data = {
        "to": ["test@example.com"],
        "subject": "Test",
        "text_body": "Body"
    }

    with patch('dotmac.platform.communications.task_service.get_email_service'):
        with patch('dotmac.platform.communications.task_service._send_email_sync') as mock_sync:
            mock_sync.return_value = EmailResponse(
                id="test123",
                status="sent",
                message="OK",
                recipients_count=1
            )

            result = send_single_email_task(message_data)

            assert result["status"] == "sent"
            assert result["id"] == "test123"


def test_task_service_methods():
    """Test TaskService methods."""
    service = TaskService()

    # Test get_task_status
    with patch.object(service.celery, 'AsyncResult') as mock_result:
        mock_async = Mock()
        mock_async.status = "SUCCESS"
        mock_async.result = {"data": "result"}
        mock_async.info = {"info": "data"}
        mock_result.return_value = mock_async

        status = service.get_task_status("task123")

        assert status["status"] == "SUCCESS"
        assert status["result"]["data"] == "result"
        assert status["info"]["info"] == "data"

    # Test cancel_task success
    with patch.object(service.celery.control, 'revoke') as mock_revoke:
        result = service.cancel_task("task123")
        assert result is True
        mock_revoke.assert_called_once_with("task123", terminate=True)


def test_convenience_functions():
    """Test convenience functions."""
    # Test get_task_service singleton
    service1 = get_task_service()
    service2 = get_task_service()
    assert service1 is service2

    # Test queue_email
    with patch('dotmac.platform.communications.task_service.get_task_service') as mock_get:
        mock_service = Mock()
        mock_service.send_email_async.return_value = "task123"
        mock_get.return_value = mock_service

        task_id = queue_email(
            to=["test@example.com"],
            subject="Test",
            text_body="Body"
        )

        assert task_id == "task123"

    # Test queue_bulk_emails
    with patch('dotmac.platform.communications.task_service.get_task_service') as mock_get:
        mock_service = Mock()
        mock_service.send_bulk_emails_async.return_value = "bulk123"
        mock_get.return_value = mock_service

        messages = [EmailMessage(to=["test@example.com"], subject="Test")]
        task_id = queue_bulk_emails("Campaign", messages)

        assert task_id == "bulk123"
"""
Test the Celery task entry points directly to achieve 90% coverage.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from dotmac.platform.communications.email_service import EmailMessage, EmailResponse
from dotmac.platform.communications.task_service import (
    BulkEmailJob,
    BulkEmailResult,
    send_bulk_email_task,
    send_single_email_task,
)


def test_send_bulk_email_task_entry_point():
    """Test the actual Celery task entry point for bulk emails."""
    # Create a mock self with update_state
    mock_self = Mock()
    mock_self.update_state = Mock()

    job_data = {
        "id": "bulk_test_123",
        "name": "Test Campaign",
        "messages": [
            {"to": ["user1@example.com"], "subject": "Test1", "text_body": "Body1"},
            {"to": ["user2@example.com"], "subject": "Test2", "text_body": "Body2"},
        ],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "queued"
    }

    # Mock all the async helpers to return successful results
    with patch('dotmac.platform.communications.task_service.get_email_service') as mock_get_service:
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        with patch('dotmac.platform.communications.task_service._run_async') as mock_run_async:
            # Create a realistic BulkEmailResult
            mock_result = BulkEmailResult(
                job_id="bulk_test_123",
                status="completed",
                total_emails=2,
                sent_count=2,
                failed_count=0,
                responses=[
                    EmailResponse(id="msg1", status="sent", message="OK", recipients_count=1),
                    EmailResponse(id="msg2", status="sent", message="OK", recipients_count=1),
                ],
                completed_at=datetime.now(timezone.utc)
            )
            mock_run_async.return_value = mock_result

            # Execute the task
            result = send_bulk_email_task.run( job_data)

            # Verify the result
            assert result["status"] == "completed"
            assert result["sent_count"] == 2
            assert result["failed_count"] == 0
            assert result["job_id"] == "bulk_test_123"

            # Verify update_state was called (progress tracking)
            assert mock_self.update_state.called
            # Should be called at least once for initial state
            assert mock_self.update_state.call_count >= 1


def test_send_bulk_email_task_with_progress():
    """Test bulk email task with progress updates."""
    mock_self = Mock()
    mock_self.update_state = Mock()

    # Create a job with more messages to trigger progress updates
    messages = []
    for i in range(12):  # 12 messages to trigger progress at 10
        messages.append({
            "to": [f"user{i}@example.com"],
            "subject": f"Test{i}",
            "text_body": f"Body{i}"
        })

    job_data = {
        "id": "progress_test",
        "name": "Progress Test",
        "messages": messages,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "queued"
    }

    with patch('dotmac.platform.communications.task_service.get_email_service') as mock_get_service:
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Mock _process_bulk_email_job to simulate progress callbacks
        async def mock_process(job, service, progress_callback):
            # Call progress callback multiple times
            if progress_callback:
                progress_callback(0, 12, 0, 0)  # Initial
                progress_callback(10, 12, 10, 0)  # At 10 messages
                progress_callback(12, 12, 12, 0)  # Final

            return BulkEmailResult(
                job_id="progress_test",
                status="completed",
                total_emails=12,
                sent_count=12,
                failed_count=0,
                responses=[],
                completed_at=datetime.now(timezone.utc)
            )

        with patch('dotmac.platform.communications.task_service._process_bulk_email_job', new=mock_process):
            with patch('dotmac.platform.communications.task_service._run_async') as mock_run:
                # Make _run_async actually call the coroutine
                import asyncio

                def run_async_side_effect(coro):
                    loop = asyncio.new_event_loop()
                    try:
                        return loop.run_until_complete(coro)
                    finally:
                        loop.close()

                mock_run.side_effect = run_async_side_effect

                result = send_bulk_email_task.run( job_data)

                assert result["status"] == "completed"
                assert result["sent_count"] == 12

                # Verify progress updates were made
                assert mock_self.update_state.call_count >= 3


def test_send_bulk_email_task_exception_handling():
    """Test bulk email task exception handling."""
    mock_self = Mock()

    # Invalid job data to trigger exception
    job_data = {
        "id": "error_test",
        # Missing required fields
    }

    result = send_bulk_email_task.run( job_data)

    # Should return error result
    assert result["status"] == "failed"
    assert result["job_id"] == "error_test"
    assert "error_message" in result
    assert result["total_emails"] == 0


def test_send_single_email_task_entry_point():
    """Test the single email task entry point."""
    message_data = {
        "to": ["recipient@example.com"],
        "subject": "Test Email",
        "text_body": "This is the email body",
        "html_body": "<p>HTML body</p>"
    }

    with patch('dotmac.platform.communications.task_service.get_email_service') as mock_get_service:
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        with patch('dotmac.platform.communications.task_service._send_email_sync') as mock_send_sync:
            mock_send_sync.return_value = EmailResponse(
                id="single_test_123",
                status="sent",
                message="Email delivered",
                recipients_count=1
            )

            result = send_single_email_task(message_data)

            assert result["status"] == "sent"
            assert result["id"] == "single_test_123"
            assert result["message"] == "Email delivered"
            assert result["recipients_count"] == 1

            # Verify the sync helper was called
            mock_send_sync.assert_called_once()
            call_args = mock_send_sync.call_args[0]
            assert call_args[0] == mock_service  # First arg is the service
            assert call_args[1].to == ["recipient@example.com"]  # Second is the message


def test_send_single_email_task_exception():
    """Test single email task with exception."""
    # Invalid message data
    message_data = {
        "invalid": "data"
    }

    result = send_single_email_task(message_data)

    # Should return error response
    assert result["status"] == "failed"
    assert "Task failed" in result["message"]
    assert result["recipients_count"] == 1


def test_run_async_fallback_paths():
    """Test _run_async fallback paths for coverage."""
    from dotmac.platform.communications.task_service import _run_async

    async def test_coro():
        return "test_result"

    # Test with RuntimeError on asyncio.run
    with patch('asyncio.run', side_effect=RuntimeError("Event loop running")):
        with patch('asyncio.get_event_loop') as mock_get_loop:
            # Test when loop is running (threadsafe path)
            mock_loop = Mock()
            mock_loop.is_running.return_value = True
            mock_get_loop.return_value = mock_loop

            mock_future = Mock()
            mock_future.result.return_value = "threadsafe_result"

            with patch('asyncio.run_coroutine_threadsafe', return_value=mock_future):
                result = _run_async(test_coro())
                assert result == "threadsafe_result"

            # Test when loop is not running
            mock_loop.is_running.return_value = False
            mock_loop.run_until_complete.return_value = "sync_result"

            result = _run_async(test_coro())
            assert result == "sync_result"

        # Test when get_event_loop also fails
        with patch('asyncio.get_event_loop', side_effect=RuntimeError("No loop")):
            with patch('asyncio.new_event_loop') as mock_new_loop:
                new_loop = Mock()
                new_loop.run_until_complete.return_value = "new_loop_result"
                mock_new_loop.return_value = new_loop

                result = _run_async(test_coro())
                assert result == "new_loop_result"
                new_loop.close.assert_called_once()
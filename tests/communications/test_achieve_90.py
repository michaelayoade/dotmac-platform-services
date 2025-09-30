"""
Final tests to achieve 90% coverage by testing the refactored task service.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timezone
import asyncio

from dotmac.platform.communications.email_service import EmailMessage, EmailResponse
from dotmac.platform.communications.task_service import (
    BulkEmailJob,
    BulkEmailResult,
    _run_async,
    send_bulk_email_task,
    send_single_email_task,
)


def test_run_async_with_fallback():
    """Test _run_async with all fallback paths."""
    async def simple_coro():
        return "result"

    # Test normal path
    result = _run_async(simple_coro())
    assert result == "result"

    # Test RuntimeError with running loop
    with patch('asyncio.run', side_effect=RuntimeError("Event loop already running")):
        with patch('asyncio.get_event_loop') as mock_get_loop:
            mock_loop = Mock()
            mock_loop.is_running.return_value = True
            mock_get_loop.return_value = mock_loop

            mock_future = Mock()
            mock_future.result.return_value = "threadsafe"

            with patch('asyncio.run_coroutine_threadsafe', return_value=mock_future):
                result = _run_async(simple_coro())
                assert result == "threadsafe"

    # Test RuntimeError with non-running loop
    with patch('asyncio.run', side_effect=RuntimeError("No loop")):
        with patch('asyncio.get_event_loop') as mock_get_loop:
            mock_loop = Mock()
            mock_loop.is_running.return_value = False
            mock_loop.run_until_complete.return_value = "complete"
            mock_get_loop.return_value = mock_loop

            result = _run_async(simple_coro())
            assert result == "complete"

    # Test creating new loop when get_event_loop fails
    with patch('asyncio.run', side_effect=RuntimeError("No loop")):
        with patch('asyncio.get_event_loop', side_effect=RuntimeError("No current loop")):
            with patch('asyncio.new_event_loop') as mock_new:
                new_loop = Mock()
                new_loop.run_until_complete.return_value = "new"
                mock_new.return_value = new_loop

                result = _run_async(simple_coro())
                assert result == "new"
                new_loop.close.assert_called_once()


def test_send_bulk_email_task_full():
    """Test send_bulk_email_task to cover lines 170-213."""
    mock_self = Mock()
    mock_self.update_state = Mock()

    job_data = {
        "id": "test123",
        "name": "Campaign",
        "messages": [
            {"to": ["user1@example.com"], "subject": "Test1", "text_body": "Body1"},
            {"to": ["user2@example.com"], "subject": "Test2", "text_body": "Body2"},
            {"to": ["user3@example.com"], "subject": "Test3", "text_body": "Body3"},
            {"to": ["user4@example.com"], "subject": "Test4", "text_body": "Body4"},
            {"to": ["user5@example.com"], "subject": "Test5", "text_body": "Body5"},
            {"to": ["user6@example.com"], "subject": "Test6", "text_body": "Body6"},
            {"to": ["user7@example.com"], "subject": "Test7", "text_body": "Body7"},
            {"to": ["user8@example.com"], "subject": "Test8", "text_body": "Body8"},
            {"to": ["user9@example.com"], "subject": "Test9", "text_body": "Body9"},
            {"to": ["user10@example.com"], "subject": "Test10", "text_body": "Body10"},
            {"to": ["user11@example.com"], "subject": "Test11", "text_body": "Body11"},
        ],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "queued"
    }

    with patch('dotmac.platform.communications.task_service.get_email_service') as mock_get:
        mock_service = Mock()
        mock_get.return_value = mock_service

        # Mock the async processing
        with patch('dotmac.platform.communications.task_service._process_bulk_email_job') as mock_process:
            async def process_mock(job, service, callback):
                # Simulate progress callbacks
                if callback:
                    callback(0, 11, 0, 0)  # Initial
                    callback(10, 11, 10, 0)  # At 10
                    callback(11, 11, 11, 0)  # Final

                return BulkEmailResult(
                    job_id="test123",
                    status="completed",
                    total_emails=11,
                    sent_count=11,
                    failed_count=0,
                    responses=[],
                    completed_at=datetime.now(timezone.utc)
                )

            mock_process.return_value = process_mock(None, None, None)

            with patch('dotmac.platform.communications.task_service._run_async') as mock_run:
                # Simulate the async execution
                async def run_coro(coro):
                    # If it's a coroutine, await it
                    if asyncio.iscoroutine(coro):
                        return await coro
                    return coro

                def run_side_effect(coro):
                    loop = asyncio.new_event_loop()
                    try:
                        return loop.run_until_complete(run_coro(coro))
                    finally:
                        loop.close()

                mock_run.side_effect = run_side_effect

                result = send_bulk_email_task.run( job_data)

                assert result["status"] == "completed"
                assert result["sent_count"] == 11
                assert mock_self.update_state.call_count >= 3  # Progress updates


def test_send_bulk_email_task_error():
    """Test error handling in send_bulk_email_task."""
    mock_self = Mock()

    # Invalid data to trigger exception
    job_data = {"invalid": "data"}

    result = send_bulk_email_task.run( job_data)

    assert result["status"] == "failed"
    assert "error_message" in result


def test_send_single_email_task_full():
    """Test send_single_email_task to cover lines 234-252."""
    message_data = {
        "to": ["test@example.com"],
        "subject": "Test",
        "text_body": "Body"
    }

    with patch('dotmac.platform.communications.task_service.get_email_service') as mock_get:
        mock_service = Mock()
        mock_get.return_value = mock_service

        with patch('dotmac.platform.communications.task_service._send_email_sync') as mock_sync:
            mock_sync.return_value = EmailResponse(
                id="msg123",
                status="sent",
                message="OK",
                recipients_count=1
            )

            result = send_single_email_task(message_data)

            assert result["status"] == "sent"
            assert result["id"] == "msg123"


def test_send_single_email_task_error():
    """Test error handling in send_single_email_task."""
    # Invalid message data
    result = send_single_email_task({"invalid": "data"})

    assert result["status"] == "failed"
    assert "Task failed" in result["message"]
"""
Comprehensive tests for task_service.py to achieve 90% coverage.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call, AsyncMock
from datetime import datetime, timezone
import asyncio

from dotmac.platform.communications.email_service import EmailMessage, EmailResponse
from dotmac.platform.communications.task_service import (
    BulkEmailJob,
    BulkEmailResult,
    TaskService,
    send_bulk_email_task,
    send_single_email_task,
    _send_email_sync,
    get_task_service,
    queue_email,
    queue_bulk_emails,
)


class TestSendEmailSync:
    """Test the _send_email_sync helper function."""

    @patch('asyncio.new_event_loop')
    @patch('asyncio.set_event_loop')
    def test_send_email_sync_success(self, mock_set_loop, mock_new_loop):
        """Test successful synchronous email sending."""
        # Setup
        mock_loop = Mock()
        mock_new_loop.return_value = mock_loop

        email_service = Mock()
        message = EmailMessage(to=["test@example.com"], subject="Test")

        expected_response = EmailResponse(
            id="test123",
            status="sent",
            message="OK",
            recipients_count=1
        )

        mock_loop.run_until_complete.return_value = expected_response

        # Execute
        result = _send_email_sync(email_service, message)

        # Verify
        assert result == expected_response
        mock_new_loop.assert_called_once()
        mock_set_loop.assert_called_once_with(mock_loop)
        mock_loop.close.assert_called_once()

    @patch('asyncio.new_event_loop')
    def test_send_email_sync_closes_loop_on_error(self, mock_new_loop):
        """Test that loop is closed even on error."""
        mock_loop = Mock()
        mock_new_loop.return_value = mock_loop
        mock_loop.run_until_complete.side_effect = Exception("Test error")

        email_service = Mock()
        message = EmailMessage(to=["test@example.com"], subject="Test")

        with pytest.raises(Exception):
            _send_email_sync(email_service, message)

        mock_loop.close.assert_called_once()


class TestSendSingleEmailTask:
    """Test the send_single_email_task Celery task."""

    @patch('dotmac.platform.communications.task_service._send_email_sync')
    @patch('dotmac.platform.communications.task_service.get_email_service')
    def test_send_single_email_task_success(self, mock_get_service, mock_send_sync):
        """Test successful single email task."""
        # Setup
        message_data = {
            "to": ["test@example.com"],
            "subject": "Test Subject",
            "text_body": "Test Body"
        }

        mock_service = Mock()
        mock_get_service.return_value = mock_service

        expected_response = EmailResponse(
            id="msg123",
            status="sent",
            message="Email sent",
            recipients_count=1
        )
        mock_send_sync.return_value = expected_response

        # Execute
        result = send_single_email_task(message_data)

        # Verify
        assert result["id"] == "msg123"
        assert result["status"] == "sent"
        mock_get_service.assert_called_once()
        mock_send_sync.assert_called_once()

    @patch('dotmac.platform.communications.task_service._send_email_sync')
    @patch('dotmac.platform.communications.task_service.get_email_service')
    def test_send_single_email_task_failure(self, mock_get_service, mock_send_sync):
        """Test single email task with failure."""
        message_data = {
            "to": ["test@example.com"],
            "subject": "Test",
            "text_body": "Body"
        }

        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_send_sync.side_effect = Exception("SMTP Error")

        result = send_single_email_task(message_data)

        assert result["status"] == "failed"
        assert "SMTP Error" in result["message"]

    def test_send_single_email_task_invalid_data(self):
        """Test single email task with invalid data."""
        message_data = {
            "invalid": "data"
        }

        result = send_single_email_task(message_data)

        assert result["status"] == "failed"
        assert "Task failed" in result["message"]


class TestSendBulkEmailTask:
    """Test the send_bulk_email_task Celery task."""

    @patch('dotmac.platform.communications.task_service._send_email_sync')
    @patch('dotmac.platform.communications.task_service.get_email_service')
    def test_bulk_email_task_all_success(self, mock_get_service, mock_send_sync):
        """Test bulk email task with all emails succeeding."""
        # Create mock for self parameter
        mock_self = Mock()
        mock_self.update_state = Mock()

        job_data = {
            "id": "bulk123",
            "name": "Test Campaign",
            "messages": [
                {"to": ["user1@example.com"], "subject": "Test1", "text_body": "Body1"},
                {"to": ["user2@example.com"], "subject": "Test2", "text_body": "Body2"}
            ],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "queued"
        }

        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Mock successful responses
        mock_send_sync.side_effect = [
            EmailResponse(id="msg1", status="sent", message="OK", recipients_count=1),
            EmailResponse(id="msg2", status="sent", message="OK", recipients_count=1)
        ]

        result = send_bulk_email_task.run( job_data)

        assert result["status"] == "completed"
        assert result["sent_count"] == 2
        assert result["failed_count"] == 0
        assert mock_self.update_state.called

    @patch('dotmac.platform.communications.task_service._send_email_sync')
    @patch('dotmac.platform.communications.task_service.get_email_service')
    def test_bulk_email_task_partial_failure(self, mock_get_service, mock_send_sync):
        """Test bulk email task with some failures."""
        mock_self = Mock()
        mock_self.update_state = Mock()

        job_data = {
            "id": "bulk123",
            "name": "Campaign",
            "messages": [
                {"to": ["user1@example.com"], "subject": "Test1", "text_body": "Body1"},
                {"to": ["user2@example.com"], "subject": "Test2", "text_body": "Body2"},
                {"to": ["user3@example.com"], "subject": "Test3", "text_body": "Body3"}
            ],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "queued"
        }

        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Mix success and failure
        mock_send_sync.side_effect = [
            EmailResponse(id="msg1", status="sent", message="OK", recipients_count=1),
            Exception("SMTP error"),
            EmailResponse(id="msg3", status="sent", message="OK", recipients_count=1)
        ]

        result = send_bulk_email_task.run( job_data)

        assert result["status"] == "completed"
        assert result["sent_count"] == 2
        assert result["failed_count"] == 1

    @patch('dotmac.platform.communications.task_service._send_email_sync')
    @patch('dotmac.platform.communications.task_service.get_email_service')
    def test_bulk_email_task_progress_updates(self, mock_get_service, mock_send_sync):
        """Test that progress updates are sent for large batches."""
        mock_self = Mock()
        mock_self.update_state = Mock()

        # Create 15 messages to trigger progress updates
        messages = [
            {"to": [f"user{i}@example.com"], "subject": f"Test{i}", "text_body": f"Body{i}"}
            for i in range(15)
        ]

        job_data = {
            "id": "bulk123",
            "name": "Large Campaign",
            "messages": messages,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "queued"
        }

        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # All succeed
        mock_send_sync.return_value = EmailResponse(
            id="msg", status="sent", message="OK", recipients_count=1
        )

        result = send_bulk_email_task.run( job_data)

        # Should have multiple progress updates (initial + every 10 + final)
        assert mock_self.update_state.call_count >= 3
        assert result["sent_count"] == 15

    def test_bulk_email_task_invalid_job_data(self):
        """Test bulk email task with invalid job data."""
        mock_self = Mock()

        job_data = {
            "invalid": "data"
        }

        result = send_bulk_email_task.run( job_data)

        assert result["status"] == "failed"
        assert "error_message" in result

    @patch('dotmac.platform.communications.task_service.get_email_service')
    def test_bulk_email_task_service_error(self, mock_get_service):
        """Test bulk email task when service fails to initialize."""
        mock_self = Mock()
        mock_get_service.side_effect = Exception("Service unavailable")

        job_data = {
            "id": "bulk123",
            "name": "Campaign",
            "messages": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "queued"
        }

        result = send_bulk_email_task.run( job_data)

        assert result["status"] == "failed"
        assert "Service unavailable" in result["error_message"]


class TestTaskService:
    """Test TaskService class methods."""

    def test_send_email_async(self):
        """Test queuing single email."""
        service = TaskService()
        message = EmailMessage(to=["test@example.com"], subject="Test")

        with patch('dotmac.platform.communications.task_service.send_single_email_task.delay') as mock_delay:
            mock_task = Mock()
            mock_task.id = "task123"
            mock_delay.return_value = mock_task

            task_id = service.send_email_async(message)

            assert task_id == "task123"
            mock_delay.assert_called_once_with(message.model_dump())

    def test_send_bulk_emails_async(self):
        """Test queuing bulk emails."""
        service = TaskService()
        job = BulkEmailJob(
            name="Campaign",
            messages=[
                EmailMessage(to=["user1@example.com"], subject="Test1"),
                EmailMessage(to=["user2@example.com"], subject="Test2")
            ]
        )

        with patch('dotmac.platform.communications.task_service.send_bulk_email_task.delay') as mock_delay:
            mock_task = Mock()
            mock_task.id = "bulk123"
            mock_delay.return_value = mock_task

            task_id = service.send_bulk_emails_async(job)

            assert task_id == "bulk123"
            mock_delay.assert_called_once()

    def test_get_task_status(self):
        """Test getting task status."""
        service = TaskService()

        with patch.object(service.celery, 'AsyncResult') as mock_result_class:
            mock_result = Mock()
            mock_result.status = "SUCCESS"
            mock_result.result = {"sent_count": 10}
            mock_result.info = {"progress": 100}
            mock_result_class.return_value = mock_result

            status = service.get_task_status("task123")

            assert status["status"] == "SUCCESS"
            assert status["result"]["sent_count"] == 10
            assert status["info"]["progress"] == 100

    def test_cancel_task_success(self):
        """Test successful task cancellation."""
        service = TaskService()

        with patch.object(service.celery.control, 'revoke') as mock_revoke:
            result = service.cancel_task("task123")

            assert result is True
            mock_revoke.assert_called_once_with("task123", terminate=True)

    def test_cancel_task_failure(self):
        """Test failed task cancellation."""
        service = TaskService()

        with patch.object(service.celery.control, 'revoke') as mock_revoke:
            mock_revoke.side_effect = Exception("Revoke failed")

            result = service.cancel_task("task123")

            assert result is False


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_get_task_service_singleton(self):
        """Test get_task_service returns singleton."""
        service1 = get_task_service()
        service2 = get_task_service()
        assert service1 is service2

    @patch('dotmac.platform.communications.task_service.get_task_service')
    def test_queue_email(self, mock_get_service):
        """Test queue_email convenience function."""
        mock_service = Mock()
        mock_service.send_email_async.return_value = "task123"
        mock_get_service.return_value = mock_service

        task_id = queue_email(
            to=["test@example.com"],
            subject="Test",
            text_body="Body"
        )

        assert task_id == "task123"
        mock_service.send_email_async.assert_called_once()

    @patch('dotmac.platform.communications.task_service.get_task_service')
    def test_queue_bulk_emails(self, mock_get_service):
        """Test queue_bulk_emails convenience function."""
        mock_service = Mock()
        mock_service.send_bulk_emails_async.return_value = "bulk123"
        mock_get_service.return_value = mock_service

        messages = [
            EmailMessage(to=["user1@example.com"], subject="Test1"),
            EmailMessage(to=["user2@example.com"], subject="Test2")
        ]

        task_id = queue_bulk_emails("Campaign", messages)

        assert task_id == "bulk123"
        mock_service.send_bulk_emails_async.assert_called_once()


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @patch('dotmac.platform.communications.task_service._send_email_sync')
    @patch('dotmac.platform.communications.task_service.get_email_service')
    def test_bulk_email_empty_messages(self, mock_get_service, mock_send_sync):
        """Test bulk email with empty message list."""
        mock_self = Mock()
        mock_self.update_state = Mock()

        job_data = {
            "id": "bulk123",
            "name": "Empty Campaign",
            "messages": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "queued"
        }

        mock_service = Mock()
        mock_get_service.return_value = mock_service

        result = send_bulk_email_task.run( job_data)

        assert result["status"] == "completed"
        assert result["sent_count"] == 0
        assert result["failed_count"] == 0

    @patch('dotmac.platform.communications.task_service._send_email_sync')
    @patch('dotmac.platform.communications.task_service.get_email_service')
    def test_bulk_email_all_failures(self, mock_get_service, mock_send_sync):
        """Test bulk email where all emails fail."""
        mock_self = Mock()
        mock_self.update_state = Mock()

        job_data = {
            "id": "bulk123",
            "name": "Failing Campaign",
            "messages": [
                {"to": ["user1@example.com"], "subject": "Test1", "text_body": "Body1"},
                {"to": ["user2@example.com"], "subject": "Test2", "text_body": "Body2"}
            ],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "queued"
        }

        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # All fail
        mock_send_sync.side_effect = [
            Exception("Error 1"),
            Exception("Error 2")
        ]

        result = send_bulk_email_task.run( job_data)

        assert result["status"] == "completed"  # Still completes even if all fail
        assert result["sent_count"] == 0
        assert result["failed_count"] == 2
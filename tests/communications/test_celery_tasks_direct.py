"""
Direct tests for Celery tasks to achieve 90% coverage.
Tests the actual task functions with proper signatures.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from celery import Task

from dotmac.platform.communications.email_service import EmailMessage, EmailResponse

# Patch Celery tasks before importing
with patch('dotmac.platform.communications.task_service.celery_app'):
    from dotmac.platform.communications.task_service import (
        send_single_email_task,
        send_bulk_email_task,
        _send_email_sync
    )


class TestSendSingleEmailTaskDirect:
    """Test send_single_email_task directly."""

    @patch('dotmac.platform.communications.task_service.get_email_service')
    def test_single_email_success(self, mock_get_service):
        """Test successful single email sending."""
        # Mock email service
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Mock the sync send
        with patch('dotmac.platform.communications.task_service._send_email_sync') as mock_sync:
            mock_sync.return_value = EmailResponse(
                id="test123",
                status="sent",
                message="Email sent",
                recipients_count=1
            )

            # Call task directly without self parameter
            email_data = {
                "to": ["test@example.com"],
                "subject": "Test Subject",
                "text_body": "Test Body"
            }

            result = send_single_email_task(email_data)

            assert result["status"] == "sent"
            assert result["id"] == "test123"
            assert "task_id" not in result  # No self.request.id available

    @patch('dotmac.platform.communications.task_service.get_email_service')
    def test_single_email_failure(self, mock_get_service):
        """Test single email failure handling."""
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        with patch('dotmac.platform.communications.task_service._send_email_sync') as mock_sync:
            mock_sync.side_effect = Exception("SMTP connection failed")

            email_data = {
                "to": ["test@example.com"],
                "subject": "Test",
                "text_body": "Body"
            }

            result = send_single_email_task(email_data)

            assert result["status"] == "failed"
            assert "SMTP connection failed" in result["message"]

    def test_single_email_invalid_data(self):
        """Test with invalid email data."""
        # Missing required fields
        result = send_single_email_task({"invalid": "data"})

        assert result["status"] == "failed"
        assert "message" in result


class TestSendBulkEmailTaskDirect:
    """Test send_bulk_email_task directly."""

    @patch('dotmac.platform.communications.task_service.get_email_service')
    def test_bulk_email_success(self, mock_get_service):
        """Test successful bulk email sending."""
        # Create a mock self with update_state
        mock_self = Mock()
        mock_self.update_state = Mock()

        # Mock email service
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Mock sync send
        with patch('dotmac.platform.communications.task_service._send_email_sync') as mock_sync:
            mock_sync.side_effect = [
                EmailResponse(id="msg1", status="sent", message="OK", recipients_count=1),
                EmailResponse(id="msg2", status="sent", message="OK", recipients_count=1),
                EmailResponse(id="msg3", status="sent", message="OK", recipients_count=1)
            ]

            job_data = {
                "id": "bulk123",
                "name": "Test Campaign",
                "messages": [
                    {"to": ["user1@example.com"], "subject": "Test1", "text_body": "Body1"},
                    {"to": ["user2@example.com"], "subject": "Test2", "text_body": "Body2"},
                    {"to": ["user3@example.com"], "subject": "Test3", "text_body": "Body3"}
                ],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "queued"
            }

            # Call with self parameter as first arg
            result = send_bulk_email_task.run( job_data)

            assert result["status"] == "completed"
            assert result["sent_count"] == 3
            assert result["failed_count"] == 0
            assert mock_self.update_state.called

    @patch('dotmac.platform.communications.task_service.get_email_service')
    def test_bulk_email_with_failures(self, mock_get_service):
        """Test bulk email with some failures."""
        mock_self = Mock()
        mock_self.update_state = Mock()

        mock_service = Mock()
        mock_get_service.return_value = mock_service

        with patch('dotmac.platform.communications.task_service._send_email_sync') as mock_sync:
            # Mix successes and failures
            mock_sync.side_effect = [
                EmailResponse(id="msg1", status="sent", message="OK", recipients_count=1),
                Exception("SMTP Error"),
                EmailResponse(id="msg3", status="sent", message="OK", recipients_count=1),
                EmailResponse(id="msg4", status="failed", message="Rejected", recipients_count=1)
            ]

            job_data = {
                "id": "bulk123",
                "name": "Campaign",
                "messages": [
                    {"to": ["user1@example.com"], "subject": "Test1", "text_body": "Body1"},
                    {"to": ["user2@example.com"], "subject": "Test2", "text_body": "Body2"},
                    {"to": ["user3@example.com"], "subject": "Test3", "text_body": "Body3"},
                    {"to": ["user4@example.com"], "subject": "Test4", "text_body": "Body4"}
                ],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "queued"
            }

            result = send_bulk_email_task.run( job_data)

            assert result["status"] == "completed"
            assert result["sent_count"] == 2
            assert result["failed_count"] == 2

    @patch('dotmac.platform.communications.task_service.get_email_service')
    def test_bulk_email_progress_updates(self, mock_get_service):
        """Test progress updates for large batches."""
        mock_self = Mock()
        mock_self.update_state = Mock()

        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Create 15 messages to trigger multiple progress updates
        messages = [
            {"to": [f"user{i}@example.com"], "subject": f"Test{i}", "text_body": f"Body{i}"}
            for i in range(15)
        ]

        with patch('dotmac.platform.communications.task_service._send_email_sync') as mock_sync:
            mock_sync.return_value = EmailResponse(
                id="msg", status="sent", message="OK", recipients_count=1
            )

            job_data = {
                "id": "bulk123",
                "name": "Large Campaign",
                "messages": messages,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "queued"
            }

            result = send_bulk_email_task.run( job_data)

            # Should have multiple progress updates
            assert mock_self.update_state.call_count >= 3
            assert result["sent_count"] == 15

            # Check progress update calls
            progress_calls = [call for call in mock_self.update_state.call_args_list]
            # First call should be 0% progress
            first_call = progress_calls[0]
            assert first_call[1]['meta']['progress'] == 0
            # Last progress update before final
            assert any(call[1]['meta']['progress'] > 0 for call in progress_calls[1:])

    @patch('dotmac.platform.communications.task_service.get_email_service')
    def test_bulk_email_empty_messages(self, mock_get_service):
        """Test bulk email with empty message list."""
        mock_self = Mock()
        mock_self.update_state = Mock()

        mock_service = Mock()
        mock_get_service.return_value = mock_service

        job_data = {
            "id": "bulk123",
            "name": "Empty Campaign",
            "messages": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "queued"
        }

        result = send_bulk_email_task.run( job_data)

        assert result["status"] == "completed"
        assert result["sent_count"] == 0
        assert result["failed_count"] == 0

    @patch('dotmac.platform.communications.task_service.get_email_service')
    def test_bulk_email_service_failure(self, mock_get_service):
        """Test bulk email when service fails to initialize."""
        mock_self = Mock()
        mock_get_service.side_effect = Exception("Service unavailable")

        job_data = {
            "id": "bulk123",
            "name": "Campaign",
            "messages": [
                {"to": ["user1@example.com"], "subject": "Test", "text_body": "Body"}
            ],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "queued"
        }

        result = send_bulk_email_task.run( job_data)

        assert result["status"] == "failed"
        assert "Service unavailable" in result["error_message"]

    def test_bulk_email_invalid_job_data(self):
        """Test bulk email with invalid job data."""
        mock_self = Mock()

        # Missing required fields
        job_data = {"invalid": "data"}

        result = send_bulk_email_task.run( job_data)

        assert result["status"] == "failed"
        assert "error_message" in result


class TestSendEmailSyncDirect:
    """Test _send_email_sync helper function."""

    @patch('asyncio.new_event_loop')
    @patch('asyncio.set_event_loop')
    def test_sync_email_success(self, mock_set_loop, mock_new_loop):
        """Test successful sync email sending."""
        # Mock event loop
        mock_loop = Mock()
        mock_new_loop.return_value = mock_loop

        # Mock email service with async send_email
        email_service = Mock()
        async_response = EmailResponse(
            id="test123",
            status="sent",
            message="OK",
            recipients_count=1
        )
        mock_loop.run_until_complete.return_value = async_response

        message = EmailMessage(
            to=["test@example.com"],
            subject="Test",
            text_body="Body"
        )

        result = _send_email_sync(email_service, message)

        assert result.id == "test123"
        assert result.status == "sent"
        mock_loop.close.assert_called_once()

    @patch('asyncio.new_event_loop')
    @patch('asyncio.set_event_loop')
    def test_sync_email_error_cleanup(self, mock_set_loop, mock_new_loop):
        """Test that event loop is closed on error."""
        mock_loop = Mock()
        mock_new_loop.return_value = mock_loop
        mock_loop.run_until_complete.side_effect = Exception("Async error")

        email_service = Mock()
        message = EmailMessage(to=["test@example.com"], subject="Test")

        with pytest.raises(Exception, match="Async error"):
            _send_email_sync(email_service, message)

        # Ensure loop is closed even on error
        mock_loop.close.assert_called_once()


class TestBulkEmailTaskEdgeCases:
    """Test edge cases for bulk email task."""

    @patch('dotmac.platform.communications.task_service.get_email_service')
    def test_bulk_email_all_failures(self, mock_get_service):
        """Test when all emails fail."""
        mock_self = Mock()
        mock_self.update_state = Mock()

        mock_service = Mock()
        mock_get_service.return_value = mock_service

        with patch('dotmac.platform.communications.task_service._send_email_sync') as mock_sync:
            # All fail
            mock_sync.side_effect = [
                Exception("Error 1"),
                Exception("Error 2"),
                Exception("Error 3")
            ]

            job_data = {
                "id": "bulk123",
                "name": "Failing Campaign",
                "messages": [
                    {"to": ["user1@example.com"], "subject": "Test1", "text_body": "Body1"},
                    {"to": ["user2@example.com"], "subject": "Test2", "text_body": "Body2"},
                    {"to": ["user3@example.com"], "subject": "Test3", "text_body": "Body3"}
                ],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "queued"
            }

            result = send_bulk_email_task.run( job_data)

            assert result["status"] == "completed"  # Task still completes
            assert result["sent_count"] == 0
            assert result["failed_count"] == 3

    @patch('dotmac.platform.communications.task_service.get_email_service')
    def test_bulk_email_invalid_message_data(self, mock_get_service):
        """Test bulk email with invalid message in batch."""
        mock_self = Mock()
        mock_self.update_state = Mock()

        mock_service = Mock()
        mock_get_service.return_value = mock_service

        with patch('dotmac.platform.communications.task_service._send_email_sync') as mock_sync:
            # First succeeds, second has validation error, third succeeds
            def side_effect(service, msg):
                if msg.to[0] == "invalid":
                    raise ValueError("Invalid email format")
                return EmailResponse(id="msg", status="sent", message="OK", recipients_count=1)

            mock_sync.side_effect = side_effect

            job_data = {
                "id": "bulk123",
                "name": "Mixed Campaign",
                "messages": [
                    {"to": ["valid1@example.com"], "subject": "Test1", "text_body": "Body1"},
                    {"to": ["invalid"], "subject": "Test2", "text_body": "Body2"},
                    {"to": ["valid2@example.com"], "subject": "Test3", "text_body": "Body3"}
                ],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "queued"
            }

            result = send_bulk_email_task.run( job_data)

            assert result["status"] == "completed"
            assert result["sent_count"] == 2
            assert result["failed_count"] == 1
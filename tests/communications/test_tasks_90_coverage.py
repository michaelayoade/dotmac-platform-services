"""
Final push to 90% coverage - test the task service implementation directly.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timezone
import asyncio

from dotmac.platform.communications.email_service import EmailMessage, EmailResponse


class TestTaskImplementation:
    """Test the actual task implementation code."""

    @patch('dotmac.platform.communications.task_service.celery_app.task')
    def test_import_and_execute_tasks(self, mock_task_decorator):
        """Test that we can import and execute the task code."""
        # Mock the decorator to return the original function
        def decorator(bind=False, name=None):
            def wrapper(func):
                # Add Celery task attributes to the function
                func.delay = Mock()
                func.apply_async = Mock()
                func.run = func  # Allow direct calling
                return func
            return wrapper
        mock_task_decorator.side_effect = decorator

        # Now import the module which will apply our mocked decorator
        import importlib
        import sys
        if 'dotmac.platform.communications.task_service' in sys.modules:
            del sys.modules['dotmac.platform.communications.task_service']

        from dotmac.platform.communications import task_service
        importlib.reload(task_service)

        # Now test send_single_email_task
        with patch.object(task_service, 'get_email_service') as mock_get_service:
            with patch.object(task_service, '_send_email_sync') as mock_sync:
                mock_sync.return_value = EmailResponse(
                    id="msg123",
                    status="sent",
                    message="OK",
                    recipients_count=1
                )

                email_data = {
                    "to": ["test@example.com"],
                    "subject": "Test",
                    "text_body": "Body"
                }

                # Create mock self if needed
                mock_self = Mock()
                mock_self.request.id = "task123"

                # Try calling without self first (for non-bound task)
                try:
                    result = task_service.send_single_email_task(email_data)
                    assert result["status"] == "sent"
                except TypeError:
                    # If it needs self, call with it
                    result = task_service.send_single_email_task( email_data)
                    assert result["status"] == "sent"

        # Test send_bulk_email_task
        with patch.object(task_service, 'get_email_service') as mock_get_service:
            with patch.object(task_service, '_send_email_sync') as mock_sync:
                mock_sync.return_value = EmailResponse(
                    id="msg1",
                    status="sent",
                    message="OK",
                    recipients_count=1
                )

                job_data = {
                    "id": "bulk123",
                    "name": "Campaign",
                    "messages": [
                        {"to": ["user1@example.com"], "subject": "Test1", "text_body": "Body1"},
                        {"to": ["user2@example.com"], "subject": "Test2", "text_body": "Body2"}
                    ],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "status": "queued"
                }

                mock_self = Mock()
                mock_self.update_state = Mock()

                result = task_service.send_bulk_email_task.run( job_data)
                assert result["status"] == "completed"
                assert result["sent_count"] == 2


class TestCoverUncoveredLines:
    """Specifically target uncovered lines 81-190."""

    def test_bulk_email_full_flow(self):
        """Test the full bulk email flow to cover lines 81-190."""
        from dotmac.platform.communications.task_service import celery_app

        # Mock Celery task context
        mock_self = Mock()
        mock_self.update_state = Mock()
        mock_self.request.id = "task123"

        job_data = {
            "id": "bulk_test_123",
            "name": "Test Campaign",
            "messages": [
                {"to": ["user1@example.com"], "subject": "Subject 1", "text_body": "Body 1"},
                {"to": ["user2@example.com"], "subject": "Subject 2", "text_body": "Body 2"},
                {"to": ["user3@example.com"], "subject": "Subject 3", "text_body": "Body 3"},
                {"to": ["user4@example.com"], "subject": "Subject 4", "text_body": "Body 4"},
                {"to": ["user5@example.com"], "subject": "Subject 5", "text_body": "Body 5"},
                {"to": ["user6@example.com"], "subject": "Subject 6", "text_body": "Body 6"},
                {"to": ["user7@example.com"], "subject": "Subject 7", "text_body": "Body 7"},
                {"to": ["user8@example.com"], "subject": "Subject 8", "text_body": "Body 8"},
                {"to": ["user9@example.com"], "subject": "Subject 9", "text_body": "Body 9"},
                {"to": ["user10@example.com"], "subject": "Subject 10", "text_body": "Body 10"},
                {"to": ["user11@example.com"], "subject": "Subject 11", "text_body": "Body 11"},
            ],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "queued"
        }

        # Patch dependencies at module level
        with patch('dotmac.platform.communications.task_service.get_email_service') as mock_get_service:
            with patch('dotmac.platform.communications.task_service._send_email_sync') as mock_sync:
                # Mix successes and failures to cover all branches
                responses = []
                for i in range(11):
                    if i == 3:  # Make 4th email fail
                        responses.append(Exception("SMTP error"))
                    elif i == 7:  # Make 8th email return failed status
                        responses.append(EmailResponse(
                            id=f"msg{i}",
                            status="failed",
                            message="Rejected",
                            recipients_count=1
                        ))
                    else:
                        responses.append(EmailResponse(
                            id=f"msg{i}",
                            status="sent",
                            message="OK",
                            recipients_count=1
                        ))

                mock_sync.side_effect = responses
                mock_service = Mock()
                mock_get_service.return_value = mock_service

                # Import and call the actual task
                from dotmac.platform.communications.task_service import send_bulk_email_task

                # Call task with mock self
                with patch.object(celery_app.Task, '__call__', return_value=None):
                    result = send_bulk_email_task.run( job_data)

                # Verify results
                assert result["status"] == "completed"
                assert result["job_id"] == "bulk_test_123"
                assert result["sent_count"] == 9  # 11 - 1 exception - 1 failed status
                assert result["failed_count"] == 2

                # Verify progress updates were called (initial + after 10th + final)
                assert mock_self.update_state.call_count >= 2

    def test_bulk_email_exception_handling(self):
        """Test exception handling in bulk email task."""
        mock_self = Mock()

        # Invalid job data to trigger exception at line 182
        job_data = {
            "invalid": "data"
        }

        from dotmac.platform.communications.task_service import send_bulk_email_task
        result = send_bulk_email_task.run( job_data)

        assert result["status"] == "failed"
        assert "error_message" in result
        assert result["job_id"] == "unknown"

    def test_bulk_email_service_initialization_failure(self):
        """Test when email service fails to initialize."""
        mock_self = Mock()
        mock_self.update_state = Mock()

        job_data = {
            "id": "bulk123",
            "name": "Test",
            "messages": [{"to": ["test@example.com"], "subject": "Test", "text_body": "Body"}],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "queued"
        }

        with patch('dotmac.platform.communications.task_service.get_email_service') as mock_get:
            mock_get.side_effect = Exception("Service initialization failed")

            from dotmac.platform.communications.task_service import send_bulk_email_task
            result = send_bulk_email_task.run( job_data)

            assert result["status"] == "failed"
            assert "Service initialization failed" in result["error_message"]

    def test_send_email_sync_function(self):
        """Test the _send_email_sync helper directly."""
        from dotmac.platform.communications.task_service import _send_email_sync

        # Create a mock email service with async send_email method
        email_service = Mock()
        async def mock_send_email(message):
            return EmailResponse(
                id="test123",
                status="sent",
                message="Email sent",
                recipients_count=1
            )
        email_service.send_email = mock_send_email

        message = EmailMessage(
            to=["test@example.com"],
            subject="Test Subject",
            text_body="Test Body"
        )

        # Call the sync wrapper
        with patch('asyncio.new_event_loop') as mock_new_loop:
            with patch('asyncio.set_event_loop') as mock_set_loop:
                mock_loop = Mock()
                mock_new_loop.return_value = mock_loop

                # Make run_until_complete return our response
                async_result = EmailResponse(
                    id="test123",
                    status="sent",
                    message="OK",
                    recipients_count=1
                )
                mock_loop.run_until_complete.return_value = async_result

                result = _send_email_sync(email_service, message)

                assert result.id == "test123"
                assert result.status == "sent"
                mock_loop.close.assert_called_once()

    def test_send_email_sync_with_exception(self):
        """Test _send_email_sync exception handling."""
        from dotmac.platform.communications.task_service import _send_email_sync

        email_service = Mock()
        message = EmailMessage(to=["test@example.com"], subject="Test")

        with patch('asyncio.new_event_loop') as mock_new_loop:
            with patch('asyncio.set_event_loop') as mock_set_loop:
                mock_loop = Mock()
                mock_new_loop.return_value = mock_loop
                mock_loop.run_until_complete.side_effect = Exception("Async error")

                with pytest.raises(Exception, match="Async error"):
                    _send_email_sync(email_service, message)

                # Verify loop was closed even on error
                mock_loop.close.assert_called_once()


class TestSingleEmailTask:
    """Test single email task to increase coverage."""

    def test_send_single_email_success(self):
        """Test successful single email send."""
        from dotmac.platform.communications.task_service import send_single_email_task

        email_data = {
            "to": ["recipient@example.com"],
            "subject": "Important Message",
            "text_body": "This is the message body",
            "html_body": "<p>HTML body</p>"
        }

        with patch('dotmac.platform.communications.task_service.get_email_service') as mock_get:
            with patch('dotmac.platform.communications.task_service._send_email_sync') as mock_sync:
                mock_sync.return_value = EmailResponse(
                    id="single123",
                    status="sent",
                    message="Delivered",
                    recipients_count=1
                )

                result = send_single_email_task(email_data)

                assert result["status"] == "sent"
                assert result["id"] == "single123"
                assert result["message"] == "Delivered"
                mock_sync.assert_called_once()

    def test_send_single_email_with_exception(self):
        """Test single email with exception."""
        from dotmac.platform.communications.task_service import send_single_email_task

        email_data = {
            "to": ["bad@example.com"],
            "subject": "Test",
            "text_body": "Body"
        }

        with patch('dotmac.platform.communications.task_service.get_email_service') as mock_get:
            with patch('dotmac.platform.communications.task_service._send_email_sync') as mock_sync:
                mock_sync.side_effect = Exception("Connection refused")

                result = send_single_email_task(email_data)

                assert result["status"] == "failed"
                assert "Connection refused" in result["message"]

    def test_send_single_email_validation_error(self):
        """Test single email with validation error."""
        from dotmac.platform.communications.task_service import send_single_email_task

        # Invalid email data
        email_data = {"invalid": "structure"}

        result = send_single_email_task(email_data)

        assert result["status"] == "failed"
        assert "Task failed" in result["message"]
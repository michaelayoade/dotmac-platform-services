"""
Mock Celery internals to achieve 90% coverage on task_service.py lines 81-190.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from datetime import datetime, timezone

from dotmac.platform.communications.email_service import EmailMessage, EmailResponse
from dotmac.platform.communications.task_service import BulkEmailJob, BulkEmailResult


class TestCeleryTasksWithMocking:
    """Mock Celery tasks at import time to test the actual implementation."""

    def test_bulk_email_task_full_implementation(self):
        """Test bulk email task by mocking Celery and calling the implementation."""
        # Create mock self with all required attributes
        mock_self = Mock()
        mock_self.update_state = Mock()
        mock_self.request = Mock()
        mock_self.request.id = "celery_task_123"

        # Create job data
        job_data = {
            "id": "bulk_job_123",
            "name": "Test Email Campaign",
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
                {"to": ["user12@example.com"], "subject": "Subject 12", "text_body": "Body 12"},
            ],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "queued"
        }

        # Mock get_email_service at module level
        with patch('dotmac.platform.communications.task_service.get_email_service') as mock_get_service:
            mock_email_service = Mock()
            mock_get_service.return_value = mock_email_service

            # Mock _send_email_sync to return mixed results
            with patch('dotmac.platform.communications.task_service._send_email_sync') as mock_send_sync:
                # Create varied responses to test all branches
                def send_side_effect(service, message):
                    email = message.to[0]
                    if email == "user3@example.com":
                        # Simulate exception for user3
                        raise Exception("SMTP connection failed")
                    elif email == "user7@example.com":
                        # Return failed status for user7
                        return EmailResponse(
                            id=f"msg_{email}",
                            status="failed",
                            message="Recipient rejected",
                            recipients_count=1
                        )
                    else:
                        # Return success for others
                        return EmailResponse(
                            id=f"msg_{email}",
                            status="sent",
                            message="Email sent successfully",
                            recipients_count=1
                        )

                mock_send_sync.side_effect = send_side_effect

                # Import and execute the task
                from dotmac.platform.communications.task_service import send_bulk_email_task

                # Execute task with mock self
                result = send_bulk_email_task.run( job_data)

                # Verify results
                assert result["status"] == "completed"
                assert result["job_id"] == "bulk_job_123"
                assert result["sent_count"] == 10  # 12 total - 1 exception - 1 failed = 10
                assert result["failed_count"] == 2   # 1 exception + 1 failed status
                assert result["total_emails"] == 12
                assert len(result["responses"]) == 12

                # Verify update_state was called for progress updates
                # Initial state + progress updates at 10th and 12th message
                assert mock_self.update_state.call_count >= 2

                # Check the progress update calls
                update_calls = mock_self.update_state.call_args_list

                # First call should be initial state with 0 progress
                first_call = update_calls[0]
                assert first_call[1]['state'] == 'PROGRESS'
                assert first_call[1]['meta']['progress'] == 0
                assert first_call[1]['meta']['job_id'] == 'bulk_job_123'

                # Last call should show completion progress
                last_call = update_calls[-1]
                assert last_call[1]['meta']['progress'] == 100
                assert last_call[1]['meta']['sent'] == 10
                assert last_call[1]['meta']['failed'] == 2

    def test_bulk_email_task_parsing_error(self):
        """Test bulk email task with invalid job data to cover error handling."""
        mock_self = Mock()

        # Invalid job data (missing required fields)
        job_data = {
            "id": "invalid_job",
            # Missing "messages" field
        }

        from dotmac.platform.communications.task_service import send_bulk_email_task

        result = send_bulk_email_task.run( job_data)

        # Should return failure result
        assert result["status"] == "failed"
        assert "error_message" in result
        assert result["job_id"] == "invalid_job"

    def test_bulk_email_task_service_initialization_error(self):
        """Test bulk email task when email service fails to initialize."""
        mock_self = Mock()
        mock_self.update_state = Mock()

        job_data = {
            "id": "service_fail_job",
            "name": "Test",
            "messages": [
                {"to": ["test@example.com"], "subject": "Test", "text_body": "Body"}
            ],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "queued"
        }

        with patch('dotmac.platform.communications.task_service.get_email_service') as mock_get_service:
            # Simulate service initialization failure
            mock_get_service.side_effect = Exception("Email service unavailable")

            from dotmac.platform.communications.task_service import send_bulk_email_task

            result = send_bulk_email_task.run( job_data)

            assert result["status"] == "failed"
            assert "Email service unavailable" in result["error_message"]
            assert result["job_id"] == "service_fail_job"

    def test_bulk_email_empty_messages(self):
        """Test bulk email with empty message list."""
        mock_self = Mock()
        mock_self.update_state = Mock()

        job_data = {
            "id": "empty_job",
            "name": "Empty Campaign",
            "messages": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "queued"
        }

        with patch('dotmac.platform.communications.task_service.get_email_service') as mock_get_service:
            mock_email_service = Mock()
            mock_get_service.return_value = mock_email_service

            from dotmac.platform.communications.task_service import send_bulk_email_task

            result = send_bulk_email_task.run( job_data)

            assert result["status"] == "completed"
            assert result["sent_count"] == 0
            assert result["failed_count"] == 0
            assert result["total_emails"] == 0

    def test_bulk_email_all_failures(self):
        """Test bulk email where all emails fail."""
        mock_self = Mock()
        mock_self.update_state = Mock()

        job_data = {
            "id": "all_fail_job",
            "name": "Failing Campaign",
            "messages": [
                {"to": ["fail1@example.com"], "subject": "Test1", "text_body": "Body1"},
                {"to": ["fail2@example.com"], "subject": "Test2", "text_body": "Body2"},
                {"to": ["fail3@example.com"], "subject": "Test3", "text_body": "Body3"},
            ],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "queued"
        }

        with patch('dotmac.platform.communications.task_service.get_email_service') as mock_get_service:
            mock_email_service = Mock()
            mock_get_service.return_value = mock_email_service

            with patch('dotmac.platform.communications.task_service._send_email_sync') as mock_send_sync:
                # All emails fail
                mock_send_sync.side_effect = [
                    Exception("Error 1"),
                    Exception("Error 2"),
                    Exception("Error 3"),
                ]

                from dotmac.platform.communications.task_service import send_bulk_email_task

                result = send_bulk_email_task.run( job_data)

                assert result["status"] == "completed"  # Task completes even if all fail
                assert result["sent_count"] == 0
                assert result["failed_count"] == 3
                assert len(result["responses"]) == 3

                # All responses should be error responses
                for response in result["responses"]:
                    assert response["status"] == "failed"
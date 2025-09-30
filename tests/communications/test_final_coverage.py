"""
Final tests to push coverage to 90%.
Focus on covering the actual Celery task internals.
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timezone
import smtplib

from dotmac.platform.communications.email_service import EmailMessage, EmailResponse, EmailService
from dotmac.platform.communications.template_service import TemplateData, TemplateService
from dotmac.platform.communications.task_service import (
    BulkEmailJob, TaskService, celery_app,
    send_single_email_task, send_bulk_email_task, _send_email_sync
)


class TestCeleryTaskInternals:
    """Test Celery task internals for coverage."""

    def test_send_email_sync_success(self):
        """Test synchronous email sending."""
        email_service = Mock()
        message = EmailMessage(to=["test@example.com"], subject="Test", text_body="Hello")

        # Mock the async send_email
        async_response = EmailResponse(
            id="test123",
            status="sent",
            message="OK",
            recipients_count=1
        )

        with patch('asyncio.run') as mock_run:
            mock_run.return_value = async_response

            result = _send_email_sync(email_service, message)

            assert result.id == "test123"
            assert result.status == "sent"

    def test_send_single_email_task_internal(self):
        """Test single email task internal logic."""
        email_data = {
            "to": ["test@example.com"],
            "subject": "Test Subject",
            "text_body": "Test Body"
        }

        mock_self = Mock()
        mock_self.request.id = "task123"

        with patch('dotmac.platform.communications.task_service.get_email_service') as mock_get:
            mock_service = Mock()

            # Mock the sync response
            with patch('dotmac.platform.communications.task_service._send_email_sync') as mock_sync:
                mock_sync.return_value = EmailResponse(
                    id="msg123",
                    status="sent",
                    message="Email sent",
                    recipients_count=1
                )

                result = send_single_email_task( email_data)

                assert result["status"] == "sent"
                assert result["message_id"] == "msg123"
                assert result["task_id"] == "task123"

    def test_send_single_email_task_error(self):
        """Test single email task error handling."""
        email_data = {
            "to": ["test@example.com"],
            "subject": "Test",
            "text_body": "Body"
        }

        mock_self = Mock()
        mock_self.request.id = "task123"

        with patch('dotmac.platform.communications.task_service.get_email_service') as mock_get:
            with patch('dotmac.platform.communications.task_service._send_email_sync') as mock_sync:
                mock_sync.side_effect = Exception("SMTP Error")

                result = send_single_email_task( email_data)

                assert result["status"] == "failed"
                assert "SMTP Error" in result["error"]

    def test_bulk_email_task_internal(self):
        """Test bulk email task internal logic."""
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
        mock_self.request.id = "task123"
        mock_self.update_state = Mock()

        with patch('dotmac.platform.communications.task_service.get_email_service') as mock_get:
            with patch('dotmac.platform.communications.task_service._send_email_sync') as mock_sync:
                # Return different responses for each email
                mock_sync.side_effect = [
                    EmailResponse(id="msg1", status="sent", message="OK", recipients_count=1),
                    EmailResponse(id="msg2", status="sent", message="OK", recipients_count=1)
                ]

                result = send_bulk_email_task.run( job_data)

                assert result["status"] == "completed"
                assert result["sent_count"] == 2
                assert result["failed_count"] == 0

                # Check progress updates were called
                assert mock_self.update_state.called

    def test_bulk_email_task_with_failures(self):
        """Test bulk email task with some failures."""
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

        mock_self = Mock()
        mock_self.request.id = "task123"
        mock_self.update_state = Mock()

        with patch('dotmac.platform.communications.task_service.get_email_service') as mock_get:
            with patch('dotmac.platform.communications.task_service._send_email_sync') as mock_sync:
                # Mix success and failure
                mock_sync.side_effect = [
                    EmailResponse(id="msg1", status="sent", message="OK", recipients_count=1),
                    EmailResponse(id="msg2", status="failed", message="Error", recipients_count=1),
                    EmailResponse(id="msg3", status="sent", message="OK", recipients_count=1)
                ]

                result = send_bulk_email_task.run( job_data)

                assert result["status"] == "completed"
                assert result["sent_count"] == 2
                assert result["failed_count"] == 1

    def test_bulk_email_task_exception(self):
        """Test bulk email task with exception."""
        job_data = {
            "id": "bulk123",
            "name": "Campaign",
            "messages": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "queued"
        }

        mock_self = Mock()
        mock_self.request.id = "task123"

        with patch('dotmac.platform.communications.task_service.get_email_service') as mock_get:
            mock_get.side_effect = Exception("Service unavailable")

            result = send_bulk_email_task.run( job_data)

            assert result["status"] == "failed"
            assert "Service unavailable" in result["error"]


class TestTaskServiceMethods:
    """Test TaskService methods."""

    def test_cancel_task_pending(self):
        """Test canceling a pending task."""
        service = TaskService()

        with patch.object(service.celery, 'AsyncResult') as mock_result_class:
            mock_result = Mock()
            mock_result.state = "PENDING"
            mock_result.revoke = Mock()
            mock_result_class.return_value = mock_result

            result = service.cancel_task("task123")

            assert result is True
            mock_result.revoke.assert_called_once_with(terminate=True)

    def test_cancel_task_already_success(self):
        """Test canceling an already successful task."""
        service = TaskService()

        with patch.object(service.celery, 'AsyncResult') as mock_result_class:
            mock_result = Mock()
            mock_result.state = "SUCCESS"
            mock_result_class.return_value = mock_result

            result = service.cancel_task("task123")

            assert result is False

    def test_cancel_task_exception(self):
        """Test cancel task exception handling."""
        service = TaskService()

        with patch.object(service.celery, 'AsyncResult') as mock_result_class:
            mock_result_class.side_effect = Exception("Redis error")

            result = service.cancel_task("task123")

            assert result is False


class TestTemplateServicePrivateMethods:
    """Test private methods through public interface."""

    def test_template_find_missing_variables(self):
        """Test finding missing variables in templates."""
        service = TemplateService()

        template = service.create_template(TemplateData(
            name="test",
            subject_template="Hello {{name}}",
            text_template="Your age is {{age}} and city is {{city}}"
        ))

        # Render with partial data
        rendered = service.render_template(template.id, {"name": "John"})

        # Missing variables should be tracked
        assert rendered.missing_variables == ["age", "city"]

    def test_template_variable_extraction(self):
        """Test variable extraction from templates."""
        service = TemplateService()

        # Create template with various variable patterns
        template = service.create_template(TemplateData(
            name="complex",
            subject_template="Hello {{user.name}}",
            text_template="""
            Welcome {{user.name}}!
            {% if user.premium %}
                Premium expires: {{user.premium_date}}
            {% endif %}
            {% for item in items %}
                - {{item}}
            {% endfor %}
            """
        ))

        # Variables should be extracted
        assert "user" in template.variables or "user.name" in template.variables
        assert "items" in template.variables

    def test_template_with_file_path(self):
        """Test template service with file path."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            service = TemplateService(template_dir=tmpdir)

            # Should still work even with directory specified
            template = service.create_template(TemplateData(
                name="file_test",
                subject_template="Test {{var}}",
                text_template="Body {{var}}"
            ))

            rendered = service.render_template(template.id, {"var": "value"})
            assert rendered.subject == "Test value"


class TestRouterErrorPaths:
    """Test router error handling paths."""

    def test_router_quick_render_error(self):
        """Test quick render error path."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from dotmac.platform.communications.router import router

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        with patch('dotmac.platform.communications.router.quick_render') as mock_quick:
            mock_quick.side_effect = Exception("Template error")

            response = client.post("/communications/quick-render", json={
                "subject": "{{invalid",
                "text_body": "Body",
                "data": {}
            })

            assert response.status_code == 400
            assert "Template error" in response.json()["detail"]

    def test_router_task_status_error(self):
        """Test task status error path."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from dotmac.platform.communications.router import router

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        with patch('dotmac.platform.communications.router.get_task_service') as mock_get:
            mock_service = Mock()
            mock_service.get_task_status.side_effect = Exception("Redis down")
            mock_get.return_value = mock_service

            response = client.get("/communications/tasks/task123")

            assert response.status_code == 500
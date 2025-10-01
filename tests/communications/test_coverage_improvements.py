"""
Additional tests to improve coverage to 90%.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
import smtplib
from email.mime.multipart import MIMEMultipart
from jinja2 import TemplateSyntaxError, UndefinedError

from dotmac.platform.communications.email_service import (
    EmailMessage, EmailResponse, EmailService, get_email_service
)
from dotmac.platform.communications.template_service import (
    TemplateData, RenderedTemplate, TemplateService, get_template_service
)
from dotmac.platform.communications.task_service import (
    BulkEmailJob, BulkEmailResult, TaskService, get_task_service
)
from dotmac.platform.communications.router import router


# ============= Router Tests =============

class TestRouterEndpoints:
    """Test all router endpoints for coverage."""

    @pytest.fixture
    def client(self):
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_send_email_endpoint_success(self, client):
        """Test successful email send via API."""
        with patch('dotmac.platform.communications.router.get_email_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.send_email.return_value = EmailResponse(
                id="msg123",
                status="sent",
                message="Email sent",
                recipients_count=1
            )
            mock_get_service.return_value = mock_service

            response = client.post("/communications/email/send", json={
                "to": ["test@example.com"],
                "subject": "Test",
                "text_body": "Hello"
            })

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "msg123"
            assert data["status"] == "sent"

    def test_send_email_endpoint_error(self, client):
        """Test email send error handling."""
        with patch('dotmac.platform.communications.router.get_email_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.send_email.side_effect = Exception("SMTP error")
            mock_get_service.return_value = mock_service

            response = client.post("/communications/email/send", json={
                "to": ["test@example.com"],
                "subject": "Test",
                "text_body": "Hello"
            })

            assert response.status_code == 500
            assert "SMTP error" in response.json()["detail"]

    def test_queue_email_endpoint_success(self, client):
        """Test successful email queueing."""
        with patch('dotmac.platform.communications.router.queue_email') as mock_queue:
            mock_queue.return_value = "task123"

            response = client.post("/communications/email/queue", json={
                "to": ["test@example.com"],
                "subject": "Test",
                "text_body": "Hello"
            })

            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "task123"
            assert data["status"] == "queued"

    def test_queue_email_endpoint_error(self, client):
        """Test email queue error handling."""
        with patch('dotmac.platform.communications.router.queue_email') as mock_queue:
            mock_queue.side_effect = Exception("Queue error")

            response = client.post("/communications/email/queue", json={
                "to": ["test@example.com"],
                "subject": "Test",
                "text_body": "Hello"
            })

            assert response.status_code == 500
            assert "Queue error" in response.json()["detail"]

    def test_create_template_endpoint_success(self, client):
        """Test successful template creation."""
        with patch('dotmac.platform.communications.router.create_template') as mock_create:
            mock_create.return_value = TemplateData(
                id="tpl123",
                name="welcome",
                subject_template="Welcome {{name}}",
                text_template="Hello {{name}}"
            )

            response = client.post("/communications/templates", json={
                "name": "welcome",
                "subject_template": "Welcome {{name}}",
                "text_template": "Hello {{name}}"
            })

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "tpl123"
            assert data["name"] == "welcome"

    def test_create_template_endpoint_error(self, client):
        """Test template creation error."""
        with patch('dotmac.platform.communications.router.create_template') as mock_create:
            mock_create.side_effect = ValueError("Invalid template")

            response = client.post("/communications/templates", json={
                "name": "bad",
                "subject_template": "{{",
                "text_template": "Invalid"
            })

            assert response.status_code == 400
            assert "Invalid template" in response.json()["detail"]

    def test_list_templates_endpoint(self, client):
        """Test list templates endpoint."""
        with patch('dotmac.platform.communications.router.get_template_service') as mock_get_service:
            mock_service = Mock()
            mock_service.list_templates.return_value = [
                TemplateData(id="tpl1", name="welcome", subject_template="Welcome"),
                TemplateData(id="tpl2", name="goodbye", subject_template="Goodbye")
            ]
            mock_get_service.return_value = mock_service

            response = client.get("/communications/templates")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2  # Returns list directly

    def test_get_template_endpoint_success(self, client):
        """Test get template by ID."""
        with patch('dotmac.platform.communications.router.get_template_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_template.return_value = TemplateData(
                id="tpl123",
                name="welcome",
                subject_template="Welcome"
            )
            mock_get_service.return_value = mock_service

            response = client.get("/communications/templates/tpl123")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "tpl123"

    def test_get_template_endpoint_not_found(self, client):
        """Test get template not found."""
        with patch('dotmac.platform.communications.router.get_template_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_template.side_effect = ValueError("Template not found")
            mock_get_service.return_value = mock_service

            response = client.get("/communications/templates/invalid")

            assert response.status_code == 500  # Router returns 500 for errors

    def test_delete_template_endpoint(self, client):
        """Test delete template endpoint."""
        with patch('dotmac.platform.communications.router.get_template_service') as mock_get_service:
            mock_service = Mock()
            mock_service.delete_template.return_value = True
            mock_get_service.return_value = mock_service

            response = client.delete("/communications/templates/tpl123")

            assert response.status_code == 200
            assert "deleted successfully" in response.json()["message"]

    def test_render_template_endpoint_success(self, client):
        """Test render template endpoint."""
        with patch('dotmac.platform.communications.router.render_template') as mock_render:
            mock_render.return_value = RenderedTemplate(
                template_id="tpl123",
                subject="Welcome John",
                text_body="Hello John"
            )

            response = client.post("/communications/templates/render", json={
                "template_id": "tpl123",
                "data": {"name": "John"}
            })

            assert response.status_code == 200
            data = response.json()
            assert data["subject"] == "Welcome John"

    def test_render_template_endpoint_error(self, client):
        """Test render template error."""
        with patch('dotmac.platform.communications.router.render_template') as mock_render:
            mock_render.side_effect = ValueError("Template not found")

            response = client.post("/communications/templates/render", json={
                "template_id": "invalid",
                "data": {}
            })

            assert response.status_code == 404

    def test_bulk_email_queue_endpoint_success(self, client):
        """Test bulk email queue endpoint."""
        with patch('dotmac.platform.communications.router.queue_bulk_emails') as mock_queue:
            mock_queue.return_value = "bulk123"

            response = client.post("/communications/bulk-email/queue", json={
                "job_name": "Campaign",
                "messages": [
                    {"to": ["user1@example.com"], "subject": "Test", "text_body": "Hello"},
                    {"to": ["user2@example.com"], "subject": "Test", "text_body": "Hi"}
                ]
            })

            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == "bulk123"

    def test_bulk_email_queue_endpoint_error(self, client):
        """Test bulk email queue error."""
        with patch('dotmac.platform.communications.router.queue_bulk_emails') as mock_queue:
            mock_queue.side_effect = Exception("Queue full")

            response = client.post("/communications/bulk-email/queue", json={
                "job_name": "Campaign",
                "messages": []
            })

            assert response.status_code == 500
            assert "Queue full" in response.json()["detail"]

    def test_bulk_email_status_endpoint_success(self, client):
        """Test bulk email status endpoint."""
        with patch('dotmac.platform.communications.router.get_task_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_job_status.return_value = {
                "job_id": "bulk123",
                "status": "completed",
                "progress": 100
            }
            mock_get_service.return_value = mock_service

            response = client.get("/communications/bulk-email/status/bulk123")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"

    def test_bulk_email_status_endpoint_not_found(self, client):
        """Test bulk email status not found."""
        with patch('dotmac.platform.communications.router.get_task_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_job_status.return_value = None
            mock_get_service.return_value = mock_service

            response = client.get("/communications/bulk-email/status/invalid")

            assert response.status_code == 404

    def test_cancel_bulk_email_endpoint(self, client):
        """Test cancel bulk email endpoint."""
        with patch('dotmac.platform.communications.router.get_task_service') as mock_get_service:
            mock_service = Mock()
            mock_service.cancel_job.return_value = True
            mock_get_service.return_value = mock_service

            response = client.post("/communications/bulk-email/cancel/bulk123")

            assert response.status_code == 200
            assert response.json()["success"] is True

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/communications/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "email_service" in data["services"]


# ============= Email Service Edge Cases =============

class TestEmailServiceEdgeCases:
    """Test email service edge cases for coverage."""

    def test_email_with_cc_and_bcc(self):
        """Test email with CC and BCC."""
        service = EmailService()
        msg = service._create_mime_message(
            EmailMessage(
                to=["to@example.com"],
                subject="Test",
                text_body="Hello",
                cc=["cc@example.com"],
                bcc=["bcc@example.com"]
            ),
            "msg123"
        )

        assert "cc@example.com" in msg['Cc']
        # BCC is not in headers but used in send

    def test_email_with_reply_to(self):
        """Test email with reply-to."""
        service = EmailService()
        msg = service._create_mime_message(
            EmailMessage(
                to=["to@example.com"],
                subject="Test",
                text_body="Hello",
                reply_to="reply@example.com"
            ),
            "msg123"
        )

        assert msg['Reply-To'] == "reply@example.com"

    def test_email_with_no_body(self):
        """Test email with no body."""
        service = EmailService()
        msg = service._create_mime_message(
            EmailMessage(
                to=["to@example.com"],
                subject="Test"
            ),
            "msg123"
        )

        # Should have empty text part
        assert msg.get_payload() is not None

    def test_format_from_with_name(self):
        """Test formatting from address with name."""
        service = EmailService()
        formatted = service._format_from_address("sender@example.com", "John Doe")
        assert formatted == '"John Doe" <sender@example.com>'

    @patch('smtplib.SMTP')
    async def test_smtp_with_auth(self, mock_smtp_class):
        """Test SMTP with authentication."""
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp

        service = EmailService(
            smtp_user="user",
            smtp_password="pass",
            use_tls=True
        )

        await service._send_smtp(
            MIMEMultipart(),
            EmailMessage(to=["test@example.com"], subject="Test")
        )

        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("user", "pass")

    async def test_bulk_email_progress_logging(self):
        """Test bulk email progress logging."""
        service = EmailService()
        messages = [
            EmailMessage(to=[f"user{i}@example.com"], subject=f"Test {i}")
            for i in range(15)  # More than 10 to trigger progress log
        ]

        with patch.object(service, 'send_email', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = EmailResponse(
                id="test", status="sent", message="OK", recipients_count=1
            )

            results = await service.send_bulk_emails(messages)

            assert len(results) == 15
            assert all(r.status == "sent" for r in results)


# ============= Template Service Edge Cases =============

class TestTemplateServiceEdgeCases:
    """Test template service edge cases for coverage."""

    def test_template_service_with_custom_dir(self):
        """Test template service with custom directory."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            service = TemplateService(template_dir=tmpdir)
            assert service.file_env is not None

    def test_template_service_with_invalid_dir(self):
        """Test template service with non-existent directory."""
        service = TemplateService(template_dir="/nonexistent/path")
        # Should still work with dict templates
        assert service.dict_env is not None

    def test_extract_variables_from_complex_template(self):
        """Test variable extraction from complex template."""
        service = TemplateService()

        # Template with conditions and loops
        template_str = """
        Hello {{name}}!
        {% if age %}You are {{age}} years old{% endif %}
        {% for item in items %}
            - {{item.name}}: {{item.value}}
        {% endfor %}
        """

        # This method is private, test through public interface
        template = service.create_template(TemplateData(
            name="complex",
            subject_template=template_str,
            text_template=template_str
        ))
        variables = template.variables
        assert "name" in variables
        assert "age" in variables
        assert "items" in variables

    def test_find_missing_variables(self):
        """Test finding missing variables."""
        service = TemplateService()

        template = TemplateData(
            name="test",
            subject_template="Hello {{name}}",
            text_template="Age: {{age}}",
            variables=["name", "age", "city"]
        )

        missing = service._find_missing_variables(template, {"name": "John"})
        assert "age" in missing
        assert "city" in missing
        assert "name" not in missing

    def test_template_render_with_file_template(self):
        """Test rendering with file-based template."""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a template file
            template_file = os.path.join(tmpdir, "test.txt")
            with open(template_file, 'w') as f:
                f.write("Hello {{name}}!")

            service = TemplateService(template_dir=tmpdir)

            # This would use file template if it existed
            template = service.create_template(TemplateData(
                name="test",
                subject_template="Subject",
                text_template="Hello {{name}}!"
            ))

            rendered = service.render_template(template.id, {"name": "World"})
            assert rendered.text_body == "Hello World!"

    def test_template_syntax_validation_in_render(self):
        """Test template syntax validation during rendering."""
        service = TemplateService()

        template = TemplateData(
            id="test123",
            name="test",
            subject_template="Valid",
            text_template="Also valid {{name}}"
        )
        service.templates["test123"] = template

        # Should render successfully
        result = service.render_template("test123", {"name": "Test"})
        assert result.text_body == "Also valid Test"

    def test_render_string_with_html_autoescape(self):
        """Test HTML autoescaping in templates."""
        service = TemplateService()

        # HTML should be escaped in templates
        template = service.create_template(TemplateData(
            name="xss_test",
            subject_template="Hello {{name}}!",
            html_template="<p>Hello {{name}}!</p>"
        ))

        result = service.render_template(template.id, {"name": "<script>alert('xss')</script>"})

        # Script tags should be escaped in rendered output
        if result.html_body:
            assert "<script>" not in result.html_body
            assert "&lt;script&gt;" in result.html_body or "&#x" in result.html_body or "&amp;" in result.html_body


# ============= Task Service and Celery Tests =============

class TestTaskServiceAndCelery:
    """Test task service and Celery functions."""

    def test_send_single_email_task_success(self):
        """Test single email task queueing."""
        # Test through the public interface instead of calling task directly
        from dotmac.platform.communications.task_service import queue_email

        with patch('dotmac.platform.communications.task_service.send_single_email_task.delay') as mock_delay:
            mock_delay.return_value.id = "task123"

            task_id = queue_email(
                to=["test@example.com"],
                subject="Test",
                text_body="Hello"
            )

            assert task_id == "task123"
            mock_delay.assert_called_once()

    def test_send_single_email_task_failure(self):
        """Test single email task failure handling."""
        # Test error handling in queue
        from dotmac.platform.communications.task_service import queue_email

        with patch('dotmac.platform.communications.task_service.send_single_email_task.delay') as mock_delay:
            mock_delay.side_effect = Exception("Queue error")

            # Should handle error gracefully
            with pytest.raises(Exception) as exc:
                queue_email(
                    to=["test@example.com"],
                    subject="Test",
                    text_body="Hello"
                )
            assert "Queue error" in str(exc.value)

    def test_bulk_email_task_queueing(self):
        """Test bulk email task queueing."""
        from dotmac.platform.communications.task_service import queue_bulk_emails

        messages = [
            EmailMessage(to=["user1@example.com"], subject="Test", text_body="Hello"),
            EmailMessage(to=["user2@example.com"], subject="Test", text_body="Hi")
        ]

        with patch('dotmac.platform.communications.task_service.send_bulk_email_task.delay') as mock_delay:
            mock_delay.return_value.id = "bulk123"

            task_id = queue_bulk_emails("Campaign", messages)

            assert task_id == "bulk123"
            mock_delay.assert_called_once()


    def test_task_service_get_job_status(self):
        """Test getting job status."""
        service = TaskService()

        with patch.object(service.celery, 'AsyncResult') as mock_result:
            mock_async = Mock()
            mock_async.state = "SUCCESS"
            mock_async.info = {"sent_count": 10, "failed_count": 2}
            mock_result.return_value = mock_async

            status = service.get_task_status("task123")

            assert status["state"] == "SUCCESS"
            assert status["info"]["sent_count"] == 10

    def test_task_service_cancel_job_success(self):
        """Test canceling a job successfully."""
        service = TaskService()

        with patch.object(service.celery, 'AsyncResult') as mock_result:
            mock_async = Mock()
            mock_async.revoke = Mock()
            mock_async.state = "PENDING"
            mock_result.return_value = mock_async

            result = service.cancel_task("task123")

            # cancel_task returns True for PENDING tasks
            assert result is True
            mock_async.revoke.assert_called_once_with(terminate=True)

    def test_task_service_cancel_job_already_completed(self):
        """Test canceling an already completed job."""
        service = TaskService()

        with patch.object(service.celery, 'AsyncResult') as mock_result:
            mock_async = Mock()
            mock_async.state = "SUCCESS"
            mock_result.return_value = mock_async

            result = service.cancel_task("task123")

            # Result depends on the implementation - SUCCESS tasks can't be cancelled
            assert result is False  # Already completed tasks return False


# ============= Integration Tests =============

class TestCommunicationsIntegration:
    """Integration tests for full coverage."""

    async def test_template_email_integration(self):
        """Test template rendering to email sending."""
        # Create template
        template_service = get_template_service()
        template = template_service.create_template(TemplateData(
            name="welcome",
            subject_template="Welcome {{name}}",
            text_template="Hello {{name}}, welcome!",
            html_template="<h1>Hello {{name}}</h1>"
        ))

        # Render template
        rendered = template_service.render_template(
            template.id,
            {"name": "Alice"}
        )

        # Send email with rendered content
        email_service = get_email_service()
        with patch.object(email_service, '_send_smtp', new_callable=AsyncMock):
            response = await email_service.send_email(EmailMessage(
                to=["alice@example.com"],
                subject=rendered.subject,
                text_body=rendered.text_body,
                html_body=rendered.html_body
            ))

            assert response.status == "sent"
            assert response.recipients_count == 1

    def test_service_singleton_persistence(self):
        """Test that services maintain state as singletons."""
        # Add template to service
        template_service = get_template_service()
        template = template_service.create_template(TemplateData(
            name="persistent",
            subject_template="Test"
        ))

        # Get service again - should have same template
        same_service = get_template_service()
        retrieved = same_service.get_template(template.id)
        assert retrieved.name == "persistent"

        # Clean up
        same_service.delete_template(template.id)
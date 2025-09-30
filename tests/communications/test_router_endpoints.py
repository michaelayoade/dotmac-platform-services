"""
Comprehensive tests for communications router endpoints.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from fastapi import HTTPException
from fastapi.testclient import TestClient

from dotmac.platform.communications.email_service import EmailResponse
from dotmac.platform.communications.template_service import Template, RenderedTemplate
from dotmac.platform.communications.router import router


@pytest.fixture
def client():
    """Create a test client."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestEmailEndpoints:
    """Test email-related endpoints."""

    def test_send_email_endpoint_success(self, client):
        """Test successful email send."""
        with patch('dotmac.platform.communications.router.get_email_service') as mock_get_service:
            with patch('dotmac.platform.communications.router.get_async_db'):
                mock_service = AsyncMock()
                mock_service.send_email.return_value = EmailResponse(
                    id="msg123",
                    status="sent",
                    message="Email sent",
                    recipients_count=1
                )
                mock_get_service.return_value = mock_service

                response = client.post("/email/send", json={
                    "to": ["test@example.com"],
                    "subject": "Test",
                    "text_body": "Body"
                })

                assert response.status_code == 200
                data = response.json()
                assert data["id"] == "msg123"
                assert data["status"] == "sent"

    def test_send_email_endpoint_failure(self, client):
        """Test email send failure."""
        with patch('dotmac.platform.communications.router.get_email_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.send_email.side_effect = Exception("SMTP error")
            mock_get_service.return_value = mock_service

            response = client.post("/email/send", json={
                "to": ["test@example.com"],
                "subject": "Test",
                "text_body": "Body"
            })

            assert response.status_code == 500
            assert "Email send failed" in response.json()["detail"]

    def test_send_email_with_db_logging(self, client):
        """Test email send with database logging."""
        with patch('dotmac.platform.communications.router.get_email_service') as mock_get_service:
            with patch('dotmac.platform.communications.router.get_async_db') as mock_get_db:
                with patch('dotmac.platform.communications.router.get_metrics_service') as mock_get_metrics:
                    # Setup mocks
                    mock_service = AsyncMock()
                    mock_service.send_email.return_value = EmailResponse(
                        id="msg123",
                        status="sent",
                        message="OK",
                        recipients_count=1
                    )
                    mock_get_service.return_value = mock_service

                    mock_metrics = AsyncMock()
                    mock_log_entry = Mock()
                    mock_log_entry.id = "log123"
                    mock_metrics.log_communication.return_value = mock_log_entry
                    mock_get_metrics.return_value = mock_metrics

                    # Mock async context manager
                    mock_db = AsyncMock()
                    mock_get_db.return_value.__aenter__.return_value = mock_db
                    mock_get_db.return_value.__aexit__.return_value = None

                    response = client.post("/email/send", json={
                        "to": ["test@example.com"],
                        "subject": "Test",
                        "text_body": "Body"
                    })

                    assert response.status_code == 200
                    # Verify metrics were called
                    assert mock_metrics.log_communication.called

    def test_queue_email_endpoint_success(self, client):
        """Test email queueing."""
        with patch('dotmac.platform.communications.router.queue_email') as mock_queue:
            mock_queue.return_value = "task_123"

            response = client.post("/email/queue", json={
                "to": ["test@example.com"],
                "subject": "Test",
                "text_body": "Body"
            })

            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "task_123"
            assert data["status"] == "queued"

    def test_queue_email_endpoint_failure(self, client):
        """Test email queueing failure."""
        with patch('dotmac.platform.communications.router.queue_email') as mock_queue:
            mock_queue.side_effect = Exception("Celery not available")

            response = client.post("/email/queue", json={
                "to": ["test@example.com"],
                "subject": "Test",
                "text_body": "Body"
            })

            assert response.status_code == 500
            assert "Email queue failed" in response.json()["detail"]

    def test_send_email_validation_error(self, client):
        """Test email send with validation error."""
        response = client.post("/email/send", json={
            "to": ["invalid-email"],
            "subject": "Test"
        })

        assert response.status_code == 422  # Validation error


class TestTemplateEndpoints:
    """Test template-related endpoints."""

    def test_create_template_endpoint(self, client):
        """Test template creation."""
        with patch('dotmac.platform.communications.router.create_template') as mock_create:
            mock_template = Template(
                id="tpl123",
                name="welcome",
                subject_template="Welcome {{ name }}",
                text_template="Hello {{ name }}",
                html_template=None,
                variables=["name"],
                created_at=datetime.now(timezone.utc)
            )
            mock_create.return_value = mock_template

            response = client.post("/templates", json={
                "name": "welcome",
                "subject_template": "Welcome {{ name }}",
                "text_template": "Hello {{ name }}"
            })

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "welcome"
            assert data["id"] == "tpl123"

    def test_list_templates_endpoint(self, client):
        """Test listing templates."""
        with patch('dotmac.platform.communications.router.get_template_service') as mock_get_service:
            mock_service = Mock()
            mock_service.list_templates.return_value = [
                Template(
                    id="tpl1",
                    name="template1",
                    subject_template="Subject 1",
                    text_template="Body 1",
                    html_template=None,
                    variables=["var1"],
                    created_at=datetime.now(timezone.utc)
                ),
                Template(
                    id="tpl2",
                    name="template2",
                    subject_template="Subject 2",
                    text_template="Body 2",
                    html_template=None,
                    variables=["var2"],
                    created_at=datetime.now(timezone.utc)
                )
            ]
            mock_get_service.return_value = mock_service

            response = client.get("/templates")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["name"] == "template1"

    def test_get_template_endpoint_success(self, client):
        """Test getting a specific template."""
        with patch('dotmac.platform.communications.router.get_template_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_template.return_value = Template(
                id="tpl123",
                name="welcome",
                subject_template="Welcome",
                text_template="Hello",
                html_template=None,
                variables=[],
                created_at=datetime.now(timezone.utc)
            )
            mock_get_service.return_value = mock_service

            response = client.get("/templates/tpl123")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "tpl123"

    def test_get_template_endpoint_not_found(self, client):
        """Test getting non-existent template."""
        with patch('dotmac.platform.communications.router.get_template_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_template.side_effect = KeyError("Template not found")
            mock_get_service.return_value = mock_service

            response = client.get("/templates/nonexistent")

            assert response.status_code == 404

    def test_render_template_endpoint(self, client):
        """Test template rendering."""
        with patch('dotmac.platform.communications.router.render_template') as mock_render:
            mock_render.return_value = RenderedTemplate(
                subject="Welcome John",
                text_body="Hello John",
                html_body=None
            )

            response = client.post("/templates/render", json={
                "template_id": "tpl123",
                "variables": {"name": "John"}
            })

            assert response.status_code == 200
            data = response.json()
            assert data["subject"] == "Welcome John"

    def test_delete_template_endpoint_success(self, client):
        """Test template deletion."""
        with patch('dotmac.platform.communications.router.get_template_service') as mock_get_service:
            mock_service = Mock()
            mock_service.delete_template.return_value = None
            mock_get_service.return_value = mock_service

            response = client.delete("/templates/tpl123")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "deleted"

    def test_delete_template_endpoint_not_found(self, client):
        """Test deleting non-existent template."""
        with patch('dotmac.platform.communications.router.get_template_service') as mock_get_service:
            mock_service = Mock()
            mock_service.delete_template.side_effect = KeyError("Not found")
            mock_get_service.return_value = mock_service

            response = client.delete("/templates/nonexistent")

            assert response.status_code == 404

    def test_quick_render_endpoint(self, client):
        """Test quick rendering without saving template."""
        with patch('dotmac.platform.communications.router.quick_render') as mock_quick:
            mock_quick.return_value = RenderedTemplate(
                subject="Hi User",
                text_body="Hello User",
                html_body=None
            )

            response = client.post("/quick-render", json={
                "subject_template": "Hi {{ name }}",
                "text_template": "Hello {{ name }}",
                "variables": {"name": "User"}
            })

            assert response.status_code == 200
            data = response.json()
            assert data["subject"] == "Hi User"


class TestBulkEmailEndpoints:
    """Test bulk email endpoints."""

    def test_queue_bulk_email_endpoint(self, client):
        """Test bulk email queueing."""
        with patch('dotmac.platform.communications.router.queue_bulk_emails') as mock_queue:
            mock_queue.return_value = "job_123"

            response = client.post("/bulk-email/queue", json={
                "name": "Campaign",
                "messages": [
                    {"to": ["user1@example.com"], "subject": "Test1", "text_body": "Body1"},
                    {"to": ["user2@example.com"], "subject": "Test2", "text_body": "Body2"}
                ]
            })

            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == "job_123"
            assert data["status"] == "queued"

    def test_get_bulk_email_status_endpoint(self, client):
        """Test getting bulk email job status."""
        with patch('dotmac.platform.communications.router.get_task_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_job_status.return_value = {
                "job_id": "job_123",
                "status": "completed",
                "total": 10,
                "sent": 8,
                "failed": 2
            }
            mock_get_service.return_value = mock_service

            response = client.get("/bulk-email/status/job_123")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"

    def test_cancel_bulk_email_endpoint(self, client):
        """Test canceling bulk email job."""
        with patch('dotmac.platform.communications.router.get_task_service') as mock_get_service:
            mock_service = Mock()
            mock_service.cancel_job.return_value = True
            mock_get_service.return_value = mock_service

            response = client.post("/bulk-email/cancel/job_123")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "cancelled"


class TestUtilityEndpoints:
    """Test utility endpoints."""

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        with patch('dotmac.platform.communications.router.get_email_service') as mock_get_email:
            with patch('dotmac.platform.communications.router.get_template_service') as mock_get_tpl:
                with patch('dotmac.platform.communications.router.get_task_service') as mock_get_task:
                    mock_get_email.return_value = Mock()
                    mock_get_tpl.return_value = Mock()
                    mock_get_task.return_value = Mock()

                    response = client.get("/health")

                    assert response.status_code == 200
                    data = response.json()
                    assert data["status"] == "healthy"
                    assert "email_service" in data["services"]

    def test_get_task_status_endpoint(self, client):
        """Test getting individual task status."""
        with patch('dotmac.platform.communications.router.get_task_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_task_status.return_value = {
                "task_id": "task_123",
                "status": "SUCCESS",
                "result": {"message_id": "msg123"}
            }
            mock_get_service.return_value = mock_service

            response = client.get("/tasks/task_123")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "SUCCESS"


class TestStatsEndpoints:
    """Test statistics and metrics endpoints."""

    def test_get_stats_endpoint(self, client):
        """Test getting communication stats."""
        with patch('dotmac.platform.communications.router.get_async_db') as mock_get_db:
            with patch('dotmac.platform.communications.router.get_metrics_service') as mock_get_metrics:
                mock_metrics = AsyncMock()
                mock_metrics.get_stats.return_value = {
                    "total_sent": 100,
                    "total_failed": 5,
                    "emails": 80,
                    "sms": 20,
                    "success_rate": 0.95
                }
                mock_get_metrics.return_value = mock_metrics

                # Mock async context manager
                mock_db = AsyncMock()
                mock_get_db.return_value.__aenter__.return_value = mock_db
                mock_get_db.return_value.__aexit__.return_value = None

                response = client.get("/stats")

                assert response.status_code == 200
                data = response.json()
                assert data["total_sent"] == 100

    def test_get_activity_endpoint(self, client):
        """Test getting communication activity."""
        with patch('dotmac.platform.communications.router.get_async_db') as mock_get_db:
            with patch('dotmac.platform.communications.router.get_metrics_service') as mock_get_metrics:
                mock_metrics = AsyncMock()
                mock_metrics.get_recent_activity.return_value = [
                    {
                        "id": "log1",
                        "type": "email",
                        "recipient": "user@example.com",
                        "status": "sent",
                        "created_at": datetime.now(timezone.utc)
                    }
                ]
                mock_get_metrics.return_value = mock_metrics

                # Mock async context manager
                mock_db = AsyncMock()
                mock_get_db.return_value.__aenter__.return_value = mock_db
                mock_get_db.return_value.__aexit__.return_value = None

                response = client.get("/activity")

                assert response.status_code == 200
                data = response.json()
                assert len(data) > 0
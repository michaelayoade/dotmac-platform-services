"""
Direct router function tests for better coverage.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
from fastapi import HTTPException

from dotmac.platform.communications.router import (
    send_email_endpoint,
    queue_email_endpoint,
    queue_bulk_email_job,
    get_bulk_email_status,
    cancel_bulk_email_job,
    create_template_endpoint,
    list_templates_endpoint,
    get_template_endpoint,
    delete_template_endpoint,
    render_template_endpoint,
    quick_render_endpoint,
    get_task_status,
    health_check,
    get_communication_stats,
    get_recent_activity,
    EmailRequest,
    BulkEmailRequest,
    TemplateRequest,
    RenderRequest,
    QuickRenderRequest,
)
from dotmac.platform.communications.email_service import EmailResponse
from dotmac.platform.communications.template_service import TemplateData, RenderedTemplate


pytestmark = pytest.mark.asyncio


class TestEmailEndpointsDirect:
    """Direct tests of email endpoints."""

    async def test_send_email_endpoint_success(self):
        """Test send_email_endpoint with successful send."""
        request = EmailRequest(
            to=["test@example.com"], subject="Test Subject", text_body="Test body"
        )

        with patch("dotmac.platform.communications.router.get_email_service") as mock_get_service:
            with patch("dotmac.platform.communications.router.get_async_db") as mock_get_db:
                # Mock email service
                mock_service = AsyncMock()
                mock_service.send_email.return_value = EmailResponse(
                    id="msg_123",
                    status="sent",
                    message="Email sent successfully",
                    recipients_count=1,
                )
                mock_get_service.return_value = mock_service

                # Mock DB context manager
                mock_db = AsyncMock()
                mock_get_db.return_value.__aenter__.return_value = mock_db
                mock_get_db.return_value.__aexit__.return_value = None

                # Mock metrics service
                with patch(
                    "dotmac.platform.communications.router.get_metrics_service"
                ) as mock_get_metrics:
                    mock_metrics = AsyncMock()
                    mock_log = Mock()
                    mock_log.id = "log_123"
                    mock_metrics.log_communication.return_value = mock_log
                    mock_metrics.update_communication_status.return_value = None
                    mock_get_metrics.return_value = mock_metrics

                    result = await send_email_endpoint(request, current_user=None)

                    assert result.id == "msg_123"
                    assert result.status == "sent"
                    mock_service.send_email.assert_called_once()

    async def test_send_email_endpoint_with_user_context(self):
        """Test send_email_endpoint with authenticated user."""
        request = EmailRequest(to=["test@example.com"], subject="Test", text_body="Body")

        mock_user = Mock()
        mock_user.user_id = "user_123"
        mock_user.tenant_id = "tenant_123"

        with patch("dotmac.platform.communications.router.get_email_service") as mock_get_service:
            with patch("dotmac.platform.communications.router.get_async_db") as mock_get_db:
                mock_service = AsyncMock()
                mock_service.send_email.return_value = EmailResponse(
                    id="msg_456", status="sent", message="OK", recipients_count=1
                )
                mock_get_service.return_value = mock_service

                mock_db = AsyncMock()
                mock_get_db.return_value.__aenter__.return_value = mock_db
                mock_get_db.return_value.__aexit__.return_value = None

                with patch(
                    "dotmac.platform.communications.router.get_metrics_service"
                ) as mock_get_metrics:
                    mock_metrics = AsyncMock()
                    mock_log = Mock()
                    mock_log.id = "log_456"
                    mock_metrics.log_communication.return_value = mock_log
                    mock_get_metrics.return_value = mock_metrics

                    result = await send_email_endpoint(request, current_user=mock_user)

                    assert result.id == "msg_456"
                    # Verify metrics called with user context
                    mock_metrics.log_communication.assert_called_once()
                    call_kwargs = mock_metrics.log_communication.call_args[1]
                    assert call_kwargs["user_id"] == "user_123"
                    assert call_kwargs["tenant_id"] == "tenant_123"

    async def test_send_email_endpoint_db_logging_failure(self):
        """Test send_email_endpoint when DB logging fails."""
        request = EmailRequest(to=["test@example.com"], subject="Test", text_body="Body")

        with patch("dotmac.platform.communications.router.get_email_service") as mock_get_service:
            with patch("dotmac.platform.communications.router.get_async_db") as mock_get_db:
                mock_service = AsyncMock()
                mock_service.send_email.return_value = EmailResponse(
                    id="msg_789", status="sent", message="OK", recipients_count=1
                )
                mock_get_service.return_value = mock_service

                # DB context raises error
                mock_get_db.return_value.__aenter__.side_effect = Exception("DB connection failed")

                result = await send_email_endpoint(request, current_user=None)

                # Should still succeed even if logging fails
                assert result.id == "msg_789"
                assert result.status == "sent"

    async def test_send_email_endpoint_email_send_failure(self):
        """Test send_email_endpoint when email sending fails."""
        request = EmailRequest(to=["test@example.com"], subject="Test", text_body="Body")

        with patch("dotmac.platform.communications.router.get_email_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_service.send_email.side_effect = Exception("SMTP connection failed")
            mock_get_service.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await send_email_endpoint(request, current_user=None)

            assert exc_info.value.status_code == 500
            assert "Email send failed" in exc_info.value.detail

    async def test_send_email_endpoint_status_update_failure(self):
        """Test when status update fails but email succeeds."""
        request = EmailRequest(to=["test@example.com"], subject="Test", text_body="Body")

        with patch("dotmac.platform.communications.router.get_email_service") as mock_get_service:
            with patch("dotmac.platform.communications.router.get_async_db") as mock_get_db:
                mock_service = AsyncMock()
                mock_service.send_email.return_value = EmailResponse(
                    id="msg_999", status="sent", message="OK", recipients_count=1
                )
                mock_get_service.return_value = mock_service

                mock_db = AsyncMock()
                mock_get_db.return_value.__aenter__.return_value = mock_db
                mock_get_db.return_value.__aexit__.return_value = None

                with patch(
                    "dotmac.platform.communications.router.get_metrics_service"
                ) as mock_get_metrics:
                    mock_metrics = AsyncMock()
                    mock_log = Mock()
                    mock_log.id = "log_999"
                    mock_metrics.log_communication.return_value = mock_log
                    # Status update fails
                    mock_metrics.update_communication_status.side_effect = Exception("DB error")
                    mock_get_metrics.return_value = mock_metrics

                    result = await send_email_endpoint(request, current_user=None)

                    # Should still return success
                    assert result.id == "msg_999"
                    assert result.status == "sent"

    async def test_queue_email_endpoint_success(self):
        """Test queue_email_endpoint successful queueing."""
        request = EmailRequest(
            to=["test@example.com"], subject="Queued Email", text_body="This will be sent async"
        )

        with patch("dotmac.platform.communications.router.queue_email") as mock_queue:
            mock_queue.return_value = "task_abc123"

            result = await queue_email_endpoint(request)

            assert result["task_id"] == "task_abc123"
            assert result["status"] == "queued"
            assert "queued for background sending" in result["message"]
            mock_queue.assert_called_once()

    async def test_queue_email_endpoint_failure(self):
        """Test queue_email_endpoint when queueing fails."""
        request = EmailRequest(to=["test@example.com"], subject="Failed Queue", text_body="Body")

        with patch("dotmac.platform.communications.router.queue_email") as mock_queue:
            mock_queue.side_effect = Exception("Celery broker unavailable")

            with pytest.raises(HTTPException) as exc_info:
                await queue_email_endpoint(request)

            assert exc_info.value.status_code == 500
            assert "Email queue failed" in exc_info.value.detail


class TestEmailEndpointValidation:
    """Test email endpoint input validation."""

    async def test_send_email_with_multiple_recipients(self):
        """Test sending to multiple recipients."""
        request = EmailRequest(
            to=["user1@example.com", "user2@example.com", "user3@example.com"],
            subject="Multi-recipient email",
            text_body="Sent to multiple people",
        )

        with patch("dotmac.platform.communications.router.get_email_service") as mock_get_service:
            with patch("dotmac.platform.communications.router.get_async_db"):
                mock_service = AsyncMock()
                mock_service.send_email.return_value = EmailResponse(
                    id="msg_multi", status="sent", message="OK", recipients_count=3
                )
                mock_get_service.return_value = mock_service

                result = await send_email_endpoint(request, current_user=None)

                assert result.recipients_count == 3

    async def test_send_email_with_html_and_text(self):
        """Test sending with both HTML and text bodies."""
        request = EmailRequest(
            to=["test@example.com"],
            subject="Rich email",
            text_body="Plain text version",
            html_body="<p>HTML version</p>",
        )

        with patch("dotmac.platform.communications.router.get_email_service") as mock_get_service:
            with patch("dotmac.platform.communications.router.get_async_db"):
                mock_service = AsyncMock()
                mock_service.send_email.return_value = EmailResponse(
                    id="msg_rich", status="sent", message="OK", recipients_count=1
                )
                mock_get_service.return_value = mock_service

                result = await send_email_endpoint(request, current_user=None)

                # Verify the message passed to service has both bodies
                call_args = mock_service.send_email.call_args[0][0]
                assert call_args.text_body == "Plain text version"
                assert call_args.html_body == "<p>HTML version</p>"

    async def test_send_email_with_custom_from(self):
        """Test sending with custom from address."""
        request = EmailRequest(
            to=["test@example.com"],
            subject="Custom sender",
            text_body="Body",
            from_email="custom@example.com",
            from_name="Custom Sender",
        )

        with patch("dotmac.platform.communications.router.get_email_service") as mock_get_service:
            with patch("dotmac.platform.communications.router.get_async_db"):
                mock_service = AsyncMock()
                mock_service.send_email.return_value = EmailResponse(
                    id="msg_custom", status="sent", message="OK", recipients_count=1
                )
                mock_get_service.return_value = mock_service

                result = await send_email_endpoint(request, current_user=None)

                # Verify custom from was passed
                call_args = mock_service.send_email.call_args[0][0]
                assert call_args.from_email == "custom@example.com"
                assert call_args.from_name == "Custom Sender"


class TestTemplateEndpointsDirect:
    """Direct tests of template management endpoints."""

    async def test_create_template_endpoint_success(self):
        """Test creating a template via endpoint."""
        request = TemplateRequest(
            name="welcome",
            subject_template="Welcome {{ name }}",
            text_template="Hello {{ name }}",
            html_template="<p>Hello {{ name }}</p>",
        )

        with patch("dotmac.platform.communications.router.create_template") as mock_create:
            template = TemplateData(
                name="welcome",
                subject_template="Welcome {{ name }}",
                text_template="Hello {{ name }}",
                html_template="<p>Hello {{ name }}</p>",
                variables=["name"],
            )
            template.id = "tpl_123"
            template.created_at = datetime.now(timezone.utc)
            mock_create.return_value = template

            result = await create_template_endpoint(request)

            assert result.id == "tpl_123"
            assert result.name == "welcome"
            assert "name" in result.variables

    async def test_create_template_endpoint_failure(self):
        """Test template creation failure."""
        request = TemplateRequest(name="bad", subject_template="{{ invalid", text_template="Body")

        with patch("dotmac.platform.communications.router.create_template") as mock_create:
            mock_create.side_effect = ValueError("Syntax error")

            with pytest.raises(HTTPException) as exc_info:
                await create_template_endpoint(request)

            assert exc_info.value.status_code == 400

    async def test_list_templates_endpoint_success(self):
        """Test listing templates."""
        with patch(
            "dotmac.platform.communications.router.get_template_service"
        ) as mock_get_service:
            mock_service = Mock()
            template = TemplateData(
                name="test", subject_template="Subject", text_template="Body", variables=[]
            )
            template.id = "tpl_1"
            template.created_at = datetime.now(timezone.utc)
            mock_service.list_templates.return_value = [template]
            mock_get_service.return_value = mock_service

            result = await list_templates_endpoint()

            assert len(result) == 1
            assert result[0].id == "tpl_1"

    async def test_list_templates_endpoint_failure(self):
        """Test listing templates failure."""
        with patch(
            "dotmac.platform.communications.router.get_template_service"
        ) as mock_get_service:
            mock_get_service.side_effect = Exception("Service error")

            with pytest.raises(HTTPException) as exc_info:
                await list_templates_endpoint()

            assert exc_info.value.status_code == 500

    async def test_get_template_endpoint_success(self):
        """Test getting specific template."""
        with patch(
            "dotmac.platform.communications.router.get_template_service"
        ) as mock_get_service:
            mock_service = Mock()
            template = TemplateData(
                name="test", subject_template="Subject", text_template="Body", variables=[]
            )
            template.id = "tpl_abc"
            template.created_at = datetime.now(timezone.utc)
            mock_service.get_template.return_value = template
            mock_get_service.return_value = mock_service

            result = await get_template_endpoint("tpl_abc")

            assert result.id == "tpl_abc"

    async def test_get_template_endpoint_not_found(self):
        """Test getting nonexistent template."""
        with patch(
            "dotmac.platform.communications.router.get_template_service"
        ) as mock_get_service:
            mock_service = Mock()
            mock_service.get_template.return_value = None
            mock_get_service.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await get_template_endpoint("nonexistent")

            assert exc_info.value.status_code == 404

    async def test_get_template_endpoint_error(self):
        """Test get template with error."""
        with patch(
            "dotmac.platform.communications.router.get_template_service"
        ) as mock_get_service:
            mock_get_service.side_effect = Exception("Service error")

            with pytest.raises(HTTPException) as exc_info:
                await get_template_endpoint("tpl_123")

            assert exc_info.value.status_code == 500

    async def test_delete_template_endpoint_success(self):
        """Test deleting template."""
        with patch(
            "dotmac.platform.communications.router.get_template_service"
        ) as mock_get_service:
            mock_service = Mock()
            mock_service.delete_template.return_value = True
            mock_get_service.return_value = mock_service

            result = await delete_template_endpoint("tpl_123")

            assert result["message"] == "Template deleted successfully"

    async def test_delete_template_endpoint_not_found(self):
        """Test deleting nonexistent template."""
        with patch(
            "dotmac.platform.communications.router.get_template_service"
        ) as mock_get_service:
            mock_service = Mock()
            mock_service.delete_template.return_value = False
            mock_get_service.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await delete_template_endpoint("nonexistent")

            assert exc_info.value.status_code == 404

    async def test_render_template_endpoint_success(self):
        """Test rendering template."""
        request = RenderRequest(template_id="tpl_123", data={"name": "John"})

        with patch("dotmac.platform.communications.router.render_template") as mock_render:
            mock_render.return_value = RenderedTemplate(
                template_id="tpl_123",
                subject="Hello John",
                text_body="Body",
                html_body="<p>HTML</p>",
            )

            result = await render_template_endpoint(request)

            assert result.subject == "Hello John"

    async def test_render_template_endpoint_failure(self):
        """Test render template failure."""
        request = RenderRequest(template_id="tpl_123", data={})

        with patch("dotmac.platform.communications.router.render_template") as mock_render:
            mock_render.side_effect = ValueError("Missing variable")

            with pytest.raises(HTTPException) as exc_info:
                await render_template_endpoint(request)

            assert exc_info.value.status_code == 404

    async def test_quick_render_endpoint_success(self):
        """Test quick render."""
        request = QuickRenderRequest(
            subject="Hello {{ name }}",
            text_body="Body {{ name }}",
            html_body="<p>{{ name }}</p>",
            data={"name": "Alice"},
        )

        with patch("dotmac.platform.communications.router.quick_render") as mock_quick:
            mock_quick.return_value = {
                "subject": "Hello Alice",
                "text_body": "Body Alice",
                "html_body": "<p>Alice</p>",
            }

            result = await quick_render_endpoint(request)

            assert result["subject"] == "Hello Alice"

    async def test_quick_render_endpoint_failure(self):
        """Test quick render failure."""
        request = QuickRenderRequest(subject="{{ invalid", text_body="Body", data={})

        with patch("dotmac.platform.communications.router.quick_render") as mock_quick:
            mock_quick.side_effect = ValueError("Syntax error")

            with pytest.raises(HTTPException) as exc_info:
                await quick_render_endpoint(request)

            assert exc_info.value.status_code == 400


class TestUtilityEndpointsDirect:
    """Direct tests of utility endpoints."""

    async def test_health_check_endpoint_healthy(self):
        """Test health check when all services healthy."""
        with patch("dotmac.platform.communications.router.get_email_service") as mock_email:
            with patch(
                "dotmac.platform.communications.router.get_template_service"
            ) as mock_template:
                with patch("dotmac.platform.communications.router.get_task_service") as mock_task:
                    mock_email.return_value = Mock()
                    mock_template.return_value = Mock()
                    mock_task.return_value = Mock()

                    result = await health_check()

                    assert result["status"] == "healthy"
                    assert result["services"]["email_service"] == "available"
                    assert result["services"]["template_service"] == "available"
                    assert result["services"]["task_service"] == "available"

    async def test_get_task_status_endpoint_success(self):
        """Test getting task status."""
        with patch("dotmac.platform.communications.router.get_task_service") as mock_get_service:
            mock_service = Mock()
            mock_service.get_task_status.return_value = {
                "task_id": "task_123",
                "status": "SUCCESS",
                "result": {"message_id": "msg_123"},
            }
            mock_get_service.return_value = mock_service

            result = await get_task_status("task_123")

            assert result["task_id"] == "task_123"
            assert result["status"] == "SUCCESS"

    async def test_get_task_status_endpoint_failure(self):
        """Test get task status failure."""
        with patch("dotmac.platform.communications.router.get_task_service") as mock_get_service:
            mock_service = Mock()
            mock_service.get_task_status.side_effect = Exception("Task not found")
            mock_get_service.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await get_task_status("task_123")

            assert exc_info.value.status_code == 500


class TestBulkEmailEndpointsDirect:
    """Direct tests of bulk email endpoints."""

    async def test_queue_bulk_email_job_success(self):
        """Test queuing bulk email job."""
        request = BulkEmailRequest(
            job_name="test_campaign",
            messages=[
                EmailRequest(to=["user1@example.com"], subject="Test 1", text_body="Body 1"),
                EmailRequest(to=["user2@example.com"], subject="Test 2", text_body="Body 2"),
            ],
        )

        with patch("dotmac.platform.communications.router.queue_bulk_emails") as mock_queue:
            mock_queue.return_value = "job_abc123"

            result = await queue_bulk_email_job(request)

            assert result["job_id"] == "job_abc123"
            assert result["status"] == "queued"
            assert "2 messages" in result["message"]

    async def test_queue_bulk_email_job_failure(self):
        """Test bulk email job queue failure."""
        request = BulkEmailRequest(
            job_name="failed_campaign",
            messages=[EmailRequest(to=["user@example.com"], subject="Test", text_body="Body")],
        )

        with patch("dotmac.platform.communications.router.queue_bulk_emails") as mock_queue:
            mock_queue.side_effect = Exception("Queue service unavailable")

            with pytest.raises(HTTPException) as exc_info:
                await queue_bulk_email_job(request)

            assert exc_info.value.status_code == 500

    async def test_get_bulk_email_status_success(self):
        """Test getting bulk email job status."""
        with patch("dotmac.platform.communications.router.get_task_service") as mock_get_service:
            mock_service = Mock()
            mock_service.get_task_status.return_value = {
                "job_id": "job_123",
                "status": "PROGRESS",
                "progress": {"completed": 50, "total": 100},
            }
            mock_get_service.return_value = mock_service

            result = await get_bulk_email_status("job_123")

            assert result["job_id"] == "job_123"
            assert result["status"] == "PROGRESS"

    async def test_get_bulk_email_status_not_found(self):
        """Test getting status of nonexistent job."""
        with patch("dotmac.platform.communications.router.get_task_service") as mock_get_service:
            mock_service = Mock()
            mock_service.get_task_status.return_value = None
            mock_get_service.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await get_bulk_email_status("nonexistent")

            assert exc_info.value.status_code == 404

    async def test_get_bulk_email_status_error(self):
        """Test bulk email status check error."""
        with patch("dotmac.platform.communications.router.get_task_service") as mock_get_service:
            mock_service = Mock()
            mock_service.get_task_status.side_effect = Exception("Service error")
            mock_get_service.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await get_bulk_email_status("job_123")

            assert exc_info.value.status_code == 500

    async def test_cancel_bulk_email_job_success(self):
        """Test cancelling bulk email job."""
        with patch("dotmac.platform.communications.router.get_task_service") as mock_get_service:
            mock_service = Mock()
            mock_service.cancel_task.return_value = True
            mock_get_service.return_value = mock_service

            result = await cancel_bulk_email_job("job_123")

            assert result["success"] is True
            assert "cancelled successfully" in result["message"]

    async def test_cancel_bulk_email_job_cannot_cancel(self):
        """Test cancelling job that cannot be cancelled."""
        with patch("dotmac.platform.communications.router.get_task_service") as mock_get_service:
            mock_service = Mock()
            mock_service.cancel_task.return_value = False
            mock_get_service.return_value = mock_service

            result = await cancel_bulk_email_job("job_123")

            assert result["success"] is False
            assert "could not be cancelled" in result["message"]

    async def test_cancel_bulk_email_job_error(self):
        """Test cancel job error."""
        with patch("dotmac.platform.communications.router.get_task_service") as mock_get_service:
            mock_service = Mock()
            mock_service.cancel_task.side_effect = Exception("Service error")
            mock_get_service.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await cancel_bulk_email_job("job_123")

            assert exc_info.value.status_code == 500


class TestStatsActivityEndpointsDirect:
    """Direct tests of stats and activity endpoints."""

    async def test_get_communication_stats_from_db(self):
        """Test getting stats from database."""
        with patch("dotmac.platform.communications.router.get_async_db") as mock_get_db:
            with patch(
                "dotmac.platform.communications.router.get_metrics_service"
            ) as mock_get_metrics:
                mock_db = AsyncMock()
                mock_get_db.return_value.__aenter__.return_value = mock_db
                mock_get_db.return_value.__aexit__.return_value = None

                mock_metrics = AsyncMock()
                mock_metrics.get_stats.return_value = {
                    "sent": 100,
                    "delivered": 95,
                    "failed": 5,
                    "pending": 10,
                }
                mock_get_metrics.return_value = mock_metrics

                result = await get_communication_stats(current_user=None)

                assert result.sent == 100
                assert result.delivered == 95
                assert result.failed == 5
                assert result.pending == 10

    async def test_get_communication_stats_db_failure_fallback(self):
        """Test stats fallback when database fails."""
        with patch("dotmac.platform.communications.router.get_async_db") as mock_get_db:
            mock_get_db.side_effect = Exception("DB connection failed")

            result = await get_communication_stats(current_user=None)

            # Should return mock data
            assert result.sent > 0
            assert isinstance(result.sent, int)

    async def test_get_communication_stats_with_user(self):
        """Test getting stats with authenticated user."""
        mock_user = Mock()
        mock_user.tenant_id = "tenant_123"

        with patch("dotmac.platform.communications.router.get_async_db") as mock_get_db:
            with patch(
                "dotmac.platform.communications.router.get_metrics_service"
            ) as mock_get_metrics:
                mock_db = AsyncMock()
                mock_get_db.return_value.__aenter__.return_value = mock_db
                mock_get_db.return_value.__aexit__.return_value = None

                mock_metrics = AsyncMock()
                mock_metrics.get_stats.return_value = {
                    "sent": 50,
                    "delivered": 48,
                    "failed": 2,
                    "pending": 5,
                }
                mock_get_metrics.return_value = mock_metrics

                result = await get_communication_stats(current_user=mock_user)

                # Verify tenant_id was passed
                mock_metrics.get_stats.assert_called_once_with(tenant_id="tenant_123")
                assert result.sent == 50

    async def test_get_recent_activity_from_db(self):
        """Test getting activity from database."""
        with patch("dotmac.platform.communications.router.get_async_db") as mock_get_db:
            with patch(
                "dotmac.platform.communications.router.get_metrics_service"
            ) as mock_get_metrics:
                mock_db = AsyncMock()
                mock_get_db.return_value.__aenter__.return_value = mock_db
                mock_get_db.return_value.__aexit__.return_value = None

                # Create mock log entries
                mock_log = Mock()
                mock_log.id = "log_123"
                mock_log.type = Mock(value="email")
                mock_log.recipient = "user@example.com"
                mock_log.subject = "Test"
                mock_log.status = Mock(value="sent")
                mock_log.created_at = datetime.now(timezone.utc)
                mock_log.metadata_ = {}

                mock_metrics = AsyncMock()
                mock_metrics.get_recent_activity.return_value = [mock_log]
                mock_get_metrics.return_value = mock_metrics

                result = await get_recent_activity(
                    limit=10, offset=0, type_filter=None, current_user=None
                )

                assert len(result) == 1
                assert result[0].id == "log_123"
                assert result[0].type == "email"

    async def test_get_recent_activity_db_failure_fallback(self):
        """Test activity fallback when database fails."""
        with patch("dotmac.platform.communications.router.get_async_db") as mock_get_db:
            mock_get_db.side_effect = Exception("DB connection failed")

            result = await get_recent_activity(
                limit=10, offset=0, type_filter=None, current_user=None
            )

            # Should return mock data
            assert len(result) > 0
            assert hasattr(result[0], "type")

    async def test_get_recent_activity_with_filters(self):
        """Test getting activity with filters."""
        with patch("dotmac.platform.communications.router.get_async_db") as mock_get_db:
            with patch(
                "dotmac.platform.communications.router.get_metrics_service"
            ) as mock_get_metrics:
                with patch(
                    "dotmac.platform.communications.router.CommunicationType"
                ) as mock_comm_type:
                    mock_db = AsyncMock()
                    mock_get_db.return_value.__aenter__.return_value = mock_db
                    mock_get_db.return_value.__aexit__.return_value = None

                    mock_comm_type.EMAIL = Mock(value="email")

                    mock_metrics = AsyncMock()
                    mock_metrics.get_recent_activity.return_value = []
                    mock_get_metrics.return_value = mock_metrics

                    result = await get_recent_activity(
                        limit=5, offset=0, type_filter="email", current_user=None
                    )

                    # Verify filters were passed
                    mock_metrics.get_recent_activity.assert_called_once()
                    assert isinstance(result, list)

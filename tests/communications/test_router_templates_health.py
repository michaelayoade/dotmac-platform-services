"""
Tests for template and health endpoints in router.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from dotmac.platform.communications.router import (
    create_template_endpoint,
    list_templates_endpoint,
    get_template_endpoint,
    delete_template_endpoint,
    render_template_endpoint,
    quick_render_endpoint,
    TemplateRequest,
    RenderRequest,
    QuickRenderRequest,
)
from dotmac.platform.communications.template_service import TemplateData, RenderedTemplate
from fastapi import HTTPException


pytestmark = pytest.mark.asyncio


class TestTemplateEndpoints:
    """Test template management endpoints."""

    async def test_create_template_endpoint(self):
        """Test template creation."""
        request = TemplateRequest(
            name="welcome_email",
            subject_template="Welcome {{ name }}!",
            text_template="Hello {{ name }}, welcome to our service.",
            html_template="<p>Hello {{ name }}</p>"
        )

        with patch('dotmac.platform.communications.router.create_template') as mock_create:
            mock_template = TemplateData(
                name="welcome_email",
                subject_template="Welcome {{ name }}!",
                text_template="Hello {{ name }}, welcome to our service.",
                html_template="<p>Hello {{ name }}</p>",
                variables=["name"]
            )
            mock_template.id = "tpl_123"
            mock_template.created_at = datetime.now(timezone.utc)
            mock_create.return_value = mock_template

            result = await create_template_endpoint(request)

            assert result.name == "welcome_email"
            assert "name" in result.variables
            mock_create.assert_called_once()

    async def test_list_templates_endpoint(self):
        """Test listing all templates."""
        with patch('dotmac.platform.communications.router.get_template_service') as mock_get_service:
            mock_service = Mock()
            template1 = TemplateData(
                name="template1",
                subject_template="Subject 1",
                text_template="Body 1",
                variables=[]
            )
            template1.id = "tpl_1"
            template1.created_at = datetime.now(timezone.utc)

            template2 = TemplateData(
                name="template2",
                subject_template="Subject 2",
                text_template="Body 2",
                variables=[]
            )
            template2.id = "tpl_2"
            template2.created_at = datetime.now(timezone.utc)

            mock_service.list_templates.return_value = [template1, template2]
            mock_get_service.return_value = mock_service

            results = await list_templates_endpoint()

            assert len(results) == 2
            assert results[0].name == "template1"
            assert results[1].name == "template2"

    async def test_list_templates_endpoint_empty(self):
        """Test listing templates when none exist."""
        with patch('dotmac.platform.communications.router.get_template_service') as mock_get_service:
            mock_service = Mock()
            mock_service.list_templates.return_value = []
            mock_get_service.return_value = mock_service

            results = await list_templates_endpoint()

            assert len(results) == 0

    async def test_get_template_endpoint_success(self):
        """Test getting a specific template."""
        with patch('dotmac.platform.communications.router.get_template_service') as mock_get_service:
            mock_service = Mock()
            template = TemplateData(
                name="my_template",
                subject_template="Subject",
                text_template="Body",
                variables=["var1"]
            )
            template.id = "tpl_abc"
            template.created_at = datetime.now(timezone.utc)
            mock_service.get_template.return_value = template
            mock_get_service.return_value = mock_service

            result = await get_template_endpoint("tpl_abc")

            assert result.id == "tpl_abc"
            assert result.name == "my_template"

    async def test_get_template_endpoint_not_found(self):
        """Test getting non-existent template."""
        with patch('dotmac.platform.communications.router.get_template_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_template.side_effect = KeyError("Template not found")
            mock_get_service.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await get_template_endpoint("nonexistent")

            assert exc_info.value.status_code == 404

    async def test_delete_template_endpoint_success(self):
        """Test successful template deletion."""
        with patch('dotmac.platform.communications.router.get_template_service') as mock_get_service:
            mock_service = Mock()
            mock_service.delete_template.return_value = None
            mock_get_service.return_value = mock_service

            result = await delete_template_endpoint("tpl_123")

            assert result["status"] == "deleted"
            assert result["template_id"] == "tpl_123"
            mock_service.delete_template.assert_called_once_with("tpl_123")

    async def test_delete_template_endpoint_not_found(self):
        """Test deleting non-existent template."""
        with patch('dotmac.platform.communications.router.get_template_service') as mock_get_service:
            mock_service = Mock()
            mock_service.delete_template.side_effect = KeyError("Not found")
            mock_get_service.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await delete_template_endpoint("nonexistent")

            assert exc_info.value.status_code == 404

    async def test_render_template_endpoint(self):
        """Test rendering a template with variables."""
        request = RenderRequest(
            template_id="tpl_welcome",
            variables={"name": "John", "company": "Acme Corp"}
        )

        with patch('dotmac.platform.communications.router.render_template') as mock_render:
            mock_render.return_value = RenderedTemplate(
                template_id="tpl_welcome",
                subject="Welcome John!",
                text_body="Hello John, welcome to Acme Corp.",
                html_body="<p>Hello John</p>"
            )

            result = await render_template_endpoint(request)

            assert result.subject == "Welcome John!"
            assert "John" in result.text_body
            assert "Acme Corp" in result.text_body
            mock_render.assert_called_once_with("tpl_welcome", {"name": "John", "company": "Acme Corp"})

    async def test_render_template_endpoint_missing_variables(self):
        """Test rendering template with missing required variables."""
        request = RenderRequest(
            template_id="tpl_test",
            variables={}
        )

        with patch('dotmac.platform.communications.router.render_template') as mock_render:
            mock_render.side_effect = ValueError("Missing variable: name")

            with pytest.raises(HTTPException) as exc_info:
                await render_template_endpoint(request)

            assert exc_info.value.status_code == 400

    async def test_quick_render_endpoint(self):
        """Test quick rendering without saving template."""
        request = QuickRenderRequest(
            subject_template="Hello {{ name }}",
            text_template="Welcome {{ name }} to {{ app }}",
            html_template="<p>Welcome {{ name }}</p>",
            variables={"name": "Alice", "app": "MyApp"}
        )

        with patch('dotmac.platform.communications.router.quick_render') as mock_quick:
            mock_quick.return_value = RenderedTemplate(
                template_id="quick",
                subject="Hello Alice",
                text_body="Welcome Alice to MyApp",
                html_body="<p>Welcome Alice</p>"
            )

            result = await quick_render_endpoint(request)

            assert result.subject == "Hello Alice"
            assert "Alice" in result.text_body
            assert "MyApp" in result.text_body

    async def test_quick_render_endpoint_syntax_error(self):
        """Test quick render with template syntax error."""
        request = QuickRenderRequest(
            subject_template="Hello {{ name }",  # Missing closing brace
            text_template="Body",
            variables={"name": "Bob"}
        )

        with patch('dotmac.platform.communications.router.quick_render') as mock_quick:
            mock_quick.side_effect = ValueError("Template syntax error")

            with pytest.raises(HTTPException) as exc_info:
                await quick_render_endpoint(request)

            assert exc_info.value.status_code == 400


class TestHealthEndpoint:
    """Test health check endpoint."""

    async def test_health_endpoint_all_healthy(self):
        """Test health endpoint when all services are healthy."""
        from dotmac.platform.communications.router import health_check_endpoint

        with patch('dotmac.platform.communications.router.get_email_service') as mock_email:
            with patch('dotmac.platform.communications.router.get_template_service') as mock_template:
                with patch('dotmac.platform.communications.router.get_task_service') as mock_task:
                    mock_email.return_value = Mock()
                    mock_template.return_value = Mock()
                    mock_task.return_value = Mock()

                    result = await health_check_endpoint()

                    assert result["status"] == "healthy"
                    assert result["services"]["email_service"] == "available"
                    assert result["services"]["template_service"] == "available"
                    assert result["services"]["task_service"] == "available"

    async def test_health_endpoint_service_unavailable(self):
        """Test health endpoint when a service fails."""
        from dotmac.platform.communications.router import health_check_endpoint

        with patch('dotmac.platform.communications.router.get_email_service') as mock_email:
            with patch('dotmac.platform.communications.router.get_template_service') as mock_template:
                with patch('dotmac.platform.communications.router.get_task_service') as mock_task:
                    mock_email.side_effect = Exception("Email service down")
                    mock_template.return_value = Mock()
                    mock_task.return_value = Mock()

                    result = await health_check_endpoint()

                    assert result["status"] == "degraded"
                    assert "unavailable" in result["services"]["email_service"]


class TestTaskStatusEndpoint:
    """Test task status endpoint."""

    async def test_get_task_status(self):
        """Test getting task status."""
        from dotmac.platform.communications.router import get_task_status_endpoint

        with patch('dotmac.platform.communications.router.get_task_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_task_status.return_value = {
                "task_id": "task_xyz",
                "status": "SUCCESS",
                "result": {"message_id": "msg_123", "status": "sent"}
            }
            mock_get_service.return_value = mock_service

            result = await get_task_status_endpoint("task_xyz")

            assert result["task_id"] == "task_xyz"
            assert result["status"] == "SUCCESS"

    async def test_get_task_status_not_found(self):
        """Test getting status of non-existent task."""
        from dotmac.platform.communications.router import get_task_status_endpoint

        with patch('dotmac.platform.communications.router.get_task_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_task_status.side_effect = Exception("Task not found")
            mock_get_service.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await get_task_status_endpoint("nonexistent")

            assert exc_info.value.status_code == 500
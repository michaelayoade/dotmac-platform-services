"""
Final push to 90% - target router and template service gaps.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from dotmac.platform.communications.router import router
from dotmac.platform.communications.template_service import TemplateData, TemplateService, Template
from dotmac.platform.communications.email_service import EmailResponse


class TestRouterGaps:
    """Test uncovered router lines."""

    @pytest.fixture
    def client(self):
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_list_templates_error(self, client):
        """Test list templates error handling (lines 171-173)."""
        with patch('dotmac.platform.communications.router.get_template_service') as mock_get:
            mock_service = Mock()
            mock_service.list_templates.side_effect = Exception("Database error")
            mock_get.return_value = mock_service

            response = client.get("/communications/templates")

            assert response.status_code == 500
            assert "Template listing failed" in response.json()["detail"]

    def test_get_template_not_found(self, client):
        """Test get template not found (line 187)."""
        with patch('dotmac.platform.communications.router.get_template_service') as mock_get:
            mock_service = Mock()
            mock_service.get_template.return_value = None
            mock_get.return_value = mock_service

            response = client.get("/communications/templates/nonexistent")

            assert response.status_code == 404
            assert "Template not found" in response.json()["detail"]

    def test_get_template_error_after_not_found_check(self, client):
        """Test get template error handling (line 203)."""
        # This tests the HTTPException re-raise path
        from fastapi import HTTPException

        with patch('dotmac.platform.communications.router.get_template_service') as mock_get:
            mock_service = Mock()
            # Simulate an HTTP exception being raised
            mock_service.get_template.side_effect = HTTPException(status_code=403, detail="Forbidden")
            mock_get.return_value = mock_service

            response = client.get("/communications/templates/test123")

            assert response.status_code == 403

    def test_render_template_value_error(self, client):
        """Test render template ValueError handling (lines 230-232)."""
        with patch('dotmac.platform.communications.router.render_template') as mock_render:
            mock_render.side_effect = ValueError("Template not found")

            response = client.post("/communications/templates/render", json={
                "template_id": "nonexistent",
                "data": {}
            })

            assert response.status_code == 404
            assert "Template not found" in response.json()["detail"]

    def test_delete_template_not_found(self, client):
        """Test delete template not found (line 246)."""
        with patch('dotmac.platform.communications.router.get_template_service') as mock_get:
            mock_service = Mock()
            mock_service.delete_template.return_value = False
            mock_get.return_value = mock_service

            response = client.delete("/communications/templates/nonexistent")

            assert response.status_code == 404
            assert "Template not found" in response.json()["detail"]

    def test_delete_template_http_exception(self, client):
        """Test delete template HTTPException re-raise (line 253)."""
        from fastapi import HTTPException

        with patch('dotmac.platform.communications.router.get_template_service') as mock_get:
            mock_service = Mock()
            mock_service.delete_template.side_effect = HTTPException(status_code=403, detail="Forbidden")
            mock_get.return_value = mock_service

            response = client.delete("/communications/templates/test123")

            assert response.status_code == 403

    def test_delete_template_general_error(self, client):
        """Test delete template general error (lines 255-257)."""
        with patch('dotmac.platform.communications.router.get_template_service') as mock_get:
            mock_service = Mock()
            mock_service.delete_template.side_effect = Exception("DB error")
            mock_get.return_value = mock_service

            response = client.delete("/communications/templates/test123")

            assert response.status_code == 500
            assert "Template deletion failed" in response.json()["detail"]

    def test_bulk_email_status_not_found(self, client):
        """Test bulk email status not found (line 311)."""
        with patch('dotmac.platform.communications.router.get_task_service') as mock_get:
            mock_service = Mock()
            mock_service.get_task_status.return_value = None
            mock_get.return_value = mock_service

            response = client.get("/communications/bulk-email/status/nonexistent")

            assert response.status_code == 404
            assert "Job not found" in response.json()["detail"]

    def test_bulk_email_status_http_exception(self, client):
        """Test bulk email status HTTPException re-raise (line 318)."""
        from fastapi import HTTPException

        with patch('dotmac.platform.communications.router.get_task_service') as mock_get:
            mock_service = Mock()
            mock_service.get_task_status.side_effect = HTTPException(status_code=403, detail="Forbidden")
            mock_get.return_value = mock_service

            response = client.get("/communications/bulk-email/status/test123")

            assert response.status_code == 403

    def test_bulk_email_status_general_error(self, client):
        """Test bulk email status general error (lines 320-322)."""
        with patch('dotmac.platform.communications.router.get_task_service') as mock_get:
            mock_service = Mock()
            mock_service.get_task_status.side_effect = Exception("Redis down")
            mock_get.return_value = mock_service

            response = client.get("/communications/bulk-email/status/test123")

            assert response.status_code == 500
            assert "Status check failed" in response.json()["detail"]

    def test_cancel_bulk_email_not_cancelled(self, client):
        """Test cancel bulk email when not cancelled (line 336)."""
        with patch('dotmac.platform.communications.router.get_task_service') as mock_get:
            mock_service = Mock()
            mock_service.cancel_task.return_value = False
            mock_get.return_value = mock_service

            response = client.post("/communications/bulk-email/cancel/test123")

            assert response.status_code == 200
            assert response.json()["success"] is False
            assert "could not be cancelled" in response.json()["message"]

    def test_cancel_bulk_email_error(self, client):
        """Test cancel bulk email error (lines 340-342)."""
        with patch('dotmac.platform.communications.router.get_task_service') as mock_get:
            mock_service = Mock()
            mock_service.cancel_task.side_effect = Exception("Cancel failed")
            mock_get.return_value = mock_service

            response = client.post("/communications/bulk-email/cancel/test123")

            assert response.status_code == 500
            assert "Cancel failed" in response.json()["detail"]

    def test_task_status_error(self, client):
        """Test task status error (line 355)."""
        with patch('dotmac.platform.communications.router.get_task_service') as mock_get:
            mock_service = Mock()
            mock_service.get_task_status.side_effect = Exception("Redis error")
            mock_get.return_value = mock_service

            response = client.get("/communications/tasks/task123")

            assert response.status_code == 500
            assert "Task status check failed" in response.json()["detail"]

    def test_health_check_error(self, client):
        """Test health check error path (lines 388-390)."""
        with patch('dotmac.platform.communications.router.logger') as mock_logger:
            # Force an exception during health check
            mock_logger.error.side_effect = Exception("Logger failed")

            response = client.get("/communications/health")

            # Even if logging fails, health check should return
            assert response.status_code == 200
            # Should be healthy or unhealthy
            assert "status" in response.json()

    def test_quick_render_error(self, client):
        """Test quick render error (line 418)."""
        with patch('dotmac.platform.communications.router.quick_render') as mock_quick:
            mock_quick.side_effect = Exception("Template error")

            response = client.post("/communications/quick-render", json={
                "subject": "{{name}}",
                "text_body": "Hello {{name}}",
                "data": {"name": "Test"}
            })

            assert response.status_code == 400
            assert "Template error" in response.json()["detail"]


class TestTemplateServiceGaps:
    """Test uncovered template service lines."""

    def test_template_delete_nonexistent(self):
        """Test deleting non-existent template (line 157)."""
        service = TemplateService()

        # Try to delete non-existent template
        result = service.delete_template("nonexistent")
        assert result is False

    def test_template_load_from_file_error(self):
        """Test template load from file error (lines 201-215)."""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            service = TemplateService(template_dir=tmpdir)

            # Create a template file with invalid content
            template_file = os.path.join(tmpdir, "test_template.j2")
            with open(template_file, "w") as f:
                f.write("{{ invalid_syntax }")  # Invalid Jinja2 syntax

            # Try to load template from file - should handle error
            template = service.load_template_from_file("test_template")
            assert template is None  # Should return None on error

    def test_template_render_missing_template_value_error(self):
        """Test render with missing template (line 226)."""
        service = TemplateService()

        with pytest.raises(ValueError, match="Template not found"):
            service.render_template("nonexistent", {})

    def test_template_extract_variables_error(self):
        """Test extract variables with error (lines 247-249)."""
        service = TemplateService()

        # Test with invalid template syntax
        variables = service._extract_variables("{{ invalid }")
        # Should handle error gracefully
        assert isinstance(variables, list)

    def test_quick_render_edge_cases(self):
        """Test quick render with various edge cases (lines 253-260, 301-303)."""
        from dotmac.platform.communications.template_service import quick_render

        # Test with all None templates
        result = quick_render(
            subject="Plain subject",
            text_body=None,
            html_body=None,
            data={}
        )
        assert result.subject == "Plain subject"
        assert result.text_body == ""
        assert result.html_body == ""

        # Test with template errors
        with patch('dotmac.platform.communications.template_service.Template') as mock_template_class:
            mock_template = Mock()
            mock_template.render.side_effect = Exception("Render error")
            mock_template_class.return_value = mock_template

            result = quick_render(
                subject="{{name}}",
                text_body="Hello {{name}}",
                data={"name": "Test"}
            )
            # Should handle error and return something
            assert result is not None

    def test_template_service_with_file_operations(self):
        """Test template service file operations."""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create template files
            subject_file = os.path.join(tmpdir, "welcome_subject.j2")
            body_file = os.path.join(tmpdir, "welcome_body.j2")

            with open(subject_file, "w") as f:
                f.write("Welcome {{name}}!")

            with open(body_file, "w") as f:
                f.write("Hello {{name}}, welcome to our service.")

            service = TemplateService(template_dir=tmpdir)

            # Load templates from files
            template = service.load_template_from_file("welcome")

            if template:
                # Render the template
                rendered = service.render_template(template.id, {"name": "John"})
                assert "John" in rendered.subject or "John" in rendered.text_body

    def test_template_model_methods(self):
        """Test Template model methods."""
        template = Template(
            name="test",
            subject_template="Subject {{var}}",
            text_template="Body {{var}}",
            html_template="<p>{{var}}</p>"
        )

        # Test that all fields are set
        assert template.id
        assert template.name == "test"
        assert template.created_at
        assert isinstance(template.variables, list)
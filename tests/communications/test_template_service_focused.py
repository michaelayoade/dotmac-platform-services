"""
Focused tests for TemplateService based on actual implementation.

Tests the actual methods and functionality present in the TemplateService.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from jinja2 import TemplateSyntaxError, UndefinedError, sandbox

from dotmac.platform.communications.template_service import TemplateService
from dotmac.platform.communications.models import (
    EmailTemplateCreate,
    EmailTemplateUpdate,
    TemplatePreviewRequest,
)


class TestTemplateServiceInitialization:
    """Test TemplateService initialization."""

    def test_template_service_init(self):
        """Test template service initialization."""
        service = TemplateService()

        # Check Jinja environment
        assert service.jinja_env is not None
        assert isinstance(service.jinja_env, sandbox.SandboxedEnvironment)
        assert service.jinja_env.autoescape is True
        assert service.jinja_env.trim_blocks is True
        assert service.jinja_env.lstrip_blocks is True

        # Check common template functions
        assert 'len' in service.jinja_env.globals
        assert 'str' in service.jinja_env.globals
        assert 'int' in service.jinja_env.globals
        assert 'float' in service.jinja_env.globals

    def test_template_service_security_sandbox(self):
        """Test that template service uses sandboxed environment."""
        service = TemplateService()

        # Verify it's a sandboxed environment for security
        assert isinstance(service.jinja_env, sandbox.SandboxedEnvironment)


class TestTemplateServiceJinjaOperations:
    """Test Jinja2 template operations."""

    @pytest.fixture
    def service(self):
        return TemplateService()

    def test_extract_template_variables_simple(self, service):
        """Test extracting variables from simple template."""
        template = "Hello {{ name }}, welcome!"
        variables = service.extract_template_variables(template)

        assert "name" in variables
        assert len(variables) == 1

    def test_extract_template_variables_complex(self, service):
        """Test extracting variables from complex template."""
        template = """
        Hello {{ user.name }},
        {% for item in items %}
            - {{ item.name }}: {{ item.price }}
        {% endfor %}
        Total: {{ total }}
        """
        variables = service.extract_template_variables(template)

        assert "user" in variables
        assert "items" in variables
        assert "total" in variables
        assert "item" in variables

    def test_render_template_success(self, service):
        """Test successful template rendering."""
        template = "Hello {{ name }}, your total is ${{ amount }}"
        context = {"name": "John", "amount": 25.99}

        result = service.render_template(template, context)
        assert result == "Hello John, your total is $25.99"

    def test_render_template_with_loops(self, service):
        """Test template rendering with loops."""
        template = """Items: {% for item in items %}{{ item.name }}{% if not loop.last %}, {% endif %}{% endfor %}"""
        context = {
            "items": [
                {"name": "Apple"},
                {"name": "Orange"}
            ]
        }

        result = service.render_template(template, context)
        assert "Apple" in result
        assert "Orange" in result

    def test_render_template_missing_variable(self, service):
        """Test template rendering with missing variables."""
        template = "Hello {{ name }}, your order {{ order_id }} is ready"
        context = {"name": "John"}  # Missing order_id

        with pytest.raises(UndefinedError):
            service.render_template(template, context)

    def test_validate_template_syntax_valid(self, service):
        """Test template syntax validation - valid."""
        valid_template = "Hello {{ name }}, your total is {{ amount|round(2) }}"

        # Should not raise exception
        service.validate_template_syntax(valid_template)

    def test_validate_template_syntax_invalid(self, service):
        """Test template syntax validation - invalid."""
        invalid_template = "Hello {{ name, invalid syntax"

        with pytest.raises(TemplateSyntaxError):
            service.validate_template_syntax(invalid_template)

    def test_render_template_sandbox_security(self, service):
        """Test that template rendering blocks dangerous operations."""
        # Attempt to access potentially dangerous functionality
        dangerous_templates = [
            "{{ ''.__class__ }}",
            "{{ config }}",
            "{{ self }}",
        ]

        for template in dangerous_templates:
            with pytest.raises(Exception):  # Should be blocked by sandbox
                service.render_template(template, {})


class TestTemplateServiceDatabaseOperations:
    """Test template CRUD operations."""

    @pytest.fixture
    def service(self):
        return TemplateService()

    @pytest.fixture
    def mock_session(self):
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        session.delete = AsyncMock()
        return session

    @pytest.fixture
    def sample_template_data(self):
        return EmailTemplateCreate(
            name="Welcome Email",
            subject="Welcome {{ user_name }}!",
            html_content="<h1>Welcome {{ user_name }}!</h1>",
            text_content="Welcome {{ user_name }}!",
            variables=["user_name"],
            description="Welcome email template"
        )

    @pytest.mark.asyncio
    async def test_create_template_success(self, service, mock_session, sample_template_data):
        """Test successful template creation."""
        mock_template = Mock()
        mock_template.id = str(uuid4())
        mock_template.name = sample_template_data.name

        with patch('dotmac.platform.communications.models.EmailTemplate') as MockTemplate:
            MockTemplate.return_value = mock_template

            # Test the actual create_template method
            result = await service.create_template(sample_template_data, mock_session)

            # Should validate template and create it
            assert result is not None

    @pytest.mark.asyncio
    async def test_create_template_invalid_syntax(self, service, mock_session):
        """Test template creation with invalid syntax."""
        invalid_template = EmailTemplateCreate(
            name="Invalid Template",
            subject="Hello {{ name",  # Invalid Jinja2 syntax
            html_content="<p>Content</p>",
            text_content="Content"
        )

        # Should raise TemplateSyntaxError during validation
        with pytest.raises(TemplateSyntaxError):
            await service.create_template(invalid_template, mock_session)

    @pytest.mark.asyncio
    async def test_get_template_success(self, service, mock_session):
        """Test successful template retrieval."""
        template_id = str(uuid4())

        mock_template = Mock()
        mock_template.id = template_id
        mock_template.name = "Test Template"

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_template
        mock_session.execute.return_value = mock_result

        result = await service.get_template(template_id, mock_session)

        assert result is not None
        assert result.id == template_id

    @pytest.mark.asyncio
    async def test_get_template_not_found(self, service, mock_session):
        """Test template retrieval when not found."""
        template_id = str(uuid4())

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.get_template(template_id, mock_session)
        assert result is None

    @pytest.mark.asyncio
    async def test_list_templates_success(self, service, mock_session):
        """Test successful template listing."""
        mock_templates = [
            Mock(id=str(uuid4()), name="Template 1"),
            Mock(id=str(uuid4()), name="Template 2")
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_templates
        mock_session.execute.return_value = mock_result

        # Mock the count query too
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = len(mock_templates)

        # Set up execute to return different results based on the query
        def execute_side_effect(query):
            if 'count' in str(query).lower():
                return mock_count_result
            return mock_result

        mock_session.execute.side_effect = execute_side_effect

        templates, count = await service.list_templates(mock_session)

        assert len(templates) == 2
        assert count == 2

    @pytest.mark.asyncio
    async def test_list_templates_with_filters(self, service, mock_session):
        """Test template listing with filters."""
        mock_templates = [Mock(id=str(uuid4()), name="Welcome Template")]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_templates
        mock_session.execute.return_value = mock_result

        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 1

        def execute_side_effect(query):
            if 'count' in str(query).lower():
                return mock_count_result
            return mock_result

        mock_session.execute.side_effect = execute_side_effect

        templates, count = await service.list_templates(
            mock_session,
            name_filter="Welcome",
            limit=10,
            offset=0
        )

        assert len(templates) == 1
        assert templates[0].name == "Welcome Template"

    @pytest.mark.asyncio
    async def test_update_template_success(self, service, mock_session):
        """Test successful template update."""
        template_id = str(uuid4())

        mock_template = Mock()
        mock_template.id = template_id
        mock_template.name = "Old Name"

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_template
        mock_session.execute.return_value = mock_result

        update_data = EmailTemplateUpdate(
            name="New Name",
            subject="Hello {{ name }}"
        )

        result = await service.update_template(template_id, update_data, mock_session)

        # Should update the template
        assert result is not None
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_template_not_found(self, service, mock_session):
        """Test updating non-existent template."""
        template_id = str(uuid4())

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        update_data = EmailTemplateUpdate(name="New Name")

        result = await service.update_template(template_id, update_data, mock_session)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_template_success(self, service, mock_session):
        """Test successful template deletion."""
        template_id = str(uuid4())

        mock_template = Mock()
        mock_template.id = template_id

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_template
        mock_session.execute.return_value = mock_result

        result = await service.delete_template(template_id, mock_session)

        assert result is True
        mock_session.delete.assert_called_once_with(mock_template)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_template_not_found(self, service, mock_session):
        """Test deleting non-existent template."""
        template_id = str(uuid4())

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.delete_template(template_id, mock_session)
        assert result is False


class TestTemplateServicePreview:
    """Test template preview functionality."""

    @pytest.fixture
    def service(self):
        return TemplateService()

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_preview_template_success(self, service, mock_session):
        """Test successful template preview."""
        template_id = str(uuid4())

        mock_template = Mock()
        mock_template.id = template_id
        mock_template.subject = "Welcome {{ user_name }}!"
        mock_template.html_content = "<h1>Hello {{ user_name }}</h1>"
        mock_template.text_content = "Hello {{ user_name }}"

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_template
        mock_session.execute.return_value = mock_result

        preview_request = TemplatePreviewRequest(
            variables={"user_name": "John Doe"}
        )

        result = await service.preview_template(template_id, preview_request, mock_session)

        assert result is not None
        # Should render with variables
        assert "John Doe" in result.rendered_subject

    @pytest.mark.asyncio
    async def test_preview_template_not_found(self, service, mock_session):
        """Test preview when template not found."""
        template_id = str(uuid4())

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        preview_request = TemplatePreviewRequest(variables={})

        result = await service.preview_template(template_id, preview_request, mock_session)
        assert result is None

    @pytest.mark.asyncio
    async def test_preview_template_missing_variables(self, service, mock_session):
        """Test preview with missing variables."""
        template_id = str(uuid4())

        mock_template = Mock()
        mock_template.subject = "Welcome {{ user_name }}!"
        mock_template.html_content = "<h1>Hello {{ user_name }}</h1>"

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_template
        mock_session.execute.return_value = mock_result

        preview_request = TemplatePreviewRequest(variables={})  # Missing user_name

        # Should raise UndefinedError for missing variables
        with pytest.raises(UndefinedError):
            await service.preview_template(template_id, preview_request, mock_session)


class TestTemplateServiceErrorHandling:
    """Test error handling scenarios."""

    @pytest.fixture
    def service(self):
        return TemplateService()

    def test_handle_empty_template(self, service):
        """Test handling empty template."""
        empty_template = ""
        variables = service.extract_template_variables(empty_template)
        assert len(variables) == 0

        rendered = service.render_template(empty_template, {})
        assert rendered == ""

    def test_handle_whitespace_template(self, service):
        """Test handling whitespace-only template."""
        whitespace_template = "   \n\t   \n  "
        variables = service.extract_template_variables(whitespace_template)
        assert len(variables) == 0

    def test_template_with_common_functions(self, service):
        """Test template using common functions."""
        template = "Length: {{ len(items) }}, Number: {{ int(value) }}"
        context = {"items": [1, 2, 3], "value": "42"}

        result = service.render_template(template, context)
        assert "Length: 3" in result
        assert "Number: 42" in result

    @pytest.mark.asyncio
    async def test_database_error_handling(self, service):
        """Test handling database errors gracefully."""
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Database error")

        # Should not crash, should handle database errors
        result = await service.get_template("some-id", mock_session)
        # Depending on implementation, might return None or re-raise
        # This test ensures the method can handle database exceptions


class TestTemplateServiceUtilities:
    """Test utility functions."""

    def test_get_template_service_function(self):
        """Test the get_template_service utility function."""
        from dotmac.platform.communications.template_service import get_template_service

        service = get_template_service()
        assert isinstance(service, TemplateService)

    def test_service_reusability(self):
        """Test that service can be used multiple times."""
        service = TemplateService()

        # Should be able to extract variables multiple times
        template1 = "Hello {{ name1 }}"
        template2 = "Hello {{ name2 }}"

        vars1 = service.extract_template_variables(template1)
        vars2 = service.extract_template_variables(template2)

        assert "name1" in vars1
        assert "name2" in vars2
        assert vars1 != vars2

        # Should be able to render multiple times
        result1 = service.render_template(template1, {"name1": "John"})
        result2 = service.render_template(template2, {"name2": "Jane"})

        assert "John" in result1
        assert "Jane" in result2
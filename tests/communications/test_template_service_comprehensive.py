"""
Comprehensive tests for TemplateService.

Tests all template functionality including:
- Template CRUD operations
- Jinja2 rendering and validation
- Template preview with variable extraction
- Security features (sandboxed environment)
- Error handling and validation
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from jinja2 import TemplateSyntaxError, UndefinedError
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.communications.template_service import TemplateService
from dotmac.platform.communications.models import (
    EmailTemplateCreate,
    EmailTemplateUpdate,
    TemplatePreviewRequest,
)


class TestTemplateServiceInitialization:
    """Test TemplateService initialization and configuration."""

    def test_template_service_init(self):
        """Test template service initialization."""
        service = TemplateService()

        # Check Jinja environment setup
        assert service.jinja_env is not None
        assert service.jinja_env.autoescape is True
        assert service.jinja_env.trim_blocks is True
        assert service.jinja_env.lstrip_blocks is True

        # Check security: SandboxedEnvironment
        from jinja2.sandbox import SandboxedEnvironment
        assert isinstance(service.jinja_env, SandboxedEnvironment)

        # Check common functions are available
        assert 'len' in service.jinja_env.globals
        assert 'str' in service.jinja_env.globals
        assert 'int' in service.jinja_env.globals
        assert 'float' in service.jinja_env.globals


class TestTemplateServiceJinjaOperations:
    """Test Jinja2 template operations."""

    @pytest.fixture
    def service(self):
        return TemplateService()

    def test_extract_template_variables(self, service):
        """Test extracting variables from template."""
        template_content = "Hello {{ name }}, your order {{ order_id }} is {{ status }}!"
        variables = service.extract_template_variables(template_content)

        assert "name" in variables
        assert "order_id" in variables
        assert "status" in variables
        assert len(variables) == 3

    def test_extract_template_variables_with_filters(self, service):
        """Test extracting variables from template with Jinja filters."""
        template_content = "Hello {{ name|title }}, total: {{ amount|round(2) }}"
        variables = service.extract_template_variables(template_content)

        assert "name" in variables
        assert "amount" in variables

    def test_extract_template_variables_with_loops(self, service):
        """Test extracting variables from template with loops."""
        template_content = """
        Hello {{ user.name }},
        {% for item in items %}
            - {{ item.name }}: {{ item.price }}
        {% endfor %}
        Total: {{ total }}
        """
        variables = service.extract_template_variables(template_content)

        assert "user" in variables
        assert "items" in variables
        assert "total" in variables

    def test_extract_template_variables_invalid_syntax(self, service):
        """Test extracting variables from invalid template."""
        template_content = "Hello {{ name, invalid syntax"

        with pytest.raises(TemplateSyntaxError):
            service.extract_template_variables(template_content)

    def test_render_template_success(self, service):
        """Test successful template rendering."""
        template_content = "Hello {{ name }}, your total is ${{ amount }}"
        variables = {"name": "John", "amount": 25.99}

        result = service.render_template(template_content, variables)

        assert result == "Hello John, your total is $25.99"

    def test_render_template_with_filters(self, service):
        """Test template rendering with Jinja filters."""
        template_content = "Hello {{ name|title }}, total: ${{ amount|round(2) }}"
        variables = {"name": "john doe", "amount": 25.999}

        result = service.render_template(template_content, variables)

        assert result == "Hello John Doe, total: $26.0"

    def test_render_template_with_loops(self, service):
        """Test template rendering with loops."""
        template_content = """
        Items:
        {% for item in items %}
        - {{ item.name }}: ${{ item.price }}
        {% endfor %}
        """.strip()

        variables = {
            "items": [
                {"name": "Apple", "price": 1.50},
                {"name": "Orange", "price": 2.00}
            ]
        }

        result = service.render_template(template_content, variables)

        assert "- Apple: $1.5" in result
        assert "- Orange: $2.0" in result

    def test_render_template_missing_variables(self, service):
        """Test template rendering with missing variables."""
        template_content = "Hello {{ name }}, your order {{ order_id }} is ready"
        variables = {"name": "John"}  # Missing order_id

        with pytest.raises(UndefinedError):
            service.render_template(template_content, variables)

    def test_render_template_sandbox_security(self, service):
        """Test that template rendering is sandboxed for security."""
        # Attempt to access restricted functionality
        template_content = "{{ ''.__class__.__mro__[2].__subclasses__() }}"
        variables = {}

        with pytest.raises(Exception):  # Should be blocked by sandbox
            service.render_template(template_content, variables)

    def test_validate_template_syntax_valid(self, service):
        """Test template syntax validation - valid template."""
        template_content = "Hello {{ name }}, total: {{ amount|round(2) }}"

        is_valid, error = service.validate_template_syntax(template_content)

        assert is_valid is True
        assert error is None

    def test_validate_template_syntax_invalid(self, service):
        """Test template syntax validation - invalid template."""
        template_content = "Hello {{ name, invalid"

        is_valid, error = service.validate_template_syntax(template_content)

        assert is_valid is False
        assert error is not None
        assert "syntax" in error.lower()


class TestTemplateServiceDatabaseOperations:
    """Test database CRUD operations for templates."""

    @pytest.fixture
    def service(self):
        return TemplateService()

    @pytest.fixture
    def mock_session(self):
        """Mock async database session."""
        session = AsyncMock(spec=AsyncSession)
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
            html_content="<h1>Welcome {{ user_name }}!</h1><p>Thanks for joining us.</p>",
            text_content="Welcome {{ user_name }}! Thanks for joining us.",
            variables=["user_name"],
            description="Welcome email for new users"
        )

    @pytest.mark.asyncio
    async def test_create_template_success(self, service, mock_session, sample_template_data):
        """Test successful template creation."""
        # Mock database template object
        mock_template = Mock()
        mock_template.id = str(uuid4())
        mock_template.name = sample_template_data.name
        mock_template.subject = sample_template_data.subject

        with patch('dotmac.platform.communications.models.EmailTemplate') as MockTemplate:
            MockTemplate.return_value = mock_template

            result = await service.create_template(sample_template_data, mock_session)

            # Verify database operations
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once_with(mock_template)

            assert result.name == sample_template_data.name

    @pytest.mark.asyncio
    async def test_create_template_invalid_syntax(self, service, mock_session):
        """Test template creation with invalid Jinja syntax."""
        invalid_template = EmailTemplateCreate(
            name="Invalid Template",
            subject="Hello {{ name",  # Invalid syntax
            html_content="<p>Content</p>",
            text_content="Content"
        )

        with pytest.raises(TemplateSyntaxError):
            await service.create_template(invalid_template, mock_session)

        # Should not have attempted database operations
        mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_template_success(self, service, mock_session):
        """Test successful template retrieval."""
        template_id = str(uuid4())

        # Mock database query result
        mock_template = Mock()
        mock_template.id = template_id
        mock_template.name = "Test Template"
        mock_template.subject = "Hello {{ name }}"

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_template
        mock_session.execute.return_value = mock_result

        result = await service.get_template(template_id, mock_session)

        assert result is not None
        assert result.id == template_id
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_template_not_found(self, service, mock_session):
        """Test template retrieval when template doesn't exist."""
        template_id = str(uuid4())

        # Mock database query result - no template found
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.get_template(template_id, mock_session)

        assert result is None

    @pytest.mark.asyncio
    async def test_list_templates_success(self, service, mock_session):
        """Test successful template listing."""
        # Mock multiple templates
        mock_templates = [
            Mock(id=str(uuid4()), name="Template 1"),
            Mock(id=str(uuid4()), name="Template 2"),
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_templates
        mock_session.execute.return_value = mock_result

        templates, count = await service.list_templates(mock_session)

        assert len(templates) == 2
        assert count == 2
        assert templates[0].name == "Template 1"
        assert templates[1].name == "Template 2"

    @pytest.mark.asyncio
    async def test_list_templates_with_filters(self, service, mock_session):
        """Test template listing with name filter."""
        mock_templates = [Mock(id=str(uuid4()), name="Welcome Template")]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_templates
        mock_session.execute.return_value = mock_result

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

        # Mock existing template
        mock_template = Mock()
        mock_template.id = template_id
        mock_template.name = "Old Name"
        mock_template.subject = "Old Subject"

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_template
        mock_session.execute.return_value = mock_result

        update_data = EmailTemplateUpdate(
            name="New Name",
            subject="New Subject {{ name }}"
        )

        result = await service.update_template(template_id, update_data, mock_session)

        assert mock_template.name == "New Name"
        assert mock_template.subject == "New Subject {{ name }}"
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_template_invalid_syntax(self, service, mock_session):
        """Test template update with invalid syntax."""
        template_id = str(uuid4())

        mock_template = Mock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_template
        mock_session.execute.return_value = mock_result

        invalid_update = EmailTemplateUpdate(
            subject="Hello {{ name"  # Invalid syntax
        )

        with pytest.raises(TemplateSyntaxError):
            await service.update_template(template_id, invalid_update, mock_session)

        mock_session.commit.assert_not_called()

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
        """Test template deletion when template doesn't exist."""
        template_id = str(uuid4())

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.delete_template(template_id, mock_session)

        assert result is False
        mock_session.delete.assert_not_called()


class TestTemplateServicePreview:
    """Test template preview functionality."""

    @pytest.fixture
    def service(self):
        return TemplateService()

    @pytest.fixture
    def mock_session(self):
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.mark.asyncio
    async def test_preview_template_success(self, service, mock_session):
        """Test successful template preview."""
        template_id = str(uuid4())

        # Mock template from database
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

        assert result.rendered_subject == "Welcome John Doe!"
        assert result.rendered_html_content == "<h1>Hello John Doe</h1>"
        assert result.rendered_text_content == "Hello John Doe"
        assert result.template_id == template_id

    @pytest.mark.asyncio
    async def test_preview_template_missing_variables(self, service, mock_session):
        """Test template preview with missing variables."""
        template_id = str(uuid4())

        mock_template = Mock()
        mock_template.subject = "Welcome {{ user_name }}!"
        mock_template.html_content = "<h1>Hello {{ user_name }}</h1>"

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_template
        mock_session.execute.return_value = mock_result

        # Missing user_name variable
        preview_request = TemplatePreviewRequest(variables={})

        with pytest.raises(UndefinedError):
            await service.preview_template(template_id, preview_request, mock_session)

    @pytest.mark.asyncio
    async def test_preview_template_not_found(self, service, mock_session):
        """Test template preview when template doesn't exist."""
        template_id = str(uuid4())

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        preview_request = TemplatePreviewRequest(variables={})

        result = await service.preview_template(template_id, preview_request, mock_session)

        assert result is None

    @pytest.mark.asyncio
    async def test_preview_template_complex_variables(self, service, mock_session):
        """Test template preview with complex nested variables."""
        template_id = str(uuid4())

        mock_template = Mock()
        mock_template.subject = "Order {{ order.id }} for {{ customer.name }}"
        mock_template.html_content = """
        <h1>Hello {{ customer.name }}</h1>
        <p>Your order details:</p>
        <ul>
        {% for item in order.items %}
            <li>{{ item.name }}: ${{ item.price }}</li>
        {% endfor %}
        </ul>
        <p>Total: ${{ order.total }}</p>
        """

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_template
        mock_session.execute.return_value = mock_result

        preview_request = TemplatePreviewRequest(
            variables={
                "customer": {"name": "Jane Smith"},
                "order": {
                    "id": "12345",
                    "total": 29.99,
                    "items": [
                        {"name": "Coffee", "price": 4.99},
                        {"name": "Sandwich", "price": 24.99}
                    ]
                }
            }
        )

        result = await service.preview_template(template_id, preview_request, mock_session)

        assert result.rendered_subject == "Order 12345 for Jane Smith"
        assert "Hello Jane Smith" in result.rendered_html_content
        assert "Coffee: $4.99" in result.rendered_html_content
        assert "Total: $29.99" in result.rendered_html_content


class TestTemplateServiceVariableExtraction:
    """Test variable extraction and analysis."""

    @pytest.fixture
    def service(self):
        return TemplateService()

    @pytest.mark.asyncio
    async def test_get_template_variables(self, service, mock_session=None):
        """Test extracting all variables from a template."""
        if mock_session is None:
            mock_session = AsyncMock(spec=AsyncSession)

        template_id = str(uuid4())

        mock_template = Mock()
        mock_template.subject = "Hello {{ customer.name }}"
        mock_template.html_content = """
        <h1>Welcome {{ customer.name }}!</h1>
        {% for item in order.items %}
            <p>{{ item.name }}: ${{ item.price }}</p>
        {% endfor %}
        <p>Total: ${{ order.total }}</p>
        """
        mock_template.text_content = "Welcome {{ customer.name }}! Total: {{ order.total }}"

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_template
        mock_session.execute.return_value = mock_result

        variables = await service.get_template_variables(template_id, mock_session)

        # Should extract all unique variables across all template parts
        assert "customer" in variables
        assert "order" in variables
        assert "item" in variables

    def test_analyze_template_complexity(self, service):
        """Test template complexity analysis."""
        simple_template = "Hello {{ name }}"
        complex_template = """
        Hello {{ user.name }},
        {% if user.premium %}
            Premium benefits:
            {% for benefit in premium_benefits %}
                - {{ benefit.name }}: {{ benefit.description }}
            {% endfor %}
        {% else %}
            <a href="{{ upgrade_url }}">Upgrade now!</a>
        {% endif %}
        """

        simple_vars = service.extract_template_variables(simple_template)
        complex_vars = service.extract_template_variables(complex_template)

        assert len(simple_vars) == 1
        assert len(complex_vars) > 3
        assert "user" in complex_vars
        assert "premium_benefits" in complex_vars
        assert "upgrade_url" in complex_vars


class TestTemplateServiceErrorHandling:
    """Test error handling and edge cases."""

    @pytest.fixture
    def service(self):
        return TemplateService()

    def test_handle_template_with_malicious_content(self, service):
        """Test handling template with potentially malicious content."""
        malicious_templates = [
            "{{ ''.__class__.__mro__[2].__subclasses__() }}",
            "{{ config.items() }}",
            "{{ self.__dict__ }}",
        ]

        for template in malicious_templates:
            with pytest.raises(Exception):  # Should be blocked
                service.render_template(template, {})

    def test_handle_template_with_large_loops(self, service):
        """Test handling template with potentially expensive loops."""
        # This should be handled gracefully by Jinja2's sandbox
        template = """
        {% for i in range(1000000) %}
            {{ i }}
        {% endfor %}
        """

        # Should work but be resource-controlled by sandbox
        variables = service.extract_template_variables(template)
        assert "range" not in variables  # range is a built-in function

    def test_handle_empty_template(self, service):
        """Test handling empty template content."""
        empty_template = ""
        variables = service.extract_template_variables(empty_template)
        assert len(variables) == 0

        rendered = service.render_template(empty_template, {})
        assert rendered == ""

    def test_handle_whitespace_only_template(self, service):
        """Test handling template with only whitespace."""
        whitespace_template = "   \n\t   \n  "
        variables = service.extract_template_variables(whitespace_template)
        assert len(variables) == 0

        rendered = service.render_template(whitespace_template, {})
        # Due to trim_blocks=True, should be empty or minimal whitespace
        assert len(rendered.strip()) == 0
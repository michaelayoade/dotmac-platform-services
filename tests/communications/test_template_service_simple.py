"""
Simple tests for TemplateService to increase coverage.

Tests basic functionality without complex mocking.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4
from jinja2 import TemplateSyntaxError

from dotmac.platform.communications.template_service import TemplateService
from dotmac.platform.communications.models import EmailTemplateCreate


class TestTemplateServiceBasics:
    """Test basic TemplateService functionality."""

    def test_init(self):
        """Test service initialization."""
        service = TemplateService()

        assert service.jinja_env is not None
        assert service.jinja_env.autoescape is True
        assert service.jinja_env.trim_blocks is True
        assert service.jinja_env.lstrip_blocks is True

        # Check sandboxed environment
        from jinja2.sandbox import SandboxedEnvironment
        assert isinstance(service.jinja_env, SandboxedEnvironment)

        # Check common functions
        assert 'len' in service.jinja_env.globals
        assert 'str' in service.jinja_env.globals
        assert 'int' in service.jinja_env.globals

    def test_extract_template_variables(self):
        """Test variable extraction from templates."""
        service = TemplateService()

        # Test simple template
        variables = service._extract_template_variables("Hello {{ name }}")
        assert "name" in variables

        # Test multiple templates
        variables = service._extract_template_variables(
            "Subject: {{ subject }}",
            "<h1>Hello {{ name }}</h1>",
            "Hello {{ name }}, your order {{ order_id }} is ready"
        )
        assert "subject" in variables
        assert "name" in variables
        assert "order_id" in variables

        # Test complex template
        complex_template = """
        Hello {{ user.name }},
        {% for item in items %}
            - {{ item.name }}: {{ item.price }}
        {% endfor %}
        Total: {{ total }}
        """
        variables = service._extract_template_variables(complex_template)
        assert "user" in variables
        assert "items" in variables
        assert "total" in variables

    @pytest.mark.asyncio
    async def test_validate_template_syntax(self):
        """Test template syntax validation."""
        service = TemplateService()

        # Valid templates should not raise
        await service._validate_template_syntax(
            "Hello {{ name }}",
            "<h1>Welcome {{ name }}</h1>",
            "Welcome {{ name }}"
        )

        # Invalid templates should raise
        with pytest.raises(TemplateSyntaxError):
            await service._validate_template_syntax("Hello {{ name")

    def test_render_template_content(self):
        """Test template rendering."""
        service = TemplateService()

        # Simple rendering
        result = service._render_template_content(
            "Hello {{ name }}, your total is {{ amount }}",
            {"name": "John", "amount": 25.50}
        )
        assert result == "Hello John, your total is 25.5"

        # Test with filters
        result = service._render_template_content(
            "Hello {{ name|title }}, total: {{ amount|round(2) }}",
            {"name": "john doe", "amount": 25.555}
        )
        assert "John Doe" in result
        assert "25.56" in result

        # Test with loops
        result = service._render_template_content(
            "Items: {% for item in items %}{{ item }}{% if not loop.last %}, {% endif %}{% endfor %}",
            {"items": ["apple", "orange", "banana"]}
        )
        assert "apple, orange, banana" in result

    def test_render_template_missing_variable(self):
        """Test rendering with missing variables raises error."""
        service = TemplateService()

        with pytest.raises(Exception):  # UndefinedError or similar
            service._render_template_content(
                "Hello {{ name }}, your order {{ missing_var }} is ready",
                {"name": "John"}
            )

    def test_security_sandbox(self):
        """Test that template rendering is sandboxed."""
        service = TemplateService()

        # These should be blocked by the sandbox
        dangerous_templates = [
            "{{ ''.__class__ }}",
            "{{ config }}",
            "{{ self }}",
        ]

        for template in dangerous_templates:
            with pytest.raises(Exception):
                service._render_template_content(template, {})

    def test_common_functions_available(self):
        """Test that common template functions are available."""
        service = TemplateService()

        # Test len function
        result = service._render_template_content(
            "Count: {{ len(items) }}",
            {"items": [1, 2, 3]}
        )
        assert "Count: 3" in result

        # Test str function
        result = service._render_template_content(
            "Number: {{ str(value) }}",
            {"value": 42}
        )
        assert "Number: 42" in result

        # Test int function
        result = service._render_template_content(
            "Value: {{ int(text) }}",
            {"text": "123"}
        )
        assert "Value: 123" in result

    @pytest.mark.asyncio
    async def test_create_template_basic(self):
        """Test basic template creation functionality."""
        service = TemplateService()

        template_data = EmailTemplateCreate(
            name="Test Template",
            description="A test template",
            subject_template="Welcome {{ name }}!",
            html_template="<h1>Hello {{ name }}</h1>",
            text_template="Hello {{ name }}",
            category="welcome",
            is_active=True
        )

        mock_session = AsyncMock()
        mock_template = Mock()
        mock_template.id = str(uuid4())
        mock_template.name = "Test Template"

        with patch('dotmac.platform.communications.models.EmailTemplate') as MockTemplate:
            MockTemplate.return_value = mock_template

            # Should validate and create template
            result = await service._create_template(template_data, mock_session)

            assert result is not None
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_template_invalid_syntax(self):
        """Test template creation with invalid syntax."""
        service = TemplateService()

        template_data = EmailTemplateCreate(
            name="Invalid Template",
            subject_template="Hello {{ name",  # Invalid syntax
            html_template="<p>Content</p>",
            text_template="Content"
        )

        mock_session = AsyncMock()

        # Should raise TemplateSyntaxError during validation
        with pytest.raises(TemplateSyntaxError):
            await service._create_template(template_data, mock_session)

    @pytest.mark.asyncio
    async def test_get_template_found(self):
        """Test getting existing template."""
        service = TemplateService()
        template_id = str(uuid4())

        mock_template = Mock()
        mock_template.id = template_id
        mock_template.name = "Test Template"

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_template
        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        with patch('dotmac.platform.communications.models.EmailTemplateResponse') as MockResponse:
            MockResponse.model_validate.return_value = mock_template

            result = await service._get_template(template_id, mock_session)

            assert result is not None
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_template_not_found(self):
        """Test getting non-existent template."""
        service = TemplateService()
        template_id = str(uuid4())

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        result = await service._get_template(template_id, mock_session)
        assert result is None

    @pytest.mark.asyncio
    async def test_list_templates_no_filter(self):
        """Test listing templates without filters."""
        service = TemplateService()

        mock_templates = [
            Mock(id="1", name="Template 1"),
            Mock(id="2", name="Template 2")
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_templates
        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        with patch('dotmac.platform.communications.models.EmailTemplateResponse') as MockResponse:
            MockResponse.model_validate.side_effect = lambda x: x

            result = await service._list_templates(None, None, mock_session)

            assert len(result) == 2
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_templates_with_filters(self):
        """Test listing templates with filters."""
        service = TemplateService()

        mock_templates = [Mock(id="1", name="Welcome Template")]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_templates
        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        with patch('dotmac.platform.communications.models.EmailTemplateResponse') as MockResponse:
            MockResponse.model_validate.side_effect = lambda x: x

            result = await service._list_templates("welcome", True, mock_session)

            assert len(result) == 1
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_render_template_basic(self):
        """Test basic template rendering functionality."""
        service = TemplateService()

        template_id = str(uuid4())
        context = {"name": "John", "order_id": "12345"}

        mock_template = Mock()
        mock_template.subject_template = "Order {{ order_id }} for {{ name }}"
        mock_template.html_template = "<h1>Hello {{ name }}</h1><p>Order: {{ order_id }}</p>"
        mock_template.text_template = "Hello {{ name }}, your order {{ order_id }} is ready"

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_template
        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        # Test the render method exists and works
        result = await service.render_template(template_id, context, mock_session)

        assert "John" in result.subject
        assert "12345" in result.subject
        assert "John" in result.html_content
        assert "John" in result.text_content

    def test_service_utility_function(self):
        """Test the utility function for getting service instance."""
        from dotmac.platform.communications.template_service import get_template_service

        service = get_template_service()
        assert isinstance(service, TemplateService)

        # Should return same instance (singleton-like behavior)
        service2 = get_template_service()
        assert service is service2

    def test_empty_template_handling(self):
        """Test handling empty templates."""
        service = TemplateService()

        # Empty template should work
        variables = service._extract_template_variables("")
        assert len(variables) == 0

        result = service._render_template_content("", {})
        assert result == ""

    def test_whitespace_template_handling(self):
        """Test handling whitespace-only templates."""
        service = TemplateService()

        whitespace_template = "   \n\t   \n  "
        variables = service._extract_template_variables(whitespace_template)
        assert len(variables) == 0

        # Should handle whitespace gracefully
        result = service._render_template_content(whitespace_template, {})
        # Due to trim_blocks and lstrip_blocks, might be empty or minimal
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_validation_with_multiple_templates(self):
        """Test validation works with multiple template parts."""
        service = TemplateService()

        # All valid should pass
        await service._validate_template_syntax(
            "Subject: {{ title }}",
            "<html><body>{{ content }}</body></html>",
            "Text content: {{ content }}"
        )

        # Any invalid should fail
        with pytest.raises(TemplateSyntaxError):
            await service._validate_template_syntax(
                "Subject: {{ title }}",  # Valid
                "<html><body>{{ content }}</body></html>",  # Valid
                "Text content: {{ invalid"  # Invalid
            )

    def test_variable_extraction_edge_cases(self):
        """Test variable extraction edge cases."""
        service = TemplateService()

        # No variables
        variables = service._extract_template_variables("Plain text")
        assert len(variables) == 0

        # Nested attributes
        variables = service._extract_template_variables("{{ user.profile.name }}")
        assert "user" in variables

        # Loop variables
        variables = service._extract_template_variables(
            "{% for item in items %}{{ item.name }}{% endfor %}"
        )
        assert "items" in variables
        assert "item" in variables

        # Conditional variables
        variables = service._extract_template_variables(
            "{% if user.is_premium %}{{ premium_content }}{% endif %}"
        )
        assert "user" in variables
        assert "premium_content" in variables
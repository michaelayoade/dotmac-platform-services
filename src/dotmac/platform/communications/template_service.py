"""
Template service using Jinja2.

Provides template functionality using Jinja2.
"""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import structlog
from jinja2 import (
    Environment,
    FileSystemLoader,
    DictLoader,
    Template,
    TemplateSyntaxError,
    UndefinedError,
    select_autoescape,
    meta
)
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class TemplateData(BaseModel):
    """Template data model."""

    id: str = Field(default_factory=lambda: f"tpl_{uuid4().hex[:8]}")
    name: str = Field(..., min_length=1, description="Template name")
    subject_template: str = Field(..., description="Subject template")
    text_template: Optional[str] = Field(None, description="Text body template")
    html_template: Optional[str] = Field(None, description="HTML body template")
    variables: List[str] = Field(default_factory=list, description="Template variables")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "str_strip_whitespace": True,
        "validate_assignment": True,
        "extra": "forbid"
    }


class RenderedTemplate(BaseModel):
    """Rendered template result."""

    template_id: str = Field(..., description="Template ID")
    subject: str = Field(..., description="Rendered subject")
    text_body: Optional[str] = Field(None, description="Rendered text body")
    html_body: Optional[str] = Field(None, description="Rendered HTML body")
    variables_used: List[str] = Field(default_factory=list, description="Variables found in template")
    missing_variables: List[str] = Field(default_factory=list, description="Missing variables")
    rendered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TemplateService:
    """Template service using Jinja2."""

    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize template service.

        Args:
            template_dir: Directory for file-based templates (optional)
        """
        self.template_dir = template_dir
        self.templates: Dict[str, TemplateData] = {}

        # Create Jinja2 environments
        if template_dir and os.path.exists(template_dir):
            # File-based loader for templates stored as files
            self.file_env = Environment(
                loader=FileSystemLoader(template_dir),
                autoescape=select_autoescape(['html', 'xml']),
                trim_blocks=True,
                lstrip_blocks=True
            )
            logger.info("File-based template environment created", template_dir=template_dir)
        else:
            self.file_env = None

        # Dictionary-based loader for in-memory templates
        self.dict_env = Environment(
            loader=DictLoader({}),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Add useful globals
        self._add_template_globals()

        logger.info("Template service initialized")

    def _add_template_globals(self):
        """Add common functions and variables to templates."""
        common_globals = {
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'now': lambda: datetime.now(timezone.utc),
            'today': lambda: datetime.now(timezone.utc).date(),
        }

        self.dict_env.globals.update(common_globals)
        if self.file_env:
            self.file_env.globals.update(common_globals)

    def create_template(self, template_data: TemplateData) -> TemplateData:
        """Create a new template."""
        try:
            # Validate template syntax
            self._validate_template_syntax(template_data)

            # Extract variables
            variables = self._extract_variables(template_data)
            template_data.variables = variables

            # Store template
            self.templates[template_data.id] = template_data

            logger.info(
                "Template created",
                template_id=template_data.id,
                name=template_data.name,
                variables_count=len(variables)
            )

            return template_data

        except Exception as e:
            logger.error(
                "Failed to create template",
                name=template_data.name,
                error=str(e)
            )
            raise

    def get_template(self, template_id: str) -> Optional[TemplateData]:
        """Get a template by ID."""
        return self.templates.get(template_id)

    def list_templates(self) -> List[TemplateData]:
        """List all templates."""
        return list(self.templates.values())

    def delete_template(self, template_id: str) -> bool:
        """Delete a template."""
        if template_id in self.templates:
            del self.templates[template_id]
            logger.info("Template deleted", template_id=template_id)
            return True
        return False

    def render_template(
        self,
        template_id: str,
        data: Dict[str, Any]
    ) -> RenderedTemplate:
        """Render a template with data."""
        template_data = self.get_template(template_id)
        if not template_data:
            raise ValueError(f"Template not found: {template_id}")

        try:
            # Create templates
            subject_tpl = self.dict_env.from_string(template_data.subject_template)
            text_tpl = self.dict_env.from_string(template_data.text_template) if template_data.text_template else None
            html_tpl = self.dict_env.from_string(template_data.html_template) if template_data.html_template else None

            # Render
            subject = subject_tpl.render(data)
            text_body = text_tpl.render(data) if text_tpl else None
            html_body = html_tpl.render(data) if html_tpl else None

            # Check for missing variables
            missing_vars = self._find_missing_variables(template_data, data)

            result = RenderedTemplate(
                template_id=template_id,
                subject=subject,
                text_body=text_body,
                html_body=html_body,
                variables_used=template_data.variables,
                missing_variables=missing_vars
            )

            logger.info(
                "Template rendered",
                template_id=template_id,
                variables_used=len(template_data.variables),
                missing_variables=len(missing_vars)
            )

            return result

        except UndefinedError as e:
            logger.error(
                "Template rendering failed - undefined variable",
                template_id=template_id,
                error=str(e)
            )
            raise ValueError(f"Template variable undefined: {str(e)}")

        except Exception as e:
            logger.error(
                "Template rendering failed",
                template_id=template_id,
                error=str(e)
            )
            raise

    def render_string_template(
        self,
        subject_template: str,
        text_template: Optional[str] = None,
        html_template: Optional[str] = None,
        data: Dict[str, Any] = None
    ) -> Dict[str, str]:
        """Render templates from strings directly."""
        if data is None:
            data = {}

        try:
            result = {}

            # Render subject
            subject_tpl = self.dict_env.from_string(subject_template)
            result['subject'] = subject_tpl.render(data)

            # Render text body
            if text_template:
                text_tpl = self.dict_env.from_string(text_template)
                result['text_body'] = text_tpl.render(data)

            # Render HTML body
            if html_template:
                html_tpl = self.dict_env.from_string(html_template)
                result['html_body'] = html_tpl.render(data)

            return result

        except Exception as e:
            logger.error("String template rendering failed", error=str(e))
            raise ValueError(f"Template rendering error: {str(e)}")

    def load_file_template(self, filename: str) -> Optional[Template]:
        """Load a template from file (if file loader is available)."""
        if not self.file_env:
            raise ValueError("File-based templates not configured")

        try:
            return self.file_env.get_template(filename)
        except Exception as e:
            logger.error("Failed to load file template", filename=filename, error=str(e))
            return None

    def _validate_template_syntax(self, template_data: TemplateData) -> None:
        """Validate Jinja2 template syntax."""
        templates_to_check = [
            ("subject", template_data.subject_template),
        ]

        if template_data.text_template:
            templates_to_check.append(("text", template_data.text_template))

        if template_data.html_template:
            templates_to_check.append(("html", template_data.html_template))

        for template_type, template_content in templates_to_check:
            try:
                self.dict_env.parse(template_content)
            except TemplateSyntaxError as e:
                logger.error(
                    "Template syntax error",
                    template_type=template_type,
                    error=str(e),
                    line=e.lineno
                )
                raise ValueError(f"Syntax error in {template_type} template: {str(e)}")

    def _extract_variables(self, template_data: TemplateData) -> List[str]:
        """Extract all variables from templates."""
        all_variables = set()

        templates_to_check = [template_data.subject_template]
        if template_data.text_template:
            templates_to_check.append(template_data.text_template)
        if template_data.html_template:
            templates_to_check.append(template_data.html_template)

        for template_content in templates_to_check:
            try:
                ast = self.dict_env.parse(template_content)
                variables = meta.find_undeclared_variables(ast)
                all_variables.update(variables)
            except TemplateSyntaxError:
                # Skip templates with syntax errors
                pass

        return sorted(list(all_variables))

    def _find_missing_variables(
        self,
        template_data: TemplateData,
        data: Dict[str, Any]
    ) -> List[str]:
        """Find variables that are used in template but not provided in data."""
        return [var for var in template_data.variables if var not in data]


# Global service instance
_template_service: Optional[TemplateService] = None


def get_template_service(template_dir: Optional[str] = None) -> TemplateService:
    """Get or create the global template service."""
    global _template_service
    if _template_service is None:
        _template_service = TemplateService(template_dir)
    return _template_service


# Convenience functions
def create_template(
    name: str,
    subject_template: str,
    text_template: Optional[str] = None,
    html_template: Optional[str] = None
) -> TemplateData:
    """Create a simple template."""
    service = get_template_service()
    template_data = TemplateData(
        name=name,
        subject_template=subject_template,
        text_template=text_template,
        html_template=html_template
    )
    return service.create_template(template_data)


def render_template(
    template_id: str,
    data: Dict[str, Any]
) -> RenderedTemplate:
    """Render a template by ID."""
    service = get_template_service()
    return service.render_template(template_id, data)


def quick_render(
    subject: str,
    text_body: Optional[str] = None,
    html_body: Optional[str] = None,
    data: Dict[str, Any] = None
) -> Dict[str, str]:
    """Quickly render templates from strings."""
    service = get_template_service()
    return service.render_string_template(subject, text_body, html_body, data or {})
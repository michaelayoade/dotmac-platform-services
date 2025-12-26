"""
Template service using Jinja2.

Provides template functionality using Jinja2 with tenant-aware template resolution.
Supports file-based templates with database overrides for tenant customization.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import structlog
from jinja2 import (
    DictLoader,
    Environment,
    FileSystemLoader,
    Template,
    TemplateNotFound,
    TemplateSyntaxError,
    UndefinedError,
    meta,
)
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


# Default template directory relative to this module
DEFAULT_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def _autoescape_for_template_name(template_name: str | None) -> bool:
    """Determine autoescape behavior based on the template filename."""
    if not template_name:
        return False
    name = template_name.lower()
    if name.endswith(".html") or name.endswith(".xml"):
        return True
    if name.endswith(".html.j2") or name.endswith(".xml.j2"):
        return True
    return False


@dataclass
class TemplateBundle:
    """Container for a complete template set (subject, HTML, text)."""

    subject_template: str
    html_template: str | None = None
    text_template: str | None = None
    source: str = "file"  # "file" or "database"
    tenant_id: str | None = None
    template_key: str = ""
    variables: list[str] = field(default_factory=list)


@dataclass
class RenderedEmail:
    """Rendered email content ready for sending."""

    subject: str
    html_body: str | None = None
    text_body: str | None = None
    template_key: str = ""
    tenant_id: str | None = None
    variables_used: dict[str, Any] = field(default_factory=dict)
    rendered_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class BrandingConfig:
    """Tenant branding configuration for templates."""

    product_name: str = "DotMac Platform"
    company_name: str | None = None
    support_email: str | None = None
    primary_color: str = "#0070f3"
    primary_color_hover: str = "#0060d0"
    secondary_color: str = "#6b7280"
    accent_color: str = "#10b981"
    logo_url: str | None = None
    logo_dark_url: str | None = None
    docs_url: str | None = None
    support_portal_url: str | None = None
    address: str | None = None


class TemplateData(BaseModel):  # BaseModel resolves to Any in isolation
    """Template data model."""

    id: str = Field(default_factory=lambda: f"tpl_{uuid4().hex[:8]}")
    name: str = Field(..., min_length=1, description="Template name")
    subject_template: str = Field(..., description="Subject template")
    text_template: str | None = Field(None, description="Text body template")
    html_template: str | None = Field(None, description="HTML body template")
    variables: list[str] = Field(default_factory=list, description="Template variables")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")


class RenderedTemplate(BaseModel):  # BaseModel resolves to Any in isolation
    """Rendered template result."""

    model_config = ConfigDict()

    template_id: str = Field(..., description="Template ID")
    subject: str = Field(..., description="Rendered subject")
    text_body: str | None = Field(None, description="Rendered text body")
    html_body: str | None = Field(None, description="Rendered HTML body")
    variables_used: list[str] = Field(
        default_factory=list, description="Variables found in template"
    )
    missing_variables: list[str] = Field(default_factory=list, description="Missing variables")
    rendered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TemplateService:
    """Template service using Jinja2."""

    def __init__(self, template_dir: str | None = None) -> None:
        """
        Initialize template service.

        Args:
            template_dir: Directory for file-based templates (optional)
        """
        self.template_dir = template_dir
        self.templates: dict[str, TemplateData] = {}

        # Create Jinja2 environments
        self.file_env: Environment | None
        if template_dir and os.path.exists(template_dir):
            # File-based loader for templates stored as files
            self.file_env = Environment(
                loader=FileSystemLoader(template_dir),
                autoescape=_autoescape_for_template_name,
                trim_blocks=True,
                lstrip_blocks=True,
            )
            logger.info("File-based template environment created", template_dir=template_dir)
        else:
            self.file_env = None

        # Dictionary-based loader for in-memory templates
        self.dict_env = Environment(
            loader=DictLoader({}),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.dict_env_html = Environment(
            loader=DictLoader({}),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add useful globals
        self._add_template_globals()

        logger.info("Template service initialized")

    def _add_template_globals(self) -> None:
        """Add common functions and variables to templates."""
        common_globals = {
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "now": lambda: datetime.now(UTC),
            "today": lambda: datetime.now(UTC).date(),
        }

        self.dict_env.globals.update(common_globals)
        self.dict_env_html.globals.update(common_globals)
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
                variables_count=len(variables),
            )

            return template_data

        except (TemplateSyntaxError, UndefinedError, ValueError) as exc:
            logger.error("Failed to create template", name=template_data.name, error=str(exc))
            raise

    def get_template(self, template_id: str) -> TemplateData | None:
        """Get a template by ID."""
        return self.templates.get(template_id)

    def list_templates(self) -> list[TemplateData]:
        """List all templates."""
        return list(self.templates.values())

    def delete_template(self, template_id: str) -> bool:
        """Delete a template."""
        if template_id in self.templates:
            del self.templates[template_id]
            logger.info("Template deleted", template_id=template_id)
            return True
        return False

    def render_template(self, template_id: str, data: Mapping[str, Any]) -> RenderedTemplate:
        """Render a template with data."""
        template_data = self.get_template(template_id)
        if not template_data:
            raise ValueError(f"Template not found: {template_id}")

        try:
            # Create templates
            subject_tpl = self.dict_env.from_string(template_data.subject_template)
            text_tpl = (
                self.dict_env.from_string(template_data.text_template)
                if template_data.text_template
                else None
            )
            html_tpl = (
                self.dict_env_html.from_string(template_data.html_template)
                if template_data.html_template
                else None
            )

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
                missing_variables=missing_vars,
            )

            logger.info(
                "Template rendered",
                template_id=template_id,
                variables_used=len(template_data.variables),
                missing_variables=len(missing_vars),
            )

            return result

        except UndefinedError as e:
            logger.error(
                "Template rendering failed - undefined variable",
                template_id=template_id,
                error=str(e),
            )
            raise ValueError(f"Template variable undefined: {str(e)}")

        except (TemplateSyntaxError, TypeError) as exc:
            logger.error("Template rendering failed", template_id=template_id, error=str(exc))
            raise ValueError(f"Template rendering error: {str(exc)}")

    def render_string_template(
        self,
        subject_template: str,
        text_template: str | None = None,
        html_template: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        """Render templates from strings directly."""
        if data is None:
            data = {}

        try:
            result = {}

            # Render subject
            subject_tpl = self.dict_env.from_string(subject_template)
            result["subject"] = subject_tpl.render(data)

            # Render text body
            if text_template:
                text_tpl = self.dict_env.from_string(text_template)
                result["text_body"] = text_tpl.render(data)

            # Render HTML body
            if html_template:
                html_tpl = self.dict_env_html.from_string(html_template)
                result["html_body"] = html_tpl.render(data)

            return result

        except (TemplateSyntaxError, UndefinedError, TypeError) as exc:
            logger.error("String template rendering failed", error=str(exc))
            raise ValueError(f"Template rendering error: {str(exc)}")

    def render_inline(
        self,
        template_str: str,
        data: Mapping[str, Any] | None = None,
        *,
        autoescape: bool = False,
    ) -> str:
        """Render a single template string."""
        context = dict(data or {})
        try:
            env = self.dict_env_html if autoescape else self.dict_env
            template = env.from_string(template_str)
            return template.render(context)
        except (TemplateSyntaxError, UndefinedError, TypeError) as exc:
            logger.error("Inline template rendering failed", error=str(exc))
            raise ValueError(f"Template rendering error: {str(exc)}")

    def load_file_template(self, filename: str) -> Template | None:
        """Load a template from file (if file loader is available)."""
        if not self.file_env:
            raise ValueError("File-based templates not configured")

        try:
            return self.file_env.get_template(filename)
        except TemplateSyntaxError as exc:
            logger.error("Failed to load file template", filename=filename, error=str(exc))
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
                    line=e.lineno,
                )
                raise ValueError(f"Syntax error in {template_type} template: {str(e)}")

    def _extract_variables(self, template_data: TemplateData) -> list[str]:
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

        return sorted(all_variables)

    def _find_missing_variables(
        self, template_data: TemplateData, data: Mapping[str, Any]
    ) -> list[str]:
        """Find variables that are used in template but not provided in data."""
        return [var for var in template_data.variables if var not in data]


# Global service instance
_template_service: TemplateService | None = None


def get_template_service(template_dir: str | None = None) -> TemplateService:
    """Get or create the global template service."""
    global _template_service
    if _template_service is None:
        _template_service = TemplateService(template_dir)
    return _template_service


# Convenience functions
def create_template(
    name: str,
    subject_template: str,
    text_template: str | None = None,
    html_template: str | None = None,
) -> TemplateData:
    """Create a simple template."""
    service = get_template_service()
    template_data = TemplateData(
        name=name,
        subject_template=subject_template,
        text_template=text_template,
        html_template=html_template,
    )
    return service.create_template(template_data)


def render_template(template_id: str, data: dict[str, Any]) -> RenderedTemplate:
    """Render a template by ID."""
    service = get_template_service()
    return service.render_template(template_id, data)


def quick_render(
    subject: str,
    text_body: str | None = None,
    html_body: str | None = None,
    data: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Quickly render templates from strings."""
    service = get_template_service()
    return service.render_string_template(subject, text_body, html_body, data or {})


class TenantAwareTemplateService:
    """
    Enhanced template service with tenant-specific override support.

    Resolution order:
    1. Check CommunicationTemplate table for tenant-specific template
    2. Fall back to file-based default template

    Template keys follow the pattern: email.{category}.{template_name}
    Example: email.auth.welcome, email.billing.payment_succeeded
    """

    def __init__(
        self,
        template_dir: str | Path | None = None,
    ) -> None:
        """
        Initialize tenant-aware template service.

        Args:
            template_dir: Directory for file-based templates. Defaults to
                         src/dotmac/platform/templates/
        """
        self.template_dir = Path(template_dir) if template_dir else DEFAULT_TEMPLATE_DIR

        # Create Jinja2 environment with file loader
        if self.template_dir.exists():
            self.env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=_autoescape_for_template_name,
                trim_blocks=True,
                lstrip_blocks=True,
            )
            logger.info(
                "Tenant-aware template service initialized",
                template_dir=str(self.template_dir),
            )
        else:
            # Fallback to dict loader if no template directory
            self.env = Environment(
                loader=DictLoader({}),
                autoescape=_autoescape_for_template_name,
                trim_blocks=True,
                lstrip_blocks=True,
            )
            logger.warning(
                "Template directory not found, using in-memory templates",
                template_dir=str(self.template_dir),
            )

        # String-based environment for database templates
        self.string_env_text = Environment(
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.string_env_html = Environment(
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        # Backwards compatibility alias for older tests and helpers.
        self.string_env = self.string_env_text

        self._add_template_globals()
        self._add_custom_filters()

    def _add_template_globals(self) -> None:
        """Add common functions and variables to templates."""
        common_globals = {
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "now": lambda: datetime.now(UTC),
            "today": lambda: datetime.now(UTC).date(),
        }

        self.env.globals.update(common_globals)
        self.string_env_text.globals.update(common_globals)
        self.string_env_html.globals.update(common_globals)

    def _add_custom_filters(self) -> None:
        """Add custom Jinja2 filters for email formatting."""
        filters = {
            "format_currency": self._format_currency,
            "format_date": self._format_date,
            "format_datetime": self._format_datetime,
            "default_if_none": lambda v, d="": d if v is None else v,
        }
        self.env.filters.update(filters)
        self.string_env_text.filters.update(filters)
        self.string_env_html.filters.update(filters)

    @staticmethod
    def _format_currency(
        amount: float | int,
        currency: str = "USD",
        locale: str = "en_US",
    ) -> str:
        """Format amount as currency string."""
        try:
            from decimal import Decimal

            from babel.numbers import format_currency as babel_format_currency
            from babel.numbers import get_currency_precision

            precision = get_currency_precision(currency)
            if isinstance(amount, int):
                divisor = Decimal(10**precision)
                decimal_amount = Decimal(amount) / divisor
            else:
                decimal_amount = Decimal(str(amount))
            return babel_format_currency(decimal_amount, currency, locale=locale)
        except Exception:
            # Fallback: assume minor units for integers, major units for floats.
            normalized_amount = amount / 100 if isinstance(amount, int) else amount
            symbols = {"USD": "$", "EUR": "€", "GBP": "£", "NGN": "₦"}
            symbol = symbols.get(currency, currency + " ")
            return f"{symbol}{normalized_amount:,.2f}"

    @staticmethod
    def _format_date(dt: datetime | None, format_str: str = "%B %d, %Y") -> str:
        """Format datetime as date string."""
        if dt is None:
            return ""
        if isinstance(dt, str):
            return dt
        return dt.strftime(format_str)

    @staticmethod
    def _format_datetime(
        dt: datetime | None,
        format_str: str = "%B %d, %Y at %I:%M %p",
    ) -> str:
        """Format datetime as datetime string."""
        if dt is None:
            return ""
        if isinstance(dt, str):
            return dt
        return dt.strftime(format_str)

    def _template_key_to_path(self, template_key: str, extension: str) -> str:
        """
        Convert template key to file path.

        email.auth.welcome -> email/auth/welcome.html.j2
        """
        parts = template_key.split(".")
        return "/".join(parts) + f".{extension}.j2"

    async def get_template(
        self,
        template_key: str,
        tenant_id: str | None = None,
        db: AsyncSession | None = None,
    ) -> TemplateBundle:
        """
        Resolve template with tenant fallback.

        Args:
            template_key: Template identifier (e.g., "email.billing.payment_succeeded")
            tenant_id: Optional tenant ID for override lookup
            db: Database session for tenant template lookup

        Returns:
            TemplateBundle containing subject, html, and text templates
        """
        # 1. Try tenant-specific override from database
        if tenant_id and db:
            db_template = await self._get_db_template(template_key, tenant_id, db)
            if db_template:
                return db_template

        # 2. Fall back to file-based template
        return self._get_file_template(template_key)

    async def _get_db_template(
        self,
        template_key: str,
        tenant_id: str,
        db: AsyncSession,
    ) -> TemplateBundle | None:
        """
        Look up tenant-specific template from database.

        Args:
            template_key: Template identifier
            tenant_id: Tenant ID
            db: Database session

        Returns:
            TemplateBundle if found, None otherwise
        """
        from sqlalchemy import select

        from .models import CommunicationTemplate

        try:
            stmt = select(CommunicationTemplate).where(
                CommunicationTemplate.template_key == template_key,
                CommunicationTemplate.tenant_id == tenant_id,
                CommunicationTemplate.is_active == True,  # noqa: E712
            )
            result = await db.execute(stmt)
            template = result.scalar_one_or_none()

            if not template:
                stmt = select(CommunicationTemplate).where(
                    CommunicationTemplate.name == template_key,
                    CommunicationTemplate.tenant_id == tenant_id,
                    CommunicationTemplate.is_active == True,  # noqa: E712
                )
                result = await db.execute(stmt)
                template = result.scalar_one_or_none()

            if template:
                logger.debug(
                    "Found tenant template override",
                    template_key=template_key,
                    tenant_id=tenant_id,
                )
                return TemplateBundle(
                    subject_template=template.subject_template or "",
                    html_template=template.html_template,
                    text_template=template.text_template,
                    source="database",
                    tenant_id=tenant_id,
                    template_key=template_key,
                    variables=template.variables or [],
                )

        except Exception as e:
            logger.warning(
                "Failed to query tenant template",
                template_key=template_key,
                tenant_id=tenant_id,
                error=str(e),
            )

        return None

    def _get_file_template(self, template_key: str) -> TemplateBundle:
        """
        Load template from file system.

        Args:
            template_key: Template identifier

        Returns:
            TemplateBundle with templates loaded from files
        """
        subject_path = self._template_key_to_path(template_key, "subject")
        html_path = self._template_key_to_path(template_key, "html")
        text_path = self._template_key_to_path(template_key, "txt")

        subject_template = ""
        html_template = None
        text_template = None

        loader = self.env.loader
        if loader is None:
            raise ValueError("Template loader is not configured.")

        # Load subject template
        try:
            # For subject, we just get the source
            subject_template = loader.get_source(self.env, subject_path)[0]
        except TemplateNotFound:
            # Try to extract subject from HTML template metadata or use default
            logger.debug("Subject template not found", path=subject_path)

        # Load HTML template
        try:
            html_template = loader.get_source(self.env, html_path)[0]
        except TemplateNotFound:
            logger.debug("HTML template not found", path=html_path)

        # Load text template
        try:
            text_template = loader.get_source(self.env, text_path)[0]
        except TemplateNotFound:
            logger.debug("Text template not found", path=text_path)

        if not html_template and not text_template:
            raise ValueError(f"No template files found for key: {template_key}")

        return TemplateBundle(
            subject_template=subject_template,
            html_template=html_template,
            text_template=text_template,
            source="file",
            template_key=template_key,
        )

    def _build_full_context(
        self,
        context: dict[str, Any],
        branding: BrandingConfig | None = None,
    ) -> dict[str, Any]:
        """
        Build full context with branding and common variables.

        Args:
            context: User-provided template variables
            branding: Tenant branding configuration

        Returns:
            Complete context dictionary for template rendering
        """
        branding = branding or BrandingConfig()

        full_context = {
            "branding": {
                "product_name": branding.product_name,
                "company_name": branding.company_name or branding.product_name,
                "support_email": branding.support_email,
                "primary_color": branding.primary_color,
                "primary_color_hover": branding.primary_color_hover,
                "secondary_color": branding.secondary_color,
                "accent_color": branding.accent_color,
                "logo_url": branding.logo_url,
                "logo_dark_url": branding.logo_dark_url,
                "docs_url": branding.docs_url,
                "support_portal_url": branding.support_portal_url,
                "address": branding.address,
            },
            "current_year": datetime.now(UTC).year,
        }

        # Merge user context (user context takes precedence)
        full_context.update(context)

        return full_context

    def _render_string(
        self,
        template_str: str,
        context: dict[str, Any],
        *,
        autoescape: bool,
    ) -> str:
        """Render a template string with context."""
        try:
            env = self.string_env_html if autoescape else self.string_env_text
            tpl = env.from_string(template_str)
            return tpl.render(context)
        except (TemplateSyntaxError, UndefinedError) as e:
            logger.error("Template rendering failed", error=str(e))
            raise ValueError(f"Template rendering error: {e}")

    def render_file_template(
        self,
        template_path: str,
        context: dict[str, Any],
        branding: BrandingConfig | None = None,
    ) -> str:
        """
        Render a file-based template.

        Args:
            template_path: Path to template file (e.g., "email/auth/welcome.html.j2")
            context: Template variables
            branding: Optional branding configuration

        Returns:
            Rendered template string
        """
        full_context = self._build_full_context(context, branding)

        try:
            template = self.env.get_template(template_path)
            return template.render(full_context)
        except TemplateNotFound:
            raise ValueError(f"Template not found: {template_path}")
        except (TemplateSyntaxError, UndefinedError) as e:
            logger.error("Template rendering failed", path=template_path, error=str(e))
            raise ValueError(f"Template rendering error: {e}")

    async def render_email(
        self,
        template_key: str,
        context: dict[str, Any],
        tenant_id: str | None = None,
        branding: BrandingConfig | None = None,
        db: AsyncSession | None = None,
    ) -> RenderedEmail:
        """
        Render an email template with full context.

        Args:
            template_key: Template identifier (e.g., "email.billing.payment_succeeded")
            context: Template variables
            tenant_id: Optional tenant for override lookup
            branding: Tenant branding configuration for styling
            db: Database session for tenant template lookup

        Returns:
            RenderedEmail with subject, HTML, and text content
        """
        # Get template bundle (with tenant override resolution)
        bundle = await self.get_template(template_key, tenant_id, db)

        # Build full context with branding
        full_context = self._build_full_context(context, branding)

        # Render each component
        subject = ""
        if bundle.subject_template:
            subject = self._render_string(
                bundle.subject_template,
                full_context,
                autoescape=False,
            )

        html_body = None
        if bundle.html_template:
            if bundle.source == "file":
                # For file templates, use the environment to support extends/includes
                html_path = self._template_key_to_path(template_key, "html")
                try:
                    template = self.env.get_template(html_path)
                    html_body = template.render(full_context)
                except TemplateNotFound:
                    html_body = self._render_string(
                        bundle.html_template,
                        full_context,
                        autoescape=True,
                    )
            else:
                html_body = self._render_string(
                    bundle.html_template,
                    full_context,
                    autoescape=True,
                )

        text_body = None
        if bundle.text_template:
            if bundle.source == "file":
                text_path = self._template_key_to_path(template_key, "txt")
                try:
                    template = self.env.get_template(text_path)
                    text_body = template.render(full_context)
                except TemplateNotFound:
                    text_body = self._render_string(
                        bundle.text_template,
                        full_context,
                        autoescape=False,
                    )
            else:
                text_body = self._render_string(
                    bundle.text_template,
                    full_context,
                    autoescape=False,
                )

        logger.info(
            "Email template rendered",
            template_key=template_key,
            tenant_id=tenant_id,
            source=bundle.source,
        )

        return RenderedEmail(
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            template_key=template_key,
            tenant_id=tenant_id,
            variables_used=context,
        )

    def validate_template(self, template_str: str) -> tuple[bool, str | None]:
        """
        Validate Jinja2 template syntax.

        Args:
            template_str: Template string to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self.string_env_text.parse(template_str)
            return True, None
        except TemplateSyntaxError as e:
            return False, f"Syntax error on line {e.lineno}: {e.message}"

    def extract_variables(self, template_str: str) -> list[str]:
        """
        Extract all undeclared variables from a template.

        Args:
            template_str: Template string to analyze

        Returns:
            List of variable names used in the template
        """
        try:
            ast = self.string_env_text.parse(template_str)
            return sorted(meta.find_undeclared_variables(ast))
        except TemplateSyntaxError:
            return []


# Global tenant-aware service instance
_tenant_template_service: TenantAwareTemplateService | None = None


def get_tenant_template_service(
    template_dir: str | Path | None = None,
) -> TenantAwareTemplateService:
    """Get or create the global tenant-aware template service."""
    global _tenant_template_service
    if _tenant_template_service is None:
        _tenant_template_service = TenantAwareTemplateService(template_dir)
    return _tenant_template_service

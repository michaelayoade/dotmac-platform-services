"""
Template service with Jinja2 rendering and validation.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple

import structlog
from jinja2 import Environment, DictLoader, meta, TemplateSyntaxError, UndefinedError
from jinja2.sandbox import SandboxedEnvironment
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from ..db import get_async_session
except ImportError:
    # Mock for testing when db module is not available
    async def get_async_session():
        return None
from .models import (
    EmailTemplate,
    EmailTemplateCreate,
    EmailTemplateResponse,
    EmailTemplateUpdate,
    TemplatePreviewRequest,
    TemplatePreviewResponse,
)

logger = structlog.get_logger(__name__)


class TemplateService:
    """Service for managing email templates with Jinja2 rendering."""

    def __init__(self):
        # Use sandboxed environment for security
        self.jinja_env = SandboxedEnvironment(
            loader=DictLoader({}),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add common template functions
        self.jinja_env.globals.update({
            'len': len,
            'str': str,
            'int': int,
            'float': float,
        })

    async def create_template(
        self,
        template_data: EmailTemplateCreate,
        session: Optional[AsyncSession] = None
    ) -> EmailTemplateResponse:
        """Create a new email template."""
        if session is None:
            async with get_async_session() as session:
                return await self._create_template(template_data, session)
        return await self._create_template(template_data, session)

    async def _create_template(
        self,
        template_data: EmailTemplateCreate,
        session: AsyncSession
    ) -> EmailTemplateResponse:
        """Internal create template method."""
        # Validate templates
        await self._validate_template_syntax(
            template_data.subject_template,
            template_data.html_template,
            template_data.text_template
        )

        # Extract variables from templates
        variables = self._extract_template_variables(
            template_data.subject_template,
            template_data.html_template,
            template_data.text_template
        )

        # Create template record
        template = EmailTemplate(
            name=template_data.name,
            description=template_data.description,
            subject_template=template_data.subject_template,
            html_template=template_data.html_template,
            text_template=template_data.text_template,
            variables=variables,
            category=template_data.category,
            is_active=template_data.is_active,
        )

        session.add(template)
        await session.commit()
        await session.refresh(template)

        logger.info("Created email template", template_id=template.id, name=template.name)
        return EmailTemplateResponse.model_validate(template)

    async def get_template(
        self,
        template_id: str,
        session: Optional[AsyncSession] = None
    ) -> Optional[EmailTemplateResponse]:
        """Get an email template by ID."""
        if session is None:
            async with get_async_session() as session:
                return await self._get_template(template_id, session)
        return await self._get_template(template_id, session)

    async def _get_template(
        self,
        template_id: str,
        session: AsyncSession
    ) -> Optional[EmailTemplateResponse]:
        """Internal get template method."""
        result = await session.execute(
            select(EmailTemplate).where(EmailTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        if template:
            return EmailTemplateResponse.model_validate(template)
        return None

    async def list_templates(
        self,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        session: Optional[AsyncSession] = None
    ) -> List[EmailTemplateResponse]:
        """List email templates with optional filtering."""
        if session is None:
            async with get_async_session() as session:
                return await self._list_templates(category, is_active, session)
        return await self._list_templates(category, is_active, session)

    async def _list_templates(
        self,
        category: Optional[str],
        is_active: Optional[bool],
        session: AsyncSession
    ) -> List[EmailTemplateResponse]:
        """Internal list templates method."""
        query = select(EmailTemplate)

        if category:
            query = query.where(EmailTemplate.category == category)
        if is_active is not None:
            query = query.where(EmailTemplate.is_active == is_active)

        query = query.order_by(EmailTemplate.created_at.desc())

        result = await session.execute(query)
        templates = result.scalars().all()

        return [EmailTemplateResponse.model_validate(template) for template in templates]

    async def update_template(
        self,
        template_id: str,
        update_data: EmailTemplateUpdate,
        session: Optional[AsyncSession] = None
    ) -> Optional[EmailTemplateResponse]:
        """Update an email template."""
        if session is None:
            async with get_async_session() as session:
                return await self._update_template(template_id, update_data, session)
        return await self._update_template(template_id, update_data, session)

    async def _update_template(
        self,
        template_id: str,
        update_data: EmailTemplateUpdate,
        session: AsyncSession
    ) -> Optional[EmailTemplateResponse]:
        """Internal update template method."""
        result = await session.execute(
            select(EmailTemplate).where(EmailTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        if not template:
            return None

        # Validate new templates if provided
        subject = update_data.subject_template or template.subject_template
        html = update_data.html_template or template.html_template
        text = update_data.text_template or template.text_template

        await self._validate_template_syntax(subject, html, text)

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(template, field, value)

        # Update variables if templates changed
        if any(field in update_dict for field in ['subject_template', 'html_template', 'text_template']):
            template.variables = self._extract_template_variables(subject, html, text)

        await session.commit()
        await session.refresh(template)

        logger.info("Updated email template", template_id=template.id)
        return EmailTemplateResponse.model_validate(template)

    async def delete_template(
        self,
        template_id: str,
        session: Optional[AsyncSession] = None
    ) -> bool:
        """Delete an email template (soft delete by setting is_active=False)."""
        if session is None:
            async with get_async_session() as session:
                return await self._delete_template(template_id, session)
        return await self._delete_template(template_id, session)

    async def _delete_template(
        self,
        template_id: str,
        session: AsyncSession
    ) -> bool:
        """Internal delete template method."""
        result = await session.execute(
            select(EmailTemplate).where(EmailTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        if not template:
            return False

        template.is_active = False
        await session.commit()

        logger.info("Deleted email template", template_id=template.id)
        return True

    async def preview_template(
        self,
        template_id: str,
        preview_data: TemplatePreviewRequest,
        session: Optional[AsyncSession] = None
    ) -> Optional[TemplatePreviewResponse]:
        """Preview template with sample data."""
        template = await self.get_template(template_id, session)
        if not template:
            return None

        return await self.render_template(
            template.subject_template,
            template.html_template,
            template.text_template,
            preview_data.template_data
        )

    async def render_template(
        self,
        subject_template: str,
        html_template: str,
        text_template: Optional[str],
        template_data: Dict[str, Any]
    ) -> TemplatePreviewResponse:
        """Render templates with provided data."""
        try:
            # Create templates
            subject_tmpl = self.jinja_env.from_string(subject_template)
            html_tmpl = self.jinja_env.from_string(html_template)
            text_tmpl = self.jinja_env.from_string(text_template) if text_template else None

            # Get all variables used in templates
            variables_used = self._extract_template_variables(
                subject_template, html_template, text_template
            )['all_variables']

            # Render templates
            subject = subject_tmpl.render(template_data)
            html_content = html_tmpl.render(template_data)
            text_content = text_tmpl.render(template_data) if text_tmpl else None

            # Find missing variables
            missing_variables = [
                var for var in variables_used
                if var not in template_data
            ]

            return TemplatePreviewResponse(
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                variables_used=list(variables_used),
                missing_variables=missing_variables
            )

        except UndefinedError as e:
            logger.error("Template rendering failed due to undefined variable", error=str(e))
            raise ValueError(f"Template rendering failed: {str(e)}")
        except Exception as e:
            logger.error("Template rendering failed", error=str(e))
            raise ValueError(f"Template rendering error: {str(e)}")

    async def _validate_template_syntax(
        self,
        subject: str,
        html: str,
        text: Optional[str]
    ) -> None:
        """Validate Jinja2 template syntax."""
        templates = [("subject", subject), ("html", html)]
        if text:
            templates.append(("text", text))

        for template_type, template_content in templates:
            try:
                self.jinja_env.from_string(template_content)
            except TemplateSyntaxError as e:
                logger.error(
                    "Template syntax error",
                    template_type=template_type,
                    error=str(e),
                    line=e.lineno
                )
                raise ValueError(f"Syntax error in {template_type} template: {str(e)}")

    def _extract_template_variables(
        self,
        subject: str,
        html: str,
        text: Optional[str]
    ) -> Dict[str, Any]:
        """Extract all variables used in templates."""
        all_variables: Set[str] = set()

        # Extract from each template
        for template_content in [subject, html, text]:
            if template_content:
                try:
                    ast = self.jinja_env.parse(template_content)
                    variables = meta.find_undeclared_variables(ast)
                    all_variables.update(variables)
                except TemplateSyntaxError:
                    # Skip if template has syntax errors
                    pass

        return {
            'all_variables': list(all_variables),
            'required_variables': [],  # Could be enhanced with analysis
            'optional_variables': list(all_variables),
        }


# Global service instance
_template_service: Optional[TemplateService] = None


def get_template_service() -> TemplateService:
    """Get or create the global template service."""
    global _template_service
    if _template_service is None:
        _template_service = TemplateService()
    return _template_service
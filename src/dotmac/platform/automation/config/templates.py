"""
Configuration templates and rendering.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ConfigTemplate:
    """
    Configuration template.
    """

    def __init__(self, name: str, template: str):
        self.name = name
        self.template = template

    def render(self, variables: dict[str, Any]) -> str:
        """Render template with variables."""
        # Simple placeholder rendering - would use Jinja2 in production
        result = self.template
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result


class ConfigRenderer:
    """
    Configuration template renderer.
    """

    def __init__(self):
        self._templates: dict[str, ConfigTemplate] = {}

    def add_template(self, template: ConfigTemplate):
        """Add configuration template."""
        self._templates[template.name] = template

    def render_template(self, name: str, variables: dict[str, Any]) -> str:
        """Render template with variables."""
        template = self._templates.get(name)
        if not template:
            raise ValueError(f"Template {name} not found")
        return template.render(variables)

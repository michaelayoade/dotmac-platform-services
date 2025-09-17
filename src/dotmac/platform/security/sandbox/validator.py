from dotmac.platform.observability.unified_logging import get_logger

"""
Plugin validation utilities and decorators.
"""

from typing import Any, Optional
from uuid import UUID

import structlog

from .manager import SecurityScanner
from .models import PluginPermissions, ResourceLimits
from .sandbox import PluginSandbox

logger = get_logger(__name__)

async def validate_plugin(
    plugin_code: str, plugin_metadata: dict[str, Any], scanner: Optional[SecurityScanner] = None
) -> bool:
    """
    Validate plugin code for security issues.

    Args:
        plugin_code: Plugin source code
        plugin_metadata: Plugin metadata dictionary
        scanner: Optional security scanner instance

    Returns:
        True if plugin is valid and safe
    """
    if not scanner:
        scanner = SecurityScanner()

    return await scanner.validate_plugin_code(plugin_code, plugin_metadata)

def create_secure_environment(
    plugin_id: str,
    tenant_id: Optional[UUID] = None,
    security_level: str = "default",
    permissions: Optional[PluginPermissions] = None,
    resource_limits: Optional[ResourceLimits] = None,
) -> PluginSandbox:
    """
    Create a secure execution environment for a plugin.

    Args:
        plugin_id: Unique plugin identifier
        tenant_id: Tenant ID for multi-tenant isolation
        security_level: Security level (minimal, default, trusted)
        permissions: Custom permissions (overrides security_level)
        resource_limits: Custom resource limits (overrides security_level)

    Returns:
        Configured PluginSandbox instance
    """
    logger.info(
        "Creating secure environment",
        plugin_id=plugin_id,
        tenant_id=str(tenant_id) if tenant_id else None,
        security_level=security_level,
    )

    # Use custom parameters if provided, otherwise use security level defaults
    if permissions or resource_limits:
        return PluginSandbox(
            plugin_id=plugin_id,
            tenant_id=tenant_id,
            permissions=permissions or PluginPermissions.create_default(),
            resource_limits=resource_limits or ResourceLimits(),
        )

    # Use SecurityScanner to create appropriate sandbox
    scanner = SecurityScanner()
    return scanner.create_sandbox(plugin_id, tenant_id, security_level)

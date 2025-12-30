"""
OSS Service Configuration Module.

Provides tenant-level configuration for external OSS services.
This is a stub module - implement actual OSS integrations as needed.
"""

from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from dotmac.platform.tenant.models import Tenant

logger = structlog.get_logger(__name__)


class OSSService:
    """OSS Service configuration manager."""

    def __init__(self, tenant_id: str) -> None:
        """Initialize OSS service for a tenant."""
        self.tenant_id = tenant_id
        self._config: dict[str, Any] = {}

    async def get_config(self) -> dict[str, Any]:
        """Get the current OSS configuration for this tenant."""
        return self._config.copy()

    async def update_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Update the OSS configuration for this tenant."""
        self._config.update(config)
        logger.info(
            "OSS config updated",
            tenant_id=self.tenant_id,
            keys=list(config.keys()),
        )
        return self._config.copy()


async def update_service_config(
    tenant_id: str,
    service_name: str,
    config: dict[str, Any],
    session: AsyncSession,
) -> dict[str, Any]:
    """
    Update configuration for a specific OSS service.

    Args:
        tenant_id: The tenant ID
        service_name: Name of the service to configure
        config: Configuration dictionary

    Returns:
        Updated configuration
    """
    logger.info(
        "Updating OSS service config",
        tenant_id=tenant_id,
        service=service_name,
    )

    result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise ValueError(f"Tenant {tenant_id} not found")

    settings = dict(tenant.settings or {})
    oss_config = dict(settings.get("oss") or {})
    service_config = dict(oss_config.get(service_name) or {})
    service_config.update(config)
    oss_config[service_name] = service_config
    settings["oss"] = oss_config

    tenant.settings = settings
    flag_modified(tenant, "settings")
    await session.commit()
    await session.refresh(tenant)

    return {
        "tenant_id": tenant_id,
        "service": service_name,
        "config": service_config,
        "status": "configured",
    }

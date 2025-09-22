from dotmac.platform.logging import get_logger

"""
Tenant security manager for multi-tenant applications.
"""

from typing import Optional

import structlog

from .models import TenantInfo, TenantStatus

logger = get_logger(__name__)

class TenantSecurityManager:
    """Manager for tenant security operations."""

    def __init__(self, cache_ttl: int = 300):
        self.cache_ttl = cache_ttl
        self._tenant_cache: dict[str, TenantInfo] = {}

    async def validate_tenant(self, tenant_id: str) -> bool:
        """Validate if tenant exists and is active."""
        tenant_info = await self.get_tenant_info(tenant_id)
        return tenant_info is not None and tenant_info.status in [
            TenantStatus.ACTIVE,
            TenantStatus.TRIAL,
        ]

    async def get_tenant_info(self, tenant_id: str) -> Optional[TenantInfo]:
        """Get tenant information from cache or database."""

        # Check cache first
        if tenant_id in self._tenant_cache:
            return self._tenant_cache[tenant_id]

        # In production, this would query the database
        # For now, simulate with basic validation
        if self._is_valid_tenant_format(tenant_id):
            tenant_info = TenantInfo(
                tenant_id=tenant_id,
                name=f"Tenant {tenant_id}",
                status=TenantStatus.ACTIVE,
                plan="standard",
            )

            # Cache the result
            self._tenant_cache[tenant_id] = tenant_info
            return tenant_info

        return None

    async def check_tenant_access(self, tenant_id: str, resource: str) -> bool:
        """Check if tenant has access to a specific resource."""
        tenant_info = await self.get_tenant_info(tenant_id)
        if not tenant_info:
            return False

        # Check if tenant is active
        if tenant_info.status not in [TenantStatus.ACTIVE, TenantStatus.TRIAL]:
            logger.warning(
                "Access denied for inactive tenant",
                tenant_id=tenant_id,
                status=tenant_info.status.value,
            )
            return False

        # Additional resource-specific checks can be added here
        return True

    async def invalidate_tenant_cache(self, tenant_id: Optional[str] = None) -> None:
        """Invalidate tenant cache for specific tenant or all tenants."""
        if tenant_id:
            self._tenant_cache.pop(tenant_id, None)
            logger.info("Invalidated tenant cache", tenant_id=tenant_id)
        else:
            self._tenant_cache.clear()
            logger.info("Invalidated all tenant cache")

    def _is_valid_tenant_format(self, tenant_id: str) -> bool:
        """Validate tenant ID format."""
        return bool(tenant_id and len(tenant_id) >= 3)

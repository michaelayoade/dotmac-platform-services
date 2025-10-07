"""
Platform Admin API Router - Cross-tenant administration endpoints.

Provides endpoints for SaaS platform administrators to:
- View and manage all tenants
- Access cross-tenant analytics
- Perform system-wide operations
- Manage platform-level configurations
"""

from typing import Any

import structlog
from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.db import get_async_session

from .core import UserInfo
from .platform_admin import (
    PLATFORM_PERMISSIONS,
    platform_audit,
    require_platform_admin,
    require_platform_permission,
)

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["Platform Administration"])


# ============================================
# Response Models
# ============================================


class TenantInfo(BaseModel):
    """Tenant information for platform admin."""

    tenant_id: str
    name: str | None = None
    created_at: str | None = None
    is_active: bool = True
    user_count: int = 0
    resource_count: int = 0


class TenantListResponse(BaseModel):
    """Response for listing all tenants."""

    tenants: list[TenantInfo]
    total: int
    page: int
    page_size: int


class PlatformStats(BaseModel):
    """Platform-wide statistics."""

    total_tenants: int
    active_tenants: int
    total_users: int
    total_resources: int
    system_health: str = "healthy"


class CrossTenantSearchRequest(BaseModel):
    """Request for cross-tenant search."""

    query: str = Field(..., min_length=1)
    resource_type: str | None = None
    tenant_ids: list[str] | None = None
    limit: int = Field(default=20, ge=1, le=100)


class HealthCheckResponse(BaseModel):
    """Health check response for platform admin."""

    status: str
    user_id: str
    is_platform_admin: bool
    permissions: list[str]


class PlatformPermissionsResponse(BaseModel):
    """Response for listing platform permissions."""

    permissions: dict[str, str]
    total: int


class CrossTenantSearchResponse(BaseModel):
    """Response for cross-tenant search."""

    results: list[dict[str, Any]]
    total: int
    query: str


class PlatformAuditResponse(BaseModel):
    """Response for platform audit log."""

    actions: list[dict[str, Any]]
    total: int
    limit: int


class ImpersonationTokenResponse(BaseModel):
    """Response for impersonation token creation."""

    access_token: str
    token_type: str
    expires_in: int
    target_tenant: str
    impersonating: bool


class CacheClearResponse(BaseModel):
    """Response for cache clearing operation."""

    status: str
    cache_type: str | None = None
    message: str | None = None


class SystemConfigResponse(BaseModel):
    """Response for system configuration."""

    environment: str
    multi_tenant_mode: bool | None = None
    features_enabled: dict[str, bool] | None = None
    message: str | None = None


# ============================================
# Platform Admin Endpoints
# ============================================


@router.get("/health", response_model=HealthCheckResponse)
async def platform_admin_health(
    admin: UserInfo = Depends(require_platform_admin),
) -> HealthCheckResponse:
    """Health check for platform admin access.

    Verifies that the requesting user has platform admin permissions.
    """
    await platform_audit.log_action(
        user=admin,
        action="platform_health_check",
    )

    return HealthCheckResponse(
        status="healthy",
        user_id=admin.user_id,
        is_platform_admin=admin.is_platform_admin,
        permissions=admin.permissions,
    )


@router.get("/tenants", response_model=TenantListResponse)
async def list_all_tenants(
    request: Request,
    admin: UserInfo = Depends(require_platform_permission("platform:tenants:read")),
    db: AsyncSession = Depends(get_async_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> TenantListResponse:
    """List all tenants in the platform.

    Requires: platform:tenants:read permission

    This endpoint returns all tenants regardless of the requesting user's tenant.
    """
    await platform_audit.log_action(
        user=admin,
        action="list_all_tenants",
        details={"page": page, "page_size": page_size},
    )

    from dotmac.platform.customer_management.models import Customer
    from dotmac.platform.user_management.models import User

    # Get distinct tenants from users table
    tenant_query = (
        select(User.tenant_id, func.count(User.id).label("user_count"))
        .group_by(User.tenant_id)
        .order_by(User.tenant_id)
    )

    # Apply pagination
    offset = (page - 1) * page_size
    tenant_query = tenant_query.offset(offset).limit(page_size)

    result = await db.execute(tenant_query)
    tenant_data = result.all()

    # Get total count
    count_query = select(func.count(func.distinct(User.tenant_id)))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Build tenant info list
    tenants = []
    for tenant_id, user_count in tenant_data:
        # Count resources (customers) for this tenant
        resource_query = select(func.count(Customer.id)).where(Customer.tenant_id == tenant_id)
        resource_result = await db.execute(resource_query)
        resource_count = resource_result.scalar() or 0

        # Get first user's created_at as tenant created_at approximation
        user_query = (
            select(User.created_at)
            .where(User.tenant_id == tenant_id)
            .order_by(User.created_at)
            .limit(1)
        )
        user_result = await db.execute(user_query)
        first_user = user_result.scalar_one_or_none()

        tenants.append(
            TenantInfo(
                tenant_id=tenant_id,
                name=f"Tenant {tenant_id}",  # Could be enhanced with a tenants table
                created_at=first_user.isoformat() if first_user else None,
                is_active=True,
                user_count=user_count,
                resource_count=resource_count,
            )
        )

    return TenantListResponse(
        tenants=tenants,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/stats", response_model=PlatformStats)
async def get_platform_stats(
    admin: UserInfo = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_async_session),
) -> PlatformStats:
    """Get platform-wide statistics.

    Requires: Platform admin access

    Returns aggregated statistics across all tenants.
    """
    await platform_audit.log_action(
        user=admin,
        action="view_platform_stats",
    )

    from dotmac.platform.customer_management.models import Customer
    from dotmac.platform.user_management.models import User

    # Get total and active tenants
    tenant_count_query = select(func.count(func.distinct(User.tenant_id)))
    tenant_count_result = await db.execute(tenant_count_query)
    total_tenants = tenant_count_result.scalar() or 0

    # Get total users
    user_count_query = select(func.count(User.id))
    user_count_result = await db.execute(user_count_query)
    total_users = user_count_result.scalar() or 0

    # Get total resources (customers)
    resource_count_query = select(func.count(Customer.id))
    resource_count_result = await db.execute(resource_count_query)
    total_resources = resource_count_result.scalar() or 0

    # For now, consider all tenants active (could add status check)
    active_tenants = total_tenants

    # Check system health
    system_health = "healthy"
    try:
        # Test database connection
        await db.execute(select(1))
    except Exception:
        system_health = "degraded"

    stats = PlatformStats(
        total_tenants=total_tenants,
        active_tenants=active_tenants,
        total_users=total_users,
        total_resources=total_resources,
        system_health=system_health,
    )

    return stats


@router.get("/permissions", response_model=PlatformPermissionsResponse)
async def list_platform_permissions(
    admin: UserInfo = Depends(require_platform_admin),
) -> PlatformPermissionsResponse:
    """List all available platform permissions.

    Returns the complete list of platform-level permissions and their descriptions.
    """
    await platform_audit.log_action(
        user=admin,
        action="list_platform_permissions",
    )

    return PlatformPermissionsResponse(
        permissions=PLATFORM_PERMISSIONS,
        total=len(PLATFORM_PERMISSIONS),
    )


@router.post("/search", response_model=CrossTenantSearchResponse)
async def cross_tenant_search(
    search_request: CrossTenantSearchRequest,
    admin: UserInfo = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_async_session),
) -> CrossTenantSearchResponse:
    """Perform cross-tenant search.

    Requires: Platform admin access

    Searches across all tenants or specific tenants for resources matching the query.
    """
    await platform_audit.log_action(
        user=admin,
        action="cross_tenant_search",
        details={
            "query": search_request.query,
            "resource_type": search_request.resource_type,
            "tenant_ids": search_request.tenant_ids,
        },
    )

    # Placeholder - implement actual cross-tenant search
    return CrossTenantSearchResponse(
        results=[],
        total=0,
        query=search_request.query,
    )


@router.get("/audit/recent", response_model=PlatformAuditResponse)
async def get_recent_platform_actions(
    admin: UserInfo = Depends(require_platform_permission("platform:audit")),
    db: AsyncSession = Depends(get_async_session),
    limit: int = Query(50, ge=1, le=200),
) -> PlatformAuditResponse:
    """Get recent platform admin actions across all tenants.

    Requires: platform:audit permission

    Returns recent administrative actions for compliance and monitoring.
    """
    await platform_audit.log_action(
        user=admin,
        action="view_platform_audit_log",
        details={"limit": limit},
    )

    # Placeholder - query audit log
    return PlatformAuditResponse(
        actions=[],
        total=0,
        limit=limit,
    )


@router.post("/tenants/{tenant_id}/impersonate", response_model=ImpersonationTokenResponse)
async def create_impersonation_token(
    tenant_id: str,
    admin: UserInfo = Depends(require_platform_permission("platform:impersonate")),
    duration_minutes: int = Query(60, ge=1, le=480),
) -> ImpersonationTokenResponse:
    """Create a temporary token for tenant impersonation.

    Requires: platform:impersonate permission

    Creates a time-limited token that allows the platform admin to act as
    if they belong to the specified tenant.

    Args:
        tenant_id: Target tenant to impersonate
        duration_minutes: Token validity in minutes (max 8 hours)
    """
    await platform_audit.log_action(
        user=admin,
        action="create_impersonation_token",
        target_tenant=tenant_id,
        details={"duration_minutes": duration_minutes},
    )

    from .core import jwt_service

    # Create a token with the target tenant
    token = jwt_service.create_access_token(
        subject=admin.user_id,
        additional_claims={
            "email": admin.email,
            "tenant_id": tenant_id,  # Override tenant
            "is_platform_admin": True,  # Maintain admin status
            "impersonating": True,
            "original_tenant": admin.tenant_id,
        },
        expire_minutes=duration_minutes,
    )

    logger.warning(
        "Platform admin impersonation token created",
        admin_id=admin.user_id,
        target_tenant=tenant_id,
        duration=duration_minutes,
    )

    return ImpersonationTokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=duration_minutes * 60,
        target_tenant=tenant_id,
        impersonating=True,
    )


# ============================================
# System Management Endpoints
# ============================================


@router.post("/system/cache/clear", response_model=CacheClearResponse)
async def clear_system_cache(
    admin: UserInfo = Depends(require_platform_admin),
    cache_type: str | None = Query(
        None, description="Specific cache to clear (e.g., 'permissions', 'all')"
    ),
) -> CacheClearResponse:
    """Clear system-wide caches.

    Requires: Platform admin access

    Clears caching layers across the platform for troubleshooting or after configuration changes.
    """
    await platform_audit.log_action(
        user=admin,
        action="clear_system_cache",
        details={"cache_type": cache_type or "all"},
    )

    # Placeholder - implement cache clearing
    from dotmac.platform.core.caching import get_redis

    try:
        redis_client = get_redis()
        if redis_client:
            if cache_type == "permissions":
                # Clear permission caches
                pattern = "user_perms:*"
                for key in redis_client.scan_iter(match=pattern):
                    redis_client.delete(key)
                return CacheClearResponse(status="success", cache_type="permissions")
            else:
                # Clear all caches
                redis_client.flushdb()
                return CacheClearResponse(status="success", cache_type="all")
    except Exception as e:
        logger.error("Failed to clear cache", error=str(e))
        return CacheClearResponse(status="error", message=str(e))

    return CacheClearResponse(status="no_cache", message="Redis not available")


@router.get("/system/config", response_model=SystemConfigResponse)
async def get_system_configuration(
    admin: UserInfo = Depends(require_platform_admin),
) -> SystemConfigResponse:
    """Get system configuration (non-sensitive values only).

    Requires: Platform admin access

    Returns current platform configuration for review.
    """
    await platform_audit.log_action(
        user=admin,
        action="view_system_config",
    )

    # Return non-sensitive configuration
    try:
        from dotmac.platform.settings import settings

        return SystemConfigResponse(
            environment=getattr(settings, "environment", "unknown"),
            multi_tenant_mode=getattr(settings, "multi_tenant_mode", False),
            features_enabled={
                "rbac": True,
                "audit_logging": True,
                "platform_admin": True,
            },
        )
    except Exception:
        return SystemConfigResponse(
            environment="unknown",
            message="Settings not fully configured",
        )


__all__ = ["router"]

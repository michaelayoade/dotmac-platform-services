"""Tenant Portal Router - Self-service endpoints for tenant admins."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.core import UserInfo, get_current_user
from dotmac.platform.database import get_async_session
from dotmac.platform.tenant.dependencies import (
    get_current_tenant,
    get_tenant_service,
)
from dotmac.platform.tenant.models import (
    Tenant,
    TenantInvitation,
    TenantInvitationStatus,
    TenantPlanType,
    TenantSetting,
    TenantStatus,
    TenantUsage,
)
from dotmac.platform.tenant.schemas import (
    TenantInvitationCreate,
    TenantInvitationResponse,
    TenantResponse,
    TenantSettingResponse,
    TenantUsageResponse,
)
from dotmac.platform.tenant.service import TenantService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/portal", tags=["Tenant Portal"])


# =============================================================================
# Portal-Specific Schemas
# =============================================================================


class TenantDashboardStats(BaseModel):
    """Dashboard statistics for tenant portal."""

    model_config = ConfigDict()

    # Usage metrics
    active_users: int = Field(default=0, alias="activeUsers")
    max_users: int = Field(default=0, alias="maxUsers")
    api_calls_this_month: int = Field(default=0, alias="apiCallsThisMonth")
    api_calls_limit: int = Field(default=0, alias="apiCallsLimit")
    storage_used_mb: float = Field(default=0.0, alias="storageUsedMb")
    storage_limit_mb: float = Field(default=0.0, alias="storageLimitMb")
    bandwidth_used_gb: float = Field(default=0.0, alias="bandwidthUsedGb")

    # Usage percentages
    user_usage_percent: float = Field(default=0.0)
    api_usage_percent: float = Field(default=0.0)
    storage_usage_percent: float = Field(default=0.0)

    # Subscription info
    plan_name: str = Field(alias="planName")
    plan_type: TenantPlanType = Field(alias="planType")
    status: TenantStatus
    days_until_renewal: int | None = Field(None, alias="daysUntilRenewal")
    is_trial: bool = Field(default=False, alias="isTrial")
    trial_ends_at: datetime | None = Field(None, alias="trialEndsAt")

    # Counts
    pending_invitations: int = Field(default=0, alias="pendingInvitations")
    total_team_members: int = Field(default=0, alias="totalTeamMembers")

    class Config:
        populate_by_name = True


class TeamMember(BaseModel):
    """Team member information."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    user_id: str | None = Field(None, alias="userId")
    email: str
    full_name: str | None = Field(None, alias="fullName")
    role: str
    status: str
    joined_at: datetime | None = Field(None, alias="joinedAt")
    last_active_at: datetime | None = Field(None, alias="lastActiveAt")


class TeamMembersResponse(BaseModel):
    """Paginated team members response."""

    model_config = ConfigDict(populate_by_name=True)

    members: list[TeamMember]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")


class InvitationsResponse(BaseModel):
    """Invitations list response."""

    model_config = ConfigDict(populate_by_name=True)

    invitations: list[TenantInvitationResponse]
    total: int


class InviteMemberRequest(BaseModel):
    """Request to invite a new member."""

    model_config = ConfigDict()

    email: EmailStr
    role: str = "member"
    send_email: bool = Field(default=True, alias="sendEmail")


class UpdateMemberRoleRequest(BaseModel):
    """Request to update member role."""

    role: str


class BillingInfo(BaseModel):
    """Tenant billing information."""

    model_config = ConfigDict(populate_by_name=True)

    plan_name: str = Field(alias="planName")
    plan_type: TenantPlanType = Field(alias="planType")
    status: TenantStatus
    billing_cycle: str = Field(alias="billingCycle")
    monthly_price: Decimal | None = Field(None, alias="monthlyPrice")
    current_period_start: datetime | None = Field(None, alias="currentPeriodStart")
    current_period_end: datetime | None = Field(None, alias="currentPeriodEnd")
    trial_ends_at: datetime | None = Field(None, alias="trialEndsAt")
    has_payment_method: bool = Field(default=False, alias="hasPaymentMethod")
    payment_method_last4: str | None = Field(None, alias="paymentMethodLast4")
    payment_method_brand: str | None = Field(None, alias="paymentMethodBrand")


class Invoice(BaseModel):
    """Invoice information."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    number: str
    status: str
    amount_due: int = Field(alias="amountDue")
    amount_paid: int = Field(alias="amountPaid")
    currency: str
    period_start: datetime = Field(alias="periodStart")
    period_end: datetime = Field(alias="periodEnd")
    paid_at: datetime | None = Field(None, alias="paidAt")
    created_at: datetime = Field(alias="createdAt")


class InvoicesResponse(BaseModel):
    """Paginated invoices response."""

    model_config = ConfigDict(populate_by_name=True)

    invoices: list[Invoice]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")


class UsageMetric(BaseModel):
    """Single usage metric with history."""

    model_config = ConfigDict(populate_by_name=True)

    current: float
    limit: float
    unit: str
    percent_used: float = Field(alias="percentUsed")
    history: list[dict[str, Any]] = Field(default_factory=list)


class UsageMetrics(BaseModel):
    """Usage metrics response."""

    model_config = ConfigDict(populate_by_name=True)

    api_calls: UsageMetric = Field(alias="apiCalls")
    storage: UsageMetric
    users: UsageMetric
    bandwidth: UsageMetric


class UsageBreakdown(BaseModel):
    """Usage breakdown response."""

    model_config = ConfigDict(populate_by_name=True)

    by_feature: list[dict[str, Any]] = Field(default_factory=list, alias="byFeature")
    by_user: list[dict[str, Any]] = Field(default_factory=list, alias="byUser")


class TenantSettingsResponse(BaseModel):
    """Tenant settings response."""

    model_config = ConfigDict(populate_by_name=True)

    general: dict[str, Any] = Field(default_factory=dict)
    branding: dict[str, Any] = Field(default_factory=dict)
    security: dict[str, Any] = Field(default_factory=dict)
    features: dict[str, Any] = Field(default_factory=dict)


class UpdateTenantSettingsRequest(BaseModel):
    """Request to update tenant settings."""

    model_config = ConfigDict()

    general: dict[str, Any] | None = None
    branding: dict[str, Any] | None = None
    security: dict[str, Any] | None = None


class ApiKey(BaseModel):
    """API key information."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    prefix: str
    last_used_at: datetime | None = Field(None, alias="lastUsedAt")
    created_at: datetime = Field(alias="createdAt")
    created_by: str = Field(alias="createdBy")


class CreateApiKeyRequest(BaseModel):
    """Request to create API key."""

    name: str


class CreateApiKeyResponse(BaseModel):
    """Response after creating API key (includes full key once)."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    key: str  # Full key, shown only once
    prefix: str
    created_at: datetime = Field(alias="createdAt")


# =============================================================================
# Portal Dependencies
# =============================================================================


async def get_portal_tenant(
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Tenant:
    """Get the current user's tenant for portal access."""
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with a tenant",
        )

    service = TenantService(db)
    try:
        tenant = await service.get_tenant(current_user.tenant_id)
        return tenant
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )


async def require_portal_admin(
    current_user: UserInfo = Depends(get_current_user),
    tenant: Tenant = Depends(get_portal_tenant),
) -> tuple[UserInfo, Tenant]:
    """Require user to have admin access for portal operations."""
    user_roles = set(r.lower() for r in (current_user.roles or []))

    if not user_roles & {"tenant_admin", "admin", "owner"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for this operation",
        )

    return current_user, tenant


# =============================================================================
# Dashboard Endpoints
# =============================================================================


@router.get("/dashboard", response_model=TenantDashboardStats)
async def get_dashboard_stats(
    tenant: Tenant = Depends(get_portal_tenant),
    db: AsyncSession = Depends(get_async_session),
) -> TenantDashboardStats:
    """Get dashboard statistics for tenant portal."""

    # Count pending invitations
    pending_invitations_result = await db.execute(
        select(func.count(TenantInvitation.id))
        .where(TenantInvitation.tenant_id == tenant.id)
        .where(TenantInvitation.status == TenantInvitationStatus.PENDING)
    )
    pending_invitations = pending_invitations_result.scalar() or 0

    # Calculate days until renewal
    days_until_renewal = None
    if tenant.subscription_ends_at:
        delta = tenant.subscription_ends_at - datetime.utcnow()
        days_until_renewal = max(0, delta.days)

    # Calculate usage percentages
    user_usage_percent = 0.0
    api_usage_percent = 0.0
    storage_usage_percent = 0.0

    if tenant.max_users > 0:
        user_usage_percent = (tenant.current_users / tenant.max_users) * 100

    if tenant.max_api_calls_per_month > 0:
        api_usage_percent = (tenant.current_api_calls / tenant.max_api_calls_per_month) * 100

    if tenant.max_storage_gb > 0:
        storage_usage_percent = (tenant.current_storage_gb / tenant.max_storage_gb) * 100

    plan_names = {
        TenantPlanType.FREE: "Free",
        TenantPlanType.STARTER: "Starter",
        TenantPlanType.PROFESSIONAL: "Professional",
        TenantPlanType.ENTERPRISE: "Enterprise",
        TenantPlanType.CUSTOM: "Custom",
    }

    return TenantDashboardStats(
        activeUsers=tenant.current_users,
        maxUsers=tenant.max_users,
        apiCallsThisMonth=tenant.current_api_calls,
        apiCallsLimit=tenant.max_api_calls_per_month,
        storageUsedMb=tenant.current_storage_gb * 1024,
        storageLimitMb=tenant.max_storage_gb * 1024,
        bandwidthUsedGb=0.0,
        user_usage_percent=round(user_usage_percent, 1),
        api_usage_percent=round(api_usage_percent, 1),
        storage_usage_percent=round(storage_usage_percent, 1),
        planName=plan_names.get(tenant.plan_type, tenant.plan_type.value),
        planType=tenant.plan_type,
        status=tenant.status,
        daysUntilRenewal=days_until_renewal,
        isTrial=tenant.is_trial,
        trialEndsAt=tenant.trial_ends_at,
        pendingInvitations=pending_invitations,
        totalTeamMembers=tenant.current_users,
    )


# =============================================================================
# Team Members Endpoints
# =============================================================================


@router.get("/members", response_model=TeamMembersResponse)
async def list_members(
    tenant: Tenant = Depends(get_portal_tenant),
    db: AsyncSession = Depends(get_async_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    search: str | None = None,
    role: str | None = None,
) -> TeamMembersResponse:
    """List all team members."""
    # TODO: Query actual user management system
    # For now return empty list - in production would join with users table
    return TeamMembersResponse(
        members=[],
        total=tenant.current_users,
        page=page,
        pageSize=page_size,
    )


@router.get("/members/{member_id}", response_model=TeamMember)
async def get_member(
    member_id: str,
    tenant: Tenant = Depends(get_portal_tenant),
) -> TeamMember:
    """Get a specific team member."""
    # TODO: Query actual user management system
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Member not found",
    )


@router.patch("/members/{member_id}/role", response_model=TeamMember)
async def update_member_role(
    member_id: str,
    data: UpdateMemberRoleRequest,
    user_tenant: tuple[UserInfo, Tenant] = Depends(require_portal_admin),
) -> TeamMember:
    """Update a member's role."""
    current_user, tenant = user_tenant
    # TODO: Implement role update via user management system
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Member not found",
    )


@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    member_id: str,
    user_tenant: tuple[UserInfo, Tenant] = Depends(require_portal_admin),
) -> None:
    """Remove a member from the team."""
    current_user, tenant = user_tenant
    # TODO: Implement member removal via user management system
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Member not found",
    )


# =============================================================================
# Invitations Endpoints
# =============================================================================


@router.get("/invitations", response_model=InvitationsResponse)
async def list_invitations(
    tenant: Tenant = Depends(get_portal_tenant),
    service: TenantService = Depends(get_tenant_service),
) -> InvitationsResponse:
    """List all invitations."""
    invitations = await service.list_tenant_invitations(tenant.id)

    responses = []
    for inv in invitations:
        response = TenantInvitationResponse.model_validate(inv)
        response.is_expired = inv.is_expired
        response.is_pending = inv.is_pending
        responses.append(response)

    return InvitationsResponse(
        invitations=responses,
        total=len(responses),
    )


@router.post("/invitations", response_model=TenantInvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    data: InviteMemberRequest,
    user_tenant: tuple[UserInfo, Tenant] = Depends(require_portal_admin),
    service: TenantService = Depends(get_tenant_service),
) -> TenantInvitationResponse:
    """Invite a new team member."""
    current_user, tenant = user_tenant

    if tenant.has_exceeded_user_limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User limit reached ({tenant.max_users}). Please upgrade your plan.",
        )

    invitation_data = TenantInvitationCreate(
        email=data.email,
        role=data.role,
    )

    invitation = await service.create_invitation(
        tenant.id, invitation_data, invited_by=current_user.user_id
    )

    response = TenantInvitationResponse.model_validate(invitation)
    response.is_expired = invitation.is_expired
    response.is_pending = invitation.is_pending

    logger.info(
        "tenant.invitation_created",
        tenant_id=tenant.id,
        email=data.email,
        role=data.role,
        invited_by=current_user.user_id,
    )

    return response


@router.delete("/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_invitation(
    invitation_id: str,
    user_tenant: tuple[UserInfo, Tenant] = Depends(require_portal_admin),
    service: TenantService = Depends(get_tenant_service),
) -> None:
    """Cancel a pending invitation."""
    current_user, tenant = user_tenant

    try:
        await service.revoke_invitation(invitation_id)
        logger.info(
            "tenant.invitation_cancelled",
            tenant_id=tenant.id,
            invitation_id=invitation_id,
            cancelled_by=current_user.user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/invitations/{invitation_id}/resend", response_model=TenantInvitationResponse)
async def resend_invitation(
    invitation_id: str,
    user_tenant: tuple[UserInfo, Tenant] = Depends(require_portal_admin),
    service: TenantService = Depends(get_tenant_service),
    db: AsyncSession = Depends(get_async_session),
) -> TenantInvitationResponse:
    """Resend an invitation email."""
    current_user, tenant = user_tenant

    # Get the invitation
    result = await db.execute(
        select(TenantInvitation).where(
            and_(
                TenantInvitation.id == invitation_id,
                TenantInvitation.tenant_id == tenant.id,
            )
        )
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    # Reset expiration
    invitation.expires_at = datetime.utcnow() + timedelta(days=7)
    invitation.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(invitation)

    # TODO: Send email notification

    logger.info(
        "tenant.invitation_resent",
        tenant_id=tenant.id,
        invitation_id=invitation_id,
        resent_by=current_user.user_id,
    )

    response = TenantInvitationResponse.model_validate(invitation)
    response.is_expired = invitation.is_expired
    response.is_pending = invitation.is_pending
    return response


# =============================================================================
# Billing Endpoints
# =============================================================================


@router.get("/billing", response_model=BillingInfo)
async def get_billing_info(
    tenant: Tenant = Depends(get_portal_tenant),
) -> BillingInfo:
    """Get tenant billing information."""

    plan_names = {
        TenantPlanType.FREE: "Free",
        TenantPlanType.STARTER: "Starter",
        TenantPlanType.PROFESSIONAL: "Professional",
        TenantPlanType.ENTERPRISE: "Enterprise",
        TenantPlanType.CUSTOM: "Custom",
    }

    return BillingInfo(
        planName=plan_names.get(tenant.plan_type, tenant.plan_type.value),
        planType=tenant.plan_type,
        status=tenant.status,
        billingCycle=tenant.billing_cycle.value if tenant.billing_cycle else "monthly",
        currentPeriodStart=tenant.subscription_starts_at,
        currentPeriodEnd=tenant.subscription_ends_at,
        trialEndsAt=tenant.trial_ends_at,
        hasPaymentMethod=False,
        paymentMethodLast4=None,
        paymentMethodBrand=None,
    )


@router.get("/invoices", response_model=InvoicesResponse)
async def list_invoices(
    tenant: Tenant = Depends(get_portal_tenant),
    db: AsyncSession = Depends(get_async_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    status_filter: str | None = Query(None, alias="status"),
) -> InvoicesResponse:
    """List tenant invoices."""
    # TODO: Query billing system for invoices
    return InvoicesResponse(
        invoices=[],
        total=0,
        page=page,
        pageSize=page_size,
    )


@router.get("/invoices/{invoice_id}/download")
async def download_invoice(
    invoice_id: str,
    tenant: Tenant = Depends(get_portal_tenant),
) -> None:
    """Download an invoice PDF."""
    # TODO: Integrate with billing system to generate PDF
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Invoice not found",
    )


# =============================================================================
# Usage Endpoints
# =============================================================================


@router.get("/usage", response_model=UsageMetrics)
async def get_usage(
    tenant: Tenant = Depends(get_portal_tenant),
    db: AsyncSession = Depends(get_async_session),
    period: str = Query("30d", description="Period: 7d, 30d, 90d, 1y"),
) -> UsageMetrics:
    """Get usage metrics for the tenant."""

    # Calculate percentages
    user_percent = (tenant.current_users / tenant.max_users * 100) if tenant.max_users > 0 else 0
    api_percent = (tenant.current_api_calls / tenant.max_api_calls_per_month * 100) if tenant.max_api_calls_per_month > 0 else 0
    storage_percent = (tenant.current_storage_gb / tenant.max_storage_gb * 100) if tenant.max_storage_gb > 0 else 0

    # TODO: Fetch historical data from usage tracking
    return UsageMetrics(
        apiCalls=UsageMetric(
            current=float(tenant.current_api_calls),
            limit=float(tenant.max_api_calls_per_month),
            unit="calls",
            percentUsed=round(api_percent, 1),
            history=[],
        ),
        storage=UsageMetric(
            current=float(tenant.current_storage_gb * 1024),  # MB
            limit=float(tenant.max_storage_gb * 1024),
            unit="MB",
            percentUsed=round(storage_percent, 1),
            history=[],
        ),
        users=UsageMetric(
            current=float(tenant.current_users),
            limit=float(tenant.max_users),
            unit="users",
            percentUsed=round(user_percent, 1),
            history=[],
        ),
        bandwidth=UsageMetric(
            current=0.0,
            limit=50.0,
            unit="GB",
            percentUsed=0.0,
            history=[],
        ),
    )


@router.get("/usage/breakdown", response_model=UsageBreakdown)
async def get_usage_breakdown(
    tenant: Tenant = Depends(get_portal_tenant),
    db: AsyncSession = Depends(get_async_session),
    period: str = Query("30d", description="Period: 7d, 30d, 90d, 1y"),
) -> UsageBreakdown:
    """Get detailed usage breakdown."""
    # TODO: Query analytics for breakdown
    return UsageBreakdown(
        byFeature=[],
        byUser=[],
    )


# =============================================================================
# Settings Endpoints
# =============================================================================


@router.get("/settings", response_model=TenantSettingsResponse)
async def get_settings(
    tenant: Tenant = Depends(get_portal_tenant),
    service: TenantService = Depends(get_tenant_service),
) -> TenantSettingsResponse:
    """Get tenant settings."""

    settings = await service.get_tenant_settings(tenant.id)
    settings_dict = {s.key: s.value for s in settings}

    return TenantSettingsResponse(
        general={
            "name": tenant.name,
            "slug": tenant.slug,
            "domain": tenant.domain,
            "timezone": tenant.timezone,
            "industry": tenant.industry,
            "companySize": tenant.company_size,
        },
        branding={
            "logoUrl": tenant.logo_url,
            "primaryColor": tenant.primary_color,
        },
        security={
            "mfaEnforced": settings_dict.get("mfa_enforced", "false").lower() == "true",
            "sessionTimeoutMinutes": int(settings_dict.get("session_timeout_minutes", "60")),
            "ipWhitelistEnabled": settings_dict.get("ip_whitelist_enabled", "false").lower() == "true",
        },
        features=tenant.features or {},
    )


@router.patch("/settings", response_model=TenantSettingsResponse)
async def update_settings(
    data: UpdateTenantSettingsRequest,
    user_tenant: tuple[UserInfo, Tenant] = Depends(require_portal_admin),
    service: TenantService = Depends(get_tenant_service),
    db: AsyncSession = Depends(get_async_session),
) -> TenantSettingsResponse:
    """Update tenant settings."""
    current_user, tenant = user_tenant

    # Update general settings
    if data.general:
        for key, value in data.general.items():
            if key in ["name", "timezone", "industry", "company_size"]:
                setattr(tenant, key, value)

    # Update branding
    if data.branding:
        if "logoUrl" in data.branding:
            tenant.logo_url = data.branding["logoUrl"]
        if "primaryColor" in data.branding:
            tenant.primary_color = data.branding["primaryColor"]

    # Update security settings
    if data.security:
        for key, value in data.security.items():
            setting_key = key.replace("camelCase", "snake_case")  # Normalize
            from dotmac.platform.tenant.schemas import TenantSettingCreate
            setting_data = TenantSettingCreate(
                key=setting_key,
                value=str(value),
                value_type="bool" if isinstance(value, bool) else "int" if isinstance(value, int) else "string",
            )
            await service.set_tenant_setting(tenant.id, setting_data)

    tenant.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(tenant)

    logger.info(
        "tenant.settings_updated",
        tenant_id=tenant.id,
        updated_by=current_user.user_id,
    )

    # Return updated settings
    return await get_settings(tenant, service)


# =============================================================================
# API Keys Endpoints
# =============================================================================


@router.get("/api-keys", response_model=list[ApiKey])
async def list_api_keys(
    tenant: Tenant = Depends(get_portal_tenant),
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> list[ApiKey]:
    """List API keys for the tenant."""
    # TODO: Query from auth API keys table
    return []


@router.post("/api-keys", response_model=CreateApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    data: CreateApiKeyRequest,
    user_tenant: tuple[UserInfo, Tenant] = Depends(require_portal_admin),
    db: AsyncSession = Depends(get_async_session),
) -> CreateApiKeyResponse:
    """Create a new API key."""
    current_user, tenant = user_tenant

    import secrets
    key = secrets.token_urlsafe(32)
    prefix = key[:8]

    # TODO: Store in auth API keys table
    logger.info(
        "tenant.api_key_created",
        tenant_id=tenant.id,
        key_name=data.name,
        created_by=current_user.user_id,
    )

    return CreateApiKeyResponse(
        id=secrets.token_hex(16),
        name=data.name,
        key=key,
        prefix=prefix,
        createdAt=datetime.utcnow(),
    )


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: str,
    user_tenant: tuple[UserInfo, Tenant] = Depends(require_portal_admin),
) -> None:
    """Delete an API key."""
    current_user, tenant = user_tenant

    # TODO: Delete from auth API keys table
    logger.info(
        "tenant.api_key_deleted",
        tenant_id=tenant.id,
        key_id=key_id,
        deleted_by=current_user.user_id,
    )

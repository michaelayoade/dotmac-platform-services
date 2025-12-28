"""Tenant Portal Router - Self-service endpoints for tenant admins."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.core import UserInfo, ensure_uuid, get_current_user
from dotmac.platform.communications.email_service import EmailMessage, get_email_service
from dotmac.platform.communications.template_service import (
    BrandingConfig,
    get_tenant_template_service,
)
from dotmac.platform.database import get_async_session
from dotmac.platform.settings import settings
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
from dotmac.platform.user_management.models import User

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/portal", tags=["Tenant Portal"])


# =============================================================================
# Portal-Specific Schemas
# =============================================================================


class TenantDashboardStats(BaseModel):
    """Dashboard statistics for tenant portal."""

    model_config = ConfigDict(populate_by_name=True)

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


class CurrentSubscription(BaseModel):
    """Current subscription information matching frontend type."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    plan_name: str = Field(alias="planName")
    plan_type: str = Field(alias="planType")
    status: str
    current_period_start: str = Field(alias="currentPeriodStart")
    current_period_end: str = Field(alias="currentPeriodEnd")
    cancel_at_period_end: bool = Field(default=False, alias="cancelAtPeriodEnd")
    monthly_price: int = Field(alias="monthlyPrice")
    billing_interval: str = Field(alias="billingInterval")
    trial_ends_at: str | None = Field(None, alias="trialEndsAt")


class PaymentMethodCard(BaseModel):
    """Payment method card details."""

    model_config = ConfigDict(populate_by_name=True)

    brand: str
    last4: str
    exp_month: int = Field(alias="expMonth")
    exp_year: int = Field(alias="expYear")


class PaymentMethod(BaseModel):
    """Payment method information."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    type: str
    is_default: bool = Field(default=False, alias="isDefault")
    card: PaymentMethodCard | None = None
    created_at: str = Field(alias="createdAt")


class UpcomingInvoice(BaseModel):
    """Upcoming invoice preview."""

    model_config = ConfigDict(populate_by_name=True)

    amount_due: int = Field(alias="amountDue")
    due_date: str = Field(alias="dueDate")


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


class BillingInfo(BaseModel):
    """Tenant billing information matching frontend BillingInfo type."""

    model_config = ConfigDict(populate_by_name=True)

    subscription: CurrentSubscription
    invoices: list[Invoice] = Field(default_factory=list)
    payment_methods: list[PaymentMethod] = Field(default_factory=list, alias="paymentMethods")
    upcoming_invoice: UpcomingInvoice | None = Field(None, alias="upcomingInvoice")


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
    secret_key: str = Field(alias="secretKey")  # Full key, shown only once
    prefix: str
    created_at: datetime = Field(alias="createdAt")
    # Also provide apiKey object for frontend compatibility
    api_key: dict[str, Any] = Field(default_factory=dict, alias="apiKey")


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
# Email Helpers
# =============================================================================


async def _send_invitation_email(
    invitation: TenantInvitation,
    tenant: Tenant,
    inviter_user_id: str,
    db: AsyncSession,
) -> None:
    """Send invitation email to the invitee."""
    try:
        # Look up inviter name
        inviter_name = "A team admin"
        inviter_result = await db.execute(
            select(User).where(User.id == ensure_uuid(inviter_user_id))
        )
        inviter = inviter_result.scalar_one_or_none()
        if inviter:
            inviter_name = inviter.full_name or inviter.username or inviter.email

        # Build accept URL
        frontend_url = getattr(settings, "frontend_url", "http://localhost:3000")
        accept_url = f"{frontend_url}/accept-invite?token={invitation.token}"

        # Build branding config from tenant
        branding = BrandingConfig(
            product_name=settings.brand.product_name or "DotMac Platform",
            company_name=settings.brand.company_name,
            support_email=settings.brand.support_email,
            primary_color=tenant.primary_color or "#0070f3",
            logo_url=tenant.logo_url,
        )

        # Render email template
        template_service = get_tenant_template_service()
        rendered = await template_service.render_email(
            template_key="email.tenant.invitation",
            context={
                "organization_name": tenant.name,
                "inviter_name": inviter_name,
                "role": invitation.role,
                "accept_url": accept_url,
            },
            tenant_id=str(tenant.id),
            branding=branding,
            db=db,
        )

        # Send email
        email_service = get_email_service()
        message = EmailMessage(
            to=[invitation.email],
            subject=rendered.subject,
            html_body=rendered.html_body,
            text_body=rendered.text_body,
        )

        await email_service.send_email(message, tenant_id=str(tenant.id), db=db)

        logger.info(
            "tenant.invitation_email_sent",
            tenant_id=str(tenant.id),
            invitation_id=str(invitation.id),
            email=invitation.email,
        )

    except Exception as e:
        logger.error(
            "tenant.invitation_email_failed",
            tenant_id=str(tenant.id),
            invitation_id=str(invitation.id),
            email=invitation.email,
            error=str(e),
        )
        # Don't raise - invitation was created, email failure is logged


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
    from dotmac.platform.user_management.service import UserService

    user_service = UserService(db)
    skip = (page - 1) * page_size

    users, total = await user_service.list_users(
        skip=skip,
        limit=page_size,
        tenant_id=str(tenant.id),
        search=search,
        role=role,
        is_active=True,
    )

    members = [
        TeamMember(
            id=str(u.id),
            userId=str(u.id),
            email=u.email,
            fullName=u.full_name or u.username,
            role=u.roles[0] if u.roles else "member",
            status="ACTIVE" if u.is_active else "INACTIVE",
            joinedAt=u.created_at,
            lastActiveAt=u.last_login,
        )
        for u in users
    ]

    return TeamMembersResponse(
        members=members,
        total=total,
        page=page,
        pageSize=page_size,
    )


@router.get("/members/{member_id}", response_model=TeamMember)
async def get_member(
    member_id: str,
    tenant: Tenant = Depends(get_portal_tenant),
    db: AsyncSession = Depends(get_async_session),
) -> TeamMember:
    """Get a specific team member."""
    from dotmac.platform.user_management.service import UserService

    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id=member_id, tenant_id=str(tenant.id))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    return TeamMember(
        id=str(user.id),
        userId=str(user.id),
        email=user.email,
        fullName=user.full_name or user.username,
        role=user.roles[0] if user.roles else "member",
        status="ACTIVE" if user.is_active else "INACTIVE",
        joinedAt=user.created_at,
        lastActiveAt=user.last_login,
    )


@router.patch("/members/{member_id}/role", response_model=TeamMember)
async def update_member_role(
    member_id: str,
    data: UpdateMemberRoleRequest,
    user_tenant: tuple[UserInfo, Tenant] = Depends(require_portal_admin),
    db: AsyncSession = Depends(get_async_session),
) -> TeamMember:
    """Update a member's role."""
    from dotmac.platform.user_management.service import UserService

    current_user, tenant = user_tenant
    user_service = UserService(db)

    # Get the user first
    user = await user_service.get_user_by_id(user_id=member_id, tenant_id=str(tenant.id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    # Update the user's roles
    updated_user = await user_service.update_user(
        user_id=member_id,
        tenant_id=str(tenant.id),
        roles=[data.role],
    )

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update member role",
        )

    return TeamMember(
        id=str(updated_user.id),
        userId=str(updated_user.id),
        email=updated_user.email,
        fullName=updated_user.full_name or updated_user.username,
        role=updated_user.roles[0] if updated_user.roles else "member",
        status="ACTIVE" if updated_user.is_active else "INACTIVE",
        joinedAt=updated_user.created_at,
        lastActiveAt=updated_user.last_login,
    )


@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    member_id: str,
    user_tenant: tuple[UserInfo, Tenant] = Depends(require_portal_admin),
    db: AsyncSession = Depends(get_async_session),
) -> None:
    """Remove a member from the team."""
    from dotmac.platform.user_management.service import UserService

    current_user, tenant = user_tenant
    user_service = UserService(db)

    # Can't remove yourself
    if str(current_user.user_id) == member_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself from the team",
        )

    # Get the user first
    user = await user_service.get_user_by_id(user_id=member_id, tenant_id=str(tenant.id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    # Soft delete by disabling the user
    deleted = await user_service.delete_user(user_id=member_id, tenant_id=str(tenant.id))
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove member",
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
    background_tasks: BackgroundTasks,
    user_tenant: tuple[UserInfo, Tenant] = Depends(require_portal_admin),
    service: TenantService = Depends(get_tenant_service),
    db: AsyncSession = Depends(get_async_session),
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

    # Send invitation email if requested
    if data.send_email:
        await _send_invitation_email(
            invitation=invitation,
            tenant=tenant,
            inviter_user_id=current_user.user_id,
            db=db,
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

    if invitation.status != TenantInvitationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending invitations can be resent",
        )

    # Reset expiration
    invitation.expires_at = datetime.now(UTC) + timedelta(days=7)
    invitation.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(invitation)

    # Send invitation email
    await _send_invitation_email(
        invitation=invitation,
        tenant=tenant,
        inviter_user_id=current_user.user_id,
        db=db,
    )

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
    db: AsyncSession = Depends(get_async_session),
) -> BillingInfo:
    """Get tenant billing information."""
    from dotmac.platform.billing.invoicing.service import InvoiceService

    plan_names = {
        TenantPlanType.FREE: "Free",
        TenantPlanType.STARTER: "Starter",
        TenantPlanType.PROFESSIONAL: "Professional",
        TenantPlanType.ENTERPRISE: "Enterprise",
        TenantPlanType.CUSTOM: "Custom",
    }

    # Build subscription info
    plan_name = plan_names.get(tenant.plan_type, tenant.plan_type.value)
    billing_cycle = tenant.billing_cycle.value if tenant.billing_cycle else "monthly"

    # Plan pricing (in dollars, will convert to cents for frontend display)
    plan_prices = {
        TenantPlanType.FREE: 0,
        TenantPlanType.STARTER: 29,
        TenantPlanType.PROFESSIONAL: 99,
        TenantPlanType.ENTERPRISE: 299,
        TenantPlanType.CUSTOM: 0,
    }
    monthly_price = plan_prices.get(tenant.plan_type, 0)

    # Format dates as ISO strings for frontend
    now = datetime.now(UTC)
    period_start = tenant.subscription_starts_at or now
    period_end = tenant.subscription_ends_at or (now + timedelta(days=30))

    # Map tenant status to subscription status
    status_map = {
        TenantStatus.ACTIVE: "ACTIVE",
        TenantStatus.TRIAL: "TRIALING",
        TenantStatus.SUSPENDED: "PAST_DUE",
        TenantStatus.CANCELLED: "CANCELLED",
        TenantStatus.PENDING: "TRIALING",
        TenantStatus.INACTIVE: "CANCELLED",
        TenantStatus.PROVISIONING: "TRIALING",
        TenantStatus.PROVISIONED: "ACTIVE",
    }

    subscription = CurrentSubscription(
        id=str(tenant.id),
        planName=plan_name,
        planType=tenant.plan_type.value.upper(),
        status=status_map.get(tenant.status, "ACTIVE"),
        currentPeriodStart=period_start.isoformat(),
        currentPeriodEnd=period_end.isoformat(),
        cancelAtPeriodEnd=False,
        monthlyPrice=monthly_price,
        billingInterval=billing_cycle,
        trialEndsAt=tenant.trial_ends_at.isoformat() if tenant.trial_ends_at else None,
    )

    # Fetch recent invoices from billing system
    # Handle case where billing tables don't exist yet
    invoices: list[Invoice] = []
    try:
        invoice_service = InvoiceService(db)
        billing_invoices, _ = await invoice_service.list_invoices_with_count(
            tenant_id=str(tenant.id),
            limit=5,
            offset=0,
        )

        invoices = [
            Invoice(
                id=inv.invoice_id or str(inv.invoice_number),
                number=inv.invoice_number or inv.invoice_id or "N/A",
                status=inv.status.upper() if inv.status else "DRAFT",
                amountDue=inv.total_amount,
                amountPaid=inv.total_amount - inv.remaining_balance if inv.remaining_balance else 0,
                currency=inv.currency,
                periodStart=inv.issue_date,
                periodEnd=inv.due_date or inv.issue_date,
                paidAt=inv.paid_at,
                createdAt=inv.created_at or inv.issue_date,
            )
            for inv in billing_invoices
        ]
    except Exception as e:
        # Log but don't fail if billing tables aren't set up yet
        logger.warning("Could not fetch invoices", error=str(e))

    # Build upcoming invoice if there's a next billing date
    upcoming_invoice = None
    if period_end > now and subscription.monthly_price > 0:
        upcoming_invoice = UpcomingInvoice(
            amountDue=subscription.monthly_price * 100,  # Convert to cents
            dueDate=period_end.isoformat(),
        )

    return BillingInfo(
        subscription=subscription,
        invoices=invoices,
        paymentMethods=[],  # No payment methods stored yet
        upcomingInvoice=upcoming_invoice,
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
    from dotmac.platform.billing.invoicing.service import InvoiceService
    from dotmac.platform.billing.core.enums import InvoiceStatus

    invoice_service = InvoiceService(db)
    offset = (page - 1) * page_size

    # Convert status filter to enum if provided
    status_enum = None
    if status_filter:
        try:
            status_enum = InvoiceStatus(status_filter.lower())
        except ValueError:
            pass

    billing_invoices, total = await invoice_service.list_invoices_with_count(
        tenant_id=str(tenant.id),
        status=status_enum,
        limit=page_size,
        offset=offset,
    )

    # Map billing invoices to portal invoice schema
    invoices = [
        Invoice(
            id=inv.invoice_id or str(inv.invoice_number),
            number=inv.invoice_number or inv.invoice_id or "N/A",
            status=inv.status.upper() if inv.status else "DRAFT",
            amountDue=inv.total_amount,
            amountPaid=inv.total_amount - inv.remaining_balance if inv.remaining_balance else 0,
            currency=inv.currency,
            periodStart=inv.issue_date,
            periodEnd=inv.due_date or inv.issue_date,
            paidAt=inv.paid_at,
            createdAt=inv.created_at or inv.issue_date,
        )
        for inv in billing_invoices
    ]

    return InvoicesResponse(
        invoices=invoices,
        total=total,
        page=page,
        pageSize=page_size,
    )


@router.get("/invoices/{invoice_id}/download")
async def download_invoice(
    invoice_id: str,
    tenant: Tenant = Depends(get_portal_tenant),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """Download an invoice PDF."""
    from fastapi.responses import Response
    from dotmac.platform.billing.invoicing.service import InvoiceService

    invoice_service = InvoiceService(db)

    # Get the invoice to verify it belongs to this tenant
    invoice = await invoice_service.get_invoice(
        tenant_id=str(tenant.id),
        invoice_id=invoice_id,
    )

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    try:
        # Generate PDF
        pdf_bytes = await invoice_service.generate_invoice_pdf(
            tenant_id=str(tenant.id),
            invoice_id=invoice_id,
        )

        filename = f"invoice_{invoice.invoice_number or invoice.invoice_id}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    except Exception as e:
        logger.error(
            "invoice.pdf_generation_failed",
            tenant_id=str(tenant.id),
            invoice_id=invoice_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate invoice PDF",
        )


# =============================================================================
# Usage History Helpers
# =============================================================================


async def _get_usage_from_audit_activity(
    db: AsyncSession, tenant_id: str, start_date: datetime
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Query AuditActivity for usage breakdown when TenantUsage metrics are empty.

    Returns:
        Tuple of (by_feature, by_user) usage data
    """
    from sqlalchemy import func
    from dotmac.platform.audit.models import AuditActivity

    # Query activity counts by activity_type (feature)
    feature_query = await db.execute(
        select(
            AuditActivity.activity_type,
            func.count(AuditActivity.id).label("count"),
        )
        .where(AuditActivity.tenant_id == tenant_id)
        .where(AuditActivity.timestamp >= start_date)
        .group_by(AuditActivity.activity_type)
        .order_by(func.count(AuditActivity.id).desc())
    )
    feature_rows = feature_query.all()

    total_calls = sum(int(row._mapping["count"]) for row in feature_rows) or 1
    by_feature = [
        {
            "feature": row.activity_type.replace(".", " ").replace("_", " ").title() if row.activity_type else "Unknown",
            "calls": int(row._mapping["count"]),
            "percentage": round((int(row._mapping["count"]) / total_calls) * 100, 1),
        }
        for row in feature_rows
    ]

    # Query activity counts by user_id
    user_query = await db.execute(
        select(
            AuditActivity.user_id,
            func.count(AuditActivity.id).label("count"),
        )
        .where(AuditActivity.tenant_id == tenant_id)
        .where(AuditActivity.timestamp >= start_date)
        .where(AuditActivity.user_id.isnot(None))
        .group_by(AuditActivity.user_id)
        .order_by(func.count(AuditActivity.id).desc())
        .limit(50)  # Top 50 users
    )
    user_rows = user_query.all()

    # Resolve user names
    user_ids_to_resolve = [row.user_id for row in user_rows if row.user_id]
    user_names: dict[str, str] = {}

    if user_ids_to_resolve:
        resolved_uuids: list[UUID] = []
        for uid in user_ids_to_resolve:
            try:
                resolved_uuids.append(UUID(uid) if isinstance(uid, str) else uid)
            except (ValueError, TypeError):
                continue

        if resolved_uuids:
            names_result = await db.execute(
                select(User.id, User.full_name, User.email)
                .where(User.id.in_(resolved_uuids))
            )
            for row in names_result.all():
                user_names[str(row.id)] = row.full_name or row.email or "Unknown"

    by_user = [
        {
            "userId": row.user_id,
            "userName": user_names.get(str(row.user_id), "Unknown"),
            "apiCalls": int(row._mapping["count"]),
            "storageUsed": 0.0,  # Not available from audit activity
        }
        for row in user_rows
    ]

    return by_feature, by_user


async def _get_usage_history_from_audit_activity(
    db: AsyncSession, tenant_id: str, start_date: datetime
) -> list[dict[str, Any]]:
    """
    Query AuditActivity for daily API call counts when TenantUsage is empty.

    Returns:
        List of {date: str, value: int} for daily activity counts
    """
    from sqlalchemy import func, cast, Date
    from dotmac.platform.audit.models import AuditActivity

    result = await db.execute(
        select(
            cast(AuditActivity.timestamp, Date).label("date"),
            func.count(AuditActivity.id).label("count"),
        )
        .where(AuditActivity.tenant_id == tenant_id)
        .where(AuditActivity.timestamp >= start_date)
        .group_by(cast(AuditActivity.timestamp, Date))
        .order_by(cast(AuditActivity.timestamp, Date))
    )
    rows = result.all()

    return [
        {
            "date": (row._mapping["date"].isoformat() if row._mapping["date"] else ""),
            "value": int(row._mapping["count"]),
        }
        for row in rows
    ]


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
    from datetime import timedelta
    from sqlalchemy import select
    from dotmac.platform.tenant.models import TenantUsage

    # Calculate percentages
    user_percent = (tenant.current_users / tenant.max_users * 100) if tenant.max_users > 0 else 0
    api_percent = (tenant.current_api_calls / tenant.max_api_calls_per_month * 100) if tenant.max_api_calls_per_month > 0 else 0
    storage_percent = (tenant.current_storage_gb / tenant.max_storage_gb * 100) if tenant.max_storage_gb > 0 else 0

    # Calculate period start date
    period_days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}.get(period, 30)
    start_date = datetime.now(UTC) - timedelta(days=period_days)

    # Query usage history from TenantUsage table
    api_calls_history: list[dict[str, Any]] = []
    storage_history: list[dict[str, Any]] = []
    users_history: list[dict[str, Any]] = []
    bandwidth_history: list[dict[str, Any]] = []

    try:
        result = await db.execute(
            select(TenantUsage)
            .where(TenantUsage.tenant_id == str(tenant.id))
            .where(TenantUsage.period_start >= start_date)
            .order_by(TenantUsage.period_start)
        )
        usage_records = result.scalars().all()

        for record in usage_records:
            date_str = record.period_start.isoformat() if record.period_start else ""
            api_calls_history.append({"date": date_str, "value": record.api_calls})
            storage_history.append({"date": date_str, "value": float(record.storage_gb) * 1024})  # Convert to MB
            users_history.append({"date": date_str, "value": record.active_users})
            bandwidth_history.append({"date": date_str, "value": float(record.bandwidth_gb)})

        # Fallback to AuditActivity for API calls history if TenantUsage is empty
        if not api_calls_history:
            api_calls_history = await _get_usage_history_from_audit_activity(
                db, str(tenant.id), start_date
            )
    except Exception as e:
        logger.warning("Failed to fetch usage history", error=str(e))

    return UsageMetrics(
        apiCalls=UsageMetric(
            current=float(tenant.current_api_calls),
            limit=float(tenant.max_api_calls_per_month),
            unit="calls",
            percentUsed=round(api_percent, 1),
            history=api_calls_history,
        ),
        storage=UsageMetric(
            current=float(tenant.current_storage_gb * 1024),  # MB
            limit=float(tenant.max_storage_gb * 1024),
            unit="MB",
            percentUsed=round(storage_percent, 1),
            history=storage_history,
        ),
        users=UsageMetric(
            current=float(tenant.current_users),
            limit=float(tenant.max_users),
            unit="users",
            percentUsed=round(user_percent, 1),
            history=users_history,
        ),
        bandwidth=UsageMetric(
            current=0.0,
            limit=50.0,
            unit="GB",
            percentUsed=0.0,
            history=bandwidth_history,
        ),
    )


@router.get("/usage/breakdown", response_model=UsageBreakdown)
async def get_usage_breakdown(
    tenant: Tenant = Depends(get_portal_tenant),
    db: AsyncSession = Depends(get_async_session),
    period: str = Query("30d", description="Period: 7d, 30d, 90d, 1y"),
) -> UsageBreakdown:
    """Get detailed usage breakdown."""
    from datetime import timedelta
    from sqlalchemy import select
    from dotmac.platform.tenant.models import TenantUsage

    period_days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}.get(period, 30)
    start_date = datetime.now(UTC) - timedelta(days=period_days)

    result = await db.execute(
        select(TenantUsage)
        .where(TenantUsage.tenant_id == str(tenant.id))
        .where(TenantUsage.period_start >= start_date)
        .order_by(TenantUsage.period_start)
    )
    usage_records = result.scalars().all()

    feature_calls: dict[str, float] = {}
    user_stats: dict[str, dict[str, Any]] = {}

    def _add_feature(feature: str, calls: float) -> None:
        if not feature:
            return
        feature_calls[feature] = feature_calls.get(feature, 0) + calls

    def _add_user(
        user_id: str,
        user_name: str | None,
        api_calls: float,
        storage_mb: float,
    ) -> None:
        if not user_id:
            return
        entry = user_stats.setdefault(
            user_id,
            {"userId": user_id, "userName": user_name, "apiCalls": 0.0, "storageUsed": 0.0},
        )
        if user_name and not entry.get("userName"):
            entry["userName"] = user_name
        entry["apiCalls"] += api_calls
        entry["storageUsed"] += storage_mb

    for record in usage_records:
        metrics = record.metrics or {}
        feature_entries = (
            metrics.get("by_feature")
            or metrics.get("byFeature")
            or metrics.get("feature_usage")
            or metrics.get("features")
        )
        if isinstance(feature_entries, list):
            for item in feature_entries:
                if not isinstance(item, dict):
                    continue
                feature = item.get("feature") or item.get("name") or item.get("key")
                calls = item.get("calls") or item.get("api_calls") or item.get("count") or 0
                _add_feature(str(feature), float(calls))
        elif isinstance(feature_entries, dict):
            for feature, calls in feature_entries.items():
                if isinstance(calls, dict):
                    calls_value = calls.get("calls") or calls.get("api_calls") or calls.get("count") or 0
                    _add_feature(str(feature), float(calls_value))
                elif isinstance(calls, (int, float)):
                    _add_feature(str(feature), float(calls))

        def _coerce_float(value: Any) -> float:
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0.0

        user_entries = (
            metrics.get("by_user")
            or metrics.get("byUser")
            or metrics.get("user_usage")
            or metrics.get("users")
        )
        if isinstance(user_entries, list):
            for item in user_entries:
                if not isinstance(item, dict):
                    continue
                user_id = item.get("userId") or item.get("user_id") or item.get("id") or item.get("email")
                user_name = item.get("userName") or item.get("name") or item.get("email")
                api_calls = item.get("apiCalls") or item.get("api_calls") or item.get("calls") or 0
                storage_mb = 0.0
                if item.get("storage_gb") is not None:
                    storage_mb = _coerce_float(item.get("storage_gb")) * 1024
                elif item.get("storageUsed") is not None:
                    storage_mb = _coerce_float(item.get("storageUsed"))
                elif item.get("storage_used") is not None:
                    storage_mb = _coerce_float(item.get("storage_used"))
                elif item.get("storage_mb") is not None:
                    storage_mb = _coerce_float(item.get("storage_mb"))
                _add_user(str(user_id), str(user_name) if user_name else None, float(api_calls), storage_mb)
        elif isinstance(user_entries, dict):
            for user_id, data in user_entries.items():
                if isinstance(data, dict):
                    user_name = data.get("userName") or data.get("name") or data.get("email")
                    api_calls = data.get("apiCalls") or data.get("api_calls") or data.get("calls") or 0
                    storage_mb = 0.0
                    if data.get("storage_gb") is not None:
                        storage_mb = _coerce_float(data.get("storage_gb")) * 1024
                    elif data.get("storageUsed") is not None:
                        storage_mb = _coerce_float(data.get("storageUsed"))
                    elif data.get("storage_used") is not None:
                        storage_mb = _coerce_float(data.get("storage_used"))
                    elif data.get("storage_mb") is not None:
                        storage_mb = _coerce_float(data.get("storage_mb"))
                    _add_user(str(user_id), str(user_name) if user_name else None, float(api_calls), storage_mb)
                elif isinstance(data, (int, float)):
                    _add_user(str(user_id), None, float(data), 0.0)

    # Fill missing user names from the users table when possible
    unresolved_ids = [
        user_id for user_id, entry in user_stats.items() if not entry.get("userName")
    ]
    if unresolved_ids:
        resolved_ids: list[UUID] = []
        for user_id in unresolved_ids:
            try:
                resolved_ids.append(UUID(user_id))
            except ValueError:
                continue

        if resolved_ids:
            user_result = await db.execute(
                select(User.id, User.full_name, User.email)
                .where(User.tenant_id == str(tenant.id))
                .where(User.id.in_(resolved_ids))
            )
            user_rows = user_result.all()
            user_names = {
                str(row.id): row.full_name or row.email for row in user_rows
            }
            for user_id, entry in user_stats.items():
                if not entry.get("userName"):
                    entry["userName"] = user_names.get(user_id)

    total_calls = sum(feature_calls.values())
    by_feature = [
        {
            "feature": feature,
            "calls": int(calls),
            "percentage": round((calls / total_calls) * 100, 1) if total_calls else 0,
        }
        for feature, calls in sorted(feature_calls.items(), key=lambda item: item[1], reverse=True)
    ]
    by_user = [
        {
            "userId": entry["userId"],
            "userName": entry.get("userName") or "Unknown",
            "apiCalls": int(entry["apiCalls"]),
            "storageUsed": round(entry["storageUsed"], 1),
        }
        for entry in sorted(user_stats.values(), key=lambda item: item["apiCalls"], reverse=True)
    ]

    # Fallback to AuditActivity if TenantUsage has no breakdown data
    if not by_feature and not by_user:
        try:
            by_feature, by_user = await _get_usage_from_audit_activity(
                db, str(tenant.id), start_date
            )
        except Exception as e:
            logger.warning("Failed to fetch usage from audit activity", error=str(e))

    return UsageBreakdown(
        byFeature=by_feature,
        byUser=by_user,
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
    from dotmac.platform.auth.api_keys_router import _list_user_api_keys

    # Get all keys for the current user - now queries database via session
    all_keys = await _list_user_api_keys(current_user.user_id, session=db)

    # Filter to only keys for this tenant
    tenant_keys = [
        ApiKey(
            id=key.get("id", ""),
            name=key.get("name", "Unknown"),
            prefix=key.get("prefix") or key.get("id", "")[:8],
            lastUsedAt=key.get("last_used_at"),
            createdAt=datetime.fromisoformat(key["created_at"]) if key.get("created_at") else datetime.utcnow(),
            createdBy=key.get("user_id", current_user.user_id),
        )
        for key in all_keys
        if key.get("tenant_id") == str(tenant.id) and key.get("is_active", True)
    ]

    return tenant_keys


@router.post("/api-keys", response_model=CreateApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    data: CreateApiKeyRequest,
    user_tenant: tuple[UserInfo, Tenant] = Depends(require_portal_admin),
    db: AsyncSession = Depends(get_async_session),
) -> CreateApiKeyResponse:
    """Create a new API key."""
    from dotmac.platform.auth.api_keys_router import _enhanced_create_api_key

    current_user, tenant = user_tenant

    # Create the API key using the auth service - now persists to database
    api_key, key_id = await _enhanced_create_api_key(
        user_id=current_user.user_id,
        name=data.name,
        tenant_id=str(tenant.id),
        session=db,
    )
    await db.commit()

    prefix = api_key[:8]
    now = datetime.now(UTC)

    logger.info(
        "tenant.api_key_created",
        tenant_id=tenant.id,
        key_name=data.name,
        key_id=key_id,
        created_by=current_user.user_id,
    )

    return CreateApiKeyResponse(
        id=key_id,
        name=data.name,
        secretKey=api_key,
        prefix=prefix,
        createdAt=now,
        apiKey={
            "id": key_id,
            "name": data.name,
            "prefix": prefix,
            "createdAt": now.isoformat(),
            "createdBy": current_user.user_id,
        },
    )


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: str,
    user_tenant: tuple[UserInfo, Tenant] = Depends(require_portal_admin),
    db: AsyncSession = Depends(get_async_session),
) -> None:
    """Delete an API key."""
    from dotmac.platform.auth.api_keys_router import _revoke_api_key_by_id

    current_user, tenant = user_tenant

    # Revoke the API key - now soft-deletes in database
    success = await _revoke_api_key_by_id(key_id, session=db)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key {key_id} not found",
        )

    await db.commit()

    logger.info(
        "tenant.api_key_deleted",
        tenant_id=tenant.id,
        key_id=key_id,
        deleted_by=current_user.user_id,
    )

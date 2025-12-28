"""
User management API router.

Provides REST endpoints for user management operations.
"""

from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.core import UserInfo
from dotmac.platform.auth.dependencies import get_current_user
from dotmac.platform.auth.platform_admin import is_platform_admin
from dotmac.platform.auth.rbac_dependencies import require_permission
from dotmac.platform.db import get_session_dependency
from dotmac.platform.tenant import get_current_tenant_id
from dotmac.platform.user_management.service import UserService

logger = structlog.get_logger(__name__)

def require_authorization_header(request: Request) -> None:
    """Ensure an Authorization header is present for protected endpoints."""
    if not request.headers.get("Authorization"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )


# Create router
user_router = APIRouter(
    prefix="/users",
    dependencies=[Depends(require_authorization_header)],
)

TARGET_TENANT_HEADER = "X-Target-Tenant-ID"
TARGET_TENANT_QUERY_PARAMS = ("tenant_id", "target_tenant_id")


def _tenant_scope_from_user(user: UserInfo | None) -> str | None:
    """Return tenant scope for the given user."""
    if user is None:
        return None
    if user.is_platform_admin:
        return None
    return user.tenant_id


def _resolve_target_tenant(
    actor: UserInfo,
    request: Request | None = None,
    override_tenant: str | None = None,
    *,
    require_tenant: bool = True,
) -> str | None:
    """
    Resolve tenant for administrative operations.

    Order of precedence:
        1. Explicit override (internal callers)
        2. Tenant context set by middleware
        3. Actor's assigned tenant
        4. Platform admin header/query overrides
        5. Platform admin fallback (cross-tenant) when allowed
    """
    if override_tenant:
        return override_tenant

    actor_tenant = getattr(actor, "tenant_id", None)
    if isinstance(actor_tenant, str) and actor_tenant.strip():
        return actor_tenant

    context_tenant = get_current_tenant_id()
    if isinstance(context_tenant, str) and context_tenant.strip():
        return context_tenant

    if request is not None and is_platform_admin(actor):
        header_candidate = request.headers.get(TARGET_TENANT_HEADER)
        if header_candidate:
            return header_candidate
        for query_key in TARGET_TENANT_QUERY_PARAMS:
            query_candidate = request.query_params.get(query_key)
            if query_candidate:
                return query_candidate

    if require_tenant:
        if is_platform_admin(actor):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Specify tenant via X-Target-Tenant-ID header or tenant_id "
                    "query parameter for this operation."
                ),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context not found for user management operation.",
        )

    if is_platform_admin(actor):
        return None

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Tenant context not found for user management operation.",
    )


# ========================================
# Request/Response Models
# ========================================


class UserCreateRequest(BaseModel):  # BaseModel resolves to Any in isolation
    """User creation request model."""

    model_config = ConfigDict()

    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password")
    full_name: str | None = Field(None, description="Full name")
    roles: list[str] = Field(default_factory=list, description="User roles")
    is_active: bool = Field(True, description="Is user active")


class UserUpdateRequest(BaseModel):  # BaseModel resolves to Any in isolation
    """User update request model."""

    model_config = ConfigDict()

    email: EmailStr | None = Field(None, description="Email address")
    full_name: str | None = Field(None, description="Full name")
    roles: list[str] | None = Field(None, description="User roles")
    is_active: bool | None = Field(None, description="Is user active")


class UserResponse(BaseModel):  # BaseModel resolves to Any in isolation
    """User response model."""

    model_config = ConfigDict()

    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    full_name: str | None = Field(None, description="Full name")
    roles: list[str] = Field(default_factory=list, description="User roles")
    is_active: bool = Field(..., description="Is user active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_login: datetime | None = Field(None, description="Last login timestamp")


class PasswordChangeRequest(BaseModel):  # BaseModel resolves to Any in isolation
    """Password change request model."""

    model_config = ConfigDict()

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Confirm new password")


class UserListResponse(BaseModel):  # BaseModel resolves to Any in isolation
    """User list response model."""

    model_config = ConfigDict()

    users: list[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page")
    per_page: int = Field(..., description="Items per page")


class UserBulkActionRequest(BaseModel):
    """Request model for bulk user actions."""

    model_config = ConfigDict()

    user_ids: list[str] = Field(..., min_length=1, description="List of user IDs to operate on")


class UserBulkDeleteRequest(UserBulkActionRequest):
    """Request model for bulk user deletion."""

    hard_delete: bool = Field(default=False, description="If true, permanently delete users")


class UserBulkActionResponse(BaseModel):
    """Response model for bulk user actions."""

    model_config = ConfigDict()

    success_count: int = Field(..., description="Number of users successfully processed")
    errors: list[dict[str, str]] = Field(
        default_factory=list, description="List of errors for failed operations"
    )


# ========================================
# Dependency Injection
# ========================================


async def get_user_service(
    session: Annotated[AsyncSession, Depends(get_session_dependency)],
) -> UserService:
    """Get user service with database session."""
    return UserService(session)


# ========================================
# Dashboard Response Models
# ========================================


class UserDashboardSummary(BaseModel):
    """Summary statistics for user dashboard"""

    model_config = ConfigDict()

    total_users: int
    active_users: int
    inactive_users: int
    verified_users: int
    unverified_users: int
    new_this_month: int
    active_today: int
    growth_rate_pct: float


class UserChartDataPoint(BaseModel):
    """Single data point for charts"""

    model_config = ConfigDict()

    label: str
    value: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class UserDashboardCharts(BaseModel):
    """Chart data for user dashboard"""

    model_config = ConfigDict()

    user_growth: list[UserChartDataPoint]
    users_by_role: list[UserChartDataPoint]
    users_by_tenant: list[UserChartDataPoint]
    login_activity: list[UserChartDataPoint]


class UserDashboardAlert(BaseModel):
    """Alert item for dashboard"""

    model_config = ConfigDict()

    type: str
    title: str
    message: str
    count: int = 0
    action_url: str | None = None


class UserDashboardActivity(BaseModel):
    """Recent activity item"""

    model_config = ConfigDict()

    id: str
    type: str
    user_email: str
    description: str
    timestamp: datetime


class UserDashboardResponse(BaseModel):
    """Consolidated user dashboard response"""

    model_config = ConfigDict()

    summary: UserDashboardSummary
    charts: UserDashboardCharts
    alerts: list[UserDashboardAlert]
    recent_activity: list[UserDashboardActivity]
    generated_at: datetime


# ========================================
# Dashboard Endpoint
# ========================================


@user_router.get(
    "/dashboard",
    response_model=UserDashboardResponse,
    summary="Get user dashboard data",
    description="Returns consolidated user metrics, charts, and alerts for the dashboard",
)
async def get_user_dashboard(
    period_months: int = Query(6, ge=1, le=24, description="Months of trend data"),
    user_service: UserService = Depends(get_user_service),
    current_user: UserInfo = Depends(require_permission("users.read")),
) -> UserDashboardResponse:
    """
    Get consolidated user dashboard data including:
    - Summary statistics (total, active, verified)
    - Chart data (growth trends, role distribution)
    - Alerts (unverified users, inactive accounts)
    - Recent activity
    """
    from datetime import timedelta, timezone
    from sqlalchemy import func, case, select

    try:
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Get session from service
        session = user_service._session

        from .models import User

        # ========== SUMMARY STATS ==========
        status_counts = await session.execute(
            select(
                func.count(User.id).label("total"),
                func.sum(case((User.is_active == True, 1), else_=0)).label("active"),
                func.sum(case((User.is_active == False, 1), else_=0)).label("inactive"),
                func.sum(case((User.is_verified == True, 1), else_=0)).label("verified"),
                func.sum(case((User.is_verified == False, 1), else_=0)).label("unverified"),
            )
        )
        counts = status_counts.one()

        # New users this month
        new_this_month = await session.execute(
            select(func.count(User.id)).where(User.created_at >= month_start)
        )
        new_count = new_this_month.scalar() or 0

        # Active today (logged in today)
        active_today = await session.execute(
            select(func.count(User.id)).where(User.last_login >= today_start)
        )
        active_today_count = active_today.scalar() or 0

        # Growth rate
        last_month_total = await session.execute(
            select(func.count(User.id)).where(User.created_at < month_start)
        )
        last_month_count = last_month_total.scalar() or 1
        growth_rate = (new_count / last_month_count) * 100 if last_month_count > 0 else 0

        summary = UserDashboardSummary(
            total_users=counts.total or 0,
            active_users=counts.active or 0,
            inactive_users=counts.inactive or 0,
            verified_users=counts.verified or 0,
            unverified_users=counts.unverified or 0,
            new_this_month=new_count,
            active_today=active_today_count,
            growth_rate_pct=round(growth_rate, 2),
        )

        # ========== CHART DATA ==========
        # User growth trend
        user_growth = []
        for i in range(period_months - 1, -1, -1):
            month_date = (now - timedelta(days=i * 30)).replace(day=1)
            next_month = (month_date + timedelta(days=32)).replace(day=1)

            month_count = await session.execute(
                select(func.count(User.id)).where(
                    User.created_at >= month_date,
                    User.created_at < next_month,
                )
            )
            user_growth.append(UserChartDataPoint(
                label=month_date.strftime("%b %Y"),
                value=month_count.scalar() or 0,
            ))

        # Users by tenant
        tenant_counts = await session.execute(
            select(User.tenant_id, func.count(User.id)).group_by(User.tenant_id).limit(10)
        )
        users_by_tenant = [
            UserChartDataPoint(label=row[0] or "No Tenant", value=row[1])
            for row in tenant_counts.all()
        ]

        # Login activity (last 7 days)
        login_activity = []
        for i in range(6, -1, -1):
            day_date = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            next_day = day_date + timedelta(days=1)

            day_logins = await session.execute(
                select(func.count(User.id)).where(
                    User.last_login >= day_date,
                    User.last_login < next_day,
                )
            )
            login_activity.append(UserChartDataPoint(
                label=day_date.strftime("%a"),
                value=day_logins.scalar() or 0,
            ))

        charts = UserDashboardCharts(
            user_growth=user_growth,
            users_by_role=[],  # Would need to join with roles table
            users_by_tenant=users_by_tenant,
            login_activity=login_activity,
        )

        # ========== ALERTS ==========
        alerts = []

        if counts.unverified and counts.unverified > 0:
            alerts.append(UserDashboardAlert(
                type="warning",
                title="Unverified Users",
                message=f"{counts.unverified} user(s) have not verified their email",
                count=counts.unverified,
                action_url="/users?verified=false",
            ))

        # Inactive users (no login in 30 days)
        inactive_30d = await session.execute(
            select(func.count(User.id)).where(
                User.is_active == True,
                User.last_login < now - timedelta(days=30),
            )
        )
        inactive_count = inactive_30d.scalar() or 0
        if inactive_count > 5:
            alerts.append(UserDashboardAlert(
                type="info",
                title="Inactive Users",
                message=f"{inactive_count} active users haven't logged in for 30+ days",
                count=inactive_count,
                action_url="/users?inactive=true",
            ))

        # ========== RECENT ACTIVITY ==========
        recent_users = await session.execute(
            select(User).order_by(User.created_at.desc()).limit(10)
        )
        recent_activity = [
            UserDashboardActivity(
                id=str(u.id),
                type="created",
                user_email=u.email or "unknown",
                description=f"User '{u.email}' was created",
                timestamp=u.created_at,
            )
            for u in recent_users.scalars().all()
        ]

        return UserDashboardResponse(
            summary=summary,
            charts=charts,
            alerts=alerts,
            recent_activity=recent_activity,
            generated_at=now,
        )

    except Exception as e:
        logger.error("Failed to generate user dashboard", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate user dashboard: {str(e)}",
        )


# ========================================
# Endpoints
# ========================================


@user_router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: UserInfo = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Get current user's profile.

    Requires authentication.
    """
    tenant_scope = _tenant_scope_from_user(current_user)
    user = await user_service.get_user_by_id(current_user.user_id, tenant_id=tenant_scope)
    if not user and tenant_scope is not None:
        user = await user_service.get_user_by_id(current_user.user_id, tenant_id=None)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")

    return UserResponse(**user.to_dict())


@user_router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    updates: UserUpdateRequest,
    current_user: UserInfo = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Update current user's profile.

    Requires authentication.
    """
    # Users can't change their own roles
    update_data = updates.model_dump(exclude_unset=True, exclude={"roles"})

    tenant_scope = _tenant_scope_from_user(current_user)
    updated_user = await user_service.update_user(
        user_id=current_user.user_id,
        tenant_id=tenant_scope,
        **update_data,
    )
    if not updated_user and tenant_scope is not None:
        updated_user = await user_service.update_user(
            user_id=current_user.user_id,
            tenant_id=None,
            **update_data,
        )
    if not updated_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserResponse(**updated_user.to_dict())


@user_router.post("/me/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: UserInfo = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> dict[str, Any]:
    """
    Change current user's password.

    Requires authentication.
    """
    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match"
        )

    tenant_scope = _tenant_scope_from_user(current_user)
    success = await user_service.change_password(
        user_id=current_user.user_id,
        current_password=request.current_password,
        new_password=request.new_password,
        tenant_id=tenant_scope,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to change password - current password may be incorrect",
        )

    return {"message": "Password changed successfully"}


@user_router.get("", response_model=UserListResponse)
async def list_users(
    request: Request,
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(100, ge=1, le=1000, description="Limit records"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    role: str | None = Query(None, description="Filter by role"),
    search: str | None = Query(None, description="Search term"),
    admin_user: UserInfo = Depends(require_permission("users.read")),
    user_service: UserService = Depends(get_user_service),
) -> UserListResponse:
    """
    List all users.

    Requires admin role.
    """
    tenant_id = _resolve_target_tenant(admin_user, request, require_tenant=False)
    require_tenant_flag = tenant_id is not None

    users, total = await user_service.list_users(
        skip=skip,
        limit=limit,
        is_active=is_active,
        role=role,
        search=search,
        tenant_id=tenant_id,
        require_tenant=require_tenant_flag,
    )

    return UserListResponse(
        users=[UserResponse(**u.to_dict()) for u in users],
        total=total,
        page=skip // limit + 1,
        per_page=limit,
    )


@user_router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateRequest,
    request: Request,
    admin_user: UserInfo = Depends(require_permission("users.create")),
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Create a new user.

    Requires admin role.
    """
    target_tenant = _resolve_target_tenant(admin_user, request, require_tenant=True)

    try:
        new_user = await user_service.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            roles=user_data.roles,
            is_active=user_data.is_active,
            tenant_id=target_tenant,
        )
        return UserResponse(**new_user.to_dict())
    except (IntegrityError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@user_router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    request: Request,
    admin_user: UserInfo = Depends(require_permission("users.read")),
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Get a specific user by ID.

    Requires admin role.
    """
    target_tenant = _resolve_target_tenant(admin_user, request, require_tenant=False)
    user = await user_service.get_user_by_id(user_id, tenant_id=target_tenant)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
        )

    return UserResponse(**user.to_dict())


@user_router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    updates: UserUpdateRequest,
    request: Request,
    admin_user: UserInfo = Depends(require_permission("users.update")),
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Update a user.

    Requires admin role.
    """
    update_data = updates.model_dump(exclude_unset=True)
    target_tenant = _resolve_target_tenant(admin_user, request, require_tenant=True)

    try:
        updated_user = await user_service.update_user(
            user_id=user_id,
            tenant_id=target_tenant,
            **update_data,
        )
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
            )

        return UserResponse(**updated_user.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@user_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    request: Request,
    admin_user: UserInfo = Depends(require_permission("users.delete")),
    user_service: UserService = Depends(get_user_service),
) -> None:
    """
    Delete a user.

    Requires admin role.
    """
    target_tenant = _resolve_target_tenant(admin_user, request, require_tenant=True)

    success = await user_service.delete_user(user_id, tenant_id=target_tenant)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
        )


@user_router.post("/{user_id}/disable", response_model=UserResponse)
async def disable_user(
    user_id: UUID,
    request: Request,
    admin_user: UserInfo = Depends(require_permission("users.update")),
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Disable a user account.

    Requires admin role.
    """
    target_tenant = _resolve_target_tenant(admin_user, request, require_tenant=True)
    updated_user = await user_service.update_user(
        user_id=user_id,
        tenant_id=target_tenant,
        is_active=False,
    )
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
        )

    return UserResponse(**updated_user.to_dict())


@user_router.post("/{user_id}/enable", response_model=UserResponse)
async def enable_user(
    user_id: UUID,
    request: Request,
    admin_user: UserInfo = Depends(require_permission("users.update")),
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Enable a user account.

    Requires admin role.
    """
    target_tenant = _resolve_target_tenant(admin_user, request, require_tenant=True)
    updated_user = await user_service.update_user(
        user_id=user_id,
        tenant_id=target_tenant,
        is_active=True,
    )
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
        )

    return UserResponse(**updated_user.to_dict())


@user_router.post("/{user_id}/resend-verification")
async def resend_user_verification(
    user_id: UUID,
    request: Request,
    admin_user: UserInfo = Depends(require_permission("users.update")),
    user_service: UserService = Depends(get_user_service),
) -> dict[str, Any]:
    """
    Resend verification email for a user.

    Requires admin role.
    """
    from dotmac.platform.auth.email_verification import send_verification_email

    target_tenant = _resolve_target_tenant(admin_user, request, require_tenant=True)
    user = await user_service.get_user_by_id(user_id=user_id, tenant_id=target_tenant)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User email is already verified",
        )

    try:
        await send_verification_email(
            session=user_service.session,
            user=user,
            email=user.email,
            include_email_in_link=True,
        )
        return {"message": f"Verification email sent to {user.email}"}
    except Exception:
        logger.error("Failed to resend verification email", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email",
        )


# ========================================
# Bulk Operations
# ========================================


@user_router.post("/bulk/delete", status_code=status.HTTP_200_OK)
async def bulk_delete_users(
    bulk_delete: UserBulkDeleteRequest,
    request: Request,
    admin_user: UserInfo = Depends(require_permission("users.delete")),
    user_service: UserService = Depends(get_user_service),
) -> UserBulkActionResponse:
    """
    Bulk delete multiple users.

    Requires admin role with users.delete permission.
    """
    target_tenant = _resolve_target_tenant(admin_user, request, require_tenant=True)
    success_count = 0
    errors: list[dict[str, str]] = []

    for user_id in bulk_delete.user_ids:
        try:
            if bulk_delete.hard_delete:
                success = await user_service.delete_user(
                    user_id=user_id,
                    tenant_id=target_tenant,
                )
                if success:
                    success_count += 1
                else:
                    errors.append({"user_id": user_id, "error": "User not found"})
                continue

            user = await user_service.get_user_by_id(user_id, tenant_id=target_tenant)
            if not user:
                errors.append({"user_id": user_id, "error": "User not found"})
                continue

            metadata = dict(user.metadata_ or {})
            metadata["deleted_at"] = datetime.now(UTC).isoformat()
            metadata["deleted_by"] = admin_user.user_id

            updated = await user_service.update_user(
                user_id=user_id,
                tenant_id=target_tenant,
                is_active=False,
                metadata=metadata,
            )
            if updated:
                success_count += 1
            else:
                errors.append({"user_id": user_id, "error": "User not found"})
        except Exception as exc:
            errors.append({"user_id": user_id, "error": str(exc)})
            logger.error("Error deleting user", user_id=user_id, error=str(exc))

    return UserBulkActionResponse(success_count=success_count, errors=errors)


@user_router.post("/bulk/suspend", status_code=status.HTTP_200_OK)
async def bulk_suspend_users(
    bulk_action: UserBulkActionRequest,
    request: Request,
    admin_user: UserInfo = Depends(require_permission("users.update")),
    user_service: UserService = Depends(get_user_service),
) -> UserBulkActionResponse:
    """
    Bulk suspend (disable) multiple users.

    Requires admin role with users.update permission.
    """
    target_tenant = _resolve_target_tenant(admin_user, request, require_tenant=True)
    success_count = 0
    errors: list[dict[str, str]] = []

    for user_id in bulk_action.user_ids:
        try:
            updated_user = await user_service.update_user(
                user_id=user_id,
                tenant_id=target_tenant,
                is_active=False,
            )
            if updated_user:
                success_count += 1
            else:
                errors.append({"user_id": user_id, "error": "User not found"})
        except Exception as exc:
            errors.append({"user_id": user_id, "error": str(exc)})
            logger.error("Error suspending user", user_id=user_id, error=str(exc))

    return UserBulkActionResponse(success_count=success_count, errors=errors)


@user_router.post("/bulk/activate", status_code=status.HTTP_200_OK)
async def bulk_activate_users(
    bulk_action: UserBulkActionRequest,
    request: Request,
    admin_user: UserInfo = Depends(require_permission("users.update")),
    user_service: UserService = Depends(get_user_service),
) -> UserBulkActionResponse:
    """
    Bulk activate (enable) multiple users.

    Requires admin role with users.update permission.
    """
    target_tenant = _resolve_target_tenant(admin_user, request, require_tenant=True)
    success_count = 0
    errors: list[dict[str, str]] = []

    for user_id in bulk_action.user_ids:
        try:
            updated_user = await user_service.update_user(
                user_id=user_id,
                tenant_id=target_tenant,
                is_active=True,
            )
            if updated_user:
                success_count += 1
            else:
                errors.append({"user_id": user_id, "error": "User not found"})
        except Exception as exc:
            errors.append({"user_id": user_id, "error": str(exc)})
            logger.error("Error activating user", user_id=user_id, error=str(exc))

    return UserBulkActionResponse(success_count=success_count, errors=errors)


@user_router.post("/bulk/resend-verification", status_code=status.HTTP_200_OK)
async def bulk_resend_verification(
    bulk_action: UserBulkActionRequest,
    request: Request,
    admin_user: UserInfo = Depends(require_permission("users.update")),
    user_service: UserService = Depends(get_user_service),
) -> UserBulkActionResponse:
    """
    Bulk resend verification emails for multiple users.

    Only sends to users who are not already verified.
    Requires admin role with users.update permission.
    """
    from dotmac.platform.auth.email_verification import send_verification_email

    target_tenant = _resolve_target_tenant(admin_user, request, require_tenant=True)
    success_count = 0
    errors: list[dict[str, str]] = []

    for user_id in bulk_action.user_ids:
        try:
            user = await user_service.get_user_by_id(user_id, tenant_id=target_tenant)
            if not user:
                errors.append({"user_id": user_id, "error": "User not found"})
                continue

            if user.is_verified:
                errors.append({"user_id": user_id, "error": "Already verified"})
                continue

            await send_verification_email(
                session=user_service.session,
                user=user,
                email=user.email,
                include_email_in_link=True,
            )
            success_count += 1
        except Exception as exc:
            errors.append({"user_id": user_id, "error": str(exc)})
            logger.error("Error resending verification", user_id=user_id, error=str(exc))

    return UserBulkActionResponse(success_count=success_count, errors=errors)


@user_router.post("/export")
async def export_users(
    request: Request,
    format: str = Query("csv", description="Export format: csv or json"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    role: str | None = Query(None, description="Filter by role"),
    admin_user: UserInfo = Depends(require_permission("users.read")),
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """
    Export users to CSV or JSON.

    Requires admin role with users.read permission.
    """
    import csv
    import io
    import json
    from fastapi.responses import StreamingResponse

    target_tenant = _resolve_target_tenant(admin_user, request, require_tenant=False)

    # Get all users (no pagination for export)
    users, _ = await user_service.list_users(
        skip=0,
        limit=10000,  # Reasonable limit
        is_active=is_active,
        role=role,
        tenant_id=target_tenant,
        require_tenant=target_tenant is not None,
    )

    if format.lower() == "json":
        user_data = [u.to_dict() for u in users]
        content = json.dumps(user_data, default=str, indent=2)
        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="users_export.json"'},
        )

    # Default to CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        "user_id", "username", "email", "full_name", "roles",
        "is_active", "is_verified", "created_at", "last_login"
    ])

    # Data rows
    for user in users:
        user_dict = user.to_dict()
        writer.writerow([
            user_dict.get("user_id", ""),
            user_dict.get("username", ""),
            user_dict.get("email", ""),
            user_dict.get("full_name", ""),
            ",".join(user_dict.get("roles", [])),
            user_dict.get("is_active", False),
            getattr(user, "is_verified", False),
            user_dict.get("created_at", ""),
            user_dict.get("last_login", ""),
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="users_export.csv"'},
    )


# Export router
__all__ = ["user_router"]

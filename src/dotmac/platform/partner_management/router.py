"""
Partner Management API Router.

Provides RESTful endpoints for partner management operations.
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated, Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.core import UserInfo
from dotmac.platform.auth.dependencies import get_current_user
from dotmac.platform.auth.platform_admin import require_platform_admin
from dotmac.platform.auth.core import hash_password
from dotmac.platform.db import get_session_dependency
from dotmac.platform.partner_management import (
    commission_rules_router,
    portal_router,
    revenue_router,
)
from dotmac.platform.partner_management.models import (
    Partner,
    PartnerApplication,
    PartnerCommissionEvent,
    PartnerInvitationStatus,
    PartnerStatus,
    PartnerUser,
    PartnerUserInvitation,
    ReferralLead,
    PartnerApplicationStatus,
)
from dotmac.platform.partner_management.schemas import (
    AcceptPartnerInvitationRequest,
    PartnerAccountCreate,
    PartnerAccountResponse,
    PartnerApplicationCreate,
    PartnerApplicationListResponse,
    PartnerApplicationRejectRequest,
    PartnerApplicationResponse,
    PartnerCommissionEventCreate,
    PartnerCommissionEventListResponse,
    PartnerCommissionEventResponse,
    PartnerCreate,
    PartnerListResponse,
    PartnerResponse,
    PartnerUpdate,
    PartnerUserCreate,
    PartnerUserResponse,
    PartnerUserUpdate,
    ReferralLeadCreate,
    ReferralLeadListResponse,
    ReferralLeadResponse,
    ReferralLeadUpdate,
)
from dotmac.platform.partner_management.service import PartnerService
from dotmac.platform.user_management.models import User

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/partners", tags=["Partner Management"])

# Include partner portal sub-routers
router.include_router(portal_router.router)
router.include_router(revenue_router.router)
router.include_router(commission_rules_router.router)


def _convert_partner_to_response(partner: Any) -> PartnerResponse:
    """Convert Partner model to PartnerResponse, handling metadata_ field."""
    partner_dict: dict[str, Any] = {}
    for key in PartnerResponse.model_fields:
        if key == "metadata":
            partner_dict["metadata"] = partner.metadata_ if hasattr(partner, "metadata_") else {}
        elif key == "total_tenants":
            partner_dict["total_tenants"] = getattr(partner, "total_customers", 0)
        elif hasattr(partner, key):
            partner_dict[key] = getattr(partner, key)
    return PartnerResponse.model_validate(partner_dict)


# Dependency for partner service
async def get_partner_service(
    session: AsyncSession = Depends(get_session_dependency),
) -> PartnerService:
    """Get partner service instance."""
    return PartnerService(session)


def require_authorization_header(request: Request) -> None:
    """Ensure an Authorization header is present for protected endpoints."""
    if not request.headers.get("Authorization"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )


# =============================================================================
# Partner Application Endpoints (Public + Admin)
# =============================================================================


@router.post("/apply", response_model=PartnerApplicationResponse, status_code=status.HTTP_201_CREATED)
async def submit_partner_application(
    data: PartnerApplicationCreate,
    service: Annotated[PartnerService, Depends(get_partner_service)],
    tenant_id: str = Query("default-tenant", description="Tenant ID for the application"),
) -> PartnerApplicationResponse:
    """
    Submit a partner application (public endpoint - no auth required).

    This is used by potential partners to apply to join the partner program.
    """
    try:
        application = await service.create_partner_application(
            data=data,
            tenant_id=tenant_id,
        )
        return PartnerApplicationResponse.model_validate(application, from_attributes=True)
    except Exception:
        logger.error("Failed to submit partner application", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit application",
        )


@router.get(
    "/applications",
    response_model=PartnerApplicationListResponse,
    dependencies=[Depends(require_authorization_header)],
)
async def list_partner_applications(
    service: Annotated[PartnerService, Depends(get_partner_service)],
    admin: Annotated[UserInfo, Depends(get_current_user)],
    status_filter: PartnerApplicationStatus | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PartnerApplicationListResponse:
    """
    List all partner applications (admin only).

    Requires platform admin access.
    """
    applications, total = await service.list_partner_applications(
        status=status_filter,
        page=page,
        page_size=page_size,
    )

    return PartnerApplicationListResponse(
        applications=[
            PartnerApplicationResponse.model_validate(a, from_attributes=True)
            for a in applications
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/applications/{application_id}",
    response_model=PartnerApplicationResponse,
    dependencies=[Depends(require_authorization_header)],
)
async def get_partner_application(
    application_id: UUID,
    service: Annotated[PartnerService, Depends(get_partner_service)],
    admin: Annotated[UserInfo, Depends(get_current_user)],
) -> PartnerApplicationResponse:
    """
    Get a single partner application (admin only).

    Requires platform admin access.
    """
    application = await service.get_partner_application(application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    return PartnerApplicationResponse.model_validate(application, from_attributes=True)


@router.post(
    "/applications/{application_id}/approve",
    response_model=PartnerApplicationResponse,
    dependencies=[Depends(require_authorization_header)],
)
async def approve_partner_application(
    application_id: UUID,
    service: Annotated[PartnerService, Depends(get_partner_service)],
    admin: Annotated[UserInfo, Depends(get_current_user)],
) -> PartnerApplicationResponse:
    """
    Approve a partner application (admin only).

    This creates the Partner record and initial PartnerUser from the application.
    Requires platform admin access.
    """
    try:
        application, partner, user = await service.approve_partner_application(
            application_id=application_id,
            reviewer_id=admin.user_id,
        )
        return PartnerApplicationResponse.model_validate(application, from_attributes=True)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception:
        logger.error("Failed to approve partner application", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve application",
        )


@router.post(
    "/applications/{application_id}/reject",
    response_model=PartnerApplicationResponse,
    dependencies=[Depends(require_authorization_header)],
)
async def reject_partner_application(
    application_id: UUID,
    data: PartnerApplicationRejectRequest,
    service: Annotated[PartnerService, Depends(get_partner_service)],
    admin: Annotated[UserInfo, Depends(get_current_user)],
) -> PartnerApplicationResponse:
    """
    Reject a partner application (admin only).

    Requires platform admin access.
    """
    try:
        application = await service.reject_partner_application(
            application_id=application_id,
            reviewer_id=admin.user_id,
            rejection_reason=data.rejection_reason,
        )
        return PartnerApplicationResponse.model_validate(application, from_attributes=True)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception:
        logger.error("Failed to reject partner application", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject application",
        )


# =============================================================================
# Partner Endpoints
# =============================================================================


@router.post(
    "/",
    response_model=PartnerResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_authorization_header)],
)
async def create_partner(
    data: PartnerCreate,
    service: Annotated[PartnerService, Depends(get_partner_service)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
) -> PartnerResponse:
    """
    Create a new partner.

    Requires authentication with partner_admin permission.
    """
    try:
        partner = await service.create_partner(
            data=data,
            created_by=current_user.user_id,
        )
        return _convert_partner_to_response(partner)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception:
        logger.error("Failed to create partner", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create partner",
        )


@router.get(
    "/{partner_id}",
    response_model=PartnerResponse,
    dependencies=[Depends(require_authorization_header)],
)
async def get_partner(
    partner_id: UUID,
    service: Annotated[PartnerService, Depends(get_partner_service)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
) -> PartnerResponse:
    """
    Get partner by ID.

    Requires authentication.
    """
    partner = await service.get_partner(partner_id=partner_id)
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Partner {partner_id} not found",
        )
    return _convert_partner_to_response(partner)


@router.get(
    "/by-number/{partner_number}",
    response_model=PartnerResponse,
    dependencies=[Depends(require_authorization_header)],
)
async def get_partner_by_number(
    partner_number: str,
    service: Annotated[PartnerService, Depends(get_partner_service)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
) -> PartnerResponse:
    """
    Get partner by partner number.

    Requires authentication.
    """
    partner = await service.get_partner_by_number(partner_number)
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Partner with number {partner_number} not found",
        )
    return _convert_partner_to_response(partner)


@router.get(
    "/",
    response_model=PartnerListResponse,
    dependencies=[Depends(require_authorization_header)],
)
async def list_partners(
    service: Annotated[PartnerService, Depends(get_partner_service)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    status_filter: PartnerStatus | None = Query(None, alias="status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
) -> PartnerListResponse:
    """
    List partners with optional filtering.

    Requires authentication.
    """
    offset = (page - 1) * page_size

    partners, total = await service.list_partners(
        status=status_filter,
        offset=offset,
        limit=page_size,
    )

    # Convert to response models
    partner_responses = [_convert_partner_to_response(p) for p in partners]

    return PartnerListResponse(
        partners=partner_responses,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch(
    "/{partner_id}",
    response_model=PartnerResponse,
    dependencies=[Depends(require_authorization_header)],
)
async def update_partner(
    partner_id: UUID,
    data: PartnerUpdate,
    service: Annotated[PartnerService, Depends(get_partner_service)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
) -> PartnerResponse:
    """
    Update partner information.

    Requires authentication with partner_admin permission.
    """
    partner = await service.update_partner(
        partner_id=partner_id,
        data=data,
        updated_by=current_user.user_id,
    )
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Partner {partner_id} not found",
        )
    return _convert_partner_to_response(partner)


@router.delete(
    "/{partner_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_authorization_header)],
)
async def delete_partner(
    partner_id: UUID,
    service: Annotated[PartnerService, Depends(get_partner_service)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
) -> None:
    """
    Delete a partner (soft delete).

    Requires authentication with partner_admin permission.
    """
    success = await service.delete_partner(
        partner_id=partner_id,
        deleted_by=current_user.user_id,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Partner {partner_id} not found",
        )


# =============================================================================
# Partner User Endpoints
# =============================================================================


@router.post(
    "/{partner_id}/users",
    response_model=PartnerUserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_authorization_header)],
)
async def create_partner_user(
    partner_id: UUID,
    data: PartnerUserCreate,
    service: Annotated[PartnerService, Depends(get_partner_service)],
    admin: Annotated[UserInfo, Depends(get_current_user)],
) -> PartnerUserResponse:
    """
    Create a partner user.

    Requires authentication.
    """
    # Validate partner exists
    partner = await service.get_partner(partner_id)
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Partner {partner_id} not found",
        )

    # Ensure partner_id matches
    data.partner_id = partner_id

    user = await service.create_partner_user(data=data)
    return PartnerUserResponse.model_validate(user, from_attributes=True)


@router.get(
    "/{partner_id}/users",
    response_model=list[PartnerUserResponse],
    dependencies=[Depends(require_authorization_header)],
)
async def list_partner_users(
    partner_id: UUID,
    service: Annotated[PartnerService, Depends(get_partner_service)],
    admin: Annotated[UserInfo, Depends(get_current_user)],
    active_only: bool = Query(True, description="Show only active users"),
) -> list[PartnerUserResponse]:
    """
    List users for a partner.

    Requires authentication.
    """
    partner = await service.get_partner(partner_id)
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Partner {partner_id} not found",
        )
    users = await service.list_partner_users(partner_id=partner_id, active_only=active_only)
    return [PartnerUserResponse.model_validate(u, from_attributes=True) for u in users]


@router.get(
    "/{partner_id}/users/{user_id}",
    response_model=PartnerUserResponse,
    dependencies=[Depends(require_authorization_header)],
)
async def get_partner_user(
    partner_id: UUID,
    user_id: UUID,
    service: Annotated[PartnerService, Depends(get_partner_service)],
    admin: Annotated[UserInfo, Depends(get_current_user)],
) -> PartnerUserResponse:
    """
    Get a single partner user by ID.

    Requires authentication.
    """
    user = await service.get_partner_user(partner_id=partner_id, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Partner user {user_id} not found",
        )
    return PartnerUserResponse.model_validate(user, from_attributes=True)


@router.patch(
    "/{partner_id}/users/{user_id}",
    response_model=PartnerUserResponse,
    dependencies=[Depends(require_authorization_header)],
)
async def update_partner_user(
    partner_id: UUID,
    user_id: UUID,
    data: PartnerUserUpdate,
    service: Annotated[PartnerService, Depends(get_partner_service)],
    admin: Annotated[UserInfo, Depends(get_current_user)],
) -> PartnerUserResponse:
    """
    Update a partner user.

    Requires authentication.
    """
    user = await service.update_partner_user(
        partner_id=partner_id,
        user_id=user_id,
        data=data,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Partner user {user_id} not found",
        )
    return PartnerUserResponse.model_validate(user, from_attributes=True)


@router.delete(
    "/{partner_id}/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_authorization_header)],
)
async def delete_partner_user(
    partner_id: UUID,
    user_id: UUID,
    service: Annotated[PartnerService, Depends(get_partner_service)],
    admin: Annotated[UserInfo, Depends(get_current_user)],
) -> None:
    """
    Soft delete a partner user (set is_active=False).

    Requires authentication.
    """
    deleted = await service.delete_partner_user(partner_id=partner_id, user_id=user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Partner user {user_id} not found",
        )


# =============================================================================
# Partner Account Endpoints
# =============================================================================


@router.post(
    "/accounts",
    response_model=PartnerAccountResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_authorization_header)],
)
async def create_partner_account(
    data: PartnerAccountCreate,
    service: Annotated[PartnerService, Depends(get_partner_service)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
) -> PartnerAccountResponse:
    """
    Assign a customer to a partner.

    Requires authentication with partner_admin permission.
    """
    account = await service.create_partner_account(data=data)

    account_dict: dict[str, Any] = {}
    for key in PartnerAccountResponse.model_fields:
        if key == "metadata":
            account_dict["metadata"] = account.metadata_ if hasattr(account, "metadata_") else {}
        elif key == "tenant_id":
            account_dict["tenant_id"] = str(account.customer_id)
        elif hasattr(account, key):
            account_dict[key] = getattr(account, key)

    return PartnerAccountResponse.model_validate(account_dict)


@router.get(
    "/{partner_id}/accounts",
    response_model=list[PartnerAccountResponse],
    dependencies=[Depends(require_authorization_header)],
)
async def list_partner_accounts(
    partner_id: UUID,
    service: Annotated[PartnerService, Depends(get_partner_service)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    active_only: bool = Query(True, description="Show only active accounts"),
) -> list[PartnerAccountResponse]:
    """
    List accounts assigned to a partner.

    Requires authentication.
    """
    accounts = await service.list_partner_accounts(partner_id=partner_id, active_only=active_only)

    responses = []
    for account in accounts:
        account_dict: dict[str, Any] = {}
        for key in PartnerAccountResponse.model_fields:
            if key == "metadata":
                account_dict["metadata"] = (
                    account.metadata_ if hasattr(account, "metadata_") else {}
                )
            elif key == "tenant_id":
                account_dict["tenant_id"] = str(account.customer_id)
            elif hasattr(account, key):
                account_dict[key] = getattr(account, key)
        responses.append(PartnerAccountResponse.model_validate(account_dict))

    return responses


# =============================================================================
# Commission Event Endpoints
# =============================================================================


@router.post(
    "/commissions",
    response_model=PartnerCommissionEventResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_authorization_header)],
)
async def create_commission_event(
    data: PartnerCommissionEventCreate,
    service: Annotated[PartnerService, Depends(get_partner_service)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
) -> PartnerCommissionEventResponse:
    """
    Create a commission event.

    Requires authentication with partner_admin permission.
    """
    event = await service.create_commission_event(data=data)

    event_dict: dict[str, Any] = {}
    for key in PartnerCommissionEventResponse.model_fields:
        if key == "metadata":
            event_dict["metadata"] = event.metadata_ if hasattr(event, "metadata_") else {}
        elif key == "tenant_id":
            event_dict["tenant_id"] = str(event.customer_id) if event.customer_id else None
        elif hasattr(event, key):
            event_dict[key] = getattr(event, key)

    return PartnerCommissionEventResponse.model_validate(event_dict)


@router.get(
    "/{partner_id}/commissions",
    response_model=PartnerCommissionEventListResponse,
    dependencies=[Depends(require_authorization_header)],
)
async def list_commission_events(
    partner_id: UUID,
    service: Annotated[PartnerService, Depends(get_partner_service)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
) -> PartnerCommissionEventListResponse:
    """
    List commission events for a partner.

    Requires authentication.
    """
    offset = (page - 1) * page_size

    events = await service.list_commission_events(
        partner_id=partner_id,
        offset=offset,
        limit=page_size,
    )

    responses = []
    for event in events:
        event_dict: dict[str, Any] = {}
        for key in PartnerCommissionEventResponse.model_fields:
            if key == "metadata":
                event_dict["metadata"] = event.metadata_ if hasattr(event, "metadata_") else {}
            elif key == "tenant_id":
                event_dict["tenant_id"] = str(event.customer_id) if event.customer_id else None
            elif hasattr(event, key):
                event_dict[key] = getattr(event, key)
        responses.append(PartnerCommissionEventResponse.model_validate(event_dict))

    return PartnerCommissionEventListResponse(
        events=responses,
        total=len(responses),
        page=page,
        page_size=page_size,
    )


# =============================================================================
# Referral Lead Endpoints
# =============================================================================


@router.post(
    "/referrals",
    response_model=ReferralLeadResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_authorization_header)],
)
async def create_referral(
    data: ReferralLeadCreate,
    service: Annotated[PartnerService, Depends(get_partner_service)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
) -> ReferralLeadResponse:
    """
    Create a referral lead.

    Requires authentication.
    """
    referral = await service.create_referral(data=data)

    referral_dict = {}
    for key in ReferralLeadResponse.model_fields:
        if key == "metadata":
            referral_dict["metadata"] = referral.metadata_ if hasattr(referral, "metadata_") else {}
        elif hasattr(referral, key):
            referral_dict[key] = getattr(referral, key)

    return ReferralLeadResponse.model_validate(referral_dict)


@router.get(
    "/{partner_id}/referrals",
    response_model=ReferralLeadListResponse,
    dependencies=[Depends(require_authorization_header)],
)
async def list_referrals(
    partner_id: UUID,
    service: Annotated[PartnerService, Depends(get_partner_service)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
) -> ReferralLeadListResponse:
    """
    List referral leads for a partner.

    Requires authentication.
    """
    offset = (page - 1) * page_size

    referrals = await service.list_referrals(
        partner_id=partner_id,
        offset=offset,
        limit=page_size,
    )

    responses = []
    for referral in referrals:
        referral_dict = {}
        for key in ReferralLeadResponse.model_fields:
            if key == "metadata":
                referral_dict["metadata"] = (
                    referral.metadata_ if hasattr(referral, "metadata_") else {}
                )
            elif hasattr(referral, key):
                referral_dict[key] = getattr(referral, key)
        responses.append(ReferralLeadResponse.model_validate(referral_dict))

    return ReferralLeadListResponse(
        referrals=responses,
        total=len(responses),
        page=page,
        page_size=page_size,
    )


@router.patch(
    "/referrals/{referral_id}",
    response_model=ReferralLeadResponse,
    dependencies=[Depends(require_authorization_header)],
)
async def update_referral(
    referral_id: UUID,
    data: ReferralLeadUpdate,
    service: Annotated[PartnerService, Depends(get_partner_service)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
) -> ReferralLeadResponse:
    """
    Update referral lead.

    Requires authentication.
    """
    referral = await service.update_referral(referral_id=referral_id, data=data)
    if not referral:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Referral {referral_id} not found",
        )

    referral_dict = {}
    for key in ReferralLeadResponse.model_fields:
        if key == "metadata":
            referral_dict["metadata"] = referral.metadata_ if hasattr(referral, "metadata_") else {}
        elif hasattr(referral, key):
            referral_dict[key] = getattr(referral, key)

    return ReferralLeadResponse.model_validate(referral_dict)


# =============================================================================
# Public Invitation Endpoints (No Auth Required)
# =============================================================================


@router.post("/invitations/accept", response_model=dict[str, Any])
async def accept_partner_invitation(
    data: AcceptPartnerInvitationRequest,
    db: AsyncSession = Depends(get_session_dependency),
) -> dict[str, Any]:
    """
    Accept a partner invitation.

    This is a public endpoint - no authentication required.
    Creates a new user account and partner user record.
    """
    # Find the invitation by token
    result = await db.execute(
        select(PartnerUserInvitation).where(PartnerUserInvitation.token == data.token)
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    if invitation.status != PartnerInvitationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invitation has already been {invitation.status.value}",
        )

    if invitation.is_expired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has expired",
        )

    # Check if email already has a user account
    tenant_clause = (
        User.tenant_id.is_(None)
        if invitation.tenant_id is None
        else User.tenant_id == invitation.tenant_id
    )
    existing_user = await db.execute(
        select(User).where(and_(User.email == invitation.email, tenant_clause))
    )
    user = existing_user.scalar_one_or_none()

    if not user:
        # Create new user account
        password_hash = hash_password(data.password)
        user = User(
            email=invitation.email,
            username=invitation.email,
            password_hash=password_hash,
            full_name=f"{data.first_name} {data.last_name}",
            first_name=data.first_name,
            last_name=data.last_name,
            is_active=True,
            is_verified=True,
            roles=["partner"],
            tenant_id=invitation.tenant_id,
        )
        db.add(user)
        await db.flush()

        logger.info(
            "partner.invitation_user_created",
            user_id=str(user.id),
            email=invitation.email,
        )

    # Create partner user record
    partner_user = PartnerUser(
        partner_id=invitation.partner_id,
        first_name=data.first_name,
        last_name=data.last_name,
        email=invitation.email,
        role=invitation.role,
        user_id=user.id,
        is_active=True,
        tenant_id=invitation.tenant_id,
    )
    db.add(partner_user)

    # Mark invitation as accepted
    invitation.status = PartnerInvitationStatus.ACCEPTED
    invitation.accepted_at = datetime.now(UTC)
    invitation.updated_at = datetime.now(UTC)

    await db.commit()

    logger.info(
        "partner.invitation_accepted",
        invitation_id=str(invitation.id),
        partner_id=str(invitation.partner_id),
        email=invitation.email,
        user_id=str(user.id),
    )

    return {
        "success": True,
        "message": "Invitation accepted successfully",
        "user_id": str(user.id),
        "partner_user_id": str(partner_user.id),
    }


# =============================================================================
# Dashboard Endpoint
# =============================================================================


class PartnerDashboardSummary(BaseModel):
    """Summary statistics for partner dashboard."""

    model_config = ConfigDict()

    total_partners: int = Field(description="Total partner count")
    active_partners: int = Field(description="Active partners count")
    pending_partners: int = Field(description="Pending partners count")
    suspended_partners: int = Field(description="Suspended partners count")
    new_this_month: int = Field(description="New partners this month")
    pending_applications: int = Field(description="Pending applications count")
    total_referrals: int = Field(description="Total referral leads")
    converted_referrals: int = Field(description="Converted referral leads")
    conversion_rate_pct: float = Field(description="Referral conversion rate")
    total_commissions: float = Field(description="Total commissions earned (in dollars)")


class PartnerChartDataPoint(BaseModel):
    """Single data point for partner charts."""

    model_config = ConfigDict()

    label: str
    value: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class PartnerCharts(BaseModel):
    """Chart data for partner dashboard."""

    model_config = ConfigDict()

    partner_growth: list[PartnerChartDataPoint] = Field(description="Monthly partner growth")
    partners_by_status: list[PartnerChartDataPoint] = Field(description="Partner breakdown by status")
    referrals_trend: list[PartnerChartDataPoint] = Field(description="Monthly referral trend")
    commissions_trend: list[PartnerChartDataPoint] = Field(description="Monthly commissions trend")


class PartnerAlert(BaseModel):
    """Alert item for partner dashboard."""

    model_config = ConfigDict()

    type: str = Field(description="Alert type: warning, error, info")
    title: str
    message: str
    count: int = 0
    action_url: str | None = None


class PartnerRecentActivity(BaseModel):
    """Recent activity item for partner dashboard."""

    model_config = ConfigDict()

    id: str
    type: str = Field(description="Activity type: partner, application, referral, commission")
    description: str
    amount: float | None = None
    status: str
    timestamp: datetime
    partner_id: str | None = None


class PartnerDashboardResponse(BaseModel):
    """Consolidated partner dashboard response."""

    model_config = ConfigDict()

    summary: PartnerDashboardSummary
    charts: PartnerCharts
    alerts: list[PartnerAlert]
    recent_activity: list[PartnerRecentActivity]
    generated_at: datetime


@router.get(
    "/dashboard",
    response_model=PartnerDashboardResponse,
    summary="Get partner dashboard data",
    description="Returns consolidated partner metrics, charts, and alerts for the dashboard",
)
async def get_partner_dashboard(
    period_months: int = Query(6, ge=1, le=24, description="Months of trend data"),
    admin: Annotated[UserInfo, Depends(require_platform_admin)] = None,
    session: AsyncSession = Depends(get_session_dependency),
) -> PartnerDashboardResponse:
    """
    Get consolidated partner dashboard data including:
    - Summary statistics (partner counts, referrals, commissions)
    - Chart data (trends, breakdowns)
    - Alerts (pending applications, inactive partners)
    - Recent activity
    """
    try:
        now = datetime.now(UTC)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # ========== SUMMARY STATS ==========
        # Partner counts by status
        partner_counts_query = select(
            func.count(Partner.id).label("total"),
            func.sum(case((Partner.status == PartnerStatus.ACTIVE, 1), else_=0)).label("active"),
            func.sum(case((Partner.status == PartnerStatus.PENDING, 1), else_=0)).label("pending"),
            func.sum(case((Partner.status == PartnerStatus.SUSPENDED, 1), else_=0)).label("suspended"),
            func.sum(case((Partner.created_at >= month_start, 1), else_=0)).label("new_this_month"),
        ).where(Partner.deleted_at.is_(None))
        partner_counts_result = await session.execute(partner_counts_query)
        partner_counts = partner_counts_result.one()

        # Pending applications count
        pending_apps_query = select(func.count(PartnerApplication.id)).where(
            PartnerApplication.status == PartnerApplicationStatus.PENDING
        )
        pending_apps_result = await session.execute(pending_apps_query)
        pending_applications = pending_apps_result.scalar() or 0

        # Referral counts
        referral_counts_query = select(
            func.count(ReferralLead.id).label("total"),
            func.sum(case((ReferralLead.status == "converted", 1), else_=0)).label("converted"),
        )
        referral_counts_result = await session.execute(referral_counts_query)
        referral_counts = referral_counts_result.one()
        total_referrals = referral_counts.total or 0
        converted_referrals = referral_counts.converted or 0
        conversion_rate = (converted_referrals / total_referrals * 100) if total_referrals > 0 else 0.0

        # Total commissions
        commissions_query = select(func.coalesce(func.sum(PartnerCommissionEvent.amount), 0))
        commissions_result = await session.execute(commissions_query)
        total_commissions = (commissions_result.scalar() or 0) / 100  # Convert cents to dollars

        summary = PartnerDashboardSummary(
            total_partners=partner_counts.total or 0,
            active_partners=partner_counts.active or 0,
            pending_partners=partner_counts.pending or 0,
            suspended_partners=partner_counts.suspended or 0,
            new_this_month=partner_counts.new_this_month or 0,
            pending_applications=pending_applications,
            total_referrals=total_referrals,
            converted_referrals=converted_referrals,
            conversion_rate_pct=round(conversion_rate, 2),
            total_commissions=total_commissions,
        )

        # ========== CHART DATA ==========
        # Partner growth trend (monthly)
        partner_growth = []
        for i in range(period_months - 1, -1, -1):
            month_date = (now - timedelta(days=i * 30)).replace(day=1)
            next_month = (month_date + timedelta(days=32)).replace(day=1)

            month_count_query = select(func.count(Partner.id)).where(
                Partner.created_at >= month_date,
                Partner.created_at < next_month,
                Partner.deleted_at.is_(None),
            )
            month_count_result = await session.execute(month_count_query)
            month_count = month_count_result.scalar() or 0

            partner_growth.append(PartnerChartDataPoint(
                label=month_date.strftime("%b %Y"),
                value=month_count,
            ))

        # Partners by status
        status_query = select(
            Partner.status,
            func.count(Partner.id),
        ).where(Partner.deleted_at.is_(None)).group_by(Partner.status)
        status_result = await session.execute(status_query)
        partners_by_status = [
            PartnerChartDataPoint(label=row[0].value if row[0] else "unknown", value=row[1])
            for row in status_result.all()
        ]

        # Referrals trend (monthly)
        referrals_trend = []
        for i in range(period_months - 1, -1, -1):
            month_date = (now - timedelta(days=i * 30)).replace(day=1)
            next_month = (month_date + timedelta(days=32)).replace(day=1)

            month_referrals_query = select(func.count(ReferralLead.id)).where(
                ReferralLead.created_at >= month_date,
                ReferralLead.created_at < next_month,
            )
            month_referrals_result = await session.execute(month_referrals_query)
            month_referrals = month_referrals_result.scalar() or 0

            referrals_trend.append(PartnerChartDataPoint(
                label=month_date.strftime("%b %Y"),
                value=month_referrals,
            ))

        # Commissions trend (monthly)
        commissions_trend = []
        for i in range(period_months - 1, -1, -1):
            month_date = (now - timedelta(days=i * 30)).replace(day=1)
            next_month = (month_date + timedelta(days=32)).replace(day=1)

            month_commissions_query = select(
                func.coalesce(func.sum(PartnerCommissionEvent.amount), 0)
            ).where(
                PartnerCommissionEvent.created_at >= month_date,
                PartnerCommissionEvent.created_at < next_month,
            )
            month_commissions_result = await session.execute(month_commissions_query)
            month_commissions = (month_commissions_result.scalar() or 0) / 100

            commissions_trend.append(PartnerChartDataPoint(
                label=month_date.strftime("%b %Y"),
                value=month_commissions,
            ))

        charts = PartnerCharts(
            partner_growth=partner_growth,
            partners_by_status=partners_by_status,
            referrals_trend=referrals_trend,
            commissions_trend=commissions_trend,
        )

        # ========== ALERTS ==========
        alerts = []

        if pending_applications > 0:
            alerts.append(PartnerAlert(
                type="info",
                title="Pending Applications",
                message=f"{pending_applications} partner application(s) awaiting review",
                count=pending_applications,
                action_url="/partners/applications?status=pending",
            ))

        if partner_counts.suspended and partner_counts.suspended > 0:
            alerts.append(PartnerAlert(
                type="warning",
                title="Suspended Partners",
                message=f"{partner_counts.suspended} partner(s) are currently suspended",
                count=partner_counts.suspended,
                action_url="/partners?status=suspended",
            ))

        # ========== RECENT ACTIVITY ==========
        recent_partners_query = (
            select(Partner)
            .where(Partner.deleted_at.is_(None))
            .order_by(Partner.created_at.desc())
            .limit(10)
        )
        recent_partners_result = await session.execute(recent_partners_query)
        recent_partners = recent_partners_result.scalars().all()

        recent_activity = [
            PartnerRecentActivity(
                id=str(p.id),
                type="partner",
                description=f"Partner: {p.company_name or p.partner_number}",
                amount=None,
                status=p.status.value if p.status else "unknown",
                timestamp=p.created_at,
                partner_id=str(p.id),
            )
            for p in recent_partners
        ]

        return PartnerDashboardResponse(
            summary=summary,
            charts=charts,
            alerts=alerts,
            recent_activity=recent_activity,
            generated_at=now,
        )

    except Exception as e:
        logger.error("Failed to generate partner dashboard", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate partner dashboard: {str(e)}",
        )

"""
Tenant management API router.

Provides REST endpoints for tenant CRUD operations, settings, usage tracking,
and invitation management.
"""

import math
from datetime import datetime
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.core import UserInfo, get_current_user
from ..database import get_async_session
from .models import TenantInvitationStatus, TenantPlanType, TenantStatus
from .schemas import (
    TenantBulkDeleteRequest,
    TenantBulkStatusUpdate,
    TenantCreate,
    TenantFeatureUpdate,
    TenantInvitationAccept,
    TenantInvitationCreate,
    TenantInvitationResponse,
    TenantListResponse,
    TenantMetadataUpdate,
    TenantResponse,
    TenantSettingCreate,
    TenantSettingResponse,
    TenantStatsResponse,
    TenantUpdate,
    TenantUsageCreate,
    TenantUsageResponse,
)
from .service import (
    TenantAlreadyExistsError,
    TenantNotFoundError,
    TenantService,
)

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["Tenant Management"])


# Dependency to get tenant service
async def get_tenant_service(db: AsyncSession = Depends(get_async_session)) -> TenantService:
    """Get tenant service instance."""
    return TenantService(db)


# Tenant CRUD Operations
@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    current_user: UserInfo = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
) -> TenantResponse:
    """
    Create a new tenant organization.

    Creates a new tenant with initial configuration, trial period, and default features.
    """
    try:
        tenant = await service.create_tenant(tenant_data, created_by=current_user.user_id)

        # Convert to response model
        response = TenantResponse.model_validate(tenant)
        response.is_trial = tenant.is_trial
        response.is_active = tenant.status_is_active
        response.trial_expired = tenant.trial_expired
        response.has_exceeded_user_limit = tenant.has_exceeded_user_limit
        response.has_exceeded_api_limit = tenant.has_exceeded_api_limit
        response.has_exceeded_storage_limit = tenant.has_exceeded_storage_limit

        return response
    except TenantAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("", response_model=TenantListResponse)
async def list_tenants(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: TenantStatus | None = Query(
        None, alias="status", description="Filter by status"
    ),
    plan_type: TenantPlanType | None = Query(None, description="Filter by plan type"),
    search: str | None = Query(None, description="Search in name, slug, email"),
    include_deleted: bool = Query(False, description="Include soft-deleted tenants"),
    current_user: UserInfo = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
) -> TenantListResponse:
    """
    List all tenants with pagination and filtering.

    Supports filtering by status, plan type, and text search.
    """
    tenants, total = await service.list_tenants(
        page=page,
        page_size=page_size,
        status=status_filter,
        plan_type=plan_type,
        search=search,
        include_deleted=include_deleted,
    )

    # Convert to response models
    tenant_responses = []
    for tenant in tenants:
        response = TenantResponse.model_validate(tenant)
        response.is_trial = tenant.is_trial
        response.is_active = tenant.status_is_active
        response.trial_expired = tenant.trial_expired
        response.has_exceeded_user_limit = tenant.has_exceeded_user_limit
        response.has_exceeded_api_limit = tenant.has_exceeded_api_limit
        response.has_exceeded_storage_limit = tenant.has_exceeded_storage_limit
        tenant_responses.append(response)

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return TenantListResponse(
        items=tenant_responses, total=total, page=page, page_size=page_size, total_pages=total_pages
    )


@router.get("/current", response_model=TenantResponse | None)
async def get_current_tenant(
    current_user: UserInfo = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
) -> TenantResponse | None:
    """
    Get the current user's tenant.

    Returns the tenant associated with the authenticated user's tenant_id.
    Returns null if the user is not associated with any tenant.
    """
    if not current_user.tenant_id:
        # Return null instead of 404 to allow frontend to handle gracefully
        return None

    try:
        tenant = await service.get_tenant(current_user.tenant_id)
    except TenantNotFoundError:
        logger.info(
            "tenant.current_not_found",
            tenant_id=current_user.tenant_id,
            user_id=current_user.user_id,
        )
        return None
    except Exception as exc:  # pragma: no cover - defensive guard for unexpected errors
        logger.exception(
            "tenant.current_fetch_error",
            tenant_id=current_user.tenant_id,
            user_id=current_user.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load current tenant",
        ) from exc

    response = TenantResponse.model_validate(tenant)
    response.is_trial = tenant.is_trial
    response.is_active = tenant.status_is_active
    response.trial_expired = tenant.trial_expired
    response.has_exceeded_user_limit = tenant.has_exceeded_user_limit
    response.has_exceeded_api_limit = tenant.has_exceeded_api_limit
    response.has_exceeded_storage_limit = tenant.has_exceeded_storage_limit

    return response


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    current_user: UserInfo = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
) -> TenantResponse:
    """
    Get a specific tenant by ID.

    Returns detailed tenant information including usage, limits, and configuration.
    """
    try:
        tenant = await service.get_tenant(tenant_id)

        response = TenantResponse.model_validate(tenant)
        response.is_trial = tenant.is_trial
        response.is_active = tenant.status_is_active
        response.trial_expired = tenant.trial_expired
        response.has_exceeded_user_limit = tenant.has_exceeded_user_limit
        response.has_exceeded_api_limit = tenant.has_exceeded_api_limit
        response.has_exceeded_storage_limit = tenant.has_exceeded_storage_limit

        return response
    except TenantNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/slug/{slug}", response_model=TenantResponse)
async def get_tenant_by_slug(
    slug: str,
    current_user: UserInfo = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
) -> TenantResponse:
    """
    Get a tenant by slug.

    Retrieve tenant information using the URL-friendly slug identifier.
    """
    try:
        tenant = await service.get_tenant_by_slug(slug)

        response = TenantResponse.model_validate(tenant)
        response.is_trial = tenant.is_trial
        response.is_active = tenant.status_is_active
        response.trial_expired = tenant.trial_expired
        response.has_exceeded_user_limit = tenant.has_exceeded_user_limit
        response.has_exceeded_api_limit = tenant.has_exceeded_api_limit
        response.has_exceeded_storage_limit = tenant.has_exceeded_storage_limit

        return response
    except TenantNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    tenant_data: TenantUpdate,
    current_user: UserInfo = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
) -> TenantResponse:
    """
    Update a tenant's information.

    Allows partial updates to tenant configuration, limits, and settings.
    """
    try:
        tenant = await service.update_tenant(
            tenant_id, tenant_data, updated_by=current_user.user_id
        )

        response = TenantResponse.model_validate(tenant)
        response.is_trial = tenant.is_trial
        response.is_active = tenant.status_is_active
        response.trial_expired = tenant.trial_expired
        response.has_exceeded_user_limit = tenant.has_exceeded_user_limit
        response.has_exceeded_api_limit = tenant.has_exceeded_api_limit
        response.has_exceeded_storage_limit = tenant.has_exceeded_storage_limit

        return response
    except TenantNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: str,
    permanent: bool = Query(False, description="Permanently delete (vs soft delete)"),
    current_user: UserInfo = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
) -> None:
    """
    Delete a tenant.

    Supports both soft delete (default) and permanent deletion.
    """
    try:
        await service.delete_tenant(tenant_id, permanent=permanent, deleted_by=current_user.user_id)
    except TenantNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{tenant_id}/restore", response_model=TenantResponse)
async def restore_tenant(
    tenant_id: str,
    current_user: UserInfo = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
) -> TenantResponse:
    """
    Restore a soft-deleted tenant.

    Recovers a tenant that was previously soft-deleted.
    """
    try:
        tenant = await service.restore_tenant(tenant_id, restored_by=current_user.user_id)

        response = TenantResponse.model_validate(tenant)
        response.is_trial = tenant.is_trial
        response.is_active = tenant.status_is_active
        response.trial_expired = tenant.trial_expired
        response.has_exceeded_user_limit = tenant.has_exceeded_user_limit
        response.has_exceeded_api_limit = tenant.has_exceeded_api_limit
        response.has_exceeded_storage_limit = tenant.has_exceeded_storage_limit

        return response
    except TenantNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Tenant Settings
@router.get("/{tenant_id}/settings", response_model=list[TenantSettingResponse])
async def get_tenant_settings(
    tenant_id: str,
    current_user: UserInfo = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
) -> list[TenantSettingResponse]:
    """
    Get all settings for a tenant.

    Returns all configuration settings for the specified tenant.
    """
    settings = await service.get_tenant_settings(tenant_id)
    return [TenantSettingResponse.model_validate(s) for s in settings]


@router.get("/{tenant_id}/settings/{key}", response_model=TenantSettingResponse)
async def get_tenant_setting(
    tenant_id: str,
    key: str,
    current_user: UserInfo = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
) -> TenantSettingResponse:
    """
    Get a specific tenant setting by key.

    Retrieves a single configuration setting.
    """
    setting = await service.get_tenant_setting(tenant_id, key)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting with key '{key}' not found for tenant",
        )
    return TenantSettingResponse.model_validate(setting)


@router.post("/{tenant_id}/settings", response_model=TenantSettingResponse)
async def create_or_update_tenant_setting(
    tenant_id: str,
    setting_data: TenantSettingCreate,
    current_user: UserInfo = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
) -> TenantSettingResponse:
    """
    Create or update a tenant setting.

    Sets a configuration value for the tenant. Updates if exists, creates if new.
    """
    setting = await service.set_tenant_setting(tenant_id, setting_data)
    return TenantSettingResponse.model_validate(setting)


@router.delete("/{tenant_id}/settings/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant_setting(
    tenant_id: str,
    key: str,
    current_user: UserInfo = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
) -> None:
    """
    Delete a tenant setting.

    Removes a configuration setting from the tenant.
    """
    await service.delete_tenant_setting(tenant_id, key)


# Usage Tracking
@router.post(
    "/{tenant_id}/usage", response_model=TenantUsageResponse, status_code=status.HTTP_201_CREATED
)
async def record_tenant_usage(
    tenant_id: str,
    usage_data: TenantUsageCreate,
    current_user: UserInfo = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
) -> TenantUsageResponse:
    """
    Record usage metrics for a tenant.

    Logs usage statistics for a specific time period.
    """
    usage = await service.record_usage(tenant_id, usage_data)
    return TenantUsageResponse.model_validate(usage)


@router.get("/{tenant_id}/usage", response_model=list[TenantUsageResponse])
async def get_tenant_usage(
    tenant_id: str,
    start_date: datetime | None = Query(None, description="Filter by start date"),
    end_date: datetime | None = Query(None, description="Filter by end date"),
    current_user: UserInfo = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
) -> list[TenantUsageResponse]:
    """
    Get usage records for a tenant.

    Retrieves historical usage data, optionally filtered by date range.
    """
    usage_records = await service.get_tenant_usage(tenant_id, start_date, end_date)
    return [TenantUsageResponse.model_validate(u) for u in usage_records]


@router.get("/{tenant_id}/stats", response_model=TenantStatsResponse)
async def get_tenant_stats(
    tenant_id: str,
    current_user: UserInfo = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
) -> TenantStatsResponse:
    """
    Get tenant usage statistics and analytics.

    Returns comprehensive usage metrics, limits, and percentages.
    """
    try:
        return await service.get_tenant_stats(tenant_id)
    except TenantNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Invitations
@router.post(
    "/{tenant_id}/invitations",
    response_model=TenantInvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invitation(
    tenant_id: str,
    invitation_data: TenantInvitationCreate,
    current_user: UserInfo = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
) -> TenantInvitationResponse:
    """
    Create a tenant invitation.

    Invites a user to join the tenant organization.
    """
    invitation = await service.create_invitation(
        tenant_id, invitation_data, invited_by=current_user.user_id
    )

    response = TenantInvitationResponse.model_validate(invitation)
    response.is_expired = invitation.is_expired
    response.is_pending = invitation.is_pending

    return response


@router.get("/{tenant_id}/invitations", response_model=list[TenantInvitationResponse])
async def list_invitations(
    tenant_id: str,
    status_filter: TenantInvitationStatus | None = Query(None, alias="status"),
    current_user: UserInfo = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
) -> list[TenantInvitationResponse]:
    """
    List invitations for a tenant.

    Returns all invitations, optionally filtered by status.
    """
    invitations = await service.list_tenant_invitations(tenant_id, status=status_filter)

    responses = []
    for inv in invitations:
        response = TenantInvitationResponse.model_validate(inv)
        response.is_expired = inv.is_expired
        response.is_pending = inv.is_pending
        responses.append(response)

    return responses


@router.post("/invitations/accept", response_model=TenantInvitationResponse)
async def accept_invitation(
    accept_data: TenantInvitationAccept,
    service: TenantService = Depends(get_tenant_service),
) -> TenantInvitationResponse:
    """
    Accept a tenant invitation.

    Processes an invitation token to join a tenant.
    """
    try:
        invitation = await service.accept_invitation(accept_data.token)

        response = TenantInvitationResponse.model_validate(invitation)
        response.is_expired = invitation.is_expired
        response.is_pending = invitation.is_pending

        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{tenant_id}/invitations/{invitation_id}/revoke", response_model=TenantInvitationResponse
)
async def revoke_invitation(
    tenant_id: str,
    invitation_id: str,
    current_user: UserInfo = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
) -> TenantInvitationResponse:
    """
    Revoke a tenant invitation.

    Cancels a pending invitation.
    """
    try:
        invitation = await service.revoke_invitation(invitation_id)

        response = TenantInvitationResponse.model_validate(invitation)
        response.is_expired = invitation.is_expired
        response.is_pending = invitation.is_pending

        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Feature Management
@router.patch("/{tenant_id}/features", response_model=TenantResponse)
async def update_tenant_features(
    tenant_id: str,
    feature_data: TenantFeatureUpdate,
    current_user: UserInfo = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
) -> TenantResponse:
    """
    Update tenant feature flags.

    Enables or disables features for the tenant.
    """
    try:
        tenant = await service.update_tenant_features(
            tenant_id, feature_data.features, updated_by=current_user.user_id
        )

        response = TenantResponse.model_validate(tenant)
        response.is_trial = tenant.is_trial
        response.is_active = tenant.status_is_active
        response.trial_expired = tenant.trial_expired
        response.has_exceeded_user_limit = tenant.has_exceeded_user_limit
        response.has_exceeded_api_limit = tenant.has_exceeded_api_limit
        response.has_exceeded_storage_limit = tenant.has_exceeded_storage_limit

        return response
    except TenantNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{tenant_id}/metadata", response_model=TenantResponse)
async def update_tenant_metadata(
    tenant_id: str,
    metadata_data: TenantMetadataUpdate,
    current_user: UserInfo = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
) -> TenantResponse:
    """
    Update tenant metadata.

    Updates custom metadata fields for the tenant.
    """
    try:
        tenant = await service.update_tenant_metadata(
            tenant_id, metadata_data.custom_metadata, updated_by=current_user.user_id
        )

        response = TenantResponse.model_validate(tenant)
        response.is_trial = tenant.is_trial
        response.is_active = tenant.status_is_active
        response.trial_expired = tenant.trial_expired
        response.has_exceeded_user_limit = tenant.has_exceeded_user_limit
        response.has_exceeded_api_limit = tenant.has_exceeded_api_limit
        response.has_exceeded_storage_limit = tenant.has_exceeded_storage_limit

        return response
    except TenantNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Bulk Operations
@router.post("/bulk/status", response_model=dict[str, Any])
async def bulk_update_status(
    update_data: TenantBulkStatusUpdate,
    current_user: UserInfo = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
) -> dict[str, Any]:
    """
    Bulk update tenant status.

    Updates the status of multiple tenants at once.
    """
    updated_count = await service.bulk_update_status(
        update_data.tenant_ids, update_data.status, updated_by=current_user.user_id
    )

    return {"updated_count": updated_count, "tenant_ids": update_data.tenant_ids}


@router.post("/bulk/delete", response_model=dict[str, Any])
async def bulk_delete_tenants(
    delete_data: TenantBulkDeleteRequest,
    current_user: UserInfo = Depends(get_current_user),
    service: TenantService = Depends(get_tenant_service),
) -> dict[str, Any]:
    """
    Bulk delete tenants.

    Deletes multiple tenants at once (soft or permanent).
    """
    deleted_count = await service.bulk_delete_tenants(
        delete_data.tenant_ids, permanent=delete_data.permanent, deleted_by=current_user.user_id
    )

    return {
        "deleted_count": deleted_count,
        "tenant_ids": delete_data.tenant_ids,
        "permanent": delete_data.permanent,
    }

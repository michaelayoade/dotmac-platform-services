"""
FastAPI router for audit and activity endpoints.
"""

from typing import Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    AuditActivityList,
    AuditActivityResponse,
    AuditFilterParams,
    ActivityType,
    ActivitySeverity,
)
from .service import AuditService, log_api_activity
from ..auth.core import get_current_user, get_current_user_optional, UserInfo
from ..tenant import get_current_tenant_id
from ..db import get_async_session


logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/activities", response_model=AuditActivityList)
async def list_activities(
    request: Request,
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    activity_type: Optional[ActivityType] = Query(None, description="Filter by activity type"),
    severity: Optional[ActivitySeverity] = Query(None, description="Filter by severity"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    days: Optional[int] = Query(30, ge=1, le=365, description="Number of days to look back"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=1000, description="Items per page"),
    session: AsyncSession = Depends(get_async_session),
    current_user: Optional[UserInfo] = Depends(get_current_user_optional),
):
    """
    Get paginated list of audit activities.

    Supports filtering by various criteria and is tenant-aware.
    """
    try:
        # Build filter parameters
        from datetime import datetime, timedelta

        start_date = datetime.utcnow() - timedelta(days=days) if days else None

        filters = AuditFilterParams(
            user_id=user_id,
            tenant_id=get_current_tenant_id(),  # Always filter by current tenant
            activity_type=activity_type,
            severity=severity,
            resource_type=resource_type,
            resource_id=resource_id,
            start_date=start_date,
            page=page,
            per_page=per_page,
        )

        # Create service and get activities
        service = AuditService(session)
        activities = await service.get_activities(filters)

        # Log this API access
        if current_user:
            await log_api_activity(
                request=request,
                action="list_activities",
                description=f"User {current_user.user_id} retrieved audit activities",
                severity=ActivitySeverity.LOW,
                details={
                    "filters": filters.model_dump(exclude_none=True),
                    "result_count": len(activities.activities),
                },
            )

        return activities

    except Exception as e:
        logger.error("Error retrieving audit activities", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve audit activities")


@router.get("/activities/recent", response_model=list[AuditActivityResponse])
async def get_recent_activities(
    request: Request,
    limit: int = Query(20, ge=1, le=100, description="Maximum number of activities to return"),
    days: int = Query(7, ge=1, le=90, description="Number of days to look back"),
    session: AsyncSession = Depends(get_async_session),
    current_user: Optional[UserInfo] = Depends(get_current_user_optional),
):
    """
    Get recent audit activities for dashboard/frontend views.

    Returns the most recent activities for the current tenant, optimized for frontend display.
    """
    try:
        service = AuditService(session)

        # Get activities for current tenant
        activities = await service.get_recent_activities(
            tenant_id=get_current_tenant_id(),
            limit=limit,
            days=days,
        )

        # Log this API access
        if current_user:
            await log_api_activity(
                request=request,
                action="get_recent_activities",
                description=f"User {current_user.user_id} retrieved recent activities",
                severity=ActivitySeverity.LOW,
                details={
                    "limit": limit,
                    "days": days,
                    "result_count": len(activities),
                },
            )

        return activities

    except Exception as e:
        logger.error("Error retrieving recent activities", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve recent activities")


@router.get("/activities/user/{user_id}", response_model=list[AuditActivityResponse])
async def get_user_activities(
    user_id: str,
    request: Request,
    limit: int = Query(50, ge=1, le=200, description="Maximum number of activities to return"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    session: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
):
    """
    Get audit activities for a specific user.

    Users can only view their own activities unless they have admin permissions.
    """
    try:
        # Security check: users can only view their own activities unless admin
        if user_id != current_user.user_id and "admin" not in current_user.roles:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to view other user's activities"
            )

        service = AuditService(session)

        activities = await service.get_recent_activities(
            user_id=user_id,
            tenant_id=current_user.tenant_id,  # Ensure tenant isolation
            limit=limit,
            days=days,
        )

        # Log this API access
        await log_api_activity(
            request=request,
            action="get_user_activities",
            description=f"User {current_user.user_id} retrieved activities for user {user_id}",
            severity=ActivitySeverity.MEDIUM if user_id != current_user.user_id else ActivitySeverity.LOW,
            details={
                "target_user_id": user_id,
                "limit": limit,
                "days": days,
                "result_count": len(activities),
            },
        )

        return activities

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving user activities", error=str(e), user_id=user_id, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve user activities")


@router.get("/activities/summary")
async def get_activity_summary(
    request: Request,
    days: int = Query(7, ge=1, le=90, description="Number of days to look back"),
    session: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
):
    """
    Get activity summary statistics for the current tenant.

    Provides aggregated data for dashboard widgets and analytics.
    """
    try:
        service = AuditService(session)

        summary = await service.get_activity_summary(
            tenant_id=current_user.tenant_id,
            days=days,
        )

        # Log this API access
        await log_api_activity(
            request=request,
            action="get_activity_summary",
            description=f"User {current_user.user_id} retrieved activity summary",
            severity=ActivitySeverity.LOW,
            details={
                "days": days,
                "total_activities": summary.get("total_activities", 0),
            },
        )

        return summary

    except Exception as e:
        logger.error("Error retrieving activity summary", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve activity summary")


@router.get("/activities/{activity_id}", response_model=AuditActivityResponse)
async def get_activity_details(
    activity_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
):
    """
    Get details for a specific audit activity.

    Returns detailed information about a single audit event.
    """
    try:
        from sqlalchemy import select
        from .models import AuditActivity

        # Query for the specific activity
        query = select(AuditActivity).where(
            AuditActivity.id == activity_id,
            AuditActivity.tenant_id == current_user.tenant_id,  # Ensure tenant isolation
        )

        result = await session.execute(query)
        activity = result.scalar_one_or_none()

        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        # Security check: users can only view activities they're involved in unless admin
        if (activity.user_id != current_user.user_id and
            "admin" not in current_user.roles):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to view this activity"
            )

        # Log this API access
        await log_api_activity(
            request=request,
            action="get_activity_details",
            description=f"User {current_user.user_id} retrieved activity details",
            severity=ActivitySeverity.LOW,
            details={
                "activity_id": str(activity_id),
                "activity_type": activity.activity_type,
            },
        )

        return AuditActivityResponse.model_validate(activity)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving activity details", error=str(e), activity_id=activity_id, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve activity details")
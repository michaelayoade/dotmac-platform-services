"""
Job API Router

REST endpoints for job management and monitoring.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as fastapi_status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.core import UserInfo
from dotmac.platform.auth.dependencies import get_current_user
from dotmac.platform.db import get_session_dependency
from dotmac.platform.jobs.schemas import (
    JobCancelResponse,
    JobCreate,
    JobListResponse,
    JobResponse,
    JobRetryResponse,
    JobStatistics,
    JobUpdate,
)
from dotmac.platform.jobs.service import JobService
from dotmac.platform.redis_client import RedisClientType, get_redis_client

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/jobs", tags=["Jobs"])


# =============================================================================
# Dependency: Get Job Service
# =============================================================================


async def get_job_service(
    session: AsyncSession = Depends(get_session_dependency),
    redis: RedisClientType = Depends(get_redis_client),
) -> JobService:
    """Get job service instance."""
    return JobService(session, redis_client=redis)


# =============================================================================
# Job Endpoints
# =============================================================================


@router.post(
    "",
    response_model=JobResponse,
    status_code=fastapi_status.HTTP_201_CREATED,
    summary="Create Job",
    description="Create a new async job",
)
async def create_job(
    job_data: JobCreate,
    service: JobService = Depends(get_job_service),
    current_user: UserInfo = Depends(get_current_user),
) -> JobResponse:
    """
    Create a new async job.

    Use this endpoint to initialize a background job. The job will be
    created in PENDING status and can be executed by background workers.

    **Job Types:**
    - `bulk_import` - Import multiple records from CSV/JSON
    - `bulk_export` - Export data to file
    - `firmware_upgrade` - Upgrade device firmware
    - `batch_provisioning` - Provision multiple devices
    - `data_migration` - Migrate data between systems
    - `report_generation` - Generate reports
    - `custom` - Custom job type
    """
    if current_user.tenant_id is None:
        raise HTTPException(
            status_code=fastapi_status.HTTP_400_BAD_REQUEST,
            detail="Tenant ID is required to create a job",
        )

    job = await service.create_job(
        tenant_id=current_user.tenant_id,
        created_by=current_user.user_id,
        job_data=job_data,
    )
    return JobResponse.model_validate(job)


@router.get(
    "",
    response_model=JobListResponse,
    summary="List Jobs",
    description="List jobs with filtering and pagination",
)
async def list_jobs(
    job_type: str | None = Query(None, description="Filter by job type"),
    job_status: str | None = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    service: JobService = Depends(get_job_service),
    current_user: UserInfo = Depends(get_current_user),
) -> JobListResponse:
    """
    List all jobs for the current tenant with optional filtering.

    **Filters:**
    - `job_type` - Filter by job type
    - `status` - Filter by status (pending, running, completed, failed, cancelled)

    **Pagination:**
    - Results are ordered by creation date (newest first)
    - Use `page` and `page_size` for pagination
    - Response includes `has_more` to indicate if there are more results
    """
    if current_user.tenant_id is None:
        raise HTTPException(
            status_code=fastapi_status.HTTP_400_BAD_REQUEST,
            detail="Tenant ID is required",
        )

    try:
        return await service.list_jobs(
            tenant_id=current_user.tenant_id,
            job_type=job_type,
            status=job_status,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        # Handle case where jobs table doesn't exist yet
        if "UndefinedTableError" in str(type(e).__name__) or "does not exist" in str(e):
            logger.warning("Jobs table not set up yet", error=str(e))
            return JobListResponse(jobs=[], total=0, page=page, page_size=page_size, has_more=False)
        raise


@router.get(
    "/statistics",
    response_model=JobStatistics,
    summary="Job Statistics",
    description="Get aggregate job statistics for the current tenant",
)
async def get_job_statistics(
    service: JobService = Depends(get_job_service),
    current_user: UserInfo = Depends(get_current_user),
) -> JobStatistics:
    """
    Get aggregated job statistics for dashboards.
    """
    if current_user.tenant_id is None:
        raise HTTPException(
            status_code=fastapi_status.HTTP_400_BAD_REQUEST,
            detail="Tenant ID is required",
        )

    return await service.get_statistics(current_user.tenant_id)


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get Job",
    description="Get job details by ID",
)
async def get_job(
    job_id: str,
    service: JobService = Depends(get_job_service),
    current_user: UserInfo = Depends(get_current_user),
) -> JobResponse:
    """
    Get detailed information about a specific job.

    Returns complete job details including progress, errors, and results.
    """
    if current_user.tenant_id is None:
        raise HTTPException(
            status_code=fastapi_status.HTTP_400_BAD_REQUEST,
            detail="Tenant ID is required",
        )

    job = await service.get_job(job_id, current_user.tenant_id)
    if not job:
        raise HTTPException(
            status_code=fastapi_status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )
    return JobResponse.model_validate(job)


@router.patch(
    "/{job_id}",
    response_model=JobResponse,
    summary="Update Job Progress",
    description="Update job progress and status",
)
async def update_job_progress(
    job_id: str,
    update_data: JobUpdate,
    service: JobService = Depends(get_job_service),
    current_user: UserInfo = Depends(get_current_user),
) -> JobResponse:
    """
    Update job progress.

    This endpoint is typically used by background workers to report progress.
    Updates are automatically broadcast to connected WebSocket clients.

    **Fields:**
    - `status` - Update job status
    - `progress_percent` - Update progress (0-100)
    - `items_processed` - Update processed item count
    - `items_succeeded` - Update succeeded item count
    - `items_failed` - Update failed item count
    - `current_item` - Update current item being processed
    - `error_message` - Set error message if job fails
    - `result` - Set final result data
    """
    if current_user.tenant_id is None:
        raise HTTPException(
            status_code=fastapi_status.HTTP_400_BAD_REQUEST,
            detail="Tenant ID is required",
        )

    job = await service.update_progress(
        job_id=job_id,
        tenant_id=current_user.tenant_id,
        update_data=update_data,
    )
    if not job:
        raise HTTPException(
            status_code=fastapi_status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )
    return JobResponse.model_validate(job)


@router.post(
    "/{job_id}/cancel",
    response_model=JobCancelResponse,
    summary="Cancel Job",
    description="Cancel a running or pending job",
)
async def cancel_job(
    job_id: str,
    service: JobService = Depends(get_job_service),
    current_user: UserInfo = Depends(get_current_user),
) -> JobCancelResponse:
    """
    Cancel a job that is pending or running.

    The job will be marked as CANCELLED and background workers should
    stop processing it. Already completed, failed, or cancelled jobs
    cannot be cancelled again.
    """
    if current_user.tenant_id is None:
        raise HTTPException(
            status_code=fastapi_status.HTTP_400_BAD_REQUEST,
            detail="Tenant ID is required",
        )

    job = await service.cancel_job(
        job_id=job_id,
        tenant_id=current_user.tenant_id,
        cancelled_by=current_user.user_id or "unknown",
    )
    if not job:
        raise HTTPException(
            status_code=fastapi_status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found or already in terminal state",
        )
    return JobCancelResponse(
        id=job.id,
        status=job.status,
        cancelled_at=job.cancelled_at,
        cancelled_by=job.cancelled_by or "unknown",
        message=f"Job {job_id} cancelled successfully",
    )


@router.post(
    "/{job_id}/retry",
    response_model=JobRetryResponse,
    summary="Retry Failed Items",
    description="Create a new job to retry failed items",
)
async def retry_failed_items(
    job_id: str,
    service: JobService = Depends(get_job_service),
    current_user: UserInfo = Depends(get_current_user),
) -> JobRetryResponse:
    """
    Retry failed items from a previous job.

    Creates a new job that will re-process only the items that failed
    in the original job. The new job will have the same parameters as
    the original but will only process failed items.

    **Requirements:**
    - Original job must have failed items recorded
    - Original job must be in a terminal state (completed, failed, or cancelled)
    """
    if current_user.tenant_id is None:
        raise HTTPException(
            status_code=fastapi_status.HTTP_400_BAD_REQUEST,
            detail="Tenant ID is required",
        )

    retry_job = await service.retry_failed_items(
        job_id=job_id,
        tenant_id=current_user.tenant_id,
        created_by=current_user.user_id,
    )
    if not retry_job:
        raise HTTPException(
            status_code=fastapi_status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found or has no failed items to retry",
        )

    parameters = retry_job.parameters if isinstance(retry_job.parameters, dict) else {}
    failed_items = parameters.get("failed_items", [])
    failed_items_count = len(failed_items)

    return JobRetryResponse(
        original_job_id=job_id,
        new_job_id=retry_job.id,
        failed_items_count=failed_items_count,
        message=f"Created retry job {retry_job.id} for {failed_items_count} failed items",
    )


# =============================================================================
# Dashboard Endpoint
# =============================================================================


class JobDashboardSummary(BaseModel):
    """Summary statistics for job dashboard."""

    model_config = ConfigDict()

    total_jobs: int = Field(description="Total job count")
    pending_jobs: int = Field(description="Pending jobs count")
    running_jobs: int = Field(description="Running jobs count")
    completed_jobs: int = Field(description="Completed jobs count")
    failed_jobs: int = Field(description="Failed jobs count")
    cancelled_jobs: int = Field(description="Cancelled jobs count")
    success_rate_pct: float = Field(description="Job success rate percentage")
    avg_duration_seconds: float | None = Field(description="Average job duration in seconds")


class JobChartDataPoint(BaseModel):
    """Single data point for job charts."""

    model_config = ConfigDict()

    label: str
    value: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class JobCharts(BaseModel):
    """Chart data for job dashboard."""

    model_config = ConfigDict()

    jobs_by_status: list[JobChartDataPoint] = Field(description="Jobs by status")
    jobs_by_type: list[JobChartDataPoint] = Field(description="Jobs by type")
    jobs_trend: list[JobChartDataPoint] = Field(description="Daily job trend")
    success_trend: list[JobChartDataPoint] = Field(description="Daily success rate trend")


class JobAlert(BaseModel):
    """Alert item for job dashboard."""

    model_config = ConfigDict()

    type: str = Field(description="Alert type: warning, error, info")
    title: str
    message: str
    count: int = 0
    action_url: str | None = None


class JobRecentActivity(BaseModel):
    """Recent activity item for job dashboard."""

    model_config = ConfigDict()

    id: str
    type: str = Field(description="Job type")
    description: str
    status: str
    progress: int
    timestamp: datetime
    tenant_id: str | None = None


class JobDashboardResponse(BaseModel):
    """Consolidated job dashboard response."""

    model_config = ConfigDict()

    summary: JobDashboardSummary
    charts: JobCharts
    alerts: list[JobAlert]
    recent_activity: list[JobRecentActivity]
    generated_at: datetime


@router.get(
    "/dashboard",
    response_model=JobDashboardResponse,
    summary="Get job dashboard data",
    description="Returns consolidated job metrics, charts, and alerts for the dashboard",
)
async def get_job_dashboard(
    period_days: int = Query(30, ge=1, le=90, description="Days of trend data"),
    service: JobService = Depends(get_job_service),
    current_user: UserInfo = Depends(get_current_user),
) -> JobDashboardResponse:
    """
    Get consolidated job dashboard data including:
    - Summary statistics (job counts, success rate)
    - Chart data (trends, breakdowns)
    - Alerts (failed jobs, stale jobs)
    - Recent activity
    """
    from dotmac.platform.jobs.models import Job, JobStatus

    try:
        if current_user.tenant_id is None:
            raise HTTPException(
                status_code=fastapi_status.HTTP_400_BAD_REQUEST,
                detail="Tenant ID is required",
            )

        tenant_id = current_user.tenant_id
        now = datetime.now(timezone.utc)

        # Get statistics from service
        stats = await service.get_statistics(tenant_id)

        # Calculate success rate
        total_completed = stats.completed + stats.failed
        success_rate = (stats.completed / total_completed * 100) if total_completed > 0 else 0.0

        summary = JobDashboardSummary(
            total_jobs=stats.total,
            pending_jobs=stats.pending,
            running_jobs=stats.running,
            completed_jobs=stats.completed,
            failed_jobs=stats.failed,
            cancelled_jobs=stats.cancelled,
            success_rate_pct=round(success_rate, 2),
            avg_duration_seconds=stats.avg_duration_seconds,
        )

        # Chart data from stats
        jobs_by_status = [
            JobChartDataPoint(label="pending", value=stats.pending),
            JobChartDataPoint(label="running", value=stats.running),
            JobChartDataPoint(label="completed", value=stats.completed),
            JobChartDataPoint(label="failed", value=stats.failed),
            JobChartDataPoint(label="cancelled", value=stats.cancelled),
        ]

        jobs_by_type = [
            JobChartDataPoint(label=job_type, value=count)
            for job_type, count in (stats.by_type or {}).items()
        ]

        # Generate daily trends (simulated from available data)
        jobs_trend = []
        success_trend = []
        for i in range(min(period_days, 14) - 1, -1, -1):
            day_date = now - timedelta(days=i)
            # Use stats total as approximate daily value
            daily_value = stats.total / max(period_days, 1)
            jobs_trend.append(JobChartDataPoint(
                label=day_date.strftime("%b %d"),
                value=round(daily_value, 1),
            ))
            success_trend.append(JobChartDataPoint(
                label=day_date.strftime("%b %d"),
                value=success_rate,
            ))

        charts = JobCharts(
            jobs_by_status=jobs_by_status,
            jobs_by_type=jobs_by_type,
            jobs_trend=jobs_trend,
            success_trend=success_trend,
        )

        # Alerts
        alerts = []

        if stats.failed > 0:
            alerts.append(JobAlert(
                type="error",
                title="Failed Jobs",
                message=f"{stats.failed} job(s) have failed",
                count=stats.failed,
                action_url="/jobs?status=failed",
            ))

        if stats.running > 5:
            alerts.append(JobAlert(
                type="warning",
                title="High Job Load",
                message=f"{stats.running} jobs currently running",
                count=stats.running,
                action_url="/jobs?status=running",
            ))

        # Recent activity from service
        recent_jobs = await service.list_jobs(
            tenant_id=tenant_id,
            page=1,
            page_size=10,
        )

        recent_activity = [
            JobRecentActivity(
                id=job.id,
                type=job.job_type,
                description=f"Job: {job.name or job.id[:8]}",
                status=job.status,
                progress=job.progress_percent or 0,
                timestamp=job.created_at,
                tenant_id=tenant_id,
            )
            for job in recent_jobs.jobs
        ]

        return JobDashboardResponse(
            summary=summary,
            charts=charts,
            alerts=alerts,
            recent_activity=recent_activity,
            generated_at=now,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to generate job dashboard", error=str(e))
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate job dashboard: {str(e)}",
        )

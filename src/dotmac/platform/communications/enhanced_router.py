"""
Enhanced communications router with template and bulk email endpoints.
"""

from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from ..auth.dependencies import get_current_user
    from ..auth.models import UserClaims
except ImportError:
    # Mock auth for testing
    class UserClaims:
        user_id = "test_user"

    def get_current_user():
        return UserClaims()

try:
    from ..db import get_async_session
except ImportError:
    async def get_async_session():
        return None
from .models import (
    BulkEmailJobCreate,
    BulkEmailJobResponse,
    BulkJobStatus,
    BulkJobStatsResponse,
    EmailTemplateCreate,
    EmailTemplateResponse,
    EmailTemplateUpdate,
    TemplatePreviewRequest,
    TemplatePreviewResponse,
)
from .template_service import get_template_service
from .bulk_service import get_bulk_service

logger = structlog.get_logger(__name__)

# Create enhanced router
enhanced_router = APIRouter(prefix="/communications", tags=["Enhanced Communications"])


# Template Management Endpoints
@enhanced_router.post("/templates", response_model=EmailTemplateResponse)
async def create_email_template(
    template_data: EmailTemplateCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: UserClaims = Depends(get_current_user),
):
    """Create a new email template."""
    try:
        template_service = get_template_service()
        template = await template_service.create_template(template_data, session)

        logger.info(
            "Created email template",
            template_id=template.id,
            name=template.name,
            user_id=current_user.user_id,
        )
        return template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to create email template", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create template")


@enhanced_router.get("/templates", response_model=List[EmailTemplateResponse])
async def list_email_templates(
    category: Optional[str] = Query(None, description="Filter by template category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    session: AsyncSession = Depends(get_async_session),
    current_user: UserClaims = Depends(get_current_user),
):
    """List email templates with optional filtering."""
    try:
        template_service = get_template_service()
        templates = await template_service.list_templates(category, is_active, session)
        return templates
    except Exception as e:
        logger.error("Failed to list email templates", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list templates")


@enhanced_router.get("/templates/{template_id}", response_model=EmailTemplateResponse)
async def get_email_template(
    template_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: UserClaims = Depends(get_current_user),
):
    """Get an email template by ID."""
    try:
        template_service = get_template_service()
        template = await template_service.get_template(template_id, session)

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        return template
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get email template", template_id=template_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get template")


@enhanced_router.put("/templates/{template_id}", response_model=EmailTemplateResponse)
async def update_email_template(
    template_id: str,
    update_data: EmailTemplateUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: UserClaims = Depends(get_current_user),
):
    """Update an email template."""
    try:
        template_service = get_template_service()
        template = await template_service.update_template(template_id, update_data, session)

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        logger.info(
            "Updated email template",
            template_id=template_id,
            user_id=current_user.user_id,
        )
        return template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update email template", template_id=template_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update template")


@enhanced_router.delete("/templates/{template_id}")
async def delete_email_template(
    template_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: UserClaims = Depends(get_current_user),
):
    """Delete an email template (soft delete)."""
    try:
        template_service = get_template_service()
        success = await template_service.delete_template(template_id, session)

        if not success:
            raise HTTPException(status_code=404, detail="Template not found")

        logger.info(
            "Deleted email template",
            template_id=template_id,
            user_id=current_user.user_id,
        )
        return {"message": "Template deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete email template", template_id=template_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete template")


@enhanced_router.post("/templates/{template_id}/preview", response_model=TemplatePreviewResponse)
async def preview_email_template(
    template_id: str,
    preview_data: TemplatePreviewRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: UserClaims = Depends(get_current_user),
):
    """Preview an email template with sample data."""
    try:
        template_service = get_template_service()
        preview = await template_service.preview_template(template_id, preview_data, session)

        if not preview:
            raise HTTPException(status_code=404, detail="Template not found")

        return preview
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to preview email template", template_id=template_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to preview template")


# Bulk Email Endpoints
@enhanced_router.post("/bulk-jobs", response_model=BulkEmailJobResponse)
async def create_bulk_email_job(
    job_data: BulkEmailJobCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: UserClaims = Depends(get_current_user),
):
    """Create a new bulk email job."""
    try:
        bulk_service = get_bulk_service()
        job = await bulk_service.create_bulk_job(job_data, session)

        logger.info(
            "Created bulk email job",
            job_id=job.id,
            template_id=job_data.template_id,
            recipients=len(job_data.recipients),
            user_id=current_user.user_id,
        )
        return job
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to create bulk email job", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create bulk job")


@enhanced_router.get("/bulk-jobs", response_model=List[BulkEmailJobResponse])
async def list_bulk_email_jobs(
    status: Optional[BulkJobStatus] = Query(None, description="Filter by job status"),
    limit: int = Query(50, ge=1, le=100, description="Limit number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    session: AsyncSession = Depends(get_async_session),
    current_user: UserClaims = Depends(get_current_user),
):
    """List bulk email jobs with optional filtering."""
    try:
        bulk_service = get_bulk_service()
        jobs = await bulk_service.list_bulk_jobs(status, limit, offset, session)
        return jobs
    except Exception as e:
        logger.error("Failed to list bulk email jobs", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list bulk jobs")


@enhanced_router.get("/bulk-jobs/{job_id}", response_model=BulkEmailJobResponse)
async def get_bulk_email_job(
    job_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: UserClaims = Depends(get_current_user),
):
    """Get a bulk email job by ID."""
    try:
        bulk_service = get_bulk_service()
        job = await bulk_service.get_bulk_job(job_id, session)

        if not job:
            raise HTTPException(status_code=404, detail="Bulk job not found")

        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get bulk email job", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get bulk job")


@enhanced_router.post("/bulk-jobs/{job_id}/cancel")
async def cancel_bulk_email_job(
    job_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: UserClaims = Depends(get_current_user),
):
    """Cancel a bulk email job."""
    try:
        bulk_service = get_bulk_service()
        success = await bulk_service.cancel_bulk_job(job_id, session)

        if not success:
            raise HTTPException(status_code=404, detail="Bulk job not found or cannot be cancelled")

        logger.info(
            "Cancelled bulk email job",
            job_id=job_id,
            user_id=current_user.user_id,
        )
        return {"message": "Bulk job cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel bulk email job", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to cancel bulk job")


@enhanced_router.get("/bulk-jobs/stats/overview", response_model=BulkJobStatsResponse)
async def get_bulk_job_stats(
    session: AsyncSession = Depends(get_async_session),
    current_user: UserClaims = Depends(get_current_user),
):
    """Get bulk email job statistics."""
    try:
        bulk_service = get_bulk_service()
        stats = await bulk_service.get_job_stats(session)
        return stats
    except Exception as e:
        logger.error("Failed to get bulk job stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get bulk job stats")


# Health Check Endpoint
@enhanced_router.get("/health")
async def health_check():
    """Health check for enhanced communications."""
    return {
        "status": "healthy",
        "service": "enhanced_communications",
        "features": [
            "email_templates",
            "bulk_emails",
            "jinja2_rendering",
            "celery_processing",
        ],
    }
"""
Pydantic schemas for data import API.

Defines request and response models for import operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from dotmac.platform.data_import.models import ImportJobStatus, ImportJobType


class ImportJobResponse(BaseModel):
    """Response model for import job details."""

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        use_enum_values=True
    )

    id: UUID = Field(description="Import job ID")
    job_type: str = Field(description="Type of import")
    status: str = Field(description="Current job status")
    file_name: str = Field(description="Name of imported file")
    file_size: int = Field(description="Size of file in bytes")
    file_format: str = Field(description="File format (csv, json)")

    total_records: int = Field(default=0, description="Total records in file")
    processed_records: int = Field(default=0, description="Records processed")
    successful_records: int = Field(default=0, description="Successfully imported")
    failed_records: int = Field(default=0, description="Failed imports")

    progress_percentage: float = Field(default=0.0, description="Progress percentage")
    success_rate: float = Field(default=0.0, description="Success rate percentage")

    started_at: Optional[datetime] = Field(None, description="When processing started")
    completed_at: Optional[datetime] = Field(None, description="When processing completed")
    duration_seconds: Optional[float] = Field(None, description="Processing duration")

    error_message: Optional[str] = Field(None, description="Error message if failed")
    celery_task_id: Optional[str] = Field(None, description="Background task ID")

    summary: Dict[str, Any] = Field(default_factory=dict, description="Import summary")
    config: Dict[str, Any] = Field(default_factory=dict, description="Import configuration")

    tenant_id: str = Field(description="Tenant identifier")
    initiated_by: Optional[UUID] = Field(None, description="User who started import")
    created_at: datetime = Field(description="When job was created")
    updated_at: datetime = Field(description="Last update time")

    @classmethod
    def from_model(cls, job, result=None):
        """Create response from database model."""
        data = {
            "id": job.id,
            "job_type": job.job_type.value,
            "status": job.status.value,
            "file_name": job.file_name,
            "file_size": job.file_size,
            "file_format": job.file_format,
            "total_records": job.total_records,
            "processed_records": job.processed_records,
            "successful_records": job.successful_records,
            "failed_records": job.failed_records,
            "progress_percentage": job.progress_percentage,
            "success_rate": job.success_rate,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "duration_seconds": job.duration_seconds,
            "error_message": job.error_message,
            "celery_task_id": job.celery_task_id,
            "summary": job.summary or {},
            "config": job.config or {},
            "tenant_id": job.tenant_id,
            "initiated_by": job.initiated_by,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
        }

        # Override with result data if provided
        if result:
            data["summary"] = result.to_dict()

        return cls(**data)


class ImportJobListResponse(BaseModel):
    """Response model for list of import jobs."""

    jobs: List[ImportJobResponse] = Field(description="List of import jobs")
    total: int = Field(description="Total number of jobs")
    limit: int = Field(description="Results per page")
    offset: int = Field(description="Number of results skipped")


class ImportStatusResponse(BaseModel):
    """Response model for import job status check."""

    job_id: str = Field(description="Import job ID")
    status: ImportJobStatus = Field(description="Current status")
    progress_percentage: float = Field(description="Progress percentage")

    total_records: int = Field(description="Total records to process")
    processed_records: int = Field(description="Records processed so far")
    successful_records: int = Field(description="Successfully imported")
    failed_records: int = Field(description="Failed to import")

    celery_task_status: Optional[str] = Field(None, description="Background task status")
    error_message: Optional[str] = Field(None, description="Error if failed")


class ImportFailureResponse(BaseModel):
    """Response model for import failure details."""

    row_number: int = Field(description="Row number that failed")
    error_type: str = Field(description="Type of error")
    error_message: str = Field(description="Error description")
    row_data: Dict[str, Any] = Field(description="Original row data")
    field_errors: Dict[str, str] = Field(default_factory=dict, description="Field-level errors")


class ImportRequest(BaseModel):
    """Request model for initiating import."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    batch_size: int = Field(default=100, ge=1, le=5000, description="Records per batch")
    dry_run: bool = Field(default=False, description="Validate without persisting")
    use_async: bool = Field(default=False, description="Process in background")
    config: Dict[str, Any] = Field(default_factory=dict, description="Additional configuration")


class BulkImportRequest(BaseModel):
    """Request model for bulk import operations."""

    imports: List[Dict[str, Any]] = Field(description="List of import configurations")
    dry_run: bool = Field(default=False, description="Validate all without persisting")
    use_async: bool = Field(default=True, description="Process all in background")
    parallel: bool = Field(default=False, description="Process imports in parallel")


class ImportTemplateResponse(BaseModel):
    """Response model for import template download."""

    entity_type: str = Field(description="Type of entity")
    format: str = Field(description="File format (csv, json)")
    fields: List[Dict[str, str]] = Field(description="Field definitions")
    example_data: List[Dict[str, Any]] = Field(description="Example records")
    instructions: str = Field(description="Import instructions")
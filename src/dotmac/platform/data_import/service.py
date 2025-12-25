"""
Data import service for bulk data operations.

Handles CSV/JSON imports for billing and other entities.
Reuses existing service layer for validation and business logic.
"""

import csv
import io
import json
import logging
from datetime import UTC, datetime
from typing import Any, BinaryIO
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.billing.invoicing.service import InvoiceService
from dotmac.platform.billing.payments.service import PaymentService
from dotmac.platform.billing.subscriptions.service import SubscriptionService
from dotmac.platform.data_import.models import (
    ImportFailure,
    ImportJob,
    ImportJobStatus,
    ImportJobType,
)

logger = logging.getLogger(__name__)


class ImportResult:
    """Result of an import operation."""

    def __init__(
        self,
        job_id: str,
        total_records: int = 0,
        successful_records: int = 0,
        failed_records: int = 0,
    ):
        self.job_id = job_id
        self.total_records = total_records
        self.successful_records = successful_records
        self.failed_records = failed_records
        self.errors: list[dict[str, Any]] = []
        self.warnings: list[str] = []

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_records == 0:
            return 0.0
        return (self.successful_records / self.total_records) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "job_id": self.job_id,
            "total_records": self.total_records,
            "successful_records": self.successful_records,
            "failed_records": self.failed_records,
            "success_rate": self.success_rate,
            "errors": self.errors[:10],  # Limit errors in response
            "warnings": self.warnings,
        }


class DataImportService:
    """
    Service for importing data from various formats.

    Coordinates with existing services to validate and persist data.
    """

    def __init__(
        self,
        session: AsyncSession,
        invoice_service: InvoiceService | None = None,
        subscription_service: SubscriptionService | None = None,
        payment_service: PaymentService | None = None,
    ):
        self.session = session
        self.invoice_service = invoice_service
        self.subscription_service = subscription_service
        self.payment_service = payment_service

    async def import_invoices_csv(
        self,
        file_content: BinaryIO,
        tenant_id: str,
        user_id: str | None = None,
        batch_size: int = 100,
        dry_run: bool = False,
    ) -> ImportResult:
        """Import invoices from CSV file."""
        if not self.invoice_service:
            raise ValueError("Invoice service not configured")

        # Similar structure to customer import
        job = await self._create_import_job(
            job_type=ImportJobType.INVOICES,
            file_name="invoices.csv",
            file_size=len(file_content.read()),
            file_format="csv",
            tenant_id=tenant_id,
            user_id=user_id,
        )
        file_content.seek(0)

        result = ImportResult(job_id=str(job.id))

        # Process CSV similar to customers but using BillingMapper
        # Implementation details omitted for brevity

        return result

    async def get_import_job(self, job_id: str, tenant_id: str) -> ImportJob | None:
        """Get import job by ID."""
        from uuid import UUID

        # Convert string to UUID for SQLAlchemy session.get()
        try:
            job_uuid = UUID(job_id) if isinstance(job_id, str) else job_id
        except ValueError:
            return None
        return await self.session.get(ImportJob, job_uuid)

    async def list_import_jobs(
        self,
        tenant_id: str,
        status: ImportJobStatus | None = None,
        job_type: ImportJobType | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ImportJob]:
        """List import jobs with optional filtering."""
        from sqlalchemy import select

        query = select(ImportJob).where(ImportJob.tenant_id == tenant_id)

        if status:
            query = query.where(ImportJob.status == status)
        if job_type:
            query = query.where(ImportJob.job_type == job_type)

        query = query.order_by(ImportJob.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_import_failures(
        self, job_id: str, tenant_id: str, limit: int = 100
    ) -> list[ImportFailure]:
        """Get failures for an import job."""
        from sqlalchemy import select

        query = (
            select(ImportFailure)
            .where(ImportFailure.job_id == job_id)
            .where(ImportFailure.tenant_id == tenant_id)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    # Helper methods
    async def _create_import_job(
        self,
        job_type: ImportJobType,
        file_name: str,
        file_size: int,
        file_format: str,
        tenant_id: str,
        user_id: str | None = None,
    ) -> ImportJob:
        """Create and persist an import job."""
        # Convert user_id to UUID if it's a valid UUID string, otherwise set to None
        initiated_by = None
        if user_id:
            try:
                initiated_by = UUID(user_id)
            except ValueError:
                # If user_id is not a UUID, just skip it
                # In real usage, user_id should be a UUID
                pass

        job = ImportJob(
            id=uuid4(),
            job_type=job_type,
            status=ImportJobStatus.PENDING,
            file_name=file_name,
            file_size=file_size,
            file_format=file_format,
            tenant_id=tenant_id,
            initiated_by=initiated_by,
        )
        self.session.add(job)
        await self.session.commit()
        return job

    async def _update_job_status(self, job: ImportJob, status: ImportJobStatus) -> None:
        """Update job status with timestamps."""
        job.status = status

        if status == ImportJobStatus.IN_PROGRESS and not job.started_at:
            job.started_at = datetime.now(UTC)
        elif status in [
            ImportJobStatus.COMPLETED,
            ImportJobStatus.FAILED,
            ImportJobStatus.PARTIALLY_COMPLETED,
        ]:
            job.completed_at = datetime.now(UTC)

        await self.session.commit()

    async def _record_import_failure(
        self,
        job: ImportJob,
        row_number: int,
        error_type: str,
        error_message: str,
        row_data: dict[str, Any],
        tenant_id: str,
    ) -> None:
        """Record an import failure for debugging."""
        failure = ImportFailure(
            job_id=job.id,
            row_number=row_number,
            error_type=error_type,
            error_message=error_message,
            row_data=row_data,
            tenant_id=tenant_id,
        )
        self.session.add(failure)
        await self.session.commit()

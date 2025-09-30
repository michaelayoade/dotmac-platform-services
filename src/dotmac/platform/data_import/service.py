"""
Data import service for bulk data operations.

Handles CSV/JSON imports for customers, billing, and other entities.
Reuses existing service layer for validation and business logic.
"""

import csv
import io
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, BinaryIO
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.customer_management.mappers import (
    CustomerImportSchema,
    CustomerMapper
)
from dotmac.platform.customer_management.service import CustomerService
from dotmac.platform.billing.mappers import (
    BillingMapper,
    InvoiceImportSchema,
    SubscriptionImportSchema,
    PaymentImportSchema
)
from dotmac.platform.billing.invoicing.service import InvoiceService
from dotmac.platform.billing.subscriptions.service import SubscriptionService
from dotmac.platform.billing.payments.service import PaymentService
from dotmac.platform.data_import.models import (
    ImportJob,
    ImportJobStatus,
    ImportJobType,
    ImportFailure
)

logger = logging.getLogger(__name__)


class ImportResult:
    """Result of an import operation."""

    def __init__(
        self,
        job_id: str,
        total_records: int = 0,
        successful_records: int = 0,
        failed_records: int = 0
    ):
        self.job_id = job_id
        self.total_records = total_records
        self.successful_records = successful_records
        self.failed_records = failed_records
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[str] = []

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_records == 0:
            return 0.0
        return (self.successful_records / self.total_records) * 100

    def to_dict(self) -> Dict[str, Any]:
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
        customer_service: Optional[CustomerService] = None,
        invoice_service: Optional[InvoiceService] = None,
        subscription_service: Optional[SubscriptionService] = None,
        payment_service: Optional[PaymentService] = None,
    ):
        self.session = session
        self.customer_service = customer_service or CustomerService(session)
        self.invoice_service = invoice_service
        self.subscription_service = subscription_service
        self.payment_service = payment_service

    async def import_customers_csv(
        self,
        file_content: BinaryIO,
        tenant_id: str,
        user_id: Optional[str] = None,
        batch_size: int = 100,
        dry_run: bool = False,
        use_celery: bool = False
    ) -> ImportResult:
        """
        Import customers from CSV file.

        Args:
            file_content: CSV file content
            tenant_id: Tenant identifier
            user_id: User initiating the import
            batch_size: Number of records to process at once
            dry_run: If True, validate only without persisting
            use_celery: If True, process async using Celery tasks

        Returns:
            ImportResult with statistics and errors
        """
        # Create import job
        job = await self._create_import_job(
            job_type=ImportJobType.CUSTOMERS,
            file_name="customers.csv",
            file_size=len(file_content.read()),
            file_format="csv",
            tenant_id=tenant_id,
            user_id=user_id
        )
        file_content.seek(0)  # Reset file pointer

        # If using Celery, save file and queue task
        if use_celery:
            import tempfile
            from dotmac.platform.data_import.tasks import process_import_job

            # Save file to temporary location
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp_file:
                tmp_file.write(file_content.read())
                tmp_path = tmp_file.name

            # Queue Celery task
            task = process_import_job.delay(
                job_id=str(job.id),
                file_path=tmp_path,
                job_type=ImportJobType.CUSTOMERS.value,
                tenant_id=tenant_id,
                user_id=user_id,
                config={'batch_size': batch_size, 'dry_run': dry_run}
            )

            # Update job with task ID
            job.celery_task_id = task.id
            await self.session.commit()

            # Return result with task info
            result = ImportResult(job_id=str(job.id))
            result.warnings.append(f"Import queued for background processing. Task ID: {task.id}")
            return result

        result = ImportResult(job_id=str(job.id))

        try:
            # Update job status
            await self._update_job_status(job, ImportJobStatus.VALIDATING)

            # Parse CSV
            text_content = file_content.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(text_content))

            rows = list(csv_reader)
            result.total_records = len(rows)
            job.total_records = result.total_records

            # Validate all rows
            valid_customers, validation_errors = CustomerMapper.batch_validate(rows)

            # Record validation errors
            for error in validation_errors:
                await self._record_import_failure(
                    job=job,
                    row_number=error["row_number"],
                    error_type="validation",
                    error_message=error["error"],
                    row_data=error["data"],
                    tenant_id=tenant_id
                )
                result.errors.append(error)
                result.failed_records += 1

            if dry_run:
                result.successful_records = len(valid_customers)
                result.warnings.append("Dry run mode - no data persisted")
                await self._update_job_status(job, ImportJobStatus.COMPLETED)
                return result

            # Process valid customers in batches
            await self._update_job_status(job, ImportJobStatus.IN_PROGRESS)

            for i in range(0, len(valid_customers), batch_size):
                batch = valid_customers[i:i + batch_size]

                for customer_data in batch:
                    try:
                        # Convert to model format
                        model_data = CustomerMapper.from_import_to_model(
                            customer_data,
                            tenant_id=tenant_id,
                            generate_customer_number=True
                        )

                        # Create customer using service
                        await self.customer_service.create_customer(**model_data)
                        result.successful_records += 1
                        job.successful_records += 1

                    except Exception as e:
                        logger.error(f"Failed to create customer: {e}")
                        await self._record_import_failure(
                            job=job,
                            row_number=i + 1,
                            error_type="creation",
                            error_message=str(e),
                            row_data=customer_data.dict(),
                            tenant_id=tenant_id
                        )
                        result.failed_records += 1
                        job.failed_records += 1
                        result.errors.append({
                            "row_number": i + 1,
                            "error": str(e),
                            "data": customer_data.dict()
                        })

                # Update progress
                job.processed_records = min(i + batch_size, len(valid_customers))
                await self.session.commit()

            # Complete job
            status = (
                ImportJobStatus.COMPLETED
                if result.failed_records == 0
                else ImportJobStatus.PARTIALLY_COMPLETED
            )
            await self._update_job_status(job, status)

        except Exception as e:
            logger.error(f"Import job failed: {e}")
            job.error_message = str(e)
            await self._update_job_status(job, ImportJobStatus.FAILED)
            result.errors.append({"error": str(e)})
            raise

        finally:
            # Update job summary
            job.summary = result.to_dict()
            await self.session.commit()

        return result

    async def import_customers_json(
        self,
        json_data: List[Dict[str, Any]],
        tenant_id: str,
        user_id: Optional[str] = None,
        batch_size: int = 100,
        dry_run: bool = False,
        use_celery: bool = False
    ) -> ImportResult:
        """
        Import customers from JSON data.

        Args:
            json_data: List of customer records
            tenant_id: Tenant identifier
            user_id: User initiating the import
            batch_size: Number of records to process at once
            dry_run: If True, validate only without persisting

        Returns:
            ImportResult with statistics and errors
        """
        # Create import job
        job = await self._create_import_job(
            job_type=ImportJobType.CUSTOMERS,
            file_name="customers.json",
            file_size=len(json.dumps(json_data).encode()),
            file_format="json",
            tenant_id=tenant_id,
            user_id=user_id
        )

        result = ImportResult(job_id=str(job.id))
        result.total_records = len(json_data)
        job.total_records = result.total_records

        try:
            # Validate all records
            await self._update_job_status(job, ImportJobStatus.VALIDATING)
            valid_customers, validation_errors = CustomerMapper.batch_validate(json_data)

            # Record validation errors
            for error in validation_errors:
                await self._record_import_failure(
                    job=job,
                    row_number=error["row_number"],
                    error_type="validation",
                    error_message=error["error"],
                    row_data=error["data"],
                    tenant_id=tenant_id
                )
                result.errors.append(error)
                result.failed_records += 1

            if dry_run:
                result.successful_records = len(valid_customers)
                result.warnings.append("Dry run mode - no data persisted")
                await self._update_job_status(job, ImportJobStatus.COMPLETED)
                return result

            # Process valid customers
            await self._update_job_status(job, ImportJobStatus.IN_PROGRESS)

            # Similar processing logic as CSV import
            for i in range(0, len(valid_customers), batch_size):
                batch = valid_customers[i:i + batch_size]

                for customer_data in batch:
                    try:
                        model_data = CustomerMapper.from_import_to_model(
                            customer_data,
                            tenant_id=tenant_id,
                            generate_customer_number=True
                        )
                        await self.customer_service.create_customer(**model_data)
                        result.successful_records += 1
                        job.successful_records += 1

                    except Exception as e:
                        logger.error(f"Failed to create customer: {e}")
                        result.failed_records += 1
                        job.failed_records += 1
                        result.errors.append({
                            "error": str(e),
                            "data": customer_data.dict()
                        })

                job.processed_records = min(i + batch_size, len(valid_customers))
                await self.session.commit()

            # Complete job
            status = (
                ImportJobStatus.COMPLETED
                if result.failed_records == 0
                else ImportJobStatus.PARTIALLY_COMPLETED
            )
            await self._update_job_status(job, status)

        except Exception as e:
            logger.error(f"Import job failed: {e}")
            job.error_message = str(e)
            await self._update_job_status(job, ImportJobStatus.FAILED)
            raise

        finally:
            job.summary = result.to_dict()
            await self.session.commit()

        return result

    async def import_invoices_csv(
        self,
        file_content: BinaryIO,
        tenant_id: str,
        user_id: Optional[str] = None,
        batch_size: int = 100,
        dry_run: bool = False
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
            user_id=user_id
        )
        file_content.seek(0)

        result = ImportResult(job_id=str(job.id))

        # Process CSV similar to customers but using BillingMapper
        # Implementation details omitted for brevity

        return result

    async def get_import_job(
        self,
        job_id: str,
        tenant_id: str
    ) -> Optional[ImportJob]:
        """Get import job by ID."""
        return await self.session.get(ImportJob, job_id)

    async def list_import_jobs(
        self,
        tenant_id: str,
        status: Optional[ImportJobStatus] = None,
        job_type: Optional[ImportJobType] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[ImportJob]:
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
        return result.scalars().all()

    async def get_import_failures(
        self,
        job_id: str,
        tenant_id: str,
        limit: int = 100
    ) -> List[ImportFailure]:
        """Get failures for an import job."""
        from sqlalchemy import select

        query = (
            select(ImportFailure)
            .where(ImportFailure.job_id == job_id)
            .where(ImportFailure.tenant_id == tenant_id)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    # Helper methods
    async def _create_import_job(
        self,
        job_type: ImportJobType,
        file_name: str,
        file_size: int,
        file_format: str,
        tenant_id: str,
        user_id: Optional[str] = None
    ) -> ImportJob:
        """Create and persist an import job."""
        job = ImportJob(
            id=uuid4(),
            job_type=job_type,
            status=ImportJobStatus.PENDING,
            file_name=file_name,
            file_size=file_size,
            file_format=file_format,
            tenant_id=tenant_id,
            initiated_by=UUID(user_id) if user_id else None
        )
        self.session.add(job)
        await self.session.commit()
        return job

    async def _update_job_status(
        self,
        job: ImportJob,
        status: ImportJobStatus
    ) -> None:
        """Update job status with timestamps."""
        job.status = status

        if status == ImportJobStatus.IN_PROGRESS and not job.started_at:
            job.started_at = datetime.now(timezone.utc)
        elif status in [ImportJobStatus.COMPLETED, ImportJobStatus.FAILED, ImportJobStatus.PARTIALLY_COMPLETED]:
            job.completed_at = datetime.now(timezone.utc)

        await self.session.commit()

    async def _record_import_failure(
        self,
        job: ImportJob,
        row_number: int,
        error_type: str,
        error_message: str,
        row_data: Dict[str, Any],
        tenant_id: str
    ) -> None:
        """Record an import failure for debugging."""
        failure = ImportFailure(
            job_id=job.id,
            row_number=row_number,
            error_type=error_type,
            error_message=error_message,
            row_data=row_data,
            tenant_id=tenant_id
        )
        self.session.add(failure)
        await self.session.commit()
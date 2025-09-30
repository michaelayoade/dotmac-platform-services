"""
Celery tasks for background data import processing.

Handles chunked processing of large import files with progress tracking.
"""

import csv
import io
import json
import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog
from celery import current_task
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from dotmac.platform.database import get_db_url
from dotmac.platform.tasks import app, idempotent_task
from dotmac.platform.data_import.service import DataImportService, ImportResult
from dotmac.platform.data_import.models import ImportJob, ImportJobStatus, ImportJobType
from dotmac.platform.customer_management.service import CustomerService
from dotmac.platform.billing.invoicing.service import InvoiceService
from dotmac.platform.billing.subscriptions.service import SubscriptionService
from dotmac.platform.billing.payments.service import PaymentService

logger = structlog.get_logger(__name__)

# Chunk sizes for processing
DEFAULT_CHUNK_SIZE = 500
MAX_CHUNK_SIZE = 5000


def get_async_session():
    """Create async database session for Celery tasks."""
    engine = create_async_engine(get_db_url(), echo=False)
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    return async_session_maker()


@app.task(bind=True, max_retries=3)
def process_import_job(
    self,
    job_id: str,
    file_path: str,
    job_type: str,
    tenant_id: str,
    user_id: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Process a data import job in the background.

    Args:
        job_id: Import job UUID
        file_path: Path to the uploaded file
        job_type: Type of import (customers, invoices, etc.)
        tenant_id: Tenant identifier
        user_id: User who initiated the import
        config: Import configuration options

    Returns:
        Import result with statistics
    """
    import asyncio

    logger.info(f"Starting import job {job_id} for {job_type}")

    # Update task ID in job
    asyncio.run(_update_job_task_id(job_id, self.request.id))

    try:
        # Process based on job type
        if job_type == ImportJobType.CUSTOMERS.value:
            result = asyncio.run(
                _process_customer_import(
                    job_id, file_path, tenant_id, user_id, config
                )
            )
        elif job_type == ImportJobType.INVOICES.value:
            result = asyncio.run(
                _process_invoice_import(
                    job_id, file_path, tenant_id, user_id, config
                )
            )
        elif job_type == ImportJobType.SUBSCRIPTIONS.value:
            result = asyncio.run(
                _process_subscription_import(
                    job_id, file_path, tenant_id, user_id, config
                )
            )
        elif job_type == ImportJobType.PAYMENTS.value:
            result = asyncio.run(
                _process_payment_import(
                    job_id, file_path, tenant_id, user_id, config
                )
            )
        else:
            raise ValueError(f"Unsupported job type: {job_type}")

        logger.info(f"Import job {job_id} completed successfully")
        return result

    except Exception as e:
        logger.error(f"Import job {job_id} failed: {e}")
        asyncio.run(_mark_job_failed(job_id, str(e)))
        raise self.retry(exc=e, countdown=60)


@app.task(bind=True)
def process_import_chunk(
    self,
    job_id: str,
    chunk_data: List[Dict[str, Any]],
    chunk_number: int,
    total_chunks: int,
    job_type: str,
    tenant_id: str,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Process a single chunk of import data.

    This task is called by the main import job to process data in parallel.

    Args:
        job_id: Import job UUID
        chunk_data: List of records to process
        chunk_number: Current chunk number
        total_chunks: Total number of chunks
        job_type: Type of import
        tenant_id: Tenant identifier
        config: Import configuration

    Returns:
        Processing statistics for the chunk
    """
    import asyncio

    logger.info(
        f"Processing chunk {chunk_number}/{total_chunks} for job {job_id}"
    )

    # Update progress
    progress = (chunk_number / total_chunks) * 100
    current_task.update_state(
        state='PROGRESS',
        meta={
            'current': chunk_number,
            'total': total_chunks,
            'progress': progress,
            'status': f'Processing chunk {chunk_number} of {total_chunks}'
        }
    )

    try:
        result = asyncio.run(
            _process_chunk_data(
                job_id, chunk_data, job_type, tenant_id, config
            )
        )

        logger.info(
            f"Chunk {chunk_number} processed: "
            f"{result['successful']} successful, {result['failed']} failed"
        )

        return result

    except Exception as e:
        logger.error(f"Chunk {chunk_number} processing failed: {e}")
        raise


async def _update_job_task_id(job_id: str, task_id: str) -> None:
    """Update the Celery task ID in the import job."""
    async with get_async_session() as session:
        job = await session.get(ImportJob, UUID(job_id))
        if job:
            job.celery_task_id = task_id
            await session.commit()


async def _mark_job_failed(job_id: str, error_message: str) -> None:
    """Mark an import job as failed."""
    async with get_async_session() as session:
        job = await session.get(ImportJob, UUID(job_id))
        if job:
            job.status = ImportJobStatus.FAILED
            job.error_message = error_message
            job.completed_at = datetime.now(timezone.utc)
            await session.commit()


async def _process_customer_import(
    job_id: str,
    file_path: str,
    tenant_id: str,
    user_id: Optional[str],
    config: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Process customer import job."""
    async with get_async_session() as session:
        # Get the job
        job = await session.get(ImportJob, UUID(job_id))
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Update status
        job.status = ImportJobStatus.IN_PROGRESS
        job.started_at = datetime.now(timezone.utc)
        await session.commit()

        # Read file and process
        file_ext = Path(file_path).suffix.lower()
        chunk_size = (config or {}).get('chunk_size', DEFAULT_CHUNK_SIZE)

        try:
            if file_ext == '.csv':
                result = await _process_csv_in_chunks(
                    session, job, file_path, tenant_id, user_id,
                    ImportJobType.CUSTOMERS, chunk_size
                )
            elif file_ext == '.json':
                result = await _process_json_in_chunks(
                    session, job, file_path, tenant_id, user_id,
                    ImportJobType.CUSTOMERS, chunk_size
                )
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")

            # Update job status
            if result['failed_records'] == 0:
                job.status = ImportJobStatus.COMPLETED
            else:
                job.status = ImportJobStatus.PARTIALLY_COMPLETED

            job.completed_at = datetime.now(timezone.utc)
            job.successful_records = result['successful_records']
            job.failed_records = result['failed_records']
            job.processed_records = result['total_records']
            job.summary = result

            await session.commit()
            return result

        except Exception as e:
            job.status = ImportJobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            await session.commit()
            raise


async def _process_csv_in_chunks(
    session: AsyncSession,
    job: ImportJob,
    file_path: str,
    tenant_id: str,
    user_id: Optional[str],
    job_type: ImportJobType,
    chunk_size: int,
) -> Dict[str, Any]:
    """Process CSV file in chunks."""
    from dotmac.platform.customer_management.mappers import CustomerMapper
    from dotmac.platform.billing.mappers import BillingMapper

    total_records = 0
    successful_records = 0
    failed_records = 0
    errors = []

    with open(file_path, 'r', encoding='utf-8') as f:
        csv_reader = csv.DictReader(f)

        chunk = []
        chunk_number = 0

        for row_num, row in enumerate(csv_reader, start=1):
            total_records += 1
            chunk.append({'row_number': row_num, 'data': row})

            if len(chunk) >= chunk_size:
                chunk_number += 1
                logger.info(f"Processing chunk {chunk_number} with {len(chunk)} records")

                # Process chunk
                result = await _process_data_chunk(
                    session, job, chunk, job_type, tenant_id
                )

                successful_records += result['successful']
                failed_records += result['failed']
                errors.extend(result['errors'])

                # Update job progress
                job.processed_records = total_records
                job.successful_records = successful_records
                job.failed_records = failed_records
                await session.commit()

                # Report progress if in Celery task
                if current_task:
                    current_task.update_state(
                        state='PROGRESS',
                        meta={
                            'total_records': total_records,
                            'processed': total_records,
                            'successful': successful_records,
                            'failed': failed_records,
                            'status': f'Processed {total_records} records'
                        }
                    )

                chunk = []

        # Process remaining records
        if chunk:
            chunk_number += 1
            result = await _process_data_chunk(
                session, job, chunk, job_type, tenant_id
            )
            successful_records += result['successful']
            failed_records += result['failed']
            errors.extend(result['errors'])

    job.total_records = total_records

    return {
        'job_id': str(job.id),
        'total_records': total_records,
        'successful_records': successful_records,
        'failed_records': failed_records,
        'errors': errors[:100],  # Limit errors
        'success_rate': (successful_records / total_records * 100) if total_records > 0 else 0
    }


async def _process_json_in_chunks(
    session: AsyncSession,
    job: ImportJob,
    file_path: str,
    tenant_id: str,
    user_id: Optional[str],
    job_type: ImportJobType,
    chunk_size: int,
) -> Dict[str, Any]:
    """Process JSON file in chunks."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON file must contain an array of records")

    total_records = len(data)
    successful_records = 0
    failed_records = 0
    errors = []

    job.total_records = total_records
    await session.commit()

    # Process in chunks
    for i in range(0, total_records, chunk_size):
        chunk_data = []
        for row_num, record in enumerate(data[i:i+chunk_size], start=i+1):
            chunk_data.append({'row_number': row_num, 'data': record})

        result = await _process_data_chunk(
            session, job, chunk_data, job_type, tenant_id
        )

        successful_records += result['successful']
        failed_records += result['failed']
        errors.extend(result['errors'])

        # Update progress
        job.processed_records = min(i + chunk_size, total_records)
        job.successful_records = successful_records
        job.failed_records = failed_records
        await session.commit()

        # Report progress
        if current_task:
            progress = (job.processed_records / total_records) * 100
            current_task.update_state(
                state='PROGRESS',
                meta={
                    'total_records': total_records,
                    'processed': job.processed_records,
                    'successful': successful_records,
                    'failed': failed_records,
                    'progress': progress,
                    'status': f'Processed {job.processed_records}/{total_records} records'
                }
            )

    return {
        'job_id': str(job.id),
        'total_records': total_records,
        'successful_records': successful_records,
        'failed_records': failed_records,
        'errors': errors[:100],
        'success_rate': (successful_records / total_records * 100) if total_records > 0 else 0
    }


async def _process_data_chunk(
    session: AsyncSession,
    job: ImportJob,
    chunk_data: List[Dict[str, Any]],
    job_type: ImportJobType,
    tenant_id: str,
) -> Dict[str, Any]:
    """Process a chunk of data records."""
    from dotmac.platform.customer_management.mappers import CustomerMapper
    from dotmac.platform.billing.mappers import BillingMapper

    successful = 0
    failed = 0
    errors = []

    # Create service based on job type
    if job_type == ImportJobType.CUSTOMERS:
        service = CustomerService(session)
        mapper = CustomerMapper
    else:
        # Add other job types as needed
        raise ValueError(f"Unsupported job type: {job_type}")

    for item in chunk_data:
        row_number = item['row_number']
        row_data = item['data']

        try:
            # Validate and transform data
            if job_type == ImportJobType.CUSTOMERS:
                validated_data = mapper.validate_import_row(row_data, row_number)
                if isinstance(validated_data, dict) and 'error' in validated_data:
                    # Validation error
                    failed += 1
                    errors.append(validated_data)
                    await _record_failure(
                        session, job, row_number,
                        "validation", validated_data['error'], row_data, tenant_id
                    )
                else:
                    # Create entity
                    model_data = mapper.from_import_to_model(
                        validated_data, tenant_id, generate_customer_number=True
                    )
                    await service.create_customer(**model_data)
                    successful += 1

        except Exception as e:
            failed += 1
            error_msg = str(e)
            errors.append({
                'row_number': row_number,
                'error': error_msg,
                'data': row_data
            })
            await _record_failure(
                session, job, row_number,
                "creation", error_msg, row_data, tenant_id
            )

    return {
        'successful': successful,
        'failed': failed,
        'errors': errors
    }


async def _record_failure(
    session: AsyncSession,
    job: ImportJob,
    row_number: int,
    error_type: str,
    error_message: str,
    row_data: Dict[str, Any],
    tenant_id: str,
) -> None:
    """Record an import failure."""
    from dotmac.platform.data_import.models import ImportFailure

    failure = ImportFailure(
        job_id=job.id,
        row_number=row_number,
        error_type=error_type,
        error_message=error_message,
        row_data=row_data,
        tenant_id=tenant_id
    )
    session.add(failure)
    await session.commit()


async def _process_invoice_import(
    job_id: str,
    file_path: str,
    tenant_id: str,
    user_id: Optional[str],
    config: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Process invoice import job."""
    # Similar structure to customer import
    # Implementation will follow the same pattern
    pass


async def _process_subscription_import(
    job_id: str,
    file_path: str,
    tenant_id: str,
    user_id: Optional[str],
    config: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Process subscription import job."""
    # Similar structure to customer import
    pass


async def _process_payment_import(
    job_id: str,
    file_path: str,
    tenant_id: str,
    user_id: Optional[str],
    config: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Process payment import job."""
    # Similar structure to customer import
    pass


async def _process_chunk_data(
    job_id: str,
    chunk_data: List[Dict[str, Any]],
    job_type: str,
    tenant_id: str,
    config: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Process a chunk of data for any job type."""
    async with get_async_session() as session:
        job = await session.get(ImportJob, UUID(job_id))
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job_type_enum = ImportJobType(job_type)
        result = await _process_data_chunk(
            session, job, chunk_data, job_type_enum, tenant_id
        )

        return result


@app.task
@idempotent_task(ttl=300)
def check_import_health() -> Dict[str, Any]:
    """
    Periodic health check for import system.

    Returns statistics about running and queued import jobs.
    """
    import asyncio

    async def _check_health():
        async with get_async_session() as session:
            from sqlalchemy import select, func

            # Count jobs by status
            result = await session.execute(
                select(
                    ImportJob.status,
                    func.count(ImportJob.id).label('count')
                ).group_by(ImportJob.status)
            )

            status_counts = {row.status.value: row.count for row in result}

            # Count recent failures (last hour)
            one_hour_ago = datetime.now(timezone.utc).replace(
                minute=datetime.now().minute - 60
            )

            result = await session.execute(
                select(func.count(ImportJob.id))
                .where(ImportJob.status == ImportJobStatus.FAILED)
                .where(ImportJob.completed_at >= one_hour_ago)
            )
            recent_failures = result.scalar() or 0

            return {
                'status_counts': status_counts,
                'recent_failures': recent_failures,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    return asyncio.run(_check_health())


# Register periodic tasks
from celery.schedules import crontab

app.conf.beat_schedule = {
    'check-import-health': {
        'task': 'dotmac.platform.data_import.tasks.check_import_health',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
}
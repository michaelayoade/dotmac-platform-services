"""
Data Transfer Base Classes and Protocols

Shared interfaces, base classes, and protocols for import/export operations.
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, UTC
from enum import Enum
from pathlib import Path
from typing import Any, AsyncGenerator, Callable, Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..core import BaseModel as DotMacBaseModel, DotMacError


class DataTransferError(DotMacError):
    """Base exception for data transfer operations."""


class ImportError(DataTransferError):
    """Exception raised during import operations."""


class ExportError(DataTransferError):
    """Exception raised during export operations."""


class DataValidationError(DataTransferError):
    """Exception raised when data validation fails."""


class FormatError(DataTransferError):
    """Exception raised for unsupported formats."""


class StreamingError(DataTransferError):
    """Exception raised during streaming operations."""


class ProgressError(DataTransferError):
    """Exception raised during progress tracking."""


class DataFormat(str, Enum):
    """Supported data formats."""

    CSV = "csv"
    JSON = "json"
    JSONL = "jsonl"
    EXCEL = "excel"
    XML = "xml"
    PARQUET = "parquet"
    YAML = "yaml"


class TransferStatus(str, Enum):
    """Transfer operation status."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CompressionType(str, Enum):
    """Supported compression types."""

    NONE = "none"
    GZIP = "gzip"
    ZIP = "zip"
    BZIP2 = "bzip2"


class ProgressInfo(DotMacBaseModel):
    """Progress tracking information."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    operation_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique operation identifier")
    total_records: int | None = Field(None, description="Total number of records")
    processed_records: int = Field(0, description="Number of processed records")
    failed_records: int = Field(0, description="Number of failed records")
    current_batch: int = Field(0, description="Current batch number")
    total_batches: int | None = Field(None, description="Total number of batches")
    bytes_processed: int = Field(0, description="Bytes processed")
    bytes_total: int | None = Field(None, description="Total bytes to process")
    start_time: datetime = Field(default_factory=datetime.utcnow)
    last_update: datetime = Field(default_factory=datetime.utcnow)
    estimated_completion: datetime | None = Field(None, description="Estimated completion time")
    status: TransferStatus = Field(TransferStatus.PENDING)
    error_message: str | None = Field(None, description="Error message if failed")

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_records and self.total_records > 0:
            return min(100.0, (self.processed_records / self.total_records) * 100.0)
        if self.bytes_total and self.bytes_total > 0:
            return min(100.0, (self.bytes_processed / self.bytes_total) * 100.0)
        return 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        total = self.processed_records + self.failed_records
        if total == 0:
            return 100.0
        return (self.processed_records / total) * 100.0


class DataRecord(DotMacBaseModel):
    """Individual data record with metadata."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="allow",  # Allow additional fields for flexible data
    )

    record_id: str = Field(default_factory=lambda: str(uuid4()))
    row_number: int | None = Field(None, description="Original row number")
    data: dict[str, Any] = Field(description="Record data")
    metadata: dict[str, Any] = Field(default_factory=dict)
    validation_errors: list[str] = Field(default_factory=list)
    is_valid: bool = Field(True)

    @field_validator("data")
    @classmethod
    def validate_data_not_empty(cls, v: dict[str, Any]) -> dict[str, Any]:
        if not v:
            raise ValueError("Record data cannot be empty")
        return v


class DataBatch(DotMacBaseModel):
    """Batch of data records."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    batch_id: str = Field(default_factory=lambda: str(uuid4()))
    batch_number: int = Field(description="Batch sequence number")
    records: list[DataRecord] = Field(description="Records in this batch")
    total_size: int = Field(description="Total size in bytes")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def valid_records(self) -> list[DataRecord]:
        """Get only valid records."""
        return [record for record in self.records if record.is_valid]

    @property
    def invalid_records(self) -> list[DataRecord]:
        """Get only invalid records."""
        return [record for record in self.records if not record.is_valid]


class TransferConfig(DotMacBaseModel):
    """Configuration for data transfer operations."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    batch_size: int = Field(default=1000, ge=1, le=50000, description="Records per batch")
    max_workers: int = Field(default=4, ge=1, le=32, description="Maximum concurrent workers")
    chunk_size: int = Field(default=8192, ge=1024, description="Chunk size for streaming")
    max_file_size: int = Field(default=100 * 1024 * 1024, ge=1024, description="Max file size in bytes")
    compression: CompressionType = Field(default=CompressionType.NONE)
    encoding: str = Field(default="utf-8", description="Text encoding")
    validate_data: bool = Field(default=True, description="Enable data validation")
    skip_invalid: bool = Field(default=False, description="Skip invalid records")
    resume_on_failure: bool = Field(default=True, description="Enable resumable operations")
    progress_callback_interval: int = Field(default=100, ge=1, description="Progress callback frequency")


# Protocols for type hinting


class ProgressCallback(Protocol):
    """Protocol for progress callback functions."""

    def __call__(self, progress: ProgressInfo) -> None:
        """Called when progress is updated."""
        ...


class DataValidator(Protocol):
    """Protocol for data validation functions."""

    def __call__(self, record: DataRecord) -> bool:
        """Validate a data record and return True if valid."""
        ...


class DataTransformer(Protocol):
    """Protocol for data transformation functions."""

    def __call__(self, record: DataRecord) -> DataRecord:
        """Transform a data record and return the transformed record."""
        ...


# Abstract base classes


class BaseDataProcessor(ABC):
    """Abstract base class for data processors."""

    def __init__(
        self,
        config: TransferConfig | None = None,
        progress_callback: ProgressCallback | None = None,
        validator: DataValidator | None = None,
        transformer: DataTransformer | None = None,
    ):
        self.config = config or TransferConfig()
        self.progress_callback = progress_callback
        self.validator = validator
        self.transformer = transformer
        self._operation_id = str(uuid4())
        self._progress = ProgressInfo(operation_id=self._operation_id)
        self._cancelled = False

    @property
    def operation_id(self) -> str:
        """Get the operation ID."""
        return self._operation_id

    @property
    def progress(self) -> ProgressInfo:
        """Get current progress information."""
        return self._progress

    def cancel(self) -> None:
        """Cancel the operation."""
        self._cancelled = True
        self._progress.status = TransferStatus.CANCELLED

    @abstractmethod
    async def process(self, source: Any, **kwargs) -> AsyncGenerator[DataBatch, None]:
        """Process data from source and yield batches."""
        ...

    def _update_progress(self, **kwargs) -> None:
        """Update progress information."""
        for key, value in kwargs.items():
            if hasattr(self._progress, key):
                setattr(self._progress, key, value)

        self._progress.last_update = datetime.now(UTC)

        if (
            self.progress_callback
            and self._progress.processed_records % self.config.progress_callback_interval == 0
        ):
            self.progress_callback(self._progress)

    def _validate_record(self, record: DataRecord) -> bool:
        """Validate a data record."""
        if not self.config.validate_data:
            return True

        if self.validator:
            try:
                return self.validator(record)
            except Exception as e:
                record.validation_errors.append(str(e))
                record.is_valid = False
                return False

        return record.is_valid

    def _transform_record(self, record: DataRecord) -> DataRecord:
        """Transform a data record."""
        if self.transformer:
            try:
                return self.transformer(record)
            except Exception as e:
                record.validation_errors.append(f"Transformation error: {e}")
                record.is_valid = False

        return record


class BaseImporter(BaseDataProcessor):
    """Abstract base class for data importers."""

    @abstractmethod
    async def import_from_file(self, file_path: Path, **kwargs) -> AsyncGenerator[DataBatch, None]:
        """Import data from a file."""
        ...

    @abstractmethod
    async def import_from_stream(self, stream: Any, **kwargs) -> AsyncGenerator[DataBatch, None]:
        """Import data from a stream."""
        ...


class BaseExporter(BaseDataProcessor):
    """Abstract base class for data exporters."""

    @abstractmethod
    async def export_to_file(
        self, data: AsyncGenerator[DataBatch, None], file_path: Path, **kwargs
    ) -> ProgressInfo:
        """Export data to a file."""
        ...

    @abstractmethod
    async def export_to_stream(
        self, data: AsyncGenerator[DataBatch, None], stream: Any, **kwargs
    ) -> ProgressInfo:
        """Export data to a stream."""
        ...

    async def export_batch_to_file(
        self, batch: DataBatch, file_path: Path, **kwargs
    ) -> ProgressInfo:
        """Export a single batch to a file."""
        async def single_batch_generator():
            yield batch

        return await self.export_to_file(single_batch_generator(), file_path, **kwargs)

    async def export_batch_to_stream(
        self, batch: DataBatch, stream: Any, **kwargs
    ) -> ProgressInfo:
        """Export a single batch to a stream."""
        async def single_batch_generator():
            yield batch

        return await self.export_to_stream(single_batch_generator(), stream, **kwargs)


# Utility functions


def create_operation_id() -> str:
    """Create a unique operation ID."""
    return str(uuid4())


def estimate_completion_time(progress: ProgressInfo) -> datetime | None:
    """Estimate completion time based on current progress."""
    if progress.total_records is None or progress.processed_records == 0:
        return None

    elapsed = (progress.last_update - progress.start_time).total_seconds()
    if elapsed <= 0:
        return None

    rate = progress.processed_records / elapsed
    remaining = progress.total_records - progress.processed_records

    if rate <= 0:
        return None

    estimated_seconds = remaining / rate
    return progress.last_update + timedelta(seconds=estimated_seconds)


def calculate_throughput(progress: ProgressInfo) -> float:
    """Calculate records per second throughput."""
    elapsed = (progress.last_update - progress.start_time).total_seconds()
    if elapsed <= 0:
        return 0.0

    return progress.processed_records / elapsed


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


async def create_batches(
    records: AsyncGenerator[DataRecord, None],
    batch_size: int,
    max_batch_size_bytes: int | None = None,
) -> AsyncGenerator[DataBatch, None]:
    """Create batches from a stream of records."""
    batch_records = []
    batch_size_bytes = 0
    batch_number = 0

    async for record in records:
        batch_records.append(record)

        # Estimate record size (rough calculation)
        record_size = len(str(record.data).encode("utf-8"))
        batch_size_bytes += record_size

        # Check if batch is ready
        should_yield = len(batch_records) >= batch_size or (
            max_batch_size_bytes and batch_size_bytes >= max_batch_size_bytes
        )

        if should_yield:
            batch_number += 1
            yield DataBatch(
                batch_number=batch_number, records=batch_records, total_size=batch_size_bytes
            )
            batch_records = []
            batch_size_bytes = 0

    # Yield remaining records
    if batch_records:
        batch_number += 1
        yield DataBatch(
            batch_number=batch_number, records=batch_records, total_size=batch_size_bytes
        )

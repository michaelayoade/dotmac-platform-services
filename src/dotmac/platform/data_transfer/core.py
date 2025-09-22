"""
Core classes and types for simplified data transfer using pandas.
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, UTC
from enum import Enum
from pathlib import Path
from typing import Any, AsyncGenerator, Callable, Protocol, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DataTransferError(Exception):
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


class ProgressInfo(BaseModel):
    """Progress tracking information."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    operation_id: str = Field(default_factory=lambda: str(uuid4()))
    total_records: Optional[int] = None
    processed_records: int = 0
    failed_records: int = 0
    current_batch: int = 0
    total_batches: Optional[int] = None
    bytes_processed: int = 0
    bytes_total: Optional[int] = None
    start_time: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_update: datetime = Field(default_factory=lambda: datetime.now(UTC))
    estimated_completion: Optional[datetime] = None
    status: TransferStatus = TransferStatus.PENDING
    error_message: Optional[str] = None

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_records and self.total_records > 0:
            return (self.processed_records / self.total_records) * 100
        return 0.0

    @property
    def elapsed_time(self) -> timedelta:
        """Calculate elapsed time."""
        return self.last_update - self.start_time

    @property
    def is_complete(self) -> bool:
        """Check if operation is complete."""
        return self.status == TransferStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if operation failed."""
        return self.status == TransferStatus.FAILED


class DataRecord(BaseModel):
    """Single data record."""
    data: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)


class DataBatch(BaseModel):
    """Batch of data records."""
    records: list[DataRecord]
    batch_number: int
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def size(self) -> int:
        """Get batch size."""
        return len(self.records)


class TransferConfig(BaseModel):
    """Configuration for transfer operations."""
    batch_size: int = 1000
    max_workers: int = 4
    chunk_size: int = 8192
    compression: CompressionType = CompressionType.NONE
    encoding: str = "utf-8"
    validate_data: bool = True
    skip_invalid: bool = False
    resume_on_failure: bool = True
    timeout: Optional[int] = None
    retry_attempts: int = 3
    retry_delay: float = 1.0


class ImportOptions(BaseModel):
    """Import-specific options."""
    delimiter: str = ","
    header_row: Optional[int] = 0
    skip_rows: int = 0
    type_inference: bool = True
    sheet_name: Optional[Union[str, int]] = None
    json_lines: bool = False
    xml_record_element: Optional[str] = None
    encoding: str = "utf-8"
    na_values: list[str] = Field(default_factory=list)
    parse_dates: bool = False


class ExportOptions(BaseModel):
    """Export-specific options."""
    delimiter: str = ","
    include_headers: bool = True
    json_indent: Optional[int] = 2
    json_ensure_ascii: bool = False
    json_sort_keys: bool = False
    json_lines: bool = False
    sheet_name: str = "Data"
    xml_root_element: str = "root"
    xml_record_element: str = "record"
    xml_pretty_print: bool = True
    auto_filter: bool = True
    freeze_panes: Optional[str] = "A2"
    encoding: str = "utf-8"
    quoting: int = 1  # csv.QUOTE_MINIMAL


# Protocols for customization
class DataTransformer(Protocol):
    """Protocol for data transformation functions."""

    def __call__(self, record: DataRecord) -> DataRecord:
        """Transform a data record."""
        ...


class DataValidator(Protocol):
    """Protocol for data validation functions."""

    def __call__(self, record: DataRecord) -> bool:
        """Validate a data record."""
        ...


class ProgressCallback(Protocol):
    """Protocol for progress callbacks."""

    def __call__(self, progress: ProgressInfo) -> None:
        """Handle progress update."""
        ...


class BaseDataProcessor(ABC):
    """Base class for data processors."""

    def __init__(
        self,
        config: TransferConfig,
        progress_callback: Optional[ProgressCallback] = None,
    ):
        self.config = config
        self.progress_callback = progress_callback
        self._progress = ProgressInfo()

    def update_progress(
        self,
        processed: int = 0,
        failed: int = 0,
        batch: Optional[int] = None,
    ) -> None:
        """Update progress information."""
        self._progress.processed_records += processed
        self._progress.failed_records += failed
        if batch is not None:
            self._progress.current_batch = batch
        self._progress.last_update = datetime.now(UTC)

        if self.progress_callback:
            self.progress_callback(self._progress)

    @abstractmethod
    async def process(self, *args, **kwargs) -> Any:
        """Process data (to be implemented by subclasses)."""
        pass


class BaseImporter(BaseDataProcessor):
    """Base class for data importers."""

    def __init__(
        self,
        config: TransferConfig,
        options: ImportOptions,
        progress_callback: Optional[ProgressCallback] = None,
    ):
        super().__init__(config, progress_callback)
        self.options = options

    @abstractmethod
    async def import_from_file(
        self, file_path: Path
    ) -> AsyncGenerator[DataBatch, None]:
        """Import data from file."""
        pass

    async def process(self, file_path: Path) -> AsyncGenerator[DataBatch, None]:
        """Process import operation."""
        async for batch in self.import_from_file(file_path):
            yield batch


class BaseExporter(BaseDataProcessor):
    """Base class for data exporters."""

    def __init__(
        self,
        config: TransferConfig,
        options: ExportOptions,
        progress_callback: Optional[ProgressCallback] = None,
    ):
        super().__init__(config, progress_callback)
        self.options = options

    @abstractmethod
    async def export_to_file(
        self,
        data: AsyncGenerator[DataBatch, None],
        file_path: Path,
    ) -> ProgressInfo:
        """Export data to file."""
        pass

    async def process(
        self,
        data: AsyncGenerator[DataBatch, None],
        file_path: Path,
    ) -> ProgressInfo:
        """Process export operation."""
        return await self.export_to_file(data, file_path)
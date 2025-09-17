"""
DotMac Data Transfer Module

Comprehensive data import/export capabilities with streaming support, progress tracking,
and resumable operations.

This module provides:
- Import support for CSV, JSON, Excel, XML, and other formats
- Export support for multiple output formats with compression
- Streaming for large files
- Progress tracking and resumable operations
- Data validation with Pydantic
- Error recovery and robust error handling

Example Usage:
    >>> from dotmac.platform.data_transfer import import_file, export_data
    >>> from dotmac.platform.data_transfer import DataFormat, TransferConfig
    >>>
    >>> # Import data
    >>> config = TransferConfig(batch_size=500)
    >>> async for batch in import_file("data.csv", DataFormat.CSV, config):
    >>>     process_batch(batch)
    >>>
    >>> # Export data
    >>> await export_data(data_generator, "output.json", DataFormat.JSON)
"""

from .base import (
    # Core classes and models
    BaseDataProcessor,
    BaseExporter,
    BaseImporter,
    CompressionType,
    DataBatch,
    DataFormat,
    DataRecord,
    ProgressInfo,
    TransferConfig,
    TransferStatus,
    # Protocols
    DataTransformer,
    DataValidator,
    ProgressCallback,
    # Exceptions
    DataTransferError,
    ExportError,
    FormatError,
    ImportError,
    ProgressError,
    StreamingError,
    DataValidationError,
    # Utility functions
    calculate_throughput,
    create_batches,
    create_operation_id,
    estimate_completion_time,
    format_file_size,
)

from .progress import (
    # Progress tracking classes
    CheckpointData,
    CheckpointStore,
    FileProgressStore,
    ProgressStore,
    ProgressTracker,
    ResumableOperation,
    # Utility functions
    cleanup_old_operations,
    create_progress_tracker,
)

from .importers import (
    # Importer classes
    CSVImporter,
    ExcelImporter,
    JSONImporter,
    XMLImporter,
    # Configuration
    ImportOptions,
    # Factory functions
    create_importer,
    detect_format,
    import_file,
)

from .exporters import (
    # Exporter classes
    CSVExporter,
    ExcelExporter,
    JSONExporter,
    XMLExporter,
    YAMLExporter,
    # Configuration
    ExportOptions,
    # Utility functions
    compress_file,
    create_exporter,
    export_data,
)

# Version info
__version__ = "1.0.0"
__author__ = "DotMac Team"


# Factory Functions


def create_transfer_config(
    batch_size: int = 1000,
    max_workers: int = 4,
    chunk_size: int = 8192,
    compression: CompressionType = CompressionType.NONE,
    encoding: str = "utf-8",
    validate_data: bool = True,
    skip_invalid: bool = False,
    resume_on_failure: bool = True,
    **kwargs,
) -> TransferConfig:
    """Create a transfer configuration with sensible defaults.

    Args:
        batch_size: Number of records per batch (default: 1000)
        max_workers: Maximum concurrent workers (default: 4)
        chunk_size: Chunk size for streaming operations (default: 8192)
        compression: Compression type (default: NONE)
        encoding: Text encoding (default: utf-8)
        validate_data: Enable data validation (default: True)
        skip_invalid: Skip invalid records (default: False)
        resume_on_failure: Enable resumable operations (default: True)
        **kwargs: Additional configuration options

    Returns:
        Configured TransferConfig instance
    """
    return TransferConfig(
        batch_size=batch_size,
        max_workers=max_workers,
        chunk_size=chunk_size,
        compression=compression,
        encoding=encoding,
        validate_data=validate_data,
        skip_invalid=skip_invalid,
        resume_on_failure=resume_on_failure,
        **kwargs,
    )


def create_import_options(data_format: DataFormat, **kwargs) -> ImportOptions:
    """Create import options optimized for specific format.

    Args:
        data_format: Target data format
        **kwargs: Format-specific options

    Returns:
        Configured ImportOptions instance
    """
    # Format-specific defaults
    format_defaults = {
        DataFormat.CSV: {
            "delimiter": ",",
            "header_row": 0,
            "type_inference": True,
        },
        DataFormat.JSON: {
            "type_inference": True,
        },
        DataFormat.JSONL: {
            "json_lines": True,
            "type_inference": True,
        },
        DataFormat.EXCEL: {
            "sheet_name": None,  # Use active sheet
            "skip_rows": 0,
            "type_inference": True,
        },
        DataFormat.XML: {
            "xml_record_element": None,  # Auto-detect
        },
    }

    # Merge format defaults with user options
    options = format_defaults.get(data_format, {})
    options.update(kwargs)

    return ImportOptions(**options)


def create_export_options(data_format: DataFormat, **kwargs) -> ExportOptions:
    """Create export options optimized for specific format.

    Args:
        data_format: Target data format
        **kwargs: Format-specific options

    Returns:
        Configured ExportOptions instance
    """
    # Format-specific defaults
    format_defaults = {
        DataFormat.CSV: {
            "delimiter": ",",
            "include_headers": True,
            "quoting": 1,  # QUOTE_MINIMAL
        },
        DataFormat.JSON: {
            "json_indent": 2,
            "json_ensure_ascii": False,
            "json_sort_keys": False,
        },
        DataFormat.JSONL: {
            "json_lines": True,
            "json_ensure_ascii": False,
        },
        DataFormat.EXCEL: {
            "sheet_name": "Data",
            "auto_filter": True,
            "freeze_panes": "A2",
        },
        DataFormat.XML: {
            "xml_root_element": "root",
            "xml_record_element": "record",
            "xml_pretty_print": True,
        },
        DataFormat.YAML: {
            "json_sort_keys": False,
        },
    }

    # Merge format defaults with user options
    options = format_defaults.get(data_format, {})
    options.update(kwargs)

    return ExportOptions(**options)


def create_data_pipeline(
    source_path: str,
    target_path: str,
    source_format: DataFormat | None = None,
    target_format: DataFormat | None = None,
    config: TransferConfig | None = None,
    import_options: ImportOptions | None = None,
    export_options: ExportOptions | None = None,
    progress_callback: ProgressCallback | None = None,
    validator: DataValidator | None = None,
    transformer: DataTransformer | None = None,
):
    """Create a data processing pipeline.

    Args:
        source_path: Path to source file
        target_path: Path to target file
        source_format: Source data format (auto-detected if None)
        target_format: Target data format (inferred from extension if None)
        config: Transfer configuration
        import_options: Import-specific options
        export_options: Export-specific options
        progress_callback: Progress tracking callback
        validator: Data validation function
        transformer: Data transformation function

    Returns:
        DataPipeline instance
    """
    from pathlib import Path

    source = Path(source_path)
    target = Path(target_path)

    # Auto-detect source format
    if source_format is None:
        source_format = detect_format(source)

    # Infer target format from extension
    if target_format is None:
        extension_map = {
            ".csv": DataFormat.CSV,
            ".json": DataFormat.JSON,
            ".jsonl": DataFormat.JSONL,
            ".xlsx": DataFormat.EXCEL,
            ".xls": DataFormat.EXCEL,
            ".xml": DataFormat.XML,
            ".yaml": DataFormat.YAML,
            ".yml": DataFormat.YAML,
        }
        target_format = extension_map.get(target.suffix.lower(), DataFormat.JSON)

    return DataPipeline(
        source_path=source,
        target_path=target,
        source_format=source_format,
        target_format=target_format,
        config=config or create_transfer_config(),
        import_options=import_options or create_import_options(source_format),
        export_options=export_options or create_export_options(target_format),
        progress_callback=progress_callback,
        validator=validator,
        transformer=transformer,
    )


class DataPipeline:
    """Data processing pipeline for import/transform/export operations."""

    def __init__(
        self,
        source_path: "Path",
        target_path: "Path",
        source_format: DataFormat,
        target_format: DataFormat,
        config: TransferConfig,
        import_options: ImportOptions,
        export_options: ExportOptions,
        progress_callback: ProgressCallback | None = None,
        validator: DataValidator | None = None,
        transformer: DataTransformer | None = None,
    ):
        self.source_path = source_path
        self.target_path = target_path
        self.source_format = source_format
        self.target_format = target_format
        self.config = config
        self.import_options = import_options
        self.export_options = export_options
        self.progress_callback = progress_callback
        self.validator = validator
        self.transformer = transformer

        # Create operation tracker
        self.operation_id = create_operation_id()
        self.progress_tracker = create_progress_tracker(self.operation_id)

        if progress_callback:
            self.progress_tracker.add_callback(progress_callback)

    async def execute(self) -> ProgressInfo:
        """Execute the data pipeline.

        Returns:
            Progress information for the completed operation
        """
        try:
            # Initialize progress tracking
            await self.progress_tracker.initialize()

            # Create importer and exporter
            importer = create_importer(
                self.source_format, self.config, self.import_options, self._on_import_progress
            )

            exporter = create_exporter(
                self.target_format, self.config, self.export_options, self._on_export_progress
            )

            # Import data with optional transformation
            async def process_data():
                async for batch in importer.import_from_file(self.source_path):
                    # Apply validation and transformation if provided
                    if self.validator or self.transformer:
                        processed_records = []
                        for record in batch.records:
                            if self.validator and not self.validator(record):
                                if not self.config.skip_invalid:
                                    processed_records.append(record)
                                continue

                            if self.transformer:
                                record = self.transformer(record)

                            processed_records.append(record)

                        batch.records = processed_records

                    yield batch

            # Export processed data
            result = await exporter.export_to_file(process_data(), self.target_path)

            await self.progress_tracker.complete()
            return result

        except Exception as e:
            await self.progress_tracker.fail(str(e))
            raise

    async def execute_with_resume(self) -> ProgressInfo:
        """Execute the pipeline with resume capability.

        Returns:
            Progress information for the completed operation
        """
        # Try to restore from checkpoint
        restored = await self.progress_tracker.restore_from_latest_checkpoint()

        if restored:
            # Resume from last checkpoint
            return await self._resume_execution()
        else:
            # Start fresh execution
            return await self.execute()

    async def pause(self) -> None:
        """Pause the pipeline execution."""
        await self.progress_tracker.pause()

    async def cancel(self) -> None:
        """Cancel the pipeline execution."""
        await self.progress_tracker.cancel()

    def _on_import_progress(self, progress: ProgressInfo) -> None:
        """Handle import progress updates."""
        # Merge import progress with pipeline progress
        self.progress_tracker._progress.processed_records = progress.processed_records
        self.progress_tracker._progress.current_batch = progress.current_batch

    def _on_export_progress(self, progress: ProgressInfo) -> None:
        """Handle export progress updates."""
        # Export progress represents final progress
        self.progress_tracker._progress = progress

    async def _resume_execution(self) -> ProgressInfo:
        """Resume execution from last checkpoint."""
        # This is a simplified implementation
        # In practice, you'd restore the exact state and continue from checkpoint
        return await self.execute()


# Convenience functions for common operations


async def convert_file(
    source_path: str,
    target_path: str,
    source_format: DataFormat | None = None,
    target_format: DataFormat | None = None,
    batch_size: int = 1000,
    progress_callback: ProgressCallback | None = None,
) -> ProgressInfo:
    """Convert a file from one format to another.

    Args:
        source_path: Path to source file
        target_path: Path to target file
        source_format: Source format (auto-detected if None)
        target_format: Target format (inferred from extension if None)
        batch_size: Number of records per batch
        progress_callback: Progress tracking callback

    Returns:
        Progress information for the completed operation
    """
    config = create_transfer_config(batch_size=batch_size)
    pipeline = create_data_pipeline(
        source_path=source_path,
        target_path=target_path,
        source_format=source_format,
        target_format=target_format,
        config=config,
        progress_callback=progress_callback,
    )

    return await pipeline.execute()


async def validate_and_clean_file(
    source_path: str,
    target_path: str,
    validator: DataValidator,
    transformer: DataTransformer | None = None,
    skip_invalid: bool = True,
    progress_callback: ProgressCallback | None = None,
) -> ProgressInfo:
    """Validate and clean a data file.

    Args:
        source_path: Path to source file
        target_path: Path to cleaned target file
        validator: Data validation function
        transformer: Optional data transformation function
        skip_invalid: Whether to skip invalid records
        progress_callback: Progress tracking callback

    Returns:
        Progress information for the completed operation
    """
    config = create_transfer_config(validate_data=True, skip_invalid=skip_invalid)

    pipeline = create_data_pipeline(
        source_path=source_path,
        target_path=target_path,
        config=config,
        progress_callback=progress_callback,
        validator=validator,
        transformer=transformer,
    )

    return await pipeline.execute()


# Export all public symbols
__all__ = [
    # Core classes and enums
    "BaseDataProcessor",
    "BaseExporter",
    "BaseImporter",
    "CompressionType",
    "DataBatch",
    "DataFormat",
    "DataRecord",
    "ProgressInfo",
    "TransferConfig",
    "TransferStatus",
    # Protocols
    "DataTransformer",
    "DataValidator",
    "ProgressCallback",
    # Exceptions
    "DataTransferError",
    "ExportError",
    "FormatError",
    "ImportError",
    "ProgressError",
    "StreamingError",
    "DataValidationError",
    # Progress tracking
    "CheckpointData",
    "CheckpointStore",
    "FileProgressStore",
    "ProgressStore",
    "ProgressTracker",
    "ResumableOperation",
    # Importers
    "CSVImporter",
    "ExcelImporter",
    "JSONImporter",
    "XMLImporter",
    "ImportOptions",
    # Exporters
    "CSVExporter",
    "ExcelExporter",
    "JSONExporter",
    "XMLExporter",
    "YAMLExporter",
    "ExportOptions",
    # Factory functions
    "create_exporter",
    "create_importer",
    "create_transfer_config",
    "create_import_options",
    "create_export_options",
    "create_data_pipeline",
    "create_progress_tracker",
    # High-level operations
    "DataPipeline",
    "convert_file",
    "export_data",
    "import_file",
    "validate_and_clean_file",
    # Utility functions
    "calculate_throughput",
    "cleanup_old_operations",
    "compress_file",
    "create_batches",
    "create_operation_id",
    "detect_format",
    "estimate_completion_time",
    "format_file_size",
]

"""
Simplified Data Transfer Module using pandas and standard libraries.

This module replaces the custom data transfer implementation with
pandas-based functionality and Python standard libraries.
"""

from .core import (
    # Core classes and enums
    DataFormat,
    TransferStatus,
    CompressionType,
    ProgressInfo,
    DataRecord,
    DataBatch,
    TransferConfig,
    # Exceptions
    DataTransferError,
    ImportError,
    ExportError,
    DataValidationError,
    FormatError,
    StreamingError,
    ProgressError,
    # Base classes
    BaseDataProcessor,
    BaseImporter,
    BaseExporter,
    # Protocols
    DataTransformer,
    DataValidator,
    ProgressCallback,
)

from .importers import (
    CSVImporter,
    JSONImporter,
    ExcelImporter,
    XMLImporter,
    YAMLImporter,
    ImportOptions,
    import_file,
    detect_format,
    create_importer,
)

from .exporters import (
    CSVExporter,
    JSONExporter,
    ExcelExporter,
    XMLExporter,
    YAMLExporter,
    ExportOptions,
    export_data,
    create_exporter,
    compress_file,
)

from .progress import (
    ProgressTracker,
    CheckpointData,
    CheckpointStore,
    FileProgressStore,
    ProgressStore,
    ResumableOperation,
    create_progress_tracker,
    cleanup_old_operations,
)

from .utils import (
    calculate_throughput,
    create_batches,
    create_operation_id,
    estimate_completion_time,
    format_file_size,
    convert_file,
    validate_and_clean_file,
    create_transfer_config,
    create_import_options,
    create_export_options,
    create_data_pipeline,
    DataPipeline,
)

# Version info
__version__ = "2.0.0"
__author__ = "DotMac Team"

__all__ = [
    # Core classes and enums
    "DataFormat",
    "TransferStatus",
    "CompressionType",
    "ProgressInfo",
    "DataRecord",
    "DataBatch",
    "TransferConfig",
    # Exceptions
    "DataTransferError",
    "ImportError",
    "ExportError",
    "DataValidationError",
    "FormatError",
    "StreamingError",
    "ProgressError",
    # Base classes
    "BaseDataProcessor",
    "BaseImporter",
    "BaseExporter",
    # Protocols
    "DataTransformer",
    "DataValidator",
    "ProgressCallback",
    # Importers
    "CSVImporter",
    "JSONImporter",
    "ExcelImporter",
    "XMLImporter",
    "YAMLImporter",
    "ImportOptions",
    "import_file",
    "detect_format",
    "create_importer",
    # Exporters
    "CSVExporter",
    "JSONExporter",
    "ExcelExporter",
    "XMLExporter",
    "YAMLExporter",
    "ExportOptions",
    "export_data",
    "create_exporter",
    "compress_file",
    # Progress tracking
    "ProgressTracker",
    "CheckpointData",
    "CheckpointStore",
    "FileProgressStore",
    "ProgressStore",
    "ResumableOperation",
    "create_progress_tracker",
    "cleanup_old_operations",
    # Utilities
    "calculate_throughput",
    "create_batches",
    "create_operation_id",
    "estimate_completion_time",
    "format_file_size",
    "convert_file",
    "validate_and_clean_file",
    "create_transfer_config",
    "create_import_options",
    "create_export_options",
    "create_data_pipeline",
    "DataPipeline",
]
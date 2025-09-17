"""
DotMac File Processing Pipeline

Comprehensive file processing capabilities including:
- Image processing (resize, optimize, thumbnails)
- Document parsing (PDF, Word, Excel)
- Video processing (thumbnails, metadata)
- Audio processing (waveforms, metadata)
- Text extraction and OCR
- Virus scanning
- Metadata extraction
- Format conversion
"""

from typing import Optional

# Core processors
from .base import (
    FileProcessor,
    ProcessingResult,
    ProcessingOptions,
    ProcessingError,
    FileMetadata,
)

from .processors import (
    ImageProcessor,
    DocumentProcessor,
    VideoProcessor,
    AudioProcessor,
)

# Pipeline components
from .pipeline import (
    ProcessingPipeline,
    PipelineStep,
    PipelineConfig,
    PipelineResult,
    create_simple_pipeline,
    create_conditional_pipeline,
)

# Utils
from .utils import (
    get_file_type,
    validate_file_size,
    sanitize_filename,
    generate_thumbnail_name,
    get_safe_filename,
    format_file_size,
    validate_file_extension,
)

# Virus scanning (optional - to be implemented)
try:
    from .security import VirusScanner, ScanResult

    VIRUS_SCANNER_AVAILABLE = True
except ImportError:
    VirusScanner = None
    ScanResult = None
    VIRUS_SCANNER_AVAILABLE = False

# OCR support (optional)
try:
    from .ocr import OCRProcessor, OCRResult

    OCR_AVAILABLE = True
except ImportError:
    OCRProcessor = None
    OCRResult = None
    OCR_AVAILABLE = False

__version__ = "1.0.0"
__all__ = [
    # Base
    "FileProcessor",
    "ProcessingResult",
    "ProcessingOptions",
    "ProcessingError",
    "FileMetadata",
    # Processors
    "ImageProcessor",
    "DocumentProcessor",
    "VideoProcessor",
    "AudioProcessor",
    # Pipeline
    "ProcessingPipeline",
    "PipelineStep",
    "PipelineConfig",
    "PipelineResult",
    "create_simple_pipeline",
    "create_conditional_pipeline",
    # Utils
    "get_file_type",
    "validate_file_size",
    "sanitize_filename",
    "generate_thumbnail_name",
    "get_safe_filename",
    "format_file_size",
    "validate_file_extension",
]

if VIRUS_SCANNER_AVAILABLE:
    __all__.extend(["VirusScanner", "ScanResult"])

if OCR_AVAILABLE:
    __all__.extend(["OCRProcessor", "OCRResult"])


def create_file_processor(
    file_path: str,
    options: Optional[ProcessingOptions] = None,
) -> FileProcessor:
    """
    Factory function to create appropriate processor based on file type.

    Args:
        file_path: Path to the file
        options: Processing options

    Returns:
        Appropriate FileProcessor instance
    """
    import mimetypes

    file_type, _ = mimetypes.guess_type(file_path)
    file_type = file_type or "application/octet-stream"

    if file_type.startswith("image/"):
        return ImageProcessor(options)
    elif file_type in [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument",
    ]:
        return DocumentProcessor(options)
    elif file_type.startswith("video/"):
        return VideoProcessor(options)
    elif file_type.startswith("audio/"):
        return AudioProcessor(options)
    else:
        # Return a base processor for unknown types
        # Note: FileProcessor is a Protocol, not a concrete class
        # For now, return ImageProcessor as a fallback
        return ImageProcessor(options)

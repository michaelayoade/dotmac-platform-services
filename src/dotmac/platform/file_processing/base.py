"""
Base classes for file processing.
"""

import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Protocol


class ProcessingStatus(str, Enum):
    """Processing status enum."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FileType(str, Enum):
    """Supported file types."""

    IMAGE = "image"
    DOCUMENT = "document"
    VIDEO = "video"
    AUDIO = "audio"
    ARCHIVE = "archive"
    TEXT = "text"
    UNKNOWN = "unknown"


@dataclass
class FileMetadata:
    """File metadata information."""

    filename: str
    file_path: str
    file_size: int
    mime_type: str
    file_hash: str
    created_at: datetime
    modified_at: datetime
    file_type: FileType
    extension: str
    dimensions: Optional[tuple[int, int]] = None  # width, height for images/videos
    duration: Optional[float] = None  # for audio/video
    pages: Optional[int] = None  # for documents
    encoding: Optional[str] = None  # for text files
    extra_metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_file(cls, file_path: str) -> "FileMetadata":
        """Create metadata from file path."""
        path = Path(file_path)
        stat = path.stat()

        # Calculate file hash
        with open(file_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        # Determine file type
        import mimetypes

        mime_type, _ = mimetypes.guess_type(file_path)
        mime_type = mime_type or "application/octet-stream"

        file_type = FileType.UNKNOWN
        if mime_type.startswith("image/"):
            file_type = FileType.IMAGE
        elif mime_type.startswith("video/"):
            file_type = FileType.VIDEO
        elif mime_type.startswith("audio/"):
            file_type = FileType.AUDIO
        elif mime_type in [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument",
        ]:
            file_type = FileType.DOCUMENT
        elif mime_type.startswith("text/"):
            file_type = FileType.TEXT
        elif mime_type in ["application/zip", "application/x-tar", "application/x-rar"]:
            file_type = FileType.ARCHIVE

        return cls(
            filename=path.name,
            file_path=str(path.absolute()),
            file_size=stat.st_size,
            mime_type=mime_type,
            file_hash=file_hash,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            file_type=file_type,
            extension=path.suffix.lower(),
        )


@dataclass
class ProcessingOptions:
    """Options for file processing."""

    # General options
    preserve_original: bool = True
    output_directory: Optional[str] = None
    output_format: Optional[str] = None
    quality: int = 85  # 0-100 for lossy formats

    # Image options
    resize_width: Optional[int] = None
    resize_height: Optional[int] = None
    maintain_aspect_ratio: bool = True
    generate_thumbnails: bool = False
    thumbnail_sizes: list[tuple[int, int]] = field(default_factory=lambda: [(150, 150), (300, 300)])
    optimize_size: bool = True
    strip_metadata: bool = False
    watermark_path: Optional[str] = None

    # Document options
    extract_text: bool = True
    extract_images: bool = False
    convert_to_pdf: bool = False
    merge_pages: Optional[list[int]] = None
    split_pages: bool = False

    # Video options
    extract_frames: bool = False
    frame_interval: float = 1.0  # seconds
    generate_preview: bool = False
    preview_duration: float = 10.0  # seconds
    video_codec: Optional[str] = None
    audio_codec: Optional[str] = None

    # Audio options
    generate_waveform: bool = False
    normalize_volume: bool = False
    audio_bitrate: Optional[int] = None

    # Security options
    scan_for_viruses: bool = False
    max_file_size: int = 100 * 1024 * 1024  # 100MB default
    allowed_extensions: Optional[list[str]] = None
    blocked_extensions: list[str] = field(
        default_factory=lambda: [".exe", ".bat", ".cmd", ".com", ".scr"]
    )


@dataclass
class ProcessingResult:
    """Result of file processing."""

    status: ProcessingStatus
    original_file: str
    processed_files: list[str] = field(default_factory=list)
    metadata: Optional[FileMetadata] = None
    extracted_text: Optional[str] = None
    thumbnails: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    processing_time: float = 0.0
    extra_data: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        """Check if processing was successful."""
        return self.status == ProcessingStatus.COMPLETED

    def add_processed_file(self, file_path: str) -> None:
        """Add a processed file to results."""
        self.processed_files.append(file_path)

    def add_thumbnail(self, thumbnail_path: str) -> None:
        """Add a thumbnail to results."""
        self.thumbnails.append(thumbnail_path)

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        self.status = ProcessingStatus.FAILED

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)


class ProcessingError(Exception):
    """Base exception for processing errors."""

    pass


class FileProcessor(Protocol):
    """Protocol for file processors."""

    async def process(
        self,
        file_path: str,
        options: Optional[ProcessingOptions] = None,
    ) -> ProcessingResult:
        """Process a file."""
        ...

    async def validate(self, file_path: str) -> bool:
        """Validate if file can be processed."""
        ...

    async def extract_metadata(self, file_path: str) -> FileMetadata:
        """Extract metadata from file."""
        ...

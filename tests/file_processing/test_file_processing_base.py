"""
Comprehensive tests for file processing base classes and models.
"""

import hashlib
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dotmac.platform.file_processing.base import (
    FileMetadata,
    FileProcessor,
    FileType,
    ProcessingError,
    ProcessingOptions,
    ProcessingResult,
    ProcessingStatus,
)


class TestFileMetadata:
    """Test file metadata functionality."""

    @pytest.fixture
    def sample_file(self):
        """Create a temporary test file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello, World!")
            temp_path = f.name

        yield temp_path

        # Cleanup
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass

    @pytest.mark.unit
    def test_file_metadata_from_file_basic(self, sample_file):
        """Test basic file metadata creation from file."""
        metadata = FileMetadata.from_file(sample_file)

        assert metadata.filename == os.path.basename(sample_file)
        assert metadata.file_path == str(Path(sample_file).absolute())
        assert metadata.file_size > 0
        assert metadata.mime_type == "text/plain"
        assert metadata.file_type == FileType.TEXT
        assert metadata.extension == ".txt"

        # Check timestamps
        assert isinstance(metadata.created_at, datetime)
        assert isinstance(metadata.modified_at, datetime)

        # Check hash
        assert len(metadata.file_hash) == 64  # SHA256 hex length

        # Verify hash is correct
        with open(sample_file, "rb") as f:
            expected_hash = hashlib.sha256(f.read()).hexdigest()
        assert metadata.file_hash == expected_hash

    @pytest.mark.unit
    def test_file_metadata_image_detection(self):
        """Test image file type detection."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            temp_path = f.name

        try:
            with patch("mimetypes.guess_type", return_value=("image/jpeg", None)):
                with patch("builtins.open", create=True) as mock_open:
                    with patch("os.path.getsize", return_value=1024):
                        with patch("os.stat") as mock_stat:
                            stat_result = Mock()
                            stat_result.st_size = 1024
                            stat_result.st_ctime = time.time()
                            stat_result.st_mtime = time.time()
                            mock_stat.return_value = stat_result

                            mock_open.return_value.__enter__.return_value.read.return_value = (
                                b"fake image data"
                            )

                            metadata = FileMetadata.from_file(temp_path)

                            assert metadata.file_type == FileType.IMAGE
                            assert metadata.mime_type == "image/jpeg"

        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    @pytest.mark.unit
    def test_file_metadata_document_detection(self):
        """Test document file type detection."""
        test_cases = [
            ("application/pdf", FileType.DOCUMENT),
            ("application/msword", FileType.DOCUMENT),
            ("application/vnd.openxmlformats-officedocument", FileType.DOCUMENT),
            ("video/mp4", FileType.VIDEO),
            ("audio/mpeg", FileType.AUDIO),
            ("application/zip", FileType.ARCHIVE),
            ("application/octet-stream", FileType.UNKNOWN),
        ]

        for mime_type, expected_type in test_cases:
            with tempfile.NamedTemporaryFile(suffix=".test", delete=False) as f:
                temp_path = f.name

            try:
                with patch("mimetypes.guess_type", return_value=(mime_type, None)):
                    with patch("builtins.open", create=True) as mock_open:
                        with patch("os.stat") as mock_stat:
                            stat_result = Mock()
                            stat_result.st_size = 1024
                            stat_result.st_ctime = time.time()
                            stat_result.st_mtime = time.time()
                            mock_stat.return_value = stat_result

                            mock_open.return_value.__enter__.return_value.read.return_value = (
                                b"test data"
                            )

                            metadata = FileMetadata.from_file(temp_path)
                            assert metadata.file_type == expected_type

            finally:
                try:
                    os.unlink(temp_path)
                except FileNotFoundError:
                    pass

    @pytest.mark.unit
    def test_file_metadata_nonexistent_file(self):
        """Test metadata creation for non-existent file."""
        with pytest.raises((FileNotFoundError, OSError)):
            FileMetadata.from_file("/nonexistent/file.txt")


class TestProcessingOptions:
    """Test processing options configuration."""

    @pytest.mark.unit
    def test_processing_options_defaults(self):
        """Test default processing options."""
        options = ProcessingOptions()

        # General options
        assert options.preserve_original is True
        assert options.output_directory is None
        assert options.output_format is None
        assert options.quality == 85

        # Image options
        assert options.resize_width is None
        assert options.resize_height is None
        assert options.maintain_aspect_ratio is True
        assert options.generate_thumbnails is False
        assert options.thumbnail_sizes == [(150, 150), (300, 300)]
        assert options.optimize_size is True
        assert options.strip_metadata is False
        assert options.watermark_path is None

        # Document options
        assert options.extract_text is True
        assert options.extract_images is False
        assert options.convert_to_pdf is False
        assert options.merge_pages is None
        assert options.split_pages is False

        # Security options
        assert options.scan_for_viruses is False
        assert options.max_file_size == 100 * 1024 * 1024  # 100MB
        assert options.allowed_extensions is None
        assert ".exe" in options.blocked_extensions

    @pytest.mark.unit
    def test_processing_options_custom_values(self):
        """Test custom processing options."""
        options = ProcessingOptions(
            quality=95,
            resize_width=800,
            resize_height=600,
            generate_thumbnails=True,
            extract_text=False,
            max_file_size=50 * 1024 * 1024,  # 50MB
            allowed_extensions=[".jpg", ".png"],
        )

        assert options.quality == 95
        assert options.resize_width == 800
        assert options.resize_height == 600
        assert options.generate_thumbnails is True
        assert options.extract_text is False
        assert options.max_file_size == 50 * 1024 * 1024
        assert options.allowed_extensions == [".jpg", ".png"]


class TestProcessingResult:
    """Test processing result functionality."""

    @pytest.mark.unit
    def test_processing_result_initialization(self):
        """Test processing result initialization."""
        result = ProcessingResult(
            status=ProcessingStatus.PENDING, original_file="/path/to/file.jpg"
        )

        assert result.status == ProcessingStatus.PENDING
        assert result.original_file == "/path/to/file.jpg"
        assert result.processed_files == []
        assert result.metadata is None
        assert result.extracted_text is None
        assert result.thumbnails == []
        assert result.errors == []
        assert result.warnings == []
        assert result.processing_time == 0.0
        assert result.extra_data == {}

        # Test success property
        assert result.success is False

    @pytest.mark.unit
    def test_processing_result_success_property(self):
        """Test processing result success property."""
        # Test successful result
        result = ProcessingResult(
            status=ProcessingStatus.COMPLETED, original_file="/path/to/file.jpg"
        )
        assert result.success is True

        # Test failed result
        result.status = ProcessingStatus.FAILED
        assert result.success is False

        # Test pending result
        result.status = ProcessingStatus.PENDING
        assert result.success is False

    @pytest.mark.unit
    def test_processing_result_add_methods(self):
        """Test processing result add methods."""
        result = ProcessingResult(
            status=ProcessingStatus.PROCESSING, original_file="/path/to/file.jpg"
        )

        # Test add_processed_file
        result.add_processed_file("/path/to/processed.jpg")
        assert "/path/to/processed.jpg" in result.processed_files

        # Test add_thumbnail
        result.add_thumbnail("/path/to/thumb.jpg")
        assert "/path/to/thumb.jpg" in result.thumbnails

        # Test add_error
        result.add_error("Processing failed")
        assert "Processing failed" in result.errors
        assert result.status == ProcessingStatus.FAILED

        # Test add_warning
        result.add_warning("Quality reduced")
        assert "Quality reduced" in result.warnings

    @pytest.mark.unit
    def test_processing_result_multiple_files(self):
        """Test processing result with multiple files."""
        result = ProcessingResult(
            status=ProcessingStatus.PROCESSING, original_file="/path/to/file.jpg"
        )

        # Add multiple processed files
        files = ["/path/to/processed1.jpg", "/path/to/processed2.jpg", "/path/to/processed3.jpg"]

        for file_path in files:
            result.add_processed_file(file_path)

        assert len(result.processed_files) == 3
        assert all(f in result.processed_files for f in files)

        # Add multiple thumbnails
        thumbnails = ["/path/to/thumb1.jpg", "/path/to/thumb2.jpg"]

        for thumb in thumbnails:
            result.add_thumbnail(thumb)

        assert len(result.thumbnails) == 2
        assert all(t in result.thumbnails for t in thumbnails)


class TestProcessingStatus:
    """Test processing status enum."""

    @pytest.mark.unit
    def test_processing_status_values(self):
        """Test processing status enum values."""
        assert ProcessingStatus.PENDING == "pending"
        assert ProcessingStatus.PROCESSING == "processing"
        assert ProcessingStatus.COMPLETED == "completed"
        assert ProcessingStatus.FAILED == "failed"
        assert ProcessingStatus.CANCELLED == "cancelled"

    @pytest.mark.unit
    def test_processing_status_comparison(self):
        """Test processing status comparisons."""
        assert ProcessingStatus.PENDING != ProcessingStatus.PROCESSING
        assert ProcessingStatus.COMPLETED == ProcessingStatus.COMPLETED

        # Test string comparison
        assert ProcessingStatus.PENDING == "pending"
        assert ProcessingStatus.COMPLETED == "completed"


class TestFileType:
    """Test file type enum."""

    @pytest.mark.unit
    def test_file_type_values(self):
        """Test file type enum values."""
        assert FileType.IMAGE == "image"
        assert FileType.DOCUMENT == "document"
        assert FileType.VIDEO == "video"
        assert FileType.AUDIO == "audio"
        assert FileType.ARCHIVE == "archive"
        assert FileType.TEXT == "text"
        assert FileType.UNKNOWN == "unknown"

    @pytest.mark.unit
    def test_file_type_comparison(self):
        """Test file type comparisons."""
        assert FileType.IMAGE != FileType.DOCUMENT
        assert FileType.UNKNOWN == FileType.UNKNOWN

        # Test string comparison
        assert FileType.IMAGE == "image"
        assert FileType.DOCUMENT == "document"


class TestProcessingError:
    """Test processing error exception."""

    @pytest.mark.unit
    def test_processing_error_creation(self):
        """Test processing error creation."""
        error = ProcessingError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    @pytest.mark.unit
    def test_processing_error_inheritance(self):
        """Test processing error inheritance."""
        error = ProcessingError("Test error")
        assert isinstance(error, Exception)
        assert isinstance(error, ProcessingError)


class MockFileProcessor:
    """Mock file processor for testing FileProcessor protocol."""

    async def process(self, file_path: str, options=None):
        """Mock process method."""
        return ProcessingResult(status=ProcessingStatus.COMPLETED, original_file=file_path)

    async def validate(self, file_path: str):
        """Mock validate method."""
        return True

    async def extract_metadata(self, file_path: str):
        """Mock extract metadata method."""
        return FileMetadata(
            filename="test.txt",
            file_path=file_path,
            file_size=1024,
            mime_type="text/plain",
            file_hash="abcd1234",
            created_at=datetime.now(),
            modified_at=datetime.now(),
            file_type=FileType.TEXT,
            extension=".txt",
        )


class TestFileProcessor:
    """Test file processor protocol."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_file_processor_protocol(self):
        """Test file processor protocol compliance."""
        processor = MockFileProcessor()

        # Test process method
        result = await processor.process("/path/to/file.txt")
        assert isinstance(result, ProcessingResult)
        assert result.status == ProcessingStatus.COMPLETED

        # Test validate method
        is_valid = await processor.validate("/path/to/file.txt")
        assert is_valid is True

        # Test extract_metadata method
        metadata = await processor.extract_metadata("/path/to/file.txt")
        assert isinstance(metadata, FileMetadata)
        assert metadata.file_type == FileType.TEXT


class TestIntegrationScenarios:
    """Integration tests for file processing base components."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_processing_workflow(self):
        """Test complete file processing workflow."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content for processing")
            temp_path = f.name

        try:
            # Extract metadata
            metadata = FileMetadata.from_file(temp_path)
            assert metadata.file_type == FileType.TEXT
            assert metadata.file_size > 0

            # Create processing options
            options = ProcessingOptions(extract_text=True, preserve_original=True)

            # Create processing result
            result = ProcessingResult(
                status=ProcessingStatus.PROCESSING, original_file=temp_path, metadata=metadata
            )

            # Simulate processing steps
            result.add_processed_file(temp_path + ".processed")
            result.processing_time = 0.5
            result.status = ProcessingStatus.COMPLETED
            result.extracted_text = "Test content for processing"

            # Verify final result
            assert result.success is True
            assert result.extracted_text is not None
            assert len(result.processed_files) == 1
            assert result.processing_time > 0

        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    @pytest.mark.integration
    def test_error_handling_workflow(self):
        """Test error handling in processing workflow."""
        result = ProcessingResult(
            status=ProcessingStatus.PROCESSING, original_file="/path/to/file.txt"
        )

        # Add multiple errors
        result.add_error("File not found")
        result.add_error("Invalid format")
        result.add_warning("Quality reduced")

        # Verify error state
        assert result.status == ProcessingStatus.FAILED
        assert len(result.errors) == 2
        assert len(result.warnings) == 1
        assert result.success is False

        # Verify error messages
        assert "File not found" in result.errors
        assert "Invalid format" in result.errors
        assert "Quality reduced" in result.warnings

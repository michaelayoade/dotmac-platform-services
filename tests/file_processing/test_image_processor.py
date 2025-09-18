"""
Comprehensive tests for image processing functionality.
"""

import io
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from PIL import Image

from dotmac.platform.file_processing.base import (
    ProcessingOptions,
    ProcessingResult,
    ProcessingStatus,
)
from dotmac.platform.file_processing.processors import ImageProcessor


class TestImageProcessor:
    """Test image processing functionality."""

    @pytest.fixture
    def image_processor(self):
        """Create image processor instance."""
        with patch(
            "dotmac.platform.file_processing.processors.ImageProcessor"
        ) as MockImageProcessor:
            instance = Mock()
            MockImageProcessor.return_value = instance
            return instance

    @pytest.fixture
    def processing_options(self):
        """Create processing options for testing."""
        return ProcessingOptions(
            resize_width=800,
            resize_height=600,
            generate_thumbnails=True,
            thumbnail_sizes=[(150, 150), (300, 300)],
            optimize_size=True,
            quality=85,
        )

    @pytest.fixture
    def sample_image_path(self):
        """Create a temporary test image."""
        # Create a simple test image
        img = Image.new("RGB", (1000, 800), color="red")

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            img.save(f.name, "JPEG")
            temp_path = f.name

        yield temp_path

        # Cleanup
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass

    @pytest.fixture
    def invalid_image_path(self):
        """Create a file that looks like an image but isn't."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"This is not an image")
            temp_path = f.name

        yield temp_path

        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass

    @pytest.mark.unit
    def test_image_processor_initialization(self):
        """Test image processor initialization."""
        processor = ImageProcessor()
        assert processor.options is not None
        assert isinstance(processor.options, ProcessingOptions)

        # Test with custom options
        options = ProcessingOptions(quality=95)
        processor = ImageProcessor(options)
        assert processor.options.quality == 95

    @pytest.mark.unit
    def test_supported_formats(self):
        """Test supported image formats."""
        processor = ImageProcessor()

        supported = processor.SUPPORTED_FORMATS

        assert ".jpg" in supported
        assert ".jpeg" in supported
        assert ".png" in supported
        assert ".gif" in supported
        assert ".bmp" in supported
        assert ".webp" in supported
        assert ".tiff" in supported
        assert ".ico" in supported
        assert ".svg" in supported

        # Test case insensitive
        assert len(supported) == len({f.lower() for f in supported})

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_valid_image(self, image_processor, sample_image_path):
        """Test validation of valid image file."""
        is_valid = await image_processor.validate(sample_image_path)
        assert is_valid is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_invalid_image(self, image_processor, invalid_image_path):
        """Test validation of invalid image file."""
        is_valid = await image_processor.validate(invalid_image_path)
        assert is_valid is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_nonexistent_file(self, image_processor):
        """Test validation of non-existent file."""
        is_valid = await image_processor.validate("/nonexistent/file.jpg")
        assert is_valid is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_unsupported_extension(self, image_processor):
        """Test validation of unsupported file extension."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            temp_path = f.name

        try:
            is_valid = await image_processor.validate(temp_path)
            assert is_valid is False
        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_metadata_basic(self, image_processor, sample_image_path):
        """Test basic metadata extraction."""
        metadata = await image_processor.extract_metadata(sample_image_path)

        assert metadata is not None
        assert metadata.dimensions == (1000, 800)
        assert metadata.file_path == sample_image_path
        assert "mode" in metadata.extra_metadata
        assert "format" in metadata.extra_metadata

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_metadata_with_exif(self, image_processor):
        """Test metadata extraction with EXIF data."""
        # Create image with EXIF data
        img = Image.new("RGB", (800, 600), color="blue")

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            img.save(f.name, "JPEG", exif=b"mock_exif_data")
            temp_path = f.name

        try:
            metadata = await image_processor.extract_metadata(temp_path)
            assert metadata.dimensions == (800, 600)
            assert metadata.extra_metadata["format"] == "JPEG"
        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_metadata_error_handling(self, image_processor, invalid_image_path):
        """Test metadata extraction error handling."""
        metadata = await image_processor.extract_metadata(invalid_image_path)

        assert metadata is not None
        assert "metadata_error" in metadata.extra_metadata

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_basic_image(self, image_processor, sample_image_path):
        """Test basic image processing."""
        options = ProcessingOptions(generate_thumbnails=False, strip_metadata=False)

        result = await image_processor.process(sample_image_path, options)

        assert result.status == ProcessingStatus.COMPLETED
        assert result.success is True
        assert result.original_file == sample_image_path
        assert result.metadata is not None
        assert result.processing_time > 0
        assert len(result.processed_files) > 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_with_resize(self, image_processor, sample_image_path):
        """Test image processing with resize."""
        options = ProcessingOptions(
            resize_width=400,
            resize_height=300,
            maintain_aspect_ratio=False,
            generate_thumbnails=False,
        )

        result = await image_processor.process(sample_image_path, options)

        assert result.status == ProcessingStatus.COMPLETED
        assert result.success is True
        assert len(result.processed_files) > 0

        # Verify the processed image exists and has correct dimensions
        processed_file = result.processed_files[0]
        if os.path.exists(processed_file):
            with Image.open(processed_file) as img:
                assert img.size == (400, 300)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_with_aspect_ratio_resize(self, image_processor, sample_image_path):
        """Test image processing with aspect ratio maintained."""
        options = ProcessingOptions(
            resize_width=500, maintain_aspect_ratio=True, generate_thumbnails=False
        )

        result = await image_processor.process(sample_image_path, options)

        assert result.status == ProcessingStatus.COMPLETED
        assert result.success is True

        # Original image is 1000x800, so with width=500, height should be 400
        processed_file = result.processed_files[0]
        if os.path.exists(processed_file):
            with Image.open(processed_file) as img:
                assert img.size == (500, 400)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_with_thumbnails(self, image_processor, sample_image_path):
        """Test image processing with thumbnail generation."""
        options = ProcessingOptions(
            generate_thumbnails=True, thumbnail_sizes=[(150, 150), (300, 300)]
        )

        result = await image_processor.process(sample_image_path, options)

        assert result.status == ProcessingStatus.COMPLETED
        assert result.success is True
        assert len(result.thumbnails) == 2

        # Verify thumbnail files exist and have correct sizes
        for i, thumb_path in enumerate(result.thumbnails):
            if os.path.exists(thumb_path):
                with Image.open(thumb_path) as img:
                    expected_size = options.thumbnail_sizes[i]
                    # Thumbnails maintain aspect ratio, so check max dimension
                    assert max(img.size) <= max(expected_size)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_with_watermark(self, image_processor, sample_image_path):
        """Test image processing with watermark."""
        # Create a simple watermark image
        watermark = Image.new("RGBA", (100, 100), (255, 255, 255, 128))
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            watermark.save(f.name, "PNG")
            watermark_path = f.name

        try:
            options = ProcessingOptions(watermark_path=watermark_path, generate_thumbnails=False)

            result = await image_processor.process(sample_image_path, options)

            assert result.status == ProcessingStatus.COMPLETED
            assert result.success is True
            assert len(result.processed_files) > 0

        finally:
            try:
                os.unlink(watermark_path)
            except FileNotFoundError:
                pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_with_metadata_stripping(self, image_processor, sample_image_path):
        """Test image processing with metadata stripping."""
        options = ProcessingOptions(strip_metadata=True, generate_thumbnails=False)

        result = await image_processor.process(sample_image_path, options)

        assert result.status == ProcessingStatus.COMPLETED
        assert result.success is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_with_custom_output_directory(self, image_processor, sample_image_path):
        """Test image processing with custom output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            options = ProcessingOptions(output_directory=temp_dir, generate_thumbnails=True)

            result = await image_processor.process(sample_image_path, options)

            assert result.status == ProcessingStatus.COMPLETED
            assert result.success is True

            # Verify files are in the output directory
            for file_path in result.processed_files + result.thumbnails:
                assert str(temp_dir) in file_path

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_with_format_conversion(self, image_processor, sample_image_path):
        """Test image processing with format conversion."""
        options = ProcessingOptions(output_format="png", generate_thumbnails=False)

        result = await image_processor.process(sample_image_path, options)

        assert result.status == ProcessingStatus.COMPLETED
        assert result.success is True
        assert len(result.processed_files) > 0

        # Verify output file has correct extension
        processed_file = result.processed_files[0]
        assert processed_file.endswith(".png")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_invalid_image(self, image_processor, invalid_image_path):
        """Test processing of invalid image."""
        result = await image_processor.process(invalid_image_path)

        assert result.status == ProcessingStatus.FAILED
        assert result.success is False
        assert len(result.errors) > 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_nonexistent_image(self, image_processor):
        """Test processing of non-existent image."""
        result = await image_processor.process("/nonexistent/file.jpg")

        assert result.status == ProcessingStatus.FAILED
        assert result.success is False
        assert len(result.errors) > 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_with_exception_handling(self, image_processor, sample_image_path):
        """Test exception handling during processing."""
        # Mock Image.open to raise an exception
        with patch("PIL.Image.open", side_effect=Exception("Mock processing error")):
            result = await image_processor.process(sample_image_path)

            assert result.status == ProcessingStatus.FAILED
            assert result.success is False
            assert len(result.errors) > 0
            assert "Mock processing error" in result.errors[0]

    @pytest.mark.unit
    def test_resize_image_width_only(self, image_processor):
        """Test resize with width only."""
        img = Image.new("RGB", (1000, 800), color="red")

        resized = image_processor._resize_image(img, 500, None, True)
        assert resized.size == (500, 400)  # Maintains aspect ratio

    @pytest.mark.unit
    def test_resize_image_height_only(self, image_processor):
        """Test resize with height only."""
        img = Image.new("RGB", (1000, 800), color="red")

        resized = image_processor._resize_image(img, None, 400, True)
        assert resized.size == (500, 400)  # Maintains aspect ratio

    @pytest.mark.unit
    def test_resize_image_both_dimensions(self, image_processor):
        """Test resize with both dimensions."""
        img = Image.new("RGB", (1000, 800), color="red")

        # With aspect ratio maintained - should fit within bounds
        resized = image_processor._resize_image(img, 600, 300, True)
        assert resized.size == (375, 300)  # Limited by height

        # Without aspect ratio maintained - should be exact dimensions
        resized = image_processor._resize_image(img, 600, 300, False)
        assert resized.size == (600, 300)

    @pytest.mark.unit
    def test_resize_image_no_dimensions(self, image_processor):
        """Test resize with no dimensions specified."""
        img = Image.new("RGB", (1000, 800), color="red")

        resized = image_processor._resize_image(img, None, None, True)
        assert resized.size == (1000, 800)  # No change

    @pytest.mark.unit
    def test_strip_metadata(self, image_processor):
        """Test metadata stripping."""
        img = Image.new("RGB", (100, 100), color="blue")

        stripped = image_processor._strip_metadata(img)
        assert stripped.size == img.size
        assert stripped.mode == img.mode

        # Verify it's a new image object
        assert stripped is not img

    @pytest.mark.unit
    def test_get_output_path_default(self, image_processor):
        """Test output path generation with defaults."""
        original_path = "/path/to/image.jpg"
        options = ProcessingOptions()

        output_path = image_processor._get_output_path(original_path, options)

        assert "image_processed.jpg" in output_path
        assert "/path/to/" in output_path

    @pytest.mark.unit
    def test_get_output_path_custom_directory(self, image_processor):
        """Test output path generation with custom directory."""
        original_path = "/path/to/image.jpg"
        options = ProcessingOptions(output_directory="/custom/output")

        with patch("os.makedirs"):
            output_path = image_processor._get_output_path(original_path, options)

        assert "/custom/output/" in output_path
        assert "image_processed.jpg" in output_path

    @pytest.mark.unit
    def test_get_output_path_format_conversion(self, image_processor):
        """Test output path generation with format conversion."""
        original_path = "/path/to/image.jpg"
        options = ProcessingOptions(output_format="png")

        output_path = image_processor._get_output_path(original_path, options)

        assert output_path.endswith(".png")
        assert "image_processed" in output_path

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_image_processing_workflow(self, image_processor):
        """Test complete image processing workflow."""
        # Create test image
        img = Image.new("RGB", (800, 600), color=(255, 0, 0))
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            img.save(f.name, "JPEG")
            temp_path = f.name

        try:
            # Create comprehensive processing options
            options = ProcessingOptions(
                resize_width=400,
                resize_height=300,
                generate_thumbnails=True,
                thumbnail_sizes=[(100, 100), (200, 200)],
                optimize_size=True,
                quality=90,
                strip_metadata=True,
            )

            # Process the image
            result = await image_processor.process(temp_path, options)

            # Verify results
            assert result.success is True
            assert result.status == ProcessingStatus.COMPLETED
            assert result.metadata is not None
            assert result.metadata.dimensions == (800, 600)
            assert len(result.processed_files) == 1
            assert len(result.thumbnails) == 2
            assert result.processing_time > 0
            assert len(result.errors) == 0

            # Verify processed files exist and have correct properties
            processed_file = result.processed_files[0]
            if os.path.exists(processed_file):
                with Image.open(processed_file) as processed_img:
                    assert processed_img.size == (400, 300)

            # Verify thumbnails exist and have correct properties
            for thumb_path in result.thumbnails:
                if os.path.exists(thumb_path):
                    with Image.open(thumb_path) as thumb_img:
                        assert max(thumb_img.size) <= 200

            # Cleanup processed files
            for file_path in result.processed_files + result.thumbnails:
                try:
                    os.unlink(file_path)
                except FileNotFoundError:
                    pass

        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_large_image_processing(self, image_processor):
        """Test processing of large images."""
        # Create a large test image
        img = Image.new("RGB", (4000, 3000), color="green")
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            img.save(f.name, "JPEG", quality=95)
            temp_path = f.name

        try:
            options = ProcessingOptions(
                resize_width=1000, generate_thumbnails=True, optimize_size=True
            )

            result = await image_processor.process(temp_path, options)

            assert result.success is True
            assert result.processing_time > 0
            assert len(result.processed_files) > 0

            # Cleanup
            for file_path in result.processed_files + result.thumbnails:
                try:
                    os.unlink(file_path)
                except FileNotFoundError:
                    pass

        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

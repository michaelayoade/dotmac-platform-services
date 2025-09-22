"""
Working tests for file processing module with correct imports.
Developer 3 - Coverage improvement.
"""

import asyncio
import io
import os
import tempfile
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, MagicMock, patch, mock_open

import pytest
from PIL import Image

from dotmac.platform.file_processing.base import (
    ProcessingStatus,
    FileType,
    FileMetadata,
    ProcessingOptions,
    ProcessingResult,
    ProcessingError,
    FileProcessor,
)
from dotmac.platform.file_processing.processors import (
    ImageProcessor,
    DocumentProcessor,
    VideoProcessor,
    AudioProcessor,
)
from dotmac.platform.file_processing.pipeline import (
    PipelineError,
    PipelineStepError,
    StepMode,
    PipelineStepResult,
    PipelineConfig,
    PipelineStep,
    PipelineResult,
    ProcessingPipeline,
)


class TestProcessingStatus:
    """Test processing status enumeration."""

    def test_processing_status_values(self):
        """Test processing status enum values."""
        assert ProcessingStatus.PENDING == "pending"
        assert ProcessingStatus.PROCESSING == "processing"
        assert ProcessingStatus.COMPLETED == "completed"
        assert ProcessingStatus.FAILED == "failed"


class TestFileType:
    """Test file type enumeration."""

    def test_file_type_values(self):
        """Test file type enum values."""
        assert FileType.IMAGE == "image"
        assert FileType.DOCUMENT == "document"
        assert FileType.VIDEO == "video"
        assert FileType.AUDIO == "audio"


class TestFileMetadata:
    """Test file metadata class."""

    def test_file_metadata_creation(self):
        """Test creating file metadata."""
        metadata = FileMetadata(
            file_name="test.png",
            file_size=1024,
            mime_type="image/png",
            created_at=datetime.now(UTC),
            modified_at=datetime.now(UTC)
        )

        assert metadata.file_name == "test.png"
        assert metadata.file_size == 1024
        assert metadata.mime_type == "image/png"
        assert metadata.created_at is not None

    def test_file_metadata_with_dimensions(self):
        """Test file metadata with image dimensions."""
        metadata = FileMetadata(
            file_name="image.jpg",
            file_size=2048,
            mime_type="image/jpeg",
            width=800,
            height=600,
            format="JPEG"
        )

        assert metadata.width == 800
        assert metadata.height == 600
        assert metadata.format == "JPEG"


class TestProcessingOptions:
    """Test processing options."""

    def test_processing_options_defaults(self):
        """Test default processing options."""
        options = ProcessingOptions()

        assert options.extract_text is True
        assert options.extract_metadata is True
        assert options.strip_metadata is False
        assert options.validate_content is True

    def test_processing_options_custom(self):
        """Test custom processing options."""
        options = ProcessingOptions(
            extract_text=False,
            strip_metadata=True,
            max_file_size=50 * 1024 * 1024,
            resize_width=800,
            resize_height=600
        )

        assert options.extract_text is False
        assert options.strip_metadata is True
        assert options.max_file_size == 50 * 1024 * 1024
        assert options.resize_width == 800
        assert options.resize_height == 600


class TestProcessingResult:
    """Test processing result."""

    def test_processing_result_creation(self):
        """Test creating processing result."""
        result = ProcessingResult(
            status=ProcessingStatus.COMPLETED,
            original_file="/path/to/file.jpg",
            processed_file="/path/to/processed.jpg"
        )

        assert result.status == ProcessingStatus.COMPLETED
        assert result.original_file == "/path/to/file.jpg"
        assert result.processed_file == "/path/to/processed.jpg"

    def test_processing_result_with_metadata(self):
        """Test processing result with metadata."""
        metadata = FileMetadata(
            file_name="test.pdf",
            file_size=5000,
            mime_type="application/pdf"
        )

        result = ProcessingResult(
            status=ProcessingStatus.COMPLETED,
            original_file="/path/to/test.pdf",
            metadata=metadata
        )

        assert result.metadata is not None
        assert result.metadata.file_name == "test.pdf"

    def test_processing_result_with_errors(self):
        """Test processing result with errors."""
        result = ProcessingResult(
            status=ProcessingStatus.FAILED,
            original_file="/path/to/file.txt"
        )

        result.add_error("File not found")
        result.add_error("Permission denied")

        assert len(result.errors) == 2
        assert "File not found" in result.errors
        assert "Permission denied" in result.errors


class TestImageProcessor:
    """Test image processor."""

    @pytest.fixture
    def image_processor(self):
        """Create image processor instance."""
        return ImageProcessor()

    @pytest.fixture
    def sample_image(self):
        """Create a sample image."""
        img = Image.new('RGB', (100, 100), color='red')
        return img

    async def test_process_valid_image(self, image_processor, sample_image):
        """Test processing a valid image."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            sample_image.save(tmp.name)
            tmp.flush()

            try:
                result = await image_processor.process(tmp.name)

                assert result.status == ProcessingStatus.COMPLETED
                assert result.metadata is not None
                assert result.metadata.width == 100
                assert result.metadata.height == 100
            finally:
                os.unlink(tmp.name)

    async def test_validate_image(self, image_processor, sample_image):
        """Test image validation."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            sample_image.save(tmp.name)
            tmp.flush()

            try:
                is_valid = await image_processor.validate(tmp.name)
                assert is_valid is True
            finally:
                os.unlink(tmp.name)

    async def test_extract_image_metadata(self, image_processor, sample_image):
        """Test extracting image metadata."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            sample_image.save(tmp.name)
            tmp.flush()

            try:
                metadata = await image_processor.extract_metadata(tmp.name)

                assert metadata is not None
                assert metadata.width == 100
                assert metadata.height == 100
                assert metadata.format in ["PNG", "png"]
            finally:
                os.unlink(tmp.name)

    async def test_process_with_resize(self, image_processor):
        """Test processing image with resize options."""
        img = Image.new('RGB', (1000, 800), color='blue')

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            img.save(tmp.name)
            tmp.flush()

            try:
                options = ProcessingOptions(
                    resize_width=500,
                    resize_height=400
                )

                result = await image_processor.process(tmp.name, options)

                assert result.status == ProcessingStatus.COMPLETED
                # Processed file should be created with new dimensions
            finally:
                os.unlink(tmp.name)
                if result.processed_file and os.path.exists(result.processed_file):
                    os.unlink(result.processed_file)

    async def test_invalid_image_file(self, image_processor):
        """Test processing invalid image file."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp.write(b"Not an image")
            tmp.flush()

            try:
                result = await image_processor.process(tmp.name)

                assert result.status == ProcessingStatus.FAILED
                assert len(result.errors) > 0
            finally:
                os.unlink(tmp.name)


class TestDocumentProcessor:
    """Test document processor."""

    @pytest.fixture
    def document_processor(self):
        """Create document processor instance."""
        return DocumentProcessor()

    async def test_process_text_file(self, document_processor):
        """Test processing text file."""
        content = "This is a test document.\nWith multiple lines."

        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w') as tmp:
            tmp.write(content)
            tmp.flush()

            try:
                result = await document_processor.process(tmp.name)

                assert result.status == ProcessingStatus.COMPLETED
                assert result.extracted_text == content
            finally:
                os.unlink(tmp.name)

    @patch('PyPDF2.PdfReader')
    async def test_process_pdf_file(self, mock_pdf_reader, document_processor):
        """Test processing PDF file."""
        # Mock PDF reader
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "PDF content"
        mock_reader.pages = [mock_page]
        mock_reader.metadata = {'/Title': 'Test PDF'}
        mock_pdf_reader.return_value = mock_reader

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(b"fake pdf content")
            tmp.flush()

            try:
                result = await document_processor.process(tmp.name)

                assert result.status == ProcessingStatus.COMPLETED
                assert result.extracted_text == "PDF content"
                assert result.metadata.title == "Test PDF"
            finally:
                os.unlink(tmp.name)

    async def test_extract_document_metadata(self, document_processor):
        """Test extracting document metadata."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w') as tmp:
            tmp.write("Test content")
            tmp.flush()

            try:
                metadata = await document_processor.extract_metadata(tmp.name)

                assert metadata is not None
                assert metadata.file_size > 0
                assert metadata.mime_type == "text/plain"
            finally:
                os.unlink(tmp.name)


class TestPipeline:
    """Test processing pipeline."""

    def test_pipeline_config(self):
        """Test pipeline configuration."""
        config = settings.Pipeline.model_copy(update={
            name="test_pipeline",
            steps=["step1", "step2"],
            parallel_execution=False,
            continue_on_error=True
        })

        assert config.name == "test_pipeline"
        assert len(config.steps) == 2
        assert config.parallel_execution is False
        assert config.continue_on_error is True

    def test_pipeline_step_result(self):
        """Test pipeline step result."""
        result = PipelineStepResult(
            step_name="validation",
            status=ProcessingStatus.COMPLETED,
            output={"valid": True},
            duration_seconds=1.5
        )

        assert result.step_name == "validation"
        assert result.status == ProcessingStatus.COMPLETED
        assert result.output["valid"] is True
        assert result.duration_seconds == 1.5

    async def test_pipeline_step_execution(self):
        """Test pipeline step execution."""
        async def process_func(file_path: str, **kwargs):
            return {"processed": True}

        step = PipelineStep(
            name="test_step",
            processor=process_func,
            mode=StepMode.SEQUENTIAL
        )

        result = await step.execute("/path/to/file.txt")

        assert result.step_name == "test_step"
        assert result.status == ProcessingStatus.COMPLETED
        assert result.output["processed"] is True

    def test_pipeline_result(self):
        """Test pipeline result."""
        step_results = [
            PipelineStepResult(
                step_name="step1",
                status=ProcessingStatus.COMPLETED
            ),
            PipelineStepResult(
                step_name="step2",
                status=ProcessingStatus.COMPLETED
            )
        ]

        result = PipelineResult(
            pipeline_name="test_pipeline",
            status=ProcessingStatus.COMPLETED,
            step_results=step_results,
            total_duration_seconds=5.0
        )

        assert result.pipeline_name == "test_pipeline"
        assert result.status == ProcessingStatus.COMPLETED
        assert len(result.step_results) == 2
        assert result.total_duration_seconds == 5.0

    async def test_processing_pipeline(self):
        """Test processing pipeline execution."""
        config = settings.Pipeline.model_copy(update={
            name="test_pipeline",
            steps=["step1"]
        })

        pipeline = ProcessingPipeline(config)

        # Add a step
        async def test_processor(file_path: str, **kwargs):
            return {"result": "success"}

        pipeline.add_step(
            PipelineStep(
                name="step1",
                processor=test_processor
            )
        )

        # Execute pipeline
        result = await pipeline.execute("/path/to/file.txt")

        assert result.status == ProcessingStatus.COMPLETED
        assert len(result.step_results) == 1

    async def test_pipeline_error_handling(self):
        """Test pipeline error handling."""
        config = settings.Pipeline.model_copy(update={
            name="test_pipeline",
            steps=["failing_step"],
            continue_on_error=False
        })

        pipeline = ProcessingPipeline(config)

        # Add a failing step
        async def failing_processor(file_path: str, **kwargs):
            raise ProcessingError("Step failed")

        pipeline.add_step(
            PipelineStep(
                name="failing_step",
                processor=failing_processor
            )
        )

        # Execute pipeline - should fail
        result = await pipeline.execute("/path/to/file.txt")

        assert result.status == ProcessingStatus.FAILED
        assert len(result.errors) > 0


class TestExceptionHandling:
    """Test exception handling."""

    def test_processing_error(self):
        """Test ProcessingError exception."""
        error = ProcessingError("Processing failed")
        assert str(error) == "Processing failed"

    def test_pipeline_error(self):
        """Test PipelineError exception."""
        error = PipelineError("Pipeline failed")
        assert "Pipeline failed" in str(error)

    def test_pipeline_step_error(self):
        """Test PipelineStepError exception."""
        error = PipelineStepError("step1", "Step execution failed")
        assert "step1" in str(error)
        assert "Step execution failed" in str(error)
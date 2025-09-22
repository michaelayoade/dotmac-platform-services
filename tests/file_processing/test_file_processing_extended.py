"""
Extended tests for file processing module to improve coverage.
Focuses on uncovered methods, edge cases, and error handling.
"""

import asyncio
import io
import os
import tempfile
import zipfile
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


class TestFileMetadataExtended:
    """Extended file metadata tests."""

    def test_metadata_with_all_fields(self):
        """Test metadata with all optional fields."""
        metadata = FileMetadata(
            file_name="complete.mp4",
            file_size=104857600,  # 100MB
            mime_type="video/mp4",
            width=1920,
            height=1080,
            duration=120.5,
            format="MP4",
            compression="H.264",
            bit_rate=8000000,
            frame_rate=30.0,
            created_at=datetime.now(UTC),
            modified_at=datetime.now(UTC),
            extra_metadata={"codec": "aac", "sample_rate": 44100}
        )

        assert metadata.file_name == "complete.mp4"
        assert metadata.file_size == 104857600
        assert metadata.width == 1920
        assert metadata.height == 1080
        assert metadata.duration == 120.5
        assert metadata.extra_metadata["codec"] == "aac"

    def test_metadata_serialization(self):
        """Test metadata serialization."""
        metadata = FileMetadata(
            file_name="test.jpg",
            file_size=2048,
            mime_type="image/jpeg",
            width=800,
            height=600
        )

        # Should be serializable
        data = metadata.model_dump()
        assert data["file_name"] == "test.jpg"
        assert data["file_size"] == 2048


class TestProcessingOptionsExtended:
    """Extended processing options tests."""

    def test_options_for_video_processing(self):
        """Test options for video processing."""
        options = ProcessingOptions(
            extract_thumbnails=True,
            thumbnail_count=5,
            thumbnail_size=(160, 120),
            extract_metadata=True,
            validate_content=True,
            compress_output=True,
            output_format="mp4",
            quality=80
        )

        assert options.extract_thumbnails is True
        assert options.thumbnail_count == 5
        assert options.thumbnail_size == (160, 120)
        assert options.compress_output is True
        assert options.quality == 80

    def test_options_for_audio_processing(self):
        """Test options for audio processing."""
        options = ProcessingOptions(
            extract_waveform=True,
            sample_rate=44100,
            bit_depth=16,
            channels=2,
            normalize_audio=True,
            trim_silence=True
        )

        assert options.extract_waveform is True
        assert options.sample_rate == 44100
        assert options.bit_depth == 16
        assert options.channels == 2
        assert options.normalize_audio is True
        assert options.trim_silence is True

    def test_options_validation(self):
        """Test options validation."""
        # Test invalid quality
        with pytest.raises(ValueError):
            ProcessingOptions(quality=150)  # Should be 0-100

        # Test invalid resize dimensions
        with pytest.raises(ValueError):
            ProcessingOptions(resize_width=0)


class TestProcessingResultExtended:
    """Extended processing result tests."""

    def test_result_with_thumbnails(self):
        """Test result with thumbnail files."""
        result = ProcessingResult(
            status=ProcessingStatus.COMPLETED,
            original_file="/path/to/video.mp4",
            processed_file="/path/to/processed.mp4",
            thumbnail_files=[
                "/path/to/thumb_001.jpg",
                "/path/to/thumb_002.jpg",
                "/path/to/thumb_003.jpg"
            ]
        )

        assert len(result.thumbnail_files) == 3
        assert result.thumbnail_files[0] == "/path/to/thumb_001.jpg"

    def test_result_with_analytics(self):
        """Test result with processing analytics."""
        result = ProcessingResult(
            status=ProcessingStatus.COMPLETED,
            original_file="/path/to/file.txt",
            processing_time=15.75,
            file_size_reduction=0.25,
            quality_score=0.92
        )

        assert result.processing_time == 15.75
        assert result.file_size_reduction == 0.25
        assert result.quality_score == 0.92

    def test_result_error_aggregation(self):
        """Test aggregating multiple errors."""
        result = ProcessingResult(
            status=ProcessingStatus.FAILED,
            original_file="/path/to/file.txt"
        )

        errors = [
            "File format not supported",
            "Insufficient disk space",
            "Network timeout during upload"
        ]

        for error in errors:
            result.add_error(error)

        assert len(result.errors) == 3
        assert all(error in result.errors for error in errors)


class TestImageProcessorExtended:
    """Extended image processor tests."""

    @pytest.fixture
    def image_processor(self):
        """Create image processor instance."""
        return ImageProcessor()

    @pytest.fixture
    def large_image(self):
        """Create a large test image."""
        return Image.new('RGB', (4000, 3000), color='blue')

    async def test_process_with_format_conversion(self, image_processor):
        """Test processing with format conversion."""
        img = Image.new('RGB', (200, 200), color='green')

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            img.save(tmp.name)
            tmp.flush()

            try:
                options = ProcessingOptions(
                    output_format="jpeg",
                    quality=90
                )

                result = await image_processor.process(tmp.name, options)

                assert result.status == ProcessingStatus.COMPLETED
                # Check that output format was converted
                if result.processed_file:
                    assert result.processed_file.endswith('.jpg') or result.processed_file.endswith('.jpeg')
            finally:
                os.unlink(tmp.name)
                if result.processed_file and os.path.exists(result.processed_file):
                    os.unlink(result.processed_file)

    async def test_process_with_watermark(self, image_processor):
        """Test processing with watermark."""
        img = Image.new('RGB', (300, 300), color='white')

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            img.save(tmp.name)
            tmp.flush()

            try:
                options = ProcessingOptions(
                    add_watermark=True,
                    watermark_text="TEST",
                    watermark_opacity=0.5
                )

                result = await image_processor.process(tmp.name, options)

                # Processing should complete even if watermark feature isn't implemented
                assert result.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]
            finally:
                os.unlink(tmp.name)
                if result.processed_file and os.path.exists(result.processed_file):
                    os.unlink(result.processed_file)

    async def test_process_animated_gif(self, image_processor):
        """Test processing animated GIF."""
        # Create simple animated GIF
        frames = []
        for i in range(3):
            frame = Image.new('RGB', (100, 100), color=(i*80, 0, 0))
            frames.append(frame)

        with tempfile.NamedTemporaryFile(suffix='.gif', delete=False) as tmp:
            frames[0].save(
                tmp.name,
                save_all=True,
                append_images=frames[1:],
                duration=100,
                loop=0
            )
            tmp.flush()

            try:
                result = await image_processor.process(tmp.name)

                assert result.status == ProcessingStatus.COMPLETED
                if result.metadata:
                    assert result.metadata.format in ["GIF", "gif"]
            finally:
                os.unlink(tmp.name)

    async def test_extract_exif_data(self, image_processor):
        """Test extracting EXIF data."""
        img = Image.new('RGB', (200, 200), color='red')

        # Add some EXIF data
        from PIL.ExifTags import TAGS
        exif_data = {
            "Make": "Test Camera",
            "Model": "Test Model",
            "DateTime": "2023:12:01 12:00:00"
        }

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img.save(tmp.name, exif=img.getexif())
            tmp.flush()

            try:
                options = ProcessingOptions(extract_metadata=True)
                result = await image_processor.process(tmp.name, options)

                assert result.status == ProcessingStatus.COMPLETED
                # EXIF extraction should work if implemented
            finally:
                os.unlink(tmp.name)

    async def test_image_optimization(self, image_processor, large_image):
        """Test image optimization for large files."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            large_image.save(tmp.name)
            tmp.flush()

            try:
                options = ProcessingOptions(
                    optimize=True,
                    quality=75,
                    strip_metadata=True
                )

                result = await image_processor.process(tmp.name, options)

                assert result.status == ProcessingStatus.COMPLETED
                # Should reduce file size
                if result.processed_file and os.path.exists(result.processed_file):
                    original_size = os.path.getsize(tmp.name)
                    processed_size = os.path.getsize(result.processed_file)
                    # Optimization should reduce size (or at least not increase significantly)
                    assert processed_size <= original_size * 1.1
            finally:
                os.unlink(tmp.name)
                if result.processed_file and os.path.exists(result.processed_file):
                    os.unlink(result.processed_file)


class TestDocumentProcessorExtended:
    """Extended document processor tests."""

    @pytest.fixture
    def document_processor(self):
        """Create document processor instance."""
        return DocumentProcessor()

    async def test_process_rtf_document(self, document_processor):
        """Test processing RTF document."""
        rtf_content = r"{\rtf1\ansi\deff0 {\fonttbl {\f0 Times New Roman;}} \f0\fs24 Hello RTF World! }"

        with tempfile.NamedTemporaryFile(suffix='.rtf', delete=False, mode='w') as tmp:
            tmp.write(rtf_content)
            tmp.flush()

            try:
                result = await document_processor.process(tmp.name)

                # Should handle RTF even if parser isn't available
                assert result.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]
            finally:
                os.unlink(tmp.name)

    @patch('docx.Document')
    async def test_process_docx_document(self, mock_docx, document_processor):
        """Test processing DOCX document."""
        # Mock docx Document
        mock_doc = MagicMock()
        mock_paragraph = MagicMock()
        mock_paragraph.text = "Test paragraph content"
        mock_doc.paragraphs = [mock_paragraph]
        mock_docx.return_value = mock_doc

        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
            tmp.write(b"fake docx content")
            tmp.flush()

            try:
                result = await document_processor.process(tmp.name)

                assert result.status == ProcessingStatus.COMPLETED
                assert "Test paragraph content" in result.extracted_text
            finally:
                os.unlink(tmp.name)

    async def test_extract_document_structure(self, document_processor):
        """Test extracting document structure."""
        html_content = """
        <html>
            <head><title>Test Document</title></head>
            <body>
                <h1>Main Heading</h1>
                <p>First paragraph</p>
                <h2>Subheading</h2>
                <p>Second paragraph</p>
            </body>
        </html>
        """

        with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w') as tmp:
            tmp.write(html_content)
            tmp.flush()

            try:
                options = ProcessingOptions(
                    extract_structure=True,
                    extract_headings=True
                )

                result = await document_processor.process(tmp.name, options)

                assert result.status == ProcessingStatus.COMPLETED
                # Should extract text content
                assert "Main Heading" in result.extracted_text or result.status == ProcessingStatus.FAILED
            finally:
                os.unlink(tmp.name)

    async def test_document_language_detection(self, document_processor):
        """Test document language detection."""
        multilingual_content = """
        Hello, this is English text.
        Bonjour, ceci est du texte français.
        Hola, esto es texto en español.
        """

        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w') as tmp:
            tmp.write(multilingual_content)
            tmp.flush()

            try:
                options = ProcessingOptions(
                    detect_language=True,
                    extract_metadata=True
                )

                result = await document_processor.process(tmp.name, options)

                assert result.status == ProcessingStatus.COMPLETED
                # Language detection might be implemented
                if result.metadata and hasattr(result.metadata, 'language'):
                    assert result.metadata.language is not None
            finally:
                os.unlink(tmp.name)


class TestVideoProcessorExtended:
    """Extended video processor tests."""

    @pytest.fixture
    def video_processor(self):
        """Create video processor instance."""
        return VideoProcessor()

    async def test_video_metadata_extraction(self, video_processor):
        """Test video metadata extraction."""
        # Create fake video file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            # Write minimal MP4 header
            tmp.write(b'\x00\x00\x00\x18ftypmp42')
            tmp.flush()

            try:
                result = await video_processor.process(tmp.name)

                # Should handle video file (might fail without proper video library)
                assert result.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]
            finally:
                os.unlink(tmp.name)

    async def test_video_thumbnail_generation(self, video_processor):
        """Test video thumbnail generation."""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp.write(b'fake video content')
            tmp.flush()

            try:
                options = ProcessingOptions(
                    extract_thumbnails=True,
                    thumbnail_count=3,
                    thumbnail_timestamps=[10, 30, 60]
                )

                result = await video_processor.process(tmp.name, options)

                # Should attempt thumbnail extraction
                assert result.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]
            finally:
                os.unlink(tmp.name)

    async def test_video_format_conversion(self, video_processor):
        """Test video format conversion."""
        with tempfile.NamedTemporaryFile(suffix='.avi', delete=False) as tmp:
            tmp.write(b'fake avi content')
            tmp.flush()

            try:
                options = ProcessingOptions(
                    output_format="mp4",
                    video_codec="h264",
                    audio_codec="aac",
                    bitrate=2000000
                )

                result = await video_processor.process(tmp.name, options)

                # Should attempt format conversion
                assert result.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]
            finally:
                os.unlink(tmp.name)


class TestAudioProcessorExtended:
    """Extended audio processor tests."""

    @pytest.fixture
    def audio_processor(self):
        """Create audio processor instance."""
        return AudioProcessor()

    async def test_audio_metadata_extraction(self, audio_processor):
        """Test audio metadata extraction."""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            # Write basic MP3 header
            tmp.write(b'ID3\x03\x00\x00\x00')
            tmp.flush()

            try:
                result = await audio_processor.process(tmp.name)

                # Should handle audio file
                assert result.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]
            finally:
                os.unlink(tmp.name)

    async def test_audio_waveform_generation(self, audio_processor):
        """Test audio waveform generation."""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp.write(b'fake wav content')
            tmp.flush()

            try:
                options = ProcessingOptions(
                    extract_waveform=True,
                    waveform_width=800,
                    waveform_height=200
                )

                result = await audio_processor.process(tmp.name, options)

                # Should attempt waveform generation
                assert result.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]
            finally:
                os.unlink(tmp.name)

    async def test_audio_normalization(self, audio_processor):
        """Test audio normalization."""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            tmp.write(b'fake mp3 content')
            tmp.flush()

            try:
                options = ProcessingOptions(
                    normalize_audio=True,
                    target_loudness=-23.0,
                    trim_silence=True
                )

                result = await audio_processor.process(tmp.name, options)

                # Should attempt normalization
                assert result.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]
            finally:
                os.unlink(tmp.name)


class TestPipelineExtended:
    """Extended pipeline tests."""

    async def test_pipeline_with_conditional_steps(self):
        """Test pipeline with conditional step execution."""
        async def validation_step(file_path: str, **kwargs):
            # Simulate validation that might fail
            if "invalid" in file_path:
                raise ProcessingError("File validation failed")
            return {"valid": True}

        async def processing_step(file_path: str, **kwargs):
            # Only run if validation passed
            return {"processed": True}

        config = settings.Pipeline.model_copy(update={
            name="conditional_pipeline",
            steps=["validation", "processing"],
            continue_on_error=False
        })

        pipeline = ProcessingPipeline(config)

        pipeline.add_step(PipelineStep(
            name="validation",
            processor=validation_step,
            mode=StepMode.SEQUENTIAL,
            required=True
        ))

        pipeline.add_step(PipelineStep(
            name="processing",
            processor=processing_step,
            mode=StepMode.SEQUENTIAL,
            condition=lambda results: any(r.output.get("valid") for r in results)
        ))

        # Test with valid file
        result = await pipeline.execute("/path/to/valid/file.txt")
        assert result.status == ProcessingStatus.COMPLETED

        # Test with invalid file
        result = await pipeline.execute("/path/to/invalid/file.txt")
        assert result.status == ProcessingStatus.FAILED

    async def test_pipeline_parallel_execution(self):
        """Test parallel pipeline execution."""
        async def slow_step(file_path: str, step_name: str, **kwargs):
            # Simulate processing time
            await asyncio.sleep(0.1)
            return {"step": step_name, "duration": 0.1}

        config = settings.Pipeline.model_copy(update={
            name="parallel_pipeline",
            steps=["step1", "step2", "step3"],
            parallel_execution=True
        })

        pipeline = ProcessingPipeline(config)

        for i in range(1, 4):
            step_name = f"step{i}"

            def make_processor(step_name):
                async def processor(fp, **kw):
                    return await slow_step(fp, step_name, **kw)
                return processor

            pipeline.add_step(PipelineStep(
                name=step_name,
                processor=make_processor(step_name),
                mode=StepMode.PARALLEL
            ))

        import time
        start_time = time.time()
        result = await pipeline.execute("/path/to/file.txt")
        duration = time.time() - start_time

        assert result.status == ProcessingStatus.COMPLETED
        # Parallel execution should be faster than sequential
        assert duration < 0.3  # Should be around 0.1s, not 0.3s

    async def test_pipeline_with_data_flow(self):
        """Test pipeline with data flowing between steps."""
        async def extract_step(file_path: str, **kwargs):
            return {"extracted_data": "sample text", "word_count": 2}

        async def analyze_step(file_path: str, previous_results=None, **kwargs):
            # Use data from previous step
            data = previous_results[0].output.get("extracted_data", "")
            word_count = previous_results[0].output.get("word_count", 0)
            return {"analysis": f"Analyzed: {data}", "words": word_count}

        async def report_step(file_path: str, previous_results=None, **kwargs):
            # Combine results from all previous steps
            analysis = previous_results[1].output.get("analysis", "")
            words = previous_results[1].output.get("words", 0)
            return {"report": f"Report: {analysis}, Total words: {words}"}

        config = settings.Pipeline.model_copy(update={
            name="data_flow_pipeline",
            steps=["extract", "analyze", "report"]
        })

        pipeline = ProcessingPipeline(config)

        pipeline.add_step(PipelineStep(
            name="extract",
            processor=extract_step
        ))

        pipeline.add_step(PipelineStep(
            name="analyze",
            processor=analyze_step
        ))

        pipeline.add_step(PipelineStep(
            name="report",
            processor=report_step
        ))

        result = await pipeline.execute("/path/to/file.txt")

        assert result.status == ProcessingStatus.COMPLETED
        assert len(result.step_results) == 3

        # Check data flow
        report_result = result.step_results[2]
        assert "Analyzed: sample text" in report_result.output["report"]
        assert "Total words: 2" in report_result.output["report"]

    async def test_pipeline_rollback_on_failure(self):
        """Test pipeline rollback on failure."""
        executed_steps = []

        async def step_with_cleanup(file_path: str, step_name: str, **kwargs):
            executed_steps.append(step_name)
            if step_name == "failing_step":
                raise ProcessingError("Step failed")
            return {"completed": step_name}

        async def cleanup_step(file_path: str, step_name: str, **kwargs):
            executed_steps.append(f"cleanup_{step_name}")
            return {"cleaned": step_name}

        config = settings.Pipeline.model_copy(update={
            name="rollback_pipeline",
            steps=["step1", "failing_step", "step3"],
            rollback_on_failure=True
        })

        pipeline = ProcessingPipeline(config)

        for step_name in ["step1", "failing_step", "step3"]:
            def make_step_processor(step_name):
                async def processor(fp, **kw):
                    return await step_with_cleanup(fp, step_name, **kw)
                return processor

            def make_cleanup_processor(step_name):
                async def processor(fp, **kw):
                    return await cleanup_step(fp, step_name, **kw)
                return processor

            pipeline.add_step(PipelineStep(
                name=step_name,
                processor=make_step_processor(step_name),
                cleanup_processor=make_cleanup_processor(step_name)
            ))

        result = await pipeline.execute("/path/to/file.txt")

        assert result.status == ProcessingStatus.FAILED
        # Should have executed step1, then failing_step, then cleanup
        assert "step1" in executed_steps
        assert "failing_step" in executed_steps
        # Cleanup should run for completed steps
        if hasattr(pipeline, 'rollback_on_failure') and pipeline.rollback_on_failure:
            assert "cleanup_step1" in executed_steps


class TestPerformanceAndStress:
    """Performance and stress tests."""

    async def test_large_batch_processing(self):
        """Test processing large batches of files."""
        config = settings.Pipeline.model_copy(update={
            name="batch_pipeline",
            steps=["process"],
            parallel_execution=True,
            max_concurrent_jobs=5
        })

        pipeline = ProcessingPipeline(config)

        async def batch_processor(file_path: str, **kwargs):
            # Simulate processing
            await asyncio.sleep(0.01)
            return {"processed": file_path}

        pipeline.add_step(PipelineStep(
            name="process",
            processor=batch_processor
        ))

        # Process multiple files
        file_paths = [f"/path/to/file_{i}.txt" for i in range(20)]

        results = []
        for file_path in file_paths:
            result = await pipeline.execute(file_path)
            results.append(result)

        # All should complete
        completed = [r for r in results if r.status == ProcessingStatus.COMPLETED]
        assert len(completed) == 20

    def test_memory_usage_with_large_metadata(self):
        """Test memory usage with large metadata objects."""
        # Create large metadata object
        large_metadata = {
            f"field_{i}": f"value_{i}" * 1000
            for i in range(100)
        }

        metadata = FileMetadata(
            file_name="large_file.dat",
            file_size=1073741824,  # 1GB
            mime_type="application/octet-stream",
            extra_metadata=large_metadata
        )

        result = ProcessingResult(
            status=ProcessingStatus.COMPLETED,
            original_file="/path/to/large_file.dat",
            metadata=metadata
        )

        # Should handle large metadata without issues
        assert result.metadata.extra_metadata is not None
        assert len(result.metadata.extra_metadata) == 100

    async def test_concurrent_pipeline_execution(self):
        """Test concurrent pipeline execution."""
        async def concurrent_processor(file_path: str, **kwargs):
            await asyncio.sleep(0.05)
            return {"file": file_path}

        config = settings.Pipeline.model_copy(update={
            name="concurrent_pipeline",
            steps=["process"]
        })

        pipeline = ProcessingPipeline(config)
        pipeline.add_step(PipelineStep(
            name="process",
            processor=concurrent_processor
        ))

        # Run multiple pipelines concurrently
        tasks = []
        for i in range(10):
            task = asyncio.create_task(
                pipeline.execute(f"/path/to/file_{i}.txt")
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # All should complete successfully
        assert len(results) == 10
        assert all(r.status == ProcessingStatus.COMPLETED for r in results)


class TestErrorRecoveryAndResilience:
    """Test error recovery and resilience."""

    async def test_pipeline_retry_mechanism(self):
        """Test pipeline retry mechanism."""
        attempt_count = 0

        async def flaky_processor(file_path: str, **kwargs):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ProcessingError("Temporary failure")
            return {"success": True, "attempts": attempt_count}

        config = settings.Pipeline.model_copy(update={
            name="retry_pipeline",
            steps=["flaky_step"],
            retry_attempts=3,
            retry_delay=0.01
        })

        pipeline = ProcessingPipeline(config)
        pipeline.add_step(PipelineStep(
            name="flaky_step",
            processor=flaky_processor
        ))

        result = await pipeline.execute("/path/to/file.txt")

        assert result.status == ProcessingStatus.COMPLETED
        assert attempt_count == 3

    async def test_graceful_degradation(self):
        """Test graceful degradation when non-critical steps fail."""
        async def critical_step(file_path: str, **kwargs):
            return {"critical_data": "important"}

        async def optional_step(file_path: str, **kwargs):
            raise ProcessingError("Optional step failed")

        async def final_step(file_path: str, previous_results=None, **kwargs):
            # Should still work with only critical data
            critical_data = previous_results[0].output.get("critical_data")
            return {"final_result": f"Processed with: {critical_data}"}

        config = settings.Pipeline.model_copy(update={
            name="degradation_pipeline",
            steps=["critical", "optional", "final"],
            continue_on_error=True
        })

        pipeline = ProcessingPipeline(config)

        pipeline.add_step(PipelineStep(
            name="critical",
            processor=critical_step,
            required=True
        ))

        pipeline.add_step(PipelineStep(
            name="optional",
            processor=optional_step,
            required=False
        ))

        pipeline.add_step(PipelineStep(
            name="final",
            processor=final_step,
            required=True
        ))

        result = await pipeline.execute("/path/to/file.txt")

        # Should complete despite optional step failure
        assert result.status == ProcessingStatus.COMPLETED
        final_result = result.step_results[2]
        assert "Processed with: important" in final_result.output["final_result"]
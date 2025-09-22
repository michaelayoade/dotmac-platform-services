"""
Comprehensive tests for file processing module.
Testing document parsing, image processing, virus scanning, and metadata extraction.
Developer 3 - Coverage Task: Data Transfer & File Processing
"""

import asyncio
import io
import os
import tempfile
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, Mock, MagicMock, patch, mock_open, PropertyMock

import pytest
from PIL import Image

from dotmac.platform.file_processing.base import (
    FileMetadata,
    FileProcessor,
    ProcessingError,
    ProcessingOptions,
    ProcessingResult,
    ProcessingStatus,
    ValidationError,
)
from dotmac.platform.file_processing.processors import (
    ImageProcessor,
    DocumentProcessor,
    VideoProcessor,
    AudioProcessor,
    SpreadsheetProcessor,
    PresentationProcessor,
)


@pytest.fixture
def mock_http_session():
    """Mock HTTP session for external APIs."""
    session = AsyncMock()
    session.post = AsyncMock(return_value=Mock(
        status_code=200,
        json=lambda: {"scan_result": "clean"}
    ))
    session.get = AsyncMock(return_value=Mock(
        status_code=200,
        content=b"file_content"
    ))
    return session


@pytest.fixture
def processing_options():
    """Create default processing options."""
    return ProcessingOptions(
        extract_text=True,
        extract_metadata=True,
        strip_metadata=False,
        validate_content=True,
        max_file_size=100 * 1024 * 1024,  # 100MB
        allowed_mime_types=None,  # Allow all
        virus_scan=True,
        ocr_enabled=False,
        resize_width=None,
        resize_height=None,
        maintain_aspect_ratio=True,
        watermark_text=None,
        compress_quality=85,
    )


@pytest.fixture
def sample_image():
    """Create a sample image for testing."""
    img = Image.new('RGB', (100, 100), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer


@pytest.fixture
def sample_pdf():
    """Create a sample PDF for testing."""
    # Simple PDF content
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Times-Roman >> >> >> /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000274 00000 n
trailer
<< /Size 5 /Root 1 0 R >>
startxref
365
%%EOF"""
    return io.BytesIO(pdf_content)


class TestImageProcessor:
    """Test image processing functionality."""

    @pytest.fixture
    def image_processor(self, processing_options):
        """Create image processor instance."""
        return ImageProcessor(options=processing_options)

    async def test_process_valid_image(self, image_processor, sample_image):
        """Test processing a valid image."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp.write(sample_image.getvalue())
            tmp.flush()

            try:
                result = await image_processor.process(tmp.name)

                assert result.status == ProcessingStatus.COMPLETED
                assert result.metadata is not None
                assert result.metadata.format == "PNG"
                assert result.metadata.width == 100
                assert result.metadata.height == 100
            finally:
                os.unlink(tmp.name)

    async def test_extract_image_metadata(self, image_processor):
        """Test metadata extraction from images."""
        # Create image with EXIF data
        img = Image.new('RGB', (200, 300), color='blue')

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            # Save with metadata
            img.save(tmp.name, format='JPEG', exif=b'Exif\x00\x00Test')

            try:
                metadata = await image_processor.extract_metadata(tmp.name)

                assert metadata.format in ["JPEG", "JPG"]
                assert metadata.width == 200
                assert metadata.height == 300
                assert metadata.file_size > 0
            finally:
                os.unlink(tmp.name)

    async def test_resize_image(self, image_processor):
        """Test image resizing functionality."""
        img = Image.new('RGB', (1000, 800), color='green')

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            img.save(tmp.name, format='PNG')

            try:
                options = ProcessingOptions(
                    resize_width=500,
                    resize_height=400,
                    maintain_aspect_ratio=True
                )

                result = await image_processor.process(tmp.name, options)

                assert result.status == ProcessingStatus.COMPLETED

                # Check if processed file exists and is smaller
                if result.processed_file:
                    with Image.open(result.processed_file) as processed:
                        assert processed.width <= 500
                        assert processed.height <= 400
            finally:
                os.unlink(tmp.name)
                if result.processed_file and os.path.exists(result.processed_file):
                    os.unlink(result.processed_file)

    async def test_strip_metadata(self, image_processor):
        """Test metadata stripping from images."""
        img = Image.new('RGB', (100, 100))

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            # Save with metadata
            img.save(tmp.name, format='JPEG', exif=b'Exif\x00\x00Sensitive')

            try:
                options = ProcessingOptions(strip_metadata=True)
                result = await image_processor.process(tmp.name, options)

                assert result.status == ProcessingStatus.COMPLETED

                # Verify metadata was stripped
                if result.processed_file:
                    with Image.open(result.processed_file) as processed:
                        assert not processed.getexif()
            finally:
                os.unlink(tmp.name)
                if result.processed_file and os.path.exists(result.processed_file):
                    os.unlink(result.processed_file)

    async def test_apply_watermark(self, image_processor):
        """Test watermark application."""
        img = Image.new('RGB', (500, 500), color='white')

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            img.save(tmp.name)

            try:
                options = ProcessingOptions(watermark_text="CONFIDENTIAL")
                result = await image_processor.process(tmp.name, options)

                assert result.status == ProcessingStatus.COMPLETED
                # Watermark should be applied
                assert result.processed_file is not None
            finally:
                os.unlink(tmp.name)
                if result.processed_file and os.path.exists(result.processed_file):
                    os.unlink(result.processed_file)

    async def test_image_format_conversion(self, image_processor):
        """Test converting between image formats."""
        img = Image.new('RGB', (100, 100), color='yellow')

        with tempfile.NamedTemporaryFile(suffix='.bmp', delete=False) as tmp:
            img.save(tmp.name, format='BMP')

            try:
                options = ProcessingOptions(output_format="PNG")
                result = await image_processor.process(tmp.name, options)

                assert result.status == ProcessingStatus.COMPLETED

                if result.processed_file:
                    # Check output format
                    with Image.open(result.processed_file) as processed:
                        assert processed.format == "PNG"
            finally:
                os.unlink(tmp.name)
                if result.processed_file and os.path.exists(result.processed_file):
                    os.unlink(result.processed_file)

    async def test_image_compression(self, image_processor):
        """Test image compression with quality settings."""
        img = Image.new('RGB', (1000, 1000), color='red')

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img.save(tmp.name, format='JPEG', quality=100)
            original_size = os.path.getsize(tmp.name)

            try:
                options = ProcessingOptions(compress_quality=30)
                result = await image_processor.process(tmp.name, options)

                assert result.status == ProcessingStatus.COMPLETED

                if result.processed_file:
                    compressed_size = os.path.getsize(result.processed_file)
                    # Compressed should be significantly smaller
                    assert compressed_size < original_size * 0.5
            finally:
                os.unlink(tmp.name)
                if result.processed_file and os.path.exists(result.processed_file):
                    os.unlink(result.processed_file)

    async def test_invalid_image_handling(self, image_processor):
        """Test handling of invalid image files."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp.write(b"Not an image")
            tmp.flush()

            try:
                result = await image_processor.process(tmp.name)

                assert result.status == ProcessingStatus.FAILED
                assert len(result.errors) > 0
                assert "Invalid image" in str(result.errors[0])
            finally:
                os.unlink(tmp.name)

    async def test_supported_formats(self, image_processor):
        """Test all supported image formats."""
        formats = [
            ('PNG', '.png'),
            ('JPEG', '.jpg'),
            ('GIF', '.gif'),
            ('BMP', '.bmp'),
            ('WEBP', '.webp'),
        ]

        for fmt, ext in formats:
            img = Image.new('RGB', (50, 50), color='blue')

            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                # Skip WEBP if not supported
                if fmt == 'WEBP':
                    try:
                        img.save(tmp.name, format=fmt)
                    except OSError:
                        os.unlink(tmp.name)
                        continue
                else:
                    img.save(tmp.name, format=fmt)

                try:
                    result = await image_processor.process(tmp.name)
                    assert result.status == ProcessingStatus.COMPLETED
                finally:
                    os.unlink(tmp.name)


class TestDocumentProcessor:
    """Test document processing functionality."""

    @pytest.fixture
    def document_processor(self, processing_options):
        """Create document processor instance."""
        return DocumentProcessor(options=processing_options)

    @patch('PyPDF2.PdfReader')
    async def test_process_pdf(self, mock_pdf_reader, document_processor, sample_pdf):
        """Test PDF processing."""
        # Mock PDF reader
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Test PDF content"
        mock_reader.pages = [mock_page]
        mock_reader.metadata = {'/Title': 'Test PDF', '/Author': 'Test Author'}
        mock_pdf_reader.return_value = mock_reader

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(sample_pdf.getvalue())
            tmp.flush()

            try:
                result = await document_processor.process(tmp.name)

                assert result.status == ProcessingStatus.COMPLETED
                assert result.extracted_text == "Test PDF content"
                assert result.metadata.title == "Test PDF"
                assert result.metadata.author == "Test Author"
                assert result.metadata.page_count == 1
            finally:
                os.unlink(tmp.name)

    @patch('docx.Document')
    async def test_process_docx(self, mock_document, document_processor):
        """Test Word document processing."""
        # Mock docx Document
        mock_doc = MagicMock()
        mock_para1 = MagicMock()
        mock_para1.text = "First paragraph"
        mock_para2 = MagicMock()
        mock_para2.text = "Second paragraph"
        mock_doc.paragraphs = [mock_para1, mock_para2]

        # Mock core properties
        mock_doc.core_properties = MagicMock()
        mock_doc.core_properties.title = "Test Document"
        mock_doc.core_properties.author = "Test Author"
        mock_doc.core_properties.created = datetime.now(UTC)

        mock_document.return_value = mock_doc

        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
            tmp.write(b"fake docx content")
            tmp.flush()

            try:
                result = await document_processor.process(tmp.name)

                assert result.status == ProcessingStatus.COMPLETED
                assert "First paragraph" in result.extracted_text
                assert "Second paragraph" in result.extracted_text
                assert result.metadata.title == "Test Document"
            finally:
                os.unlink(tmp.name)

    async def test_extract_text_from_txt(self, document_processor):
        """Test plain text extraction."""
        content = "This is a test document.\nWith multiple lines.\n"

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
    async def test_pdf_with_multiple_pages(self, mock_pdf_reader, document_processor):
        """Test PDF with multiple pages."""
        mock_reader = MagicMock()

        # Create multiple mock pages
        pages = []
        for i in range(10):
            mock_page = MagicMock()
            mock_page.extract_text.return_value = f"Page {i+1} content"
            pages.append(mock_page)

        mock_reader.pages = pages
        mock_pdf_reader.return_value = mock_reader

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(b"fake pdf")
            tmp.flush()

            try:
                result = await document_processor.process(tmp.name)

                assert result.status == ProcessingStatus.COMPLETED
                assert result.metadata.page_count == 10

                # Check all pages extracted
                for i in range(10):
                    assert f"Page {i+1} content" in result.extracted_text
            finally:
                os.unlink(tmp.name)

    @patch('pytesseract.image_to_string')
    @patch('pdf2image.convert_from_path')
    async def test_ocr_processing(self, mock_pdf2image, mock_tesseract, document_processor):
        """Test OCR processing for scanned documents."""
        # Mock PDF to image conversion
        mock_image = MagicMock()
        mock_pdf2image.return_value = [mock_image]

        # Mock OCR
        mock_tesseract.return_value = "OCR extracted text"

        options = ProcessingOptions(ocr_enabled=True)

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(b"fake scanned pdf")
            tmp.flush()

            try:
                result = await document_processor.process(tmp.name, options)

                assert result.status == ProcessingStatus.COMPLETED
                assert "OCR extracted text" in result.extracted_text
                mock_tesseract.assert_called()
            finally:
                os.unlink(tmp.name)

    async def test_document_validation(self, document_processor):
        """Test document validation."""
        # Test with invalid file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(b"Invalid PDF content")
            tmp.flush()

            try:
                result = await document_processor.process(tmp.name)

                assert result.status == ProcessingStatus.FAILED
                assert len(result.errors) > 0
            finally:
                os.unlink(tmp.name)

    async def test_metadata_extraction(self, document_processor):
        """Test comprehensive metadata extraction."""
        # Create a file with known size and modification time
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w') as tmp:
            tmp.write("Test content for metadata")
            tmp.flush()

            try:
                result = await document_processor.process(tmp.name)

                assert result.status == ProcessingStatus.COMPLETED
                assert result.metadata.file_size > 0
                assert result.metadata.mime_type == "text/plain"
                assert result.metadata.created_at is not None
                assert result.metadata.modified_at is not None
            finally:
                os.unlink(tmp.name)


class TestVideoProcessor:
    """Test video processing functionality."""

    @pytest.fixture
    def video_processor(self, processing_options):
        """Create video processor instance."""
        return VideoProcessor(options=processing_options)

    @patch('ffmpeg.probe')
    @patch('ffmpeg.input')
    async def test_process_video(self, mock_ffmpeg_input, mock_ffmpeg_probe, video_processor):
        """Test basic video processing."""
        # Mock ffmpeg probe output
        mock_ffmpeg_probe.return_value = {
            'format': {
                'duration': '120.5',
                'bit_rate': '1000000',
                'format_name': 'mp4'
            },
            'streams': [
                {
                    'codec_type': 'video',
                    'codec_name': 'h264',
                    'width': 1920,
                    'height': 1080,
                    'r_frame_rate': '30/1'
                },
                {
                    'codec_type': 'audio',
                    'codec_name': 'aac',
                    'sample_rate': '48000'
                }
            ]
        }

        # Mock ffmpeg operations
        mock_stream = MagicMock()
        mock_ffmpeg_input.return_value = mock_stream
        mock_stream.output.return_value = mock_stream
        mock_stream.overwrite_output.return_value = mock_stream
        mock_stream.run = AsyncMock()

        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp.write(b"fake video content")
            tmp.flush()

            try:
                result = await video_processor.process(tmp.name)

                assert result.status == ProcessingStatus.COMPLETED
                assert result.metadata.duration == 120.5
                assert result.metadata.video_codec == "h264"
                assert result.metadata.width == 1920
                assert result.metadata.height == 1080
                assert result.metadata.frame_rate == 30.0
            finally:
                os.unlink(tmp.name)

    @patch('ffmpeg.probe')
    @patch('ffmpeg.input')
    async def test_video_thumbnail_generation(self, mock_ffmpeg_input, mock_ffmpeg_probe, video_processor):
        """Test video thumbnail generation."""
        mock_ffmpeg_probe.return_value = {
            'format': {'duration': '60'},
            'streams': [{'codec_type': 'video', 'width': 1280, 'height': 720}]
        }

        mock_stream = MagicMock()
        mock_ffmpeg_input.return_value = mock_stream
        mock_stream.filter.return_value = mock_stream
        mock_stream.output.return_value = mock_stream
        mock_stream.run = AsyncMock()

        options = ProcessingOptions(generate_thumbnail=True, thumbnail_time=10)

        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp.write(b"fake video")
            tmp.flush()

            try:
                result = await video_processor.process(tmp.name, options)

                assert result.status == ProcessingStatus.COMPLETED
                # Thumbnail generation should be called
                mock_stream.filter.assert_called()
            finally:
                os.unlink(tmp.name)

    @patch('ffmpeg.probe')
    @patch('ffmpeg.input')
    async def test_video_transcoding(self, mock_ffmpeg_input, mock_ffmpeg_probe, video_processor):
        """Test video transcoding to different formats."""
        mock_ffmpeg_probe.return_value = {
            'format': {'format_name': 'avi'},
            'streams': [{'codec_type': 'video', 'codec_name': 'mpeg4'}]
        }

        mock_stream = MagicMock()
        mock_ffmpeg_input.return_value = mock_stream
        mock_stream.output.return_value = mock_stream
        mock_stream.overwrite_output.return_value = mock_stream
        mock_stream.run = AsyncMock()

        options = ProcessingOptions(
            transcode=True,
            output_format="mp4",
            video_codec="h264"
        )

        with tempfile.NamedTemporaryFile(suffix='.avi', delete=False) as tmp:
            tmp.write(b"fake avi video")
            tmp.flush()

            try:
                result = await video_processor.process(tmp.name, options)

                assert result.status == ProcessingStatus.COMPLETED
                # Verify transcoding was attempted
                mock_stream.output.assert_called()
            finally:
                os.unlink(tmp.name)


class TestSpreadsheetProcessor:
    """Test spreadsheet processing functionality."""

    @pytest.fixture
    def spreadsheet_processor(self, processing_options):
        """Create spreadsheet processor instance."""
        return SpreadsheetProcessor(options=processing_options)

    @patch('openpyxl.load_workbook')
    async def test_process_excel(self, mock_load_workbook, spreadsheet_processor):
        """Test Excel file processing."""
        # Mock workbook
        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_ws.title = "Sheet1"
        mock_ws.max_row = 10
        mock_ws.max_column = 5

        # Mock cell iteration
        mock_ws.iter_rows.return_value = [
            [MagicMock(value=f"Cell{i}{j}") for j in range(5)]
            for i in range(10)
        ]

        mock_wb.worksheets = [mock_ws]
        mock_wb.sheetnames = ["Sheet1"]
        mock_load_workbook.return_value = mock_wb

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            tmp.write(b"fake excel content")
            tmp.flush()

            try:
                result = await spreadsheet_processor.process(tmp.name)

                assert result.status == ProcessingStatus.COMPLETED
                assert result.metadata.sheet_count == 1
                assert result.metadata.total_rows == 10
                assert result.metadata.total_columns == 5
                assert "Sheet1" in result.extracted_data
            finally:
                os.unlink(tmp.name)

    @patch('pandas.read_csv')
    async def test_process_csv(self, mock_read_csv, spreadsheet_processor):
        """Test CSV file processing."""
        # Mock pandas DataFrame
        mock_df = MagicMock()
        mock_df.shape = (100, 10)
        mock_df.columns = ["col1", "col2", "col3"]
        mock_df.dtypes = {"col1": "int64", "col2": "float64", "col3": "object"}
        mock_df.to_dict.return_value = {
            "col1": [1, 2, 3],
            "col2": [1.1, 2.2, 3.3],
            "col3": ["a", "b", "c"]
        }
        mock_read_csv.return_value = mock_df

        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w') as tmp:
            tmp.write("col1,col2,col3\n1,1.1,a\n2,2.2,b\n3,3.3,c\n")
            tmp.flush()

            try:
                result = await spreadsheet_processor.process(tmp.name)

                assert result.status == ProcessingStatus.COMPLETED
                assert result.metadata.total_rows == 100
                assert result.metadata.total_columns == 10
            finally:
                os.unlink(tmp.name)

    @patch('openpyxl.load_workbook')
    async def test_formula_extraction(self, mock_load_workbook, spreadsheet_processor):
        """Test extraction of formulas from spreadsheets."""
        mock_wb = MagicMock()
        mock_ws = MagicMock()

        # Create cells with formulas
        cell_with_formula = MagicMock()
        cell_with_formula.value = "=SUM(A1:A10)"
        cell_with_formula.data_type = "f"  # Formula type

        cell_with_value = MagicMock()
        cell_with_value.value = 100
        cell_with_value.data_type = "n"  # Number type

        mock_ws.iter_rows.return_value = [
            [cell_with_formula, cell_with_value]
        ]

        mock_wb.worksheets = [mock_ws]
        mock_load_workbook.return_value = mock_wb

        options = ProcessingOptions(extract_formulas=True)

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            tmp.write(b"fake excel")
            tmp.flush()

            try:
                result = await spreadsheet_processor.process(tmp.name, options)

                assert result.status == ProcessingStatus.COMPLETED
                assert result.formulas is not None
                assert "SUM(A1:A10)" in str(result.formulas)
            finally:
                os.unlink(tmp.name)


class TestVirusScanIntegration:
    """Test virus scanning integration."""

    @patch('requests.post')
    async def test_virus_scan_clean_file(self, mock_post, processing_options):
        """Test virus scanning with clean file."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "scan_result": "clean",
            "threats": []
        }
        mock_post.return_value = mock_response

        processor = DocumentProcessor(options=processing_options)

        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w') as tmp:
            tmp.write("Clean content")
            tmp.flush()

            try:
                result = await processor.scan_for_viruses(tmp.name)
                assert result["scan_result"] == "clean"
            finally:
                os.unlink(tmp.name)

    @patch('requests.post')
    async def test_virus_scan_infected_file(self, mock_post, processing_options):
        """Test virus scanning with infected file."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "scan_result": "infected",
            "threats": ["Trojan.Generic"]
        }
        mock_post.return_value = mock_response

        processor = DocumentProcessor(options=processing_options)

        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w') as tmp:
            tmp.write("EICAR test string")
            tmp.flush()

            try:
                result = await processor.scan_for_viruses(tmp.name)
                assert result["scan_result"] == "infected"
                assert len(result["threats"]) > 0
            finally:
                os.unlink(tmp.name)


class TestMetadataExtraction:
    """Test metadata extraction from various file types."""

    async def test_extract_exif_metadata(self):
        """Test EXIF metadata extraction from images."""
        processor = ImageProcessor()

        # Create image with EXIF
        img = Image.new('RGB', (100, 100))
        exif_data = img.getexif()
        exif_data[0x010F] = "Test Camera"  # Make
        exif_data[0x0110] = "Model X"      # Model

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img.save(tmp.name, exif=exif_data)

            try:
                metadata = await processor.extract_metadata(tmp.name)
                assert metadata.camera_make == "Test Camera"
                assert metadata.camera_model == "Model X"
            finally:
                os.unlink(tmp.name)

    @patch('PyPDF2.PdfReader')
    async def test_extract_pdf_metadata(self, mock_pdf_reader):
        """Test PDF metadata extraction."""
        processor = DocumentProcessor()

        mock_reader = MagicMock()
        mock_reader.metadata = {
            '/Title': 'Test Document',
            '/Author': 'John Doe',
            '/Subject': 'Testing',
            '/Keywords': 'test, pdf, metadata',
            '/CreationDate': "D:20240101120000+00'00'"
        }
        mock_pdf_reader.return_value = mock_reader

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(b"fake pdf")
            tmp.flush()

            try:
                metadata = await processor.extract_metadata(tmp.name)
                assert metadata.title == "Test Document"
                assert metadata.author == "John Doe"
                assert metadata.keywords == "test, pdf, metadata"
            finally:
                os.unlink(tmp.name)

    async def test_extract_file_system_metadata(self):
        """Test file system metadata extraction."""
        processor = FileProcessor()

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"Test content")
            tmp.flush()

            try:
                metadata = await processor.extract_basic_metadata(tmp.name)

                assert metadata.file_name == os.path.basename(tmp.name)
                assert metadata.file_size == 12  # "Test content" = 12 bytes
                assert metadata.created_at is not None
                assert metadata.modified_at is not None
            finally:
                os.unlink(tmp.name)


class TestPerformanceOptimization:
    """Test performance optimizations for file processing."""

    @pytest.mark.slow
    async def test_large_file_streaming(self, processing_options):
        """Test streaming processing of large files."""
        processor = DocumentProcessor(options=processing_options)

        # Create a large file (100MB)
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w') as tmp:
            # Write 100MB of text
            chunk = "A" * 1024  # 1KB
            for _ in range(100 * 1024):  # 100K iterations = 100MB
                tmp.write(chunk)
            tmp.flush()

            try:
                import time
                start = time.time()

                result = await processor.process_stream(tmp.name)

                elapsed = time.time() - start

                assert result.status == ProcessingStatus.COMPLETED
                # Should process in reasonable time (< 10 seconds)
                assert elapsed < 10
            finally:
                os.unlink(tmp.name)

    async def test_parallel_file_processing(self):
        """Test parallel processing of multiple files."""
        processor = ImageProcessor()

        # Create multiple test images
        temp_files = []
        for i in range(10):
            img = Image.new('RGB', (100, 100), color='red')
            tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            img.save(tmp.name)
            temp_files.append(tmp.name)

        try:
            # Process files in parallel
            tasks = [processor.process(f) for f in temp_files]
            results = await asyncio.gather(*tasks)

            # All should complete successfully
            for result in results:
                assert result.status == ProcessingStatus.COMPLETED
        finally:
            for f in temp_files:
                os.unlink(f)

    async def test_memory_efficient_processing(self):
        """Test memory-efficient file processing."""
        import tracemalloc

        processor = DocumentProcessor()

        # Start memory tracking
        tracemalloc.start()

        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w') as tmp:
            # Create 10MB file
            tmp.write("X" * (10 * 1024 * 1024))
            tmp.flush()

            try:
                snapshot1 = tracemalloc.take_snapshot()

                # Process file
                result = await processor.process_stream(tmp.name)

                snapshot2 = tracemalloc.take_snapshot()
                top_stats = snapshot2.compare_to(snapshot1, 'lineno')

                # Memory increase should be minimal (< 50MB)
                total_diff = sum(stat.size_diff for stat in top_stats)
                assert total_diff < 50 * 1024 * 1024

                assert result.status == ProcessingStatus.COMPLETED
            finally:
                os.unlink(tmp.name)
                tracemalloc.stop()


class TestErrorHandling:
    """Test error handling in file processing."""

    async def test_file_not_found(self, processing_options):
        """Test handling of non-existent files."""
        processor = DocumentProcessor(options=processing_options)

        result = await processor.process("/non/existent/file.txt")

        assert result.status == ProcessingStatus.FAILED
        assert len(result.errors) > 0
        assert "not found" in str(result.errors[0]).lower()

    async def test_permission_denied(self, processing_options):
        """Test handling of permission errors."""
        processor = ImageProcessor(options=processing_options)

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp.write(b"test")
            tmp.flush()

            # Remove read permissions
            os.chmod(tmp.name, 0o000)

            try:
                result = await processor.process(tmp.name)

                assert result.status == ProcessingStatus.FAILED
                assert len(result.errors) > 0
            finally:
                os.chmod(tmp.name, 0o644)  # Restore permissions
                os.unlink(tmp.name)

    async def test_corrupted_file_handling(self, processing_options):
        """Test handling of corrupted files."""
        processor = DocumentProcessor(options=processing_options)

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            # Write corrupted PDF header
            tmp.write(b"%PDF-1.4\nCorrupted content")
            tmp.flush()

            try:
                result = await processor.process(tmp.name)

                assert result.status == ProcessingStatus.FAILED
                assert len(result.errors) > 0
            finally:
                os.unlink(tmp.name)

    async def test_timeout_handling(self, processing_options):
        """Test handling of processing timeouts."""
        options = ProcessingOptions(
            timeout_seconds=1,  # 1 second timeout
            ocr_enabled=True    # OCR is slow
        )
        processor = DocumentProcessor(options=options)

        with patch('pytesseract.image_to_string') as mock_ocr:
            # Make OCR take too long
            async def slow_ocr(*args):
                await asyncio.sleep(5)
                return "text"

            mock_ocr.side_effect = slow_ocr

            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                tmp.write(b"fake pdf")
                tmp.flush()

                try:
                    result = await processor.process(tmp.name)

                    assert result.status == ProcessingStatus.FAILED
                    assert "timeout" in str(result.errors[0]).lower()
                finally:
                    os.unlink(tmp.name)
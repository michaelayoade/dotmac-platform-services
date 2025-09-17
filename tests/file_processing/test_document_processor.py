"""
Comprehensive tests for document processing functionality.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dotmac.platform.file_processing.base import (
    ProcessingOptions,
    ProcessingResult,
    ProcessingStatus,
)
from dotmac.platform.file_processing.processors import DocumentProcessor


class TestDocumentProcessor:
    """Test document processing functionality."""

    @pytest.fixture
    def document_processor(self):
        """Create document processor instance."""
        return DocumentProcessor()

    @pytest.fixture
    def processing_options(self):
        """Create processing options for testing."""
        return ProcessingOptions(
            extract_text=True,
            extract_images=False,
            split_pages=False,
            convert_to_pdf=False,
        )

    @pytest.fixture
    def sample_pdf_path(self):
        """Create a temporary test PDF file."""
        # Create a mock PDF file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            # Write minimal PDF structure
            f.write(b"%PDF-1.4\n")
            f.write(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
            f.write(b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n")
            f.write(b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >> endobj\n")
            f.write(b"xref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n")
            f.write(b"0000000053 00000 n\n0000000102 00000 n\n")
            f.write(b"trailer << /Size 4 /Root 1 0 R >>\nstartxref\n149\n%%EOF")
            temp_path = f.name

        yield temp_path

        # Cleanup
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass

    @pytest.fixture
    def sample_text_file(self):
        """Create a temporary text file that looks like a document."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".docx", delete=False) as f:
            f.write("This is a mock document content")
            temp_path = f.name

        yield temp_path

        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass

    @pytest.mark.unit
    def test_document_processor_initialization(self):
        """Test document processor initialization."""
        processor = DocumentProcessor()
        assert processor.options is not None
        assert isinstance(processor.options, ProcessingOptions)

        # Test with custom options
        options = ProcessingOptions(extract_text=False)
        processor = DocumentProcessor(options)
        assert processor.options.extract_text is False

    @pytest.mark.unit
    def test_supported_formats(self):
        """Test supported document formats."""
        processor = DocumentProcessor()

        supported = processor.SUPPORTED_FORMATS

        assert ".pdf" in supported
        assert ".doc" in supported
        assert ".docx" in supported
        assert ".xls" in supported
        assert ".xlsx" in supported
        assert ".ppt" in supported
        assert ".pptx" in supported
        assert ".odt" in supported
        assert ".ods" in supported
        assert ".odp" in supported

        # Test case sensitivity
        assert len(supported) == len({f.lower() for f in supported})

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_valid_pdf(self, document_processor, sample_pdf_path):
        """Test validation of valid PDF file."""
        is_valid = await document_processor.validate(sample_pdf_path)
        assert is_valid is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_valid_docx(self, document_processor, sample_text_file):
        """Test validation of valid DOCX file."""
        is_valid = await document_processor.validate(sample_text_file)
        assert is_valid is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_nonexistent_file(self, document_processor):
        """Test validation of non-existent file."""
        is_valid = await document_processor.validate("/nonexistent/file.pdf")
        assert is_valid is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_unsupported_extension(self, document_processor):
        """Test validation of unsupported file extension."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            temp_path = f.name

        try:
            is_valid = await document_processor.validate(temp_path)
            assert is_valid is False
        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_metadata_pdf(self, document_processor):
        """Test PDF metadata extraction."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            # Mock PyPDF2.PdfReader
            with patch("PyPDF2.PdfReader") as mock_reader:
                mock_reader_instance = Mock()
                mock_reader_instance.pages = [Mock(), Mock()]  # 2 pages
                mock_reader_instance.metadata = {
                    "/Title": "Test Document",
                    "/Author": "Test Author",
                    "/Subject": "Test Subject",
                }
                mock_reader.return_value = mock_reader_instance

                with patch("builtins.open", create=True):
                    with patch(
                        "dotmac.platform.file_processing.base.FileMetadata.from_file"
                    ) as mock_from_file:
                        # Create mock base metadata
                        mock_metadata = Mock()
                        mock_metadata.extra_metadata = {}
                        mock_from_file.return_value = mock_metadata

                        metadata = await document_processor.extract_metadata(temp_path)

                        assert metadata.pages == 2
                        assert metadata.extra_metadata["title"] == "Test Document"
                        assert metadata.extra_metadata["author"] == "Test Author"
                        assert metadata.extra_metadata["subject"] == "Test Subject"

        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_metadata_docx(self, document_processor):
        """Test DOCX metadata extraction."""
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            temp_path = f.name

        try:
            # Mock docx.Document
            with patch("docx.Document") as mock_doc:
                mock_doc_instance = Mock()
                mock_doc_instance.element.body = [Mock(), Mock(), Mock()]  # 3 elements
                mock_doc_instance.paragraphs = [Mock() for _ in range(5)]  # 5 paragraphs
                mock_doc.return_value = mock_doc_instance

                with patch(
                    "dotmac.platform.file_processing.base.FileMetadata.from_file"
                ) as mock_from_file:
                    mock_metadata = Mock()
                    mock_metadata.extra_metadata = {}
                    mock_from_file.return_value = mock_metadata

                    metadata = await document_processor.extract_metadata(temp_path)

                    assert metadata.pages == 3
                    assert metadata.extra_metadata["paragraphs"] == 5

        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_metadata_xlsx(self, document_processor):
        """Test XLSX metadata extraction."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            temp_path = f.name

        try:
            # Mock openpyxl.load_workbook
            with patch("openpyxl.load_workbook") as mock_workbook:
                mock_wb = Mock()
                mock_wb.sheetnames = ["Sheet1", "Sheet2", "Sheet3"]
                mock_workbook.return_value = mock_wb

                with patch(
                    "dotmac.platform.file_processing.base.FileMetadata.from_file"
                ) as mock_from_file:
                    mock_metadata = Mock()
                    mock_metadata.extra_metadata = {}
                    mock_from_file.return_value = mock_metadata

                    metadata = await document_processor.extract_metadata(temp_path)

                    assert metadata.pages == 3
                    assert metadata.extra_metadata["sheets"] == ["Sheet1", "Sheet2", "Sheet3"]

        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_metadata_error_handling(self, document_processor):
        """Test metadata extraction error handling."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            # Mock PyPDF2.PdfReader to raise an exception
            with patch("PyPDF2.PdfReader", side_effect=Exception("PDF read error")):
                with patch("builtins.open", create=True):
                    with patch(
                        "dotmac.platform.file_processing.base.FileMetadata.from_file"
                    ) as mock_from_file:
                        mock_metadata = Mock()
                        mock_metadata.extra_metadata = {}
                        mock_from_file.return_value = mock_metadata

                        metadata = await document_processor.extract_metadata(temp_path)

                        assert "metadata_error" in metadata.extra_metadata
                        assert "PDF read error" in metadata.extra_metadata["metadata_error"]

        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_text_pdf(self, document_processor):
        """Test PDF text extraction."""
        test_text = "This is test content from PDF"

        with patch("PyPDF2.PdfReader") as mock_reader:
            mock_page = Mock()
            mock_page.extract_text.return_value = test_text

            mock_reader_instance = Mock()
            mock_reader_instance.pages = [mock_page]
            mock_reader.return_value = mock_reader_instance

            with patch("builtins.open", create=True):
                extracted_text = await document_processor._extract_text("/fake/path.pdf")

            assert extracted_text == test_text

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_text_docx(self, document_processor):
        """Test DOCX text extraction."""
        with patch("docx.Document") as mock_doc:
            mock_para1 = Mock()
            mock_para1.text = "First paragraph"
            mock_para2 = Mock()
            mock_para2.text = "Second paragraph"

            mock_doc_instance = Mock()
            mock_doc_instance.paragraphs = [mock_para1, mock_para2]
            mock_doc.return_value = mock_doc_instance

            extracted_text = await document_processor._extract_text("/fake/path.docx")

            expected_text = "First paragraph\nSecond paragraph"
            assert extracted_text == expected_text

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_text_xlsx(self, document_processor):
        """Test XLSX text extraction."""
        with patch("openpyxl.load_workbook") as mock_workbook:
            # Mock worksheet
            mock_sheet = Mock()
            mock_sheet.iter_rows.return_value = [
                ("Header1", "Header2", "Header3"),
                ("Value1", "Value2", "Value3"),
                ("Data1", "Data2", None),
            ]

            mock_wb = Mock()
            mock_wb.sheetnames = ["TestSheet"]
            mock_wb.__getitem__.return_value = mock_sheet
            mock_workbook.return_value = mock_wb

            extracted_text = await document_processor._extract_text("/fake/path.xlsx")

            assert "Sheet: TestSheet" in extracted_text
            assert "Header1\tHeader2\tHeader3" in extracted_text
            assert "Value1\tValue2\tValue3" in extracted_text
            assert "Data1\tData2\t" in extracted_text

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_text_error_handling(self, document_processor):
        """Test text extraction error handling."""
        with patch("PyPDF2.PdfReader", side_effect=Exception("PDF read error")):
            with patch("builtins.open", create=True):
                extracted_text = await document_processor._extract_text("/fake/path.pdf")

            assert "Text extraction failed: PDF read error" in extracted_text

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_basic_pdf(self, document_processor):
        """Test basic PDF processing."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            options = ProcessingOptions(extract_text=True, split_pages=False)

            # Mock validation and metadata extraction
            with patch.object(document_processor, "validate", return_value=True):
                with patch.object(document_processor, "extract_metadata") as mock_metadata:
                    mock_meta = Mock()
                    mock_meta.pages = 3
                    mock_metadata.return_value = mock_meta

                    with patch.object(
                        document_processor, "_extract_text", return_value="Test text"
                    ):
                        result = await document_processor.process(temp_path, options)

                        assert result.status == ProcessingStatus.COMPLETED
                        assert result.success is True
                        assert result.original_file == temp_path
                        assert result.extracted_text == "Test text"
                        assert result.metadata is not None
                        assert result.processing_time > 0

        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_pdf_with_page_splitting(self, document_processor):
        """Test PDF processing with page splitting."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            options = ProcessingOptions(split_pages=True, extract_text=False)

            # Mock PyPDF2 components for page splitting
            with patch("PyPDF2.PdfReader") as mock_reader:
                with patch("PyPDF2.PdfWriter") as mock_writer:
                    # Mock pages
                    mock_pages = [Mock(), Mock(), Mock()]
                    mock_reader_instance = Mock()
                    mock_reader_instance.pages = mock_pages
                    mock_reader.return_value = mock_reader_instance

                    mock_writer_instance = Mock()
                    mock_writer.return_value = mock_writer_instance

                    with patch.object(document_processor, "validate", return_value=True):
                        with patch.object(document_processor, "extract_metadata") as mock_metadata:
                            mock_meta = Mock()
                            mock_meta.pages = 3
                            mock_metadata.return_value = mock_meta

                            with patch("builtins.open", create=True):
                                result = await document_processor.process(temp_path, options)

                                assert result.status == ProcessingStatus.COMPLETED
                                assert result.success is True
                                assert len(result.processed_files) == 3  # One per page

        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_word_document(self, document_processor):
        """Test Word document processing."""
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            temp_path = f.name

        try:
            options = ProcessingOptions(extract_text=True, convert_to_pdf=True)

            with patch.object(document_processor, "validate", return_value=True):
                with patch.object(document_processor, "extract_metadata") as mock_metadata:
                    mock_meta = Mock()
                    mock_meta.pages = 1
                    mock_metadata.return_value = mock_meta

                    with patch.object(
                        document_processor, "_extract_text", return_value="Word text"
                    ):
                        result = await document_processor.process(temp_path, options)

                        assert result.status == ProcessingStatus.COMPLETED
                        assert result.success is True
                        assert result.extracted_text == "Word text"
                        # PDF conversion warning should be added
                        assert len(result.warnings) > 0
                        assert "Word to PDF conversion not yet implemented" in result.warnings

        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_excel_document(self, document_processor):
        """Test Excel document processing."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            temp_path = f.name

        try:
            options = ProcessingOptions(extract_text=True, convert_to_pdf=True)

            with patch.object(document_processor, "validate", return_value=True):
                with patch.object(document_processor, "extract_metadata") as mock_metadata:
                    mock_meta = Mock()
                    mock_meta.pages = 2
                    mock_metadata.return_value = mock_meta

                    with patch.object(
                        document_processor, "_extract_text", return_value="Excel data"
                    ):
                        result = await document_processor.process(temp_path, options)

                        assert result.status == ProcessingStatus.COMPLETED
                        assert result.success is True
                        assert result.extracted_text == "Excel data"
                        # PDF conversion warning should be added
                        assert len(result.warnings) > 0
                        assert "Excel to PDF conversion not yet implemented" in result.warnings

        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_invalid_document(self, document_processor):
        """Test processing of invalid document."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"This is not a valid PDF")
            temp_path = f.name

        try:
            with patch.object(document_processor, "validate", return_value=False):
                result = await document_processor.process(temp_path)

                assert result.status == ProcessingStatus.FAILED
                assert result.success is False
                assert len(result.errors) > 0

        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_nonexistent_document(self, document_processor):
        """Test processing of non-existent document."""
        result = await document_processor.process("/nonexistent/file.pdf")

        assert result.status == ProcessingStatus.FAILED
        assert result.success is False
        assert len(result.errors) > 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_with_exception_handling(self, document_processor):
        """Test exception handling during processing."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            # Mock validate to raise an exception
            with patch.object(
                document_processor, "validate", side_effect=Exception("Mock processing error")
            ):
                result = await document_processor.process(temp_path)

                assert result.status == ProcessingStatus.FAILED
                assert result.success is False
                assert len(result.errors) > 0
                assert "Mock processing error" in result.errors[0]

        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    @pytest.mark.unit
    def test_get_page_output_path_default(self, document_processor):
        """Test page output path generation with defaults."""
        original_path = "/path/to/document.pdf"
        options = ProcessingOptions()

        output_path = document_processor._get_page_output_path(original_path, 3, options)

        assert "document_page_3.pdf" in output_path
        assert "/path/to/" in output_path

    @pytest.mark.unit
    def test_get_page_output_path_custom_directory(self, document_processor):
        """Test page output path generation with custom directory."""
        original_path = "/path/to/document.pdf"
        options = ProcessingOptions(output_directory="/custom/output")

        with patch("os.makedirs"):
            output_path = document_processor._get_page_output_path(original_path, 5, options)

        assert "/custom/output/" in output_path
        assert "document_page_5.pdf" in output_path

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_document_processing_workflow(self, document_processor):
        """Test complete document processing workflow."""
        # Create a mock PDF with multiple pages
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            # Create comprehensive processing options
            options = ProcessingOptions(extract_text=True, split_pages=True, extract_images=False)

            # Mock all the dependencies for a complete workflow
            with patch.object(document_processor, "validate", return_value=True):
                with patch.object(document_processor, "extract_metadata") as mock_metadata:
                    mock_meta = Mock()
                    mock_meta.pages = 3
                    mock_meta.extra_metadata = {"title": "Test Document"}
                    mock_metadata.return_value = mock_meta

                    with patch.object(
                        document_processor, "_extract_text", return_value="Extracted document text"
                    ):
                        # Mock PDF page splitting
                        with patch("PyPDF2.PdfReader") as mock_reader:
                            with patch("PyPDF2.PdfWriter") as mock_writer:
                                mock_pages = [Mock(), Mock(), Mock()]
                                mock_reader_instance = Mock()
                                mock_reader_instance.pages = mock_pages
                                mock_reader.return_value = mock_reader_instance

                                mock_writer_instance = Mock()
                                mock_writer.return_value = mock_writer_instance

                                with patch("builtins.open", create=True):
                                    result = await document_processor.process(temp_path, options)

                                    # Verify results
                                    assert result.success is True
                                    assert result.status == ProcessingStatus.COMPLETED
                                    assert result.metadata is not None
                                    assert result.metadata.pages == 3
                                    assert result.extracted_text == "Extracted document text"
                                    assert len(result.processed_files) == 3  # One per page
                                    assert result.processing_time > 0
                                    assert len(result.errors) == 0

        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_large_document_processing(self, document_processor):
        """Test processing of large documents."""
        # This test would be more realistic with actual large files
        # For now, we simulate processing time and memory usage
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            options = ProcessingOptions(extract_text=True, split_pages=False)

            # Mock a large document with many pages
            with patch.object(document_processor, "validate", return_value=True):
                with patch.object(document_processor, "extract_metadata") as mock_metadata:
                    mock_meta = Mock()
                    mock_meta.pages = 100  # Large document
                    mock_metadata.return_value = mock_meta

                    with patch.object(document_processor, "_extract_text") as mock_extract:
                        # Simulate large text extraction
                        large_text = "This is a large document. " * 1000
                        mock_extract.return_value = large_text

                        result = await document_processor.process(temp_path, options)

                        assert result.success is True
                        assert len(result.extracted_text) > 10000
                        assert result.processing_time > 0

        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

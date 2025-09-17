"""
Comprehensive tests for data import functionality.
"""

import csv
import io
import json
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from dotmac.platform.data_transfer.base import (
    DataBatch,
    DataFormat,
    DataRecord,
    FormatError,
    ImportError,
    TransferConfig,
    TransferStatus,
)
from dotmac.platform.data_transfer.importers import (
    CSVImporter,
    ExcelImporter,
    ImportOptions,
    JSONImporter,
    XMLImporter,
    create_importer,
    detect_format,
)


class TestImportOptions:
    """Test import options configuration."""

    @pytest.mark.unit
    def test_import_options_defaults(self):
        """Test default import options."""
        options = ImportOptions()

        # CSV options
        assert options.delimiter == ","
        assert options.quotechar == '"'
        assert options.escapechar is None
        assert options.skip_blank_lines is True
        assert options.header_row == 0

        # Excel options
        assert options.sheet_name is None
        assert options.skip_rows == 0

        # JSON options
        assert options.json_lines is False
        assert options.json_path is None

        # XML options
        assert options.xml_root_element is None
        assert options.xml_record_element is None

        # General options
        assert options.sample_size == 1000
        assert options.type_inference is True
        assert len(options.date_formats) > 0

    @pytest.mark.unit
    def test_import_options_custom_values(self):
        """Test custom import options."""
        options = ImportOptions(
            delimiter=";",
            quotechar="'",
            sheet_name="Sheet2",
            json_lines=True,
            type_inference=False,
            sample_size=5000,
        )

        assert options.delimiter == ";"
        assert options.quotechar == "'"
        assert options.sheet_name == "Sheet2"
        assert options.json_lines is True
        assert options.type_inference is False
        assert options.sample_size == 5000

    @pytest.mark.unit
    def test_import_options_delimiter_validation(self):
        """Test delimiter validation."""
        with pytest.raises(ValueError, match="Delimiter must be a single character"):
            ImportOptions(delimiter=";;")

        with pytest.raises(ValueError, match="Delimiter must be a single character"):
            ImportOptions(delimiter="")

        # Single character should work
        options = ImportOptions(delimiter="|")
        assert options.delimiter == "|"


class TestCSVImporter:
    """Test CSV import functionality."""

    @pytest.fixture
    def csv_importer(self):
        """Create CSV importer instance."""
        return CSVImporter()

    @pytest.fixture
    def csv_data(self):
        """Sample CSV data for testing."""
        return """name,age,city
John,25,New York
Jane,30,London
Bob,35,Paris"""

    @pytest.fixture
    def csv_file_path(self, csv_data):
        """Create temporary CSV file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_data)
            temp_path = Path(f.name)

        yield temp_path

        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass

    @pytest.mark.unit
    def test_csv_importer_initialization(self):
        """Test CSV importer initialization."""
        importer = CSVImporter()
        assert importer.options is not None
        assert isinstance(importer.options, ImportOptions)

        # Test with custom config and options
        config = TransferConfig(batch_size=500)
        options = ImportOptions(delimiter=";")
        importer = CSVImporter(config, options)
        assert importer.config.batch_size == 500
        assert importer.options.delimiter == ";"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_csv_import_from_stream_basic(self, csv_importer, csv_data):
        """Test basic CSV import from stream."""
        stream = io.StringIO(csv_data)

        batches = []
        async for batch in csv_importer.import_from_stream(stream):
            batches.append(batch)

        assert len(batches) == 1
        batch = batches[0]
        assert isinstance(batch, DataBatch)
        assert len(batch.records) == 3

        # Check first record
        record = batch.records[0]
        assert record.data["name"] == "John"
        assert record.data["age"] == 25  # Should be converted to int
        assert record.data["city"] == "New York"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_csv_import_from_file(self, csv_importer, csv_file_path):
        """Test CSV import from file."""
        batches = []
        async for batch in csv_importer.import_from_file(csv_file_path):
            batches.append(batch)

        assert len(batches) == 1
        assert len(batches[0].records) == 3

        # Verify data integrity
        record = batches[0].records[1]
        assert record.data["name"] == "Jane"
        assert record.data["age"] == 30
        assert record.data["city"] == "London"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_csv_import_with_custom_delimiter(self, csv_file_path):
        """Test CSV import with custom delimiter."""
        # Create CSV with semicolon delimiter
        csv_data = "name;age;city\nAlice;28;Berlin\nCharlie;32;Tokyo"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_data)
            temp_path = Path(f.name)

        try:
            options = ImportOptions(delimiter=";")
            importer = CSVImporter(options=options)

            batches = []
            async for batch in importer.import_from_file(temp_path):
                batches.append(batch)

            assert len(batches) == 1
            assert len(batches[0].records) == 2
            assert batches[0].records[0].data["name"] == "Alice"

        finally:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_csv_import_with_type_inference_disabled(self, csv_importer):
        """Test CSV import with type inference disabled."""
        csv_data = "id,score,active\n123,99.5,true\n456,87.2,false"

        options = ImportOptions(type_inference=False)
        importer = CSVImporter(options=options)

        stream = io.StringIO(csv_data)
        batches = []
        async for batch in importer.import_from_stream(stream):
            batches.append(batch)

        record = batches[0].records[0]
        # All values should remain as strings
        assert record.data["id"] == "123"
        assert record.data["score"] == "99.5"
        assert record.data["active"] == "true"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_csv_import_skip_blank_lines(self, csv_importer):
        """Test CSV import with blank line handling."""
        csv_data = """name,age
John,25

Jane,30
"""

        options = ImportOptions(skip_blank_lines=True)
        importer = CSVImporter(options=options)

        stream = io.StringIO(csv_data)
        batches = []
        async for batch in importer.import_from_stream(stream):
            batches.append(batch)

        # Should skip the blank line
        assert len(batches[0].records) == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_csv_import_error_handling(self, csv_importer):
        """Test CSV import error handling."""
        # Test with non-existent file
        with pytest.raises(ImportError):
            async for batch in csv_importer.import_from_file(Path("/nonexistent/file.csv")):
                pass

    @pytest.mark.unit
    def test_csv_type_inference(self, csv_importer):
        """Test CSV data type inference."""
        test_cases = {
            "123": 123,
            "99.5": 99.5,
            "true": True,
            "false": False,
            "yes": True,
            "no": False,
            "": None,
            "2023-01-01": datetime(2023, 1, 1),  # Converted to datetime
            "regular text": "regular text",
        }

        for input_val, expected in test_cases.items():
            data = {"test": input_val}
            result = csv_importer._infer_types(data)
            if expected is None:
                assert result["test"] is None
            else:
                assert result["test"] == expected or isinstance(result["test"], type(expected))


class TestJSONImporter:
    """Test JSON import functionality."""

    @pytest.fixture
    def json_importer(self):
        """Create JSON importer instance."""
        return JSONImporter()

    @pytest.fixture
    def json_data(self):
        """Sample JSON data for testing."""
        return [
            {"id": 1, "name": "John", "age": 25},
            {"id": 2, "name": "Jane", "age": 30},
            {"id": 3, "name": "Bob", "age": 35},
        ]

    @pytest.fixture
    def json_file_path(self, json_data):
        """Create temporary JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(json_data, f)
            temp_path = Path(f.name)

        yield temp_path

        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_json_import_from_stream_array(self, json_importer, json_data):
        """Test JSON import from stream with array data."""
        stream = io.StringIO(json.dumps(json_data))

        batches = []
        async for batch in json_importer.import_from_stream(stream):
            batches.append(batch)

        assert len(batches) == 1
        batch = batches[0]
        assert len(batch.records) == 3

        record = batch.records[0]
        assert record.data["id"] == 1
        assert record.data["name"] == "John"
        assert record.data["age"] == 25

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_json_import_from_stream_single_object(self, json_importer):
        """Test JSON import from stream with single object."""
        data = {"id": 1, "name": "John", "age": 25}
        stream = io.StringIO(json.dumps(data))

        batches = []
        async for batch in json_importer.import_from_stream(stream):
            batches.append(batch)

        assert len(batches) == 1
        assert len(batches[0].records) == 1
        assert batches[0].records[0].data == data

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_json_import_jsonl_format(self, json_importer):
        """Test JSON Lines format import."""
        jsonl_data = """{"id": 1, "name": "John"}
{"id": 2, "name": "Jane"}
{"id": 3, "name": "Bob"}"""

        options = ImportOptions(json_lines=True)
        importer = JSONImporter(options=options)

        stream = io.StringIO(jsonl_data)
        batches = []
        async for batch in importer.import_from_stream(stream):
            batches.append(batch)

        assert len(batches) == 1
        assert len(batches[0].records) == 3
        assert batches[0].records[1].data["name"] == "Jane"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_json_import_with_json_path(self, json_importer):
        """Test JSON import with JSONPath extraction."""
        nested_data = {"users": [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]}

        options = ImportOptions(json_path="users")
        importer = JSONImporter(options=options)

        stream = io.StringIO(json.dumps(nested_data))
        batches = []
        async for batch in importer.import_from_stream(stream):
            batches.append(batch)

        assert len(batches) == 1
        assert len(batches[0].records) == 2
        assert batches[0].records[0].data["name"] == "John"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_json_import_invalid_json(self, json_importer):
        """Test JSON import with invalid JSON."""
        invalid_json = '{"id": 1, "name": "John"'  # Missing closing brace

        stream = io.StringIO(invalid_json)

        with pytest.raises(ImportError):
            async for batch in json_importer.import_from_stream(stream):
                pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_json_import_jsonl_with_invalid_lines(self, json_importer):
        """Test JSON Lines import with some invalid lines."""
        jsonl_data = """{"id": 1, "name": "John"}
invalid json line
{"id": 3, "name": "Bob"}"""

        options = ImportOptions(json_lines=True)
        importer = JSONImporter(options=options)

        stream = io.StringIO(jsonl_data)
        batches = []
        async for batch in importer.import_from_stream(stream):
            batches.append(batch)

        assert len(batches) == 1
        assert len(batches[0].records) == 3  # Includes error record

        # Check that invalid record is marked as invalid
        error_record = batches[0].records[1]
        assert error_record.is_valid is False
        assert len(error_record.validation_errors) > 0

    @pytest.mark.unit
    def test_json_path_extraction(self, json_importer):
        """Test JSONPath extraction functionality."""
        data = {"level1": {"level2": [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]}}

        # Test simple path
        result = json_importer._extract_json_path(data, "level1.level2")
        assert len(result) == 2
        assert result[0]["name"] == "John"

        # Test array indexing
        result = json_importer._extract_json_path(data, "level1.level2.0")
        assert result["name"] == "John"

        # Test non-existent path
        result = json_importer._extract_json_path(data, "nonexistent")
        assert result is None


class TestExcelImporter:
    """Test Excel import functionality."""

    @pytest.fixture
    def excel_importer(self):
        """Create Excel importer instance."""
        return ExcelImporter()

    @pytest.mark.unit
    def test_excel_importer_initialization(self, excel_importer):
        """Test Excel importer initialization."""
        assert excel_importer.options is not None
        assert isinstance(excel_importer.options, ImportOptions)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_excel_import_mock_workbook(self, excel_importer):
        """Test Excel import with mocked workbook."""
        # Mock openpyxl workbook
        with patch("openpyxl.load_workbook") as mock_load:
            mock_ws = Mock()
            mock_ws.max_column = 3
            mock_ws.max_row = 4

            # Mock header row
            mock_ws.cell.side_effect = lambda row, column: Mock(value=f"col{column}")

            # Mock data rows
            def mock_cell(row, column):
                if row == 1:  # Header row
                    return Mock(value=f"col{column}")
                else:  # Data rows
                    return Mock(value=f"data{row}_{column}", is_date=False)

            mock_ws.cell = mock_cell

            mock_wb = Mock()
            mock_wb.active = mock_ws
            mock_load.return_value = mock_wb

            with tempfile.NamedTemporaryFile(suffix=".xlsx") as f:
                batches = []
                async for batch in excel_importer.import_from_file(Path(f.name)):
                    batches.append(batch)

                assert len(batches) == 1
                # Should have 3 data rows (rows 2, 3, 4)
                assert len(batches[0].records) == 3

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_excel_import_with_sheet_selection(self, excel_importer):
        """Test Excel import with specific sheet selection."""
        options = ImportOptions(sheet_name="Sheet2")
        importer = ExcelImporter(options=options)

        with patch("openpyxl.load_workbook") as mock_load:
            mock_wb = Mock()
            mock_sheet2 = Mock()
            mock_sheet2.max_column = 2
            mock_sheet2.max_row = 3
            mock_sheet2.cell.side_effect = lambda row, column: Mock(
                value=f"sheet2_data{row}_{column}"
            )

            mock_wb.__getitem__ = Mock(return_value=mock_sheet2)
            mock_load.return_value = mock_wb

            with tempfile.NamedTemporaryFile(suffix=".xlsx") as f:
                batches = []
                async for batch in importer.import_from_file(Path(f.name)):
                    batches.append(batch)

                mock_wb.__getitem__.assert_called_with("Sheet2")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_excel_import_error_handling(self, excel_importer):
        """Test Excel import error handling."""
        # Test with non-existent file
        with pytest.raises(ImportError):
            async for batch in excel_importer.import_from_file(Path("/nonexistent/file.xlsx")):
                pass


class TestXMLImporter:
    """Test XML import functionality."""

    @pytest.fixture
    def xml_importer(self):
        """Create XML importer instance."""
        return XMLImporter()

    @pytest.fixture
    def xml_data(self):
        """Sample XML data for testing."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<root>
    <person id="1">
        <name>John</name>
        <age>25</age>
        <city>New York</city>
    </person>
    <person id="2">
        <name>Jane</name>
        <age>30</age>
        <city>London</city>
    </person>
</root>"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_xml_import_from_stream(self, xml_importer, xml_data):
        """Test XML import from stream."""
        stream = io.StringIO(xml_data)

        batches = []
        async for batch in xml_importer.import_from_stream(stream):
            batches.append(batch)

        assert len(batches) == 1
        assert len(batches[0].records) == 2  # Two person elements

        record = batches[0].records[0]
        assert record.data["@id"] == "1"  # Attribute
        assert record.data["name"] == "John"
        assert record.data["age"] == "25"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_xml_import_with_record_element(self, xml_importer, xml_data):
        """Test XML import with specific record element."""
        options = ImportOptions(xml_record_element="person")
        importer = XMLImporter(options=options)

        stream = io.StringIO(xml_data)
        batches = []
        async for batch in importer.import_from_stream(stream):
            batches.append(batch)

        assert len(batches) == 1
        assert len(batches[0].records) == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_xml_import_invalid_xml(self, xml_importer):
        """Test XML import with invalid XML."""
        invalid_xml = "<root><person><name>John</person></root>"  # Mismatched tags

        stream = io.StringIO(invalid_xml)

        with pytest.raises(ImportError):
            async for batch in xml_importer.import_from_stream(stream):
                pass

    @pytest.mark.unit
    def test_xml_element_to_dict_simple(self, xml_importer):
        """Test XML element to dictionary conversion."""
        xml_str = '<person id="1"><name>John</name><age>25</age></person>'
        element = ET.fromstring(xml_str)

        result = xml_importer._element_to_dict(element)

        assert result["@id"] == "1"  # Attribute
        assert result["name"] == "John"
        assert result["age"] == "25"

    @pytest.mark.unit
    def test_xml_element_to_dict_with_text_content(self, xml_importer):
        """Test XML element to dictionary with text content."""
        xml_str = "<description>This is a description</description>"
        element = ET.fromstring(xml_str)

        result = xml_importer._element_to_dict(element)

        assert result == "This is a description"

    @pytest.mark.unit
    def test_xml_element_to_dict_multiple_same_elements(self, xml_importer):
        """Test XML element to dictionary with multiple elements of same name."""
        xml_str = """<person>
            <hobby>reading</hobby>
            <hobby>swimming</hobby>
            <hobby>coding</hobby>
        </person>"""
        element = ET.fromstring(xml_str)

        result = xml_importer._element_to_dict(element)

        assert isinstance(result["hobby"], list)
        assert len(result["hobby"]) == 3
        assert "reading" in result["hobby"]


class TestImporterFactory:
    """Test importer factory functions."""

    @pytest.mark.unit
    def test_create_importer_csv(self):
        """Test creating CSV importer."""
        importer = create_importer(DataFormat.CSV)
        assert isinstance(importer, CSVImporter)

    @pytest.mark.unit
    def test_create_importer_json(self):
        """Test creating JSON importer."""
        importer = create_importer(DataFormat.JSON)
        assert isinstance(importer, JSONImporter)

    @pytest.mark.unit
    def test_create_importer_jsonl(self):
        """Test creating JSON Lines importer."""
        importer = create_importer(DataFormat.JSONL)
        assert isinstance(importer, JSONImporter)
        assert importer.options.json_lines is True

    @pytest.mark.unit
    def test_create_importer_excel(self):
        """Test creating Excel importer."""
        importer = create_importer(DataFormat.EXCEL)
        assert isinstance(importer, ExcelImporter)

    @pytest.mark.unit
    def test_create_importer_xml(self):
        """Test creating XML importer."""
        importer = create_importer(DataFormat.XML)
        assert isinstance(importer, XMLImporter)

    @pytest.mark.unit
    def test_create_importer_unsupported_format(self):
        """Test creating importer with unsupported format."""
        with pytest.raises(FormatError):
            create_importer(DataFormat.PARQUET)

    @pytest.mark.unit
    def test_create_importer_with_options(self):
        """Test creating importer with custom options."""
        config = TransferConfig(batch_size=100)
        options = ImportOptions(delimiter=";")

        importer = create_importer(DataFormat.CSV, config, options)

        assert isinstance(importer, CSVImporter)
        assert importer.config.batch_size == 100
        assert importer.options.delimiter == ";"


class TestFormatDetection:
    """Test format detection functionality."""

    @pytest.mark.unit
    def test_detect_format_by_extension(self):
        """Test format detection by file extension."""
        test_cases = [
            ("file.csv", DataFormat.CSV),
            ("data.json", DataFormat.JSON),
            ("lines.jsonl", DataFormat.JSONL),
            ("sheet.xlsx", DataFormat.EXCEL),
            ("old_sheet.xls", DataFormat.EXCEL),
            ("config.xml", DataFormat.XML),
        ]

        for filename, expected_format in test_cases:
            with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix) as f:
                detected_format = detect_format(Path(f.name))
                assert detected_format == expected_format

    @pytest.mark.unit
    def test_detect_format_by_content_json(self):
        """Test format detection by JSON content."""
        json_content = '{"key": "value"}'

        with tempfile.NamedTemporaryFile(mode="w", suffix=".unknown", delete=False) as f:
            f.write(json_content)
            temp_path = Path(f.name)

        try:
            detected_format = detect_format(temp_path)
            assert detected_format == DataFormat.JSON
        finally:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass

    @pytest.mark.unit
    def test_detect_format_by_content_jsonl(self):
        """Test format detection by JSON Lines content."""
        jsonl_content = '{"key": "value1"}\n{"key": "value2"}\n{"key": "value3"}'

        with tempfile.NamedTemporaryFile(mode="w", suffix=".unknown", delete=False) as f:
            f.write(jsonl_content)
            temp_path = Path(f.name)

        try:
            detected_format = detect_format(temp_path)
            assert detected_format == DataFormat.JSONL
        finally:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass

    @pytest.mark.unit
    def test_detect_format_by_content_xml(self):
        """Test format detection by XML content."""
        xml_content = '<?xml version="1.0"?><root><item>test</item></root>'

        with tempfile.NamedTemporaryFile(mode="w", suffix=".unknown", delete=False) as f:
            f.write(xml_content)
            temp_path = Path(f.name)

        try:
            detected_format = detect_format(temp_path)
            assert detected_format == DataFormat.XML
        finally:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass

    @pytest.mark.unit
    def test_detect_format_default_csv(self):
        """Test format detection defaults to CSV."""
        text_content = "name,age,city\nJohn,25,NYC"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".unknown", delete=False) as f:
            f.write(text_content)
            temp_path = Path(f.name)

        try:
            detected_format = detect_format(temp_path)
            assert detected_format == DataFormat.CSV
        finally:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass


class TestImportFileFunction:
    """Test the import_file convenience function."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_import_file_auto_detect(self):
        """Test import_file with automatic format detection."""
        csv_data = "name,age\nJohn,25\nJane,30"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_data)
            temp_path = Path(f.name)

        try:
            # Import using the convenience function
            from dotmac.platform.data_transfer.importers import import_file

            batches = []
            async for batch in import_file(temp_path):
                batches.append(batch)

            assert len(batches) == 1
            assert len(batches[0].records) == 2
            assert batches[0].records[0].data["name"] == "John"

        finally:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_import_file_explicit_format(self):
        """Test import_file with explicit format specification."""
        json_data = [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".data", delete=False) as f:
            json.dump(json_data, f)
            temp_path = Path(f.name)

        try:
            from dotmac.platform.data_transfer.importers import import_file

            batches = []
            async for batch in import_file(temp_path, data_format=DataFormat.JSON):
                batches.append(batch)

            assert len(batches) == 1
            assert len(batches[0].records) == 2
            assert batches[0].records[0].data["name"] == "John"

        finally:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass


class TestIntegrationScenarios:
    """Integration tests for import functionality."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_large_csv_import_batching(self):
        """Test importing large CSV with proper batching."""
        # Create large CSV data
        rows = []
        for i in range(1000):
            rows.append(f"user{i},{20 + (i % 50)},city{i % 10}")

        csv_data = "name,age,city\n" + "\n".join(rows)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_data)
            temp_path = Path(f.name)

        try:
            config = TransferConfig(batch_size=100)  # Small batches for testing
            importer = CSVImporter(config=config)

            batches = []
            async for batch in importer.import_from_file(temp_path):
                batches.append(batch)

            # Should create multiple batches
            assert len(batches) >= 10

            # Verify total records
            total_records = sum(len(batch.records) for batch in batches)
            assert total_records == 1000

        finally:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_mixed_data_types_import(self):
        """Test importing data with mixed data types."""
        csv_data = """name,age,salary,active,start_date
John Doe,25,50000.50,true,2023-01-15
Jane Smith,30,75000.00,false,2022-06-01
Bob Johnson,35,,true,2021-12-10"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_data)
            temp_path = Path(f.name)

        try:
            importer = CSVImporter()

            batches = []
            async for batch in importer.import_from_file(temp_path):
                batches.append(batch)

            records = batches[0].records

            # Check type inference
            assert isinstance(records[0].data["age"], int)
            assert isinstance(records[0].data["salary"], float)
            assert isinstance(records[0].data["active"], bool)
            assert records[0].data["name"] == "John Doe"

            # Check empty value handling
            assert records[2].data["salary"] is None

        finally:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass

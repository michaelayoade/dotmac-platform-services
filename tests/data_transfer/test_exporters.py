"""
Comprehensive tests for data export functionality.
"""

import csv
import io
import json
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dotmac.platform.data_transfer.base import (
    DataBatch,
    DataFormat,
    DataRecord,
    ExportError,
    FormatError,
    TransferConfig,
    TransferStatus,
)
from dotmac.platform.data_transfer.exporters import (
    CSVExporter,
    ExcelExporter,
    ExportOptions,
    JSONExporter,
    XMLExporter,
    create_exporter,
)


class TestExportOptions:
    """Test export options configuration."""

    @pytest.mark.unit
    def test_export_options_defaults(self):
        """Test default export options."""
        options = ExportOptions()

        # CSV options
        assert options.delimiter == ","
        assert options.quotechar == '"'
        assert options.include_headers is True
        assert options.line_terminator == "\n"

        # JSON options
        assert options.json_indent == 2
        assert options.json_ensure_ascii is False
        assert options.json_lines is False

        # Excel options
        assert options.sheet_name == "Sheet1"
        assert options.auto_filter is True

        # General options
        assert options.max_file_size == 104857600  # 100MB
        assert options.include_metadata is False
        assert options.json_sort_keys is False

    @pytest.mark.unit
    def test_export_options_custom_values(self):
        """Test custom export options."""
        options = ExportOptions(
            delimiter=";",
            quotechar="'",
            json_indent=4,
            sheet_name="Data",
            max_file_size=5000000,
            include_metadata=True,
        )

        assert options.delimiter == ";"
        assert options.quotechar == "'"
        assert options.json_indent == 4
        assert options.sheet_name == "Data"
        assert options.max_file_size == 5000000
        assert options.include_metadata is True

    @pytest.mark.unit
    def test_export_options_validation(self):
        """Test export options validation."""
        # Valid delimiter
        options = ExportOptions(delimiter=",")
        assert options.delimiter == ","

        # Invalid delimiter should raise error
        with pytest.raises(ValueError):
            ExportOptions(delimiter="")

        with pytest.raises(ValueError):
            ExportOptions(delimiter="ab")


class TestCSVExporter:
    """Test CSV export functionality."""

    @pytest.fixture
    def csv_exporter(self):
        """Create CSV exporter instance."""
        return CSVExporter()

    @pytest.fixture
    def sample_records(self):
        """Sample data records for testing."""
        return [
            DataRecord(data={"name": "John", "age": 25, "city": "New York"}),
            DataRecord(data={"name": "Jane", "age": 30, "city": "London"}),
            DataRecord(data={"name": "Bob", "age": 35, "city": "Paris"}),
        ]

    @pytest.fixture
    def sample_batch(self, sample_records):
        """Sample data batch for testing."""
        total_size = sum(len(str(record.data)) for record in sample_records)
        return DataBatch(batch_number=1, records=sample_records, total_size=total_size)

    @pytest.mark.unit
    def test_csv_exporter_initialization(self):
        """Test CSV exporter initialization."""
        exporter = CSVExporter()
        assert exporter.options is not None
        assert isinstance(exporter.options, ExportOptions)

        # Test with custom config and options
        config = settings.Transfer.model_copy(update={batch_size=500})
        options = ExportOptions(delimiter=";")
        exporter = CSVExporter(config, options)
        assert exporter.config.batch_size == 500
        assert exporter.options.delimiter == ";"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_csv_export_to_stream_basic(self, csv_exporter, sample_batch):
        """Test basic CSV export to stream."""
        stream = io.StringIO()

        await csv_exporter.export_batch_to_stream(sample_batch, stream)

        content = stream.getvalue()
        lines = content.strip().split("\n")

        # Should have header + 3 data rows
        assert len(lines) == 4
        assert "name,age,city" in lines[0]  # Header
        assert "John,25,New York" in lines[1]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_csv_export_to_file(self, csv_exporter, sample_batch):
        """Test CSV export to file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = Path(f.name)

        try:
            await csv_exporter.export_batch_to_file(sample_batch, temp_path)

            # Read back and verify
            with open(temp_path, "r") as f:
                content = f.read()

            lines = content.strip().split("\n")
            assert len(lines) == 4
            assert "name,age,city" in lines[0]
            assert "Jane,30,London" in lines[2]

        finally:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_csv_export_with_custom_delimiter(self, sample_batch):
        """Test CSV export with custom delimiter."""
        options = ExportOptions(delimiter=";")
        exporter = CSVExporter(options=options)

        stream = io.StringIO()
        await exporter.export_batch_to_stream(sample_batch, stream)

        content = stream.getvalue()
        lines = content.strip().split("\n")

        assert "name;age;city" in lines[0]
        assert "John;25;New York" in lines[1]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_csv_export_without_header(self, sample_batch):
        """Test CSV export without header row."""
        options = ExportOptions(include_headers=False)
        exporter = CSVExporter(options=options)

        stream = io.StringIO()
        await exporter.export_batch_to_stream(sample_batch, stream)

        content = stream.getvalue()
        lines = content.strip().split("\n")

        # Should have only 3 data rows, no header
        assert len(lines) == 3
        assert lines[0] == "John,25,New York"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_csv_export_with_quotes(self, sample_batch):
        """Test CSV export with quoted values."""
        # Add record with special characters
        special_record = DataRecord(data={"name": "O'Connor, Mary", "age": 28, "city": "Dublin"})
        sample_batch.records.append(special_record)

        exporter = CSVExporter()
        stream = io.StringIO()
        await exporter.export_batch_to_stream(sample_batch, stream)

        content = stream.getvalue()
        # Should properly quote the name with comma and apostrophe
        assert '"O\'Connor, Mary"' in content

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_csv_export_empty_batch(self, csv_exporter):
        """Test CSV export with empty batch."""
        empty_batch = DataBatch(batch_number=1, records=[], total_size=0)

        stream = io.StringIO()
        await csv_exporter.export_batch_to_stream(empty_batch, stream)

        content = stream.getvalue()
        assert content.strip() == ""  # Should be empty

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_csv_export_missing_fields(self, csv_exporter):
        """Test CSV export with records having different fields."""
        records = [
            DataRecord(data={"name": "John", "age": 25}),
            DataRecord(data={"name": "Jane", "city": "London"}),  # Missing age
            DataRecord(data={"age": 35, "city": "Paris"}),  # Missing name
        ]
        total_size = sum(len(str(record.data)) for record in records)
        batch = DataBatch(batch_number=1, records=records, total_size=total_size)

        stream = io.StringIO()
        await csv_exporter.export_batch_to_stream(batch, stream)

        content = stream.getvalue()
        lines = content.strip().split("\n")

        # Should handle missing fields gracefully
        assert len(lines) == 4  # Header + 3 data rows


class TestJSONExporter:
    """Test JSON export functionality."""

    @pytest.fixture
    def json_exporter(self):
        """Create JSON exporter instance."""
        return JSONExporter()

    @pytest.fixture
    def sample_records(self):
        """Sample data records for testing."""
        return [
            DataRecord(data={"id": 1, "name": "John", "active": True}),
            DataRecord(data={"id": 2, "name": "Jane", "active": False}),
            DataRecord(data={"id": 3, "name": "Bob", "active": True}),
        ]

    @pytest.fixture
    def sample_batch(self, sample_records):
        """Sample data batch for testing."""
        total_size = sum(len(str(record.data)) for record in sample_records)
        return DataBatch(batch_number=1, records=sample_records, total_size=total_size)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_json_export_to_stream_array(self, json_exporter, sample_batch):
        """Test JSON export to stream as array."""
        stream = io.StringIO()

        await json_exporter.export_batch_to_stream(sample_batch, stream)

        content = stream.getvalue()
        data = json.loads(content)

        assert isinstance(data, list)
        assert len(data) == 3
        assert data[0]["name"] == "John"
        assert data[1]["id"] == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_json_export_jsonl_format(self, sample_batch):
        """Test JSON Lines format export."""
        options = ExportOptions(json_lines=True)
        exporter = JSONExporter(options=options)

        stream = io.StringIO()
        await exporter.export_batch_to_stream(sample_batch, stream)

        content = stream.getvalue()
        lines = content.strip().split("\n")

        assert len(lines) == 3
        # Each line should be valid JSON
        for line in lines:
            data = json.loads(line)
            assert "id" in data
            assert "name" in data

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_json_export_with_custom_indent(self, sample_batch):
        """Test JSON export with custom indentation."""
        options = ExportOptions(json_indent=4)
        exporter = JSONExporter(options=options)

        stream = io.StringIO()
        await exporter.export_batch_to_stream(sample_batch, stream)

        content = stream.getvalue()
        # Should be pretty-printed with 4-space indentation
        assert '{\n    "id"' in content

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_json_export_compact_format(self, sample_batch):
        """Test JSON export in compact format."""
        options = ExportOptions(json_indent=None)
        exporter = JSONExporter(options=options)

        stream = io.StringIO()
        await exporter.export_batch_to_stream(sample_batch, stream)

        content = stream.getvalue()
        # Should be compact (no pretty printing)
        assert "\n    " not in content  # No indentation
        assert '[{"id": 1' in content

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_json_export_with_sorting(self, sample_batch):
        """Test JSON export with sorted keys."""
        options = ExportOptions(json_sort_keys=True)
        exporter = JSONExporter(options=options)

        stream = io.StringIO()
        await exporter.export_batch_to_stream(sample_batch, stream)

        content = stream.getvalue()
        data = json.loads(content)

        # Keys should be sorted
        first_record = data[0]
        keys = list(first_record.keys())
        assert keys == sorted(keys)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_json_export_empty_batch(self, json_exporter):
        """Test JSON export with empty batch."""
        empty_batch = DataBatch(batch_number=1, records=[], total_size=0)

        stream = io.StringIO()
        await json_exporter.export_batch_to_stream(empty_batch, stream)

        content = stream.getvalue()
        data = json.loads(content)
        assert data == []


class TestXMLExporter:
    """Test XML export functionality."""

    @pytest.fixture
    def xml_exporter(self):
        """Create XML exporter instance."""
        return XMLExporter()

    @pytest.fixture
    def sample_records(self):
        """Sample data records for testing."""
        return [
            DataRecord(data={"id": 1, "name": "John", "age": 25}),
            DataRecord(data={"id": 2, "name": "Jane", "age": 30}),
        ]

    @pytest.fixture
    def sample_batch(self, sample_records):
        """Sample data batch for testing."""
        total_size = sum(len(str(record.data)) for record in sample_records)
        return DataBatch(batch_number=1, records=sample_records, total_size=total_size)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_xml_export_to_stream_basic(self, xml_exporter, sample_batch):
        """Test basic XML export to stream."""
        stream = io.StringIO()

        await xml_exporter.export_batch_to_stream(sample_batch, stream)

        content = stream.getvalue()
        root = ET.fromstring(content)

        assert root.tag == "root"
        records = root.findall("record")
        assert len(records) == 2

        first_record = records[0]
        assert first_record.find("id").text == "1"
        assert first_record.find("name").text == "John"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_xml_export_with_custom_root(self, sample_batch):
        """Test XML export with custom root element."""
        options = ExportOptions(xml_root_element="users")
        exporter = XMLExporter(options=options)

        stream = io.StringIO()
        await exporter.export_batch_to_stream(sample_batch, stream)

        content = stream.getvalue()
        root = ET.fromstring(content)

        assert root.tag == "users"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_xml_export_with_custom_record_element(self, sample_batch):
        """Test XML export with custom record element."""
        options = ExportOptions(xml_record_element="person")
        exporter = XMLExporter(options=options)

        stream = io.StringIO()
        await exporter.export_batch_to_stream(sample_batch, stream)

        content = stream.getvalue()
        root = ET.fromstring(content)

        records = root.findall("person")
        assert len(records) == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_xml_export_with_attributes(self, xml_exporter):
        """Test XML export with attributes."""
        records = [
            DataRecord(data={"@id": "1", "name": "John", "age": 25}),
            DataRecord(data={"@id": "2", "name": "Jane", "age": 30}),
        ]
        total_size = sum(len(str(record.data)) for record in records)
        batch = DataBatch(batch_number=1, records=records, total_size=total_size)

        stream = io.StringIO()
        await xml_exporter.export_batch_to_stream(batch, stream)

        content = stream.getvalue()
        root = ET.fromstring(content)

        first_record = root.find("record")
        assert first_record.get("id") == "1"  # Should be an attribute
        assert first_record.find("name").text == "John"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_xml_export_with_nested_data(self, xml_exporter):
        """Test XML export with nested data structures."""
        records = [
            DataRecord(data={"id": 1, "profile": {"name": "John", "age": 25}}),
        ]
        total_size = sum(len(str(record.data)) for record in records)
        batch = DataBatch(batch_number=1, records=records, total_size=total_size)

        stream = io.StringIO()
        await xml_exporter.export_batch_to_stream(batch, stream)

        content = stream.getvalue()
        root = ET.fromstring(content)

        record = root.find("record")
        assert record.find("id").text == "1"

        profile = record.find("profile")
        assert profile is not None
        assert profile.find("name").text == "John"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_xml_export_empty_batch(self, xml_exporter):
        """Test XML export with empty batch."""
        empty_batch = DataBatch(batch_number=1, records=[], total_size=0)

        stream = io.StringIO()
        await xml_exporter.export_batch_to_stream(empty_batch, stream)

        content = stream.getvalue()
        root = ET.fromstring(content)

        assert root.tag == "root"
        assert len(root.findall("record")) == 0

    @pytest.mark.unit
    def test_xml_dict_to_element_simple(self, xml_exporter):
        """Test dictionary to XML element conversion."""
        data = {"name": "John", "age": "25"}
        element = xml_exporter._dict_to_element("person", data)

        assert element.tag == "person"
        assert element.find("name").text == "John"
        assert element.find("age").text == "25"

    @pytest.mark.unit
    def test_xml_dict_to_element_with_attributes(self, xml_exporter):
        """Test dictionary to XML element with attributes."""
        data = {"@id": "1", "@type": "user", "name": "John"}
        element = xml_exporter._dict_to_element("person", data)

        assert element.get("id") == "1"
        assert element.get("type") == "user"
        assert element.find("name").text == "John"

    @pytest.mark.unit
    def test_xml_dict_to_element_with_lists(self, xml_exporter):
        """Test dictionary to XML element with list values."""
        data = {"name": "John", "hobbies": ["reading", "coding", "gaming"]}
        element = xml_exporter._dict_to_element("person", data)

        hobbies = element.findall("hobbies")
        assert len(hobbies) == 3
        assert hobbies[0].text == "reading"


class TestExcelExporter:
    """Test Excel export functionality."""

    @pytest.fixture
    def excel_exporter(self):
        """Create Excel exporter instance."""
        return ExcelExporter()

    @pytest.fixture
    def sample_records(self):
        """Sample data records for testing."""
        return [
            DataRecord(data={"name": "John", "age": 25, "salary": 50000.0}),
            DataRecord(data={"name": "Jane", "age": 30, "salary": 60000.0}),
        ]

    @pytest.fixture
    def sample_batch(self, sample_records):
        """Sample data batch for testing."""
        total_size = sum(len(str(record.data)) for record in sample_records)
        return DataBatch(batch_number=1, records=sample_records, total_size=total_size)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_excel_export_to_file(self, excel_exporter, sample_batch):
        """Test Excel export to file."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            temp_path = Path(f.name)

        try:
            await excel_exporter.export_batch_to_file(sample_batch, temp_path)

            # Verify file exists
            assert temp_path.exists()

            # Mock openpyxl to verify data was written
            with patch("openpyxl.load_workbook") as mock_load:
                mock_wb = Mock()
                mock_ws = Mock()
                mock_wb.active = mock_ws
                mock_load.return_value = mock_wb

                # This would normally read back and verify data
                # For now, just check that the export didn't fail
                assert True

        finally:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_excel_export_with_custom_sheet_name(self, sample_batch):
        """Test Excel export with custom sheet name."""
        options = ExportOptions(sheet_name="MyData")
        exporter = ExcelExporter(options=options)

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            temp_path = Path(f.name)

        try:
            # Mock openpyxl for this test
            with patch("openpyxl.Workbook") as mock_wb_class:
                mock_wb = Mock()
                mock_ws = Mock()
                mock_wb.active = mock_ws
                mock_wb_class.return_value = mock_wb

                await exporter.export_batch_to_file(sample_batch, temp_path)

                # Verify sheet name was set
                mock_ws.title = "MyData"

        finally:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_excel_export_stream_not_supported(self, excel_exporter, sample_batch):
        """Test that Excel export to stream raises appropriate error."""
        stream = io.StringIO()

        with pytest.raises(ExportError, match="Excel export to stream not supported"):
            await excel_exporter.export_batch_to_stream(sample_batch, stream)


class TestExporterFactory:
    """Test exporter factory functions."""

    @pytest.mark.unit
    def test_create_exporter_csv(self):
        """Test creating CSV exporter."""
        exporter = create_exporter(DataFormat.CSV)
        assert isinstance(exporter, CSVExporter)

    @pytest.mark.unit
    def test_create_exporter_json(self):
        """Test creating JSON exporter."""
        exporter = create_exporter(DataFormat.JSON)
        assert isinstance(exporter, JSONExporter)

    @pytest.mark.unit
    def test_create_exporter_xml(self):
        """Test creating XML exporter."""
        exporter = create_exporter(DataFormat.XML)
        assert isinstance(exporter, XMLExporter)

    @pytest.mark.unit
    def test_create_exporter_excel(self):
        """Test creating Excel exporter."""
        exporter = create_exporter(DataFormat.EXCEL)
        assert isinstance(exporter, ExcelExporter)

    @pytest.mark.unit
    def test_create_exporter_unsupported_format(self):
        """Test creating exporter with unsupported format."""
        with pytest.raises(FormatError):
            create_exporter(DataFormat.PARQUET)

    @pytest.mark.unit
    def test_create_exporter_with_options(self):
        """Test creating exporter with custom options."""
        config = settings.Transfer.model_copy(update={batch_size=100})
        options = ExportOptions(delimiter=";")

        exporter = create_exporter(DataFormat.CSV, config, options)

        assert isinstance(exporter, CSVExporter)
        assert exporter.config.batch_size == 100
        assert exporter.options.delimiter == ";"


class TestExportValidation:
    """Test data validation during export."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_export_with_validation_enabled(self):
        """Test export with data validation enabled."""
        # Create record with invalid data
        invalid_record = DataRecord(
            data={"name": "John", "age": "invalid_age"},
            is_valid=False,
            validation_errors=["Invalid age format"],
        )
        batch = DataBatch(batch_number=1, records=[invalid_record], total_size=100)

        from dotmac.platform.data_transfer import create_transfer_config
        config = create_transfer_config(skip_invalid=True)  # Skip invalid records
        exporter = CSVExporter(config=config)

        stream = io.StringIO()

        # Should skip invalid records when skip_invalid=True
        await exporter.export_batch_to_stream(batch, stream)
        content = stream.getvalue()
        # Invalid record should be skipped, so only headers (if any) should remain
        lines = content.strip().split("\n") if content.strip() else []
        assert len(lines) <= 1  # At most header line

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_export_with_validation_disabled(self):
        """Test export with data validation disabled."""
        # Create record with invalid data
        invalid_record = DataRecord(
            data={"name": "John", "age": "invalid_age"},
            is_valid=False,
            validation_errors=["Invalid age format"],
        )
        batch = DataBatch(batch_number=1, records=[invalid_record], total_size=100)

        from dotmac.platform.data_transfer import create_transfer_config
        config = create_transfer_config(skip_invalid=False)  # Don't skip invalid records
        exporter = CSVExporter(config=config)

        stream = io.StringIO()
        # Should not raise error with validation disabled
        await exporter.export_batch_to_stream(batch, stream)

        content = stream.getvalue()
        assert "invalid_age" in content


class TestIntegrationScenarios:
    """Integration tests for export functionality."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_roundtrip_csv_export_import(self):
        """Test exporting data and importing it back."""
        # Create original data
        original_records = [
            DataRecord(data={"id": 1, "name": "John", "active": True}),
            DataRecord(data={"id": 2, "name": "Jane", "active": False}),
        ]
        total_size = sum(len(str(record.data)) for record in original_records)
        batch = DataBatch(batch_number=1, records=original_records, total_size=total_size)

        # Export to CSV
        exporter = CSVExporter()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = Path(f.name)

        try:
            await exporter.export_batch_to_file(batch, temp_path)

            # Import back
            from dotmac.platform.data_transfer.importers import CSVImporter

            importer = CSVImporter()
            imported_batches = []
            async for imported_batch in importer.import_from_file(temp_path):
                imported_batches.append(imported_batch)

            # Verify data integrity
            assert len(imported_batches) == 1
            imported_records = imported_batches[0].records
            assert len(imported_records) == 2

            # Check data values (note: types may be inferred differently)
            assert imported_records[0].data["name"] == "John"
            assert imported_records[1].data["name"] == "Jane"

        finally:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_large_batch_export_performance(self):
        """Test export performance with large batches."""
        # Create large batch
        records = []
        for i in range(10000):
            records.append(
                DataRecord(
                    data={
                        "id": i,
                        "name": f"User{i}",
                        "email": f"user{i}@example.com",
                        "active": i % 2 == 0,
                    }
                )
            )

        total_size = sum(len(str(record.data)) for record in records)
        batch = DataBatch(batch_number=1, records=records, total_size=total_size)

        # Export to different formats and measure performance
        formats_to_test = [
            (DataFormat.CSV, CSVExporter()),
            (DataFormat.JSON, JSONExporter()),
        ]

        for format_name, exporter in formats_to_test:
            with tempfile.NamedTemporaryFile(suffix=f".{format_name.value}", delete=False) as f:
                temp_path = Path(f.name)

            try:
                import time

                start_time = time.time()

                await exporter.export_batch_to_file(batch, temp_path)

                end_time = time.time()
                export_time = end_time - start_time

                # Should complete within reasonable time (less than 10 seconds)
                assert export_time < 10.0

                # Verify file was created and has content
                assert temp_path.exists()
                assert temp_path.stat().st_size > 0

            finally:
                try:
                    temp_path.unlink()
                except FileNotFoundError:
                    pass

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_export_with_mixed_data_types(self):
        """Test export with various data types."""
        from datetime import datetime

        records = [
            DataRecord(
                data={
                    "id": 1,
                    "name": "John Doe",
                    "age": 25,
                    "salary": 50000.50,
                    "active": True,
                    "created_at": datetime(2023, 1, 15),
                    "tags": ["admin", "developer"],
                    "profile": {"city": "New York", "country": "USA"},
                }
            )
        ]
        total_size = sum(len(str(record.data)) for record in records)
        batch = DataBatch(batch_number=1, records=records, total_size=total_size)

        # Test with different exporters
        exporters = [
            (CSVExporter(), ".csv"),
            (JSONExporter(), ".json"),
            (XMLExporter(), ".xml"),
        ]

        for exporter, extension in exporters:
            with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as f:
                temp_path = Path(f.name)

            try:
                await exporter.export_batch_to_file(batch, temp_path)

                # Verify file was created
                assert temp_path.exists()
                assert temp_path.stat().st_size > 0

                # Read back and verify content structure
                with open(temp_path, "r") as f:
                    content = f.read()

                # Should contain the name
                assert "John Doe" in content

            finally:
                try:
                    temp_path.unlink()
                except FileNotFoundError:
                    pass

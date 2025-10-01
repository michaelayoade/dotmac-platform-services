"""
Targeted tests to boost exporters.py coverage from 28% to 90%+.
Focuses on missing lines: 42-83, 95-134, 146-179, 191-221, 225-238, 250-276, 298, 316-328, 348, 384, 390
"""

import asyncio
import json
import tempfile
from pathlib import Path
from typing import AsyncGenerator

import pandas as pd
import pytest
import yaml

from dotmac.platform.data_transfer.core import (
    DataBatch,
    DataFormat,
    DataRecord,
    ExportOptions,
    TransferConfig,
    TransferStatus,
)
from dotmac.platform.data_transfer.exporters import (
    CSVExporter,
    JSONExporter,
    ExcelExporter,
    XMLExporter,
    YAMLExporter,
    create_exporter,
    export_data,
    detect_format,
    compress_file,
    CompressionType,
    ExportError,
    FormatError,
)


@pytest.fixture
async def sample_data() -> AsyncGenerator[DataBatch, None]:
    """Generate sample data batches."""
    records = [
        DataRecord(data={"name": "Alice", "age": 30, "city": "NYC"}),
        DataRecord(data={"name": "Bob", "age": 25, "city": "LA"}),
    ]
    batch = DataBatch(records=records, batch_number=1)
    yield batch


@pytest.fixture
async def empty_data() -> AsyncGenerator[DataBatch, None]:
    """Generate empty data batches."""
    batch = DataBatch(records=[], batch_number=0)
    yield batch


@pytest.mark.asyncio
class TestCSVExporter:
    """Test CSV exporter - covers lines 36-83."""

    async def test_export_csv_with_all_records(self, tmpdir):
        """Test CSV export with multiple records."""
        config = TransferConfig()
        options = ExportOptions(delimiter=",", include_headers=True, encoding="utf-8")
        exporter = CSVExporter(config, options)

        async def data_gen():
            records = [
                DataRecord(data={"name": "Alice", "age": 30}),
                DataRecord(data={"name": "Bob", "age": 25}),
            ]
            yield DataBatch(records=records, batch_number=1)

        file_path = Path(tmpdir) / "test.csv"
        result = await exporter.export_to_file(data_gen(), file_path)

        assert result.status == TransferStatus.COMPLETED
        assert file_path.exists()

        # Verify CSV content
        df = pd.read_csv(file_path)
        assert len(df) == 2
        assert list(df.columns) == ["name", "age"]
        assert df.iloc[0]["name"] == "Alice"

    async def test_export_csv_with_custom_quoting(self, tmpdir):
        """Test CSV export with different quoting options - covers lines 58-75."""
        config = TransferConfig()
        file_path = Path(tmpdir) / "test_quote.csv"

        async def data_gen():
            records = [DataRecord(data={"text": "hello, world"})]
            yield DataBatch(records=records, batch_number=1)

        # Test QUOTE_ALL (quoting=1)
        options = ExportOptions(quoting=1)
        exporter = CSVExporter(config, options)
        await exporter.export_to_file(data_gen(), file_path)
        assert file_path.exists()

        # Test QUOTE_NONNUMERIC (quoting=2)
        options = ExportOptions(quoting=2)
        exporter = CSVExporter(config, options)
        await exporter.export_to_file(data_gen(), file_path)

        # Test QUOTE_NONE (quoting=3)
        options = ExportOptions(quoting=3)
        exporter = CSVExporter(config, options)
        await exporter.export_to_file(data_gen(), file_path)

        # Test invalid quoting (defaults to 0)
        options = ExportOptions(quoting=99)
        exporter = CSVExporter(config, options)
        await exporter.export_to_file(data_gen(), file_path)

    async def test_export_csv_empty_records(self, tmpdir):
        """Test CSV export with no records - covers line 54 branch."""
        config = TransferConfig()
        exporter = CSVExporter(config, ExportOptions())

        async def empty_gen():
            yield DataBatch(records=[], batch_number=0)

        file_path = Path(tmpdir) / "empty.csv"
        result = await exporter.export_to_file(empty_gen(), file_path)

        assert result.status == TransferStatus.COMPLETED

    async def test_export_csv_error_handling(self, tmpdir):
        """Test CSV export error handling - covers lines 80-83."""
        config = TransferConfig()
        exporter = CSVExporter(config, ExportOptions())

        async def error_gen():
            if False:
                yield
            raise ValueError("Test error")

        file_path = Path(tmpdir) / "error.csv"

        with pytest.raises(ExportError) as exc_info:
            await exporter.export_to_file(error_gen(), file_path)

        assert "Failed to export CSV" in str(exc_info.value)


@pytest.mark.asyncio
class TestJSONExporter:
    """Test JSON exporter - covers lines 89-134."""

    async def test_export_json_lines_mode(self, tmpdir):
        """Test JSON Lines export - covers lines 98-110."""
        config = TransferConfig()
        options = ExportOptions(
            json_lines=True, json_ensure_ascii=False, json_sort_keys=True
        )
        exporter = JSONExporter(config, options)

        async def data_gen():
            records = [
                DataRecord(data={"name": "Alice"}),
                DataRecord(data={"name": "Bob"}),
            ]
            yield DataBatch(records=records, batch_number=1)

        file_path = Path(tmpdir) / "test.jsonl"
        result = await exporter.export_to_file(data_gen(), file_path)

        assert result.status == TransferStatus.COMPLETED
        assert file_path.exists()

        # Verify JSONL format
        with open(file_path, "r") as f:
            lines = f.readlines()
            assert len(lines) == 2
            assert json.loads(lines[0])["name"] == "Alice"
            assert json.loads(lines[1])["name"] == "Bob"

    async def test_export_json_regular_mode(self, tmpdir):
        """Test regular JSON export - covers lines 111-127."""
        config = TransferConfig()
        options = ExportOptions(
            json_lines=False, json_indent=2, json_ensure_ascii=True
        )
        exporter = JSONExporter(config, options)

        async def data_gen():
            records = [
                DataRecord(data={"name": "Charlie", "age": 35}),
            ]
            yield DataBatch(records=records, batch_number=1)

        file_path = Path(tmpdir) / "test.json"
        result = await exporter.export_to_file(data_gen(), file_path)

        assert result.status == TransferStatus.COMPLETED

        # Verify JSON content
        with open(file_path, "r") as f:
            data = json.load(f)
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["name"] == "Charlie"

    async def test_export_json_empty_records(self, tmpdir):
        """Test JSON export with empty records - covers line 120 branch."""
        config = TransferConfig()
        exporter = JSONExporter(config, ExportOptions(json_lines=False))

        async def empty_gen():
            yield DataBatch(records=[], batch_number=0)

        file_path = Path(tmpdir) / "empty.json"
        result = await exporter.export_to_file(empty_gen(), file_path)
        assert result.status == TransferStatus.COMPLETED

    async def test_export_json_error_handling(self, tmpdir):
        """Test JSON export error handling - covers lines 131-134."""
        config = TransferConfig()
        exporter = JSONExporter(config, ExportOptions())

        async def error_gen():
            if False:
                yield
            raise ValueError("JSON export error")

        with pytest.raises(ExportError) as exc_info:
            await exporter.export_to_file(error_gen(), Path(tmpdir) / "err.json")

        assert "Failed to export JSON" in str(exc_info.value)


@pytest.mark.asyncio
class TestExcelExporter:
    """Test Excel exporter - covers lines 140-179."""

    async def test_export_excel_with_options(self, tmpdir):
        """Test Excel export with all options - covers lines 146-172."""
        config = TransferConfig()
        options = ExportOptions(
            sheet_name="TestSheet", freeze_panes=True, auto_filter=True
        )
        exporter = ExcelExporter(config, options)

        async def data_gen():
            records = [
                DataRecord(data={"product": "Widget", "price": 10.5}),
                DataRecord(data={"product": "Gadget", "price": 20.0}),
            ]
            yield DataBatch(records=records, batch_number=1)

        file_path = Path(tmpdir) / "test.xlsx"
        result = await exporter.export_to_file(data_gen(), file_path)

        assert result.status == TransferStatus.COMPLETED
        assert file_path.exists()

        # Verify Excel content
        df = pd.read_excel(file_path, sheet_name="TestSheet")
        assert len(df) == 2
        assert df.iloc[0]["product"] == "Widget"

    async def test_export_excel_empty_records(self, tmpdir):
        """Test Excel export with no records - covers line 158 branch."""
        config = TransferConfig()
        exporter = ExcelExporter(config, ExportOptions())

        async def empty_gen():
            yield DataBatch(records=[], batch_number=0)

        file_path = Path(tmpdir) / "empty.xlsx"
        result = await exporter.export_to_file(empty_gen(), file_path)
        assert result.status == TransferStatus.COMPLETED

    async def test_export_excel_error_handling(self, tmpdir):
        """Test Excel export error handling - covers lines 176-179."""
        config = TransferConfig()
        exporter = ExcelExporter(config, ExportOptions())

        async def error_gen():
            if False:
                yield
            raise ValueError("Excel error")

        with pytest.raises(ExportError) as exc_info:
            await exporter.export_to_file(error_gen(), Path(tmpdir) / "err.xlsx")

        assert "Failed to export Excel" in str(exc_info.value)


@pytest.mark.asyncio
class TestXMLExporter:
    """Test XML exporter - covers lines 185-238."""

    async def test_export_xml_with_pretty_print(self, tmpdir):
        """Test XML export with pretty printing - covers lines 191-211."""
        config = TransferConfig()
        options = ExportOptions(
            xml_root_element="data",
            xml_record_element="item",
            xml_pretty_print=True,
            encoding="utf-8",
        )
        exporter = XMLExporter(config, options)

        async def data_gen():
            records = [
                DataRecord(data={"name": "Test", "value": 42}),
            ]
            yield DataBatch(records=records, batch_number=1)

        file_path = Path(tmpdir) / "test.xml"
        result = await exporter.export_to_file(data_gen(), file_path)

        assert result.status == TransferStatus.COMPLETED
        assert file_path.exists()

        # Verify XML is readable
        with open(file_path, "r") as f:
            content = f.read()
            assert "<data>" in content
            assert "<item>" in content
            assert "<name>Test</name>" in content

    async def test_export_xml_without_pretty_print(self, tmpdir):
        """Test XML export without pretty printing - covers lines 212-214."""
        config = TransferConfig()
        options = ExportOptions(xml_pretty_print=False)
        exporter = XMLExporter(config, options)

        async def data_gen():
            records = [DataRecord(data={"key": "value"})]
            yield DataBatch(records=records, batch_number=1)

        file_path = Path(tmpdir) / "compact.xml"
        await exporter.export_to_file(data_gen(), file_path)
        assert file_path.exists()

    async def test_export_xml_with_nested_data(self, tmpdir):
        """Test XML export with nested data - covers _dict_to_xml lines 223-238."""
        config = TransferConfig()
        exporter = XMLExporter(config, ExportOptions())

        async def data_gen():
            records = [
                DataRecord(
                    record_id="1",
                    data={
                        "user": {"name": "Alice", "email": "alice@test.com"},
                        "tags": ["admin", "user"],
                        "active": True,
                        "score": None,
                    },
                )
            ]
            yield DataBatch(records=records, batch_number=1)

        file_path = Path(tmpdir) / "nested.xml"
        result = await exporter.export_to_file(data_gen(), file_path)

        assert result.status == TransferStatus.COMPLETED

    async def test_export_xml_error_handling(self, tmpdir):
        """Test XML export error handling - covers lines 218-221."""
        config = TransferConfig()
        exporter = XMLExporter(config, ExportOptions())

        async def error_gen():
            if False:
                yield
            raise ValueError("XML error")

        with pytest.raises(ExportError) as exc_info:
            await exporter.export_to_file(error_gen(), Path(tmpdir) / "err.xml")

        assert "Failed to export XML" in str(exc_info.value)


@pytest.mark.asyncio
class TestYAMLExporter:
    """Test YAML exporter - covers lines 244-276."""

    async def test_export_yaml_success(self, tmpdir):
        """Test YAML export - covers lines 250-272."""
        config = TransferConfig()
        options = ExportOptions(json_sort_keys=True, encoding="utf-8")
        exporter = YAMLExporter(config, options)

        async def data_gen():
            records = [
                DataRecord(data={"name": "Alice", "tags": ["a", "b"]}),
                DataRecord(data={"name": "Bob", "tags": ["c"]}),
            ]
            yield DataBatch(records=records, batch_number=1)

        file_path = Path(tmpdir) / "test.yaml"
        result = await exporter.export_to_file(data_gen(), file_path)

        assert result.status == TransferStatus.COMPLETED
        assert file_path.exists()

        # Verify YAML content
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)
            assert isinstance(data, list)
            assert len(data) == 2
            assert data[0]["name"] == "Alice"

    async def test_export_yaml_error_handling(self, tmpdir):
        """Test YAML export error handling - covers lines 273-276."""
        config = TransferConfig()
        exporter = YAMLExporter(config, ExportOptions())

        async def error_gen():
            if False:
                yield
            raise ValueError("YAML error")

        with pytest.raises(ExportError) as exc_info:
            await exporter.export_to_file(error_gen(), Path(tmpdir) / "err.yaml")

        assert "Failed to export YAML" in str(exc_info.value)


@pytest.mark.asyncio
class TestExporterFactory:
    """Test create_exporter factory - covers lines 279-304."""

    async def test_create_exporter_all_formats(self):
        """Test creating exporters for all formats - covers lines 286-303."""
        config = TransferConfig()

        # Test all supported formats
        csv_exp = create_exporter(DataFormat.CSV, config)
        assert isinstance(csv_exp, CSVExporter)

        json_exp = create_exporter(DataFormat.JSON, config)
        assert isinstance(json_exp, JSONExporter)

        jsonl_exp = create_exporter(DataFormat.JSONL, config)
        assert isinstance(jsonl_exp, JSONExporter)
        assert jsonl_exp.options.json_lines is True  # line 298

        excel_exp = create_exporter(DataFormat.EXCEL, config)
        assert isinstance(excel_exp, ExcelExporter)

        xml_exp = create_exporter(DataFormat.XML, config)
        assert isinstance(xml_exp, XMLExporter)

        yaml_exp = create_exporter(DataFormat.YAML, config)
        assert isinstance(yaml_exp, YAMLExporter)

    async def test_create_exporter_invalid_format(self):
        """Test creating exporter with unsupported format - covers lines 300-302."""
        config = TransferConfig()

        # Create a fake format enum member
        class FakeFormat:
            pass

        with pytest.raises(FormatError) as exc_info:
            create_exporter(FakeFormat(), config)

        assert "No exporter available" in str(exc_info.value)


@pytest.mark.asyncio
class TestExportDataFunction:
    """Test export_data helper function - covers lines 307-328."""

    async def test_export_data_with_format_detection(self, tmpdir):
        """Test export_data with automatic format detection - covers lines 316-328."""

        async def data_gen():
            records = [DataRecord(data={"test": "data"})]
            yield DataBatch(records=records, batch_number=1)

        # Test CSV
        csv_path = str(Path(tmpdir) / "output.csv")
        result = await export_data(data_gen(), csv_path)
        assert result.status == TransferStatus.COMPLETED

        # Test JSON
        json_path = str(Path(tmpdir) / "output.json")
        result = await export_data(data_gen(), json_path)
        assert result.status == TransferStatus.COMPLETED

        # Test with explicit format
        xlsx_path = str(Path(tmpdir) / "output.xlsx")
        result = await export_data(
            data_gen(), xlsx_path, format=DataFormat.EXCEL, config=TransferConfig()
        )
        assert result.status == TransferStatus.COMPLETED


class TestDetectFormat:
    """Test detect_format function - covers lines 331-348."""

    def test_detect_all_extensions(self):
        """Test format detection for all extensions - covers lines 333-346."""
        assert detect_format(Path("file.csv")) == DataFormat.CSV
        assert detect_format(Path("file.json")) == DataFormat.JSON
        assert detect_format(Path("file.jsonl")) == DataFormat.JSONL
        assert detect_format(Path("file.xlsx")) == DataFormat.EXCEL
        assert detect_format(Path("file.xls")) == DataFormat.EXCEL
        assert detect_format(Path("file.xml")) == DataFormat.XML
        assert detect_format(Path("file.yaml")) == DataFormat.YAML
        assert detect_format(Path("file.yml")) == DataFormat.YAML

    def test_detect_format_case_insensitive(self):
        """Test format detection is case insensitive."""
        assert detect_format(Path("FILE.CSV")) == DataFormat.CSV
        assert detect_format(Path("FILE.JSON")) == DataFormat.JSON

    def test_detect_format_unsupported(self):
        """Test format detection with unsupported extension - covers line 348."""
        with pytest.raises(FormatError) as exc_info:
            detect_format(Path("file.txt"))

        assert "Unsupported file format: .txt" in str(exc_info.value)


class TestCompressFile:
    """Test compress_file function - covers lines 351-391."""

    def test_compress_file_none(self, tmpdir):
        """Test no compression - covers lines 357-358."""
        file_path = Path(tmpdir) / "test.txt"
        file_path.write_text("test content")

        result = compress_file(file_path, CompressionType.NONE)
        assert result == file_path

    def test_compress_file_gzip(self, tmpdir):
        """Test gzip compression - covers lines 363-367."""
        file_path = Path(tmpdir) / "test.txt"
        file_path.write_text("test content for gzip")

        compressed = compress_file(file_path, CompressionType.GZIP)
        assert compressed.suffix == ".gz"
        assert compressed.exists()

    def test_compress_file_zip(self, tmpdir):
        """Test zip compression - covers lines 369-372."""
        file_path = Path(tmpdir) / "test.txt"
        file_path.write_text("test content for zip")

        compressed = compress_file(file_path, CompressionType.ZIP)
        assert compressed.suffix == ".zip"
        assert compressed.exists()

    def test_compress_file_bzip2(self, tmpdir):
        """Test bzip2 compression - covers lines 374-378."""
        file_path = Path(tmpdir) / "test.txt"
        file_path.write_text("test content for bzip2")

        compressed = compress_file(file_path, CompressionType.BZIP2)
        assert compressed.suffix == ".bz2"
        assert compressed.exists()

    def test_compress_file_delete_original(self, tmpdir):
        """Test compression with delete_original - covers line 383-384."""
        file_path = Path(tmpdir) / "test.txt"
        file_path.write_text("test content")

        compressed = compress_file(
            file_path, CompressionType.GZIP, delete_original=True
        )
        assert compressed.exists()
        assert not file_path.exists()  # Original deleted

    def test_compress_file_unsupported_type(self, tmpdir):
        """Test unsupported compression type - covers line 380-381."""
        file_path = Path(tmpdir) / "test.txt"
        file_path.write_text("test content")

        # Create a fake compression type
        class FakeCompression:
            pass

        with pytest.raises(ExportError) as exc_info:
            compress_file(file_path, FakeCompression())

        assert "Unsupported compression type" in str(exc_info.value)

    def test_compress_file_error_cleanup(self, tmpdir):
        """Test compression error cleanup - covers lines 388-391."""
        file_path = Path(tmpdir) / "test.txt"
        file_path.write_text("test content")

        # Force an error by making file unreadable
        file_path.chmod(0o000)

        try:
            with pytest.raises(ExportError):
                compress_file(file_path, CompressionType.GZIP)
        finally:
            file_path.chmod(0o644)  # Restore permissions for cleanup

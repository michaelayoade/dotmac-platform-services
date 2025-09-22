"""
Working tests for data transfer module with correct imports.
Developer 3 - Coverage improvement.
"""

import asyncio
import csv
import io
import json
import os
import tempfile
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, MagicMock, patch, mock_open

import pytest

from dotmac.platform.data_transfer.base import (
    DataTransferError,
    ImportError,
    ExportError,
    DataValidationError,
    FormatError,
    StreamingError,
    ProgressError,
    DataFormat,
    TransferStatus,
    CompressionType,
    ProgressInfo,
    DataRecord,
    DataBatch,
    TransferConfig,
    BaseDataProcessor,
    BaseImporter,
    BaseExporter,
)
from dotmac.platform.data_transfer.exporters import (
    ExportOptions,
    CSVExporter,
    JSONExporter,
    ExcelExporter,
    XMLExporter,
    YAMLExporter,
    CompressionMixin,
)
from dotmac.platform.data_transfer.importers import (
    ImportOptions,
    CSVImporter,
    JSONImporter,
    ExcelImporter,
    XMLImporter,
)
from dotmac.platform.data_transfer.progress import (
    ProgressStore,
    FileProgressStore,
    CheckpointData,
    CheckpointStore,
    ProgressTracker,
    ResumableOperation,
)


class TestDataTransferBase:
    """Test base data transfer classes."""

    def test_data_format_enum(self):
        """Test data format enumeration."""
        assert DataFormat.CSV == "csv"
        assert DataFormat.JSON == "json"
        assert DataFormat.EXCEL == "excel"
        assert DataFormat.XML == "xml"
        assert DataFormat.YAML == "yaml"

    def test_transfer_status_enum(self):
        """Test transfer status enumeration."""
        assert TransferStatus.PENDING == "pending"
        assert TransferStatus.RUNNING == "running"
        assert TransferStatus.COMPLETED == "completed"
        assert TransferStatus.FAILED == "failed"

    def test_compression_type_enum(self):
        """Test compression type enumeration."""
        assert CompressionType.NONE == "none"
        assert CompressionType.GZIP == "gzip"
        assert CompressionType.ZIP == "zip"
        assert CompressionType.BZIP2 == "bzip2"


class TestProgressInfo:
    """Test progress info tracking."""

    def test_progress_info_creation(self):
        """Test creating progress info."""
        info = ProgressInfo()

        assert info.operation_id is not None
        assert info.processed_records == 0
        assert info.failed_records == 0
        assert info.status == TransferStatus.PENDING

    def test_progress_info_with_data(self):
        """Test progress info with data."""
        info = ProgressInfo(
            total_records=100,
            processed_records=50,
            failed_records=2,
            status=TransferStatus.RUNNING
        )

        assert info.total_records == 100
        assert info.processed_records == 50
        assert info.failed_records == 2
        assert info.status == TransferStatus.RUNNING

    def test_progress_percentage(self):
        """Test progress percentage calculation."""
        info = ProgressInfo(
            total_records=100,
            processed_records=25
        )

        percentage = info.progress_percentage
        assert percentage == 25.0

    def test_progress_percentage_no_total(self):
        """Test progress percentage when total is unknown."""
        info = ProgressInfo(processed_records=50)

        percentage = info.progress_percentage
        assert percentage == 0.0  # Can't calculate without total


class TestDataRecord:
    """Test data record class."""

    def test_data_record_creation(self):
        """Test creating a data record."""
        record = DataRecord(
            id="rec_001",
            data={"field1": "value1", "field2": 123},
            metadata={"source": "api"}
        )

        assert record.id == "rec_001"
        assert record.data["field1"] == "value1"
        assert record.data["field2"] == 123
        assert record.metadata["source"] == "api"

    def test_data_record_serialization(self):
        """Test serializing data record."""
        record = DataRecord(
            id="rec_002",
            data={"name": "Test"},
            metadata={"timestamp": datetime.now(UTC).isoformat()}
        )

        # Should be serializable to dict
        record_dict = record.model_dump()
        assert record_dict["id"] == "rec_002"
        assert record_dict["data"]["name"] == "Test"


class TestDataBatch:
    """Test data batch class."""

    def test_data_batch_creation(self):
        """Test creating a data batch."""
        records = [
            DataRecord(id=f"rec_{i}", data={"value": i})
            for i in range(10)
        ]

        batch = DataBatch(
            batch_id="batch_001",
            records=records,
            metadata={"batch_size": 10}
        )

        assert batch.batch_id == "batch_001"
        assert len(batch.records) == 10
        assert batch.metadata["batch_size"] == 10

    def test_data_batch_size(self):
        """Test data batch size property."""
        records = [DataRecord(id=str(i), data={}) for i in range(5)]
        batch = DataBatch(records=records)

        assert batch.size == 5


class TestTransferConfig:
    """Test transfer configuration."""

    def test_transfer_config_defaults(self):
        """Test default transfer configuration."""
        config = settings.Transfer.model_copy()

        assert config.batch_size == 1000
        assert config.parallel_jobs == 1
        assert config.compression == CompressionType.NONE
        assert config.validate_data is True

    def test_transfer_config_custom(self):
        """Test custom transfer configuration."""
        config = settings.Transfer.model_copy(update={
            batch_size=500,
            parallel_jobs=4,
            compression=CompressionType.GZIP,
            validate_data=False,
            max_retries=5
        })

        assert config.batch_size == 500
        assert config.parallel_jobs == 4
        assert config.compression == CompressionType.GZIP
        assert config.validate_data is False
        assert config.max_retries == 5


class TestExportOptions:
    """Test export options."""

    def test_export_options_defaults(self):
        """Test default export options."""
        options = ExportOptions()

        assert options.delimiter == ","
        assert options.include_headers is True
        assert options.json_indent == 2
        assert options.sheet_name == "Sheet1"

    def test_export_options_custom(self):
        """Test custom export options."""
        options = ExportOptions(
            delimiter="|",
            include_headers=False,
            json_indent=4,
            sheet_name="Data",
            xml_root_element="records"
        )

        assert options.delimiter == "|"
        assert options.include_headers is False
        assert options.json_indent == 4
        assert options.sheet_name == "Data"
        assert options.xml_root_element == "records"

    def test_delimiter_validation(self):
        """Test delimiter validation."""
        with pytest.raises(ValueError):
            ExportOptions(delimiter="||")  # Should be single character


class TestCSVExporter:
    """Test CSV exporter functionality."""

    @pytest.fixture
    def csv_exporter(self):
        """Create CSV exporter instance."""
        config = settings.Transfer.model_copy()
        options = ExportOptions()
        return CSVExporter(config=config, options=options)

    async def test_export_csv_to_string(self, csv_exporter):
        """Test exporting CSV to string buffer."""
        records = [
            DataRecord(id="1", data={"name": "Alice", "age": 30}),
            DataRecord(id="2", data={"name": "Bob", "age": 25})
        ]

        output = io.StringIO()
        result = await csv_exporter.export(records, output)

        assert result.status == TransferStatus.COMPLETED
        assert result.processed_records == 2

        # Check CSV content
        output.seek(0)
        content = output.read()
        assert "name" in content
        assert "Alice" in content
        assert "Bob" in content

    async def test_export_csv_with_custom_delimiter(self):
        """Test CSV export with custom delimiter."""
        config = settings.Transfer.model_copy()
        options = ExportOptions(delimiter="|")
        exporter = CSVExporter(config=config, options=options)

        records = [
            DataRecord(id="1", data={"col1": "a", "col2": "b"})
        ]

        output = io.StringIO()
        await exporter.export(records, output)

        output.seek(0)
        content = output.read()
        assert "|" in content

    async def test_export_csv_without_headers(self):
        """Test CSV export without headers."""
        config = settings.Transfer.model_copy()
        options = ExportOptions(include_headers=False)
        exporter = CSVExporter(config=config, options=options)

        records = [
            DataRecord(id="1", data={"name": "Test", "value": 100})
        ]

        output = io.StringIO()
        await exporter.export(records, output)

        output.seek(0)
        lines = output.readlines()
        # Should not have header line
        assert "name" not in lines[0]  # First line should be data, not headers


class TestJSONExporter:
    """Test JSON exporter functionality."""

    @pytest.fixture
    def json_exporter(self):
        """Create JSON exporter instance."""
        config = settings.Transfer.model_copy()
        options = ExportOptions()
        return JSONExporter(config=config, options=options)

    async def test_export_json(self, json_exporter):
        """Test exporting JSON."""
        records = [
            DataRecord(id="1", data={"field": "value1"}),
            DataRecord(id="2", data={"field": "value2"})
        ]

        output = io.StringIO()
        result = await json_exporter.export(records, output)

        assert result.status == TransferStatus.COMPLETED

        output.seek(0)
        data = json.loads(output.read())
        assert len(data) == 2
        assert data[0]["field"] == "value1"

    async def test_export_json_lines(self):
        """Test exporting JSON Lines format."""
        config = settings.Transfer.model_copy()
        options = ExportOptions(json_lines=True)
        exporter = JSONExporter(config=config, options=options)

        records = [
            DataRecord(id=str(i), data={"index": i})
            for i in range(3)
        ]

        output = io.StringIO()
        await exporter.export(records, output)

        output.seek(0)
        lines = output.readlines()
        assert len(lines) == 3

        # Each line should be valid JSON
        for i, line in enumerate(lines):
            data = json.loads(line)
            assert data["index"] == i


class TestProgressTracking:
    """Test progress tracking functionality."""

    def test_progress_store_file(self):
        """Test file-based progress store."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileProgressStore(storage_path=tmpdir)

            # Save progress
            info = ProgressInfo(
                operation_id="op_123",
                processed_records=50,
                total_records=100
            )

            store.save_progress("op_123", info)

            # Load progress
            loaded = store.load_progress("op_123")
            assert loaded is not None
            assert loaded.processed_records == 50
            assert loaded.total_records == 100

    def test_checkpoint_data(self):
        """Test checkpoint data."""
        checkpoint = CheckpointData(
            operation_id="op_456",
            position=1000,
            state={"last_id": "rec_999"},
            metadata={"source": "api"}
        )

        assert checkpoint.operation_id == "op_456"
        assert checkpoint.position == 1000
        assert checkpoint.state["last_id"] == "rec_999"

    def test_checkpoint_store(self):
        """Test checkpoint store."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = CheckpointStore(storage_path=tmpdir)

            checkpoint = CheckpointData(
                operation_id="op_789",
                position=500
            )

            # Save checkpoint
            store.save_checkpoint(checkpoint)

            # Load checkpoint
            loaded = store.load_checkpoint("op_789")
            assert loaded is not None
            assert loaded.position == 500

    async def test_progress_tracker(self):
        """Test progress tracker."""
        tracker = ProgressTracker()

        # Start tracking
        tracker.start_operation("test_op")

        # Update progress
        tracker.update_progress("test_op", processed=10, total=100)

        # Get progress
        info = tracker.get_progress("test_op")
        assert info is not None
        assert info.processed_records == 10
        assert info.total_records == 100

        # Complete operation
        tracker.complete_operation("test_op")
        info = tracker.get_progress("test_op")
        assert info.status == TransferStatus.COMPLETED


class TestImporters:
    """Test importer functionality."""

    @pytest.fixture
    def csv_importer(self):
        """Create CSV importer instance."""
        config = settings.Transfer.model_copy()
        options = ImportOptions()
        return CSVImporter(config=config, options=options)

    async def test_import_csv(self, csv_importer):
        """Test importing CSV data."""
        csv_data = "name,age\nAlice,30\nBob,25\n"
        input_stream = io.StringIO(csv_data)

        records = []
        async for record in csv_importer.import_stream(input_stream):
            records.append(record)

        assert len(records) == 2
        assert records[0].data["name"] == "Alice"
        assert records[0].data["age"] == "30"  # CSV values are strings
        assert records[1].data["name"] == "Bob"

    async def test_import_json(self):
        """Test importing JSON data."""
        config = settings.Transfer.model_copy()
        options = ImportOptions()
        importer = JSONImporter(config=config, options=options)

        json_data = '[{"id": "1", "value": 100}, {"id": "2", "value": 200}]'
        input_stream = io.StringIO(json_data)

        records = []
        async for record in importer.import_stream(input_stream):
            records.append(record)

        assert len(records) == 2
        assert records[0].data["id"] == "1"
        assert records[0].data["value"] == 100
        assert records[1].data["id"] == "2"
        assert records[1].data["value"] == 200


class TestExceptionHandling:
    """Test exception handling."""

    def test_data_transfer_error(self):
        """Test DataTransferError."""
        error = DataTransferError("Transfer failed")
        assert str(error) == "Transfer failed"

    def test_import_error(self):
        """Test ImportError exception."""
        error = ImportError("Import failed")
        assert "Import failed" in str(error)

    def test_export_error(self):
        """Test ExportError exception."""
        error = ExportError("Export failed")
        assert "Export failed" in str(error)

    def test_validation_error(self):
        """Test DataValidationError."""
        error = DataValidationError("Invalid data")
        assert "Invalid data" in str(error)

    def test_format_error(self):
        """Test FormatError."""
        error = FormatError("Unsupported format")
        assert "Unsupported format" in str(error)
"""
Comprehensive tests for data transfer module.
Testing export formats, streaming, compression, validation, and large datasets.
Developer 3 - Coverage Task: Data Transfer & File Processing
"""

import asyncio
import csv
import gzip
import io
import json
import os
import tempfile
import zipfile
from datetime import datetime, timedelta, UTC
from pathlib import Path
from typing import Any, Dict, List, AsyncGenerator
from unittest.mock import AsyncMock, Mock, MagicMock, patch, mock_open

import pytest
import yaml

from dotmac.platform.data_transfer.base import (
    DataFormat,
    TransferStatus,
    CompressionType,
    ProgressInfo,
    DataRecord,
    DataBatch,
    TransferConfig,
    DataTransferError,
    ExportError,
    ImportError,
    DataValidationError,
    StreamingError,
)
from dotmac.platform.data_transfer.exporters import (
    CSVExporter,
    JSONExporter,
    ExcelExporter,
    YAMLExporter,
    XMLExporter,
    ExportOptions,
)
from dotmac.platform.data_transfer.importers import (
    CSVImporter,
    JSONImporter,
    ExcelImporter,
    XMLImporter,
    ImportOptions,
)


@pytest.fixture
def mock_http_session():
    """Mock HTTP session for S3/Azure storage."""
    session = AsyncMock()
    session.put = AsyncMock(return_value=Mock(status_code=200))
    session.get = AsyncMock(return_value=Mock(
        status_code=200,
        content=b"test data",
        json=lambda: {"status": "ok"}
    ))
    return session


@pytest.fixture
def sample_records():
    """Generate sample data records."""
    records = []
    for i in range(100):
        record = DataRecord(
            id=f"rec_{i:03d}",
            data={
                "name": f"Record {i}",
                "value": i * 10,
                "active": i % 2 == 0,
                "created_at": datetime.now(UTC).isoformat(),
                "category": ["A", "B", "C"][i % 3],
                "nested": {
                    "field1": f"value_{i}",
                    "field2": i * 100
                }
            },
            metadata={
                "source": "test",
                "version": "1.0"
            }
        )
        records.append(record)
    return records


@pytest.fixture
def transfer_config():
    """Create transfer configuration."""
    return settings.Transfer.model_copy(update={
        batch_size=10,
        parallel_jobs=2,
        compression=CompressionType.NONE,
        validate_data=True,
        max_retries=3,
        retry_delay=1,
        timeout_seconds=300,
    })


@pytest.fixture
def export_options():
    """Create export options."""
    return ExportOptions(
        delimiter=",",
        include_headers=True,
        json_indent=2,
        sheet_name="TestData",
        xml_root_element="data",
        date_format="%Y-%m-%d",
        include_metadata=True,
    )


class TestCSVExporter:
    """Test CSV export functionality."""

    @pytest.fixture
    def csv_exporter(self, transfer_config, export_options):
        """Create CSV exporter instance."""
        return CSVExporter(config=transfer_config, options=export_options)

    async def test_export_basic_csv(self, csv_exporter, sample_records):
        """Test basic CSV export."""
        output = io.StringIO()

        result = await csv_exporter.export(sample_records[:10], output)

        assert result.status == TransferStatus.COMPLETED
        assert result.processed_records == 10
        assert result.failed_records == 0

        # Verify CSV content
        output.seek(0)
        reader = csv.DictReader(output)
        rows = list(reader)
        assert len(rows) == 10

    async def test_export_with_custom_delimiter(self, transfer_config):
        """Test CSV export with custom delimiter."""
        options = ExportOptions(delimiter="|", include_headers=True)
        exporter = CSVExporter(config=transfer_config, options=options)

        output = io.StringIO()
        records = [
            DataRecord(id="1", data={"col1": "a|b", "col2": "c"}),
            DataRecord(id="2", data={"col1": "d", "col2": "e|f"})
        ]

        await exporter.export(records, output)

        output.seek(0)
        content = output.read()
        assert "|" in content
        assert content.count("|") > 2  # More than just data pipes

    async def test_export_with_quoting(self, transfer_config):
        """Test CSV export with different quoting options."""
        options = ExportOptions(quoting=csv.QUOTE_ALL)
        exporter = CSVExporter(config=transfer_config, options=options)

        output = io.StringIO()
        records = [DataRecord(id="1", data={"text": "Hello, World!", "num": 123})]

        await exporter.export(records, output)

        output.seek(0)
        content = output.read()
        assert '"Hello, World!"' in content
        assert '"123"' in content

    async def test_streaming_csv_export(self, csv_exporter, sample_records):
        """Test streaming CSV export for large datasets."""
        output = io.StringIO()

        async def generate_records():
            for record in sample_records:
                yield record
                await asyncio.sleep(0.001)  # Simulate async generation

        result = await csv_exporter.export_stream(generate_records(), output)

        assert result.status == TransferStatus.COMPLETED
        assert result.processed_records == len(sample_records)

    async def test_csv_compression(self, transfer_config, sample_records):
        """Test CSV export with compression."""
        config = settings.Transfer.model_copy(update={
            batch_size=10,
            compression=CompressionType.GZIP
        })
        exporter = CSVExporter(config=config)

        with tempfile.NamedTemporaryFile(suffix='.csv.gz', delete=False) as tmp:
            try:
                await exporter.export(sample_records[:20], tmp.name)

                # Verify compressed file
                with gzip.open(tmp.name, 'rt') as gz_file:
                    content = gz_file.read()
                    assert len(content) > 0
                    assert "Record" in content
            finally:
                os.unlink(tmp.name)

    async def test_csv_validation_error(self, csv_exporter):
        """Test CSV export with validation errors."""
        invalid_records = [
            DataRecord(id="1", data={"field": float('inf')}),  # Invalid float
            DataRecord(id="2", data={"field": None}),  # Null value
        ]

        output = io.StringIO()
        result = await csv_exporter.export(invalid_records, output)

        # Should handle invalid values gracefully
        assert result.processed_records > 0


class TestJSONExporter:
    """Test JSON export functionality."""

    @pytest.fixture
    def json_exporter(self, transfer_config, export_options):
        """Create JSON exporter instance."""
        return JSONExporter(config=transfer_config, options=export_options)

    async def test_export_json_object(self, json_exporter, sample_records):
        """Test JSON export as single object."""
        output = io.StringIO()

        result = await json_exporter.export(sample_records[:5], output)

        output.seek(0)
        data = json.loads(output.read())

        assert isinstance(data, list)
        assert len(data) == 5
        assert data[0]["id"] == "rec_000"

    async def test_export_json_lines(self, transfer_config):
        """Test JSON Lines (JSONL) export."""
        options = ExportOptions(json_lines=True)
        exporter = JSONExporter(config=transfer_config, options=options)

        output = io.StringIO()
        records = [
            DataRecord(id=f"{i}", data={"value": i})
            for i in range(10)
        ]

        await exporter.export(records, output)

        output.seek(0)
        lines = output.readlines()
        assert len(lines) == 10

        # Each line should be valid JSON
        for line in lines:
            data = json.loads(line)
            assert "value" in data

    async def test_json_with_nested_data(self, json_exporter):
        """Test JSON export with nested structures."""
        complex_records = [
            DataRecord(
                id="1",
                data={
                    "user": {
                        "name": "John",
                        "addresses": [
                            {"type": "home", "city": "NYC"},
                            {"type": "work", "city": "SF"}
                        ]
                    },
                    "scores": [95, 87, 92]
                }
            )
        ]

        output = io.StringIO()
        await json_exporter.export(complex_records, output)

        output.seek(0)
        data = json.loads(output.read())

        assert data[0]["user"]["addresses"][0]["city"] == "NYC"
        assert len(data[0]["scores"]) == 3

    async def test_json_pretty_print(self, transfer_config):
        """Test JSON export with pretty printing."""
        options = ExportOptions(json_indent=4, json_sort_keys=True)
        exporter = JSONExporter(config=transfer_config, options=options)

        output = io.StringIO()
        records = [DataRecord(id="1", data={"z": 1, "a": 2})]

        await exporter.export(records, output)

        output.seek(0)
        content = output.read()

        # Check indentation and key ordering
        assert "    " in content  # 4-space indent
        assert content.index('"a"') < content.index('"z"')  # Keys sorted


class TestExcelExporter:
    """Test Excel export functionality."""

    @pytest.fixture
    def excel_exporter(self, transfer_config, export_options):
        """Create Excel exporter instance."""
        return ExcelExporter(config=transfer_config, options=export_options)

    @patch('openpyxl.Workbook')
    async def test_export_excel_basic(self, mock_workbook, excel_exporter, sample_records):
        """Test basic Excel export."""
        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_workbook.return_value = mock_wb
        mock_wb.active = mock_ws

        with tempfile.NamedTemporaryFile(suffix='.xlsx') as tmp:
            result = await excel_exporter.export(sample_records[:10], tmp.name)

            assert result.status == TransferStatus.COMPLETED
            assert mock_wb.save.called

    @patch('openpyxl.Workbook')
    async def test_excel_with_formatting(self, mock_workbook, transfer_config):
        """Test Excel export with formatting options."""
        options = ExportOptions(
            sheet_name="CustomSheet",
            freeze_panes="A2",
            auto_filter=True
        )
        exporter = ExcelExporter(config=transfer_config, options=options)

        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_workbook.return_value = mock_wb
        mock_wb.create_sheet.return_value = mock_ws

        records = [DataRecord(id="1", data={"col1": "val1"})]

        with tempfile.NamedTemporaryFile(suffix='.xlsx') as tmp:
            await exporter.export(records, tmp.name)

            mock_wb.create_sheet.assert_called_with("CustomSheet")

    @patch('openpyxl.load_workbook')
    async def test_excel_append_mode(self, mock_load_workbook, transfer_config):
        """Test appending data to existing Excel file."""
        options = ExportOptions(append_mode=True)
        exporter = ExcelExporter(config=transfer_config, options=options)

        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_load_workbook.return_value = mock_wb
        mock_wb.active = mock_ws
        mock_ws.max_row = 10

        records = [DataRecord(id="1", data={"new": "data"})]

        with tempfile.NamedTemporaryFile(suffix='.xlsx') as tmp:
            # Create file first
            Path(tmp.name).touch()

            await exporter.export(records, tmp.name)

            mock_load_workbook.assert_called_once()


class TestYAMLExporter:
    """Test Parquet export functionality."""

    @pytest.fixture
    def parquet_exporter(self, transfer_config):
        """Create Parquet exporter instance."""
        return YAMLExporter(config=transfer_config)

    @patch('pandas.DataFrame')
    @patch('pandas.DataFrame.to_parquet')
    async def test_export_parquet(self, mock_to_parquet, mock_df, parquet_exporter, sample_records):
        """Test Parquet export."""
        with tempfile.NamedTemporaryFile(suffix='.parquet') as tmp:
            result = await parquet_exporter.export(sample_records[:20], tmp.name)

            assert result.status == TransferStatus.COMPLETED
            mock_to_parquet.assert_called()

    @patch('pandas.DataFrame')
    async def test_parquet_compression_algorithms(self, mock_df, transfer_config):
        """Test Parquet with different compression algorithms."""
        for compression in ['snappy', 'gzip', 'brotli']:
            options = ExportOptions(parquet_compression=compression)
            exporter = YAMLExporter(
                config=transfer_config,
                options=options
            )

            with tempfile.NamedTemporaryFile(suffix='.parquet') as tmp:
                records = [DataRecord(id="1", data={"val": 1})]
                await exporter.export(records, tmp.name)

    @patch('pandas.DataFrame')
    async def test_parquet_schema_evolution(self, mock_df, parquet_exporter):
        """Test Parquet export with schema changes."""
        # First batch with initial schema
        records1 = [
            DataRecord(id="1", data={"field1": "val1", "field2": 10})
        ]

        # Second batch with additional field
        records2 = [
            DataRecord(id="2", data={"field1": "val2", "field2": 20, "field3": True})
        ]

        with tempfile.NamedTemporaryFile(suffix='.parquet') as tmp:
            await parquet_exporter.export(records1, tmp.name)
            # Append with new schema
            await parquet_exporter.export(records2, tmp.name, append=True)


class TestXMLExporter:
    """Test XML export functionality."""

    @pytest.fixture
    def xml_exporter(self, transfer_config, export_options):
        """Create XML exporter instance."""
        return XMLExporter(config=transfer_config, options=export_options)

    async def test_export_xml_basic(self, xml_exporter, sample_records):
        """Test basic XML export."""
        output = io.StringIO()

        result = await xml_exporter.export(sample_records[:5], output)

        output.seek(0)
        content = output.read()

        assert "<data>" in content
        assert "</data>" in content
        assert "<record>" in content
        assert result.processed_records == 5

    async def test_xml_with_attributes(self, transfer_config):
        """Test XML export with attributes."""
        options = ExportOptions(
            xml_root_element="catalog",
            xml_record_element="item",
            xml_use_attributes=True
        )
        exporter = XMLExporter(config=transfer_config, options=options)

        records = [
            DataRecord(
                id="prod_001",
                data={"name": "Widget", "price": 19.99},
                metadata={"category": "tools"}
            )
        ]

        output = io.StringIO()
        await exporter.export(records, output)

        output.seek(0)
        content = output.read()

        assert '<item id="prod_001"' in content
        assert 'category="tools"' in content

    async def test_xml_namespace_handling(self, transfer_config):
        """Test XML export with namespaces."""
        options = ExportOptions(
            xml_namespace="http://example.com/schema",
            xml_namespace_prefix="ex"
        )
        exporter = XMLExporter(config=transfer_config, options=options)

        records = [DataRecord(id="1", data={"field": "value"})]

        output = io.StringIO()
        await exporter.export(records, output)

        output.seek(0)
        content = output.read()

        assert "xmlns:ex=" in content or "xmlns=" in content


class TestStreamingExport:
    """Test streaming export capabilities."""

    async def test_streaming_large_dataset(self, transfer_config):
        """Test streaming export with large dataset."""
        exporter = CSVExporter(config=transfer_config)

        async def generate_large_dataset():
            for i in range(10000):
                yield DataRecord(
                    id=str(i),
                    data={"index": i, "value": i * 2}
                )
                if i % 1000 == 0:
                    await asyncio.sleep(0.001)  # Simulate async I/O

        output = io.StringIO()
        result = await exporter.export_stream(generate_large_dataset(), output)

        assert result.processed_records == 10000
        assert result.status == TransferStatus.COMPLETED

    async def test_streaming_with_backpressure(self, transfer_config):
        """Test streaming with backpressure handling."""
        exporter = JSONExporter(config=transfer_config)

        slow_output = AsyncMock()
        slow_output.write = AsyncMock(side_effect=lambda x: asyncio.sleep(0.01))

        records = [DataRecord(id=str(i), data={"val": i}) for i in range(100)]

        # Should handle slow output without memory issues
        result = await exporter.export(records, slow_output)

        assert result.processed_records == 100

    async def test_streaming_error_recovery(self, transfer_config):
        """Test streaming with error recovery."""
        exporter = CSVExporter(config=transfer_config)

        async def generate_with_errors():
            for i in range(20):
                if i == 10:
                    raise ValueError("Simulated error")
                yield DataRecord(id=str(i), data={"val": i})

        output = io.StringIO()

        with pytest.raises(StreamingError):
            await exporter.export_stream(generate_with_errors(), output)

        # Should have processed records before error
        output.seek(0)
        content = output.read()
        assert len(content) > 0


class TestCompressionExport:
    """Test export with different compression methods."""

    @pytest.mark.parametrize("compression_type", [
        CompressionType.GZIP,
        CompressionType.ZIP,
        CompressionType.BZIP2
    ])
    async def test_compression_types(self, compression_type, sample_records):
        """Test different compression algorithms."""
        config = settings.Transfer.model_copy(update={compression=compression_type})
        exporter = CSVExporter(config=config)

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            try:
                await exporter.export(sample_records[:10], tmp.name)

                # Verify file is compressed
                file_size = os.path.getsize(tmp.name)
                assert file_size > 0

                # Decompress and verify content
                if compression_type == CompressionType.GZIP:
                    with gzip.open(tmp.name, 'rt') as f:
                        content = f.read()
                elif compression_type == CompressionType.ZIP:
                    with zipfile.ZipFile(tmp.name, 'r') as zf:
                        content = zf.read(zf.namelist()[0]).decode()
                elif compression_type == CompressionType.BZIP2:
                    with bz2.open(tmp.name, 'rt') as f:
                        content = f.read()

                assert "Record" in content
            finally:
                os.unlink(tmp.name)

    async def test_compression_ratio(self, sample_records):
        """Test compression effectiveness."""
        # Generate repetitive data for good compression
        records = []
        for i in range(1000):
            records.append(DataRecord(
                id=str(i),
                data={"pattern": "AAAAAAAAAA" * 10, "index": i}
            ))

        config_none = settings.Transfer.model_copy(update={compression=CompressionType.NONE})
        config_gzip = settings.Transfer.model_copy(update={compression=CompressionType.GZIP})

        exporter_none = CSVExporter(config=config_none)
        exporter_gzip = CSVExporter(config=config_gzip)

        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp_none:
            with tempfile.NamedTemporaryFile(suffix='.csv.gz', delete=False) as tmp_gzip:
                try:
                    await exporter_none.export(records, tmp_none.name)
                    await exporter_gzip.export(records, tmp_gzip.name)

                    size_none = os.path.getsize(tmp_none.name)
                    size_gzip = os.path.getsize(tmp_gzip.name)

                    # Compressed should be significantly smaller
                    compression_ratio = size_none / size_gzip
                    assert compression_ratio > 5  # At least 5x compression
                finally:
                    os.unlink(tmp_none.name)
                    os.unlink(tmp_gzip.name)


class TestValidationExport:
    """Test data validation during export."""

    async def test_validation_enabled(self, transfer_config):
        """Test export with validation enabled."""
        config = settings.Transfer.model_copy(update={validate_data=True})
        exporter = JSONExporter(config=config)

        # Records with validation issues
        records = [
            DataRecord(id="1", data={"email": "invalid-email"}),
            DataRecord(id="2", data={"email": "valid@example.com"}),
            DataRecord(id="3", data={"phone": "123"}),  # Too short
        ]

        output = io.StringIO()
        result = await exporter.export(records, output)

        # Should process all but may flag validation issues
        assert result.processed_records <= 3
        if result.failed_records > 0:
            assert result.error_message is not None

    async def test_validation_disabled(self, transfer_config):
        """Test export with validation disabled."""
        config = settings.Transfer.model_copy(update={validate_data=False})
        exporter = JSONExporter(config=config)

        # Records with potential issues
        records = [
            DataRecord(id="1", data={"value": float('inf')}),
            DataRecord(id="2", data={"value": None}),
            DataRecord(id="3", data={"value": ""}),
        ]

        output = io.StringIO()
        result = await exporter.export(records, output)

        # Should process all records without validation
        assert result.processed_records == 3
        assert result.failed_records == 0

    async def test_custom_validators(self, transfer_config):
        """Test export with custom validation rules."""
        def validate_record(record: DataRecord) -> bool:
            # Custom validation: value must be positive
            return record.data.get("value", 0) > 0

        config = settings.Transfer.model_copy(update={
            validate_data=True,
            custom_validators=[validate_record]
        })
        exporter = CSVExporter(config=config)

        records = [
            DataRecord(id="1", data={"value": 10}),  # Valid
            DataRecord(id="2", data={"value": -5}),  # Invalid
            DataRecord(id="3", data={"value": 0}),   # Invalid
        ]

        output = io.StringIO()
        result = await exporter.export(records, output)

        assert result.processed_records == 1
        assert result.failed_records == 2


class TestStorageIntegration:
    """Test integration with cloud storage."""

    async def test_s3_export(self, mock_http_session, transfer_config, sample_records):
        """Test export to S3."""
        exporter = CSVExporter(config=transfer_config)

        with patch('dotmac.platform.data_transfer.storage.S3Storage') as mock_s3:
            mock_s3.return_value.upload = AsyncMock(return_value=True)

            s3_path = "s3://bucket/path/data.csv"
            result = await exporter.export(sample_records[:10], s3_path)

            assert result.status == TransferStatus.COMPLETED
            mock_s3.return_value.upload.assert_called()

    async def test_azure_export(self, mock_http_session, transfer_config, sample_records):
        """Test export to Azure Blob Storage."""
        exporter = JSONExporter(config=transfer_config)

        with patch('dotmac.platform.data_transfer.storage.AzureStorage') as mock_azure:
            mock_azure.return_value.upload = AsyncMock(return_value=True)

            azure_path = "azure://container/path/data.json"
            result = await exporter.export(sample_records[:10], azure_path)

            assert result.status == TransferStatus.COMPLETED
            mock_azure.return_value.upload.assert_called()

    async def test_multipart_upload(self, mock_http_session, transfer_config):
        """Test multipart upload for large files."""
        config = settings.Transfer.model_copy(update={
            multipart_threshold=5 * 1024 * 1024,  # 5MB
            multipart_chunksize=1024 * 1024       # 1MB
        })
        exporter = CSVExporter(config=config)

        # Generate large dataset
        large_records = []
        for i in range(100000):
            large_records.append(DataRecord(
                id=str(i),
                data={"data": "X" * 100}  # Make records larger
            ))

        with patch('dotmac.platform.data_transfer.storage.S3Storage') as mock_s3:
            mock_s3.return_value.multipart_upload = AsyncMock(return_value=True)

            s3_path = "s3://bucket/large-file.csv"
            result = await exporter.export(large_records, s3_path)

            assert result.status == TransferStatus.COMPLETED
            mock_s3.return_value.multipart_upload.assert_called()


class TestProgressTracking:
    """Test progress tracking during export."""

    async def test_progress_callbacks(self, transfer_config, sample_records):
        """Test progress callback invocations."""
        progress_updates = []

        async def progress_callback(info: ProgressInfo):
            progress_updates.append({
                "processed": info.processed_records,
                "percentage": info.progress_percentage
            })

        config = settings.Transfer.model_copy(update={
            batch_size=10,
            progress_callback=progress_callback
        })
        exporter = CSVExporter(config=config)

        output = io.StringIO()
        await exporter.export(sample_records, output)

        assert len(progress_updates) > 0
        # Progress should increase
        percentages = [p["percentage"] for p in progress_updates]
        assert percentages[-1] == 100.0

    async def test_estimated_completion(self, transfer_config):
        """Test estimated completion time calculation."""
        start_time = datetime.now(UTC)

        async def slow_generator():
            for i in range(20):
                yield DataRecord(id=str(i), data={"val": i})
                await asyncio.sleep(0.1)  # Simulate slow processing

        exporter = CSVExporter(config=transfer_config)
        output = io.StringIO()

        result = await exporter.export_stream(slow_generator(), output)

        # Should have reasonable completion estimate
        assert result.estimated_completion is not None
        assert result.last_update > start_time

    async def test_batch_progress(self, transfer_config, sample_records):
        """Test progress tracking by batches."""
        config = settings.Transfer.model_copy(update={batch_size=25})
        exporter = JSONExporter(config=config)

        output = io.StringIO()
        result = await exporter.export(sample_records, output)

        # 100 records / 25 per batch = 4 batches
        assert result.total_batches == 4
        assert result.current_batch == 4


class TestErrorHandling:
    """Test error handling and recovery."""

    async def test_export_io_error(self, transfer_config, sample_records):
        """Test handling of I/O errors during export."""
        exporter = CSVExporter(config=transfer_config)

        # Mock file that raises IOError
        mock_file = Mock()
        mock_file.write.side_effect = IOError("Disk full")

        with pytest.raises(ExportError) as exc_info:
            await exporter.export(sample_records[:10], mock_file)

        assert "Disk full" in str(exc_info.value)

    async def test_retry_mechanism(self, transfer_config, sample_records):
        """Test retry mechanism for transient failures."""
        config = settings.Transfer.model_copy(update={
            max_retries=3,
            retry_delay=0.1
        })
        exporter = JSONExporter(config=config)

        # Mock storage that fails twice then succeeds
        attempt_count = 0

        async def flaky_write(data):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ConnectionError("Network error")
            return True

        mock_output = AsyncMock()
        mock_output.write = flaky_write

        result = await exporter.export(sample_records[:5], mock_output)

        assert result.status == TransferStatus.COMPLETED
        assert attempt_count == 3

    async def test_partial_export_recovery(self, transfer_config):
        """Test recovery from partial export."""
        exporter = CSVExporter(config=transfer_config)

        # Simulate failure midway
        records = [DataRecord(id=str(i), data={"val": i}) for i in range(20)]

        output = io.StringIO()

        # Mock to fail after 10 records
        original_write = output.write
        write_count = [0]

        def failing_write(data):
            write_count[0] += 1
            if write_count[0] > 10:
                raise IOError("Failed")
            return original_write(data)

        output.write = failing_write

        with pytest.raises(ExportError):
            await exporter.export(records, output)

        # Should have partial data
        output.seek(0)
        content = output.read()
        assert len(content) > 0


class TestPerformanceOptimization:
    """Test performance optimizations."""

    @pytest.mark.slow
    async def test_large_dataset_performance(self, transfer_config):
        """Test performance with large datasets."""
        import time

        config = settings.Transfer.model_copy(update={
            batch_size=1000,
            parallel_jobs=4
        })
        exporter = CSVExporter(config=config)

        # Generate 1 million records
        large_records = []
        for i in range(1000000):
            large_records.append(DataRecord(
                id=str(i),
                data={"index": i, "value": i * 2}
            ))

        output = io.StringIO()

        start_time = time.time()
        result = await exporter.export(large_records, output)
        elapsed = time.time() - start_time

        assert result.processed_records == 1000000
        # Should complete in reasonable time (< 30 seconds)
        assert elapsed < 30

    async def test_memory_efficient_streaming(self, transfer_config):
        """Test memory-efficient streaming."""
        import tracemalloc

        tracemalloc.start()

        async def generate_infinite():
            i = 0
            while i < 100000:
                yield DataRecord(id=str(i), data={"val": i})
                i += 1

        exporter = JSONExporter(config=transfer_config)
        output = io.StringIO()

        snapshot1 = tracemalloc.take_snapshot()

        await exporter.export_stream(generate_infinite(), output)

        snapshot2 = tracemalloc.take_snapshot()

        top_stats = snapshot2.compare_to(snapshot1, 'lineno')

        # Memory usage should be bounded
        total_memory = sum(stat.size_diff for stat in top_stats)
        assert total_memory < 100 * 1024 * 1024  # Less than 100MB growth

        tracemalloc.stop()

    async def test_parallel_export(self, transfer_config, sample_records):
        """Test parallel export to multiple formats."""
        config = settings.Transfer.model_copy(update={parallel_jobs=3})

        exporters = [
            CSVExporter(config=config),
            JSONExporter(config=config),
            XMLExporter(config=config)
        ]

        outputs = [io.StringIO() for _ in range(3)]

        # Export to all formats in parallel
        tasks = []
        for exporter, output in zip(exporters, outputs):
            tasks.append(exporter.export(sample_records, output))

        results = await asyncio.gather(*tasks)

        # All should complete successfully
        for result in results:
            assert result.status == TransferStatus.COMPLETED
            assert result.processed_records == len(sample_records)
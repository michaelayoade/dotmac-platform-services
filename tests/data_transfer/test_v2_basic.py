"""
Basic tests for the new pandas-based data transfer module.
"""

import asyncio
import tempfile
from pathlib import Path
import pandas as pd
import pytest

from dotmac.platform.data_transfer import (
    DataFormat,
    TransferConfig,
    ImportOptions,
    ExportOptions,
    DataRecord,
    DataBatch,
    import_file,
    export_data,
    convert_file,
    CSVImporter,
    JSONExporter,
    create_batches,
)


@pytest.fixture
def sample_csv_data():
    """Create sample CSV data."""
    return """name,age,city
Alice,30,New York
Bob,25,Los Angeles
Charlie,35,Chicago"""


@pytest.fixture
def sample_json_data():
    """Create sample JSON data."""
    return [
        {"name": "Alice", "age": 30, "city": "New York"},
        {"name": "Bob", "age": 25, "city": "Los Angeles"},
        {"name": "Charlie", "age": 35, "city": "Chicago"},
    ]


class TestBasicDataTransfer:
    """Test basic data transfer functionality."""

    def test_data_record_creation(self):
        """Test DataRecord creation."""
        record = DataRecord(data={"name": "Alice", "age": 30})
        assert record.data["name"] == "Alice"
        assert record.data["age"] == 30
        assert record.metadata == {}

    def test_data_batch_creation(self):
        """Test DataBatch creation."""
        records = [
            DataRecord(data={"name": "Alice"}),
            DataRecord(data={"name": "Bob"}),
        ]
        batch = DataBatch(records=records, batch_number=0)
        assert batch.size == 2
        assert batch.batch_number == 0

    def test_transfer_config(self):
        """Test TransferConfig creation."""
        config = settings.Transfer.model_copy(update={batch_size=500, encoding="utf-8"})
        assert config.batch_size == 500
        assert config.encoding == "utf-8"
        assert config.validate_data is True

    @pytest.mark.asyncio
    async def test_csv_import(self, sample_csv_data):
        """Test CSV import functionality."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(sample_csv_data)
            csv_path = Path(f.name)

        try:
            config = settings.Transfer.model_copy(update={batch_size=2})
            importer = CSVImporter(config, ImportOptions())

            batches = []
            async for batch in importer.import_from_file(csv_path):
                batches.append(batch)

            assert len(batches) == 2  # 3 records with batch_size=2
            assert batches[0].size == 2
            assert batches[1].size == 1

            # Check data content
            first_record = batches[0].records[0].data
            assert first_record["name"] == "Alice"
            assert first_record["age"] == 30
        finally:
            csv_path.unlink()

    @pytest.mark.asyncio
    async def test_json_export(self, sample_json_data):
        """Test JSON export functionality."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            json_path = Path(f.name)

        try:
            # Create batches from sample data
            async def data_generator():
                records = [DataRecord(data=item) for item in sample_json_data]
                yield DataBatch(records=records, batch_number=0)

            config = settings.Transfer.model_copy()
            exporter = JSONExporter(config, ExportOptions())

            progress = await exporter.export_to_file(data_generator(), json_path)

            assert progress.processed_records == 3
            assert json_path.exists()

            # Verify exported data
            df = pd.read_json(json_path)
            assert len(df) == 3
            assert df.iloc[0]["name"] == "Alice"
        finally:
            json_path.unlink()

    @pytest.mark.asyncio
    async def test_file_conversion(self, sample_csv_data):
        """Test file format conversion."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(sample_csv_data)
            csv_path = f.name

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            json_path = f.name

        try:
            # Convert CSV to JSON
            progress = await convert_file(
                source_path=csv_path,
                target_path=json_path,
                source_format=DataFormat.CSV,
                target_format=DataFormat.JSON,
                batch_size=10,
            )

            assert Path(json_path).exists()

            # Verify conversion
            df = pd.read_json(json_path)
            assert len(df) == 3
            assert "name" in df.columns
            assert "age" in df.columns
            assert "city" in df.columns
        finally:
            Path(csv_path).unlink()
            Path(json_path).unlink()

    @pytest.mark.asyncio
    async def test_create_batches_utility(self):
        """Test create_batches utility function."""
        data = [
            {"id": 1, "value": "a"},
            {"id": 2, "value": "b"},
            {"id": 3, "value": "c"},
            {"id": 4, "value": "d"},
            {"id": 5, "value": "e"},
        ]

        batches = []
        async for batch in create_batches(data, batch_size=2):
            batches.append(batch)

        assert len(batches) == 3
        assert batches[0].size == 2
        assert batches[1].size == 2
        assert batches[2].size == 1
        assert batches[0].batch_number == 0
        assert batches[1].batch_number == 1
        assert batches[2].batch_number == 2
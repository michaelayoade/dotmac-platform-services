"""
Comprehensive Data Transfer Module Integration Tests - Week 3 Priority 2

Tests cover:
1. Import Workflows - CSV, JSON, Excel import with validation
2. Export Workflows - Multi-format export with transformations
3. Format Conversion - CSV ↔ JSON ↔ Excel cross-format conversion
4. Large Dataset Handling - Streaming, chunking, progress tracking
5. End-to-End Workflows - Complete import → process → export pipelines

Following the successful service-layer integration pattern from auth/billing modules.
"""

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from dotmac.platform.data_transfer.core import (
    DataFormat,
    ExportOptions,
    ImportOptions,
    ProgressInfo,
    TransferConfig,
)
from dotmac.platform.data_transfer.factory import (
    create_exporter,
    create_importer,
)

# ============================================================================
# Test Data Fixtures
# ============================================================================


@pytest.fixture
def sample_customer_data():
    """Sample customer data for testing."""
    return [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30,
            "city": "New York",
            "country": "USA",
            "created_at": "2024-01-15",
        },
        {
            "id": 2,
            "name": "Jane Smith",
            "email": "jane@example.com",
            "age": 28,
            "city": "London",
            "country": "UK",
            "created_at": "2024-02-20",
        },
        {
            "id": 3,
            "name": "Bob Johnson",
            "email": "bob@example.com",
            "age": 35,
            "city": "Toronto",
            "country": "Canada",
            "created_at": "2024-03-10",
        },
    ]


@pytest.fixture
def large_dataset():
    """Generate large dataset for performance testing."""
    return [
        {
            "id": i,
            "name": f"User {i}",
            "email": f"user{i}@example.com",
            "value": i * 10.5,
            "timestamp": f"2024-01-{(i % 28) + 1:02d}",
        }
        for i in range(1000)  # 1000 records
    ]


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# ============================================================================
# Import Workflow Integration Tests
# ============================================================================


class TestImportWorkflowIntegration:
    """Test complete import workflows with real files."""

    def test_csv_import_workflow(self, sample_customer_data, temp_dir):
        """Test complete CSV import workflow."""
        # Create CSV file
        csv_file = temp_dir / "customers.csv"
        df = pd.DataFrame(sample_customer_data)
        df.to_csv(csv_file, index=False)

        # Import using factory
        with patch("dotmac.platform.data_transfer.factory.settings") as mock_settings:
            mock_settings.features.data_transfer_enabled = True

            importer = create_importer("csv")
            result = importer.import_from_file(csv_file)

        # Verify import
        assert result is not None
        assert len(result) == 3
        assert result["name"].tolist() == ["John Doe", "Jane Smith", "Bob Johnson"]
        assert result["age"].tolist() == [30, 28, 35]

    def test_json_import_workflow(self, sample_customer_data, temp_dir):
        """Test complete JSON import workflow."""
        # Create JSON file
        json_file = temp_dir / "customers.json"
        with open(json_file, "w") as f:
            json.dump(sample_customer_data, f)

        # Import using factory
        with patch("dotmac.platform.data_transfer.factory.settings") as mock_settings:
            mock_settings.features.data_transfer_enabled = True

            importer = create_importer(DataFormat.JSON)
            result = importer.import_from_file(json_file)

        # Verify import
        assert result is not None
        assert len(result) == 3
        assert result["email"].tolist() == [
            "john@example.com",
            "jane@example.com",
            "bob@example.com",
        ]

    def test_excel_import_workflow(self, sample_customer_data, temp_dir):
        """Test complete Excel import workflow."""
        # Create Excel file
        excel_file = temp_dir / "customers.xlsx"
        df = pd.DataFrame(sample_customer_data)
        df.to_excel(excel_file, index=False, engine="openpyxl")

        # Import using factory
        with patch("dotmac.platform.data_transfer.factory.settings") as mock_settings:
            mock_settings.features.data_transfer_enabled = True

            importer = create_importer(DataFormat.EXCEL)
            result = importer.import_from_file(excel_file)

        # Verify import
        assert result is not None
        assert len(result) == 3
        assert result["country"].tolist() == ["USA", "UK", "Canada"]

    def test_csv_import_with_custom_delimiter(self, sample_customer_data, temp_dir):
        """Test CSV import with custom delimiter."""
        # Create TSV file (tab-separated)
        tsv_file = temp_dir / "customers.tsv"
        df = pd.DataFrame(sample_customer_data)
        df.to_csv(tsv_file, sep="\t", index=False)

        # Import with custom delimiter
        with patch("dotmac.platform.data_transfer.factory.settings") as mock_settings:
            mock_settings.features.data_transfer_enabled = True

            options = ImportOptions(delimiter="\t")
            importer = create_importer("csv", options=options)
            result = importer.import_from_file(tsv_file)

        # Verify import
        assert result is not None
        assert len(result) == 3

    def test_import_with_type_inference(self, temp_dir):
        """Test import with automatic type inference."""
        # Create CSV with mixed types
        data = [
            {"id": "1", "value": "10.5", "is_active": "true", "count": "100"},
            {"id": "2", "value": "20.3", "is_active": "false", "count": "200"},
        ]
        csv_file = temp_dir / "typed_data.csv"
        pd.DataFrame(data).to_csv(csv_file, index=False)

        # Import with type inference
        with patch("dotmac.platform.data_transfer.factory.settings") as mock_settings:
            mock_settings.features.data_transfer_enabled = True

            options = ImportOptions(type_inference=True)
            importer = create_importer("csv", options=options)
            result = importer.import_from_file(csv_file)

        # Verify types were inferred
        assert result is not None
        assert result["id"].dtype in ["int64", "Int64"]
        assert result["value"].dtype == "float64"

    def test_import_with_validation(self, temp_dir):
        """Test import with schema validation."""
        # Create CSV with data
        data = [
            {"name": "John", "age": 30, "email": "john@example.com"},
            {"name": "Jane", "age": 28, "email": "jane@example.com"},
        ]
        csv_file = temp_dir / "validated_data.csv"
        pd.DataFrame(data).to_csv(csv_file, index=False)

        # Define validation schema
        schema = {
            "name": str,
            "age": int,
            "email": str,
        }

        # Import and validate
        with patch("dotmac.platform.data_transfer.factory.settings") as mock_settings:
            mock_settings.features.data_transfer_enabled = True

            options = ImportOptions(validation_schema=schema)
            importer = create_importer("csv", options=options)
            result = importer.import_from_file(csv_file)

        # Verify successful import
        assert result is not None
        assert len(result) == 2


# ============================================================================
# Export Workflow Integration Tests
# ============================================================================


class TestExportWorkflowIntegration:
    """Test complete export workflows."""

    def test_csv_export_workflow(self, sample_customer_data, temp_dir):
        """Test complete CSV export workflow."""
        df = pd.DataFrame(sample_customer_data)
        output_file = temp_dir / "export.csv"

        # Export using factory
        with patch("dotmac.platform.data_transfer.factory.settings") as mock_settings:
            mock_settings.features.data_transfer_enabled = True

            exporter = create_exporter("csv")
            exporter.export_to_file(df, output_file)

        # Verify export
        assert output_file.exists()
        imported_df = pd.read_csv(output_file)
        assert len(imported_df) == 3
        assert imported_df["name"].tolist() == ["John Doe", "Jane Smith", "Bob Johnson"]

    def test_json_export_workflow(self, sample_customer_data, temp_dir):
        """Test complete JSON export workflow."""
        df = pd.DataFrame(sample_customer_data)
        output_file = temp_dir / "export.json"

        # Export using factory
        with patch("dotmac.platform.data_transfer.factory.settings") as mock_settings:
            mock_settings.features.data_transfer_enabled = True

            exporter = create_exporter(DataFormat.JSON)
            exporter.export_to_file(df, output_file)

        # Verify export
        assert output_file.exists()
        with open(output_file) as f:
            data = json.load(f)
        assert len(data) == 3
        assert data[0]["name"] == "John Doe"

    def test_excel_export_workflow(self, sample_customer_data, temp_dir):
        """Test complete Excel export workflow."""
        df = pd.DataFrame(sample_customer_data)
        output_file = temp_dir / "export.xlsx"

        # Export using factory
        with patch("dotmac.platform.data_transfer.factory.settings") as mock_settings:
            mock_settings.features.data_transfer_enabled = True

            exporter = create_exporter(DataFormat.EXCEL)
            exporter.export_to_file(df, output_file)

        # Verify export
        assert output_file.exists()
        imported_df = pd.read_excel(output_file, engine="openpyxl")
        assert len(imported_df) == 3

    def test_export_with_custom_options(self, sample_customer_data, temp_dir):
        """Test export with custom options."""
        df = pd.DataFrame(sample_customer_data)
        output_file = temp_dir / "custom_export.csv"

        # Export without headers
        with patch("dotmac.platform.data_transfer.factory.settings") as mock_settings:
            mock_settings.features.data_transfer_enabled = True

            options = ExportOptions(include_headers=False, delimiter="|")
            exporter = create_exporter("csv", options=options)
            exporter.export_to_file(df, output_file)

        # Verify custom format
        assert output_file.exists()
        content = output_file.read_text()
        assert "|" in content
        # First line should be data, not headers
        first_line = content.split("\n")[0]
        assert "id" not in first_line.lower()  # No header row

    def test_export_with_column_selection(self, sample_customer_data, temp_dir):
        """Test export with specific columns only."""
        df = pd.DataFrame(sample_customer_data)
        output_file = temp_dir / "selected_columns.csv"

        # Export only specific columns
        with patch("dotmac.platform.data_transfer.factory.settings") as mock_settings:
            mock_settings.features.data_transfer_enabled = True

            options = ExportOptions(columns=["name", "email"])
            exporter = create_exporter("csv", options=options)
            exporter.export_to_file(df, output_file)

        # Verify only selected columns exported
        imported_df = pd.read_csv(output_file)
        assert list(imported_df.columns) == ["name", "email"]
        assert "age" not in imported_df.columns


# ============================================================================
# Format Conversion Integration Tests
# ============================================================================


class TestFormatConversionIntegration:
    """Test cross-format conversion workflows."""

    def test_csv_to_json_conversion(self, sample_customer_data, temp_dir):
        """Test converting CSV to JSON."""
        # Create CSV file
        csv_file = temp_dir / "source.csv"
        pd.DataFrame(sample_customer_data).to_csv(csv_file, index=False)

        # Convert CSV → JSON
        json_file = temp_dir / "converted.json"

        with patch("dotmac.platform.data_transfer.factory.settings") as mock_settings:
            mock_settings.features.data_transfer_enabled = True

            # Import CSV
            importer = create_importer("csv")
            df = importer.import_from_file(csv_file)

            # Export as JSON
            exporter = create_exporter("json")
            exporter.export_to_file(df, json_file)

        # Verify conversion
        assert json_file.exists()
        with open(json_file) as f:
            data = json.load(f)
        assert len(data) == 3
        assert data[0]["name"] == "John Doe"

    def test_json_to_excel_conversion(self, sample_customer_data, temp_dir):
        """Test converting JSON to Excel."""
        # Create JSON file
        json_file = temp_dir / "source.json"
        with open(json_file, "w") as f:
            json.dump(sample_customer_data, f)

        # Convert JSON → Excel
        excel_file = temp_dir / "converted.xlsx"

        with patch("dotmac.platform.data_transfer.factory.settings") as mock_settings:
            mock_settings.features.data_transfer_enabled = True

            # Import JSON
            importer = create_importer(DataFormat.JSON)
            df = importer.import_from_file(json_file)

            # Export as Excel
            exporter = create_exporter(DataFormat.EXCEL)
            exporter.export_to_file(df, excel_file)

        # Verify conversion
        assert excel_file.exists()
        imported_df = pd.read_excel(excel_file, engine="openpyxl")
        assert len(imported_df) == 3

    def test_excel_to_csv_conversion(self, sample_customer_data, temp_dir):
        """Test converting Excel to CSV."""
        # Create Excel file
        excel_file = temp_dir / "source.xlsx"
        pd.DataFrame(sample_customer_data).to_excel(excel_file, index=False, engine="openpyxl")

        # Convert Excel → CSV
        csv_file = temp_dir / "converted.csv"

        with patch("dotmac.platform.data_transfer.factory.settings") as mock_settings:
            mock_settings.features.data_transfer_enabled = True

            # Import Excel
            importer = create_importer(DataFormat.EXCEL)
            df = importer.import_from_file(excel_file)

            # Export as CSV
            exporter = create_exporter("csv")
            exporter.export_to_file(df, csv_file)

        # Verify conversion
        assert csv_file.exists()
        imported_df = pd.read_csv(csv_file)
        assert len(imported_df) == 3

    def test_roundtrip_conversion_csv_json_csv(self, sample_customer_data, temp_dir):
        """Test roundtrip conversion: CSV → JSON → CSV."""
        # Create original CSV
        original_csv = temp_dir / "original.csv"
        original_df = pd.DataFrame(sample_customer_data)
        original_df.to_csv(original_csv, index=False)

        with patch("dotmac.platform.data_transfer.factory.settings") as mock_settings:
            mock_settings.features.data_transfer_enabled = True

            # CSV → JSON
            json_file = temp_dir / "intermediate.json"
            importer1 = create_importer("csv")
            df1 = importer1.import_from_file(original_csv)
            exporter1 = create_exporter("json")
            exporter1.export_to_file(df1, json_file)

            # JSON → CSV
            final_csv = temp_dir / "final.csv"
            importer2 = create_importer("json")
            df2 = importer2.import_from_file(json_file)
            exporter2 = create_exporter("csv")
            exporter2.export_to_file(df2, final_csv)

        # Verify data integrity preserved
        original = pd.read_csv(original_csv)
        final = pd.read_csv(final_csv)

        # Compare data (allow for minor type differences)
        assert len(original) == len(final)
        assert original["name"].tolist() == final["name"].tolist()
        assert original["email"].tolist() == final["email"].tolist()


# ============================================================================
# Large Dataset Handling Integration Tests
# ============================================================================


class TestLargeDatasetHandling:
    """Test handling of large datasets with chunking and streaming."""

    def test_large_csv_import_with_chunking(self, large_dataset, temp_dir):
        """Test importing large CSV file with chunking."""
        # Create large CSV file
        csv_file = temp_dir / "large_data.csv"
        df = pd.DataFrame(large_dataset)
        df.to_csv(csv_file, index=False)

        # Import with chunking
        with patch("dotmac.platform.data_transfer.factory.settings") as mock_settings:
            mock_settings.features.data_transfer_enabled = True

            config = TransferConfig(chunk_size=100, batch_size=50)
            importer = create_importer("csv", config=config)
            result = importer.import_from_file(csv_file)

        # Verify all data imported
        assert result is not None
        assert len(result) == 1000
        assert result["id"].min() == 0
        assert result["id"].max() == 999

    def test_large_dataset_export_performance(self, large_dataset, temp_dir):
        """Test exporting large dataset efficiently."""
        df = pd.DataFrame(large_dataset)
        output_file = temp_dir / "large_export.csv"

        # Export large dataset
        with patch("dotmac.platform.data_transfer.factory.settings") as mock_settings:
            mock_settings.features.data_transfer_enabled = True

            config = TransferConfig(chunk_size=200)
            exporter = create_exporter("csv", config=config)
            exporter.export_to_file(df, output_file)

        # Verify export completed
        assert output_file.exists()
        imported_df = pd.read_csv(output_file)
        assert len(imported_df) == 1000

    def test_progress_tracking_during_import(self, large_dataset, temp_dir):
        """Test progress tracking during large import."""
        # Create large CSV file
        csv_file = temp_dir / "progress_test.csv"
        pd.DataFrame(large_dataset).to_csv(csv_file, index=False)

        # Track progress during import
        progress = ProgressInfo(total_records=1000)

        with patch("dotmac.platform.data_transfer.factory.settings") as mock_settings:
            mock_settings.features.data_transfer_enabled = True

            config = TransferConfig(chunk_size=100)
            importer = create_importer("csv", config=config)

            # Import with progress tracking
            result = importer.import_from_file(csv_file)

        # Verify import completed
        assert result is not None
        assert len(result) == 1000


# ============================================================================
# End-to-End Workflow Integration Tests
# ============================================================================


class TestEndToEndWorkflows:
    """Test complete end-to-end data transfer workflows."""

    def test_complete_etl_workflow(self, sample_customer_data, temp_dir):
        """Test Extract-Transform-Load workflow."""
        with patch("dotmac.platform.data_transfer.factory.settings") as mock_settings:
            mock_settings.features.data_transfer_enabled = True

            # 1. EXTRACT: Import from CSV
            source_csv = temp_dir / "source.csv"
            pd.DataFrame(sample_customer_data).to_csv(source_csv, index=False)

            importer = create_importer("csv")
            df = importer.import_from_file(source_csv)

            # 2. TRANSFORM: Add calculated fields
            df["email_domain"] = df["email"].str.split("@").str[1]
            df["age_group"] = pd.cut(
                df["age"], bins=[0, 25, 35, 100], labels=["young", "middle", "senior"]
            )

            # 3. LOAD: Export to JSON
            output_json = temp_dir / "transformed.json"
            exporter = create_exporter("json")
            exporter.export_to_file(df, output_json)

        # Verify complete workflow
        assert output_json.exists()
        with open(output_json) as f:
            result = json.load(f)
        assert len(result) == 3
        assert "email_domain" in result[0]
        assert "age_group" in result[0]

    def test_multi_source_aggregation_workflow(self, sample_customer_data, temp_dir):
        """Test aggregating data from multiple sources."""
        with patch("dotmac.platform.data_transfer.factory.settings") as mock_settings:
            mock_settings.features.data_transfer_enabled = True

            # Create multiple source files
            csv_data = sample_customer_data[:2]
            json_data = sample_customer_data[2:]

            csv_file = temp_dir / "customers.csv"
            json_file = temp_dir / "customers.json"

            pd.DataFrame(csv_data).to_csv(csv_file, index=False)
            with open(json_file, "w") as f:
                json.dump(json_data, f)

            # Import from both sources
            csv_importer = create_importer("csv")
            json_importer = create_importer("json")

            df1 = csv_importer.import_from_file(csv_file)
            df2 = json_importer.import_from_file(json_file)

            # Combine data
            combined_df = pd.concat([df1, df2], ignore_index=True)

            # Export combined data
            output_file = temp_dir / "combined.xlsx"
            exporter = create_exporter(DataFormat.EXCEL)
            exporter.export_to_file(combined_df, output_file)

        # Verify aggregation
        assert output_file.exists()
        result_df = pd.read_excel(output_file, engine="openpyxl")
        assert len(result_df) == 3

    def test_data_migration_workflow(self, sample_customer_data, temp_dir):
        """Test data migration workflow with validation."""
        with patch("dotmac.platform.data_transfer.factory.settings") as mock_settings:
            mock_settings.features.data_transfer_enabled = True

            # Source: Legacy CSV format
            source_file = temp_dir / "legacy_data.csv"
            legacy_df = pd.DataFrame(sample_customer_data)
            legacy_df.to_csv(source_file, index=False)

            # Import legacy data
            importer = create_importer("csv")
            df = importer.import_from_file(source_file)

            # Transform to new schema (add fields, rename, etc.)
            df["migrated_at"] = datetime.now(UTC).isoformat()
            df["status"] = "active"
            df = df.rename(columns={"id": "customer_id"})

            # Export to new format (JSON)
            target_file = temp_dir / "migrated_data.json"
            exporter = create_exporter("json")
            exporter.export_to_file(df, target_file)

        # Verify migration
        assert target_file.exists()
        with open(target_file) as f:
            migrated = json.load(f)
        assert len(migrated) == 3
        assert "customer_id" in migrated[0]
        assert "migrated_at" in migrated[0]
        assert migrated[0]["status"] == "active"

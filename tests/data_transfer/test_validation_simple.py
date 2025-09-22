"""
Simple tests for data transfer validation functionality.
Focuses on working validation patterns and edge cases.
"""

import io
from typing import Any

import pytest

from dotmac.platform.data_transfer.base import (
    DataRecord,
    DataBatch,
    DataValidationError,
    StreamingError,
    TransferConfig,
)
from dotmac.platform.data_transfer.exporters import ExportOptions


class TestDataValidationExceptions:
    """Test data validation exception handling."""

    def test_data_validation_error_creation(self):
        """Test DataValidationError exception creation."""
        error = DataValidationError("Validation failed")
        assert str(error) == "Validation failed"
        assert isinstance(error, Exception)

    def test_streaming_error_creation(self):
        """Test StreamingError exception creation."""
        error = StreamingError("Stream processing failed")
        assert str(error) == "Stream processing failed"
        assert isinstance(error, Exception)

    def test_data_validation_error_with_context(self):
        """Test DataValidationError with additional context."""
        try:
            raise ValueError("Original error")
        except ValueError as e:
            validation_error = DataValidationError("Validation failed due to value error")
            validation_error.__cause__ = e

            assert str(validation_error) == "Validation failed due to value error"
            assert isinstance(validation_error.__cause__, ValueError)


class TestDataRecordValidation:
    """Test DataRecord validation functionality."""

    def test_data_record_basic_validation(self):
        """Test basic data record validation."""
        record = DataRecord(
            data={"name": "John", "age": 30},
            validation_errors=[],
            is_valid=True
        )

        assert record.validation_errors == []
        assert record.is_valid is True
        assert record.data["name"] == "John"

    def test_data_record_with_validation_errors(self):
        """Test data record with validation errors."""
        record = DataRecord(
            data={"name": "John"},
            validation_errors=["Email required", "Phone invalid"],
            is_valid=False
        )

        assert len(record.validation_errors) == 2
        assert "Email required" in record.validation_errors
        assert "Phone invalid" in record.validation_errors
        assert record.is_valid is False

    def test_data_record_row_number_tracking(self):
        """Test data record with row number for error tracking."""
        record = DataRecord(
            data={"field": "value"},
            row_number=42,
            validation_errors=["Parse error on row 42"],
            is_valid=False
        )

        assert record.row_number == 42
        assert "Parse error on row 42" in record.validation_errors

    def test_data_record_empty_data_validation(self):
        """Test that empty data raises validation error."""
        with pytest.raises(ValueError, match="Record data cannot be empty"):
            DataRecord(data={})

    def test_data_record_validation_error_modification(self):
        """Test modifying validation errors after creation."""
        record = DataRecord(
            data={"name": "John"},
            validation_errors=["Initial error"]
        )

        # Add more validation errors
        record.validation_errors.append("Second error")
        record.validation_errors.extend(["Third error", "Fourth error"])
        record.is_valid = False

        assert len(record.validation_errors) == 4
        assert "Initial error" in record.validation_errors
        assert "Second error" in record.validation_errors
        assert "Third error" in record.validation_errors
        assert "Fourth error" in record.validation_errors

    def test_data_record_metadata_validation(self):
        """Test data record with metadata."""
        metadata = {
            "source_file": "data.csv",
            "import_timestamp": "2024-01-01T10:00:00",
            "validation_rules": ["email_format", "age_range"]
        }

        record = DataRecord(
            data={"email": "test@example.com", "age": 25},
            metadata=metadata,
            is_valid=True
        )

        assert record.metadata["source_file"] == "data.csv"
        assert "validation_rules" in record.metadata
        assert record.is_valid is True


class TestDataBatchValidation:
    """Test DataBatch validation functionality with correct constructor."""

    def test_data_batch_valid_records_filtering(self):
        """Test valid_records property filtering."""
        records = [
            DataRecord(data={"field": "value1"}, is_valid=True),
            DataRecord(data={"field": "value2"}, is_valid=False),
            DataRecord(data={"field": "value3"}, is_valid=True),
        ]

        batch = DataBatch(
            batch_number=1,
            records=records,
            total_size=1024
        )

        valid_records = batch.valid_records
        assert len(valid_records) == 2
        assert all(record.is_valid for record in valid_records)

    def test_data_batch_invalid_records_filtering(self):
        """Test invalid_records property filtering."""
        records = [
            DataRecord(data={"field": "value1"}, is_valid=True),
            DataRecord(data={"field": "value2"}, is_valid=False),
            DataRecord(data={"field": "value3"}, is_valid=False),
        ]

        batch = DataBatch(
            batch_number=1,
            records=records,
            total_size=1024
        )

        invalid_records = batch.invalid_records
        assert len(invalid_records) == 2
        assert all(not record.is_valid for record in invalid_records)

    def test_data_batch_all_valid_records(self):
        """Test batch with all valid records."""
        records = [
            DataRecord(data={"field": "value1"}, is_valid=True),
            DataRecord(data={"field": "value2"}, is_valid=True),
        ]

        batch = DataBatch(
            batch_number=1,
            records=records,
            total_size=512
        )

        assert len(batch.valid_records) == 2
        assert len(batch.invalid_records) == 0
        assert len(batch.records) == 2

    def test_data_batch_all_invalid_records(self):
        """Test batch with all invalid records."""
        records = [
            DataRecord(data={"field": "value1"}, is_valid=False),
            DataRecord(data={"field": "value2"}, is_valid=False),
        ]

        batch = DataBatch(
            batch_number=1,
            records=records,
            total_size=512
        )

        assert len(batch.valid_records) == 0
        assert len(batch.invalid_records) == 2
        assert len(batch.records) == 2

    def test_data_batch_empty_records(self):
        """Test batch with no records."""
        batch = DataBatch(
            batch_number=1,
            records=[],
            total_size=0
        )

        assert len(batch.valid_records) == 0
        assert len(batch.invalid_records) == 0
        assert len(batch.records) == 0

    def test_data_batch_batch_id_generation(self):
        """Test batch with auto-generated batch ID."""
        records = [
            DataRecord(data={"name": "John"}, is_valid=True),
        ]

        batch = DataBatch(
            batch_number=1,
            records=records,
            total_size=256
        )

        # Check that batch_id is generated
        assert batch.batch_id is not None
        assert len(batch.batch_id) > 0
        assert batch.batch_number == 1
        assert batch.total_size == 256


class TestTransferConfigValidation:
    """Test TransferConfig validation behavior."""

    def test_transfer_config_validation_enabled(self):
        """Test transfer config with validation enabled."""
        config = settings.Transfer.model_copy(update={validate_data=True})
        assert config.validate_data is True

    def test_transfer_config_validation_disabled(self):
        """Test transfer config with validation disabled."""
        config = settings.Transfer.model_copy(update={validate_data=False})
        assert config.validate_data is False

    def test_transfer_config_batch_size_validation(self):
        """Test batch size validation in config."""
        # Valid batch size
        config = settings.Transfer.model_copy(update={batch_size=1000})
        assert config.batch_size == 1000

        # Test boundary values
        config_min = settings.Transfer.model_copy(update={batch_size=1})
        assert config_min.batch_size == 1

        config_max = settings.Transfer.model_copy(update={batch_size=50000})
        assert config_max.batch_size == 50000

    def test_transfer_config_invalid_batch_size(self):
        """Test invalid batch size validation."""
        with pytest.raises(ValueError):
            settings.Transfer.model_copy(update={batch_size=0})

        with pytest.raises(ValueError):
            settings.Transfer.model_copy(update={batch_size=-1})

        with pytest.raises(ValueError):
            settings.Transfer.model_copy(update={batch_size=50001})  # Above maximum

    def test_transfer_config_max_workers_validation(self):
        """Test max workers validation."""
        config = settings.Transfer.model_copy(update={max_workers=4})
        assert config.max_workers == 4

        # Test boundary values
        config_min = settings.Transfer.model_copy(update={max_workers=1})
        assert config_min.max_workers == 1

        config_max = settings.Transfer.model_copy(update={max_workers=32})
        assert config_max.max_workers == 32

    def test_transfer_config_invalid_max_workers(self):
        """Test invalid max workers validation."""
        with pytest.raises(ValueError):
            settings.Transfer.model_copy(update={max_workers=0})

        with pytest.raises(ValueError):
            settings.Transfer.model_copy(update={max_workers=-1})

        with pytest.raises(ValueError):
            settings.Transfer.model_copy(update={max_workers=33})  # Above maximum


class TestExportOptionsValidation:
    """Test ExportOptions validation behavior."""

    def test_export_options_delimiter_validation(self):
        """Test delimiter validation in export options."""
        # Valid single character delimiters
        options_comma = ExportOptions(delimiter=",")
        assert options_comma.delimiter == ","

        options_pipe = ExportOptions(delimiter="|")
        assert options_pipe.delimiter == "|"

        options_semicolon = ExportOptions(delimiter=";")
        assert options_semicolon.delimiter == ";"

        options_colon = ExportOptions(delimiter=":")
        assert options_colon.delimiter == ":"

    def test_export_options_invalid_delimiter(self):
        """Test invalid delimiter validation."""
        # Multi-character delimiter should fail
        with pytest.raises(ValueError):
            ExportOptions(delimiter="||")

        # Empty delimiter should fail
        with pytest.raises(ValueError):
            ExportOptions(delimiter="")

    def test_export_options_json_configuration(self):
        """Test JSON-specific export options."""
        # Standard JSON format
        options_standard = ExportOptions(
            json_lines=False,
            json_indent=2,
            json_sort_keys=True
        )
        assert options_standard.json_lines is False
        assert options_standard.json_indent == 2
        assert options_standard.json_sort_keys is True

        # JSON Lines format
        options_jsonl = ExportOptions(
            json_lines=True,
            json_indent=None  # No indentation for JSONL
        )
        assert options_jsonl.json_lines is True
        assert options_jsonl.json_indent is None

    def test_export_options_xml_configuration(self):
        """Test XML-specific export options."""
        options = ExportOptions(
            xml_root_element="data",
            xml_record_element="record",
            xml_pretty_print=True
        )

        assert options.xml_root_element == "data"
        assert options.xml_record_element == "record"
        assert options.xml_pretty_print is True

    def test_export_options_excel_configuration(self):
        """Test Excel-specific export options."""
        options = ExportOptions(
            sheet_name="DataSheet",
            freeze_panes="A2",
            auto_filter=True,
            include_headers=True
        )

        assert options.sheet_name == "DataSheet"
        assert options.freeze_panes == "A2"
        assert options.auto_filter is True
        assert options.include_headers is True


class TestValidationPatterns:
    """Test common validation patterns."""

    def test_email_validation_pattern(self):
        """Test email validation pattern simulation."""
        def validate_email(record: DataRecord) -> bool:
            """Simple email validation."""
            email = record.data.get("email", "")
            if not email or "@" not in email or "." not in email:
                record.validation_errors.append("Invalid email format")
                record.is_valid = False
                return False
            return True

        # Valid email
        valid_record = DataRecord(data={"email": "test@example.com"})
        result = validate_email(valid_record)
        assert result is True
        assert valid_record.is_valid is True

        # Invalid email
        invalid_record = DataRecord(data={"email": "invalid-email"})
        result = validate_email(invalid_record)
        assert result is False
        assert "Invalid email format" in invalid_record.validation_errors

    def test_required_fields_validation_pattern(self):
        """Test required fields validation pattern."""
        def validate_required_fields(record: DataRecord, required_fields: list[str]) -> bool:
            """Validate required fields are present."""
            missing_fields = []
            for field in required_fields:
                if field not in record.data or not record.data[field]:
                    missing_fields.append(field)

            if missing_fields:
                record.validation_errors.append(f"Missing required fields: {', '.join(missing_fields)}")
                record.is_valid = False
                return False
            return True

        # Valid record with all required fields
        valid_record = DataRecord(data={"name": "John", "email": "john@test.com", "age": 30})
        result = validate_required_fields(valid_record, ["name", "email"])
        assert result is True

        # Invalid record missing required fields
        invalid_record = DataRecord(data={"name": "John"})  # Missing email
        result = validate_required_fields(invalid_record, ["name", "email"])
        assert result is False
        assert "Missing required fields: email" in invalid_record.validation_errors

    def test_range_validation_pattern(self):
        """Test numeric range validation pattern."""
        def validate_age_range(record: DataRecord) -> bool:
            """Validate age is in valid range."""
            age = record.data.get("age")
            if age is None:
                return True  # Optional field

            try:
                age_int = int(age)
                if age_int < 0 or age_int > 150:
                    record.validation_errors.append("Age must be between 0 and 150")
                    record.is_valid = False
                    return False
            except (ValueError, TypeError):
                record.validation_errors.append("Age must be a valid number")
                record.is_valid = False
                return False

            return True

        # Valid age
        valid_record = DataRecord(data={"name": "John", "age": "30"})
        result = validate_age_range(valid_record)
        assert result is True

        # Invalid age (out of range)
        invalid_record = DataRecord(data={"name": "John", "age": "200"})
        result = validate_age_range(invalid_record)
        assert result is False
        assert "Age must be between 0 and 150" in invalid_record.validation_errors

        # Invalid age (not a number)
        invalid_record2 = DataRecord(data={"name": "John", "age": "not-a-number"})
        result = validate_age_range(invalid_record2)
        assert result is False
        assert "Age must be a valid number" in invalid_record2.validation_errors

    def test_composite_validation_pattern(self):
        """Test composite validation with multiple rules."""
        def validate_user_record(record: DataRecord) -> bool:
            """Validate user record with multiple rules."""
            errors = []

            # Check required fields
            required_fields = ["name", "email"]
            for field in required_fields:
                if not record.data.get(field):
                    errors.append(f"Missing required field: {field}")

            # Validate email format
            email = record.data.get("email", "")
            if email and ("@" not in email or "." not in email):
                errors.append("Invalid email format")

            # Validate age if provided
            age = record.data.get("age")
            if age is not None:
                try:
                    age_int = int(age)
                    if age_int < 0 or age_int > 150:
                        errors.append("Age must be between 0 and 150")
                except (ValueError, TypeError):
                    errors.append("Age must be a valid number")

            if errors:
                record.validation_errors.extend(errors)
                record.is_valid = False
                return False

            return True

        # Valid record
        valid_record = DataRecord(data={
            "name": "John Doe",
            "email": "john@example.com",
            "age": "30"
        })
        result = validate_user_record(valid_record)
        assert result is True
        assert valid_record.is_valid is True

        # Invalid record with multiple errors
        invalid_record = DataRecord(data={
            "name": "",  # Missing name
            "email": "invalid-email",  # Invalid email
            "age": "200"  # Invalid age
        })
        result = validate_user_record(invalid_record)
        assert result is False
        assert len(invalid_record.validation_errors) == 3
        assert any("Missing required field: name" in error for error in invalid_record.validation_errors)
        assert any("Invalid email format" in error for error in invalid_record.validation_errors)
        assert any("Age must be between 0 and 150" in error for error in invalid_record.validation_errors)
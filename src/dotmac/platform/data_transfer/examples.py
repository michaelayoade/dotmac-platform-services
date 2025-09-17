"""
Data Transfer Examples

Example usage patterns for the data transfer module.
"""

import asyncio
import tempfile
from pathlib import Path
from typing import AsyncGenerator

from .base import DataBatch, DataRecord, TransferConfig
from .importers import import_file
from .exporters import export_data
from . import (
    DataFormat,
    convert_file,
    create_data_pipeline,
    create_transfer_config,
    validate_and_clean_file,
)


def example_validator(record: DataRecord) -> bool:
    """Example validation function."""
    # Validate that record has required fields
    required_fields = ["id", "name", "email"]
    return all(field in record.data for field in required_fields)


def example_transformer(record: DataRecord) -> DataRecord:
    """Example transformation function."""
    # Normalize email to lowercase
    if "email" in record.data and record.data["email"]:
        record.data["email"] = record.data["email"].lower()

    # Add computed field
    if "first_name" in record.data and "last_name" in record.data:
        record.data["full_name"] = f"{record.data['first_name']} {record.data['last_name']}"

    return record


async def example_basic_import():
    """Example: Basic file import."""
    # Create sample CSV data
    sample_data = """id,name,email
1,John Doe,john@example.com
2,Jane Smith,jane@example.com
3,Bob Wilson,bob@example.com"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(sample_data)
        csv_file = Path(f.name)

    try:
        print("Importing CSV file...")

        # Import with basic configuration
        config = create_transfer_config(batch_size=2)

        async for batch in import_file(csv_file, DataFormat.CSV, config):
            print(f"Batch {batch.batch_number}: {len(batch.records)} records")
            for record in batch.records:
                print(f"  Row {record.row_number}: {record.data}")

    finally:
        csv_file.unlink()  # Clean up


async def example_format_conversion():
    """Example: Convert CSV to JSON."""
    # Create sample CSV data
    sample_data = """id,name,age,city
1,Alice,25,New York
2,Bob,30,San Francisco
3,Charlie,35,Chicago"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(sample_data)
        csv_file = Path(f.name)

    json_file = csv_file.with_suffix(".json")

    try:
        print("Converting CSV to JSON...")

        def progress_callback(progress):
            print(
                f"Progress: {progress.progress_percentage:.1f}% "
                f"({progress.processed_records} records)"
            )

        result = await convert_file(
            source_path=str(csv_file),
            target_path=str(json_file),
            batch_size=1,
            progress_callback=progress_callback,
        )

        print(f"Conversion completed: {result.processed_records} records processed")

        # Read and display result
        with open(json_file, "r") as f:
            print("Output JSON:", f.read())

    finally:
        csv_file.unlink()
        if json_file.exists():
            json_file.unlink()


async def example_data_pipeline():
    """Example: Data pipeline with validation and transformation."""
    # Create sample data with some invalid records
    sample_data = """id,first_name,last_name,email,age
1,John,Doe,JOHN@EXAMPLE.COM,25
2,Jane,Smith,,30
3,,Wilson,bob@example.com,35
4,Alice,Johnson,alice@example.com,28"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(sample_data)
        input_file = Path(f.name)

    output_file = input_file.with_suffix(".json")

    try:
        print("Running data pipeline with validation and transformation...")

        def progress_callback(progress):
            print(
                f"Pipeline progress: {progress.progress_percentage:.1f}% "
                f"({progress.processed_records}/{progress.total_records})"
            )

        # Create pipeline with validation and transformation
        pipeline = create_data_pipeline(
            source_path=str(input_file),
            target_path=str(output_file),
            progress_callback=progress_callback,
            validator=example_validator,
            transformer=example_transformer,
        )

        result = await pipeline.execute()

        print(f"Pipeline completed:")
        print(f"  Total processed: {result.processed_records}")
        print(f"  Failed records: {result.failed_records}")
        print(f"  Success rate: {result.success_rate:.1f}%")

        # Show output
        with open(output_file, "r") as f:
            print("Pipeline output:", f.read())

    finally:
        input_file.unlink()
        if output_file.exists():
            output_file.unlink()


async def example_streaming_large_file():
    """Example: Stream processing of large file."""
    print("Simulating large file processing...")

    async def generate_sample_data() -> AsyncGenerator[DataBatch, None]:
        """Generate sample data batches."""
        for batch_num in range(1, 4):  # 3 batches
            records = []
            for i in range(5):  # 5 records per batch
                record_id = (batch_num - 1) * 5 + i + 1
                record = DataRecord(
                    row_number=record_id,
                    data={
                        "id": record_id,
                        "name": f"User {record_id}",
                        "email": f"user{record_id}@example.com",
                        "batch": batch_num,
                    },
                )
                records.append(record)

            batch = DataBatch(
                batch_number=batch_num,
                records=records,
                total_size=sum(len(str(r.data)) for r in records),
            )

            print(f"Generated batch {batch_num} with {len(records)} records")
            yield batch

            # Simulate processing delay
            await asyncio.sleep(0.1)

    # Export streaming data to JSON
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        output_file = Path(f.name)

    try:

        def progress_callback(progress):
            print(
                f"Export progress: {progress.processed_records} records, "
                f"batch {progress.current_batch}"
            )

        result = await export_data(
            data=generate_sample_data(),
            file_path=output_file,
            data_format=DataFormat.JSON,
            progress_callback=progress_callback,
        )

        print(f"Streaming export completed: {result.processed_records} records")

        # Show result
        with open(output_file, "r") as f:
            print("Exported data:", f.read()[:500] + "..." if len(f.read()) > 500 else f.read())

    finally:
        if output_file.exists():
            output_file.unlink()


async def example_data_validation_and_cleaning():
    """Example: Data validation and cleaning."""
    # Create sample data with various issues
    sample_data = """id,name,email,age
1,John Doe,john@example.com,25
2,,jane@example.com,30
3,Bob Wilson,invalid-email,35
4,Alice Smith,alice@example.com,
5,Charlie Brown,charlie@example.com,40"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(sample_data)
        input_file = Path(f.name)

    cleaned_file = input_file.with_suffix("_cleaned.csv")

    try:
        print("Validating and cleaning data...")

        def data_validator(record: DataRecord) -> bool:
            """Validate record has required fields and valid data."""
            data = record.data

            # Check required fields
            if not data.get("name") or not data.get("email"):
                record.validation_errors.append("Missing required fields")
                record.is_valid = False
                return False

            # Validate email format (basic check)
            email = data.get("email", "")
            if "@" not in email or "." not in email:
                record.validation_errors.append("Invalid email format")
                record.is_valid = False
                return False

            return True

        def data_transformer(record: DataRecord) -> DataRecord:
            """Clean and normalize data."""
            data = record.data

            # Normalize email
            if "email" in data and data["email"]:
                data["email"] = data["email"].lower().strip()

            # Convert age to integer if possible
            if "age" in data and data["age"]:
                try:
                    data["age"] = int(data["age"])
                except ValueError:
                    data["age"] = None

            # Trim whitespace from strings
            for key, value in data.items():
                if isinstance(value, str):
                    data[key] = value.strip()

            return record

        def progress_callback(progress):
            print(
                f"Cleaning progress: {progress.processed_records} processed, "
                f"{progress.failed_records} failed"
            )

        result = await validate_and_clean_file(
            source_path=str(input_file),
            target_path=str(cleaned_file),
            validator=data_validator,
            transformer=data_transformer,
            skip_invalid=True,
            progress_callback=progress_callback,
        )

        print(f"Data cleaning completed:")
        print(f"  Records processed: {result.processed_records}")
        print(f"  Records failed: {result.failed_records}")
        print(f"  Success rate: {result.success_rate:.1f}%")

        # Show cleaned data
        if cleaned_file.exists():
            with open(cleaned_file, "r") as f:
                print("Cleaned data:", f.read())

    finally:
        input_file.unlink()
        if cleaned_file.exists():
            cleaned_file.unlink()


async def main():
    """Run all examples."""
    print("=== Data Transfer Module Examples ===\n")

    print("1. Basic Import Example")
    await example_basic_import()
    print()

    print("2. Format Conversion Example")
    await example_format_conversion()
    print()

    print("3. Data Pipeline Example")
    await example_data_pipeline()
    print()

    print("4. Streaming Large File Example")
    await example_streaming_large_file()
    print()

    print("5. Data Validation and Cleaning Example")
    await example_data_validation_and_cleaning()
    print()

    print("=== All examples completed ===")


if __name__ == "__main__":
    asyncio.run(main())

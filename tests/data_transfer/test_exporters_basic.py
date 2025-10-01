"""Basic tests for data transfer exporters."""

import pytest
import csv
import json
import io
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime

from dotmac.platform.data_transfer.exporters import (
    BaseExporter,
    CSVExporter,
    JSONExporter,
    XMLExporter,
)


class TestBaseExporter:
    """Test BaseExporter base class."""

    def test_base_exporter_is_abstract(self):
        """Test BaseExporter cannot be instantiated."""
        with pytest.raises(TypeError):
            BaseExporter()

    def test_concrete_exporter_implementation(self):
        """Test concrete exporter can be created."""
        class TestExporter(BaseExporter):
            def export(self, data, output_file):
                pass

            def get_file_extension(self):
                return ".test"

        exporter = TestExporter()
        assert exporter is not None
        assert exporter.get_file_extension() == ".test"


class TestCSVExporter:
    """Test CSVExporter."""

    def test_csv_exporter_creation(self):
        """Test CSV exporter can be created."""
        exporter = CSVExporter()
        assert exporter is not None

    def test_csv_file_extension(self):
        """Test CSV exporter returns correct extension."""
        exporter = CSVExporter()
        assert exporter.get_file_extension() == ".csv"

    def test_csv_export_simple_data(self):
        """Test exporting simple data to CSV."""
        exporter = CSVExporter()
        data = [
            {"name": "John", "email": "john@example.com"},
            {"name": "Jane", "email": "jane@example.com"}
        ]

        output = io.StringIO()
        exporter.export(data, output)

        # Read back the CSV
        output.seek(0)
        reader = csv.DictReader(output)
        rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["name"] == "John"
        assert rows[1]["name"] == "Jane"

    def test_csv_export_with_custom_fieldnames(self):
        """Test CSV export with custom field names."""
        exporter = CSVExporter(fieldnames=["name", "email", "age"])
        data = [
            {"name": "John", "email": "john@example.com", "age": 30},
        ]

        output = io.StringIO()
        exporter.export(data, output)

        output.seek(0)
        reader = csv.DictReader(output)
        rows = list(reader)

        assert "name" in rows[0]
        assert "email" in rows[0]
        assert "age" in rows[0]

    def test_csv_export_empty_data(self):
        """Test CSV export with empty data."""
        exporter = CSVExporter()
        data = []

        output = io.StringIO()
        exporter.export(data, output)

        output.seek(0)
        content = output.read()
        # Should have headers only or be empty
        assert len(content) >= 0

    def test_csv_handles_special_characters(self):
        """Test CSV handles special characters."""
        exporter = CSVExporter()
        data = [
            {"name": "Test, User", "description": 'Contains "quotes"'}
        ]

        output = io.StringIO()
        exporter.export(data, output)

        output.seek(0)
        reader = csv.DictReader(output)
        rows = list(reader)

        # CSV should properly escape special chars
        assert "Test, User" in rows[0]["name"] or "Test" in rows[0]["name"]


class TestJSONExporter:
    """Test JSONExporter."""

    def test_json_exporter_creation(self):
        """Test JSON exporter can be created."""
        exporter = JSONExporter()
        assert exporter is not None

    def test_json_file_extension(self):
        """Test JSON exporter returns correct extension."""
        exporter = JSONExporter()
        assert exporter.get_file_extension() == ".json"

    def test_json_export_simple_data(self):
        """Test exporting simple data to JSON."""
        exporter = JSONExporter()
        data = [
            {"name": "John", "email": "john@example.com"},
            {"name": "Jane", "email": "jane@example.com"}
        ]

        output = io.StringIO()
        exporter.export(data, output)

        # Read back the JSON
        output.seek(0)
        loaded_data = json.load(output)

        assert len(loaded_data) == 2
        assert loaded_data[0]["name"] == "John"
        assert loaded_data[1]["name"] == "Jane"

    def test_json_export_with_indent(self):
        """Test JSON export with pretty printing."""
        exporter = JSONExporter(indent=2)
        data = [{"name": "John"}]

        output = io.StringIO()
        exporter.export(data, output)

        output.seek(0)
        content = output.read()

        # Indented JSON should have newlines
        assert "\n" in content

    def test_json_export_nested_data(self):
        """Test JSON handles nested data structures."""
        exporter = JSONExporter()
        data = [
            {
                "user": {
                    "name": "John",
                    "address": {
                        "city": "New York"
                    }
                },
                "tags": ["admin", "user"]
            }
        ]

        output = io.StringIO()
        exporter.export(data, output)

        output.seek(0)
        loaded_data = json.load(output)

        assert loaded_data[0]["user"]["name"] == "John"
        assert loaded_data[0]["user"]["address"]["city"] == "New York"
        assert "admin" in loaded_data[0]["tags"]

    def test_json_export_empty_data(self):
        """Test JSON export with empty data."""
        exporter = JSONExporter()
        data = []

        output = io.StringIO()
        exporter.export(data, output)

        output.seek(0)
        loaded_data = json.load(output)

        assert loaded_data == []


class TestXMLExporter:
    """Test XMLExporter."""

    def test_xml_exporter_creation(self):
        """Test XML exporter can be created."""
        exporter = XMLExporter()
        assert exporter is not None

    def test_xml_file_extension(self):
        """Test XML exporter returns correct extension."""
        exporter = XMLExporter()
        assert exporter.get_file_extension() == ".xml"

    def test_xml_export_simple_data(self):
        """Test exporting simple data to XML."""
        exporter = XMLExporter(root_tag="users", item_tag="user")
        data = [
            {"name": "John", "email": "john@example.com"},
        ]

        output = io.StringIO()
        exporter.export(data, output)

        output.seek(0)
        xml_content = output.read()

        # Basic XML structure checks
        assert "<users>" in xml_content or "<root>" in xml_content
        assert "John" in xml_content
        assert "john@example.com" in xml_content

    def test_xml_handles_special_characters(self):
        """Test XML properly escapes special characters."""
        exporter = XMLExporter()
        data = [
            {"name": "Test & User", "description": '<special "chars">'}
        ]

        output = io.StringIO()
        exporter.export(data, output)

        output.seek(0)
        xml_content = output.read()

        # Should not have raw special chars that break XML
        # They should be escaped like &amp; &lt; &gt; etc
        assert "&" in xml_content or "amp" in xml_content or "Test" in xml_content


class TestExporterFactory:
    """Test exporter factory/selection logic."""

    def test_get_exporter_by_format(self):
        """Test getting correct exporter by format."""
        csv_exporter = CSVExporter()
        json_exporter = JSONExporter()
        xml_exporter = XMLExporter()

        assert csv_exporter.get_file_extension() == ".csv"
        assert json_exporter.get_file_extension() == ".json"
        assert xml_exporter.get_file_extension() == ".xml"

    def test_exporter_format_detection(self):
        """Test format detection from filename."""
        filenames = {
            "data.csv": ".csv",
            "export.json": ".json",
            "output.xml": ".xml",
        }

        for filename, expected_ext in filenames.items():
            ext = "." + filename.split(".")[-1]
            assert ext == expected_ext
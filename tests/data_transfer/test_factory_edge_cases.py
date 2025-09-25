"""
Edge case tests for data_transfer factory module.

These tests focus on edge cases, error conditions, and boundary scenarios
to achieve comprehensive test coverage.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock

from dotmac.platform.data_transfer.factory import (
    DataTransferRegistry,
    DataTransferFactory,
    create_excel_importer,
    create_excel_exporter,
    _registry,
    _register_optional_formats,
)
from dotmac.platform.data_transfer.core import (
    DataFormat,
    TransferConfig,
    ImportOptions,
    ExportOptions,
    FormatError,
    BaseImporter,
    BaseExporter,
)
from dotmac.platform.dependencies import DependencyError


class TestRegistryEdgeCases:
    """Test edge cases in the registry."""

    def test_register_none_values(self):
        """Test registering None values."""
        registry = DataTransferRegistry()

        # This should not crash but might cause issues later
        with pytest.raises(TypeError):
            registry.register_importer(DataFormat.CSV, None)

    def test_get_class_after_clear(self):
        """Test getting classes after clearing registry."""
        registry = DataTransferRegistry()

        # Clear and verify error messages
        original_importers = registry._importers.copy()
        original_exporters = registry._exporters.copy()

        try:
            registry._importers.clear()
            registry._exporters.clear()

            with pytest.raises(FormatError) as exc_info:
                registry.get_importer_class(DataFormat.CSV)
            assert "No importer available for format 'csv'" in str(exc_info.value)
            assert "Available: []" in str(exc_info.value)

            with pytest.raises(FormatError) as exc_info:
                registry.get_exporter_class(DataFormat.JSON)
            assert "No exporter available for format 'json'" in str(exc_info.value)
            assert "Available: []" in str(exc_info.value)

        finally:
            # Restore original state
            registry._importers = original_importers
            registry._exporters = original_exporters

    def test_list_formats_with_empty_registry(self):
        """Test listing formats with empty registry."""
        registry = DataTransferRegistry()

        # Save original state
        original_importers = registry._importers.copy()
        original_exporters = registry._exporters.copy()

        try:
            registry._importers.clear()
            registry._exporters.clear()

            formats = registry.list_available_formats()
            assert formats["importers"] == []
            assert formats["exporters"] == []

            enabled = registry.list_enabled_formats()
            # Should still be empty even if features are enabled
            assert enabled["importers"] == []
            assert enabled["exporters"] == []

        finally:
            registry._importers = original_importers
            registry._exporters = original_exporters

    def test_enabled_formats_with_partial_excel_support(self):
        """Test enabled formats with Excel partially supported."""
        registry = DataTransferRegistry()

        # Test Excel enabled but dependency check fails
        with patch('dotmac.platform.data_transfer.factory.settings') as mock_settings:
            with patch('dotmac.platform.data_transfer.factory.DependencyChecker') as mock_dep:
                mock_settings.features.data_transfer_enabled = True
                mock_settings.features.data_transfer_excel = True
                mock_dep.check_feature_dependency.return_value = False

                enabled = registry.list_enabled_formats()

                # Core formats should be enabled
                assert DataFormat.CSV in enabled["importers"]
                assert DataFormat.JSON in enabled["importers"]

                # Excel should not be enabled
                assert DataFormat.EXCEL not in enabled["importers"]
                assert DataFormat.EXCEL not in enabled["exporters"]


class TestFactoryEdgeCases:
    """Test edge cases in the factory."""

    def test_create_with_dataformat_enum_vs_string(self):
        """Test creating importers/exporters with enum vs string formats."""
        with patch('dotmac.platform.data_transfer.factory.settings') as mock_settings:
            mock_settings.features.data_transfer_enabled = True

            # Test with enum
            importer_enum = DataTransferFactory.create_importer(DataFormat.CSV)
            exporter_enum = DataTransferFactory.create_exporter(DataFormat.CSV)

            # Test with string
            importer_str = DataTransferFactory.create_importer("csv")
            exporter_str = DataTransferFactory.create_exporter("csv")

            # Should be the same type
            assert type(importer_enum) == type(importer_str)
            assert type(exporter_enum) == type(exporter_str)

    def test_case_insensitive_format_strings(self):
        """Test case insensitive format string handling."""
        with patch('dotmac.platform.data_transfer.factory.settings') as mock_settings:
            mock_settings.features.data_transfer_enabled = True

            # These should all work
            test_cases = ["CSV", "csv", "Csv", "CSV"]
            for format_str in test_cases:
                importer = DataTransferFactory.create_importer(format_str)
                exporter = DataTransferFactory.create_exporter(format_str)
                assert isinstance(importer, BaseImporter)
                assert isinstance(exporter, BaseExporter)

    def test_format_string_edge_cases(self):
        """Test edge cases in format string parsing."""
        with patch('dotmac.platform.data_transfer.factory.settings') as mock_settings:
            mock_settings.features.data_transfer_enabled = True

            # Empty string
            with pytest.raises(FormatError):
                DataTransferFactory.create_importer("")

            # Whitespace
            with pytest.raises(FormatError):
                DataTransferFactory.create_importer("   ")

            # Special characters
            with pytest.raises(FormatError):
                DataTransferFactory.create_importer("csv!")

            # Numbers
            with pytest.raises(FormatError):
                DataTransferFactory.create_importer("123")

    def test_validate_format_edge_cases(self):
        """Test format validation edge cases."""
        # Test with various exception types
        with patch('dotmac.platform.data_transfer.factory.DataTransferFactory.create_importer') as mock_create:
            # FormatError
            mock_create.side_effect = FormatError("Invalid format")
            assert DataTransferFactory.validate_format("invalid") is False

            # ValueError
            mock_create.side_effect = ValueError("Feature disabled")
            assert DataTransferFactory.validate_format("csv") is False

            # ImportError
            mock_create.side_effect = ImportError("Missing dependency")
            assert DataTransferFactory.validate_format("excel") is False

            # Other exceptions should also return False
            mock_create.side_effect = RuntimeError("Unexpected error")
            assert DataTransferFactory.validate_format("csv") is False

    def test_detect_format_case_insensitive_extensions(self):
        """Test format detection with case insensitive extensions."""
        test_cases = [
            ("file.CSV", DataFormat.CSV),
            ("file.Json", DataFormat.JSON),
            ("file.XLSX", DataFormat.EXCEL),
            ("file.XML", DataFormat.XML),
            ("file.YAML", DataFormat.YAML),
            ("file.YML", DataFormat.YAML),
        ]

        for file_path, expected_format in test_cases:
            result = DataTransferFactory.detect_format(file_path)
            assert result == expected_format

    def test_detect_format_complex_paths(self):
        """Test format detection with complex file paths."""
        test_cases = [
            ("/very/long/path/to/some/data/file.csv", DataFormat.CSV),
            ("../relative/path/data.json", DataFormat.JSON),
            ("./current/dir/file.xlsx", DataFormat.EXCEL),
            ("C:\\Windows\\Path\\file.xml", DataFormat.XML),
            ("~/home/user/config.yaml", DataFormat.YAML),
            ("file.name.with.dots.csv", DataFormat.CSV),
        ]

        for file_path, expected_format in test_cases:
            result = DataTransferFactory.detect_format(file_path)
            assert result == expected_format

    def test_detect_format_no_extension(self):
        """Test format detection with no extension."""
        with pytest.raises(FormatError) as exc_info:
            DataTransferFactory.detect_format("filename_without_extension")
        assert "Cannot detect format" in str(exc_info.value)

    def test_detect_format_empty_extension(self):
        """Test format detection with empty extension."""
        with pytest.raises(FormatError) as exc_info:
            DataTransferFactory.detect_format("filename.")
        assert "Cannot detect format" in str(exc_info.value)

    def test_create_importer_with_kwargs(self):
        """Test creating importer with additional kwargs."""
        with patch('dotmac.platform.data_transfer.factory.settings') as mock_settings:
            with patch('dotmac.platform.data_transfer.factory._registry') as mock_registry:
                mock_settings.features.data_transfer_enabled = True

                # Mock importer class that accepts kwargs
                mock_importer_class = Mock()
                mock_instance = Mock()
                mock_importer_class.return_value = mock_instance
                mock_registry.get_importer_class.return_value = mock_importer_class

                # Call with custom kwargs
                result = DataTransferFactory.create_importer(
                    "csv",
                    custom_param="test_value",
                    another_param=123
                )

                # Verify kwargs were passed
                mock_importer_class.assert_called_once()
                args, kwargs = mock_importer_class.call_args
                assert "custom_param" in kwargs
                assert kwargs["custom_param"] == "test_value"
                assert "another_param" in kwargs
                assert kwargs["another_param"] == 123

    def test_create_exporter_with_kwargs(self):
        """Test creating exporter with additional kwargs."""
        with patch('dotmac.platform.data_transfer.factory.settings') as mock_settings:
            with patch('dotmac.platform.data_transfer.factory._registry') as mock_registry:
                mock_settings.features.data_transfer_enabled = True

                mock_exporter_class = Mock()
                mock_instance = Mock()
                mock_exporter_class.return_value = mock_instance
                mock_registry.get_exporter_class.return_value = mock_exporter_class

                result = DataTransferFactory.create_exporter(
                    "json",
                    indent=4,
                    sort_keys=True
                )

                mock_exporter_class.assert_called_once()
                args, kwargs = mock_exporter_class.call_args
                assert "indent" in kwargs
                assert kwargs["indent"] == 4
                assert "sort_keys" in kwargs
                assert kwargs["sort_keys"] is True


class TestExcelFunctionEdgeCases:
    """Test edge cases for Excel convenience functions."""

    def test_excel_functions_with_dependency_decorator(self):
        """Test Excel functions with dependency decorator behavior."""

        # Test successful case (dependencies available)
        with patch('dotmac.platform.data_transfer.factory.settings') as mock_settings:
            with patch('dotmac.platform.data_transfer.factory.DependencyChecker') as mock_dep:
                with patch('dotmac.platform.data_transfer.factory.DataTransferFactory') as mock_factory:
                    mock_settings.features.data_transfer_enabled = True
                    mock_settings.features.data_transfer_excel = True
                    mock_dep.check_feature_dependency.return_value = True
                    mock_dep.require_feature_dependency.return_value = None

                    mock_importer = Mock()
                    mock_factory.create_importer.return_value = mock_importer

                    result = create_excel_importer(sheet_name="Sheet1")

                    assert result == mock_importer
                    mock_factory.create_importer.assert_called_once_with(
                        DataFormat.EXCEL, sheet_name="Sheet1"
                    )

        # Test dependency failure
        with patch('dotmac.platform.data_transfer.factory.DependencyChecker') as mock_dep:
            mock_dep.require_feature_dependency.side_effect = DependencyError("Missing openpyxl")

            with pytest.raises(DependencyError):
                create_excel_importer()

    def test_excel_exporter_with_dependency_failure(self):
        """Test Excel exporter with dependency failure."""
        with patch('dotmac.platform.data_transfer.factory.DependencyChecker') as mock_dep:
            mock_dep.require_feature_dependency.side_effect = ImportError("No module named 'openpyxl'")

            with pytest.raises(ImportError):
                create_excel_exporter()


class TestOptionalFormatRegistrationEdgeCases:
    """Test edge cases in optional format registration."""

    def test_register_optional_formats_with_import_errors(self):
        """Test optional format registration when imports fail."""

        # Mock settings to enable Excel
        with patch('dotmac.platform.data_transfer.factory.settings') as mock_settings:
            with patch('dotmac.platform.data_transfer.factory.DependencyChecker') as mock_dep:
                mock_settings.features.data_transfer_excel = True
                mock_dep.check_feature_dependency.return_value = True

                # Mock import failure
                with patch('builtins.__import__', side_effect=ImportError("No module")):
                    # This should not crash the registration process
                    _register_optional_formats()

    def test_register_optional_formats_excel_disabled(self):
        """Test optional format registration with Excel disabled."""
        with patch('dotmac.platform.data_transfer.factory.settings') as mock_settings:
            mock_settings.features.data_transfer_excel = False

            # Should complete without attempting to import Excel modules
            _register_optional_formats()  # Should not raise

    def test_register_optional_formats_dependency_check_false(self):
        """Test optional format registration when dependency check returns False."""
        with patch('dotmac.platform.data_transfer.factory.settings') as mock_settings:
            with patch('dotmac.platform.data_transfer.factory.DependencyChecker') as mock_dep:
                mock_settings.features.data_transfer_excel = True
                mock_dep.check_feature_dependency.return_value = False

                # Should complete without importing
                _register_optional_formats()  # Should not raise


class TestRegistryStateConsistency:
    """Test registry state consistency across operations."""

    def test_registry_state_after_multiple_registrations(self):
        """Test registry state after multiple custom registrations."""
        registry = DataTransferRegistry()

        # Save original state
        original_importers = registry._importers.copy()
        original_exporters = registry._exporters.copy()

        try:
            # Create mock classes
            class MockImporter1(BaseImporter):
                pass

            class MockImporter2(BaseImporter):
                pass

            class MockExporter1(BaseExporter):
                pass

            # Register multiple times
            registry.register_importer(DataFormat.PARQUET, MockImporter1)
            registry.register_importer(DataFormat.PARQUET, MockImporter2)  # Override
            registry.register_exporter(DataFormat.PARQUET, MockExporter1)

            # Latest registration should win
            assert registry.get_importer_class(DataFormat.PARQUET) == MockImporter2
            assert registry.get_exporter_class(DataFormat.PARQUET) == MockExporter1

            # Should appear in listings
            formats = registry.list_available_formats()
            assert DataFormat.PARQUET in formats["importers"]
            assert DataFormat.PARQUET in formats["exporters"]

        finally:
            # Restore state
            registry._importers = original_importers
            registry._exporters = original_exporters

    def test_factory_methods_return_different_instances(self):
        """Test that factory methods return different instances each time."""
        with patch('dotmac.platform.data_transfer.factory.settings') as mock_settings:
            mock_settings.features.data_transfer_enabled = True

            # Create multiple instances
            importer1 = DataTransferFactory.create_importer("csv")
            importer2 = DataTransferFactory.create_importer("csv")
            exporter1 = DataTransferFactory.create_exporter("csv")
            exporter2 = DataTransferFactory.create_exporter("csv")

            # Should be different instances
            assert importer1 is not importer2
            assert exporter1 is not exporter2

            # But same type
            assert type(importer1) == type(importer2)
            assert type(exporter1) == type(exporter2)

    def test_list_methods_consistency(self):
        """Test consistency between different listing methods."""
        with patch('dotmac.platform.data_transfer.factory.settings') as mock_settings:
            mock_settings.features.data_transfer_enabled = True
            mock_settings.features.data_transfer_excel = False

            # Get formats from different sources
            registry_available = _registry.list_available_formats()
            registry_enabled = _registry.list_enabled_formats()
            factory_available = DataTransferFactory.list_available_formats()
            factory_enabled = DataTransferFactory.list_enabled_formats()

            # Available formats should be consistent
            assert len(registry_available["importers"]) == len(set(f.value for f in registry_available["importers"]))
            assert len(factory_available["importers"]) == len(registry_available["importers"])

            # Enabled should be subset of available
            for importer in registry_enabled["importers"]:
                assert importer in registry_available["importers"]

            for exporter in registry_enabled["exporters"]:
                assert exporter in registry_available["exporters"]
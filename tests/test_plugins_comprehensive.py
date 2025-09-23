"""Comprehensive tests for plugin system to achieve 90%+ coverage."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import importlib.util
import sys

from dotmac.platform.plugins import (
    SimplePluginManager,
    Plugin,
    PluginInfo,
    plugin_manager,
    load_plugin,
    get_plugin,
)


class TestPluginProtocol:
    """Test the Plugin protocol interface."""

    def test_plugin_protocol_methods(self):
        """Test that Plugin protocol has required methods."""
        # Test protocol attributes
        assert hasattr(Plugin, 'activate')
        assert hasattr(Plugin, 'deactivate')


class TestPluginDiscovery:
    """Test plugin discovery functionality."""

    def test_discover_plugins_with_no_paths(self):
        """Test discovery when no plugin paths are set."""
        manager = SimplePluginManager()
        # No paths added
        discovered = manager.discover_plugins()
        assert discovered == 0

    def test_discover_plugins_with_nonexistent_path(self):
        """Test discovery with non-existent plugin path."""
        manager = SimplePluginManager()
        manager.add_plugin_path("/nonexistent/path")
        discovered = manager.discover_plugins()
        assert discovered == 0

    def test_discover_plugins_with_real_plugins(self):
        """Test discovering actual plugin files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SimplePluginManager()
            manager.add_plugin_path(tmpdir)

            # Create a plugin file with correct class name pattern
            plugin_file = Path(tmpdir) / "test_plugin.py"
            plugin_file.write_text("""
class TestPluginPlugin:  # Follows the pattern: {stem}Plugin
    name = "test_plugin"
    version = "1.0.0"

    def activate(self):
        pass

    def deactivate(self):
        pass
""")

            discovered = manager.discover_plugins()
            assert discovered == 1
            assert "test_plugin" in manager.plugins

    def test_discover_plugins_with_multiple_class_patterns(self):
        """Test discovery tries multiple class name patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SimplePluginManager()
            manager.add_plugin_path(tmpdir)

            # Create plugin with non-standard class name
            plugin_file = Path(tmpdir) / "my_custom_plugin.py"
            plugin_file.write_text("""
class Plugin:  # Uses the fallback "Plugin" class name
    name = "custom"
    version = "1.0.0"

    def activate(self):
        pass

    def deactivate(self):
        pass
""")

            discovered = manager.discover_plugins()
            assert discovered == 1
            assert "custom" in manager.plugins

    def test_discover_plugins_skips_non_matching_files(self):
        """Test discovery skips files that don't match pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SimplePluginManager()
            manager.add_plugin_path(tmpdir)

            # Create non-plugin file
            non_plugin = Path(tmpdir) / "not_a_plugin.txt"
            non_plugin.write_text("This is not a plugin")

            discovered = manager.discover_plugins()
            assert discovered == 0

    def test_discover_plugins_handles_load_errors(self):
        """Test discovery continues when plugin loading fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SimplePluginManager()
            manager.add_plugin_path(tmpdir)

            # Create plugin with syntax error
            bad_plugin = Path(tmpdir) / "bad_plugin.py"
            bad_plugin.write_text("This is invalid Python syntax {[}")

            # Create good plugin with correct class naming
            good_plugin = Path(tmpdir) / "good_plugin.py"
            good_plugin.write_text("""
class GoodPluginPlugin:  # Follows the pattern: {stem}Plugin
    name = "good"
    def activate(self): pass
    def deactivate(self): pass
""")

            discovered = manager.discover_plugins()
            # Only good plugin should be discovered
            assert discovered == 1
            assert "good" in manager.plugins


class TestPluginActivationEdgeCases:
    """Test edge cases in plugin activation/deactivation."""

    def test_activate_nonexistent_plugin(self):
        """Test activating a plugin that doesn't exist."""
        manager = SimplePluginManager()
        result = manager.activate_plugin("nonexistent")
        assert result is False

    def test_activate_already_active_plugin(self):
        """Test activating an already active plugin."""
        manager = SimplePluginManager()

        # Add a mock plugin
        plugin = Mock()
        plugin.name = "test"
        plugin.activate = Mock()

        manager.plugins["test"] = PluginInfo(
            name="test",
            module=Mock(),
            instance=plugin,
            active=True  # Already active
        )

        result = manager.activate_plugin("test")
        assert result is True
        # activate() should not be called since already active
        plugin.activate.assert_not_called()

    def test_activate_plugin_with_error(self):
        """Test activation when plugin raises an error."""
        manager = SimplePluginManager()

        # Add a plugin that raises error on activation
        plugin = Mock()
        plugin.name = "error_plugin"
        plugin.activate = Mock(side_effect=RuntimeError("Activation failed"))

        manager.plugins["error_plugin"] = PluginInfo(
            name="error_plugin",
            module=Mock(),
            instance=plugin,
            active=False
        )

        result = manager.activate_plugin("error_plugin")
        assert result is False
        assert manager.plugins["error_plugin"].error == "Activation failed"
        assert manager.plugins["error_plugin"].active is False

    def test_deactivate_nonexistent_plugin(self):
        """Test deactivating a plugin that doesn't exist."""
        manager = SimplePluginManager()
        result = manager.deactivate_plugin("nonexistent")
        assert result is False

    def test_deactivate_inactive_plugin(self):
        """Test deactivating an already inactive plugin."""
        manager = SimplePluginManager()

        # Add an inactive plugin
        plugin = Mock()
        plugin.name = "test"
        plugin.deactivate = Mock()

        manager.plugins["test"] = PluginInfo(
            name="test",
            module=Mock(),
            instance=plugin,
            active=False  # Already inactive
        )

        result = manager.deactivate_plugin("test")
        assert result is True
        # deactivate() should not be called since already inactive
        plugin.deactivate.assert_not_called()

    def test_deactivate_plugin_with_error(self):
        """Test deactivation when plugin raises an error."""
        manager = SimplePluginManager()

        # Add a plugin that raises error on deactivation
        plugin = Mock()
        plugin.name = "error_plugin"
        plugin.deactivate = Mock(side_effect=RuntimeError("Deactivation failed"))

        manager.plugins["error_plugin"] = PluginInfo(
            name="error_plugin",
            module=Mock(),
            instance=plugin,
            active=True
        )

        result = manager.deactivate_plugin("error_plugin")
        assert result is False
        # Plugin should remain active if deactivation fails
        assert manager.plugins["error_plugin"].active is True


class TestPluginLoadingErrors:
    """Test error handling in plugin loading."""

    def test_load_plugin_from_module_import_error(self):
        """Test loading plugin when module import fails."""
        manager = SimplePluginManager()

        with patch('importlib.import_module', side_effect=ImportError("Module not found")):
            result = manager.load_plugin_from_module("nonexistent.module", "Plugin")
            assert result is False

    def test_load_plugin_from_module_missing_class(self):
        """Test loading plugin when class doesn't exist in module."""
        manager = SimplePluginManager()

        # Create a module without the requested attribute using types.ModuleType
        import types
        mock_module = types.ModuleType("test_module")
        # Don't add the NonExistentClass to the module

        with patch('importlib.import_module', return_value=mock_module):
            result = manager.load_plugin_from_module("test.module", "NonExistentClass")
            assert result is False

    def test_load_plugin_from_module_instantiation_error(self):
        """Test loading plugin when instantiation fails."""
        manager = SimplePluginManager()

        mock_module = Mock()
        mock_class = Mock(side_effect=RuntimeError("Cannot instantiate"))
        mock_module.PluginClass = mock_class

        with patch('importlib.import_module', return_value=mock_module):
            result = manager.load_plugin_from_module("test.module", "PluginClass")
            assert result is False

    def test_load_plugin_from_file_no_spec(self):
        """Test loading plugin when spec creation fails."""
        manager = SimplePluginManager()

        with patch('importlib.util.spec_from_file_location', return_value=None):
            result = manager.load_plugin_from_file("/path/to/plugin.py", "Plugin")
            assert result is False

    def test_load_plugin_from_file_no_loader(self):
        """Test loading plugin when spec has no loader."""
        manager = SimplePluginManager()

        mock_spec = Mock()
        mock_spec.loader = None

        with patch('importlib.util.spec_from_file_location', return_value=mock_spec):
            result = manager.load_plugin_from_file("/path/to/plugin.py", "Plugin")
            assert result is False

    def test_load_plugin_from_file_exec_error(self):
        """Test loading plugin when module execution fails."""
        manager = SimplePluginManager()

        mock_spec = Mock()
        mock_loader = Mock()
        mock_loader.exec_module = Mock(side_effect=RuntimeError("Exec failed"))
        mock_spec.loader = mock_loader

        with patch('importlib.util.spec_from_file_location', return_value=mock_spec):
            with patch('importlib.util.module_from_spec', return_value=Mock()):
                result = manager.load_plugin_from_file("/path/to/plugin.py", "Plugin")
                assert result is False


class TestPluginListingAndRetrieval:
    """Test plugin listing and retrieval methods."""

    def test_get_plugin_active(self):
        """Test getting an active plugin."""
        manager = SimplePluginManager()

        plugin = Mock()
        plugin.name = "test"

        manager.plugins["test"] = PluginInfo(
            name="test",
            module=Mock(),
            instance=plugin,
            active=True
        )

        result = manager.get_plugin("test")
        assert result is plugin

    def test_get_plugin_inactive(self):
        """Test getting an inactive plugin returns None."""
        manager = SimplePluginManager()

        plugin = Mock()
        plugin.name = "test"

        manager.plugins["test"] = PluginInfo(
            name="test",
            module=Mock(),
            instance=plugin,
            active=False
        )

        result = manager.get_plugin("test")
        assert result is None

    def test_get_plugin_nonexistent(self):
        """Test getting a non-existent plugin returns None."""
        manager = SimplePluginManager()
        result = manager.get_plugin("nonexistent")
        assert result is None

    def test_list_plugins_with_versions(self):
        """Test listing plugins with version info."""
        manager = SimplePluginManager()

        # Add plugin with version
        plugin1 = Mock()
        plugin1.name = "plugin1"
        plugin1.version = "2.0.0"

        manager.plugins["plugin1"] = PluginInfo(
            name="plugin1",
            module=Mock(),
            instance=plugin1,
            active=True
        )

        # Add plugin without version - Mock will auto-create version attribute
        plugin2 = Mock(spec=['name'])  # Use spec to prevent auto-creation of version
        plugin2.name = "plugin2"
        # No version attribute

        manager.plugins["plugin2"] = PluginInfo(
            name="plugin2",
            module=Mock(),
            instance=plugin2,
            active=False,
            error="Some error"
        )

        plugins = manager.list_plugins()

        assert "plugin1" in plugins
        assert plugins["plugin1"]["active"] is True
        assert plugins["plugin1"]["version"] == "2.0.0"
        assert plugins["plugin1"]["error"] is None

        assert "plugin2" in plugins
        assert plugins["plugin2"]["active"] is False
        assert plugins["plugin2"]["version"] == "1.0.0"  # Default
        assert plugins["plugin2"]["error"] == "Some error"


class TestActivateDeactivateAll:
    """Test bulk activation/deactivation."""

    def test_activate_all(self):
        """Test activating all plugins."""
        manager = SimplePluginManager()

        # Add multiple plugins
        for i in range(3):
            plugin = Mock()
            plugin.name = f"plugin{i}"
            plugin.activate = Mock()

            manager.plugins[f"plugin{i}"] = PluginInfo(
                name=f"plugin{i}",
                module=Mock(),
                instance=plugin,
                active=False
            )

        activated = manager.activate_all()
        assert activated == 3

        for plugin_info in manager.plugins.values():
            assert plugin_info.active is True
            plugin_info.instance.activate.assert_called_once()

    def test_deactivate_all(self):
        """Test deactivating all plugins."""
        manager = SimplePluginManager()

        # Add multiple active plugins
        for i in range(3):
            plugin = Mock()
            plugin.name = f"plugin{i}"
            plugin.deactivate = Mock()

            manager.plugins[f"plugin{i}"] = PluginInfo(
                name=f"plugin{i}",
                module=Mock(),
                instance=plugin,
                active=True
            )

        deactivated = manager.deactivate_all()
        assert deactivated == 3

        for plugin_info in manager.plugins.values():
            assert plugin_info.active is False
            plugin_info.instance.deactivate.assert_called_once()


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    def test_load_plugin_file_path(self):
        """Test load_plugin with file path."""
        with patch.object(plugin_manager, 'load_plugin_from_file') as mock_load:
            mock_load.return_value = True

            # Path with slash indicates file
            result = load_plugin("/path/to/plugin.py", "MyPlugin")

            assert result is True
            mock_load.assert_called_once_with("/path/to/plugin.py", "MyPlugin")

    def test_load_plugin_file_with_py_extension(self):
        """Test load_plugin with .py file."""
        with patch.object(plugin_manager, 'load_plugin_from_file') as mock_load:
            mock_load.return_value = True

            # .py extension indicates file
            result = load_plugin("plugin.py", "MyPlugin")

            assert result is True
            mock_load.assert_called_once_with("plugin.py", "MyPlugin")

    def test_get_plugin_convenience(self):
        """Test get_plugin convenience function."""
        mock_plugin = Mock()
        with patch.object(plugin_manager, 'get_plugin') as mock_get:
            mock_get.return_value = mock_plugin

            result = get_plugin("test")

            assert result is mock_plugin
            mock_get.assert_called_once_with("test")
"""
Simple plugin system using Python's importlib - no bloat.

Replace 13,500+ lines of enterprise plugin architecture with ~200 lines.
Use standard Python import mechanisms instead of custom loaders.
"""

import importlib
import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

import structlog

logger = structlog.get_logger(__name__)


class Plugin(Protocol):
    """Simple plugin interface."""

    name: str
    version: str = "1.0.0"

    def activate(self) -> None:
        """Activate the plugin."""
        ...

    def deactivate(self) -> None:
        """Deactivate the plugin."""
        ...


@dataclass
class PluginInfo:
    """Plugin metadata."""

    name: str
    module: Any
    instance: Optional[Plugin] = None
    active: bool = False
    error: Optional[str] = None


class SimplePluginManager:
    """Simple plugin manager using importlib."""

    def __init__(self) -> None:
        self.plugins: Dict[str, PluginInfo] = {}
        self.plugin_paths: List[Path] = []

    def add_plugin_path(self, path: str | Path) -> None:
        """Add a directory to search for plugins."""
        self.plugin_paths.append(Path(path))

    def load_plugin_from_module(self, module_name: str, plugin_class: str) -> bool:
        """Load plugin from installed module."""
        try:
            module = importlib.import_module(module_name)
            plugin_cls = getattr(module, plugin_class)
            instance = plugin_cls()

            self.plugins[instance.name] = PluginInfo(
                name=instance.name, module=module, instance=instance
            )
            logger.info("Loaded plugin from module", plugin=instance.name, module=module_name)
            return True

        except Exception as e:
            logger.error("Failed to load plugin from module", module=module_name, error=str(e))
            return False

    def load_plugin_from_file(self, file_path: str | Path, plugin_class: str) -> bool:
        """Load plugin from Python file."""
        try:
            file_path = Path(file_path)
            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            if not spec or not spec.loader:
                raise ImportError(f"Cannot load spec from {file_path}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            plugin_cls = getattr(module, plugin_class)
            instance = plugin_cls()

            self.plugins[instance.name] = PluginInfo(
                name=instance.name, module=module, instance=instance
            )
            logger.info("Loaded plugin from file", plugin=instance.name, file=str(file_path))
            return True

        except Exception as e:
            logger.error("Failed to load plugin from file", file=str(file_path), error=str(e))
            return False

    def discover_plugins(self, pattern: str = "*_plugin.py") -> int:
        """Auto-discover plugins in plugin paths."""
        discovered = 0
        for plugin_path in self.plugin_paths:
            if not plugin_path.exists():
                continue

            for plugin_file in plugin_path.glob(pattern):
                if plugin_file.is_file():
                    # Try to load with common class name patterns
                    class_names = [
                        plugin_file.stem.replace("_", "").title() + "Plugin",
                        plugin_file.stem.title().replace("_", "") + "Plugin",
                        "Plugin",
                    ]

                    for class_name in class_names:
                        if self.load_plugin_from_file(plugin_file, class_name):
                            discovered += 1
                            break

        logger.info("Plugin discovery completed", discovered=discovered)
        return discovered

    def activate_plugin(self, name: str) -> bool:
        """Activate a plugin."""
        if name not in self.plugins:
            logger.warning("Plugin not found", plugin=name)
            return False

        plugin_info = self.plugins[name]
        if plugin_info.active:
            logger.info("Plugin already active", plugin=name)
            return True

        try:
            if plugin_info.instance:
                plugin_info.instance.activate()
            plugin_info.active = True
            plugin_info.error = None
            logger.info("Plugin activated", plugin=name)
            return True

        except Exception as e:
            error_msg = str(e)
            plugin_info.error = error_msg
            logger.error("Failed to activate plugin", plugin=name, error=error_msg)
            return False

    def deactivate_plugin(self, name: str) -> bool:
        """Deactivate a plugin."""
        if name not in self.plugins:
            return False

        plugin_info = self.plugins[name]
        if not plugin_info.active:
            return True

        try:
            if plugin_info.instance:
                plugin_info.instance.deactivate()
            plugin_info.active = False
            logger.info("Plugin deactivated", plugin=name)
            return True

        except Exception as e:
            logger.error("Failed to deactivate plugin", plugin=name, error=str(e))
            return False

    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get active plugin instance."""
        plugin_info = self.plugins.get(name)
        if plugin_info and plugin_info.active:
            return plugin_info.instance
        return None

    def list_plugins(self) -> Dict[str, Dict[str, Any]]:
        """List all plugins with status."""
        return {
            name: {
                "active": info.active,
                "version": getattr(info.instance, "version", "1.0.0") if info.instance else None,
                "error": info.error,
            }
            for name, info in self.plugins.items()
        }

    def activate_all(self) -> int:
        """Activate all loaded plugins."""
        activated = 0
        for name in self.plugins:
            if self.activate_plugin(name):
                activated += 1
        return activated

    def deactivate_all(self) -> int:
        """Deactivate all plugins."""
        deactivated = 0
        for name in list(self.plugins.keys()):
            if self.deactivate_plugin(name):
                deactivated += 1
        return deactivated


# Global instance
plugin_manager = SimplePluginManager()


# Convenience functions
def load_plugin(module_or_file: str, plugin_class: str = "Plugin") -> bool:
    """Load plugin from module name or file path."""
    if "/" in module_or_file or module_or_file.endswith(".py"):
        return plugin_manager.load_plugin_from_file(module_or_file, plugin_class)
    else:
        return plugin_manager.load_plugin_from_module(module_or_file, plugin_class)


def get_plugin(name: str) -> Optional[Plugin]:
    """Get active plugin by name."""
    return plugin_manager.get_plugin(name)


# Example usage:
#
# # Load from installed package
# load_plugin("my_auth_plugin", "AuthPlugin")
#
# # Load from file
# load_plugin("/path/to/my_plugin.py", "MyPlugin")
#
# # Auto-discover plugins
# plugin_manager.add_plugin_path("./plugins")
# plugin_manager.discover_plugins()
#
# # Activate plugin
# plugin_manager.activate_plugin("my_auth_plugin")
#
# # Use plugin
# auth_plugin = get_plugin("my_auth_plugin")
# if auth_plugin:
#     auth_plugin.some_method()

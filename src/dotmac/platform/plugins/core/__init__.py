"""
Core plugin system components.

Contains base classes, interfaces, and fundamental plugin infrastructure.
"""

from .dependency_resolver import DependencyResolver
from .exceptions import (
    PluginConfigError,
    PluginDependencyError,
    PluginError,
    PluginNotFoundError,
    PluginValidationError,
)
from .lifecycle_manager import LifecycleManager
from .manager import PluginManager
from .plugin_base import BasePlugin, PluginMetadata, PluginStatus
from .registry import PluginRegistry

__all__ = [
    "BasePlugin",
    "PluginMetadata",
    "PluginStatus",
    "PluginRegistry",
    "LifecycleManager",
    "DependencyResolver",
    "PluginManager",
    "PluginError",
    "PluginNotFoundError",
    "PluginDependencyError",
    "PluginValidationError",
    "PluginConfigError",
]

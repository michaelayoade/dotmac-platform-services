"""
Plugin system for DotMac Platform Services.

This package provides a dynamic plugin system that allows plugins to:
- Register their own configuration schemas
- Have UI forms auto-generated from schemas
- Store sensitive configuration in Vault
- Provide health checks and connection tests
"""

from .schema import (
    FieldSpec,
    FieldType,
    PluginConfig,
    PluginInstance,
    PluginStatus,
    PluginType,
    PluginHealthCheck,
    PluginTestResult,
    SelectOption,
    ValidationRule,
)
from .registry import PluginRegistry, get_plugin_registry
from .interfaces import PluginProvider, PluginInterface

__all__ = [
    # Schema types
    "FieldSpec",
    "FieldType",
    "PluginConfig",
    "PluginInstance",
    "PluginStatus",
    "PluginType",
    "PluginHealthCheck",
    "PluginTestResult",
    "SelectOption",
    "ValidationRule",
    # Core components
    "PluginRegistry",
    "get_plugin_registry",
    "PluginProvider",
    "PluginInterface",
]
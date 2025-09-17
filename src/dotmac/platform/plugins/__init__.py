"""
DotMac Plugins - Universal Plugin System

A comprehensive, reusable plugin system for any application domain.
Supports dynamic loading, dependency management, and domain-specific adapters.

Example Usage:
    ```python
    from dotmac_plugins import PluginRegistry, PluginManager

    # Initialize plugin system
    registry = PluginRegistry()
    manager = PluginManager(registry)

    # Load plugins from configuration
    await manager.load_plugins_from_config("plugins.yaml")

    # Execute plugin methods
    result = await manager.execute_plugin(
        domain="communication",
        plugin_name="email_sender",
        method="send_message",
        recipient="user@example.com",
        message="Hello World"
    )
    ```

Architecture:
    - Core: Base plugin interfaces and lifecycle management
    - Registry: Plugin discovery, loading, and dependency resolution
    - Middleware: Validation, rate limiting, metrics collection
    - Adapters: Domain-specific plugin implementations
    - Loaders: Multiple plugin source support (YAML, Python, remote)
"""

from typing import Optional

from .core.dependency_resolver import DependencyResolver
from .core.exceptions import (
    PluginConfigError,
    PluginDependencyError,
    PluginError,
    PluginNotFoundError,
    PluginValidationError,
)
from .core.lifecycle_manager import LifecycleManager

# Main plugin manager for easy access
from .core.manager import PluginManager
from .core.plugin_base import BasePlugin, PluginMetadata, PluginStatus
from .core.registry import PluginRegistry
from .loaders.python_loader import PythonPluginLoader
from .loaders.remote_loader import RemotePluginLoader
from .loaders.yaml_loader import YamlPluginLoader
from .middleware.metrics import MetricsMiddleware
from .middleware.rate_limiting import RateLimitingMiddleware
from .middleware.validation import ValidationMiddleware

__version__ = "1.0.0"
__author__ = "DotMac Framework Team"
__email__ = "dev@dotmac.com"

# Default configuration for the plugin system
DEFAULT_CONFIG = {
    "registry": {
        "auto_discover": True,
        "plugin_dirs": ["plugins", "./plugins", "~/.dotmac/plugins"],
        "cache_enabled": True,
        "cache_ttl": 3600,
    },
    "lifecycle": {
        "auto_start": True,
        "graceful_shutdown": True,
        "startup_timeout": 30,
        "shutdown_timeout": 10,
    },
    "security": {
        "sandbox_enabled": True,
        "max_memory_mb": 256,
        "max_cpu_time": 10,
        "allowed_imports": ["datetime", "json", "re", "uuid"],
        "blocked_imports": ["os", "sys", "subprocess"],
    },
    "middleware": {
        "validation_enabled": True,
        "metrics_enabled": True,
        "rate_limiting_enabled": False,
        "default_rate_limit": "100/minute",
    },
    "loaders": {
        "yaml_enabled": True,
        "python_enabled": True,
        "remote_enabled": False,
        "remote_timeout": 30,
    },
}


def get_config():
    """Get default plugin system configuration."""
    return DEFAULT_CONFIG.copy()


def create_plugin_system(config: Optional[dict] = None) -> PluginManager:
    """
    Create a fully configured plugin system.

    Args:
        config: Optional configuration dictionary

    Returns:
        Configured PluginManager instance
    """
    if config is None:
        config = get_config()

    # Create manager with config (it creates its own registry internally)
    manager = PluginManager(config=config)

    # Configure middleware if enabled
    if config.get("middleware", {}).get("validation_enabled", True):
        manager.add_middleware(ValidationMiddleware())

    if config.get("middleware", {}).get("metrics_enabled", True):
        manager.add_middleware(MetricsMiddleware())

    if config.get("middleware", {}).get("rate_limiting_enabled", False):
        manager.add_middleware(RateLimitingMiddleware())

    return manager


async def quick_start(plugin_config_path: Optional[str] = None) -> PluginManager:
    """
    Quick start function for common plugin system setup.

    Args:
        plugin_config_path: Path to plugin configuration file

    Returns:
        Initialized and ready-to-use PluginManager
    """
    manager = create_plugin_system()

    if plugin_config_path:
        await manager.load_plugins_from_config(plugin_config_path)
    else:
        # Auto-discover plugins in default directories
        await manager.discover_plugins()

    return manager


# Convenience aliases for backward compatibility
PluginSystem = PluginManager
create_plugin_manager = create_plugin_system

__all__ = [
    # Core components
    "BasePlugin",
    "PluginMetadata",
    "PluginStatus",
    "PluginRegistry",
    "PluginManager",
    "LifecycleManager",
    "DependencyResolver",
    # Exceptions
    "PluginError",
    "PluginNotFoundError",
    "PluginDependencyError",
    "PluginValidationError",
    "PluginConfigError",
    # Loaders
    "YamlPluginLoader",
    "PythonPluginLoader",
    "RemotePluginLoader",
    # Middleware
    "ValidationMiddleware",
    "RateLimitingMiddleware",
    "MetricsMiddleware",
    # Convenience functions
    "create_plugin_system",
    "create_plugin_manager",
    "quick_start",
    "get_config",
    # Aliases
    "PluginSystem",
    # Metadata
    "__version__",
    "__author__",
    "__email__",
]

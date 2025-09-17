"""
Main plugin manager orchestrating all plugin system components.

Provides high-level interface for plugin management, loading, and execution.
"""

import asyncio

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Union

from .dependency_resolver import DependencyResolver
from .exceptions import (

    PluginConfigError,
    PluginError,
    PluginExecutionError,
    PluginNotFoundError,
)
from dotmac.platform.observability.unified_logging import get_logger

from .lifecycle_manager import LifecycleEvent, LifecycleManager
from .plugin_base import BasePlugin, PluginStatus
from .registry import PluginRegistry

class PluginManager:
    """
    Central plugin management system.

    Orchestrates plugin loading, dependency resolution, lifecycle management,
    and provides a unified interface for plugin operations.
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        # Configuration
        self.config = config or {}

        # Core components
        import datetime

        self.registry = PluginRegistry()
        self.dependency_resolver = DependencyResolver()
        self.lifecycle_manager = LifecycleManager(
            registry=self.registry,
            dependency_resolver=self.dependency_resolver,
            default_timeout=self.config.get("default_timeout", 30.0),
            health_check_interval=self.config.get("health_check_interval", 60.0),
            max_concurrent_operations=self.config.get("max_concurrent_operations", 10),
        )

        # Plugin loaders (will be populated when loaders are created)
        self._loaders: dict[str, Any] = {}

        # Middleware stack
        self._middleware_stack: list[Any] = []

        # State
        self._initialized = False
        self._shutdown = False
        self._logger = get_logger("plugins.manager")

        # Plugin execution cache
        self._execution_cache: dict[str, Any] = {}

        # Setup event handlers
        self._setup_event_handlers()

        self._logger.info("PluginManager initialized")

    # Initialization and configuration

    async def initialize(self) -> None:
        """Initialize the plugin manager and start health monitoring."""
        if self._initialized:
            self._logger.warning("PluginManager is already initialized")
            return

        self._logger.info("Initializing PluginManager")

        try:
            # Start health monitoring if enabled
            if self.config.get("enable_health_monitoring", True):
                await self.lifecycle_manager.start_health_monitoring()

            self._initialized = True
            self._logger.info("PluginManager initialization complete")

        except Exception as e:
            self._logger.error(f"Failed to initialize PluginManager: {e}")
            raise PluginError(f"PluginManager initialization failed: {e}") from e

    async def shutdown(self) -> None:
        """Shutdown the plugin manager and all plugins."""
        if self._shutdown:
            return

        self._logger.info("Shutting down PluginManager")
        self._shutdown = True

        try:
            # Shutdown all plugins
            await self.lifecycle_manager.shutdown_all_plugins(force=True)

            # Stop health monitoring
            await self.lifecycle_manager.stop_health_monitoring()

            # Cleanup lifecycle manager
            await self.lifecycle_manager.cleanup()

            self._logger.info("PluginManager shutdown complete")

        except Exception as e:
            self._logger.error(f"Error during PluginManager shutdown: {e}")

    # Plugin registration and management

    async def register_plugin(self, plugin: BasePlugin, auto_initialize: bool = True) -> None:
        """
        Register a plugin with the manager.

        Args:
            plugin: Plugin instance to register
            auto_initialize: Whether to automatically initialize the plugin
        """
        if self._shutdown:
            raise PluginError("Cannot register plugins during shutdown")

        plugin_key = f"{plugin.domain}.{plugin.name}"
        self._logger.info(f"Registering plugin: {plugin_key}")

        try:
            # Register with registry
            await self.registry.register_plugin(plugin)

            # Add to dependency resolver
            self.dependency_resolver.add_plugin(plugin_key, plugin.metadata)

            # Auto-initialize if requested
            if auto_initialize:
                await self.lifecycle_manager.initialize_plugin(plugin_key)

            self._logger.info(f"Plugin registered successfully: {plugin_key}")

        except Exception as e:
            self._logger.error(f"Failed to register plugin {plugin_key}: {e}")

            # Cleanup on failure
            try:
                await self.registry.unregister_plugin(plugin.domain, plugin.name)
                self.dependency_resolver.remove_plugin(plugin_key)
            except Exception as cleanup_error:
                self._logger.warning(
                    f"Failed to cleanup after plugin registration failure: {cleanup_error}"
                )

            raise PluginError(
                f"Plugin registration failed: {e}",
                plugin_name=plugin.name,
                plugin_domain=plugin.domain,
            ) from e

    async def unregister_plugin(self, domain: str, name: str) -> bool:
        """
        Unregister a plugin from the manager.

        Args:
            domain: Plugin domain
            name: Plugin name

        Returns:
            True if plugin was unregistered
        """
        plugin_key = f"{domain}.{name}"
        self._logger.info(f"Unregistering plugin: {plugin_key}")

        try:
            # Shutdown plugin first
            await self.lifecycle_manager.shutdown_plugin(plugin_key)

            # Remove from registry
            plugin = await self.registry.unregister_plugin(domain, name)

            # Remove from dependency resolver
            self.dependency_resolver.remove_plugin(plugin_key)

            # Clear execution cache
            self._execution_cache.pop(plugin_key, None)

            success = plugin is not None
            if success:
                self._logger.info(f"Plugin unregistered successfully: {plugin_key}")
            else:
                self._logger.warning(f"Plugin was not found during unregistration: {plugin_key}")

            return success

        except Exception as e:
            self._logger.error(f"Failed to unregister plugin {plugin_key}: {e}")
            raise PluginError(
                f"Plugin unregistration failed: {e}",
                plugin_name=name,
                plugin_domain=domain,
            ) from e

    # Plugin loading from external sources

    async def load_plugins_from_config(
        self, config_path: Union[str, Path], auto_initialize: bool = True
    ) -> dict[str, bool]:
        """
        Load plugins from a configuration file.

        Args:
            config_path: Path to the plugin configuration file
            auto_initialize: Whether to automatically initialize loaded plugins

        Returns:
            Dict mapping plugin keys to load success status
        """
        config_path = Path(config_path)
        self._logger.info(f"Loading plugins from config: {config_path}")

        if not config_path.exists():
            raise PluginConfigError(
                "config_file",
                config_path=str(config_path),
                config_errors=[f"Configuration file not found: {config_path}"],
            )

        # Import loader here to avoid circular imports
        from ..loaders.yaml_loader import YamlPluginLoader

        loader = YamlPluginLoader()

        try:
            plugins = await loader.load_plugins_from_file(config_path)
            results = {}

            # Register all loaded plugins
            for plugin in plugins:
                plugin_key = f"{plugin.domain}.{plugin.name}"

                try:
                    await self.register_plugin(plugin, auto_initialize=auto_initialize)
                    results[plugin_key] = True

                except Exception as e:
                    self._logger.error(f"Failed to register plugin {plugin_key}: {e}")
                    results[plugin_key] = False

            successful_count = sum(1 for success in results.values() if success)
            self._logger.info(f"Loaded {successful_count}/{len(plugins)} plugins from config")

            return results

        except Exception as e:
            self._logger.error(f"Failed to load plugins from config {config_path}: {e}")
            raise PluginConfigError(
                "config_loader", config_path=str(config_path), original_error=e
            ) from e

    async def load_plugin_from_module(
        self,
        module_path: str,
        plugin_class_name: str,
        plugin_config: Optional[dict[str, Any]] = None,
        auto_initialize: bool = True,
    ) -> str:
        """
        Load a plugin from a Python module.

        Args:
            module_path: Python module path (e.g., 'mypackage.myplugin')
            plugin_class_name: Name of the plugin class
            plugin_config: Configuration for the plugin
            auto_initialize: Whether to automatically initialize the plugin

        Returns:
            Plugin key of the loaded plugin
        """
        self._logger.info(f"Loading plugin from module: {module_path}.{plugin_class_name}")

        # Import loader here to avoid circular imports
        from ..loaders.python_loader import PythonPluginLoader

        loader = PythonPluginLoader()

        try:
            plugin = await loader.load_plugin_from_module(
                module_path, plugin_class_name, plugin_config
            )

            plugin_key = f"{plugin.domain}.{plugin.name}"
            await self.register_plugin(plugin, auto_initialize=auto_initialize)

            self._logger.info(f"Loaded plugin from module: {plugin_key}")
            return plugin_key

        except Exception as e:
            self._logger.error(f"Failed to load plugin from module {module_path}: {e}")
            raise PluginError(f"Module plugin loading failed: {e}") from e

    # Plugin discovery and access

    async def discover_plugins(self) -> dict[str, list[str]]:
        """
        Discover plugins in default directories.

        Returns:
            Dict mapping domain to list of discovered plugin names
        """
        discovered = {}
        plugin_dirs = self.config.get("registry", {}).get("plugin_dirs", ["plugins", "./plugins"])

        for plugin_dir in plugin_dirs:
            try:
                plugin_path = Path(plugin_dir)
                if plugin_path.exists() and plugin_path.is_dir():
                    self._logger.info(f"Scanning for plugins in: {plugin_path}")

                    # Basic Python module discovery
                    for py_file in plugin_path.rglob("*.py"):
                        if py_file.name.startswith("_"):
                            continue

                        # Simple heuristic: look for plugin-like files
                        if "plugin" in py_file.name.lower():
                            domain = (
                                py_file.parent.name if py_file.parent != plugin_path else "default"
                            )
                            if domain not in discovered:
                                discovered[domain] = []
                            discovered[domain].append(py_file.stem)

            except Exception as e:
                self._logger.warning(f"Failed to scan plugin directory {plugin_dir}: {e}")

        self._logger.info(f"Discovered plugins: {discovered}")
        return discovered

    async def get_plugin(self, domain: str, name: str) -> Optional[BasePlugin]:
        """Get a plugin by domain and name."""
        return await self.registry.get_plugin(domain, name)

    async def find_plugins(
        self,
        domain: Optional[str] = None,
        status: Optional[PluginStatus] = None,
        tags: Optional[set[str]] = None,
        categories: Optional[set[str]] = None,
        name_pattern: Optional[str] = None,
    ) -> list[BasePlugin]:
        """Find plugins matching specified criteria."""
        return await self.registry.find_plugins(
            domain=domain,
            status=status,
            tags=tags,
            categories=categories,
            name_pattern=name_pattern,
        )

    async def list_plugins(self, domain: Optional[str] = None) -> list[BasePlugin]:
        """List all plugins or plugins in a specific domain."""
        if domain:
            return await self.registry.list_plugins_by_domain(domain)
        else:
            return await self.registry.list_all_plugins()

    async def get_available_domains(self) -> list[str]:
        """Get list of all available plugin domains."""
        return await self.registry.get_domains()

    # Plugin execution

    async def execute_plugin(
        self, domain: str, plugin_name: str, method: str, *args, **kwargs
    ) -> Any:
        """
        Execute a method on a plugin.

        Args:
            domain: Plugin domain
            plugin_name: Plugin name
            method: Method name to execute
            *args: Positional arguments for the method
            **kwargs: Keyword arguments for the method

        Returns:
            Result of the method execution

        Raises:
            PluginNotFoundError: If plugin is not found
            PluginExecutionError: If method execution fails
        """
        plugin = await self.get_plugin(domain, plugin_name)

        if not plugin:
            available_plugins = [f"{p.domain}.{p.name}" for p in await self.list_plugins(domain)]

            raise PluginNotFoundError(
                plugin_name, domain=domain, available_plugins=available_plugins
            )

        if not plugin.is_active:
            raise PluginExecutionError(
                plugin_name,
                method,
                execution_context={"plugin_status": plugin.status.value},
            )

        # Check if method exists
        if not hasattr(plugin, method):
            raise PluginExecutionError(
                plugin_name,
                method,
                execution_context={"error": f"Method '{method}' not found"},
            )

        try:
            plugin_method = getattr(plugin, method)

            # Execute method (handle both sync and async)
            if asyncio.iscoroutinefunction(plugin_method):
                result = await plugin_method(*args, **kwargs)
            else:
                result = plugin_method(*args, **kwargs)

            # Record successful execution
            plugin._record_success()

            return result

        except Exception as e:
            # Record failed execution
            plugin._record_error()

            raise PluginExecutionError(
                plugin_name,
                method,
                original_error=e,
                execution_context={"args": args, "kwargs": kwargs},
            ) from e

    # Batch operations

    async def initialize_plugins_by_domain(
        self, domain: str, parallel: bool = True
    ) -> dict[str, bool]:
        """Initialize all plugins in a specific domain."""
        plugins = await self.registry.list_plugins_by_domain(domain)
        plugin_keys = {f"{p.domain}.{p.name}" for p in plugins}

        return await self.lifecycle_manager.initialize_plugins(plugin_keys, parallel=parallel)

    async def shutdown_plugins_by_domain(self, domain: str) -> dict[str, bool]:
        """Shutdown all plugins in a specific domain."""
        plugins = await self.registry.list_plugins_by_domain(domain)
        results = {}

        for plugin in plugins:
            plugin_key = f"{plugin.domain}.{plugin.name}"
            try:
                success = await self.lifecycle_manager.shutdown_plugin(plugin_key)
                results[plugin_key] = success
            except Exception as e:
                self._logger.error(f"Error shutting down plugin {plugin_key}: {e}")
                results[plugin_key] = False

        return results

    # Health and monitoring

    async def get_system_health(self) -> dict[str, Any]:
        """Get comprehensive system health information."""
        registry_status = await self.registry.get_registry_status()
        lifecycle_metrics = self.lifecycle_manager.get_system_metrics()

        # Get plugin health summary
        all_plugins = await self.registry.list_all_plugins()
        plugin_health = {
            "total_plugins": len(all_plugins),
            "active_plugins": len([p for p in all_plugins if p.is_active]),
            "healthy_plugins": len([p for p in all_plugins if p.is_healthy]),
            "error_plugins": len([p for p in all_plugins if p.status == PluginStatus.ERROR]),
        }

        return {
            "manager": {
                "initialized": self._initialized,
                "shutdown": self._shutdown,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "registry": registry_status,
            "lifecycle": lifecycle_metrics,
            "plugins": plugin_health,
        }

    async def get_plugin_health(self, domain: str, name: str) -> dict[str, Any]:
        """Get health information for a specific plugin."""
        plugin_key = f"{domain}.{name}"
        return await self.lifecycle_manager.perform_health_check(plugin_key)

    # Configuration and middleware

    def add_middleware(self, middleware: Any) -> None:
        """Add middleware to the plugin execution stack."""
        self._middleware_stack.append(middleware)
        self._logger.info(f"Added middleware: {middleware.__class__.__name__}")

    def remove_middleware(self, middleware: Any) -> None:
        """Remove middleware from the plugin execution stack."""
        if middleware in self._middleware_stack:
            self._middleware_stack.remove(middleware)
            self._logger.info(f"Removed middleware: {middleware.__class__.__name__}")

    # Event handling

    def add_lifecycle_event_handler(self, event: LifecycleEvent, handler: callable) -> None:
        """Add a handler for plugin lifecycle events."""
        self.lifecycle_manager.add_event_handler(event, handler)

    def remove_lifecycle_event_handler(self, event: LifecycleEvent, handler: callable) -> None:
        """Remove a lifecycle event handler."""
        self.lifecycle_manager.remove_event_handler(event, handler)

    # Private methods

    def _setup_event_handlers(self) -> None:
        """Setup default event handlers for the plugin manager."""

        async def on_plugin_registered(plugin: BasePlugin) -> None:
            self._logger.info(f"Plugin registered: {plugin.domain}.{plugin.name}")

        async def on_plugin_unregistered(plugin: BasePlugin) -> None:
            self._logger.info(f"Plugin unregistered: {plugin.domain}.{plugin.name}")

        async def on_status_changed(event: LifecycleEvent, plugin: BasePlugin, data: Any) -> None:
            self._logger.info(
                f"Plugin {plugin.domain}.{plugin.name} status changed to {plugin.status.value}"
            )

        async def on_error_occurred(
            event: LifecycleEvent, plugin: BasePlugin, error: Exception
        ) -> None:
            self._logger.error(f"Plugin {plugin.domain}.{plugin.name} error: {error}")

        # Register event handlers
        self.registry.add_registration_callback(on_plugin_registered)
        self.registry.add_unregistration_callback(on_plugin_unregistered)

        self.lifecycle_manager.add_event_handler(LifecycleEvent.STATUS_CHANGED, on_status_changed)
        self.lifecycle_manager.add_event_handler(LifecycleEvent.ERROR_OCCURRED, on_error_occurred)

    # Context manager support

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown()

    def __repr__(self) -> str:
        return f"<PluginManager(initialized={self._initialized}, shutdown={self._shutdown})>"

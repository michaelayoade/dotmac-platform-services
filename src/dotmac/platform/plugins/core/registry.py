"""
Plugin registry for discovery and management.

Centralized registry for all loaded plugins with support for domain-based organization,
dependency tracking, and query capabilities.
"""

import asyncio

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Optional

from .exceptions import PluginDependencyError, PluginError
from .plugin_base import BasePlugin, PluginMetadata, PluginStatus

from dotmac.platform.observability.unified_logging import get_logger
class PluginRegistry:
    """
    Central registry for managing loaded plugins.

    Provides plugin discovery, dependency resolution, and lifecycle management.
    """

    def __init__(self):
        # Main plugin storage: domain -> name -> plugin
        self._plugins: dict[str, dict[str, BasePlugin]] = defaultdict(dict)

        # Metadata storage for fast lookups
        self._metadata: dict[str, PluginMetadata] = {}

        # Dependency tracking
        self._dependencies: dict[str, set[str]] = defaultdict(set)
        self._dependents: dict[str, set[str]] = defaultdict(set)

        # Registry state
        self._lock = asyncio.Lock()  # Use standard asyncio.Lock instead of RWLock
        self._logger = get_logger("plugins.registry")
        self._created_at = datetime.now(timezone.utc)

        # Event callbacks
        self._on_plugin_registered: list[callable] = []
        self._on_plugin_unregistered: list[callable] = []

    # Plugin registration and management

    async def register_plugin(self, plugin: BasePlugin) -> None:
        """
        Register a plugin in the registry.

        Args:
            plugin: Plugin instance to register

        Raises:
            PluginError: If plugin already exists or registration fails
        """
        async with self._lock:
            plugin_key = f"{plugin.domain}.{plugin.name}"

            # Check if plugin already exists
            if plugin_key in self._metadata:
                raise PluginError(
                    f"Plugin '{plugin_key}' is already registered",
                    plugin_name=plugin.name,
                    plugin_domain=plugin.domain,
                )

            try:
                # Register plugin
                self._plugins[plugin.domain][plugin.name] = plugin
                self._metadata[plugin_key] = plugin.metadata

                # Track dependencies
                self._update_dependencies(plugin_key, plugin.metadata.dependencies)

                self._logger.info(f"Registered plugin: {plugin_key}")

                # Notify callbacks
                await self._notify_plugin_registered(plugin)

            except Exception as e:
                # Cleanup on failure
                self._plugins[plugin.domain].pop(plugin.name, None)
                self._metadata.pop(plugin_key, None)
                self._dependencies.pop(plugin_key, None)

                raise PluginError(
                    f"Failed to register plugin '{plugin_key}': {e}",
                    plugin_name=plugin.name,
                    plugin_domain=plugin.domain,
                ) from e

    async def unregister_plugin(self, domain: str, name: str) -> Optional[BasePlugin]:
        """
        Unregister a plugin from the registry.

        Args:
            domain: Plugin domain
            name: Plugin name

        Returns:
            The unregistered plugin, or None if not found
        """
        async with self._lock:
            plugin_key = f"{domain}.{name}"

            # Get plugin before removal
            plugin = self._plugins.get(domain, {}).get(name)
            if not plugin:
                return None

            try:
                # Check for dependent plugins
                dependents = self._dependents.get(plugin_key, set())
                if dependents:
                    active_dependents = []
                    for dependent_key in dependents:
                        dep_domain, dep_name = dependent_key.split(".", 1)
                        dep_plugin = self._plugins.get(dep_domain, {}).get(dep_name)
                        if dep_plugin and dep_plugin.is_active:
                            active_dependents.append(dependent_key)

                    if active_dependents:
                        raise PluginDependencyError(name, [], active_dependents)

                # Remove from registry
                del self._plugins[domain][name]
                del self._metadata[plugin_key]

                # Clean up empty domains
                if not self._plugins[domain]:
                    del self._plugins[domain]

                # Update dependency tracking
                self._remove_dependencies(plugin_key)

                self._logger.info(f"Unregistered plugin: {plugin_key}")

                # Notify callbacks
                await self._notify_plugin_unregistered(plugin)

                return plugin

            except Exception as e:
                self._logger.error(f"Error unregistering plugin {plugin_key}: {e}")
                raise PluginError(
                    f"Failed to unregister plugin '{plugin_key}': {e}",
                    plugin_name=name,
                    plugin_domain=domain,
                ) from e

    # Plugin discovery and access

    async def get_plugin(self, domain: str, name: str) -> Optional[BasePlugin]:
        """
        Get a plugin by domain and name.

        Args:
            domain: Plugin domain
            name: Plugin name

        Returns:
            Plugin instance or None if not found
        """
        async with self._lock:
            return self._plugins.get(domain, {}).get(name)

    async def get_plugin_by_key(self, plugin_key: str) -> Optional[BasePlugin]:
        """
        Get a plugin by its key (domain.name).

        Args:
            plugin_key: Plugin key in format "domain.name"

        Returns:
            Plugin instance or None if not found
        """
        if "." not in plugin_key:
            return None

        domain, name = plugin_key.split(".", 1)
        return await self.get_plugin(domain, name)

    async def find_plugins(
        self,
        domain: Optional[str] = None,
        status: Optional[PluginStatus] = None,
        tags: Optional[set[str]] = None,
        categories: Optional[set[str]] = None,
        name_pattern: Optional[str] = None,
    ) -> list[BasePlugin]:
        """
        Find plugins matching specified criteria.

        Args:
            domain: Filter by domain
            status: Filter by plugin status
            tags: Filter by tags (plugin must have all specified tags)
            categories: Filter by categories (plugin must be in all specified categories)
            name_pattern: Filter by name pattern (simple wildcard matching)

        Returns:
            List of matching plugins
        """
        async with self._lock:
            matching_plugins = []

            # Determine domains to search
            domains_to_search = [domain] if domain else self._plugins.keys()

            for search_domain in domains_to_search:
                if search_domain not in self._plugins:
                    continue

                for plugin in self._plugins[search_domain].values():
                    # Status filter
                    if status and plugin.status != status:
                        continue

                    # Tags filter
                    if tags and not tags.issubset(plugin.metadata.tags):
                        continue

                    # Categories filter
                    if categories and not categories.issubset(plugin.metadata.categories):
                        continue

                    # Name pattern filter
                    if name_pattern:
                        import fnmatch

                        if not fnmatch.fnmatch(plugin.name.lower(), name_pattern.lower()):
                            continue

                    matching_plugins.append(plugin)

            return matching_plugins

    async def list_plugins_by_domain(self, domain: str) -> list[BasePlugin]:
        """
        List all plugins in a specific domain.

        Args:
            domain: Domain name

        Returns:
            List of plugins in the domain
        """
        async with self._lock:
            return list(self._plugins.get(domain, {}).values())

    async def list_all_plugins(self) -> list[BasePlugin]:
        """
        List all registered plugins.

        Returns:
            List of all plugins
        """
        async with self._lock:
            all_plugins = []
            for domain_plugins in self._plugins.values():
                all_plugins.extend(domain_plugins.values())
            return all_plugins

    async def get_domains(self) -> list[str]:
        """
        Get list of all domains with registered plugins.

        Returns:
            List of domain names
        """
        async with self._lock:
            return list(self._plugins.keys())

    # Plugin metadata and information

    async def get_plugin_metadata(self, domain: str, name: str) -> Optional[PluginMetadata]:
        """
        Get plugin metadata without loading the plugin.

        Args:
            domain: Plugin domain
            name: Plugin name

        Returns:
            Plugin metadata or None if not found
        """
        plugin_key = f"{domain}.{name}"
        async with self._lock:
            return self._metadata.get(plugin_key)

    async def plugin_exists(self, domain: str, name: str) -> bool:
        """
        Check if a plugin is registered.

        Args:
            domain: Plugin domain
            name: Plugin name

        Returns:
            True if plugin exists
        """
        async with self._lock:
            return name in self._plugins.get(domain, {})

    async def get_plugin_count(self) -> int:
        """
        Get total number of registered plugins.

        Returns:
            Number of plugins
        """
        async with self._lock:
            return sum(len(domain_plugins) for domain_plugins in self._plugins.values())

    async def get_plugin_count_by_domain(self) -> dict[str, int]:
        """
        Get plugin count grouped by domain.

        Returns:
            Dict mapping domain names to plugin counts
        """
        async with self._lock:
            return {domain: len(plugins) for domain, plugins in self._plugins.items()}

    # Dependency management

    async def get_plugin_dependencies(self, domain: str, name: str) -> set[str]:
        """
        Get direct dependencies of a plugin.

        Args:
            domain: Plugin domain
            name: Plugin name

        Returns:
            Set of dependency plugin keys
        """
        plugin_key = f"{domain}.{name}"
        async with self._lock:
            return self._dependencies.get(plugin_key, set()).copy()

    async def get_plugin_dependents(self, domain: str, name: str) -> set[str]:
        """
        Get plugins that depend on the specified plugin.

        Args:
            domain: Plugin domain
            name: Plugin name

        Returns:
            Set of dependent plugin keys
        """
        plugin_key = f"{domain}.{name}"
        async with self._lock:
            return self._dependents.get(plugin_key, set()).copy()

    async def validate_dependencies(self) -> dict[str, list[str]]:
        """
        Validate all plugin dependencies.

        Returns:
            Dict mapping plugin keys to lists of missing dependencies
        """
        async with self._lock:
            missing_deps = {}

            for plugin_key, dependencies in self._dependencies.items():
                missing = []
                for dep_key in dependencies:
                    if dep_key not in self._metadata:
                        missing.append(dep_key)

                if missing:
                    missing_deps[plugin_key] = missing

            return missing_deps

    # Registry status and health

    async def get_registry_status(self) -> dict[str, Any]:
        """
        Get comprehensive registry status.

        Returns:
            Dict with registry statistics and health information
        """
        async with self._lock:
            total_plugins = await self.get_plugin_count()
            domain_counts = await self.get_plugin_count_by_domain()

            # Count plugins by status
            status_counts = defaultdict(int)
            healthy_plugins = 0

            for domain_plugins in self._plugins.values():
                for plugin in domain_plugins.values():
                    status_counts[plugin.status.value] += 1
                    if plugin.is_healthy:
                        healthy_plugins += 1

            return {
                "total_plugins": total_plugins,
                "healthy_plugins": healthy_plugins,
                "domains": len(self._plugins),
                "domain_counts": dict(domain_counts),
                "status_counts": dict(status_counts),
                "created_at": self._created_at.isoformat(),
                "uptime_seconds": (datetime.now(timezone.utc) - self._created_at).total_seconds(),
            }

    # Event system

    def add_registration_callback(self, callback: callable) -> None:
        """Add callback for plugin registration events."""
        self._on_plugin_registered.append(callback)

    def add_unregistration_callback(self, callback: callable) -> None:
        """Add callback for plugin unregistration events."""
        self._on_plugin_unregistered.append(callback)

    def remove_registration_callback(self, callback: callable) -> None:
        """Remove plugin registration callback."""
        if callback in self._on_plugin_registered:
            self._on_plugin_registered.remove(callback)

    def remove_unregistration_callback(self, callback: callable) -> None:
        """Remove plugin unregistration callback."""
        if callback in self._on_plugin_unregistered:
            self._on_plugin_unregistered.remove(callback)

    # Private helper methods

    def _update_dependencies(self, plugin_key: str, dependencies: list[str]) -> None:
        """Update dependency tracking for a plugin."""
        self._dependencies[plugin_key] = set(dependencies)

        # Update reverse dependency tracking
        for dep_key in dependencies:
            self._dependents[dep_key].add(plugin_key)

    def _remove_dependencies(self, plugin_key: str) -> None:
        """Remove dependency tracking for a plugin."""
        # Remove from dependencies
        dependencies = self._dependencies.pop(plugin_key, set())

        # Update reverse dependencies
        for dep_key in dependencies:
            self._dependents[dep_key].discard(plugin_key)
            if not self._dependents[dep_key]:
                del self._dependents[dep_key]

        # Remove from dependents (this plugin as a dependency)
        if plugin_key in self._dependents:
            del self._dependents[plugin_key]

    async def _notify_plugin_registered(self, plugin: BasePlugin) -> None:
        """Notify callbacks of plugin registration."""
        for callback in self._on_plugin_registered:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(plugin)
                else:
                    callback(plugin)
            except Exception as e:
                self._logger.error(f"Registration callback error: {e}")

    async def _notify_plugin_unregistered(self, plugin: BasePlugin) -> None:
        """Notify callbacks of plugin unregistration."""
        for callback in self._on_plugin_unregistered:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(plugin)
                else:
                    callback(plugin)
            except Exception as e:
                self._logger.error(f"Unregistration callback error: {e}")

    # Context manager support

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cleanup registry on exit
        async with self._lock:
            self._plugins.clear()
            self._metadata.clear()
            self._dependencies.clear()
            self._dependents.clear()

    def __repr__(self) -> str:
        return f"<PluginRegistry(domains={len(self._plugins)}, plugins={sum(len(p) for p in self._plugins.values())})>"

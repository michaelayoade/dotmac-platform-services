"""
Tenant-Isolated Plugin Management System

Provides complete plugin isolation per tenant following DRY container-per-tenant architecture.
Ensures no plugin state or data leakage between tenants.
"""

import asyncio

from typing import Any, Optional
from uuid import UUID

from .._internal.cache import get_cache_service
from .._internal.monitoring import get_monitoring
from ..core.exceptions import PluginError, PluginNotFoundError
from ..core.manager import PluginManager
from ..core.plugin_base import BasePlugin, PluginStatus
from ..core.registry import PluginRegistry
from ..security.plugin_sandbox import PluginSandbox, SecurityScanner

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger("plugins.tenant_isolation")

class TenantPluginRegistry(PluginRegistry):
    """
    Tenant-specific plugin registry with complete isolation.
    Extends base registry with tenant-aware operations.
    """

    def __init__(self, tenant_id: UUID):
        super().__init__()
        self.tenant_id = tenant_id
        self._tenant_prefix = f"tenant:{tenant_id}:plugins"

        # Override registry state with tenant-specific namespacing
        self._plugins: dict[str, dict[str, BasePlugin]] = {}
        self._tenant_cache_key = f"{self._tenant_prefix}:registry"

        logger.info(f"Initialized tenant plugin registry for tenant {tenant_id}")

    async def register_plugin(self, plugin: BasePlugin) -> None:
        """Register plugin with tenant isolation."""
        # Add tenant context to plugin
        plugin._tenant_id = self.tenant_id
        plugin._isolation_context = f"tenant_{self.tenant_id}"

        # Register with tenant-specific key
        await super().register_plugin(plugin)

        # Update tenant-specific cache
        await self._update_tenant_cache()

        logger.info(f"Registered plugin {plugin.domain}.{plugin.name} for tenant {self.tenant_id}")

    async def unregister_plugin(self, domain: str, name: str) -> Optional[BasePlugin]:
        """Unregister plugin with tenant cleanup."""
        plugin = await super().unregister_plugin(domain, name)

        if plugin:
            # Clean up tenant-specific resources
            await self._cleanup_tenant_plugin(plugin)
            await self._update_tenant_cache()

        return plugin

    async def _cleanup_tenant_plugin(self, plugin: BasePlugin) -> None:
        """Clean up tenant-specific plugin resources."""
        try:
            # Clean up plugin data, caches, etc.
            if hasattr(plugin, "cleanup_tenant_data"):
                await plugin.cleanup_tenant_data()

            logger.info(f"Cleaned up tenant data for plugin {plugin.domain}.{plugin.name}")

        except Exception as e:
            logger.error(f"Error cleaning up tenant plugin data: {e}")

    async def _update_tenant_cache(self) -> None:
        """Update tenant-specific cache."""
        cache_manager = get_cache_service()
        if cache_manager:
            await cache_manager.set(
                self._tenant_cache_key,
                await self.get_registry_status(),
                ttl=300,  # 5 minutes
            )

    def get_tenant_id(self) -> UUID:
        """Get the tenant ID this registry serves."""
        return self.tenant_id

class TenantPluginManager:
    """
    Tenant-isolated plugin manager following DRY patterns.

    Provides complete plugin isolation per tenant with no shared state.
    Each tenant gets their own plugin execution environment.
    """

    def __init__(
        self,
        tenant_id: UUID,
        config: Optional[dict[str, Any]] = None,
        security_level: str = "default",
    ):
        self.tenant_id = tenant_id
        self.config = config or {}
        self.security_level = security_level

        # Tenant-specific components
        self.registry = TenantPluginRegistry(tenant_id)
        self.security_manager = SecurityScanner()

        # Tenant-specific plugin manager with isolated configuration
        tenant_config = {
            **self.config,
            "tenant_id": str(tenant_id),
            "isolation_enabled": True,
            "default_timeout": self.config.get("tenant_timeout", 30.0),
        }

        self.plugin_manager = PluginManager(config=tenant_config)
        self.plugin_manager.registry = self.registry  # Use tenant registry

        # Monitoring and logging
        self.monitoring = get_monitoring("plugins.tenant")
        self._logger = get_logger(f"plugins.tenant.{tenant_id}")

        # Tenant state
        self._initialized = False
        self._active_sandboxes: dict[str, PluginSandbox] = {}
        self._plugin_contexts: dict[str, dict[str, Any]] = {}

        self._logger.info(f"Initialized tenant plugin manager for tenant {tenant_id}")

    async def initialize(self) -> None:
        """Initialize tenant plugin manager."""
        if self._initialized:
            self._logger.warning("Tenant plugin manager already initialized")
            return

        self._logger.info(f"Initializing tenant plugin manager for {self.tenant_id}")

        try:
            # Initialize core plugin manager
            await self.plugin_manager.initialize()

            # Setup tenant-specific monitoring
            if self.monitoring:
                self.monitoring.record_metric(
                    name="tenant_plugin_manager_initialized",
                    value=1,
                    tags={"tenant_id": str(self.tenant_id)},
                )

            self._initialized = True
            self._logger.info(f"Tenant plugin manager initialized for {self.tenant_id}")

        except Exception as e:
            self._logger.error(f"Failed to initialize tenant plugin manager: {e}")
            raise PluginError(f"Tenant plugin manager initialization failed: {e}") from e

    async def shutdown(self) -> None:
        """Shutdown tenant plugin manager with complete cleanup."""
        if not self._initialized:
            return

        self._logger.info(f"Shutting down tenant plugin manager for {self.tenant_id}")

        try:
            # Clean up active sandboxes
            await self._cleanup_all_sandboxes()

            # Shutdown plugin manager
            await self.plugin_manager.shutdown()

            # Clear tenant-specific caches
            await self._clear_tenant_caches()

            # Record shutdown
            if self.monitoring:
                self.monitoring.record_metric(
                    name="tenant_plugin_manager_shutdown",
                    value=1,
                    tags={"tenant_id": str(self.tenant_id)},
                )

            self._initialized = False
            self._logger.info(f"Tenant plugin manager shutdown complete for {self.tenant_id}")

        except Exception as e:
            self._logger.error(f"Error during tenant plugin manager shutdown: {e}")

    # ============================================================================
    # Tenant-Isolated Plugin Operations
    # ============================================================================

    async def install_plugin(
        self, plugin: BasePlugin, configuration: Optional[dict[str, Any]] = None
    ) -> str:
        """
        Install plugin with tenant isolation.

        Returns the plugin key for future operations.
        """
        if not self._initialized:
            await self.initialize()

        plugin_key = f"{plugin.domain}.{plugin.name}"
        self._logger.info(f"Installing plugin {plugin_key} for tenant {self.tenant_id}")

        try:
            # Validate plugin code for security
            if hasattr(plugin, "__source__"):
                await self.security_manager.validate_plugin_code(
                    plugin.__source__, plugin.metadata.__dict__
                )

            # Add tenant-specific configuration
            tenant_config = {
                **(configuration or {}),
                "tenant_id": str(self.tenant_id),
                "isolation_context": f"tenant_{self.tenant_id}",
            }

            if hasattr(plugin, "configure"):
                await plugin.configure(tenant_config)

            # Register plugin with tenant registry
            await self.registry.register_plugin(plugin)

            # Create plugin context
            self._plugin_contexts[plugin_key] = {
                "tenant_id": self.tenant_id,
                "configuration": tenant_config,
                "install_time": asyncio.get_event_loop().time(),
                "isolation_level": self.security_level,
            }

            # Record installation
            if self.monitoring:
                self.monitoring.record_metric(
                    name="tenant_plugin_installed",
                    value=1,
                    tags={
                        "tenant_id": str(self.tenant_id),
                        "plugin_key": plugin_key,
                        "plugin_domain": plugin.domain,
                    },
                )

            self._logger.info(f"Plugin {plugin_key} installed for tenant {self.tenant_id}")
            return plugin_key

        except Exception as e:
            self._logger.error(f"Plugin installation failed for {plugin_key}: {e}")
            raise PluginError(f"Tenant plugin installation failed: {e}") from e

    async def uninstall_plugin(self, plugin_key: str) -> bool:
        """
        Uninstall plugin with complete tenant cleanup.
        """
        self._logger.info(f"Uninstalling plugin {plugin_key} for tenant {self.tenant_id}")

        try:
            domain, name = plugin_key.split(".", 1)

            # Get plugin before uninstalling
            plugin = await self.registry.get_plugin(domain, name)
            if not plugin:
                self._logger.warning(f"Plugin {plugin_key} not found for uninstall")
                return False

            # Cleanup active sandbox if exists
            if plugin_key in self._active_sandboxes:
                await self._active_sandboxes[plugin_key].cleanup()
                del self._active_sandboxes[plugin_key]

            # Unregister from tenant registry
            await self.registry.unregister_plugin(domain, name)

            # Remove plugin context
            self._plugin_contexts.pop(plugin_key, None)

            # Record uninstallation
            if self.monitoring:
                self.monitoring.record_metric(
                    name="tenant_plugin_uninstalled",
                    value=1,
                    tags={"tenant_id": str(self.tenant_id), "plugin_key": plugin_key},
                )

            self._logger.info(f"Plugin {plugin_key} uninstalled for tenant {self.tenant_id}")
            return True

        except Exception as e:
            self._logger.error(f"Plugin uninstallation failed for {plugin_key}: {e}")
            raise PluginError(f"Tenant plugin uninstallation failed: {e}") from e

    async def execute_plugin(self, plugin_key: str, method: str, *args, **kwargs) -> Any:
        """
        Execute plugin method in isolated sandbox.
        """
        self._logger.debug(f"Executing {plugin_key}.{method} for tenant {self.tenant_id}")

        try:
            domain, name = plugin_key.split(".", 1)
            plugin = await self.registry.get_plugin(domain, name)

            if not plugin:
                raise PluginNotFoundError(
                    name, domain=domain, available_plugins=await self.list_plugin_keys()
                )

            # Create or reuse sandbox for plugin
            sandbox = await self._get_or_create_sandbox(plugin_key)

            # Execute in sandbox with tenant isolation
            async with sandbox:
                # Inject tenant context into execution
                execution_context = {
                    **kwargs,
                    "_tenant_id": self.tenant_id,
                    "_plugin_context": self._plugin_contexts.get(plugin_key, {}),
                }

                # Execute method with sandbox protection
                result = await sandbox.execute_with_timeout(
                    getattr(plugin, method), *args, **execution_context
                )

                # Record successful execution
                if self.monitoring:
                    self.monitoring.record_metric(
                        name="tenant_plugin_execution_success",
                        value=1,
                        tags={
                            "tenant_id": str(self.tenant_id),
                            "plugin_key": plugin_key,
                            "method": method,
                        },
                    )

                return result

        except Exception as e:
            # Record failed execution
            if self.monitoring:
                self.monitoring.record_metric(
                    name="tenant_plugin_execution_error",
                    value=1,
                    tags={
                        "tenant_id": str(self.tenant_id),
                        "plugin_key": plugin_key,
                        "method": method,
                        "error_type": type(e).__name__,
                    },
                )

            self._logger.error(f"Plugin execution failed for {plugin_key}.{method}: {e}")
            raise PluginError(f"Tenant plugin execution failed: {e}") from e

    # ============================================================================
    # Tenant-Specific Plugin Information
    # ============================================================================

    async def list_plugins(self) -> list[BasePlugin]:
        """List all plugins installed for this tenant."""
        return await self.registry.list_all_plugins()

    async def list_plugin_keys(self) -> list[str]:
        """List all plugin keys for this tenant."""
        plugins = await self.list_plugins()
        return [f"{p.domain}.{p.name}" for p in plugins]

    async def get_plugin_status(self, plugin_key: str) -> Optional[dict[str, Any]]:
        """Get tenant-specific plugin status."""
        try:
            domain, name = plugin_key.split(".", 1)
            plugin = await self.registry.get_plugin(domain, name)

            if not plugin:
                return None

            context = self._plugin_contexts.get(plugin_key, {})
            sandbox_active = plugin_key in self._active_sandboxes

            return {
                "plugin_key": plugin_key,
                "tenant_id": str(self.tenant_id),
                "status": plugin.status.value,
                "is_active": plugin.is_active,
                "is_healthy": plugin.is_healthy,
                "install_time": context.get("install_time"),
                "sandbox_active": sandbox_active,
                "isolation_level": context.get("isolation_level"),
                "execution_count": plugin._execution_stats.get("total_executions", 0),
                "error_count": plugin._execution_stats.get("total_errors", 0),
            }

        except Exception as e:
            self._logger.error(f"Error getting plugin status for {plugin_key}: {e}")
            return None

    async def get_tenant_health(self) -> dict[str, Any]:
        """Get comprehensive tenant plugin system health."""
        plugins = await self.list_plugins()

        health_data = {
            "tenant_id": str(self.tenant_id),
            "total_plugins": len(plugins),
            "active_plugins": len([p for p in plugins if p.is_active]),
            "healthy_plugins": len([p for p in plugins if p.is_healthy]),
            "error_plugins": len([p for p in plugins if p.status == PluginStatus.ERROR]),
            "active_sandboxes": len(self._active_sandboxes),
            "initialized": self._initialized,
        }

        return health_data

    # ============================================================================
    # Private Helper Methods
    # ============================================================================

    async def _get_or_create_sandbox(self, plugin_key: str) -> PluginSandbox:
        """Get existing sandbox or create new one for plugin."""
        if plugin_key not in self._active_sandboxes:
            sandbox = self.security_manager.create_sandbox(
                plugin_id=plugin_key,
                tenant_id=self.tenant_id,
                security_level=self.security_level,
            )
            self._active_sandboxes[plugin_key] = sandbox

        return self._active_sandboxes[plugin_key]

    async def _cleanup_all_sandboxes(self) -> None:
        """Clean up all active sandboxes."""
        cleanup_tasks = []

        for _plugin_key, sandbox in self._active_sandboxes.items():
            cleanup_tasks.append(sandbox.cleanup())

        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)

        self._active_sandboxes.clear()
        self._logger.info(f"Cleaned up all sandboxes for tenant {self.tenant_id}")

    async def _clear_tenant_caches(self) -> None:
        """Clear all tenant-specific caches."""
        cache_manager = get_cache_service()
        if cache_manager:
            await cache_manager.delete_pattern(f"tenant:{self.tenant_id}:*")

    # Context manager support
    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown()

class TenantPluginOrchestrator:
    """
    Orchestrates plugin management across multiple tenants.

    Manages tenant-specific plugin managers and ensures complete isolation.
    """

    def __init__(self):
        self._tenant_managers: dict[UUID, TenantPluginManager] = {}
        self._logger = get_logger("plugins.orchestrator")
        self.monitoring = get_monitoring("plugins.tenant")

    async def get_tenant_manager(
        self,
        tenant_id: UUID,
        config: Optional[dict[str, Any]] = None,
        security_level: str = "default",
    ) -> TenantPluginManager:
        """
        Get or create tenant-specific plugin manager.
        """
        if tenant_id not in self._tenant_managers:
            self._logger.info(f"Creating plugin manager for tenant {tenant_id}")

            manager = TenantPluginManager(
                tenant_id=tenant_id, config=config, security_level=security_level
            )

            await manager.initialize()
            self._tenant_managers[tenant_id] = manager

            if self.monitoring:
                self.monitoring.record_metric(
                    name="tenant_plugin_manager_created",
                    value=1,
                    tags={"tenant_id": str(tenant_id)},
                )

        return self._tenant_managers[tenant_id]

    async def remove_tenant_manager(self, tenant_id: UUID) -> bool:
        """
        Remove and cleanup tenant plugin manager.
        """
        if tenant_id in self._tenant_managers:
            self._logger.info(f"Removing plugin manager for tenant {tenant_id}")

            manager = self._tenant_managers[tenant_id]
            await manager.shutdown()
            del self._tenant_managers[tenant_id]

            if self.monitoring:
                self.monitoring.record_metric(
                    name="tenant_plugin_manager_removed",
                    value=1,
                    tags={"tenant_id": str(tenant_id)},
                )

            return True

        return False

    async def get_system_health(self) -> dict[str, Any]:
        """Get health status across all tenant plugin managers."""
        health_data = {
            "total_tenant_managers": len(self._tenant_managers),
            "tenant_health": {},
        }

        for tenant_id, manager in self._tenant_managers.items():
            health_data["tenant_health"][str(tenant_id)] = await manager.get_tenant_health()

        return health_data

    async def shutdown_all(self) -> None:
        """Shutdown all tenant plugin managers."""
        self._logger.info("Shutting down all tenant plugin managers")

        shutdown_tasks = []
        for manager in self._tenant_managers.values():
            shutdown_tasks.append(manager.shutdown())

        if shutdown_tasks:
            await asyncio.gather(*shutdown_tasks, return_exceptions=True)

        self._tenant_managers.clear()
        self._logger.info("All tenant plugin managers shut down")

# Global orchestrator instance
_tenant_orchestrator = TenantPluginOrchestrator()

def get_tenant_plugin_manager(
    tenant_id: UUID,
    config: Optional[dict[str, Any]] = None,
    security_level: str = "default",
) -> TenantPluginManager:
    """
    Get tenant plugin manager following DRY dependency injection patterns.
    """
    return asyncio.create_task(
        _tenant_orchestrator.get_tenant_manager(tenant_id, config, security_level)
    )

__all__ = [
    "TenantPluginRegistry",
    "TenantPluginManager",
    "TenantPluginOrchestrator",
    "get_tenant_plugin_manager",
]

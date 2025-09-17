"""
Plugin lifecycle management system.

Manages plugin initialization, shutdown, health monitoring, and state transitions.
"""

import asyncio

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from .dependency_resolver import DependencyResolver
from .exceptions import (

    PluginDependencyError,
    PluginError,
    PluginExecutionError,
    PluginTimeoutError,
)
from dotmac.platform.observability.unified_logging import get_logger

from .plugin_base import BasePlugin, PluginStatus
from .registry import PluginRegistry

class LifecycleEvent(Enum):
    """Plugin lifecycle events."""

    BEFORE_INITIALIZE = "before_initialize"
    AFTER_INITIALIZE = "after_initialize"
    BEFORE_SHUTDOWN = "before_shutdown"
    AFTER_SHUTDOWN = "after_shutdown"
    STATUS_CHANGED = "status_changed"
    ERROR_OCCURRED = "error_occurred"
    HEALTH_CHECK_FAILED = "health_check_failed"

@dataclass
class LifecycleMetrics:
    """Metrics for plugin lifecycle operations."""

    # Initialization metrics
    total_initializations: int = 0
    successful_initializations: int = 0
    failed_initializations: int = 0
    avg_initialization_time: float = 0.0

    # Shutdown metrics
    total_shutdowns: int = 0
    successful_shutdowns: int = 0
    failed_shutdowns: int = 0
    avg_shutdown_time: float = 0.0

    # Health check metrics
    total_health_checks: int = 0
    successful_health_checks: int = 0
    failed_health_checks: int = 0
    avg_health_check_time: float = 0.0

    # Error metrics
    total_errors: int = 0
    error_types: dict[str, int] = field(default_factory=dict)

    # Timing tracking
    _initialization_times: list[float] = field(default_factory=list)
    _shutdown_times: list[float] = field(default_factory=list)
    _health_check_times: list[float] = field(default_factory=list)

    def record_initialization(self, success: bool, duration: float) -> None:
        """Record an initialization attempt."""
        self.total_initializations += 1
        if success:
            self.successful_initializations += 1
        else:
            self.failed_initializations += 1

        self._initialization_times.append(duration)
        self.avg_initialization_time = sum(self._initialization_times) / len(
            self._initialization_times
        )

    def record_shutdown(self, success: bool, duration: float) -> None:
        """Record a shutdown attempt."""
        self.total_shutdowns += 1
        if success:
            self.successful_shutdowns += 1
        else:
            self.failed_shutdowns += 1

        self._shutdown_times.append(duration)
        self.avg_shutdown_time = sum(self._shutdown_times) / len(self._shutdown_times)

    def record_health_check(self, success: bool, duration: float) -> None:
        """Record a health check attempt."""
        self.total_health_checks += 1
        if success:
            self.successful_health_checks += 1
        else:
            self.failed_health_checks += 1

        self._health_check_times.append(duration)
        self.avg_health_check_time = sum(self._health_check_times) / len(self._health_check_times)

    def record_error(self, error_type: str) -> None:
        """Record an error occurrence."""
        self.total_errors += 1
        self.error_types[error_type] = self.error_types.get(error_type, 0) + 1

class LifecycleManager:
    """
    Comprehensive plugin lifecycle management.

    Handles initialization, shutdown, health monitoring, and state management
    for all plugins in the system.
    """

    def __init__(
        self,
        registry: PluginRegistry,
        dependency_resolver: DependencyResolver,
        default_timeout: float = 30.0,
        health_check_interval: float = 60.0,
        max_concurrent_operations: int = 10,
    ):
        self.registry = registry
        self.dependency_resolver = dependency_resolver
        self.default_timeout = default_timeout
        self.health_check_interval = health_check_interval
        self.max_concurrent_operations = max_concurrent_operations

        # State tracking
        self._plugin_metrics: dict[str, LifecycleMetrics] = defaultdict(LifecycleMetrics)
        self._initialization_tasks: dict[str, asyncio.Task] = {}
        self._shutdown_tasks: dict[str, asyncio.Task] = {}
        self._health_check_tasks: dict[str, asyncio.Task] = {}

        # Event system
        self._event_handlers: dict[LifecycleEvent, list[Callable]] = defaultdict(list)

        # Lifecycle state
        self._shutdown_requested = False
        self._health_monitoring_active = False
        self._semaphore = asyncio.Semaphore(max_concurrent_operations)

        self._logger = get_logger("plugins.lifecycle_manager")
        self._logger.info("LifecycleManager initialized")

    # Plugin initialization

    async def initialize_plugin(self, plugin_key: str, timeout: Optional[float] = None) -> bool:
        """
        Initialize a single plugin.

        Args:
            plugin_key: Plugin key in format "domain.name"
            timeout: Timeout for initialization (uses default if None)

        Returns:
            True if initialization succeeded

        Raises:
            PluginError: If initialization fails
        """
        if "." not in plugin_key:
            raise PluginError(f"Invalid plugin key format: {plugin_key}")

        domain, name = plugin_key.split(".", 1)
        plugin = await self.registry.get_plugin(domain, name)

        if not plugin:
            raise PluginError(
                f"Plugin '{plugin_key}' not found in registry",
                plugin_name=name,
                plugin_domain=domain,
            )

        return await self._initialize_single_plugin(plugin, timeout or self.default_timeout)

    async def initialize_plugins(
        self,
        plugin_keys: set[str],
        parallel: bool = True,
        timeout: Optional[float] = None,
    ) -> dict[str, bool]:
        """
        Initialize multiple plugins with dependency resolution.

        Args:
            plugin_keys: Set of plugin keys to initialize
            parallel: Whether to initialize plugins in parallel where possible
            timeout: Timeout for each plugin initialization

        Returns:
            Dict mapping plugin keys to initialization success status
        """
        self._logger.info(f"Initializing {len(plugin_keys)} plugins (parallel={parallel})")

        results = {}
        timeout = timeout or self.default_timeout

        try:
            if parallel:
                # Get parallel initialization groups based on dependencies
                groups = self.dependency_resolver.get_parallel_load_groups(plugin_keys)

                for group_index, group in enumerate(groups):
                    self._logger.info(
                        f"Initializing group {group_index + 1}/{len(groups)}: {group}"
                    )

                    # Initialize plugins in this group in parallel
                    group_results = await self._initialize_plugin_group(group, timeout)
                    results.update(group_results)

                    # Check if any initialization failed
                    failed_plugins = [k for k, success in group_results.items() if not success]
                    if failed_plugins:
                        self._logger.warning(
                            f"Failed to initialize plugins in group: {failed_plugins}"
                        )
                        # Continue with next group - dependent plugins will fail gracefully
            else:
                # Sequential initialization in dependency order
                load_order = self.dependency_resolver.resolve_load_order(plugin_keys)

                for plugin_key in load_order:
                    try:
                        success = await self.initialize_plugin(plugin_key, timeout)
                        results[plugin_key] = success

                        if not success:
                            self._logger.warning(f"Failed to initialize plugin: {plugin_key}")

                    except Exception as e:
                        self._logger.error(f"Error initializing plugin {plugin_key}: {e}")
                        results[plugin_key] = False

        except PluginDependencyError as e:
            self._logger.error(f"Dependency resolution failed: {e}")
            # Mark all plugins as failed
            for plugin_key in plugin_keys:
                results[plugin_key] = False

        successful_count = sum(1 for success in results.values() if success)
        self._logger.info(
            f"Plugin initialization complete: {successful_count}/{len(plugin_keys)} successful"
        )

        return results

    async def _initialize_plugin_group(
        self, plugin_keys: list[str], timeout: float
    ) -> dict[str, bool]:
        """Initialize a group of plugins in parallel."""
        tasks = []

        for plugin_key in plugin_keys:
            task = asyncio.create_task(
                self._initialize_plugin_with_semaphore(plugin_key, timeout),
                name=f"init_{plugin_key}",
            )
            tasks.append((plugin_key, task))

        results = {}

        # Wait for all tasks to complete
        for plugin_key, task in tasks:
            try:
                success = await task
                results[plugin_key] = success
            except Exception as e:
                self._logger.error(f"Error in parallel initialization of {plugin_key}: {e}")
                results[plugin_key] = False

        return results

    async def _initialize_plugin_with_semaphore(self, plugin_key: str, timeout: float) -> bool:
        """Initialize a plugin with semaphore-controlled concurrency."""
        async with self._semaphore:
            return await self.initialize_plugin(plugin_key, timeout)

    async def _initialize_single_plugin(self, plugin: BasePlugin, timeout: float) -> bool:
        """Initialize a single plugin with full lifecycle management."""
        plugin_key = f"{plugin.domain}.{plugin.name}"

        # Emit before initialize event
        await self._emit_event(LifecycleEvent.BEFORE_INITIALIZE, plugin)

        start_time = datetime.now(timezone.utc)

        try:
            # Check if already initialized
            if plugin.is_active:
                self._logger.debug(f"Plugin {plugin_key} is already active")
                return True

            # Initialize with timeout
            await asyncio.wait_for(plugin.initialize(), timeout=timeout)

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()

            self._plugin_metrics[plugin_key].record_initialization(True, duration)
            self._logger.info(f"Plugin {plugin_key} initialized successfully in {duration:.2f}s")

            # Emit after initialize event
            await self._emit_event(LifecycleEvent.AFTER_INITIALIZE, plugin)

            return True

        except asyncio.TimeoutError:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            self._plugin_metrics[plugin_key].record_initialization(False, duration)
            self._plugin_metrics[plugin_key].record_error("timeout")

            error = PluginTimeoutError(plugin.name, "initialization", timeout)
            await self._emit_event(LifecycleEvent.ERROR_OCCURRED, plugin, error)

            raise error

        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            self._plugin_metrics[plugin_key].record_initialization(False, duration)
            self._plugin_metrics[plugin_key].record_error(type(e).__name__)

            await self._emit_event(LifecycleEvent.ERROR_OCCURRED, plugin, e)

            raise PluginExecutionError(plugin.name, "initialize", original_error=e) from e

    # Plugin shutdown

    async def shutdown_plugin(
        self, plugin_key: str, timeout: Optional[float] = None, force: bool = False
    ) -> bool:
        """
        Shutdown a single plugin.

        Args:
            plugin_key: Plugin key in format "domain.name"
            timeout: Timeout for shutdown (uses default if None)
            force: Whether to force shutdown even if dependents are active

        Returns:
            True if shutdown succeeded
        """
        if "." not in plugin_key:
            raise PluginError(f"Invalid plugin key format: {plugin_key}")

        domain, name = plugin_key.split(".", 1)
        plugin = await self.registry.get_plugin(domain, name)

        if not plugin:
            self._logger.warning(f"Plugin '{plugin_key}' not found for shutdown")
            return True  # Consider missing plugin as successfully shut down

        # Check if plugin can be safely shut down
        if not force:
            active_plugins = set()
            all_plugins = await self.registry.list_all_plugins()

            for p in all_plugins:
                if p.is_active:
                    active_plugins.add(f"{p.domain}.{p.name}")

            can_shutdown, blocking_dependents = self.dependency_resolver.can_unload_plugin(
                plugin_key, active_plugins
            )

            if not can_shutdown:
                raise PluginDependencyError(plugin.name, [], blocking_dependents)

        return await self._shutdown_single_plugin(plugin, timeout or self.default_timeout)

    async def shutdown_all_plugins(
        self, timeout: Optional[float] = None, force: bool = False
    ) -> dict[str, bool]:
        """
        Shutdown all active plugins in dependency order.

        Args:
            timeout: Timeout for each plugin shutdown
            force: Whether to force shutdown regardless of dependencies

        Returns:
            Dict mapping plugin keys to shutdown success status
        """
        self._shutdown_requested = True
        self._logger.info("Shutting down all plugins")

        # Get all active plugins
        all_plugins = await self.registry.list_all_plugins()
        active_plugin_keys = {f"{p.domain}.{p.name}" for p in all_plugins if p.is_active}

        if not active_plugin_keys:
            self._logger.info("No active plugins to shut down")
            return {}

        # Get shutdown order (reverse of load order)
        shutdown_order = self.dependency_resolver.get_shutdown_order(active_plugin_keys)

        results = {}
        timeout = timeout or self.default_timeout

        # Shutdown plugins in order
        for plugin_key in shutdown_order:
            try:
                success = await self.shutdown_plugin(plugin_key, timeout, force)
                results[plugin_key] = success

                if not success:
                    self._logger.warning(f"Failed to shutdown plugin: {plugin_key}")

            except Exception as e:
                self._logger.error(f"Error shutting down plugin {plugin_key}: {e}")
                results[plugin_key] = False

        successful_count = sum(1 for success in results.values() if success)
        self._logger.info(
            f"Plugin shutdown complete: {successful_count}/{len(active_plugin_keys)} successful"
        )

        return results

    async def _shutdown_single_plugin(self, plugin: BasePlugin, timeout: float) -> bool:
        """Shutdown a single plugin with full lifecycle management."""
        plugin_key = f"{plugin.domain}.{plugin.name}"

        # Emit before shutdown event
        await self._emit_event(LifecycleEvent.BEFORE_SHUTDOWN, plugin)

        start_time = datetime.now(timezone.utc)

        try:
            # Check if already shut down
            if plugin.status in [PluginStatus.UNINITIALIZED, PluginStatus.INACTIVE]:
                self._logger.debug(f"Plugin {plugin_key} is already inactive")
                return True

            # Shutdown with timeout
            await asyncio.wait_for(plugin.shutdown(), timeout=timeout)

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            self._plugin_metrics[plugin_key].record_shutdown(True, duration)
            self._logger.info(f"Plugin {plugin_key} shut down successfully in {duration:.2f}s")

            # Emit after shutdown event
            await self._emit_event(LifecycleEvent.AFTER_SHUTDOWN, plugin)

            return True

        except asyncio.TimeoutError:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            self._plugin_metrics[plugin_key].record_shutdown(False, duration)
            self._plugin_metrics[plugin_key].record_error("shutdown_timeout")

            self._logger.error(f"Plugin {plugin_key} shutdown timed out after {timeout}s")
            return False

        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            self._plugin_metrics[plugin_key].record_shutdown(False, duration)
            self._plugin_metrics[plugin_key].record_error(type(e).__name__)

            self._logger.error(f"Error shutting down plugin {plugin_key}: {e}")
            await self._emit_event(LifecycleEvent.ERROR_OCCURRED, plugin, e)

            return False

    # Health monitoring

    async def start_health_monitoring(self) -> None:
        """Start continuous health monitoring for all plugins."""
        if self._health_monitoring_active:
            self._logger.warning("Health monitoring is already active")
            return

        self._health_monitoring_active = True
        self._logger.info(f"Starting health monitoring (interval: {self.health_check_interval}s)")

        # Start health monitoring task
        asyncio.create_task(self._health_monitoring_loop(), name="health_monitoring")

    async def stop_health_monitoring(self) -> None:
        """Stop continuous health monitoring."""
        self._health_monitoring_active = False
        self._logger.info("Stopped health monitoring")

        # Cancel all active health check tasks
        for task in list(self._health_check_tasks.values()):
            if not task.done():
                task.cancel()

        self._health_check_tasks.clear()

    async def perform_health_check(self, plugin_key: str) -> dict[str, Any]:
        """
        Perform health check on a specific plugin.

        Args:
            plugin_key: Plugin key in format "domain.name"

        Returns:
            Health check results
        """
        if "." not in plugin_key:
            raise PluginError(f"Invalid plugin key format: {plugin_key}")

        domain, name = plugin_key.split(".", 1)
        plugin = await self.registry.get_plugin(domain, name)

        if not plugin:
            return {
                "status": "not_found",
                "plugin_key": plugin_key,
                "healthy": False,
                "error": f"Plugin '{plugin_key}' not found",
            }

        return await self._perform_plugin_health_check(plugin)

    async def _health_monitoring_loop(self) -> None:
        """Continuous health monitoring loop."""
        while self._health_monitoring_active and not self._shutdown_requested:
            try:
                # Get all active plugins
                all_plugins = await self.registry.list_all_plugins()
                active_plugins = [p for p in all_plugins if p.is_active]

                if active_plugins:
                    # Perform health checks in parallel
                    health_check_tasks = []

                    for plugin in active_plugins:
                        task = asyncio.create_task(
                            self._perform_plugin_health_check(plugin),
                            name=f"health_check_{plugin.domain}.{plugin.name}",
                        )
                        health_check_tasks.append(task)

                    # Wait for all health checks to complete
                    await asyncio.gather(*health_check_tasks, return_exceptions=True)

                # Wait before next health check cycle
                await asyncio.sleep(self.health_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(5)  # Short delay before retry

        self._logger.info("Health monitoring loop stopped")

    async def _perform_plugin_health_check(self, plugin: BasePlugin) -> dict[str, Any]:
        """Perform health check on a single plugin."""
        plugin_key = f"{plugin.domain}.{plugin.name}"
        start_time = datetime.now(timezone.utc)

        try:
            health_data = await plugin.health_check()

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            self._plugin_metrics[plugin_key].record_health_check(True, duration)

            return health_data

        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            self._plugin_metrics[plugin_key].record_health_check(False, duration)
            self._plugin_metrics[plugin_key].record_error("health_check_failure")

            self._logger.warning(f"Health check failed for plugin {plugin_key}: {e}")

            await self._emit_event(LifecycleEvent.HEALTH_CHECK_FAILED, plugin, e)

            return {
                "status": "error",
                "plugin_key": plugin_key,
                "healthy": False,
                "error": str(e),
                "check_duration": duration,
            }

    # Event system

    def add_event_handler(self, event: LifecycleEvent, handler: Callable) -> None:
        """Add an event handler for lifecycle events."""
        self._event_handlers[event].append(handler)
        self._logger.debug(f"Added event handler for {event.value}")

    def remove_event_handler(self, event: LifecycleEvent, handler: Callable) -> None:
        """Remove an event handler."""
        if handler in self._event_handlers[event]:
            self._event_handlers[event].remove(handler)
            self._logger.debug(f"Removed event handler for {event.value}")

    async def _emit_event(
        self, event: LifecycleEvent, plugin: BasePlugin, data: Any = None
    ) -> None:
        """Emit a lifecycle event to all registered handlers."""
        handlers = self._event_handlers.get(event, [])

        if not handlers:
            return

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event, plugin, data)
                else:
                    handler(event, plugin, data)
            except Exception as e:
                self._logger.error(f"Error in event handler for {event.value}: {e}")

    # Metrics and statistics

    def get_plugin_metrics(self, plugin_key: str) -> LifecycleMetrics:
        """Get lifecycle metrics for a specific plugin."""
        return self._plugin_metrics.get(plugin_key, LifecycleMetrics())

    def get_all_metrics(self) -> dict[str, LifecycleMetrics]:
        """Get lifecycle metrics for all plugins."""
        return dict(self._plugin_metrics)

    def get_system_metrics(self) -> dict[str, Any]:
        """Get system-wide lifecycle metrics."""
        all_metrics = list(self._plugin_metrics.values())

        if not all_metrics:
            return {
                "total_plugins": 0,
                "total_operations": 0,
                "health_monitoring_active": self._health_monitoring_active,
                "shutdown_requested": self._shutdown_requested,
            }

        return {
            "total_plugins": len(self._plugin_metrics),
            "total_initializations": sum(m.total_initializations for m in all_metrics),
            "total_shutdowns": sum(m.total_shutdowns for m in all_metrics),
            "total_health_checks": sum(m.total_health_checks for m in all_metrics),
            "total_errors": sum(m.total_errors for m in all_metrics),
            "avg_initialization_time": sum(m.avg_initialization_time for m in all_metrics)
            / len(all_metrics),
            "avg_shutdown_time": sum(m.avg_shutdown_time for m in all_metrics) / len(all_metrics),
            "avg_health_check_time": sum(m.avg_health_check_time for m in all_metrics)
            / len(all_metrics),
            "health_monitoring_active": self._health_monitoring_active,
            "shutdown_requested": self._shutdown_requested,
            "active_tasks": {
                "initialization": len(self._initialization_tasks),
                "shutdown": len(self._shutdown_tasks),
                "health_checks": len(self._health_check_tasks),
            },
        }

    # Cleanup

    async def cleanup(self) -> None:
        """Clean up the lifecycle manager."""
        self._logger.info("Cleaning up LifecycleManager")

        # Stop health monitoring
        await self.stop_health_monitoring()

        # Cancel any remaining tasks
        all_tasks = (
            list(self._initialization_tasks.values())
            + list(self._shutdown_tasks.values())
            + list(self._health_check_tasks.values())
        )

        for task in all_tasks:
            if not task.done():
                task.cancel()

        # Clear task tracking
        self._initialization_tasks.clear()
        self._shutdown_tasks.clear()
        self._health_check_tasks.clear()

        self._logger.info("LifecycleManager cleanup complete")

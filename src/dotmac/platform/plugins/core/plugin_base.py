"""
Base plugin classes and interfaces.

Defines the core plugin architecture and contracts that all plugins must implement.
"""

import asyncio

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from .exceptions import PluginError, PluginValidationError

from dotmac.platform.observability.unified_logging import get_logger
class PluginStatus(Enum):
    """Plugin lifecycle states."""

    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DISABLED = "disabled"
    UPDATING = "updating"

@dataclass
class PluginMetadata:
    """Plugin metadata and configuration."""

    # Core identification
    name: str
    version: str
    domain: str

    # Plugin information
    description: Optional[str] = None
    author: Optional[str] = None
    homepage: Optional[str] = None

    # Dependencies and compatibility
    dependencies: list[str] = field(default_factory=list)
    optional_dependencies: list[str] = field(default_factory=list)
    python_requires: Optional[str] = None
    platform_compatibility: list[str] = field(default_factory=lambda: ["any"])

    # Plugin capabilities
    supports_async: bool = True
    supports_streaming: bool = False
    supports_batching: bool = False
    thread_safe: bool = True

    # Configuration
    config_schema: Optional[dict[str, Any]] = None
    default_config: dict[str, Any] = field(default_factory=dict)
    required_permissions: set[str] = field(default_factory=set)

    # Runtime information
    plugin_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

    # Tags for categorization and discovery
    tags: set[str] = field(default_factory=set)
    categories: set[str] = field(default_factory=set)

    def __post_init__(self):
        """Validate metadata after initialization."""
        if not self.name:
            raise PluginValidationError(self.name or "unknown", ["Plugin name cannot be empty"])

        if not self.version:
            raise PluginValidationError(self.name, ["Plugin version cannot be empty"])

        if not self.domain:
            raise PluginValidationError(self.name, ["Plugin domain cannot be empty"])

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary for serialization."""
        return {
            "name": self.name,
            "version": self.version,
            "domain": self.domain,
            "description": self.description,
            "author": self.author,
            "homepage": self.homepage,
            "dependencies": self.dependencies,
            "optional_dependencies": self.optional_dependencies,
            "python_requires": self.python_requires,
            "platform_compatibility": self.platform_compatibility,
            "supports_async": self.supports_async,
            "supports_streaming": self.supports_streaming,
            "supports_batching": self.supports_batching,
            "thread_safe": self.thread_safe,
            "config_schema": self.config_schema,
            "default_config": self.default_config,
            "required_permissions": list(self.required_permissions),
            "plugin_id": str(self.plugin_id),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "tags": list(self.tags),
            "categories": list(self.categories),
        }

class BasePlugin(ABC):
    """
    Base plugin class that all plugins must inherit from.

    Provides lifecycle management, configuration handling, and standardized interfaces.
    """

    def __init__(self, metadata: PluginMetadata, config: Optional[dict[str, Any]] = None):
        self.metadata = metadata
        self.config = config or {}
        self.status = PluginStatus.UNINITIALIZED
        self.logger = get_logger(f"plugins.{metadata.domain}.{metadata.name}")

        # Runtime state
        self._initialization_lock = asyncio.Lock()
        self._shutdown_lock = asyncio.Lock()
        self._initialized_at: Optional[datetime] = None
        self._last_activity: Optional[datetime] = None
        self._error_count = 0
        self._success_count = 0

        # Plugin-specific state storage
        self._state: dict[str, Any] = {}

    @property
    def name(self) -> str:
        """Plugin name."""
        return self.metadata.name

    @property
    def version(self) -> str:
        """Plugin version."""
        return self.metadata.version

    @property
    def domain(self) -> str:
        """Plugin domain."""
        return self.metadata.domain

    @property
    def is_active(self) -> bool:
        """Check if plugin is active and ready for use."""
        return self.status == PluginStatus.ACTIVE

    @property
    def is_healthy(self) -> bool:
        """Check if plugin is in a healthy state."""
        return self.status in [PluginStatus.ACTIVE, PluginStatus.INACTIVE]

    @property
    def uptime(self) -> Optional[float]:
        """Get plugin uptime in seconds."""
        if self._initialized_at:
            return (datetime.now(timezone.utc) - self._initialized_at).total_seconds()
        return None

    # Lifecycle methods

    async def initialize(self) -> None:
        """
        Initialize the plugin.

        Called once during plugin loading. Should prepare plugin for use.
        """
        async with self._initialization_lock:
            if self.status != PluginStatus.UNINITIALIZED:
                return

            try:
                self.status = PluginStatus.INITIALIZING
                self.logger.info(f"Initializing plugin {self.name} v{self.version}")

                # Validate configuration against schema
                await self._validate_config()

                # Perform plugin-specific initialization
                await self._initialize_plugin()

                self.status = PluginStatus.ACTIVE
                self._initialized_at = datetime.now(timezone.utc)
                self.logger.info(f"Plugin {self.name} initialized successfully")

            except Exception as e:
                self.status = PluginStatus.ERROR
                self.logger.error(f"Failed to initialize plugin {self.name}: {e}")
                raise PluginError(
                    f"Plugin initialization failed: {e}",
                    plugin_name=self.name,
                    plugin_domain=self.domain,
                ) from e

    async def shutdown(self) -> None:
        """
        Shutdown the plugin gracefully.

        Called during plugin unloading or system shutdown.
        """
        async with self._shutdown_lock:
            if self.status in [PluginStatus.UNINITIALIZED, PluginStatus.INACTIVE]:
                return

            try:
                self.logger.info(f"Shutting down plugin {self.name}")

                # Perform plugin-specific cleanup
                await self._shutdown_plugin()

                self.status = PluginStatus.INACTIVE
                self.logger.info(f"Plugin {self.name} shut down successfully")

            except Exception as e:
                self.status = PluginStatus.ERROR
                self.logger.error(f"Error during plugin shutdown: {e}")
                # Don't raise exception during shutdown to allow cleanup to continue

    async def health_check(self) -> dict[str, Any]:
        """
        Perform health check on the plugin.

        Returns:
            Dict containing health status and metrics
        """
        try:
            # Basic health information
            health_data = {
                "status": self.status.value,
                "name": self.name,
                "version": self.version,
                "domain": self.domain,
                "healthy": self.is_healthy,
                "uptime_seconds": self.uptime,
                "error_count": self._error_count,
                "success_count": self._success_count,
                "last_activity": (self._last_activity.isoformat() if self._last_activity else None),
            }

            # Add plugin-specific health data
            plugin_health = await self._plugin_health_check()
            if plugin_health:
                health_data["plugin_specific"] = plugin_health

            return health_data

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": PluginStatus.ERROR.value,
                "name": self.name,
                "healthy": False,
                "error": str(e),
            }

    async def reload_config(self, new_config: dict[str, Any]) -> None:
        """
        Reload plugin configuration.

        Args:
            new_config: New configuration dictionary
        """
        try:
            old_config = self.config.copy()
            self.config = new_config

            # Validate new configuration
            await self._validate_config()

            # Apply configuration changes
            await self._apply_config_changes(old_config, new_config)

            self.logger.info(f"Configuration reloaded for plugin {self.name}")

        except Exception as e:
            # Rollback to old configuration on error
            self.config = old_config
            self.logger.error(f"Failed to reload configuration: {e}")
            raise PluginError(
                f"Configuration reload failed: {e}",
                plugin_name=self.name,
                plugin_domain=self.domain,
            ) from e

    # State management

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get plugin state value."""
        return self._state.get(key, default)

    def set_state(self, key: str, value: Any) -> None:
        """Set plugin state value."""
        self._state[key] = value

    def clear_state(self) -> None:
        """Clear all plugin state."""
        self._state.clear()

    # Metrics and monitoring

    def _record_success(self) -> None:
        """Record successful operation."""
        self._success_count += 1
        self._last_activity = datetime.now(timezone.utc)

    def _record_error(self) -> None:
        """Record failed operation."""
        self._error_count += 1
        self._last_activity = datetime.now(timezone.utc)

    # Abstract methods that plugins must implement

    @abstractmethod
    async def _initialize_plugin(self) -> None:
        """
        Plugin-specific initialization logic.

        Override this method to implement custom initialization.
        """
        pass

    @abstractmethod
    async def _shutdown_plugin(self) -> None:
        """
        Plugin-specific shutdown logic.

        Override this method to implement custom cleanup.
        """
        pass

    # Optional methods that plugins can override

    async def _validate_config(self) -> None:
        """
        Validate plugin configuration against schema.

        Override to implement custom validation logic.
        """
        if not self.metadata.config_schema:
            return

        # Basic schema validation would go here
        # In a real implementation, you'd use a validation library like cerberus or pydantic
        pass

    async def _plugin_health_check(self) -> Optional[dict[str, Any]]:
        """
        Plugin-specific health check.

        Override to return plugin-specific health information.

        Returns:
            Dict with plugin-specific health data, or None
        """
        return None

    async def _apply_config_changes(
        self, old_config: dict[str, Any], new_config: dict[str, Any]
    ) -> None:
        """
        Apply configuration changes.

        Override to handle configuration updates.

        Args:
            old_config: Previous configuration
            new_config: New configuration
        """
        pass

    # Utility methods

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', version='{self.version}', status='{self.status.value}')>"

    def __str__(self) -> str:
        return f"{self.name} v{self.version} [{self.status.value}]"

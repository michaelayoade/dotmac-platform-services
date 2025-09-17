"""
YAML-based plugin loader.

Loads plugin configurations from YAML files and instantiates plugins.
"""

import importlib

from pathlib import Path
from typing import Any, Optional, Union

import yaml

from ..core.exceptions import PluginConfigError, PluginLoadError
from ..core.plugin_base import BasePlugin, PluginMetadata

from dotmac.platform.observability.unified_logging import get_logger
class YamlPluginLoader:
    """
    Load plugins from YAML configuration files.

    Supports both single plugin definitions and multi-plugin manifests.
    """

    def __init__(self):
        self._logger = get_logger("plugins.yaml_loader")

    async def load_plugins_from_file(self, config_path: Union[str, Path]) -> list[BasePlugin]:
        """
        Load plugins from a YAML configuration file.

        Args:
            config_path: Path to the YAML configuration file

        Returns:
            List of loaded plugin instances

        Raises:
            PluginConfigError: If configuration is invalid
            PluginLoadError: If plugin loading fails
        """
        config_path = Path(config_path)
        self._logger.info(f"Loading plugins from YAML file: {config_path}")

        if not config_path.exists():
            raise PluginConfigError(
                "yaml_loader",
                config_path=str(config_path),
                config_errors=[f"Configuration file not found: {config_path}"],
            )

        try:
            # Load YAML content
            with open(config_path, encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            if not config_data:
                raise PluginConfigError(
                    "yaml_loader",
                    config_path=str(config_path),
                    config_errors=["Empty configuration file"],
                )

            # Parse configuration and load plugins
            plugins = await self._parse_and_load_plugins(config_data, config_path)

            self._logger.info(f"Successfully loaded {len(plugins)} plugins from {config_path}")
            return plugins

        except yaml.YAMLError as e:
            raise PluginConfigError(
                "yaml_loader",
                config_path=str(config_path),
                config_errors=[f"YAML parsing error: {e}"],
                original_error=e,
            ) from e

        except Exception as e:
            raise PluginLoadError(
                "yaml_loader",
                plugin_path=str(config_path),
                loader_type="yaml",
                original_error=e,
            ) from e

    async def load_plugins_from_string(self, yaml_content: str) -> list[BasePlugin]:
        """
        Load plugins from a YAML string.

        Args:
            yaml_content: YAML content as string

        Returns:
            List of loaded plugin instances
        """
        self._logger.info("Loading plugins from YAML string")

        try:
            config_data = yaml.safe_load(yaml_content)

            if not config_data:
                raise PluginConfigError("yaml_loader", config_errors=["Empty YAML content"])

            plugins = await self._parse_and_load_plugins(config_data)

            self._logger.info(f"Successfully loaded {len(plugins)} plugins from YAML string")
            return plugins

        except yaml.YAMLError as e:
            raise PluginConfigError(
                "yaml_loader",
                config_errors=[f"YAML parsing error: {e}"],
                original_error=e,
            ) from e

    async def _parse_and_load_plugins(
        self, config_data: dict[str, Any], config_path: Optional[Path] = None
    ) -> list[BasePlugin]:
        """Parse YAML configuration and load plugins."""
        plugins = []

        # Handle different configuration formats
        if "plugins" in config_data:
            # Multi-plugin manifest format
            plugin_configs = config_data["plugins"]
        elif "plugin" in config_data:
            # Single plugin format
            plugin_configs = [config_data["plugin"]]
        elif self._is_plugin_config(config_data):
            # Direct plugin configuration
            plugin_configs = [config_data]
        else:
            raise PluginConfigError(
                "yaml_loader",
                config_path=str(config_path) if config_path else None,
                config_errors=[
                    "Invalid configuration format. Expected 'plugins', 'plugin', or direct plugin config"
                ],
            )

        # Load each plugin
        for i, plugin_config in enumerate(plugin_configs):
            try:
                plugin = await self._load_single_plugin(plugin_config)
                plugins.append(plugin)

            except Exception as e:
                error_context = f"plugin index {i}"
                if "name" in plugin_config:
                    error_context = f"plugin '{plugin_config['name']}'"

                self._logger.error(f"Failed to load {error_context}: {e}")

                # Re-raise with additional context
                if isinstance(e, (PluginLoadError, PluginConfigError)):
                    raise
                else:
                    raise PluginLoadError(
                        plugin_config.get("name", f"plugin_{i}"),
                        plugin_path=str(config_path) if config_path else None,
                        loader_type="yaml",
                        original_error=e,
                    ) from e

        return plugins

    async def _load_single_plugin(self, plugin_config: dict[str, Any]) -> BasePlugin:
        """Load a single plugin from its configuration."""
        # Validate required fields
        required_fields = ["name", "module", "class"]
        missing_fields = [field for field in required_fields if field not in plugin_config]

        if missing_fields:
            raise PluginConfigError(
                plugin_config.get("name", "unknown"),
                config_errors=[f"Missing required fields: {missing_fields}"],
            )

        plugin_name = plugin_config["name"]
        module_path = plugin_config["module"]
        class_name = plugin_config["class"]

        try:
            # Import the plugin module
            module = importlib.import_module(module_path)

            # Get the plugin class
            if not hasattr(module, class_name):
                raise PluginLoadError(
                    plugin_name,
                    plugin_path=module_path,
                    loader_type="yaml",
                    original_error=AttributeError(
                        f"Class '{class_name}' not found in module '{module_path}'"
                    ),
                )

            plugin_class = getattr(module, class_name)

            # Validate that it's a BasePlugin subclass
            if not issubclass(plugin_class, BasePlugin):
                raise PluginLoadError(
                    plugin_name,
                    plugin_path=module_path,
                    loader_type="yaml",
                    original_error=TypeError(f"Class '{class_name}' is not a BasePlugin subclass"),
                )

            # Create plugin metadata
            metadata = self._create_plugin_metadata(plugin_config)

            # Get plugin configuration
            plugin_config_data = plugin_config.get("config", {})

            # Instantiate the plugin
            plugin = plugin_class(metadata, plugin_config_data)

            self._logger.debug(f"Successfully loaded plugin: {plugin_name}")
            return plugin

        except ImportError as e:
            raise PluginLoadError(
                plugin_name,
                plugin_path=module_path,
                loader_type="yaml",
                original_error=e,
            ) from e

        except Exception as e:
            raise PluginLoadError(
                plugin_name,
                plugin_path=module_path,
                loader_type="yaml",
                original_error=e,
            ) from e

    def _create_plugin_metadata(self, plugin_config: dict[str, Any]) -> PluginMetadata:
        """Create plugin metadata from configuration."""

        # Required fields
        name = plugin_config["name"]
        version = plugin_config.get("version", "1.0.0")
        domain = plugin_config.get("domain", "default")

        # Optional fields
        description = plugin_config.get("description")
        author = plugin_config.get("author")
        homepage = plugin_config.get("homepage")

        # Dependencies
        dependencies = plugin_config.get("dependencies", [])
        optional_dependencies = plugin_config.get("optional_dependencies", [])
        python_requires = plugin_config.get("python_requires")
        platform_compatibility = plugin_config.get("platform_compatibility", ["any"])

        # Capabilities
        supports_async = plugin_config.get("supports_async", True)
        supports_streaming = plugin_config.get("supports_streaming", False)
        supports_batching = plugin_config.get("supports_batching", False)
        thread_safe = plugin_config.get("thread_safe", True)

        # Configuration schema
        config_schema = plugin_config.get("config_schema")
        default_config = plugin_config.get("default_config", {})
        required_permissions = set(plugin_config.get("required_permissions", []))

        # Tags and categories
        tags = set(plugin_config.get("tags", []))
        categories = set(plugin_config.get("categories", []))

        return PluginMetadata(
            name=name,
            version=version,
            domain=domain,
            description=description,
            author=author,
            homepage=homepage,
            dependencies=dependencies,
            optional_dependencies=optional_dependencies,
            python_requires=python_requires,
            platform_compatibility=platform_compatibility,
            supports_async=supports_async,
            supports_streaming=supports_streaming,
            supports_batching=supports_batching,
            thread_safe=thread_safe,
            config_schema=config_schema,
            default_config=default_config,
            required_permissions=required_permissions,
            tags=tags,
            categories=categories,
        )

    def _is_plugin_config(self, config: dict[str, Any]) -> bool:
        """Check if a configuration dict is a plugin configuration."""
        required_plugin_fields = ["name", "module", "class"]
        return all(field in config for field in required_plugin_fields)

    @staticmethod
    def create_sample_config() -> str:
        """
        Create a sample YAML configuration for reference.

        Returns:
            Sample YAML configuration as string
        """
        return """
# DotMac Plugin System Configuration
# Multi-plugin manifest format
plugins:
  # Communication plugin example
  - name: email_sender
    version: "1.0.0"
    domain: communication
    description: "Email sending plugin using SMTP"
    author: "DotMac Team"
    module: "mypackage.plugins.email_plugin"
    class: "EmailSenderPlugin"

    # Dependencies
    dependencies: []
    optional_dependencies:
      - "communication.template_engine"

    # Plugin capabilities
    supports_async: true
    supports_streaming: false
    supports_batching: true
    thread_safe: true

    # Configuration schema (optional)
    config_schema:
      type: object
      properties:
        smtp_host:
          type: string
          required: true
        smtp_port:
          type: integer
          default: 587
        use_tls:
          type: boolean
          default: true

    # Default configuration
    default_config:
      smtp_port: 587
      use_tls: true
      timeout: 30

    # Plugin-specific configuration
    config:
      smtp_host: "localhost"
      smtp_port: 587
      use_tls: true
      username: "${SMTP_USERNAME}"
      password: "${SMTP_PASSWORD}"

    # Metadata
    tags:
      - email
      - communication
      - smtp
    categories:
      - messaging
    required_permissions:
      - network_access

  # Storage plugin example
  - name: file_storage
    version: "2.1.0"
    domain: storage
    description: "Local file storage plugin"
    module: "mypackage.plugins.storage_plugin"
    class: "FileStoragePlugin"

    config:
      base_path: "/var/lib/myapp/storage"
      max_file_size: 104857600  # 100MB
      allowed_extensions:
        - .txt
        - .json
        - .csv

    tags:
      - storage
      - files
    categories:
      - persistence

# Global plugin system settings (optional)
settings:
  default_timeout: 30.0
  health_check_interval: 60.0
  max_concurrent_operations: 10
  enable_health_monitoring: true
"""

    @staticmethod
    def create_single_plugin_config() -> str:
        """
        Create a sample single plugin YAML configuration.

        Returns:
            Sample single plugin YAML configuration as string
        """
        return """
# Single plugin configuration format
plugin:
  name: my_awesome_plugin
  version: "1.0.0"
  domain: utilities
  description: "An awesome utility plugin"
  author: "My Name"
  homepage: "https://github.com/myuser/my-awesome-plugin"

  module: "my_package.my_plugin"
  class: "MyAwesomePlugin"

  dependencies: []
  optional_dependencies:
    - "utilities.helper_plugin"

  supports_async: true
  thread_safe: true

  config:
    setting1: "value1"
    setting2: 42
    setting3: true

  tags:
    - utility
    - helper
  categories:
    - tools
"""

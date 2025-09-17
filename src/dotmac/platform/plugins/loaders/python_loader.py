"""
Python module-based plugin loader.

Loads plugins directly from Python modules and classes.
"""

import importlib
import importlib.util
import inspect

from pathlib import Path
from typing import Any, Optional, Union

from ..core.exceptions import PluginLoadError
from ..core.plugin_base import BasePlugin, PluginMetadata

from dotmac.platform.observability.unified_logging import get_logger
class PythonPluginLoader:
    """
    Load plugins from Python modules.

    Supports loading from installed packages, file paths, and dynamic plugin discovery.
    """

    def __init__(self):
        self._logger = get_logger("plugins.python_loader")

    async def load_plugin_from_module(
        self,
        module_path: str,
        plugin_class_name: str,
        plugin_config: Optional[dict[str, Any]] = None,
    ) -> BasePlugin:
        """
        Load a single plugin from a Python module.

        Args:
            module_path: Python module path (e.g., 'mypackage.myplugin')
            plugin_class_name: Name of the plugin class
            plugin_config: Configuration dictionary for the plugin

        Returns:
            Loaded plugin instance

        Raises:
            PluginLoadError: If plugin loading fails
        """
        self._logger.info(f"Loading plugin {plugin_class_name} from module {module_path}")

        try:
            # Import the module
            module = importlib.import_module(module_path)

            # Get the plugin class
            if not hasattr(module, plugin_class_name):
                raise PluginLoadError(
                    plugin_class_name,
                    plugin_path=module_path,
                    loader_type="python",
                    original_error=AttributeError(
                        f"Class '{plugin_class_name}' not found in module '{module_path}'"
                    ),
                )

            plugin_class = getattr(module, plugin_class_name)

            # Validate that it's a BasePlugin subclass
            if not issubclass(plugin_class, BasePlugin):
                raise PluginLoadError(
                    plugin_class_name,
                    plugin_path=module_path,
                    loader_type="python",
                    original_error=TypeError(
                        f"Class '{plugin_class_name}' is not a BasePlugin subclass"
                    ),
                )

            # Create plugin metadata from class attributes or defaults
            metadata = await self._create_metadata_from_class(plugin_class, module_path)

            # Instantiate the plugin
            plugin = plugin_class(metadata, plugin_config or {})

            self._logger.info(f"Successfully loaded plugin: {metadata.name}")
            return plugin

        except ImportError as e:
            raise PluginLoadError(
                plugin_class_name,
                plugin_path=module_path,
                loader_type="python",
                original_error=e,
            ) from e

        except Exception as e:
            raise PluginLoadError(
                plugin_class_name,
                plugin_path=module_path,
                loader_type="python",
                original_error=e,
            ) from e

    async def load_plugin_from_file(
        self,
        file_path: Union[str, Path],
        plugin_class_name: str,
        plugin_config: Optional[dict[str, Any]] = None,
    ) -> BasePlugin:
        """
        Load a plugin from a Python file.

        Args:
            file_path: Path to the Python file
            plugin_class_name: Name of the plugin class
            plugin_config: Configuration dictionary for the plugin

        Returns:
            Loaded plugin instance

        Raises:
            PluginLoadError: If plugin loading fails
        """
        file_path = Path(file_path)
        self._logger.info(f"Loading plugin {plugin_class_name} from file {file_path}")

        if not file_path.exists():
            raise PluginLoadError(
                plugin_class_name,
                plugin_path=str(file_path),
                loader_type="python",
                original_error=FileNotFoundError(f"Plugin file not found: {file_path}"),
            )

        try:
            # Load module from file
            module_name = file_path.stem
            spec = importlib.util.spec_from_file_location(module_name, file_path)

            if spec is None or spec.loader is None:
                raise PluginLoadError(
                    plugin_class_name,
                    plugin_path=str(file_path),
                    loader_type="python",
                    original_error=ImportError(f"Could not create module spec for {file_path}"),
                )

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Get the plugin class
            if not hasattr(module, plugin_class_name):
                raise PluginLoadError(
                    plugin_class_name,
                    plugin_path=str(file_path),
                    loader_type="python",
                    original_error=AttributeError(
                        f"Class '{plugin_class_name}' not found in file {file_path}"
                    ),
                )

            plugin_class = getattr(module, plugin_class_name)

            # Validate that it's a BasePlugin subclass
            if not issubclass(plugin_class, BasePlugin):
                raise PluginLoadError(
                    plugin_class_name,
                    plugin_path=str(file_path),
                    loader_type="python",
                    original_error=TypeError(
                        f"Class '{plugin_class_name}' is not a BasePlugin subclass"
                    ),
                )

            # Create plugin metadata
            metadata = await self._create_metadata_from_class(plugin_class, str(file_path))

            # Instantiate the plugin
            plugin = plugin_class(metadata, plugin_config or {})

            self._logger.info(f"Successfully loaded plugin: {metadata.name}")
            return plugin

        except Exception as e:
            if isinstance(e, PluginLoadError):
                raise

            raise PluginLoadError(
                plugin_class_name,
                plugin_path=str(file_path),
                loader_type="python",
                original_error=e,
            ) from e

    async def discover_plugins_in_module(
        self,
        module_path: str,
        plugin_config: Optional[dict[str, dict[str, Any]]] = None,
    ) -> list[BasePlugin]:
        """
        Discover and load all plugins in a module.

        Args:
            module_path: Python module path to search
            plugin_config: Dict mapping plugin class names to their configs

        Returns:
            List of discovered plugin instances
        """
        self._logger.info(f"Discovering plugins in module: {module_path}")

        try:
            module = importlib.import_module(module_path)
            plugins = []
            plugin_config = plugin_config or {}

            # Find all BasePlugin subclasses in the module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(obj, BasePlugin)
                    and obj != BasePlugin
                    and obj.__module__ == module.__name__
                ):
                    try:
                        config = plugin_config.get(name, {})
                        plugin = await self.load_plugin_from_module(module_path, name, config)
                        plugins.append(plugin)

                    except Exception as e:
                        self._logger.error(f"Failed to load discovered plugin {name}: {e}")
                        # Continue with other plugins

            self._logger.info(f"Discovered {len(plugins)} plugins in module {module_path}")
            return plugins

        except ImportError as e:
            self._logger.error(f"Failed to import module {module_path}: {e}")
            return []

        except Exception as e:
            self._logger.error(f"Error discovering plugins in module {module_path}: {e}")
            return []

    async def discover_plugins_in_directory(
        self,
        directory_path: Union[str, Path],
        plugin_config: Optional[dict[str, dict[str, Any]]] = None,
        recursive: bool = True,
    ) -> list[BasePlugin]:
        """
        Discover and load all plugins in a directory.

        Args:
            directory_path: Directory path to search
            plugin_config: Dict mapping plugin class names to their configs
            recursive: Whether to search subdirectories

        Returns:
            List of discovered plugin instances
        """
        directory_path = Path(directory_path)
        self._logger.info(f"Discovering plugins in directory: {directory_path}")

        if not directory_path.exists() or not directory_path.is_dir():
            self._logger.warning(f"Directory not found: {directory_path}")
            return []

        plugins = []
        plugin_config = plugin_config or {}

        # Find Python files
        pattern = "**/*.py" if recursive else "*.py"

        for python_file in directory_path.glob(pattern):
            if python_file.name.startswith("__"):
                continue  # Skip __init__.py, __pycache__, etc.

            try:
                # Load the module and find plugin classes
                discovered_plugins = await self._discover_plugins_in_file(
                    python_file, plugin_config
                )
                plugins.extend(discovered_plugins)

            except Exception as e:
                self._logger.error(f"Error processing file {python_file}: {e}")
                # Continue with other files

        self._logger.info(f"Discovered {len(plugins)} plugins in directory {directory_path}")
        return plugins

    async def _discover_plugins_in_file(
        self, file_path: Path, plugin_config: dict[str, dict[str, Any]]
    ) -> list[BasePlugin]:
        """Discover plugins in a single Python file."""
        try:
            # Load module from file
            module_name = file_path.stem
            spec = importlib.util.spec_from_file_location(module_name, file_path)

            if spec is None or spec.loader is None:
                return []

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            plugins = []

            # Find all BasePlugin subclasses
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(obj, BasePlugin)
                    and obj != BasePlugin
                    and obj.__module__ == module.__name__
                ):
                    try:
                        config = plugin_config.get(name, {})
                        plugin = await self.load_plugin_from_file(file_path, name, config)
                        plugins.append(plugin)

                    except Exception as e:
                        self._logger.error(f"Failed to load plugin {name} from {file_path}: {e}")

            return plugins

        except Exception as e:
            self._logger.error(f"Error processing file {file_path}: {e}")
            return []

    async def _create_metadata_from_class(
        self, plugin_class: type[BasePlugin], module_path: str
    ) -> PluginMetadata:
        """Create plugin metadata from class attributes and inspection."""

        # Get basic info from class attributes or defaults
        name = getattr(plugin_class, "__plugin_name__", plugin_class.__name__)
        version = getattr(plugin_class, "__plugin_version__", "1.0.0")
        domain = getattr(plugin_class, "__plugin_domain__", "default")
        description = getattr(plugin_class, "__plugin_description__", plugin_class.__doc__)
        author = getattr(plugin_class, "__plugin_author__", None)
        homepage = getattr(plugin_class, "__plugin_homepage__", None)

        # Dependencies
        dependencies = getattr(plugin_class, "__plugin_dependencies__", [])
        optional_dependencies = getattr(plugin_class, "__plugin_optional_dependencies__", [])
        python_requires = getattr(plugin_class, "__plugin_python_requires__", None)
        platform_compatibility = getattr(plugin_class, "__plugin_platform_compatibility__", ["any"])

        # Capabilities - inspect the class to determine capabilities
        supports_async = self._class_has_async_methods(plugin_class)
        supports_streaming = getattr(plugin_class, "__plugin_supports_streaming__", False)
        supports_batching = getattr(plugin_class, "__plugin_supports_batching__", False)
        thread_safe = getattr(plugin_class, "__plugin_thread_safe__", True)

        # Configuration
        config_schema = getattr(plugin_class, "__plugin_config_schema__", None)
        default_config = getattr(plugin_class, "__plugin_default_config__", {})
        required_permissions = set(getattr(plugin_class, "__plugin_required_permissions__", []))

        # Tags and categories
        tags = set(getattr(plugin_class, "__plugin_tags__", []))
        categories = set(getattr(plugin_class, "__plugin_categories__", []))

        # Clean up description
        if description:
            description = inspect.cleandoc(description).split("\n")[0]  # First line only

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

    def _class_has_async_methods(self, plugin_class: type[BasePlugin]) -> bool:
        """Check if the plugin class has async methods."""
        for _name, method in inspect.getmembers(plugin_class, inspect.isfunction):
            if inspect.iscoroutinefunction(method):
                return True
        return False

    @staticmethod
    def create_sample_plugin() -> str:
        """
        Create a sample plugin class for reference.

        Returns:
            Sample plugin code as string
        """
        return '''
"""
Sample plugin implementation for the DotMac Plugin System.

This example shows how to create a plugin using class attributes for metadata.
"""

import asyncio
from typing import Any, Optional
from dotmac_plugins.core.plugin_base import BasePlugin, PluginMetadata

class SampleEmailPlugin(BasePlugin):
    """
    Sample email sending plugin.

    Demonstrates plugin implementation with metadata attributes.
    """

    # Plugin metadata attributes
    __plugin_name__ = "email_sender"
    __plugin_version__ = "1.2.0"
    __plugin_domain__ = "communication"
    __plugin_description__ = "Send emails via SMTP with template support"
    __plugin_author__ = "DotMac Team"
    __plugin_homepage__ = "https://github.com/dotmac/plugins/email"

    # Dependencies
    __plugin_dependencies__ = []
    __plugin_optional_dependencies__ = ["communication.template_engine"]
    __plugin_python_requires__ = ">=3.8"
    __plugin_platform_compatibility__ = ["linux", "darwin", "win32"]

    # Capabilities
    __plugin_supports_streaming__ = False
    __plugin_supports_batching__ = True
    __plugin_thread_safe__ = True

    # Configuration schema
    __plugin_config_schema__ = {
        "type": "object",
        "properties": {
            "smtp_host": {"type": "string", "required": True},
            "smtp_port": {"type": "integer", "default": 587},
            "use_tls": {"type": "boolean", "default": True},
            "username": {"type": "string"},
            "password": {"type": "string"}
        }
    }

    __plugin_default_config__ = {
        "smtp_port": 587,
        "use_tls": True,
        "timeout": 30,
        "retry_attempts": 3
    }

    # Permissions and metadata
    __plugin_required_permissions__ = ["network_access"]
    __plugin_tags__ = ["email", "smtp", "communication"]
    __plugin_categories__ = ["messaging", "notifications"]

    def __init__(self, metadata: PluginMetadata, config: dict[str, Any]):
        super().__init__(metadata, config)

        # Plugin-specific state
        self._smtp_client = None
        self._connected = False
        self._sent_count = 0

    async def _initialize_plugin(self) -> None:
        """Initialize the email plugin."""
        self.logger.info("Initializing email plugin")

        # Validate configuration
        required_config = ["smtp_host"]
        for key in required_config:
            if key not in self.config:
                raise ValueError(f"Missing required configuration: {key}")

        # Initialize SMTP connection (placeholder)
        await self._connect_smtp()

        self.logger.info("Email plugin initialized successfully")

    async def _shutdown_plugin(self) -> None:
        """Shutdown the email plugin."""
        self.logger.info("Shutting down email plugin")

        if self._connected:
            await self._disconnect_smtp()

        self.logger.info("Email plugin shut down successfully")

    async def _plugin_health_check(self) -> Optional[dict[str, Any]]:
        """Perform plugin-specific health check."""
        return {
            "smtp_connected": self._connected,
            "emails_sent": self._sent_count,
            "smtp_host": self.config.get("smtp_host"),
            "smtp_port": self.config.get("smtp_port")
        }

    async def send_email(
        self,
        to_address: str,
        subject: str,
        body: str,
        from_address: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Send an email.

        Args:
            to_address: Recipient email address
            subject: Email subject
            body: Email body content
            from_address: Sender email address (optional)

        Returns:
            Dict with send results
        """
        if not self._connected:
            raise RuntimeError("SMTP not connected")

        self.logger.info(f"Sending email to {to_address}")

        try:
            # Simulate email sending
            await asyncio.sleep(0.1)  # Simulate network delay

            self._sent_count += 1

            return {
                "success": True,
                "message_id": f"msg_{self._sent_count}",
                "to_address": to_address,
                "subject": subject,
                "sent_at": "2024-01-01T12:00:00Z"  # Would be actual timestamp
            }

        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            raise

    async def send_bulk_emails(self, emails: list) -> dict[str, Any]:
        """
        Send multiple emails in batch.

        Args:
            emails: List of email dicts with 'to', 'subject', 'body'

        Returns:
            Batch send results
        """
        self.logger.info(f"Sending {len(emails)} emails in batch")

        results = []
        for email in emails:
            try:
                result = await self.send_email(
                    email["to"],
                    email["subject"],
                    email["body"],
                    email.get("from")
                )
                results.append(result)

            except Exception as e:
                results.append({
                    "success": False,
                    "to_address": email["to"],
                    "error": str(e)
                })

        successful = sum(1 for r in results if r.get("success"))

        return {
            "total_emails": len(emails),
            "successful": successful,
            "failed": len(emails) - successful,
            "results": results
        }

    async def _connect_smtp(self) -> None:
        """Connect to SMTP server."""
        # Placeholder - would implement actual SMTP connection
        self.logger.debug("Connecting to SMTP server")
        await asyncio.sleep(0.1)  # Simulate connection time
        self._connected = True
        self.logger.debug("Connected to SMTP server")

    async def _disconnect_smtp(self) -> None:
        """Disconnect from SMTP server."""
        # Placeholder - would implement actual SMTP disconnection
        self.logger.debug("Disconnecting from SMTP server")
        await asyncio.sleep(0.05)  # Simulate disconnection time
        self._connected = False
        self.logger.debug("Disconnected from SMTP server")

# You can also define multiple plugins in the same file
class SampleSMSPlugin(BasePlugin):
    """Sample SMS plugin for demonstration."""

    __plugin_name__ = "sms_sender"
    __plugin_version__ = "1.0.0"
    __plugin_domain__ = "communication"
    __plugin_description__ = "Send SMS messages via Twilio"

    async def _initialize_plugin(self) -> None:
        """Initialize SMS plugin."""
        self.logger.info("SMS plugin initialized")

    async def _shutdown_plugin(self) -> None:
        """Shutdown SMS plugin."""
        self.logger.info("SMS plugin shut down")

    async def send_sms(self, to_number: str, message: str) -> dict[str, Any]:
        """Send an SMS message."""
        # Placeholder implementation
        return {
            "success": True,
            "message_id": "sms_123",
            "to_number": to_number
        }
'''

"""
Remote plugin loader.

Loads plugins from remote sources like Git repositories, HTTP URLs, and plugin registries.
"""

import asyncio

import os
import tarfile
import zipfile
from pathlib import Path
from typing import Any, Optional, Union
from urllib.parse import urlparse

import aiohttp

from ..core.exceptions import PluginConfigError, PluginLoadError
from ..core.plugin_base import BasePlugin
from .python_loader import PythonPluginLoader
from .yaml_loader import YamlPluginLoader

from dotmac.platform.observability.unified_logging import get_logger
def _is_safe_path(path: str, base_path: Path) -> bool:
    """Check if extracted path is safe (no path traversal)."""
    try:
        extracted_path = base_path / path
        return str(extracted_path.resolve()).startswith(str(base_path.resolve()))
    except (OSError, ValueError):
        return False

def _safe_extract_zip(zip_ref: zipfile.ZipFile, extract_path: Path) -> None:
    """Safely extract ZIP file preventing path traversal attacks."""
    for member in zip_ref.namelist():
        if not _is_safe_path(member, extract_path):
            raise ValueError(f"Unsafe path in ZIP archive: {member}")
        # Additional check for absolute paths
        if os.path.isabs(member) or ".." in member:
            raise ValueError(f"Unsafe path in ZIP archive: {member}")

    zip_ref.extractall(extract_path)

def _safe_extract_tar(tar_ref: tarfile.TarFile, extract_path: Path) -> None:
    """Safely extract TAR file preventing path traversal attacks."""
    for member in tar_ref.getmembers():
        if not _is_safe_path(member.name, extract_path):
            raise ValueError(f"Unsafe path in TAR archive: {member.name}")
        # Additional checks
        if os.path.isabs(member.name) or ".." in member.name:
            raise ValueError(f"Unsafe path in TAR archive: {member.name}")
        if member.isdev():
            raise ValueError(f"Device file not allowed: {member.name}")
        if member.issym() or member.islnk():
            # Check symlink/hardlink targets
            if not _is_safe_path(member.linkname, extract_path):
                raise ValueError(f"Unsafe link target: {member.linkname}")

    tar_ref.extractall(extract_path)

class RemotePluginLoader:
    """
    Load plugins from remote sources.

    Supports Git repositories, HTTP downloads, and plugin registries.
    """

    def __init__(self, cache_dir: Optional[Union[str, Path]] = None):
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".dotmac_plugins"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._python_loader = PythonPluginLoader()
        self._yaml_loader = YamlPluginLoader()
        self._logger = get_logger("plugins.remote_loader")

        # HTTP session for downloads
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    async def load_plugin_from_url(
        self,
        url: str,
        plugin_class_name: str,
        plugin_config: Optional[dict[str, Any]] = None,
        force_refresh: bool = False,
    ) -> BasePlugin:
        """
        Load a plugin from a remote URL.

        Args:
            url: URL to the plugin file or archive
            plugin_class_name: Name of the plugin class
            plugin_config: Configuration for the plugin
            force_refresh: Whether to force re-download

        Returns:
            Loaded plugin instance

        Raises:
            PluginLoadError: If plugin loading fails
        """
        self._logger.info(f"Loading plugin {plugin_class_name} from URL: {url}")

        try:
            # Download and extract plugin
            local_path = await self._download_and_extract(url, force_refresh)

            # Find and load the plugin
            plugin = await self._load_plugin_from_path(local_path, plugin_class_name, plugin_config)

            self._logger.info(f"Successfully loaded plugin {plugin_class_name} from URL")
            return plugin

        except Exception as e:
            raise PluginLoadError(
                plugin_class_name,
                plugin_path=url,
                loader_type="remote_url",
                original_error=e,
            ) from e

    async def load_plugins_from_repository(
        self,
        repo_url: str,
        branch: str = "main",
        plugin_config_path: Optional[str] = None,
        force_refresh: bool = False,
    ) -> list[BasePlugin]:
        """
        Load plugins from a Git repository.

        Args:
            repo_url: Git repository URL
            branch: Branch to checkout
            plugin_config_path: Path to plugin config file in repo
            force_refresh: Whether to force repository re-clone

        Returns:
            List of loaded plugins

        Raises:
            PluginLoadError: If repository loading fails
        """
        self._logger.info(f"Loading plugins from repository: {repo_url}")

        try:
            # Clone or pull repository
            repo_path = await self._clone_repository(repo_url, branch, force_refresh)

            # Load plugins from repository
            if plugin_config_path:
                # Load from specific config file
                config_file = repo_path / plugin_config_path
                if config_file.exists():
                    plugins = await self._yaml_loader.load_plugins_from_file(config_file)
                else:
                    raise PluginConfigError(
                        "repository_loader",
                        config_path=str(config_file),
                        config_errors=[f"Plugin config file not found: {config_file}"],
                    )
            else:
                # Discover plugins in repository
                plugins = await self._python_loader.discover_plugins_in_directory(
                    repo_path, recursive=True
                )

            self._logger.info(f"Loaded {len(plugins)} plugins from repository {repo_url}")
            return plugins

        except Exception as e:
            raise PluginLoadError(
                "repository_plugins",
                plugin_path=repo_url,
                loader_type="remote_git",
                original_error=e,
            ) from e

    async def load_plugin_from_registry(
        self,
        registry_url: str,
        plugin_name: str,
        version: Optional[str] = None,
        plugin_config: Optional[dict[str, Any]] = None,
    ) -> BasePlugin:
        """
        Load a plugin from a plugin registry.

        Args:
            registry_url: Base URL of the plugin registry
            plugin_name: Name of the plugin to load
            version: Specific version to load (latest if None)
            plugin_config: Configuration for the plugin

        Returns:
            Loaded plugin instance

        Raises:
            PluginLoadError: If registry loading fails
        """
        self._logger.info(f"Loading plugin {plugin_name} from registry: {registry_url}")

        try:
            # Query registry for plugin information
            plugin_info = await self._query_registry(registry_url, plugin_name, version)

            # Download plugin from registry
            download_url = plugin_info["download_url"]
            plugin_class_name = plugin_info.get("class_name", plugin_name)

            plugin = await self.load_plugin_from_url(download_url, plugin_class_name, plugin_config)

            self._logger.info(f"Successfully loaded plugin {plugin_name} from registry")
            return plugin

        except Exception as e:
            raise PluginLoadError(
                plugin_name,
                plugin_path=registry_url,
                loader_type="remote_registry",
                original_error=e,
            ) from e

    async def _download_and_extract(self, url: str, force_refresh: bool = False) -> Path:
        """Download and extract a plugin from URL."""
        parsed_url = urlparse(url)
        filename = Path(parsed_url.path).name or "plugin"

        # Create cache path
        cache_path = self.cache_dir / f"url_{hash(url)}"
        cache_file = cache_path / filename

        # Check if already cached
        if not force_refresh and cache_file.exists():
            self._logger.debug(f"Using cached plugin from {cache_file}")
            return self._extract_if_needed(cache_file)

        # Create cache directory
        cache_path.mkdir(parents=True, exist_ok=True)

        # Download file
        if not self._session:
            self._session = aiohttp.ClientSession()

        self._logger.debug(f"Downloading plugin from {url}")

        async with self._session.get(url) as response:
            response.raise_for_status()

            with open(cache_file, "wb") as f:
                async for chunk in response.content.iter_chunked(8192):
                    f.write(chunk)

        self._logger.debug(f"Downloaded plugin to {cache_file}")

        # Extract if needed
        return self._extract_if_needed(cache_file)

    def _extract_if_needed(self, file_path: Path) -> Path:
        """Extract archive if needed, return path to content."""

        # Check if it's an archive
        if file_path.suffix.lower() in [".zip"]:
            extract_path = file_path.parent / file_path.stem

            if extract_path.exists():
                return extract_path

            self._logger.debug(f"Extracting ZIP archive: {file_path}")

            with zipfile.ZipFile(file_path, "r") as zip_ref:
                _safe_extract_zip(zip_ref, extract_path)

            return extract_path

        elif file_path.suffix.lower() in [".tar", ".tar.gz", ".tgz"]:
            extract_path = file_path.parent / file_path.stem.replace(".tar", "")

            if extract_path.exists():
                return extract_path

            self._logger.debug(f"Extracting TAR archive: {file_path}")

            with tarfile.open(file_path, "r:*") as tar_ref:
                _safe_extract_tar(tar_ref, extract_path)

            return extract_path

        else:
            # Single file, return parent directory
            return file_path.parent

    async def _clone_repository(
        self, repo_url: str, branch: str = "main", force_refresh: bool = False
    ) -> Path:
        """Clone or update a Git repository."""

        # Create cache path based on repo URL
        repo_hash = hash(repo_url + branch)
        repo_path = self.cache_dir / f"repo_{repo_hash}"

        # Check if already cloned
        if not force_refresh and repo_path.exists() and (repo_path / ".git").exists():
            self._logger.debug(f"Updating existing repository at {repo_path}")

            # Update repository
            proc = await asyncio.create_subprocess_exec(
                "git",
                "pull",
                "origin",
                branch,
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                self._logger.warning(f"Git pull failed: {stderr.decode()}")
                # Continue with existing repo

            return repo_path

        # Remove existing directory if force refresh
        if force_refresh and repo_path.exists():
            import shutil

            shutil.rmtree(repo_path)

        # Clone repository
        repo_path.mkdir(parents=True, exist_ok=True)

        self._logger.debug(f"Cloning repository {repo_url} to {repo_path}")

        proc = await asyncio.create_subprocess_exec(
            "git",
            "clone",
            "--branch",
            branch,
            "--depth",
            "1",
            repo_url,
            str(repo_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise PluginLoadError(
                "git_clone",
                plugin_path=repo_url,
                loader_type="remote_git",
                original_error=RuntimeError(f"Git clone failed: {stderr.decode()}"),
            )

        return repo_path

    async def _query_registry(
        self, registry_url: str, plugin_name: str, version: Optional[str] = None
    ) -> dict[str, Any]:
        """Query plugin registry for plugin information."""

        if not self._session:
            self._session = aiohttp.ClientSession()

        # Construct registry API URL
        version_param = f"/{version}" if version else ""
        query_url = f"{registry_url.rstrip('/')}/plugins/{plugin_name}{version_param}"

        self._logger.debug(f"Querying plugin registry: {query_url}")

        try:
            async with self._session.get(query_url) as response:
                response.raise_for_status()
                plugin_info = await response.json()

                # Validate required fields
                required_fields = ["download_url"]
                missing_fields = [field for field in required_fields if field not in plugin_info]

                if missing_fields:
                    raise PluginLoadError(
                        plugin_name,
                        plugin_path=registry_url,
                        loader_type="remote_registry",
                        original_error=ValueError(
                            f"Registry response missing fields: {missing_fields}"
                        ),
                    )

                return plugin_info

        except aiohttp.ClientError as e:
            raise PluginLoadError(
                plugin_name,
                plugin_path=registry_url,
                loader_type="remote_registry",
                original_error=e,
            ) from e

    async def _load_plugin_from_path(
        self,
        path: Path,
        plugin_class_name: str,
        plugin_config: Optional[dict[str, Any]] = None,
    ) -> BasePlugin:
        """Load plugin from a local path (file or directory)."""

        if path.is_file():
            # Single Python file
            if path.suffix == ".py":
                return await self._python_loader.load_plugin_from_file(
                    path, plugin_class_name, plugin_config
                )
            else:
                raise PluginLoadError(
                    plugin_class_name,
                    plugin_path=str(path),
                    loader_type="remote_file",
                    original_error=ValueError(f"Unsupported file type: {path.suffix}"),
                )

        elif path.is_dir():
            # Directory - search for plugin files

            # First try to find YAML config files
            yaml_files = list(path.glob("*.yaml")) + list(path.glob("*.yml"))

            if yaml_files:
                # Load from YAML config
                plugins = await self._yaml_loader.load_plugins_from_file(yaml_files[0])

                # Find the requested plugin
                for plugin in plugins:
                    if plugin.__class__.__name__ == plugin_class_name:
                        return plugin

                raise PluginLoadError(
                    plugin_class_name,
                    plugin_path=str(path),
                    loader_type="remote_directory",
                    original_error=ValueError(
                        f"Plugin class '{plugin_class_name}' not found in YAML config"
                    ),
                )

            else:
                # Search for Python files
                python_files = list(path.glob("*.py"))

                for py_file in python_files:
                    try:
                        return await self._python_loader.load_plugin_from_file(
                            py_file, plugin_class_name, plugin_config
                        )
                    except PluginLoadError:
                        continue  # Try next file

                raise PluginLoadError(
                    plugin_class_name,
                    plugin_path=str(path),
                    loader_type="remote_directory",
                    original_error=ValueError(
                        f"Plugin class '{plugin_class_name}' not found in directory"
                    ),
                )

        else:
            raise PluginLoadError(
                plugin_class_name,
                plugin_path=str(path),
                loader_type="remote_path",
                original_error=FileNotFoundError(f"Path does not exist: {path}"),
            )

    def clear_cache(self, url_pattern: Optional[str] = None) -> None:
        """
        Clear plugin cache.

        Args:
            url_pattern: Optional pattern to match URLs for selective clearing
        """
        self._logger.info(f"Clearing plugin cache at {self.cache_dir}")

        if url_pattern:
            # Selective clearing - would implement pattern matching
            self._logger.info(f"Clearing cache entries matching pattern: {url_pattern}")
            # Implementation would go here
        else:
            # Clear all cache
            import shutil

            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._logger.info("Plugin cache cleared")

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._session:
            await self._session.close()
            self._session = None

    @staticmethod
    def create_sample_registry_response() -> dict[str, Any]:
        """
        Create a sample registry API response for reference.

        Returns:
            Sample registry response structure
        """
        return {
            "name": "email_sender",
            "version": "1.2.0",
            "domain": "communication",
            "description": "Email sending plugin with SMTP support",
            "author": "DotMac Team",
            "homepage": "https://github.com/dotmac/plugins/email",
            "download_url": "https://registry.example.com/plugins/email_sender/1.2.0/download",
            "class_name": "EmailSenderPlugin",
            "dependencies": [],
            "optional_dependencies": ["communication.template_engine"],
            "tags": ["email", "smtp", "communication"],
            "categories": ["messaging"],
            "file_size": 15360,
            "checksum": "sha256:a1b2c3d4e5f6...",
            "published_at": "2024-01-15T10:30:00Z",
            "downloads": 1250,
            "rating": 4.8,
            "license": "MIT",
        }

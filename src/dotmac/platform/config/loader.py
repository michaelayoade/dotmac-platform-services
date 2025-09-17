"""
Configuration loader with validation and environment integration.

Provides utilities for loading and validating configuration from
various sources including environment variables, files, and CLI.
"""

import json

import os
from pathlib import Path
from typing import Any, Optional, Type, TypeVar

import yaml
from pydantic import ValidationError

from .base import BaseConfig
from .environments import (

    DevelopmentConfig,
    ProductionConfig,
    StagingConfig,
    TestingConfig,
    get_config,
)
from dotmac.platform.observability.unified_logging import get_logger
from dotmac.platform.licensing import configure_licensing


logger = get_logger(__name__)

T = TypeVar("T", bound=BaseConfig)

class ConfigLoader:
    """
    Configuration loader with multiple source support.

    Supports loading configuration from:
    - Environment variables
    - JSON files
    - YAML files
    - Python modules
    - Command-line arguments
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration loader.

        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = config_dir or Path.cwd() / "config"
        self._config_cache: dict[str, BaseConfig] = {}

    def load_from_env(
        self,
        config_class: Type[T] = BaseConfig,
        prefix: str = "",
    ) -> T:
        """
        Load configuration from environment variables.

        Args:
            config_class: Configuration class to instantiate
            prefix: Prefix for environment variables

        Returns:
            Configuration instance
        """
        try:
            config = config_class()
            logger.info(f"Loaded configuration from environment variables")
            return config
        except ValidationError as e:
            logger.error(f"Configuration validation failed: {e}")
            raise

    def load_from_file(
        self,
        file_path: Path,
        config_class: Type[T] = BaseConfig,
    ) -> T:
        """
        Load configuration from a file.

        Args:
            file_path: Path to configuration file
            config_class: Configuration class to instantiate

        Returns:
            Configuration instance

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValueError: If file format is not supported
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        # Determine file format
        suffix = file_path.suffix.lower()

        if suffix in [".yaml", ".yml"]:
            data = self._load_yaml(file_path)
        elif suffix == ".json":
            data = self._load_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

        try:
            config = config_class(**data)
            logger.info(f"Loaded configuration from file: {file_path}")
            return config
        except ValidationError as e:
            logger.error(f"Configuration validation failed: {e}")
            raise

    def load_for_environment(
        self,
        environment: Optional[str] = None,
        override_file: Optional[Path] = None,
    ) -> BaseConfig:
        """
        Load configuration for a specific environment.

        Args:
            environment: Environment name
            override_file: Optional override configuration file

        Returns:
            Configuration instance
        """
        # Get base configuration for environment
        config = get_config(environment)

        # Apply overrides from file if provided
        if override_file:
            overrides = self._load_overrides(override_file)
            config = self._apply_overrides(config, overrides)

        # Cache the configuration
        cache_key = f"{environment}:{override_file}"
        self._config_cache[cache_key] = config

        return config

    def _load_yaml(self, file_path: Path) -> dict[str, Any]:
        """Load YAML configuration file."""
        with open(file_path, "r") as f:
            return yaml.safe_load(f) or {}

    def _load_json(self, file_path: Path) -> dict[str, Any]:
        """Load JSON configuration file."""
        with open(file_path, "r") as f:
            return json.load(f)

    def _load_overrides(self, file_path: Path) -> dict[str, Any]:
        """Load override configuration from file."""
        suffix = file_path.suffix.lower()

        if suffix in [".yaml", ".yml"]:
            return self._load_yaml(file_path)
        elif suffix == ".json":
            return self._load_json(file_path)
        else:
            raise ValueError(f"Unsupported override file format: {suffix}")

    def _apply_overrides(
        self,
        config: BaseConfig,
        overrides: dict[str, Any],
    ) -> BaseConfig:
        """
        Apply override values to configuration.

        Args:
            config: Base configuration
            overrides: Override values

        Returns:
            Updated configuration
        """
        # Get current config as dict
        config_dict = config.model_dump()

        # Apply overrides recursively
        self._merge_dicts(config_dict, overrides)

        # Create new config instance with overrides
        return config.__class__(**config_dict)

    def _merge_dicts(self, base: dict, override: dict) -> None:
        """
        Recursively merge override dict into base dict.

        Args:
            base: Base dictionary (modified in place)
            override: Override dictionary
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_dicts(base[key], value)
            else:
                base[key] = value

    def validate_config(self, config: BaseConfig) -> list[str]:
        """
        Validate configuration and return any issues.

        Args:
            config: Configuration to validate

        Returns:
            List of validation issues (empty if valid)
        """
        issues = []

        # Check database configuration
        if config.database and config.database.url.startswith("sqlite"):
            if config.environment == "production":
                issues.append("SQLite should not be used in production")

        # Check security configuration
        if config.security.secret_key.startswith(
            "development"
        ) or config.security.secret_key.startswith("testing"):
            if config.environment in ["staging", "production"]:
                issues.append("Insecure secret key detected for non-development environment")

        # Check Redis configuration
        if config.cache.backend == "redis" and not config.redis:
            issues.append("Redis backend selected but Redis not configured")

        # Check observability configuration
        if config.observability.signoz_enabled and not config.observability.signoz_endpoint:
            issues.append("SigNoz enabled but endpoint not configured")

        # Check workflow configuration
        if config.workflow.engine == "temporal" and not config.workflow.temporal_host:
            issues.append("Temporal workflow engine selected but host not configured")

        if config.workflow.engine == "celery":
            if not config.workflow.celery_broker_url:
                issues.append("Celery workflow engine selected but broker not configured")

        return issues

    def export_config(
        self,
        config: BaseConfig,
        file_path: Path,
        format: str = "yaml",
        include_secrets: bool = False,
    ) -> None:
        """
        Export configuration to a file.

        Args:
            config: Configuration to export
            file_path: Output file path
            format: Output format (yaml or json)
            include_secrets: Whether to include sensitive values
        """
        # Convert to dict
        config_dict = config.model_dump()

        # Remove secrets if requested
        if not include_secrets:
            config_dict = self._remove_secrets(config_dict)

        # Write to file
        with open(file_path, "w") as f:
            if format == "yaml":
                yaml.safe_dump(config_dict, f, default_flow_style=False)
            elif format == "json":
                json.dump(config_dict, f, indent=2)
            else:
                raise ValueError(f"Unsupported export format: {format}")

        logger.info(f"Exported configuration to: {file_path}")

    def _remove_secrets(self, data: Any) -> Any:
        """
        Remove sensitive values from configuration data.

        Args:
            data: Configuration data

        Returns:
            Data with secrets removed
        """
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                # Check for sensitive keys
                if any(s in key.lower() for s in ["secret", "password", "token", "key"]):
                    result[key] = "***REDACTED***"
                else:
                    result[key] = self._remove_secrets(value)
            return result
        elif isinstance(data, list):
            return [self._remove_secrets(item) for item in data]
        else:
            return data

# Global loader instance
_loader: Optional[ConfigLoader] = None

def get_loader() -> ConfigLoader:
    """Get the global configuration loader instance."""
    global _loader
    if _loader is None:
        _loader = ConfigLoader()
    return _loader

def load_config(
    environment: Optional[str] = None,
    config_file: Optional[str] = None,
) -> BaseConfig:
    """
    Load configuration for the application.

    Args:
        environment: Environment name
        config_file: Optional configuration file path

    Returns:
        Loaded and validated configuration
    """
    loader = get_loader()

    # Load configuration
    override_file = Path(config_file) if config_file else None
    config = loader.load_for_environment(environment, override_file)

    # Validate configuration
    issues = loader.validate_config(config)
    if issues:
        logger.warning(f"Configuration validation issues: {issues}")

    configure_licensing(config.licensing)

    return config

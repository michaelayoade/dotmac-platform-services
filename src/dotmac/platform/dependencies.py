"""
Dependency management with clear error messages and feature flag integration.

This module provides utilities for checking optional dependencies and providing
helpful error messages when they're missing.
"""

import importlib
from typing import Dict, List, Optional, Union

from .settings import settings


class DependencyError(ImportError):
    """Raised when a required dependency is missing."""

    def __init__(
        self, feature: str, packages: Union[str, List[str]], install_cmd: Optional[str] = None
    ):
        if isinstance(packages, str):
            packages = [packages]

        pkg_list = ", ".join(packages)
        message = f"Feature '{feature}' requires: {pkg_list}"

        if install_cmd:
            message += f"\nInstall with: {install_cmd}"
        elif len(packages) == 1:
            message += f"\nInstall with: pip install {packages[0]}"
        else:
            message += f"\nInstall with: pip install {' '.join(packages)}"

        super().__init__(message)


class DependencyChecker:
    """Utility for checking and managing optional dependencies."""

    # Mapping of feature flags to required packages
    FEATURE_DEPENDENCIES: Dict[str, Dict[str, Union[str, List[str]]]] = {
        # Storage backends
        "storage_s3_enabled": {
            "packages": ["boto3", "botocore"],
            "install_cmd": "poetry install --extras s3",
        },
        "storage_minio_enabled": {
            "packages": ["minio"],
            "install_cmd": "poetry install --extras minio",
        },
        "storage_azure_enabled": {
            "packages": ["azure-storage-blob"],
            "install_cmd": "poetry install --extras azure",
        },
        # Search backends
        "search_meilisearch_enabled": {
            "packages": ["meilisearch"],
            "install_cmd": "poetry install --extras search",
        },
        "search_elasticsearch_enabled": {
            "packages": ["elasticsearch"],
            "install_cmd": "poetry install --extras search",
        },
        # GraphQL removed - using REST APIs only
        # Observability
        "tracing_opentelemetry": {
            "packages": ["opentelemetry-api", "opentelemetry-sdk"],
            "install_cmd": "poetry install --extras observability",
        },
        "metrics_prometheus": {
            "packages": ["prometheus-client"],
            "install_cmd": "poetry install --extras metrics",
        },
        "sentry_enabled": {
            "packages": ["sentry-sdk"],
            "install_cmd": "poetry install --extras sentry",
        },
        # Encryption and secrets
        "encryption_fernet": {
            "packages": ["cryptography"],
            "install_cmd": "pip install cryptography",
        },
        "secrets_vault": {"packages": ["hvac"], "install_cmd": "poetry install --extras vault"},
        # Data transfer
        "data_transfer_excel": {
            "packages": ["openpyxl", "xlsxwriter"],
            "install_cmd": "poetry install --extras data-transfer",
        },
        # File processing
        "file_processing_pdf": {
            "packages": ["PyMuPDF"],
            "install_cmd": "poetry install --extras file-processing",
        },
        "file_processing_images": {
            "packages": ["Pillow"],
            "install_cmd": "poetry install --extras file-processing",
        },
        # Task queue
        "celery_enabled": {"packages": ["celery"], "install_cmd": "poetry install --extras celery"},
        # Communication
        "slack_enabled": {
            "packages": ["slack-sdk"],
            "install_cmd": "poetry install --extras notifications",
        },
        # Database
        "db_postgresql": {"packages": ["asyncpg"], "install_cmd": "pip install asyncpg"},
        "db_sqlite": {"packages": ["aiosqlite"], "install_cmd": "pip install aiosqlite"},
    }

    @classmethod
    def check_feature_dependency(cls, feature_flag: str) -> bool:
        """
        Check if a feature's dependencies are available.

        Args:
            feature_flag: The feature flag name (e.g., 'storage_s3_enabled')

        Returns:
            True if all dependencies are available, False otherwise
        """
        if feature_flag not in cls.FEATURE_DEPENDENCIES:
            return True  # No dependencies required

        dep_info = cls.FEATURE_DEPENDENCIES[feature_flag]
        packages = dep_info["packages"]
        if isinstance(packages, str):
            packages = [packages]

        for package in packages:
            try:
                importlib.import_module(package)
            except ImportError:
                return False
        return True

    @classmethod
    def require_feature_dependency(cls, feature_flag: str) -> None:
        """
        Require that a feature's dependencies are available, raise DependencyError if not.

        Args:
            feature_flag: The feature flag name

        Raises:
            DependencyError: If dependencies are missing
        """
        if feature_flag not in cls.FEATURE_DEPENDENCIES:
            return  # No dependencies required

        dep_info = cls.FEATURE_DEPENDENCIES[feature_flag]
        packages = dep_info["packages"]
        install_cmd = dep_info.get("install_cmd")

        if isinstance(packages, str):
            packages = [packages]

        missing = []
        for package in packages:
            try:
                importlib.import_module(package)
            except ImportError:
                missing.append(package)

        if missing:
            raise DependencyError(feature_flag, missing, install_cmd)

    @classmethod
    def check_enabled_features(cls) -> Dict[str, bool]:
        """
        Check all enabled features and their dependency status.

        Returns:
            Dict mapping feature names to whether their dependencies are available
        """
        results = {}

        for feature_flag, _dep_info in cls.FEATURE_DEPENDENCIES.items():
            # Check if feature is enabled in settings
            feature_enabled = getattr(settings.features, feature_flag, False)
            if feature_enabled:
                results[feature_flag] = cls.check_feature_dependency(feature_flag)

        return results

    @classmethod
    def validate_enabled_features(cls) -> None:
        """
        Validate all enabled features have their dependencies available.

        Raises:
            DependencyError: If any enabled feature has missing dependencies
        """
        for feature_flag, _dep_info in cls.FEATURE_DEPENDENCIES.items():
            # Check if feature is enabled in settings
            feature_enabled = getattr(settings.features, feature_flag, False)
            if feature_enabled:
                cls.require_feature_dependency(feature_flag)


def require_dependency(feature_flag: str):
    """
    Decorator to require dependencies for a function/class.

    Args:
        feature_flag: The feature flag name

    Example:
        @require_dependency("storage_s3_enabled")
        def create_s3_client():
            import boto3
            return boto3.client('s3')
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Check if feature is enabled
            if not getattr(settings.features, feature_flag, False):
                raise ValueError(f"Feature '{feature_flag}' is not enabled in settings")

            # Check dependencies
            DependencyChecker.require_feature_dependency(feature_flag)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def safe_import(module_name: str, feature_flag: Optional[str] = None):
    """
    Safely import a module with helpful error messages.

    Args:
        module_name: The module to import
        feature_flag: Optional feature flag that controls this import

    Returns:
        The imported module or None if not available

    Raises:
        DependencyError: If feature is enabled but dependency is missing
    """
    try:
        return importlib.import_module(module_name)
    except ImportError:
        if feature_flag:
            # Check if feature is enabled
            feature_enabled = getattr(settings.features, feature_flag, False)
            if feature_enabled:
                # Feature is enabled but dependency is missing - this is an error
                DependencyChecker.require_feature_dependency(feature_flag)
        return None


# Convenience functions for common dependencies
def require_boto3():
    """Require boto3 for S3 operations."""
    if settings.features.storage_s3_enabled:
        DependencyChecker.require_feature_dependency("storage_s3_enabled")
        import boto3

        return boto3
    else:
        raise ValueError("S3 storage is not enabled. Set FEATURES__STORAGE_S3_ENABLED=true")


def require_meilisearch():
    """Require meilisearch for search operations."""
    if settings.features.search_meilisearch_enabled:
        DependencyChecker.require_feature_dependency("search_meilisearch_enabled")
        import meilisearch

        return meilisearch
    else:
        raise ValueError(
            "MeiliSearch is not enabled. Set FEATURES__SEARCH_MEILISEARCH_ENABLED=true"
        )


def require_cryptography():
    """Require cryptography for Fernet encryption."""
    if settings.features.encryption_fernet:
        DependencyChecker.require_feature_dependency("encryption_fernet")
        from cryptography.fernet import Fernet

        return Fernet
    else:
        raise ValueError("Fernet encryption is not enabled. Set FEATURES__ENCRYPTION_FERNET=true")


# GraphQL support removed - using REST APIs only

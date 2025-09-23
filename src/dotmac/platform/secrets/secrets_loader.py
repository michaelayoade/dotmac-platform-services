"""
Secrets loader for fetching sensitive configuration from Vault/OpenBao.

This module provides functionality to load secrets from Vault/OpenBao
and update the application settings with secure values at runtime.
"""

import logging
from typing import Any, Dict, Optional

from dotmac.platform.secrets.vault_client import AsyncVaultClient, VaultClient, VaultError
from dotmac.platform.settings import Settings, settings

try:
    from .vault_config import get_async_vault_client, get_vault_client
    HAS_VAULT_CONFIG = True
except ImportError:
    HAS_VAULT_CONFIG = False

logger = logging.getLogger(__name__)


# Mapping of settings fields to Vault paths
SECRETS_MAPPING = {
    # Application secrets
    "secret_key": "app/secret_key",
    # Database credentials
    "database.password": "database/password",
    "database.username": "database/username",
    # Redis credentials
    "redis.password": "redis/password",
    # JWT secrets
    "jwt.secret_key": "auth/jwt_secret",
    # Email/SMTP credentials
    "email.smtp_password": "smtp/password",
    "email.smtp_user": "smtp/username",
    # Storage credentials (S3/MinIO)
    "storage.access_key": "storage/access_key",
    "storage.secret_key": "storage/secret_key",
    # Vault token (for token renewal)
    "vault.token": "vault/token",
    # Observability
    "observability.sentry_dsn": "observability/sentry_dsn",
}


def set_nested_attr(obj: Any, path: str, value: Any) -> None:
    """
    Set a nested attribute on an object using dot notation.

    Args:
        obj: The object to set the attribute on
        path: Dot-separated path to the attribute (e.g., "database.password")
        value: The value to set
    """
    parts = path.split(".")
    for part in parts[:-1]:
        obj = getattr(obj, part)
    setattr(obj, parts[-1], value)


def get_nested_attr(obj: Any, path: str, default: Any = None) -> Any:
    """
    Get a nested attribute from an object using dot notation.

    Args:
        obj: The object to get the attribute from
        path: Dot-separated path to the attribute
        default: Default value if attribute doesn't exist

    Returns:
        The attribute value or default
    """
    try:
        parts = path.split(".")
        for part in parts:
            obj = getattr(obj, part)
        return obj
    except AttributeError:
        return default


async def load_secrets_from_vault(
    settings_obj: Optional[Settings] = None,
    vault_client: Optional[AsyncVaultClient] = None,
) -> None:
    """
    Load secrets from Vault/OpenBao and update settings.

    This function fetches all sensitive configuration values from Vault
    and updates the settings object with these secure values.

    Args:
        settings_obj: Settings object to update (defaults to global settings)
        vault_client: Optional Vault client to use
    """
    if settings_obj is None:
        settings_obj = settings

    # Skip if Vault is not enabled
    if not settings_obj.vault.enabled:
        logger.info("Vault is disabled, using default settings values")
        return

    # Create Vault client if not provided
    if vault_client is None:
        if HAS_VAULT_CONFIG:
            # Use configured client from vault_config
            vault_client = get_async_vault_client()
        else:
            # Fallback to creating client directly
            vault_client = AsyncVaultClient(
                url=settings_obj.vault.url,
                token=settings_obj.vault.token,
                namespace=settings_obj.vault.namespace,
                mount_path=settings_obj.vault.mount_path,
                kv_version=settings_obj.vault.kv_version,
            )

    try:
        # Check Vault health
        if not await vault_client.health_check():
            logger.error("Vault health check failed, using default settings")
            return

        # Collect all Vault paths to fetch
        vault_paths = list(set(SECRETS_MAPPING.values()))

        logger.info(f"Fetching {len(vault_paths)} secrets from Vault")

        # Fetch all secrets in parallel
        secrets = await vault_client.get_secrets(vault_paths)

        # Update settings with fetched secrets
        updated_count = 0
        for setting_path, vault_path in SECRETS_MAPPING.items():
            secret_data = secrets.get(vault_path, {})

            # Vault stores key-value pairs, we need the 'value' key
            # Or the secret could be stored directly as a string
            if isinstance(secret_data, dict) and "value" in secret_data:
                secret_value = secret_data["value"]
            elif isinstance(secret_data, str):
                secret_value = secret_data
            elif secret_data:
                # If it's a dict without 'value', take the first value
                secret_value = next(iter(secret_data.values()), None) if secret_data else None
            else:
                secret_value = None

            if secret_value:
                try:
                    set_nested_attr(settings_obj, setting_path, secret_value)
                    updated_count += 1
                    logger.debug(f"Updated {setting_path} from Vault")
                except Exception as e:
                    logger.error(f"Failed to set {setting_path}: {e}")

        logger.info(f"Successfully loaded {updated_count} secrets from Vault")

        # Validate critical secrets in production
        if settings_obj.environment == "production":
            validate_production_secrets(settings_obj)

    except VaultError as e:
        logger.error(f"Failed to load secrets from Vault: {e}")
        # In production, we might want to fail fast here
        if settings_obj.environment == "production":
            raise
    finally:
        # Clean up client if we created it
        if vault_client and not isinstance(vault_client, AsyncVaultClient):
            await vault_client.close()


def load_secrets_from_vault_sync(
    settings_obj: Optional[Settings] = None,
    vault_client: Optional[VaultClient] = None,
) -> None:
    """
    Synchronous version of load_secrets_from_vault.

    Use this for non-async contexts.
    """
    if settings_obj is None:
        settings_obj = settings

    if not settings_obj.vault.enabled:
        logger.info("Vault is disabled, using default settings values")
        return

    if vault_client is None:
        vault_client = VaultClient(
            url=settings_obj.vault.url,
            token=settings_obj.vault.token,
            namespace=settings_obj.vault.namespace,
            mount_path=settings_obj.vault.mount_path,
            kv_version=settings_obj.vault.kv_version,
        )

    try:
        if not vault_client.health_check():
            logger.error("Vault health check failed, using default settings")
            return

        vault_paths = list(set(SECRETS_MAPPING.values()))

        logger.info(f"Fetching {len(vault_paths)} secrets from Vault")

        secrets = vault_client.get_secrets(vault_paths)

        updated_count = 0
        for setting_path, vault_path in SECRETS_MAPPING.items():
            secret_data = secrets.get(vault_path, {})

            if isinstance(secret_data, dict) and "value" in secret_data:
                secret_value = secret_data["value"]
            elif isinstance(secret_data, str):
                secret_value = secret_data
            elif secret_data:
                secret_value = next(iter(secret_data.values()), None) if secret_data else None
            else:
                secret_value = None

            if secret_value:
                try:
                    set_nested_attr(settings_obj, setting_path, secret_value)
                    updated_count += 1
                    logger.debug(f"Updated {setting_path} from Vault")
                except Exception as e:
                    logger.error(f"Failed to set {setting_path}: {e}")

        logger.info(f"Successfully loaded {updated_count} secrets from Vault")

        if settings_obj.environment == "production":
            validate_production_secrets(settings_obj)

    except VaultError as e:
        logger.error(f"Failed to load secrets from Vault: {e}")
        if settings_obj.environment == "production":
            raise
    finally:
        if vault_client and not isinstance(vault_client, VaultClient):
            vault_client.close()


def validate_production_secrets(settings_obj: Settings) -> None:
    """
    Validate that critical secrets are properly set for production.

    Args:
        settings_obj: Settings object to validate

    Raises:
        ValueError: If critical secrets are missing or invalid
    """
    errors = []

    # Check critical secrets
    if settings_obj.secret_key == "change-me-in-production":
        errors.append("Application secret_key must be changed from default")

    if settings_obj.jwt.secret_key == "change-me":
        errors.append("JWT secret_key must be changed from default")

    if not settings_obj.database.password:
        errors.append("Database password is not set")

    # Check for weak passwords (basic check)
    if settings_obj.database.password and len(settings_obj.database.password) < 12:
        errors.append("Database password is too short (minimum 12 characters)")

    if errors:
        error_msg = "Production secrets validation failed:\n" + "\n".join(
            f"  - {e}" for e in errors
        )
        logger.error(error_msg)
        raise ValueError(error_msg)


def get_vault_secret(path: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to fetch a single secret from Vault.

    Args:
        path: Vault path to the secret

    Returns:
        Secret data or None if not found
    """
    if not settings.vault.enabled:
        return None

    try:
        client = VaultClient(
            url=settings.vault.url,
            token=settings.vault.token,
            namespace=settings.vault.namespace,
            mount_path=settings.vault.mount_path,
            kv_version=settings.vault.kv_version,
        )

        with client:
            return client.get_secret(path)
    except VaultError as e:
        logger.error(f"Failed to fetch secret from {path}: {e}")
        return None


async def get_vault_secret_async(path: str) -> Optional[Dict[str, Any]]:
    """
    Async convenience function to fetch a single secret from Vault.

    Args:
        path: Vault path to the secret

    Returns:
        Secret data or None if not found
    """
    if not settings.vault.enabled:
        return None

    try:
        client = AsyncVaultClient(
            url=settings.vault.url,
            token=settings.vault.token,
            namespace=settings.vault.namespace,
            mount_path=settings.vault.mount_path,
            kv_version=settings.vault.kv_version,
        )

        async with client:
            return await client.get_secret(path)
    except VaultError as e:
        logger.error(f"Failed to fetch secret from {path}: {e}")
        return None

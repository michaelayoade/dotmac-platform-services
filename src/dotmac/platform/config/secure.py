"""
Secure configuration management with secrets integration.

Provides secure handling of sensitive configuration values with
support for environment variables and external secrets management.
"""

import asyncio

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Optional

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

@dataclass
class SecureConfigValue:
    """Represents a securely retrieved configuration value."""

    value: str
    source: str
    cached: bool = False

class SecureConfigManager:
    """
    Secure configuration manager for handling sensitive values.

    Provides:
    - Environment variable fallback
    - Caching of retrieved values
    - Async and sync interfaces
    - Extensible for external secrets managers
    """

    def __init__(self):
        """Initialize the secure config manager."""
        self._cache: dict[str, SecureConfigValue] = {}
        self._external_provider: Optional[Any] = None

    async def get_secret(
        self,
        key: str,
        env_fallback: Optional[str] = None,
        default: Optional[str] = None,
        required: bool = True,
    ) -> str:
        """
        Get a secret value securely.

        Args:
            key: Secret key/path
            env_fallback: Environment variable name for fallback
            default: Default value if not found
            required: Whether this secret is required

        Returns:
            Secret value as string

        Raises:
            ValueError: If required secret is not found
        """
        # Check cache first
        if key in self._cache:
            cached_value = self._cache[key]
            logger.debug(f"Retrieved cached secret: {key} from {cached_value.source}")
            return cached_value.value

        secret_value = None
        source = "unknown"

        # Try external provider first (if configured)
        if self._external_provider:
            try:
                secret_value = await self._get_from_provider(key)
                if secret_value:
                    source = "external_provider"
                    logger.info(f"Retrieved secret from external provider: {key}")
            except Exception as e:
                logger.warning(f"External provider retrieval failed for {key}: {e}")

        # Fallback to environment variable
        if not secret_value and env_fallback:
            secret_value = os.getenv(env_fallback)
            if secret_value:
                source = "environment"
                logger.info(f"Retrieved secret from environment: {env_fallback}")

        # Use default if provided
        if not secret_value and default is not None:
            secret_value = default
            source = "default"
            logger.debug(f"Using default value for: {key}")

        # Check if secret was found
        if not secret_value:
            error_msg = f"Secret not found: {key}"
            if env_fallback:
                error_msg += f" (also checked env: {env_fallback})"

            if required:
                logger.error(error_msg)
                raise ValueError(error_msg)
            else:
                logger.warning(error_msg)
                return ""

        # Cache the result
        config_value = SecureConfigValue(value=secret_value, source=source, cached=True)
        self._cache[key] = config_value

        return secret_value

    def get_secret_sync(
        self,
        key: str,
        env_fallback: Optional[str] = None,
        default: Optional[str] = None,
        required: bool = True,
    ) -> str:
        """
        Synchronous wrapper for get_secret.

        Args:
            key: Secret key/path
            env_fallback: Environment variable name for fallback
            default: Default value if not found
            required: Whether this secret is required

        Returns:
            Secret value as string
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, can't use run_until_complete
                # Fall back to environment variable only
                return self._get_from_env_only(key, env_fallback, default, required)
            return loop.run_until_complete(self.get_secret(key, env_fallback, default, required))
        except RuntimeError:
            # No event loop running, create a new one
            return asyncio.run(self.get_secret(key, env_fallback, default, required))

    def _get_from_env_only(
        self, key: str, env_fallback: Optional[str], default: Optional[str], required: bool
    ) -> str:
        """Get secret from environment variables only (sync fallback)."""
        # Check cache
        if key in self._cache:
            return self._cache[key].value

        # Try environment variable
        secret_value = None
        source = "unknown"

        if env_fallback:
            secret_value = os.getenv(env_fallback)
            if secret_value:
                source = "environment"

        # Use default
        if not secret_value and default is not None:
            secret_value = default
            source = "default"

        # Check if found
        if not secret_value:
            if required:
                raise ValueError(f"Secret not found: {key}")
            return ""

        # Cache
        self._cache[key] = SecureConfigValue(value=secret_value, source=source, cached=True)

        return secret_value

    async def _get_from_provider(self, key: str) -> Optional[str]:
        """
        Get secret from external provider.

        This is a placeholder for integration with external secrets managers
        like HashiCorp Vault, AWS Secrets Manager, etc.

        Args:
            key: Secret key

        Returns:
            Secret value or None
        """
        # Placeholder for external provider integration
        return None

    def clear_cache(self, key: Optional[str] = None):
        """
        Clear cached secrets.

        Args:
            key: Specific key to clear, or None to clear all
        """
        if key:
            self._cache.pop(key, None)
            logger.debug(f"Cleared cache for: {key}")
        else:
            self._cache.clear()
            logger.debug("Cleared all cached secrets")

    def get_cache_info(self) -> dict[str, Any]:
        """
        Get information about cached secrets.

        Returns:
            Cache statistics and metadata
        """
        return {
            "cached_secrets": len(self._cache),
            "sources": {path: config.source for path, config in self._cache.items()},
            "external_provider": self._external_provider is not None,
        }

    def set_external_provider(self, provider: Any) -> None:
        """
        Set an external secrets provider.

        Args:
            provider: External provider instance
        """
        self._external_provider = provider
        logger.info("External secrets provider configured")

# Global instance
_config_manager: Optional[SecureConfigManager] = None

@lru_cache
def get_config_manager() -> SecureConfigManager:
    """
    Get the global secure configuration manager instance.

    Returns:
        SecureConfigManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = SecureConfigManager()
    return _config_manager

# Convenience functions for common secrets
async def get_jwt_secret() -> str:
    """Get JWT secret key."""
    config_manager = get_config_manager()
    return await config_manager.get_secret(
        key="auth/jwt_secret", env_fallback="JWT_SECRET_KEY", required=True
    )

async def get_database_url() -> str:
    """Get database connection URL."""
    config_manager = get_config_manager()
    return await config_manager.get_secret(
        key="database/url", env_fallback="DATABASE_URL", required=True
    )

async def get_redis_url() -> str:
    """Get Redis connection URL."""
    config_manager = get_config_manager()
    return await config_manager.get_secret(
        key="redis/url",
        env_fallback="REDIS_URL",
        default="redis://localhost:6379/0",
        required=False,
    )

async def get_api_key(service: str) -> str:
    """
    Get API key for a specific service.

    Args:
        service: Service name

    Returns:
        API key
    """
    config_manager = get_config_manager()
    return await config_manager.get_secret(
        key=f"api_keys/{service}", env_fallback=f"{service.upper()}_API_KEY", required=True
    )

async def get_encryption_key() -> str:
    """Get data encryption key."""
    config_manager = get_config_manager()
    return await config_manager.get_secret(
        key="security/encryption_key", env_fallback="ENCRYPTION_KEY", required=True
    )

"""
Vault/OpenBao configuration and connection management.

This module provides utilities to configure and connect to Vault/OpenBao backends.
"""

import os
from typing import Any

import structlog
from pydantic import BaseModel, Field

from ..settings import get_settings

logger = structlog.get_logger(__name__)


class VaultConnectionConfig(BaseModel):
    """Configuration for Vault/OpenBao connection."""

    url: str = Field(description="Vault/OpenBao server URL")
    token: str | None = Field(None, description="Authentication token")
    namespace: str | None = Field(None, description="Vault namespace (enterprise)")
    mount_path: str = Field("secret", description="KV mount path")
    kv_version: int = Field(2, description="KV version (1 or 2)")
    timeout: float = Field(30.0, description="Request timeout in seconds")
    verify_ssl: bool = Field(True, description="Verify SSL certificates")
    role_id: str | None = Field(None, description="AppRole role ID")
    secret_id: str | None = Field(None, description="AppRole secret ID")
    kubernetes_role: str | None = Field(None, description="Kubernetes auth role")


def get_vault_config_from_env() -> VaultConnectionConfig:
    """
    Get Vault configuration from environment variables.

    Environment variables:
        VAULT_ADDR: Vault server URL
        VAULT_TOKEN: Authentication token
        VAULT_NAMESPACE: Vault namespace
        VAULT_MOUNT_PATH: KV mount path (default: secret)
        VAULT_KV_VERSION: KV version (default: 2)
        VAULT_SKIP_VERIFY: Skip SSL verification if set
        VAULT_ROLE_ID: AppRole role ID
        VAULT_SECRET_ID: AppRole secret ID
        VAULT_KUBERNETES_ROLE: Kubernetes auth role
    """
    return VaultConnectionConfig(
        url=os.getenv("VAULT_ADDR", "http://localhost:8200"),
        token=os.getenv("VAULT_TOKEN"),
        namespace=os.getenv("VAULT_NAMESPACE"),
        mount_path=os.getenv("VAULT_MOUNT_PATH", "secret"),
        kv_version=int(os.getenv("VAULT_KV_VERSION", "2")),
        verify_ssl=not os.getenv("VAULT_SKIP_VERIFY"),
        role_id=os.getenv("VAULT_ROLE_ID"),
        secret_id=os.getenv("VAULT_SECRET_ID"),
        kubernetes_role=os.getenv("VAULT_KUBERNETES_ROLE"),
    )


def get_vault_config_from_settings() -> VaultConnectionConfig:
    """Get Vault configuration from platform settings."""
    settings = get_settings()

    if not settings.vault.enabled:
        raise ValueError("Vault is not enabled in settings")

    return VaultConnectionConfig(
        url=settings.vault.url,
        token=settings.vault.token,
        namespace=settings.vault.namespace,
        mount_path=settings.vault.mount_path,
        kv_version=settings.vault.kv_version,
    )


def get_vault_config() -> VaultConnectionConfig:
    """
    Get Vault configuration from the best available source.

    Priority:
    1. Environment variables (if VAULT_ADDR is set)
    2. Platform settings
    3. Default configuration
    """
    # Check if Vault is configured via environment
    if os.getenv("VAULT_ADDR"):
        logger.info("Using Vault configuration from environment")
        return get_vault_config_from_env()

    # Check platform settings
    settings = get_settings()
    if settings.vault.enabled:
        logger.info("Using Vault configuration from settings")
        return get_vault_config_from_settings()

    # Return default configuration for development
    logger.warning("Using default Vault configuration (development mode)")
    return VaultConnectionConfig(
        url="http://localhost:8200",
        token="root-token",
        mount_path="secret",
        kv_version=2,
    )


class VaultConnectionManager:
    """Manages Vault client connections with connection pooling and retry logic."""

    def __init__(self, config: VaultConnectionConfig | None = None):
        """Initialize connection manager."""
        self.config = config or get_vault_config()
        self._client = None
        self._async_client = None

    def get_sync_client(self):
        """Get or create synchronous Vault client."""
        if self._client is None:
            from .vault_client import VaultClient

            self._client = VaultClient(
                url=self.config.url,
                token=self.config.token,
                namespace=self.config.namespace,
                mount_path=self.config.mount_path,
                kv_version=self.config.kv_version,
                timeout=self.config.timeout,
            )

            # Authenticate if using AppRole
            if self.config.role_id and self.config.secret_id:
                self._authenticate_approle()

            # Authenticate if using Kubernetes
            if self.config.kubernetes_role:
                self._authenticate_kubernetes()

        return self._client

    def get_async_client(self):
        """Get or create asynchronous Vault client."""
        if self._async_client is None:
            from .vault_client import AsyncVaultClient

            self._async_client = AsyncVaultClient(
                url=self.config.url,
                token=self.config.token,
                namespace=self.config.namespace,
                mount_path=self.config.mount_path,
                kv_version=self.config.kv_version,
                timeout=self.config.timeout,
            )

        return self._async_client

    def _authenticate_approle(self):
        """Authenticate using AppRole."""
        if not self._client:
            return

        try:
            # Send AppRole authentication request
            response = self._client.client.post(
                "/v1/auth/approle/login",
                json={
                    "role_id": self.config.role_id,
                    "secret_id": self.config.secret_id,
                },
            )
            response.raise_for_status()

            # Extract token from response
            data = response.json()
            token = data["auth"]["client_token"]

            # Update client with new token
            self._client.token = token
            self._client.client.headers["X-Vault-Token"] = token

            logger.info("Successfully authenticated with AppRole")

        except Exception as e:
            logger.error("Failed to authenticate with AppRole", error=str(e))
            raise

    def _authenticate_kubernetes(self):
        """Authenticate using Kubernetes service account."""
        if not self._client:
            return

        try:
            # Read service account token
            with open("/var/run/secrets/kubernetes.io/serviceaccount/token") as f:
                jwt_token = f.read()

            # Send Kubernetes authentication request
            response = self._client.client.post(
                "/v1/auth/kubernetes/login",
                json={
                    "role": self.config.kubernetes_role,
                    "jwt": jwt_token,
                },
            )
            response.raise_for_status()

            # Extract token from response
            data = response.json()
            token = data["auth"]["client_token"]

            # Update client with new token
            self._client.token = token
            self._client.client.headers["X-Vault-Token"] = token

            logger.info("Successfully authenticated with Kubernetes")

        except FileNotFoundError:
            logger.error("Kubernetes service account token not found")
            raise
        except Exception as e:
            logger.error("Failed to authenticate with Kubernetes", error=str(e))
            raise

    def close(self):
        """Close client connections."""
        if self._client:
            self._client.close()
            self._client = None

        if self._async_client:
            self._async_client.close()
            self._async_client = None


# Global connection manager instance
_connection_manager: VaultConnectionManager | None = None


def get_vault_connection_manager() -> VaultConnectionManager:
    """Get or create global Vault connection manager."""
    global _connection_manager

    if _connection_manager is None:
        _connection_manager = VaultConnectionManager()

    return _connection_manager


def get_vault_client():
    """Get configured Vault client (synchronous)."""
    manager = get_vault_connection_manager()
    return manager.get_sync_client()


def get_async_vault_client():
    """Get configured Vault client (asynchronous)."""
    manager = get_vault_connection_manager()
    return manager.get_async_client()


# Health check function
def check_vault_health() -> dict[str, Any]:
    """
    Check Vault server health.

    Returns:
        Dictionary with health status information
    """
    try:
        client = get_vault_client()
        response = client.client.get("/v1/sys/health")

        return {
            "healthy": response.status_code == 200,
            "status_code": response.status_code,
            "sealed": response.json().get("sealed", False),
            "initialized": response.json().get("initialized", True),
            "version": response.json().get("version", "unknown"),
        }
    except Exception as e:
        logger.error("Vault health check failed", error=str(e))
        return {
            "healthy": False,
            "error": str(e),
        }

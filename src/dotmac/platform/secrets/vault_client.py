"""
Vault/OpenBao client for secure secrets management.

Provides a simple interface to fetch secrets from HashiCorp Vault or OpenBao.
"""

import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class VaultError(Exception):
    """Base exception for Vault operations."""

    pass


class VaultAuthenticationError(VaultError):
    """Raised when Vault authentication fails."""

    pass


class VaultClient:
    """
    Client for interacting with HashiCorp Vault or OpenBao.

    Supports KV v2 secrets engine for secure secret storage and retrieval.
    """

    def __init__(
        self,
        url: str,
        token: Optional[str] = None,
        namespace: Optional[str] = None,
        mount_path: str = "secret",
        kv_version: int = 2,
        timeout: float = 30.0,
    ):
        """
        Initialize Vault client.

        Args:
            url: Vault/OpenBao server URL
            token: Authentication token
            namespace: Vault namespace (enterprise feature)
            mount_path: KV secrets engine mount path
            kv_version: KV secrets engine version (1 or 2)
            timeout: Request timeout in seconds
        """
        self.url = url.rstrip("/")
        self.token = token
        self.namespace = namespace
        self.mount_path = mount_path
        self.kv_version = kv_version
        self.timeout = timeout

        # Create HTTP client with headers
        headers = {}
        if token:
            headers["X-Vault-Token"] = token
        if namespace:
            headers["X-Vault-Namespace"] = namespace

        self.client = httpx.Client(
            base_url=self.url,
            headers=headers,
            timeout=httpx.Timeout(timeout),
        )

    def _get_secret_path(self, path: str) -> str:
        """Build the full API path for a secret."""
        # Remove leading/trailing slashes from path
        path = path.strip("/")

        if self.kv_version == 2:
            # KV v2 uses /data/ in the path
            return f"/v1/{self.mount_path}/data/{path}"
        else:
            # KV v1 uses direct path
            return f"/v1/{self.mount_path}/{path}"

    def get_secret(self, path: str) -> Dict[str, Any]:
        """
        Retrieve a secret from Vault.

        Args:
            path: Secret path (e.g., "database/credentials")

        Returns:
            Dictionary containing secret data

        Raises:
            VaultError: If secret retrieval fails
        """
        try:
            secret_path = self._get_secret_path(path)
            response = self.client.get(secret_path)

            if response.status_code == 403:
                raise VaultAuthenticationError(f"Permission denied accessing secret at {path}")
            elif response.status_code == 404:
                logger.warning(f"Secret not found at path: {path}")
                return {}

            response.raise_for_status()
            data = response.json()

            # Extract data based on KV version
            if self.kv_version == 2:
                return data.get("data", {}).get("data", {})
            else:
                return data.get("data", {})

        except httpx.HTTPError as e:
            raise VaultError(f"Failed to retrieve secret from {path}: {e}")

    def get_secrets(self, paths: list[str]) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve multiple secrets from Vault.

        Args:
            paths: List of secret paths

        Returns:
            Dictionary mapping paths to their secret data
        """
        secrets = {}
        for path in paths:
            try:
                secrets[path] = self.get_secret(path)
            except VaultError as e:
                logger.error(f"Failed to fetch secret at {path}: {e}")
                secrets[path] = {}
        return secrets

    def set_secret(self, path: str, data: Dict[str, Any]) -> None:
        """
        Store a secret in Vault.

        Args:
            path: Secret path
            data: Secret data to store

        Raises:
            VaultError: If secret storage fails
        """
        try:
            secret_path = self._get_secret_path(path)

            # Wrap data for KV v2
            if self.kv_version == 2:
                payload = {"data": data}
            else:
                payload = data

            response = self.client.post(secret_path, json=payload)

            if response.status_code == 403:
                raise VaultAuthenticationError(f"Permission denied writing secret to {path}")

            response.raise_for_status()

        except httpx.HTTPError as e:
            raise VaultError(f"Failed to store secret at {path}: {e}")

    def list_secrets(self, path: str = "") -> list[str]:
        """
        List secrets at a given path.

        Args:
            path: Path to list (empty string for root)

        Returns:
            List of secret keys at the path

        Raises:
            VaultError: If listing fails
        """
        try:
            # Build the list path
            path = path.strip("/")
            if self.kv_version == 2:
                list_path = f"/v1/{self.mount_path}/metadata/{path}"
            else:
                list_path = f"/v1/{self.mount_path}/{path}"

            # Append ?list=true to get listing
            response = self.client.get(f"{list_path}?list=true")

            if response.status_code == 404:
                return []

            response.raise_for_status()
            data = response.json()

            # Extract keys from response
            keys = data.get("data", {}).get("keys", [])
            return keys

        except httpx.HTTPError as e:
            raise VaultError(f"Failed to list secrets at {path}: {e}")

    def delete_secret(self, path: str) -> None:
        """
        Delete a secret from Vault.

        Args:
            path: Secret path to delete

        Raises:
            VaultError: If deletion fails
        """
        try:
            # Build the delete path
            path = path.strip("/")
            if self.kv_version == 2:
                delete_path = f"/v1/{self.mount_path}/metadata/{path}"
            else:
                delete_path = f"/v1/{self.mount_path}/{path}"

            response = self.client.delete(delete_path)

            if response.status_code == 403:
                raise VaultAuthenticationError(f"Permission denied deleting secret at {path}")

            # 204 No Content is success for delete
            if response.status_code not in (200, 204, 404):
                response.raise_for_status()

        except httpx.HTTPError as e:
            raise VaultError(f"Failed to delete secret at {path}: {e}")

    def health_check(self) -> bool:
        """
        Check if Vault is healthy and accessible.

        Returns:
            True if Vault is healthy, False otherwise
        """
        try:
            response = self.client.get("/v1/sys/health")
            return response.status_code in (200, 429, 473, 501, 503)
        except Exception as e:
            logger.error(f"Vault health check failed: {e}")
            return False

    def close(self):
        """Close the HTTP client connection."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class AsyncVaultClient:
    """
    Async client for interacting with Vault/OpenBao.
    """

    def __init__(
        self,
        url: str,
        token: Optional[str] = None,
        namespace: Optional[str] = None,
        mount_path: str = "secret",
        kv_version: int = 2,
        timeout: float = 30.0,
    ):
        """Initialize async Vault client with same parameters as sync version."""
        self.url = url.rstrip("/")
        self.token = token
        self.namespace = namespace
        self.mount_path = mount_path
        self.kv_version = kv_version
        self.timeout = timeout

        # Create async HTTP client
        headers = {}
        if token:
            headers["X-Vault-Token"] = token
        if namespace:
            headers["X-Vault-Namespace"] = namespace

        self.client = httpx.AsyncClient(
            base_url=self.url,
            headers=headers,
            timeout=httpx.Timeout(timeout),
        )

    def _get_secret_path(self, path: str) -> str:
        """Build the full API path for a secret."""
        path = path.strip("/")

        if self.kv_version == 2:
            return f"/v1/{self.mount_path}/data/{path}"
        else:
            return f"/v1/{self.mount_path}/{path}"

    async def get_secret(self, path: str) -> Dict[str, Any]:
        """Async version of get_secret."""
        try:
            secret_path = self._get_secret_path(path)
            response = await self.client.get(secret_path)

            if response.status_code == 403:
                raise VaultAuthenticationError(f"Permission denied accessing secret at {path}")
            elif response.status_code == 404:
                logger.warning(f"Secret not found at path: {path}")
                return {}

            response.raise_for_status()
            data = response.json()

            if self.kv_version == 2:
                return data.get("data", {}).get("data", {})
            else:
                return data.get("data", {})

        except httpx.HTTPError as e:
            raise VaultError(f"Failed to retrieve secret from {path}: {e}")

    async def get_secrets(self, paths: list[str]) -> Dict[str, Dict[str, Any]]:
        """Async version of get_secrets."""
        import asyncio

        tasks = [self.get_secret(path) for path in paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        secrets = {}
        for path, result in zip(paths, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch secret at {path}: {result}")
                secrets[path] = {}
            else:
                secrets[path] = result

        return secrets

    async def set_secret(self, path: str, data: Dict[str, Any]) -> None:
        """Async version of set_secret."""
        try:
            secret_path = self._get_secret_path(path)

            if self.kv_version == 2:
                payload = {"data": data}
            else:
                payload = data

            response = await self.client.post(secret_path, json=payload)

            if response.status_code == 403:
                raise VaultAuthenticationError(f"Permission denied writing secret to {path}")

            response.raise_for_status()

        except httpx.HTTPError as e:
            raise VaultError(f"Failed to store secret at {path}: {e}")

    async def list_secrets(self, path: str = "") -> list[str]:
        """
        Async version of list_secrets.

        Args:
            path: Path to list (empty string for root)

        Returns:
            List of secret keys at the path

        Raises:
            VaultError: If listing fails
        """
        try:
            # Build the list path
            path = path.strip("/")
            if self.kv_version == 2:
                list_path = f"/v1/{self.mount_path}/metadata/{path}"
            else:
                list_path = f"/v1/{self.mount_path}/{path}"

            # Append ?list=true to get listing
            response = await self.client.get(f"{list_path}?list=true")

            if response.status_code == 404:
                return []

            response.raise_for_status()
            data = response.json()

            # Extract keys from response
            keys = data.get("data", {}).get("keys", [])
            return keys

        except httpx.HTTPError as e:
            raise VaultError(f"Failed to list secrets at {path}: {e}")

    async def delete_secret(self, path: str) -> None:
        """
        Async version of delete_secret.

        Args:
            path: Secret path to delete

        Raises:
            VaultError: If deletion fails
        """
        try:
            # Build the delete path
            path = path.strip("/")
            if self.kv_version == 2:
                delete_path = f"/v1/{self.mount_path}/metadata/{path}"
            else:
                delete_path = f"/v1/{self.mount_path}/{path}"

            response = await self.client.delete(delete_path)

            if response.status_code == 403:
                raise VaultAuthenticationError(f"Permission denied deleting secret at {path}")

            # 204 No Content is success for delete
            if response.status_code not in (200, 204, 404):
                response.raise_for_status()

        except httpx.HTTPError as e:
            raise VaultError(f"Failed to delete secret at {path}: {e}")

    async def health_check(self) -> bool:
        """Async version of health_check."""
        try:
            response = await self.client.get("/v1/sys/health")
            return response.status_code in (200, 429, 473, 501, 503)
        except Exception as e:
            logger.error(f"Vault health check failed: {e}")
            return False

    async def close(self):
        """Close the async HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

"""Tests for Vault client module."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import httpx

from dotmac.platform.secrets.vault_client import (
    VaultClient,
    AsyncVaultClient,
    VaultError,
    VaultAuthenticationError,
)


class TestVaultClient:
    """Test synchronous Vault client."""

    def test_vault_client_init(self):
        """Test VaultClient initialization."""
        client = VaultClient(
            url="http://vault:8200",
            token="test-token",
            namespace="test-ns",
            mount_path="secret",
            kv_version=2,
            timeout=30.0,
        )

        assert client.url == "http://vault:8200"
        assert client.token == "test-token"
        assert client.namespace == "test-ns"
        assert client.mount_path == "secret"
        assert client.kv_version == 2
        assert client.timeout == 30.0

    @patch("httpx.Client")
    def test_vault_client_headers(self, mock_httpx_client):
        """Test VaultClient sets correct headers."""
        mock_client = MagicMock()
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200", token="test-token", namespace="test-ns")

        # Check headers were set
        call_kwargs = mock_httpx_client.call_args[1]
        headers = call_kwargs["headers"]
        assert headers["X-Vault-Token"] == "test-token"
        assert headers["X-Vault-Namespace"] == "test-ns"

    def test_get_secret_path_kv_v2(self):
        """Test secret path building for KV v2."""
        client = VaultClient(url="http://vault:8200", mount_path="secret", kv_version=2)

        path = client._get_secret_path("app/database")
        assert path == "/v1/secret/data/app/database"

    def test_get_secret_path_kv_v1(self):
        """Test secret path building for KV v1."""
        client = VaultClient(url="http://vault:8200", mount_path="kv", kv_version=1)

        path = client._get_secret_path("app/config")
        assert path == "/v1/kv/app/config"

    @patch("httpx.Client")
    def test_get_secret_success(self, mock_httpx_client):
        """Test successful secret retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"data": {"username": "admin", "password": "secret123"}}
        }

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200", kv_version=2)
        result = client.get_secret("app/database")

        assert result == {"username": "admin", "password": "secret123"}
        mock_client.get.assert_called_once_with("/v1/secret/data/app/database")

    @patch("httpx.Client")
    def test_get_secret_not_found(self, mock_httpx_client):
        """Test secret not found returns empty dict."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200")
        result = client.get_secret("missing/secret")

        assert result == {}

    @patch("httpx.Client")
    def test_get_secret_permission_denied(self, mock_httpx_client):
        """Test permission denied raises VaultAuthenticationError."""
        mock_response = MagicMock()
        mock_response.status_code = 403

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200")

        with pytest.raises(VaultAuthenticationError, match="Permission denied"):
            client.get_secret("forbidden/secret")

    @patch("httpx.Client")
    def test_get_secrets_multiple(self, mock_httpx_client):
        """Test getting multiple secrets."""
        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {"data": {"data": {"key1": "value1"}}}

        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {"data": {"data": {"key2": "value2"}}}

        mock_client = MagicMock()
        mock_client.get.side_effect = [mock_response1, mock_response2]
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200", kv_version=2)
        result = client.get_secrets(["path1", "path2"])

        assert result == {"path1": {"key1": "value1"}, "path2": {"key2": "value2"}}

    @patch("httpx.Client")
    def test_set_secret_kv_v2(self, mock_httpx_client):
        """Test setting secret in KV v2."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200", kv_version=2)
        client.set_secret("app/config", {"key": "value"})

        mock_client.post.assert_called_once_with(
            "/v1/secret/data/app/config", json={"data": {"key": "value"}}
        )

    @patch("httpx.Client")
    def test_set_secret_kv_v1(self, mock_httpx_client):
        """Test setting secret in KV v1."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200", kv_version=1)
        client.set_secret("app/config", {"key": "value"})

        mock_client.post.assert_called_once_with("/v1/secret/app/config", json={"key": "value"})

    @patch("httpx.Client")
    def test_health_check_success(self, mock_httpx_client):
        """Test health check when Vault is healthy."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200")
        result = client.health_check()

        assert result is True
        mock_client.get.assert_called_once_with("/v1/sys/health")

    @patch("httpx.Client")
    def test_health_check_sealed(self, mock_httpx_client):
        """Test health check when Vault is sealed."""
        mock_response = MagicMock()
        mock_response.status_code = 503  # Sealed status

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200")
        result = client.health_check()

        assert result is True  # Still considered "healthy" for sealed vault

    @patch("httpx.Client")
    def test_health_check_failure(self, mock_httpx_client):
        """Test health check when connection fails."""
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("Connection failed")
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200")
        result = client.health_check()

        assert result is False

    @patch("httpx.Client")
    def test_context_manager(self, mock_httpx_client):
        """Test VaultClient as context manager."""
        mock_client = MagicMock()
        mock_httpx_client.return_value = mock_client

        with VaultClient(url="http://vault:8200") as client:
            assert isinstance(client, VaultClient)

        mock_client.close.assert_called_once()


class TestAsyncVaultClient:
    """Test asynchronous Vault client."""

    def test_async_vault_client_init(self):
        """Test AsyncVaultClient initialization."""
        client = AsyncVaultClient(url="http://vault:8200", token="test-token", namespace="test-ns")

        assert client.url == "http://vault:8200"
        assert client.token == "test-token"
        assert client.namespace == "test-ns"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_async_get_secret_success(self, mock_httpx_client):
        """Test async secret retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"data": {"async_key": "async_value"}}}

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value = mock_client

        client = AsyncVaultClient(url="http://vault:8200", kv_version=2)
        result = await client.get_secret("app/async")

        assert result == {"async_key": "async_value"}

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_async_get_secrets_parallel(self, mock_httpx_client):
        """Test async parallel secret retrieval."""
        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {"data": {"data": {"key1": "value1"}}}

        mock_response2 = MagicMock()
        mock_response2.status_code = 404  # Not found

        mock_response3 = MagicMock()
        mock_response3.status_code = 200
        mock_response3.json.return_value = {"data": {"data": {"key3": "value3"}}}

        mock_client = AsyncMock()
        mock_client.get.side_effect = [mock_response1, mock_response2, mock_response3]
        mock_httpx_client.return_value = mock_client

        client = AsyncVaultClient(url="http://vault:8200", kv_version=2)
        result = await client.get_secrets(["path1", "path2", "path3"])

        assert result == {
            "path1": {"key1": "value1"},
            "path2": {},  # Not found returns empty
            "path3": {"key3": "value3"},
        }

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_async_set_secret(self, mock_httpx_client):
        """Test async secret setting."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_httpx_client.return_value = mock_client

        client = AsyncVaultClient(url="http://vault:8200", kv_version=2)
        await client.set_secret("app/async", {"async": "data"})

        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_async_health_check(self, mock_httpx_client):
        """Test async health check."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value = mock_client

        client = AsyncVaultClient(url="http://vault:8200")
        result = await client.health_check()

        assert result is True

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_async_context_manager(self, mock_httpx_client):
        """Test AsyncVaultClient as async context manager."""
        mock_client = AsyncMock()
        mock_httpx_client.return_value = mock_client

        async with AsyncVaultClient(url="http://vault:8200") as client:
            assert isinstance(client, AsyncVaultClient)

        mock_client.aclose.assert_called_once()


class TestVaultErrors:
    """Test Vault error classes."""

    def test_vault_error(self):
        """Test VaultError exception."""
        error = VaultError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_vault_authentication_error(self):
        """Test VaultAuthenticationError exception."""
        error = VaultAuthenticationError("Auth failed")
        assert str(error) == "Auth failed"
        assert isinstance(error, VaultError)

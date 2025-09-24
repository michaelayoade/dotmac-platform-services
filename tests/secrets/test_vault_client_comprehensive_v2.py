"""Comprehensive vault_client tests to achieve high coverage."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock, Mock
import httpx
from dotmac.platform.secrets.vault_client import (
    VaultClient,
    AsyncVaultClient,
    VaultError,
    VaultAuthenticationError
)


class TestVaultClientComprehensive:
    """Comprehensive tests for VaultClient."""

    def test_vault_error_inheritance(self):
        """Test VaultError exception hierarchy."""
        error = VaultError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"

    def test_vault_authentication_error_inheritance(self):
        """Test VaultAuthenticationError exception hierarchy."""
        error = VaultAuthenticationError("Auth failed")
        assert isinstance(error, VaultError)
        assert isinstance(error, Exception)
        assert str(error) == "Auth failed"

    @patch("httpx.Client")
    def test_vault_client_init_with_all_params(self, mock_httpx_client):
        """Test VaultClient initialization with all parameters."""
        mock_client = MagicMock()
        mock_httpx_client.return_value = mock_client

        client = VaultClient(
            url="http://vault:8200",
            token="test-token",
            namespace="test-ns",
            mount_path="custom",
            kv_version=1,
            timeout=60.0
        )

        assert client.url == "http://vault:8200"
        assert client.token == "test-token"
        assert client.namespace == "test-ns"
        assert client.mount_path == "custom"
        assert client.kv_version == 1
        assert client.timeout == 60.0

    @patch("httpx.Client")
    def test_vault_client_init_minimal(self, mock_httpx_client):
        """Test VaultClient initialization with minimal parameters."""
        mock_client = MagicMock()
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200")

        assert client.url == "http://vault:8200"
        assert client.token is None
        assert client.namespace is None
        assert client.mount_path == "secret"
        assert client.kv_version == 2
        assert client.timeout == 30.0

    @patch("httpx.Client")
    def test_get_secret_path_methods(self, mock_httpx_client):
        """Test _get_secret_path for both KV versions."""
        mock_client = MagicMock()
        mock_httpx_client.return_value = mock_client

        # Test KV v2
        client_v2 = VaultClient(url="http://vault:8200", kv_version=2)
        path_v2 = client_v2._get_secret_path("test/secret")
        assert path_v2 == "/v1/secret/data/test/secret"

        # Test KV v1
        client_v1 = VaultClient(url="http://vault:8200", kv_version=1)
        path_v1 = client_v1._get_secret_path("test/secret")
        assert path_v1 == "/v1/secret/test/secret"

    @patch("httpx.Client")
    def test_get_data_path_methods(self, mock_httpx_client):
        """Test _get_data_path for both KV versions."""
        mock_client = MagicMock()
        mock_httpx_client.return_value = mock_client

        # Test KV v2
        client_v2 = VaultClient(url="http://vault:8200", kv_version=2)
        path_v2 = client_v2._get_data_path("test/secret")
        assert path_v2 == "/v1/secret/data/test/secret"

        # Test KV v1
        client_v1 = VaultClient(url="http://vault:8200", kv_version=1)
        path_v1 = client_v1._get_data_path("test/secret")
        assert path_v1 == "/v1/secret/test/secret"

    @patch("httpx.Client")
    def test_get_secret_success_kv2(self, mock_httpx_client):
        """Test successful secret retrieval with KV v2."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "data": {"password": "secret123", "username": "admin"},
                "metadata": {"version": 1}
            }
        }

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200", token="test-token")
        result = client.get_secret("database/creds")

        assert result == {"password": "secret123", "username": "admin"}
        mock_client.get.assert_called_once_with("/v1/secret/data/database/creds")

    @patch("httpx.Client")
    def test_get_secret_success_kv1(self, mock_httpx_client):
        """Test successful secret retrieval with KV v1."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"password": "secret123", "username": "admin"}
        }

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200", token="test-token", kv_version=1)
        result = client.get_secret("database/creds")

        assert result == {"password": "secret123", "username": "admin"}
        mock_client.get.assert_called_once_with("/v1/secret/database/creds")

    @patch("httpx.Client")
    def test_get_secret_not_found(self, mock_httpx_client):
        """Test get_secret when secret doesn't exist."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"errors": ["secret not found"]}

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200", token="test-token")
        result = client.get_secret("nonexistent")

        assert result == {}

    @patch("httpx.Client")
    def test_get_secret_http_error(self, mock_httpx_client):
        """Test get_secret with HTTP error."""
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.RequestError("Connection failed")
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200", token="test-token")

        with pytest.raises(VaultError) as exc_info:
            client.get_secret("test/path")

        assert "Failed to retrieve secret" in str(exc_info.value)

    @patch("httpx.Client")
    def test_get_secrets_multiple_paths(self, mock_httpx_client):
        """Test get_secrets with multiple paths."""
        def mock_get(path):
            if "success1" in path:
                response = MagicMock()
                response.status_code = 200
                response.json.return_value = {
                    "data": {"data": {"key1": "value1"}}
                }
                return response
            elif "success2" in path:
                response = MagicMock()
                response.status_code = 200
                response.json.return_value = {
                    "data": {"data": {"key2": "value2"}}
                }
                return response
            else:
                raise httpx.HTTPError("Failed")

        mock_client = MagicMock()
        mock_client.get.side_effect = mock_get
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200", token="test-token")

        with patch('dotmac.platform.secrets.vault_client.logger') as mock_logger:
            result = client.get_secrets(["success1", "success2", "fail"])

        assert result["success1"] == {"key1": "value1"}
        assert result["success2"] == {"key2": "value2"}
        assert result["fail"] == {}
        mock_logger.error.assert_called_once()

    @patch("httpx.Client")
    def test_health_check_success(self, mock_httpx_client):
        """Test health_check when Vault is healthy."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200", token="test-token")
        result = client.health_check()

        assert result is True
        mock_client.get.assert_called_once_with("/v1/sys/health")

    @patch("httpx.Client")
    def test_health_check_sealed(self, mock_httpx_client):
        """Test health_check when Vault is sealed."""
        mock_response = MagicMock()
        mock_response.status_code = 503

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200", token="test-token")
        result = client.health_check()

        assert result is True  # Vault returns 503 when sealed but alive

    @patch("httpx.Client")
    def test_health_check_error(self, mock_httpx_client):
        """Test health_check with connection error."""
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.RequestError("Connection refused")
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200", token="test-token")
        result = client.health_check()

        assert result is False


class TestAsyncVaultClientComprehensive:
    """Comprehensive tests for AsyncVaultClient."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_async_vault_client_init(self, mock_httpx_client):
        """Test AsyncVaultClient initialization."""
        mock_client = MagicMock()
        mock_httpx_client.return_value = mock_client

        client = AsyncVaultClient(
            url="http://vault:8200",
            token="test-token",
            namespace="test-ns"
        )

        assert client.url == "http://vault:8200"
        assert client.token == "test-token"
        assert client.namespace == "test-ns"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_async_get_secret_success(self, mock_httpx_client):
        """Test async get_secret success."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"data": {"key": "value"}}
        }

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value = mock_client

        client = AsyncVaultClient(url="http://vault:8200", token="test-token")
        result = await client.get_secret("test/path")

        assert result == {"key": "value"}

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_async_get_secret_error(self, mock_httpx_client):
        """Test async get_secret with error."""
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.HTTPError("Failed")
        mock_httpx_client.return_value = mock_client

        client = AsyncVaultClient(url="http://vault:8200", token="test-token")

        with pytest.raises(VaultError):
            await client.get_secret("test/path")

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_async_get_secrets_batch(self, mock_httpx_client):
        """Test async get_secrets with multiple paths."""
        async def mock_get(path):
            if "fail" in path:
                raise httpx.HTTPError("Failed")
            response = MagicMock()
            response.status_code = 200
            response.json.return_value = {"data": {"data": {"key": "value"}}}
            return response

        mock_client = AsyncMock()
        mock_client.get.side_effect = mock_get
        mock_httpx_client.return_value = mock_client

        client = AsyncVaultClient(url="http://vault:8200", token="test-token")

        with patch('dotmac.platform.secrets.vault_client.logger') as mock_logger:
            result = await client.get_secrets(["success", "fail"])

        assert result["success"] == {"key": "value"}
        assert result["fail"] == {}
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_async_health_check(self, mock_httpx_client):
        """Test async health_check."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value = mock_client

        client = AsyncVaultClient(url="http://vault:8200", token="test-token")
        result = await client.health_check()

        assert result is True

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_async_aclose(self, mock_httpx_client):
        """Test async client cleanup."""
        mock_client = AsyncMock()
        mock_httpx_client.return_value = mock_client

        client = AsyncVaultClient(url="http://vault:8200", token="test-token")
        await client.aclose()

        mock_client.aclose.assert_called_once()
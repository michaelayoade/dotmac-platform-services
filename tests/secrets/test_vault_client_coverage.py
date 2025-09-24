"""Comprehensive tests to improve vault_client.py coverage."""

import pytest
from unittest.mock import patch, MagicMock, Mock
import httpx
import json

from dotmac.platform.secrets.vault_client import (
    VaultClient,
    AsyncVaultClient,
    VaultError,
    VaultAuthenticationError,
)


class TestVaultClientCoverage:
    """Test VaultClient missing coverage areas."""

    def test_vault_client_init_without_namespace(self):
        """Test VaultClient initialization without namespace."""
        client = VaultClient(url="http://vault:8200", token="test-token")

        assert client.url == "http://vault:8200"
        assert client.token == "test-token"
        assert client.namespace is None
        assert client.mount_path == "secret"
        assert client.kv_version == 2

    @patch("httpx.Client")
    def test_vault_client_headers_without_namespace(self, mock_httpx_client):
        """Test VaultClient headers when no namespace provided."""
        mock_client = MagicMock()
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200", token="test-token")

        # Check headers were set correctly without namespace
        call_kwargs = mock_httpx_client.call_args[1]
        headers = call_kwargs["headers"]
        assert headers["X-Vault-Token"] == "test-token"
        assert "X-Vault-Namespace" not in headers

    @patch("httpx.Client")
    def test_get_secret_kv_v1_path(self, mock_httpx_client):
        """Test get_secret with KV v1 engine (line 116)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"key1": "value1", "key2": "value2"}
        }

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200", token="test-token", kv_version=1)
        result = client.get_secret("test/path")

        assert result == {"key1": "value1", "key2": "value2"}
        mock_client.get.assert_called_once_with("/v1/secret/test/path")

    @patch("httpx.Client")
    def test_get_secret_http_error(self, mock_httpx_client):
        """Test get_secret with HTTP error (line 119)."""
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.HTTPError("Network error")
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200", token="test-token")

        with pytest.raises(VaultError, match="Failed to retrieve secret from test/path"):
            client.get_secret("test/path")

    @patch("httpx.Client")
    def test_get_secrets_with_error(self, mock_httpx_client):
        """Test get_secrets with one path failing (lines 135-137)."""
        def side_effect(path):
            if path == "/v1/secret/data/test/fail":
                raise httpx.HTTPError("Network error")
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {"data": {"key": "value"}}
            }
            return mock_response

        mock_client = MagicMock()
        mock_client.get.side_effect = side_effect
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200", token="test-token")

        with patch('dotmac.platform.secrets.vault_client.logger') as mock_logger:
            result = client.get_secrets(["test/success", "test/fail"])

        assert "test/success" in result
        assert "test/fail" in result
        assert result["test/fail"] == {}
        mock_logger.error.assert_called()

    @patch("httpx.Client")
    def test_put_secret_kv_v1(self, mock_httpx_client):
        """Test put_secret with KV v1 engine."""
        mock_response = MagicMock()
        mock_response.status_code = 204

        mock_client = MagicMock()
        mock_client.put.return_value = mock_response
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200", token="test-token", kv_version=1)
        client.put_secret("test/path", {"key": "value"})

        expected_url = "/v1/secret/test/path"
        mock_client.put.assert_called_once()
        call_args = mock_client.put.call_args
        assert call_args[0][0] == expected_url

    @patch("httpx.Client")
    def test_put_secret_http_error(self, mock_httpx_client):
        """Test put_secret with HTTP error."""
        mock_client = MagicMock()
        mock_client.put.side_effect = httpx.HTTPError("Network error")
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200", token="test-token")

        with pytest.raises(VaultError, match="Failed to store secret at test/path"):
            client.put_secret("test/path", {"key": "value"})

    @patch("httpx.Client")
    def test_delete_secret_kv_v1(self, mock_httpx_client):
        """Test delete_secret with KV v1 engine."""
        mock_response = MagicMock()
        mock_response.status_code = 204

        mock_client = MagicMock()
        mock_client.delete.return_value = mock_response
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200", token="test-token", kv_version=1)
        client.delete_secret("test/path")

        expected_url = "/v1/secret/test/path"
        mock_client.delete.assert_called_once_with(expected_url)

    @patch("httpx.Client")
    def test_delete_secret_http_error(self, mock_httpx_client):
        """Test delete_secret with HTTP error."""
        mock_client = MagicMock()
        mock_client.delete.side_effect = httpx.HTTPError("Network error")
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200", token="test-token")

        with pytest.raises(VaultError, match="Failed to delete secret at test/path"):
            client.delete_secret("test/path")

    @patch("httpx.Client")
    def test_list_secrets_kv_v1(self, mock_httpx_client):
        """Test list_secrets with KV v1 engine."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"keys": ["secret1", "secret2/"]}
        }

        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200", token="test-token", kv_version=1)
        result = client.list_secrets("test/path")

        assert result == ["secret1", "secret2/"]
        expected_url = "/v1/secret/test/path"
        mock_client.request.assert_called_once_with(
            "LIST", expected_url, params={"list": "true"}
        )

    @patch("httpx.Client")
    def test_list_secrets_http_error(self, mock_httpx_client):
        """Test list_secrets with HTTP error."""
        mock_client = MagicMock()
        mock_client.request.side_effect = httpx.HTTPError("Network error")
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200", token="test-token")

        with pytest.raises(VaultError, match="Failed to list secrets at test/path"):
            client.list_secrets("test/path")

    @patch("httpx.Client")
    def test_health_check_unhealthy(self, mock_httpx_client):
        """Test health_check when vault is unhealthy."""
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.json.return_value = {
            "initialized": True,
            "sealed": True,
            "standby": False
        }

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200", token="test-token")
        result = client.health_check()

        assert result is False

    @patch("httpx.Client")
    def test_health_check_http_error(self, mock_httpx_client):
        """Test health_check with HTTP error."""
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.HTTPError("Network error")
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200", token="test-token")
        result = client.health_check()

        assert result is False

    def test_get_secret_path_kv_v1(self):
        """Test _get_secret_path with KV v1."""
        client = VaultClient(url="http://vault:8200", token="test-token", kv_version=1)
        path = client._get_secret_path("test/path")
        assert path == "/v1/secret/test/path"

    def test_get_data_path_kv_v1(self):
        """Test _get_data_path with KV v1."""
        client = VaultClient(url="http://vault:8200", token="test-token", kv_version=1)
        path = client._get_data_path("test/path")
        assert path == "/v1/secret/test/path"


class TestAsyncVaultClientCoverage:
    """Test AsyncVaultClient missing coverage areas."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_async_get_secret_kv_v1(self, mock_httpx_client):
        """Test async get_secret with KV v1 engine."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"key1": "value1", "key2": "value2"}
        }

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value = mock_client

        client = AsyncVaultClient(url="http://vault:8200", token="test-token", kv_version=1)
        result = await client.get_secret("test/path")

        assert result == {"key1": "value1", "key2": "value2"}

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_async_get_secret_http_error(self, mock_httpx_client):
        """Test async get_secret with HTTP error."""
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.HTTPError("Network error")
        mock_httpx_client.return_value = mock_client

        client = AsyncVaultClient(url="http://vault:8200", token="test-token")

        with pytest.raises(VaultError, match="Failed to retrieve secret from test/path"):
            await client.get_secret("test/path")

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_async_get_secrets_with_error(self, mock_httpx_client):
        """Test async get_secrets with one path failing."""
        async def async_side_effect(path):
            if path == "/v1/secret/data/test/fail":
                raise httpx.HTTPError("Network error")
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {"data": {"key": "value"}}
            }
            return mock_response

        mock_client = MagicMock()
        mock_client.get.side_effect = async_side_effect
        mock_httpx_client.return_value = mock_client

        client = AsyncVaultClient(url="http://vault:8200", token="test-token")

        with patch('dotmac.platform.secrets.vault_client.logger') as mock_logger:
            result = await client.get_secrets(["test/success", "test/fail"])

        assert "test/success" in result
        assert "test/fail" in result
        assert result["test/fail"] == {}
        mock_logger.error.assert_called()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_async_put_secret_http_error(self, mock_httpx_client):
        """Test async put_secret with HTTP error."""
        mock_client = MagicMock()
        mock_client.put.side_effect = httpx.HTTPError("Network error")
        mock_httpx_client.return_value = mock_client

        client = AsyncVaultClient(url="http://vault:8200", token="test-token")

        with pytest.raises(VaultError, match="Failed to store secret at test/path"):
            await client.put_secret("test/path", {"key": "value"})

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_async_delete_secret_http_error(self, mock_httpx_client):
        """Test async delete_secret with HTTP error."""
        mock_client = MagicMock()
        mock_client.delete.side_effect = httpx.HTTPError("Network error")
        mock_httpx_client.return_value = mock_client

        client = AsyncVaultClient(url="http://vault:8200", token="test-token")

        with pytest.raises(VaultError, match="Failed to delete secret at test/path"):
            await client.delete_secret("test/path")

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_async_list_secrets_http_error(self, mock_httpx_client):
        """Test async list_secrets with HTTP error."""
        mock_client = MagicMock()
        mock_client.request.side_effect = httpx.HTTPError("Network error")
        mock_httpx_client.return_value = mock_client

        client = AsyncVaultClient(url="http://vault:8200", token="test-token")

        with pytest.raises(VaultError, match="Failed to list secrets at test/path"):
            await client.list_secrets("test/path")

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_async_health_check_unhealthy(self, mock_httpx_client):
        """Test async health_check when vault is unhealthy."""
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.json.return_value = {
            "initialized": True,
            "sealed": True,
            "standby": False
        }

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value = mock_client

        client = AsyncVaultClient(url="http://vault:8200", token="test-token")
        result = await client.health_check()

        assert result is False

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_async_health_check_http_error(self, mock_httpx_client):
        """Test async health_check with HTTP error."""
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.HTTPError("Network error")
        mock_httpx_client.return_value = mock_client

        client = AsyncVaultClient(url="http://vault:8200", token="test-token")
        result = await client.health_check()

        assert result is False


class TestVaultExceptions:
    """Test Vault exception classes."""

    def test_vault_error(self):
        """Test VaultError exception."""
        error = VaultError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_vault_authentication_error(self):
        """Test VaultAuthenticationError exception."""
        error = VaultAuthenticationError("Auth failed")
        assert str(error) == "Auth failed"
        assert isinstance(error, VaultError)
        assert isinstance(error, Exception)
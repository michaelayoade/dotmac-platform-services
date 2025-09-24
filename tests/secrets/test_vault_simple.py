"""Simple tests to improve vault_client coverage."""

import pytest
from unittest.mock import patch, MagicMock
import httpx
from dotmac.platform.secrets.vault_client import VaultClient, VaultError


class TestVaultClientSimpleCoverage:
    """Test VaultClient missing coverage areas simply."""

    @patch("httpx.Client")
    def test_get_secret_kv_v1_response(self, mock_httpx_client):
        """Test get_secret with KV v1 response format (line 116)."""
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

        # For KV v1, should return data directly without nested "data"
        assert result == {"key1": "value1", "key2": "value2"}

    @patch("httpx.Client")
    def test_get_secret_http_error_handling(self, mock_httpx_client):
        """Test get_secret HTTP error handling (line 119)."""
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.HTTPError("Connection failed")
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200", token="test-token")

        with pytest.raises(VaultError) as exc_info:
            client.get_secret("test/path")

        assert "Failed to retrieve secret from test/path" in str(exc_info.value)

    @patch("httpx.Client")
    def test_get_secrets_with_error_path(self, mock_httpx_client):
        """Test get_secrets when one path fails (lines 135-137)."""
        call_count = 0

        def mock_get(path):
            nonlocal call_count
            call_count += 1
            if "fail" in path:
                raise httpx.HTTPError("Network error")

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {"data": {"key": "value"}}
            }
            return mock_response

        mock_client = MagicMock()
        mock_client.get.side_effect = mock_get
        mock_httpx_client.return_value = mock_client

        client = VaultClient(url="http://vault:8200", token="test-token")

        with patch('dotmac.platform.secrets.vault_client.logger') as mock_logger:
            result = client.get_secrets(["test/success", "test/fail"])

        # Should log error for failed path
        mock_logger.error.assert_called()

        # Result should have both paths, with empty dict for failed one
        assert "test/success" in result
        assert "test/fail" in result
        assert result["test/fail"] == {}

    def test_vault_client_init_without_namespace(self):
        """Test VaultClient initialization without namespace."""
        client = VaultClient(url="http://vault:8200", token="test-token")
        assert client.namespace is None
        assert client.url == "http://vault:8200"
        assert client.token == "test-token"
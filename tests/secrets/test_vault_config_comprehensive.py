"""
Comprehensive tests for the vault configuration module.
"""

import os
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pydantic import ValidationError

from dotmac.platform.secrets.vault_config import (
    VaultConnectionConfig,
    get_vault_config_from_env,
    get_vault_config_from_settings,
    get_vault_config,
    VaultConnectionManager,
    get_vault_connection_manager,
    get_vault_client,
    get_async_vault_client,
    check_vault_health,
)


class TestVaultConnectionConfig:
    """Test the VaultConnectionConfig model."""

    def test_vault_config_defaults(self):
        """Test VaultConnectionConfig with defaults."""
        config = VaultConnectionConfig(url="http://vault:8200")

        assert config.url == "http://vault:8200"
        assert config.token is None
        assert config.namespace is None
        assert config.mount_path == "secret"
        assert config.kv_version == 2
        assert config.timeout == 30.0
        assert config.verify_ssl is True
        assert config.role_id is None
        assert config.secret_id is None
        assert config.kubernetes_role is None

    def test_vault_config_all_fields(self):
        """Test VaultConnectionConfig with all fields set."""
        config = VaultConnectionConfig(
            url="https://vault.example.com:8200",
            token="test-token",
            namespace="dev",
            mount_path="kv",
            kv_version=1,
            timeout=60.0,
            verify_ssl=False,
            role_id="role123",
            secret_id="secret456",
            kubernetes_role="k8s-role"
        )

        assert config.url == "https://vault.example.com:8200"
        assert config.token == "test-token"
        assert config.namespace == "dev"
        assert config.mount_path == "kv"
        assert config.kv_version == 1
        assert config.timeout == 60.0
        assert config.verify_ssl is False
        assert config.role_id == "role123"
        assert config.secret_id == "secret456"
        assert config.kubernetes_role == "k8s-role"

    def test_vault_config_validation_error(self):
        """Test VaultConnectionConfig validation errors."""
        with pytest.raises(ValidationError):
            VaultConnectionConfig()  # Missing required url field

    def test_vault_config_kv_version_validation(self):
        """Test VaultConnectionConfig KV version field."""
        # Valid versions
        config1 = VaultConnectionConfig(url="http://vault:8200", kv_version=1)
        config2 = VaultConnectionConfig(url="http://vault:8200", kv_version=2)

        assert config1.kv_version == 1
        assert config2.kv_version == 2


class TestGetVaultConfigFromEnv:
    """Test getting vault config from environment variables."""

    def test_get_vault_config_from_env_defaults(self):
        """Test getting config from env with default values."""
        with patch.dict(os.environ, {}, clear=True):
            config = get_vault_config_from_env()

            assert config.url == "http://localhost:8200"
            assert config.token is None
            assert config.namespace is None
            assert config.mount_path == "secret"
            assert config.kv_version == 2
            assert config.verify_ssl is True

    def test_get_vault_config_from_env_all_set(self):
        """Test getting config from env with all variables set."""
        env_vars = {
            "VAULT_ADDR": "https://vault.prod.com:8200",
            "VAULT_TOKEN": "prod-token",
            "VAULT_NAMESPACE": "production",
            "VAULT_MOUNT_PATH": "kv-v2",
            "VAULT_KV_VERSION": "1",
            "VAULT_SKIP_VERIFY": "1",
            "VAULT_ROLE_ID": "app-role-id",
            "VAULT_SECRET_ID": "app-secret-id",
            "VAULT_KUBERNETES_ROLE": "k8s-app-role"
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = get_vault_config_from_env()

            assert config.url == "https://vault.prod.com:8200"
            assert config.token == "prod-token"
            assert config.namespace == "production"
            assert config.mount_path == "kv-v2"
            assert config.kv_version == 1
            assert config.verify_ssl is False  # VAULT_SKIP_VERIFY inverts this
            assert config.role_id == "app-role-id"
            assert config.secret_id == "app-secret-id"
            assert config.kubernetes_role == "k8s-app-role"

    def test_get_vault_config_skip_verify_variations(self):
        """Test VAULT_SKIP_VERIFY environment variable variations."""
        # VAULT_SKIP_VERIFY not set -> verify_ssl = True
        with patch.dict(os.environ, {}, clear=True):
            config = get_vault_config_from_env()
            assert config.verify_ssl is True

        # VAULT_SKIP_VERIFY = "1" -> verify_ssl = False
        with patch.dict(os.environ, {"VAULT_SKIP_VERIFY": "1"}, clear=True):
            config = get_vault_config_from_env()
            assert config.verify_ssl is False

        # VAULT_SKIP_VERIFY = "true" -> verify_ssl = False
        with patch.dict(os.environ, {"VAULT_SKIP_VERIFY": "true"}, clear=True):
            config = get_vault_config_from_env()
            assert config.verify_ssl is False

        # VAULT_SKIP_VERIFY = "" -> verify_ssl = True
        with patch.dict(os.environ, {"VAULT_SKIP_VERIFY": ""}, clear=True):
            config = get_vault_config_from_env()
            assert config.verify_ssl is True

    def test_get_vault_config_kv_version_env(self):
        """Test KV version from environment."""
        with patch.dict(os.environ, {"VAULT_KV_VERSION": "1"}, clear=True):
            config = get_vault_config_from_env()
            assert config.kv_version == 1

        with patch.dict(os.environ, {"VAULT_KV_VERSION": "2"}, clear=True):
            config = get_vault_config_from_env()
            assert config.kv_version == 2


class TestGetVaultConfigFromSettings:
    """Test getting vault config from platform settings."""

    def test_get_vault_config_from_settings_success(self):
        """Test getting config from settings when vault is enabled."""
        mock_settings = MagicMock()
        mock_settings.vault.enabled = True
        mock_settings.vault.url = "http://settings-vault:8200"
        mock_settings.vault.token = "settings-token"
        mock_settings.vault.namespace = "settings-ns"
        mock_settings.vault.mount_path = "settings-mount"
        mock_settings.vault.kv_version = 1

        with patch("dotmac.platform.secrets.vault_config.get_settings", return_value=mock_settings):
            config = get_vault_config_from_settings()

            assert config.url == "http://settings-vault:8200"
            assert config.token == "settings-token"
            assert config.namespace == "settings-ns"
            assert config.mount_path == "settings-mount"
            assert config.kv_version == 1

    def test_get_vault_config_from_settings_disabled(self):
        """Test getting config from settings when vault is disabled."""
        mock_settings = MagicMock()
        mock_settings.vault.enabled = False

        with patch("dotmac.platform.secrets.vault_config.get_settings", return_value=mock_settings):
            with pytest.raises(ValueError) as exc_info:
                get_vault_config_from_settings()

            assert "Vault is not enabled in settings" in str(exc_info.value)


class TestGetVaultConfig:
    """Test the main get_vault_config function."""

    def test_get_vault_config_priority_env(self):
        """Test config priority: environment variables first."""
        mock_settings = MagicMock()
        mock_settings.vault.enabled = True

        with patch.dict(os.environ, {"VAULT_ADDR": "http://env-vault:8200"}, clear=True):
            with patch("dotmac.platform.secrets.vault_config.get_settings", return_value=mock_settings):
                with patch("dotmac.platform.secrets.vault_config.logger") as mock_logger:
                    config = get_vault_config()

                    assert config.url == "http://env-vault:8200"
                    mock_logger.info.assert_called_with("Using Vault configuration from environment")

    def test_get_vault_config_priority_settings(self):
        """Test config priority: settings when no env vars."""
        mock_settings = MagicMock()
        mock_settings.vault.enabled = True
        mock_settings.vault.url = "http://settings-vault:8200"
        mock_settings.vault.token = "settings-token"
        mock_settings.vault.namespace = None
        mock_settings.vault.mount_path = "secret"
        mock_settings.vault.kv_version = 2

        with patch.dict(os.environ, {}, clear=True):
            with patch("dotmac.platform.secrets.vault_config.get_settings", return_value=mock_settings):
                with patch("dotmac.platform.secrets.vault_config.logger") as mock_logger:
                    config = get_vault_config()

                    assert config.url == "http://settings-vault:8200"
                    mock_logger.info.assert_called_with("Using Vault configuration from settings")

    def test_get_vault_config_fallback_default(self):
        """Test config fallback to defaults."""
        mock_settings = MagicMock()
        mock_settings.vault.enabled = False

        with patch.dict(os.environ, {}, clear=True):
            with patch("dotmac.platform.secrets.vault_config.get_settings", return_value=mock_settings):
                with patch("dotmac.platform.secrets.vault_config.logger") as mock_logger:
                    config = get_vault_config()

                    assert config.url == "http://localhost:8200"
                    assert config.token == "root-token"
                    assert config.mount_path == "secret"
                    assert config.kv_version == 2
                    mock_logger.warning.assert_called_with("Using default Vault configuration (development mode)")


class TestVaultConnectionManager:
    """Test the VaultConnectionManager class."""

    def test_vault_manager_init_default(self):
        """Test VaultConnectionManager initialization with default config."""
        with patch("dotmac.platform.secrets.vault_config.get_vault_config") as mock_get_config:
            mock_config = MagicMock()
            mock_get_config.return_value = mock_config

            manager = VaultConnectionManager()

            assert manager.config == mock_config
            assert manager._client is None
            assert manager._async_client is None

    def test_vault_manager_init_custom_config(self):
        """Test VaultConnectionManager initialization with custom config."""
        custom_config = VaultConnectionConfig(url="http://custom:8200")

        manager = VaultConnectionManager(config=custom_config)

        assert manager.config == custom_config
        assert manager._client is None
        assert manager._async_client is None

    def test_get_sync_client_first_time(self):
        """Test getting sync client for the first time."""
        config = VaultConnectionConfig(
            url="http://vault:8200",
            token="test-token",
            namespace="test-ns",
            mount_path="secret",
            kv_version=2,
            timeout=30.0
        )

        with patch("dotmac.platform.secrets.vault_config.VaultClient") as mock_vault_client:
            mock_client_instance = MagicMock()
            mock_vault_client.return_value = mock_client_instance

            manager = VaultConnectionManager(config=config)
            result = manager.get_sync_client()

            assert result == mock_client_instance
            assert manager._client == mock_client_instance

            mock_vault_client.assert_called_once_with(
                url="http://vault:8200",
                token="test-token",
                namespace="test-ns",
                mount_path="secret",
                kv_version=2,
                timeout=30.0
            )

    def test_get_sync_client_cached(self):
        """Test getting sync client returns cached instance."""
        config = VaultConnectionConfig(url="http://vault:8200")
        manager = VaultConnectionManager(config=config)

        with patch("dotmac.platform.secrets.vault_config.VaultClient") as mock_vault_client:
            mock_client_instance = MagicMock()
            mock_vault_client.return_value = mock_client_instance

            # First call
            result1 = manager.get_sync_client()
            # Second call
            result2 = manager.get_sync_client()

            assert result1 == result2 == mock_client_instance
            mock_vault_client.assert_called_once()  # Only called once due to caching

    def test_get_async_client_first_time(self):
        """Test getting async client for the first time."""
        config = VaultConnectionConfig(
            url="http://vault:8200",
            token="test-token"
        )

        with patch("dotmac.platform.secrets.vault_config.AsyncVaultClient") as mock_async_client:
            mock_client_instance = MagicMock()
            mock_async_client.return_value = mock_client_instance

            manager = VaultConnectionManager(config=config)
            result = manager.get_async_client()

            assert result == mock_client_instance
            assert manager._async_client == mock_client_instance

    def test_get_sync_client_with_approle_auth(self):
        """Test sync client creation with AppRole authentication."""
        config = VaultConnectionConfig(
            url="http://vault:8200",
            role_id="test-role-id",
            secret_id="test-secret-id"
        )

        with patch("dotmac.platform.secrets.vault_config.VaultClient") as mock_vault_client:
            mock_client_instance = MagicMock()
            mock_vault_client.return_value = mock_client_instance

            manager = VaultConnectionManager(config=config)

            with patch.object(manager, '_authenticate_approle') as mock_auth:
                result = manager.get_sync_client()

                assert result == mock_client_instance
                mock_auth.assert_called_once()

    def test_get_sync_client_with_kubernetes_auth(self):
        """Test sync client creation with Kubernetes authentication."""
        config = VaultConnectionConfig(
            url="http://vault:8200",
            kubernetes_role="test-k8s-role"
        )

        with patch("dotmac.platform.secrets.vault_config.VaultClient") as mock_vault_client:
            mock_client_instance = MagicMock()
            mock_vault_client.return_value = mock_client_instance

            manager = VaultConnectionManager(config=config)

            with patch.object(manager, '_authenticate_kubernetes') as mock_auth:
                result = manager.get_sync_client()

                assert result == mock_client_instance
                mock_auth.assert_called_once()

    def test_authenticate_approle_success(self):
        """Test successful AppRole authentication."""
        config = VaultConnectionConfig(
            url="http://vault:8200",
            role_id="test-role-id",
            secret_id="test-secret-id"
        )

        manager = VaultConnectionManager(config=config)
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "auth": {"client_token": "new-token"}
        }
        mock_client.client.post.return_value = mock_response
        manager._client = mock_client

        with patch("dotmac.platform.secrets.vault_config.logger") as mock_logger:
            manager._authenticate_approle()

            mock_client.client.post.assert_called_once_with(
                "/v1/auth/approle/login",
                json={
                    "role_id": "test-role-id",
                    "secret_id": "test-secret-id"
                }
            )
            mock_response.raise_for_status.assert_called_once()

            assert mock_client.token == "new-token"
            # Check that the header was set (mock object)
            mock_client.client.headers.__setitem__.assert_called_with("X-Vault-Token", "new-token")
            mock_logger.info.assert_called_with("Successfully authenticated with AppRole")

    def test_authenticate_approle_failure(self):
        """Test AppRole authentication failure."""
        config = VaultConnectionConfig(
            url="http://vault:8200",
            role_id="test-role-id",
            secret_id="test-secret-id"
        )

        manager = VaultConnectionManager(config=config)
        mock_client = MagicMock()
        mock_client.client.post.side_effect = Exception("Auth failed")
        manager._client = mock_client

        with patch("dotmac.platform.secrets.vault_config.logger") as mock_logger:
            with pytest.raises(Exception):
                manager._authenticate_approle()

            mock_logger.error.assert_called_once()

    def test_authenticate_approle_no_client(self):
        """Test AppRole authentication with no client."""
        config = VaultConnectionConfig(url="http://vault:8200")
        manager = VaultConnectionManager(config=config)

        # Should return early if no client
        manager._authenticate_approle()
        # No assertions needed, just testing it doesn't crash

    def test_authenticate_kubernetes_success(self):
        """Test successful Kubernetes authentication."""
        config = VaultConnectionConfig(
            url="http://vault:8200",
            kubernetes_role="test-k8s-role"
        )

        manager = VaultConnectionManager(config=config)
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "auth": {"client_token": "k8s-token"}
        }
        mock_client.client.post.return_value = mock_response
        manager._client = mock_client

        mock_file_content = "jwt-token-content"

        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            with patch("dotmac.platform.secrets.vault_config.logger") as mock_logger:
                manager._authenticate_kubernetes()

                mock_client.client.post.assert_called_once_with(
                    "/v1/auth/kubernetes/login",
                    json={
                        "role": "test-k8s-role",
                        "jwt": "jwt-token-content"
                    }
                )

                assert mock_client.token == "k8s-token"
                mock_client.client.headers.__setitem__.assert_called_with("X-Vault-Token", "k8s-token")
                mock_logger.info.assert_called_with("Successfully authenticated with Kubernetes")

    def test_authenticate_kubernetes_file_not_found(self):
        """Test Kubernetes authentication with missing service account token."""
        config = VaultConnectionConfig(
            url="http://vault:8200",
            kubernetes_role="test-k8s-role"
        )

        manager = VaultConnectionManager(config=config)
        mock_client = MagicMock()
        manager._client = mock_client

        with patch("builtins.open", side_effect=FileNotFoundError("Token file not found")):
            with patch("dotmac.platform.secrets.vault_config.logger") as mock_logger:
                with pytest.raises(FileNotFoundError):
                    manager._authenticate_kubernetes()

                mock_logger.error.assert_called_with("Kubernetes service account token not found")

    def test_authenticate_kubernetes_failure(self):
        """Test Kubernetes authentication failure."""
        config = VaultConnectionConfig(
            url="http://vault:8200",
            kubernetes_role="test-k8s-role"
        )

        manager = VaultConnectionManager(config=config)
        mock_client = MagicMock()
        mock_client.client.post.side_effect = Exception("K8s auth failed")
        manager._client = mock_client

        with patch("builtins.open", mock_open(read_data="jwt-token")):
            with patch("dotmac.platform.secrets.vault_config.logger") as mock_logger:
                with pytest.raises(Exception):
                    manager._authenticate_kubernetes()

                mock_logger.error.assert_called_with(
                    "Failed to authenticate with Kubernetes",
                    error="K8s auth failed"
                )

    def test_close_clients(self):
        """Test closing client connections."""
        manager = VaultConnectionManager()

        # Mock clients
        mock_sync_client = MagicMock()
        mock_async_client = MagicMock()
        manager._client = mock_sync_client
        manager._async_client = mock_async_client

        manager.close()

        mock_sync_client.close.assert_called_once()
        mock_async_client.close.assert_called_once()
        assert manager._client is None
        assert manager._async_client is None

    def test_close_no_clients(self):
        """Test closing when no clients exist."""
        manager = VaultConnectionManager()

        # Should not raise any exceptions
        manager.close()


class TestGlobalConnectionManager:
    """Test global connection manager functions."""

    def test_get_vault_connection_manager_singleton(self):
        """Test that get_vault_connection_manager returns singleton."""
        # Clear the global variable
        with patch("dotmac.platform.secrets.vault_config._connection_manager", None):
            manager1 = get_vault_connection_manager()
            manager2 = get_vault_connection_manager()

            assert manager1 is manager2
            assert isinstance(manager1, VaultConnectionManager)

    @patch("dotmac.platform.secrets.vault_config.get_vault_connection_manager")
    def test_get_vault_client_function(self, mock_get_manager):
        """Test get_vault_client function."""
        mock_manager = MagicMock()
        mock_client = MagicMock()
        mock_manager.get_sync_client.return_value = mock_client
        mock_get_manager.return_value = mock_manager

        result = get_vault_client()

        assert result == mock_client
        mock_manager.get_sync_client.assert_called_once()

    @patch("dotmac.platform.secrets.vault_config.get_vault_connection_manager")
    def test_get_async_vault_client_function(self, mock_get_manager):
        """Test get_async_vault_client function."""
        mock_manager = MagicMock()
        mock_client = MagicMock()
        mock_manager.get_async_client.return_value = mock_client
        mock_get_manager.return_value = mock_manager

        result = get_async_vault_client()

        assert result == mock_client
        mock_manager.get_async_client.assert_called_once()


class TestVaultHealthCheck:
    """Test the vault health check function."""

    @patch("dotmac.platform.secrets.vault_config.get_vault_client")
    def test_check_vault_health_success(self, mock_get_client):
        """Test successful vault health check."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "sealed": False,
            "initialized": True,
            "version": "1.8.0"
        }
        mock_client.client.get.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = check_vault_health()

        assert result["healthy"] is True
        assert result["status_code"] == 200
        assert result["sealed"] is False
        assert result["initialized"] is True
        assert result["version"] == "1.8.0"

        mock_client.client.get.assert_called_once_with("/v1/sys/health")

    @patch("dotmac.platform.secrets.vault_config.get_vault_client")
    def test_check_vault_health_failure(self, mock_get_client):
        """Test vault health check failure."""
        mock_get_client.side_effect = Exception("Connection failed")

        with patch("dotmac.platform.secrets.vault_config.logger") as mock_logger:
            result = check_vault_health()

            assert result["healthy"] is False
            assert result["error"] == "Connection failed"

            mock_logger.error.assert_called_once()

    @patch("dotmac.platform.secrets.vault_config.get_vault_client")
    def test_check_vault_health_unhealthy_status(self, mock_get_client):
        """Test vault health check with unhealthy status code."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 503  # Service unavailable
        mock_response.json.return_value = {
            "sealed": True,
            "initialized": True,
            "version": "1.8.0"
        }
        mock_client.client.get.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = check_vault_health()

        assert result["healthy"] is False
        assert result["status_code"] == 503
        assert result["sealed"] is True
        assert result["initialized"] is True
        assert result["version"] == "1.8.0"
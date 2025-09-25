"""Comprehensive tests to improve vault_config.py coverage."""

import pytest
from unittest.mock import patch, MagicMock, Mock
from dotmac.platform.secrets.vault_config import (
    VaultConnectionManager,
    get_vault_client,
    get_async_vault_client,
    get_vault_connection_manager
)


class TestVaultConnectionManagerCoverage:
    """Test VaultConnectionManager missing coverage areas."""

    def test_vault_connection_manager_singleton(self):
        """Test VaultConnectionManager singleton behavior via get_vault_connection_manager."""
        # Clear any existing global instance
        import dotmac.platform.secrets.vault_config as vault_config_module
        vault_config_module._connection_manager = None

        manager1 = get_vault_connection_manager()
        manager2 = get_vault_connection_manager()
        assert manager1 is manager2

        # Cleanup
        vault_config_module._connection_manager = None

    @patch('dotmac.platform.secrets.vault_config.VaultClient')
    def test_get_sync_client_with_error(self, mock_vault_client):
        """Test get_sync_client when VaultClient creation fails."""
        mock_vault_client.side_effect = Exception("Connection failed")

        manager = VaultConnectionManager()

        with pytest.raises(Exception, match="Connection failed"):
            manager.get_sync_client()

    @patch('dotmac.platform.secrets.vault_config.AsyncVaultClient')
    def test_get_async_client_with_error(self, mock_async_vault_client):
        """Test get_async_client when AsyncVaultClient creation fails."""
        mock_async_vault_client.side_effect = Exception("Connection failed")

        manager = VaultConnectionManager()

        with pytest.raises(Exception, match="Connection failed"):
            manager.get_async_client()

    @patch('dotmac.platform.secrets.vault_config.settings')
    @patch('dotmac.platform.secrets.vault_config.VaultClient')
    def test_get_sync_client_with_custom_settings(self, mock_vault_client, mock_settings):
        """Test get_sync_client with custom vault settings."""
        mock_settings.vault.url = "http://custom-vault:8200"
        mock_settings.vault.token = "custom-token"
        mock_settings.vault.namespace = "custom-ns"
        mock_settings.vault.mount_path = "custom-mount"
        mock_settings.vault.kv_version = 1
        mock_settings.vault.timeout = 60.0

        mock_client = MagicMock()
        mock_vault_client.return_value = mock_client

        manager = VaultConnectionManager()
        client = manager.get_sync_client()

        mock_vault_client.assert_called_once_with(
            url="http://custom-vault:8200",
            token="custom-token",
            namespace="custom-ns",
            mount_path="custom-mount",
            kv_version=1,
            timeout=60.0
        )
        assert client is mock_client

    @patch('dotmac.platform.secrets.vault_config.settings')
    @patch('dotmac.platform.secrets.vault_config.AsyncVaultClient')
    def test_get_async_client_with_custom_settings(self, mock_async_vault_client, mock_settings):
        """Test get_async_client with custom vault settings."""
        mock_settings.vault.url = "http://custom-vault:8200"
        mock_settings.vault.token = "custom-token"
        mock_settings.vault.namespace = "custom-ns"
        mock_settings.vault.mount_path = "custom-mount"
        mock_settings.vault.kv_version = 1
        mock_settings.vault.timeout = 60.0

        mock_client = MagicMock()
        mock_async_vault_client.return_value = mock_client

        manager = VaultConnectionManager()
        client = manager.get_async_client()

        mock_async_vault_client.assert_called_once_with(
            url="http://custom-vault:8200",
            token="custom-token",
            namespace="custom-ns",
            mount_path="custom-mount",
            kv_version=1,
            timeout=60.0
        )
        assert client is mock_client

    @patch('dotmac.platform.secrets.vault_config.settings')
    def test_get_sync_client_caching_behavior(self, mock_settings):
        """Test that get_sync_client properly caches clients."""
        mock_settings.vault.url = "http://vault:8200"
        mock_settings.vault.token = "test-token"
        mock_settings.vault.namespace = None
        mock_settings.vault.mount_path = "secret"
        mock_settings.vault.kv_version = 2
        mock_settings.vault.timeout = 30.0

        manager = VaultConnectionManager()

        with patch('dotmac.platform.secrets.vault_config.VaultClient') as mock_vault_client:
            mock_client = MagicMock()
            mock_vault_client.return_value = mock_client

            # First call should create client
            client1 = manager.get_sync_client()

            # Second call should return cached client
            client2 = manager.get_sync_client()

            # Should have been called only once
            mock_vault_client.assert_called_once()
            assert client1 is client2
            assert client1 is mock_client

    @patch('dotmac.platform.secrets.vault_config.settings')
    def test_get_async_client_caching_behavior(self, mock_settings):
        """Test that get_async_client properly caches clients."""
        mock_settings.vault.url = "http://vault:8200"
        mock_settings.vault.token = "test-token"
        mock_settings.vault.namespace = None
        mock_settings.vault.mount_path = "secret"
        mock_settings.vault.kv_version = 2
        mock_settings.vault.timeout = 30.0

        manager = VaultConnectionManager()

        with patch('dotmac.platform.secrets.vault_config.AsyncVaultClient') as mock_async_vault_client:
            mock_client = MagicMock()
            mock_async_vault_client.return_value = mock_client

            # First call should create client
            client1 = manager.get_async_client()

            # Second call should return cached client
            client2 = manager.get_async_client()

            # Should have been called only once
            mock_async_vault_client.assert_called_once()
            assert client1 is client2
            assert client1 is mock_client


class TestConvenienceFunctionsCoverage:
    """Test convenience functions missing coverage areas."""

    @patch('dotmac.platform.secrets.vault_config.settings')
    def test_get_vault_client_vault_disabled(self, mock_settings):
        """Test get_vault_client when vault is disabled (line 189)."""
        mock_settings.vault.enabled = False

        result = get_vault_client()
        assert result is None

    @patch('dotmac.platform.secrets.vault_config.settings')
    @patch('dotmac.platform.secrets.vault_config.VaultConnectionManager')
    def test_get_vault_client_vault_enabled(self, mock_manager_class, mock_settings):
        """Test get_vault_client when vault is enabled."""
        mock_settings.vault.enabled = True

        mock_manager = MagicMock()
        mock_client = MagicMock()
        mock_manager.get_sync_client.return_value = mock_client
        mock_manager_class.return_value = mock_manager

        result = get_vault_client()

        assert result is mock_client
        mock_manager.get_sync_client.assert_called_once()

    @patch('dotmac.platform.secrets.vault_config.settings')
    def test_get_async_vault_client_vault_disabled(self, mock_settings):
        """Test get_async_vault_client when vault is disabled."""
        mock_settings.vault.enabled = False

        result = get_async_vault_client()
        assert result is None

    @patch('dotmac.platform.secrets.vault_config.settings')
    @patch('dotmac.platform.secrets.vault_config.VaultConnectionManager')
    def test_get_async_vault_client_vault_enabled(self, mock_manager_class, mock_settings):
        """Test get_async_vault_client when vault is enabled."""
        mock_settings.vault.enabled = True

        mock_manager = MagicMock()
        mock_client = MagicMock()
        mock_manager.get_async_client.return_value = mock_client
        mock_manager_class.return_value = mock_manager

        result = get_async_vault_client()

        assert result is mock_client
        mock_manager.get_async_client.assert_called_once()

    @patch('dotmac.platform.secrets.vault_config.settings')
    @patch('dotmac.platform.secrets.vault_config.VaultConnectionManager')
    def test_get_vault_client_with_exception(self, mock_manager_class, mock_settings):
        """Test get_vault_client when manager raises exception."""
        mock_settings.vault.enabled = True

        mock_manager = MagicMock()
        mock_manager.get_sync_client.side_effect = Exception("Connection failed")
        mock_manager_class.return_value = mock_manager

        with pytest.raises(Exception, match="Connection failed"):
            get_vault_client()

    @patch('dotmac.platform.secrets.vault_config.settings')
    @patch('dotmac.platform.secrets.vault_config.VaultConnectionManager')
    def test_get_async_vault_client_with_exception(self, mock_manager_class, mock_settings):
        """Test get_async_vault_client when manager raises exception."""
        mock_settings.vault.enabled = True

        mock_manager = MagicMock()
        mock_manager.get_async_client.side_effect = Exception("Connection failed")
        mock_manager_class.return_value = mock_manager

        with pytest.raises(Exception, match="Connection failed"):
            get_async_vault_client()


class TestVaultConfigEdgeCases:
    """Test edge cases for vault configuration."""

    @patch('dotmac.platform.secrets.vault_config.settings')
    def test_manager_with_none_values(self, mock_settings):
        """Test VaultConnectionManager with None values in settings."""
        mock_settings.vault.url = None
        mock_settings.vault.token = None
        mock_settings.vault.namespace = None
        mock_settings.vault.mount_path = None
        mock_settings.vault.kv_version = None
        mock_settings.vault.timeout = None

        manager = VaultConnectionManager()

        with patch('dotmac.platform.secrets.vault_config.VaultClient') as mock_vault_client:
            mock_vault_client.return_value = MagicMock()

            manager.get_sync_client()

            # Verify None values are passed through
            call_args = mock_vault_client.call_args[1]
            assert call_args['url'] is None
            assert call_args['token'] is None
            assert call_args['namespace'] is None
            assert call_args['mount_path'] is None
            assert call_args['kv_version'] is None
            assert call_args['timeout'] is None

    def test_manager_reset_behavior(self):
        """Test that multiple get_vault_connection_manager calls return the same instance."""
        # Clear any existing global instance
        import dotmac.platform.secrets.vault_config as vault_config_module
        vault_config_module._connection_manager = None

        manager1 = get_vault_connection_manager()
        manager2 = get_vault_connection_manager()

        # They should be the same instance (singleton)
        assert manager1 is manager2

        # Setting attributes on one should affect the other
        manager1._sync_client = "test_client"
        assert manager2._sync_client == "test_client"

        # Cleanup
        vault_config_module._connection_manager = None
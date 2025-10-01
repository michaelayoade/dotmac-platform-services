"""Simple tests to improve factory.py coverage."""

import pytest
from unittest.mock import patch, MagicMock
from dotmac.platform.secrets.factory import (
    SecretsManagerFactory,
    create_secrets_manager,
    LocalSecretsManager
)


class TestSecretsManagerFactoryCoverage:
    """Test SecretsManagerFactory missing coverage areas."""

    @patch('dotmac.platform.secrets.factory.DependencyChecker')
    @patch('dotmac.platform.secrets.factory.settings')
    def test_auto_select_backend_vault_available(self, mock_settings, mock_checker):
        """Test _auto_select_backend when vault is available."""
        mock_settings.features.secrets_vault = True
        mock_checker.check_feature_dependency.return_value = True

        result = SecretsManagerFactory._auto_select_backend()
        assert result == "vault"

    @patch('dotmac.platform.secrets.factory.DependencyChecker')
    @patch('dotmac.platform.secrets.factory.settings')
    def test_auto_select_backend_vault_unavailable(self, mock_settings, mock_checker):
        """Test _auto_select_backend when vault is unavailable."""
        mock_settings.features.secrets_vault = False
        mock_checker.check_feature_dependency.return_value = False

        result = SecretsManagerFactory._auto_select_backend()
        assert result == "local"

    @patch('dotmac.platform.secrets.factory.DependencyChecker')
    @patch('dotmac.platform.secrets.factory.settings')
    def test_list_available_backends_vault_available(self, mock_settings, mock_checker):
        """Test list_available_backends when vault is available."""
        mock_settings.features.secrets_vault = True
        mock_checker.check_feature_dependency.return_value = True

        result = SecretsManagerFactory.list_available_backends()
        assert "local" in result
        assert "vault" in result

    @patch('dotmac.platform.secrets.factory.DependencyChecker')
    @patch('dotmac.platform.secrets.factory.settings')
    def test_list_available_backends_vault_unavailable(self, mock_settings, mock_checker):
        """Test list_available_backends when vault is unavailable."""
        mock_settings.features.secrets_vault = False

        result = SecretsManagerFactory.list_available_backends()
        assert result == ["local"]

    @patch.object(SecretsManagerFactory, 'create_secrets_manager')
    def test_create_secrets_manager_convenience_function(self, mock_create):
        """Test create_secrets_manager convenience function."""
        mock_manager = MagicMock()
        mock_create.return_value = mock_manager

        result = create_secrets_manager(backend="local", test_param="value")

        assert result is mock_manager
        mock_create.assert_called_once_with("local", test_param="value")


class TestLocalSecretsManagerCoverage:
    """Test LocalSecretsManager missing coverage areas."""

    def test_local_secrets_manager_init_default(self):
        """Test LocalSecretsManager with default secrets file."""
        manager = LocalSecretsManager()
        assert manager.secrets_file == ".env"
        assert manager._secrets == {}

    def test_local_secrets_manager_init_custom(self):
        """Test LocalSecretsManager with custom secrets file."""
        manager = LocalSecretsManager(secrets_file="/custom/path")
        assert manager.secrets_file == "/custom/path"

    def test_local_secrets_manager_get_secret_exists(self):
        """Test getting existing secret."""
        manager = LocalSecretsManager()
        manager._secrets["test/secret"] = {"key": "value"}

        result = manager.get_secret("test/secret")
        assert result == {"key": "value"}

    def test_local_secrets_manager_get_secret_not_exists(self):
        """Test getting non-existing secret."""
        manager = LocalSecretsManager()

        result = manager.get_secret("non/existent")
        assert result == {}

    def test_local_secrets_manager_set_secret(self):
        """Test setting a secret."""
        manager = LocalSecretsManager()
        data = {"password": "secret123"}

        manager.set_secret("test/path", data)

        assert manager._secrets["test/path"] == data

    def test_local_secrets_manager_health_check(self):
        """Test health check always returns True."""
        manager = LocalSecretsManager()
        assert manager.health_check() is True

    def test_local_secrets_manager_multiple_operations(self):
        """Test multiple operations on LocalSecretsManager."""
        manager = LocalSecretsManager()

        # Set multiple secrets
        manager.set_secret("secret1", {"key1": "value1"})
        manager.set_secret("secret2", {"key2": "value2"})

        # Get secrets
        assert manager.get_secret("secret1") == {"key1": "value1"}
        assert manager.get_secret("secret2") == {"key2": "value2"}
        assert manager.get_secret("secret3") == {}

        # Overwrite existing secret
        manager.set_secret("secret1", {"new_key": "new_value"})
        assert manager.get_secret("secret1") == {"new_key": "new_value"}
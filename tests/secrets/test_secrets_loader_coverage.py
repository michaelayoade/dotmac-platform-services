"""Comprehensive tests to improve secrets_loader.py coverage."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from dotmac.platform.secrets.secrets_loader import (
    get_nested_attr,
    load_secrets_from_vault
)
from dotmac.platform.secrets.vault_client import AsyncVaultClient
from dotmac.platform.settings import Settings


class TestGetNestedAttrCoverage:
    """Test get_nested_attr missing coverage areas."""

    def test_get_nested_attr_missing_no_default(self):
        """Test get_nested_attr with missing attribute and no default (line 80)."""
        obj = MagicMock()
        obj.existing = "value"
        # Don't set 'missing' attribute

        result = get_nested_attr(obj, "missing")
        assert result is None

    def test_get_nested_attr_nested_missing_no_default(self):
        """Test get_nested_attr with nested missing attribute and no default."""
        obj = MagicMock()
        obj.level1 = MagicMock()
        # Don't set level1.missing

        result = get_nested_attr(obj, "level1.missing")
        assert result is None

    def test_get_nested_attr_deep_missing_with_default(self):
        """Test get_nested_attr with deeply nested missing attribute."""
        obj = MagicMock()
        obj.level1 = MagicMock()
        obj.level1.level2 = MagicMock()
        # Don't set level1.level2.missing

        result = get_nested_attr(obj, "level1.level2.missing", "default_value")
        assert result == "default_value"

    def test_get_nested_attr_attribute_error_chain(self):
        """Test get_nested_attr when AttributeError occurs in chain."""
        class TestObj:
            def __init__(self):
                self.level1 = None

        obj = TestObj()
        result = get_nested_attr(obj, "level1.missing", "fallback")
        assert result == "fallback"


class TestLoadSecretsFromVaultCoverage:
    """Test load_secrets_from_vault missing coverage areas."""

    @pytest.mark.asyncio
    async def test_load_secrets_vault_disabled(self):
        """Test load_secrets_from_vault when vault is disabled (line 98, 102)."""
        mock_settings = MagicMock()
        mock_settings.vault.enabled = False

        with patch('dotmac.platform.secrets.secrets_loader.logger') as mock_logger:
            await load_secrets_from_vault(settings_obj=mock_settings)

        mock_logger.info.assert_called_with("Vault is disabled, using default settings values")

    @pytest.mark.asyncio
    async def test_load_secrets_no_settings_provided(self):
        """Test load_secrets_from_vault with default settings (line 98)."""
        with patch('dotmac.platform.secrets.secrets_loader.settings') as mock_global_settings:
            mock_global_settings.vault.enabled = False
            with patch('dotmac.platform.secrets.secrets_loader.logger') as mock_logger:
                await load_secrets_from_vault()

        mock_logger.info.assert_called_with("Vault is disabled, using default settings values")

    @pytest.mark.asyncio
    async def test_load_secrets_vault_client_creation_failure(self):
        """Test load_secrets_from_vault when client creation fails (line 112)."""
        mock_settings = MagicMock()
        mock_settings.vault.enabled = True
        mock_settings.vault.url = "http://vault:8200"
        mock_settings.vault.token = "test-token"

        with patch('dotmac.platform.secrets.secrets_loader.AsyncVaultClient') as mock_client_class:
            mock_client_class.side_effect = Exception("Connection failed")
            with patch('dotmac.platform.secrets.secrets_loader.logger') as mock_logger:
                await load_secrets_from_vault(settings_obj=mock_settings)

        mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_load_secrets_vault_client_cleanup_failure(self):
        """Test load_secrets_from_vault when client cleanup fails."""
        mock_settings = MagicMock()
        mock_settings.vault.enabled = True
        mock_settings.vault.url = "http://vault:8200"
        mock_settings.vault.token = "test-token"

        mock_client = AsyncMock()
        mock_client.get_secrets.return_value = {}
        mock_client.aclose.side_effect = Exception("Cleanup failed")

        with patch('dotmac.platform.secrets.secrets_loader.AsyncVaultClient') as mock_client_class:
            mock_client_class.return_value = mock_client
            with patch('dotmac.platform.secrets.secrets_loader.logger') as mock_logger:
                await load_secrets_from_vault(settings_obj=mock_settings, vault_client=mock_client)

        mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_load_secrets_with_custom_vault_client(self):
        """Test load_secrets_from_vault with provided vault client."""
        mock_settings = MagicMock()
        mock_settings.vault.enabled = True

        mock_vault_client = AsyncMock()
        mock_vault_client.get_secrets.return_value = {
            "secret/database": {"host": "db.example.com", "password": "secret123"},
            "secret/api": {"key": "api-key-123"}
        }

        # Mock the secret configuration
        with patch('dotmac.platform.secrets.secrets_loader.VAULT_SECRET_MAPPINGS', {
            "secret/database": [
                ("host", "database.host"),
                ("password", "database.password")
            ],
            "secret/api": [
                ("key", "api.key")
            ]
        }):
            await load_secrets_from_vault(settings_obj=mock_settings, vault_client=mock_vault_client)

        # Verify client was used
        mock_vault_client.get_secrets.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_secrets_missing_secret_data(self):
        """Test load_secrets_from_vault when secret data is missing."""
        mock_settings = MagicMock()
        mock_settings.vault.enabled = True

        mock_vault_client = AsyncMock()
        mock_vault_client.get_secrets.return_value = {
            "secret/missing": {}  # Empty secret data
        }

        # Mock the secret configuration
        with patch('dotmac.platform.secrets.secrets_loader.VAULT_SECRET_MAPPINGS', {
            "secret/missing": [
                ("missing_key", "settings.missing_value")
            ]
        }):
            with patch('dotmac.platform.secrets.secrets_loader.logger') as mock_logger:
                await load_secrets_from_vault(settings_obj=mock_settings, vault_client=mock_vault_client)

        mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_load_secrets_setattr_failure(self):
        """Test load_secrets_from_vault when setattr fails."""
        mock_settings = MagicMock()
        mock_settings.vault.enabled = True

        # Create a settings object that will fail on setattr
        class FailingSettings:
            def __setattr__(self, name, value):
                if name == "failing_attr":
                    raise AttributeError("Cannot set attribute")
                super().__setattr__(name, value)

        failing_settings = FailingSettings()

        mock_vault_client = AsyncMock()
        mock_vault_client.get_secrets.return_value = {
            "secret/test": {"key": "value"}
        }

        # Mock the secret configuration
        with patch('dotmac.platform.secrets.secrets_loader.VAULT_SECRET_MAPPINGS', {
            "secret/test": [
                ("key", "failing_attr")
            ]
        }):
            with patch('dotmac.platform.secrets.secrets_loader.logger') as mock_logger:
                await load_secrets_from_vault(settings_obj=failing_settings, vault_client=mock_vault_client)

        mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_load_secrets_complex_nested_path(self):
        """Test load_secrets_from_vault with complex nested setting paths."""
        mock_settings = MagicMock()
        mock_settings.vault.enabled = True
        mock_settings.database = MagicMock()
        mock_settings.database.connection = MagicMock()

        mock_vault_client = AsyncMock()
        mock_vault_client.get_secrets.return_value = {
            "secret/database": {"password": "complex_password_123"}
        }

        # Mock the secret configuration with nested path
        with patch('dotmac.platform.secrets.secrets_loader.VAULT_SECRET_MAPPINGS', {
            "secret/database": [
                ("password", "database.connection.password")
            ]
        }):
            await load_secrets_from_vault(settings_obj=mock_settings, vault_client=mock_vault_client)

        # Verify the nested attribute was set
        assert mock_settings.database.connection.password == "complex_password_123"

    @pytest.mark.asyncio
    async def test_load_secrets_get_secrets_exception(self):
        """Test load_secrets_from_vault when get_secrets raises exception."""
        mock_settings = MagicMock()
        mock_settings.vault.enabled = True

        mock_vault_client = AsyncMock()
        mock_vault_client.get_secrets.side_effect = Exception("Vault connection failed")

        with patch('dotmac.platform.secrets.secrets_loader.logger') as mock_logger:
            await load_secrets_from_vault(settings_obj=mock_settings, vault_client=mock_vault_client)

        mock_logger.error.assert_called_with(
            "Failed to load secrets from Vault: Vault connection failed"
        )

    @pytest.mark.asyncio
    async def test_load_secrets_vault_mappings_missing(self):
        """Test load_secrets_from_vault when VAULT_SECRET_MAPPINGS is not available."""
        mock_settings = MagicMock()
        mock_settings.vault.enabled = True

        mock_vault_client = AsyncMock()
        mock_vault_client.get_secrets.return_value = {}

        # Mock missing VAULT_SECRET_MAPPINGS
        with patch('dotmac.platform.secrets.secrets_loader.VAULT_SECRET_MAPPINGS', None):
            with patch('dotmac.platform.secrets.secrets_loader.logger') as mock_logger:
                await load_secrets_from_vault(settings_obj=mock_settings, vault_client=mock_vault_client)

        # Should handle gracefully when mappings are not available
        mock_vault_client.get_secrets.assert_called_once_with([])


class TestSecretsLoaderEdgeCases:
    """Test edge cases and error conditions."""

    def test_get_nested_attr_with_none_object(self):
        """Test get_nested_attr with None object."""
        result = get_nested_attr(None, "any.path", "default")
        assert result == "default"

    def test_get_nested_attr_empty_path(self):
        """Test get_nested_attr with empty path."""
        obj = MagicMock()
        obj.test = "value"

        result = get_nested_attr(obj, "", "default")
        assert result == "default"

    def test_get_nested_attr_single_level_success(self):
        """Test get_nested_attr with single level attribute."""
        obj = MagicMock()
        obj.test = "success_value"

        result = get_nested_attr(obj, "test")
        assert result == "success_value"

    def test_get_nested_attr_multi_level_success(self):
        """Test get_nested_attr with multi-level attribute."""
        obj = MagicMock()
        obj.level1 = MagicMock()
        obj.level1.level2 = MagicMock()
        obj.level1.level2.value = "deep_value"

        result = get_nested_attr(obj, "level1.level2.value")
        assert result == "deep_value"
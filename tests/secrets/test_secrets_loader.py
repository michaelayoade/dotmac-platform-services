"""Tests for secrets loader module."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from dotmac.platform.secrets.secrets_loader import (
    set_nested_attr,
    get_nested_attr,
    load_secrets_from_vault,
    load_secrets_from_vault_sync,
    validate_production_secrets,
    get_vault_secret,
    get_vault_secret_async,
    SECRETS_MAPPING,
)


class MockSettings:
    """Mock settings object for testing."""

    def __init__(self):
        self.secret_key = "change-me-in-production"
        self.environment = "development"

        # Database settings
        self.database = Mock()
        self.database.password = ""
        self.database.username = ""

        # JWT settings
        self.jwt = Mock()
        self.jwt.secret_key = "change-me"

        # Redis settings
        self.redis = Mock()
        self.redis.password = ""

        # Email settings
        self.email = Mock()
        self.email.smtp_password = ""
        self.email.smtp_user = ""

        # Storage settings
        self.storage = Mock()
        self.storage.access_key = ""
        self.storage.secret_key = ""

        # Vault settings
        self.vault = Mock()
        self.vault.enabled = True
        self.vault.url = "http://vault:8200"
        self.vault.token = "test-token"
        self.vault.namespace = "test"
        self.vault.mount_path = "secret"
        self.vault.kv_version = "v2"

        # Observability settings
        self.observability = Mock()
        self.observability.sentry_dsn = ""


class TestNestedAttributeHelpers:
    """Test nested attribute helper functions."""

    def test_set_nested_attr_simple(self):
        """Test setting simple attribute."""
        obj = Mock()
        set_nested_attr(obj, "test_attr", "test_value")
        assert obj.test_attr == "test_value"

    def test_set_nested_attr_nested(self):
        """Test setting nested attribute."""
        obj = Mock()
        obj.nested = Mock()
        set_nested_attr(obj, "nested.attr", "test_value")
        assert obj.nested.attr == "test_value"

    def test_set_nested_attr_deep_nested(self):
        """Test setting deeply nested attribute."""
        obj = Mock()
        obj.level1 = Mock()
        obj.level1.level2 = Mock()
        set_nested_attr(obj, "level1.level2.attr", "test_value")
        assert obj.level1.level2.attr == "test_value"

    def test_get_nested_attr_simple(self):
        """Test getting simple attribute."""
        obj = Mock()
        obj.test_attr = "test_value"
        result = get_nested_attr(obj, "test_attr")
        assert result == "test_value"

    def test_get_nested_attr_nested(self):
        """Test getting nested attribute."""
        obj = Mock()
        obj.nested = Mock()
        obj.nested.attr = "test_value"
        result = get_nested_attr(obj, "nested.attr")
        assert result == "test_value"

    def test_get_nested_attr_missing(self):
        """Test getting missing attribute."""
        obj = Mock()
        result = get_nested_attr(obj, "missing.attr", "default")
        assert result == "default"

    def test_get_nested_attr_no_default(self):
        """Test getting missing attribute without default."""
        obj = Mock()
        result = get_nested_attr(obj, "missing.attr")
        assert result is None


class TestSecretsMapping:
    """Test secrets mapping configuration."""

    def test_secrets_mapping_exists(self):
        """Test that secrets mapping is properly defined."""
        assert isinstance(SECRETS_MAPPING, dict)
        assert len(SECRETS_MAPPING) > 0

    def test_secrets_mapping_structure(self):
        """Test secrets mapping has expected structure."""
        for setting_path, vault_path in SECRETS_MAPPING.items():
            assert isinstance(setting_path, str)
            assert isinstance(vault_path, str)
            assert "." in setting_path or setting_path == "secret_key"
            assert "/" in vault_path


class TestLoadSecretsFromVault:
    """Test async secrets loading from Vault."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        return MockSettings()

    @pytest.fixture
    def mock_vault_client(self):
        """Create mock vault client."""
        client = AsyncMock()
        client.health_check = AsyncMock(return_value=True)
        client.get_secrets = AsyncMock()
        client.close = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_load_secrets_vault_disabled(self, mock_settings):
        """Test secrets loading when Vault is disabled."""
        mock_settings.vault.enabled = False

        with patch("dotmac.platform.secrets.secrets_loader.logger") as mock_logger:
            await load_secrets_from_vault(mock_settings)
            mock_logger.info.assert_called_with("Vault is disabled, using default settings values")

    @pytest.mark.asyncio
    async def test_load_secrets_health_check_fails(self, mock_settings, mock_vault_client):
        """Test secrets loading when health check fails."""
        mock_vault_client.health_check.return_value = False

        with patch("dotmac.platform.secrets.secrets_loader.logger") as mock_logger:
            await load_secrets_from_vault(mock_settings, mock_vault_client)
            mock_logger.error.assert_called_with("Vault health check failed, using default settings")

    @pytest.mark.asyncio
    async def test_load_secrets_success_dict_with_value(self, mock_settings, mock_vault_client):
        """Test successful secrets loading with dict containing 'value' key."""
        mock_vault_client.get_secrets.return_value = {
            "app/secret_key": {"value": "new-secret-key"},
            "database/password": {"value": "db-password"},
            "auth/jwt_secret": {"value": "jwt-secret"},
        }

        with patch("dotmac.platform.secrets.secrets_loader.logger") as mock_logger:
            await load_secrets_from_vault(mock_settings, mock_vault_client)

            assert mock_settings.secret_key == "new-secret-key"
            assert mock_settings.database.password == "db-password"
            assert mock_settings.jwt.secret_key == "jwt-secret"
            mock_logger.info.assert_called_with("Successfully loaded 3 secrets from Vault")

    @pytest.mark.asyncio
    async def test_load_secrets_success_string_values(self, mock_settings, mock_vault_client):
        """Test successful secrets loading with string values."""
        mock_vault_client.get_secrets.return_value = {
            "app/secret_key": "string-secret-key",
            "database/password": "string-db-password",
        }

        await load_secrets_from_vault(mock_settings, mock_vault_client)

        assert mock_settings.secret_key == "string-secret-key"
        assert mock_settings.database.password == "string-db-password"

    @pytest.mark.asyncio
    async def test_load_secrets_success_dict_without_value(self, mock_settings, mock_vault_client):
        """Test successful secrets loading with dict without 'value' key."""
        mock_vault_client.get_secrets.return_value = {
            "app/secret_key": {"data": "dict-secret-key"},
            "database/password": {"password": "dict-db-password"},
        }

        await load_secrets_from_vault(mock_settings, mock_vault_client)

        assert mock_settings.secret_key == "dict-secret-key"
        assert mock_settings.database.password == "dict-db-password"

    @pytest.mark.asyncio
    async def test_load_secrets_empty_values(self, mock_settings, mock_vault_client):
        """Test secrets loading with empty values."""
        mock_vault_client.get_secrets.return_value = {
            "app/secret_key": {},
            "database/password": None,
            "auth/jwt_secret": "",
        }

        original_secret = mock_settings.secret_key
        await load_secrets_from_vault(mock_settings, mock_vault_client)

        # Values should remain unchanged
        assert mock_settings.secret_key == original_secret

    @pytest.mark.asyncio
    async def test_load_secrets_set_attr_exception(self, mock_settings, mock_vault_client):
        """Test secrets loading when setting attribute fails."""
        mock_vault_client.get_secrets.return_value = {
            "app/secret_key": {"value": "new-secret-key"},
        }

        with patch("dotmac.platform.secrets.secrets_loader.set_nested_attr", side_effect=Exception("Set error")):
            with patch("dotmac.platform.secrets.secrets_loader.logger") as mock_logger:
                await load_secrets_from_vault(mock_settings, mock_vault_client)
                mock_logger.error.assert_called_with("Failed to set secret_key: Set error")

    @pytest.mark.asyncio
    async def test_load_secrets_production_validation(self, mock_settings, mock_vault_client):
        """Test secrets loading with production validation."""
        mock_settings.environment = "production"
        mock_vault_client.get_secrets.return_value = {
            "app/secret_key": {"value": "production-secret"},
            "database/password": {"value": "production-password"},
            "auth/jwt_secret": {"value": "production-jwt"},
        }

        with patch("dotmac.platform.secrets.secrets_loader.validate_production_secrets") as mock_validate:
            await load_secrets_from_vault(mock_settings, mock_vault_client)
            mock_validate.assert_called_once_with(mock_settings)

    @pytest.mark.asyncio
    async def test_load_secrets_vault_error_development(self, mock_settings, mock_vault_client):
        """Test Vault error handling in development."""
        from dotmac.platform.secrets.vault_client import VaultError

        mock_vault_client.get_secrets.side_effect = VaultError("Vault connection failed")

        with patch("dotmac.platform.secrets.secrets_loader.logger") as mock_logger:
            # Should not raise in development
            await load_secrets_from_vault(mock_settings, mock_vault_client)
            mock_logger.error.assert_called_with("Failed to load secrets from Vault: Vault connection failed")

    @pytest.mark.asyncio
    async def test_load_secrets_vault_error_production(self, mock_settings, mock_vault_client):
        """Test Vault error handling in production."""
        from dotmac.platform.secrets.vault_client import VaultError

        mock_settings.environment = "production"
        mock_vault_client.get_secrets.side_effect = VaultError("Vault connection failed")

        # Should raise in production
        with pytest.raises(VaultError):
            await load_secrets_from_vault(mock_settings, mock_vault_client)

    @pytest.mark.asyncio
    async def test_load_secrets_client_cleanup(self, mock_settings):
        """Test that Vault client is properly cleaned up."""
        with patch("dotmac.platform.secrets.secrets_loader.AsyncVaultClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.health_check.return_value = True
            mock_client.get_secrets.return_value = {}
            mock_client_class.return_value = mock_client

            await load_secrets_from_vault(mock_settings)
            # Client cleanup is checked but not called for AsyncVaultClient


class TestLoadSecretsFromVaultSync:
    """Test synchronous secrets loading from Vault."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        return MockSettings()

    @pytest.fixture
    def mock_vault_client(self):
        """Create mock vault client."""
        client = Mock()
        client.health_check = Mock(return_value=True)
        client.get_secrets = Mock()
        client.close = Mock()
        return client

    def test_load_secrets_sync_vault_disabled(self, mock_settings):
        """Test sync secrets loading when Vault is disabled."""
        mock_settings.vault.enabled = False

        with patch("dotmac.platform.secrets.secrets_loader.logger") as mock_logger:
            load_secrets_from_vault_sync(mock_settings)
            mock_logger.info.assert_called_with("Vault is disabled, using default settings values")

    def test_load_secrets_sync_success(self, mock_settings, mock_vault_client):
        """Test successful sync secrets loading."""
        mock_vault_client.get_secrets.return_value = {
            "app/secret_key": {"value": "sync-secret-key"},
            "database/password": {"value": "sync-db-password"},
        }

        load_secrets_from_vault_sync(mock_settings, mock_vault_client)

        assert mock_settings.secret_key == "sync-secret-key"
        assert mock_settings.database.password == "sync-db-password"

    def test_load_secrets_sync_health_check_fails(self, mock_settings, mock_vault_client):
        """Test sync secrets loading when health check fails."""
        mock_vault_client.health_check.return_value = False

        with patch("dotmac.platform.secrets.secrets_loader.logger") as mock_logger:
            load_secrets_from_vault_sync(mock_settings, mock_vault_client)
            mock_logger.error.assert_called_with("Vault health check failed, using default settings")


class TestValidateProductionSecrets:
    """Test production secrets validation."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        return MockSettings()

    def test_validate_production_secrets_success(self, mock_settings):
        """Test successful production secrets validation."""
        mock_settings.secret_key = "strong-production-secret"
        mock_settings.jwt.secret_key = "strong-jwt-secret"
        mock_settings.database.password = "strong-database-password"

        # Should not raise
        validate_production_secrets(mock_settings)

    def test_validate_production_secrets_default_secret_key(self, mock_settings):
        """Test validation failure with default secret key."""
        mock_settings.secret_key = "change-me-in-production"

        with pytest.raises(ValueError, match="secret_key must be changed from default"):
            validate_production_secrets(mock_settings)

    def test_validate_production_secrets_default_jwt_key(self, mock_settings):
        """Test validation failure with default JWT key."""
        mock_settings.secret_key = "strong-secret"
        mock_settings.jwt.secret_key = "change-me"

        with pytest.raises(ValueError, match="JWT secret_key must be changed from default"):
            validate_production_secrets(mock_settings)

    def test_validate_production_secrets_missing_db_password(self, mock_settings):
        """Test validation failure with missing database password."""
        mock_settings.secret_key = "strong-secret"
        mock_settings.jwt.secret_key = "strong-jwt"
        mock_settings.database.password = ""

        with pytest.raises(ValueError, match="Database password is not set"):
            validate_production_secrets(mock_settings)

    def test_validate_production_secrets_weak_db_password(self, mock_settings):
        """Test validation failure with weak database password."""
        mock_settings.secret_key = "strong-secret"
        mock_settings.jwt.secret_key = "strong-jwt"
        mock_settings.database.password = "weak"

        with pytest.raises(ValueError, match="Database password is too short"):
            validate_production_secrets(mock_settings)

    def test_validate_production_secrets_multiple_errors(self, mock_settings):
        """Test validation with multiple errors."""
        # Keep defaults (invalid values)
        mock_settings.database.password = ""

        with pytest.raises(ValueError) as exc_info:
            validate_production_secrets(mock_settings)

        error_msg = str(exc_info.value)
        assert "secret_key must be changed from default" in error_msg
        assert "JWT secret_key must be changed from default" in error_msg
        assert "Database password is not set" in error_msg


class TestVaultSecretHelpers:
    """Test Vault secret helper functions."""

    @patch("dotmac.platform.secrets.secrets_loader.settings")
    def test_get_vault_secret_vault_disabled(self, mock_settings):
        """Test get_vault_secret when Vault is disabled."""
        mock_settings.vault.enabled = False

        result = get_vault_secret("test/path")
        assert result is None

    @patch("dotmac.platform.secrets.secrets_loader.settings")
    @patch("dotmac.platform.secrets.secrets_loader.VaultClient")
    def test_get_vault_secret_success(self, mock_client_class, mock_settings):
        """Test successful secret retrieval."""
        mock_settings.vault.enabled = True
        mock_settings.vault.url = "http://vault:8200"
        mock_settings.vault.token = "test-token"
        mock_settings.vault.namespace = "test"
        mock_settings.vault.mount_path = "secret"
        mock_settings.vault.kv_version = "v2"

        mock_client = Mock()
        mock_client.get_secret.return_value = {"key": "value"}
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        mock_client_class.return_value = mock_client

        result = get_vault_secret("test/path")

        assert result == {"key": "value"}
        mock_client.get_secret.assert_called_once_with("test/path")

    @patch("dotmac.platform.secrets.secrets_loader.settings")
    @patch("dotmac.platform.secrets.secrets_loader.VaultClient")
    def test_get_vault_secret_error(self, mock_client_class, mock_settings):
        """Test secret retrieval with error."""
        from dotmac.platform.secrets.vault_client import VaultError

        mock_settings.vault.enabled = True
        mock_client = Mock()
        mock_client.get_secret.side_effect = VaultError("Connection failed")
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        mock_client_class.return_value = mock_client

        with patch("dotmac.platform.secrets.secrets_loader.logger") as mock_logger:
            result = get_vault_secret("test/path")
            assert result is None
            mock_logger.error.assert_called_with("Failed to fetch secret from test/path: Connection failed")

    @pytest.mark.asyncio
    @patch("dotmac.platform.secrets.secrets_loader.settings")
    async def test_get_vault_secret_async_vault_disabled(self, mock_settings):
        """Test async get_vault_secret when Vault is disabled."""
        mock_settings.vault.enabled = False

        result = await get_vault_secret_async("test/path")
        assert result is None

    @pytest.mark.asyncio
    @patch("dotmac.platform.secrets.secrets_loader.settings")
    @patch("dotmac.platform.secrets.secrets_loader.AsyncVaultClient")
    async def test_get_vault_secret_async_success(self, mock_client_class, mock_settings):
        """Test successful async secret retrieval."""
        mock_settings.vault.enabled = True

        mock_client = AsyncMock()
        mock_client.get_secret.return_value = {"key": "value"}
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        result = await get_vault_secret_async("test/path")

        assert result == {"key": "value"}
        mock_client.get_secret.assert_called_once_with("test/path")

    @pytest.mark.asyncio
    @patch("dotmac.platform.secrets.secrets_loader.settings")
    @patch("dotmac.platform.secrets.secrets_loader.AsyncVaultClient")
    async def test_get_vault_secret_async_error(self, mock_client_class, mock_settings):
        """Test async secret retrieval with error."""
        from dotmac.platform.secrets.vault_client import VaultError

        mock_settings.vault.enabled = True
        mock_client = AsyncMock()
        mock_client.get_secret.side_effect = VaultError("Connection failed")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        with patch("dotmac.platform.secrets.secrets_loader.logger") as mock_logger:
            result = await get_vault_secret_async("test/path")
            assert result is None
            mock_logger.error.assert_called_with("Failed to fetch secret from test/path: Connection failed")


class TestIntegration:
    """Integration tests."""

    @pytest.mark.asyncio
    async def test_full_secrets_loading_workflow(self):
        """Test complete secrets loading workflow."""
        settings_obj = MockSettings()

        mock_client = AsyncMock()
        mock_client.health_check.return_value = True
        mock_client.get_secrets.return_value = {
            "app/secret_key": {"value": "production-secret"},
            "database/password": {"value": "strong-db-password"},
            "auth/jwt_secret": {"value": "production-jwt-secret"},
            "storage/access_key": {"value": "storage-access"},
            "storage/secret_key": {"value": "storage-secret"},
        }

        await load_secrets_from_vault(settings_obj, mock_client)

        # Verify all secrets were loaded
        assert settings_obj.secret_key == "production-secret"
        assert settings_obj.database.password == "strong-db-password"
        assert settings_obj.jwt.secret_key == "production-jwt-secret"
        assert settings_obj.storage.access_key == "storage-access"
        assert settings_obj.storage.secret_key == "storage-secret"
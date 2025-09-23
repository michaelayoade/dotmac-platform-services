"""
Comprehensive tests for the secrets API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from dotmac.platform.secrets.api import (
    router,
    get_vault_client,
    SecretData,
    SecretResponse,
    SecretListResponse,
    HealthResponse,
    check_vault_health,
    get_secret,
    create_or_update_secret,
    delete_secret,
    list_secrets,
)
from dotmac.platform.secrets.vault_client import VaultError


class TestGetVaultClient:
    """Test the vault client dependency."""

    @pytest.mark.asyncio
    async def test_get_vault_client_disabled(self):
        """Test vault client when vault is disabled."""
        with patch("dotmac.platform.secrets.api.settings") as mock_settings:
            mock_settings.vault.enabled = False

            with pytest.raises(HTTPException) as exc_info:
                await get_vault_client()

            assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            assert "Vault/OpenBao is not enabled" in str(exc_info.value.detail)

    @patch("dotmac.platform.secrets.api.AsyncVaultClient")
    @pytest.mark.asyncio
    async def test_get_vault_client_enabled(self, mock_client):
        """Test vault client when vault is enabled."""
        with patch("dotmac.platform.secrets.api.settings") as mock_settings:
            mock_settings.vault.enabled = True
            mock_settings.vault.url = "http://vault:8200"
            mock_settings.vault.token = "test-token"
            mock_settings.vault.namespace = "test-ns"
            mock_settings.vault.mount_path = "secret"
            mock_settings.vault.kv_version = 2

            result = await get_vault_client()

            mock_client.assert_called_once_with(
                url="http://vault:8200",
                token="test-token",
                namespace="test-ns",
                mount_path="secret",
                kv_version=2,
            )


class TestSecretModels:
    """Test Pydantic models for secrets API."""

    def test_secret_data_model(self):
        """Test SecretData model validation."""
        data = SecretData(
            data={"username": "admin", "password": "secret"},
            metadata={"created_by": "user123"}
        )

        assert data.data == {"username": "admin", "password": "secret"}
        assert data.metadata == {"created_by": "user123"}

    def test_secret_data_model_without_metadata(self):
        """Test SecretData model without metadata."""
        data = SecretData(data={"key": "value"})

        assert data.data == {"key": "value"}
        assert data.metadata is None

    def test_secret_response_model(self):
        """Test SecretResponse model."""
        response = SecretResponse(
            path="app/database",
            data={"host": "localhost", "port": 5432},
            metadata={"version": 1}
        )

        assert response.path == "app/database"
        assert response.data == {"host": "localhost", "port": 5432}
        assert response.metadata == {"version": 1}

    def test_secret_list_response_model(self):
        """Test SecretListResponse model."""
        response = SecretListResponse(
            secrets=["app/database", "app/cache", "api/keys"]
        )

        assert response.secrets == ["app/database", "app/cache", "api/keys"]

    def test_health_response_model(self):
        """Test HealthResponse model."""
        response = HealthResponse(
            healthy=True,
            vault_url="http://vault:8200",
            mount_path="secret"
        )

        assert response.healthy is True
        assert response.vault_url == "http://vault:8200"
        assert response.mount_path == "secret"


class TestHealthEndpoint:
    """Test the health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check."""
        mock_vault = AsyncMock()
        mock_vault.health_check.return_value = True

        with patch("dotmac.platform.secrets.api.settings") as mock_settings:
            mock_settings.vault.url = "http://vault:8200"
            mock_settings.vault.mount_path = "secret"

            result = await check_vault_health(mock_vault)

            assert isinstance(result, HealthResponse)
            assert result.healthy is True
            assert result.vault_url == "http://vault:8200"
            assert result.mount_path == "secret"

            mock_vault.health_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check when vault is unhealthy."""
        mock_vault = AsyncMock()
        mock_vault.health_check.side_effect = Exception("Connection failed")

        with patch("dotmac.platform.secrets.api.settings") as mock_settings:
            mock_settings.vault.url = "http://vault:8200"
            mock_settings.vault.mount_path = "secret"

            with patch("dotmac.platform.secrets.api.logger") as mock_logger:
                result = await check_vault_health(mock_vault)

                assert isinstance(result, HealthResponse)
                assert result.healthy is False
                assert result.vault_url == "http://vault:8200"
                assert result.mount_path == "secret"

                mock_logger.error.assert_called_once()


class TestGetSecretEndpoint:
    """Test the get secret endpoint."""

    @pytest.mark.asyncio
    async def test_get_secret_success(self):
        """Test successful secret retrieval."""
        mock_vault = AsyncMock()
        mock_vault.get_secret.return_value = {"username": "admin", "password": "secret"}

        result = await get_secret("app/database", mock_vault)

        assert isinstance(result, SecretResponse)
        assert result.path == "app/database"
        assert result.data == {"username": "admin", "password": "secret"}
        assert result.metadata is None

        mock_vault.__aenter__.assert_called_once()
        mock_vault.get_secret.assert_called_once_with("app/database")

    @pytest.mark.asyncio
    async def test_get_secret_not_found(self):
        """Test get secret when secret doesn't exist."""
        mock_vault = AsyncMock()
        mock_vault.get_secret.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_secret("nonexistent/path", mock_vault)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Secret not found at path: nonexistent/path" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_secret_vault_error(self):
        """Test get secret with vault error."""
        mock_vault = AsyncMock()
        mock_vault.get_secret.side_effect = VaultError("Vault connection failed")

        with patch("dotmac.platform.secrets.api.logger") as mock_logger:
            with pytest.raises(HTTPException) as exc_info:
                await get_secret("app/database", mock_vault)

            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to retrieve secret" in str(exc_info.value.detail)
            mock_logger.error.assert_called_once()


class TestCreateOrUpdateSecretEndpoint:
    """Test the create/update secret endpoint."""

    @pytest.mark.asyncio
    async def test_create_secret_success(self):
        """Test successful secret creation."""
        mock_vault = AsyncMock()
        secret_data = SecretData(
            data={"username": "admin", "password": "secret"},
            metadata={"created_by": "user123"}
        )

        result = await create_or_update_secret("app/database", secret_data, mock_vault)

        assert isinstance(result, SecretResponse)
        assert result.path == "app/database"
        assert result.data == {"username": "admin", "password": "secret"}
        assert result.metadata == {"created_by": "user123"}

        mock_vault.__aenter__.assert_called_once()
        mock_vault.set_secret.assert_called_once_with("app/database", {"username": "admin", "password": "secret"})

    @pytest.mark.asyncio
    async def test_create_secret_vault_error(self):
        """Test create secret with vault error."""
        mock_vault = AsyncMock()
        mock_vault.set_secret.side_effect = VaultError("Permission denied")

        secret_data = SecretData(data={"key": "value"})

        with patch("dotmac.platform.secrets.api.logger") as mock_logger:
            with pytest.raises(HTTPException) as exc_info:
                await create_or_update_secret("app/test", secret_data, mock_vault)

            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to store secret" in str(exc_info.value.detail)
            mock_logger.error.assert_called_once()


class TestDeleteSecretEndpoint:
    """Test the delete secret endpoint."""

    @pytest.mark.asyncio
    async def test_delete_secret_success(self):
        """Test successful secret deletion."""
        mock_vault = AsyncMock()

        # Should not raise an exception
        result = await delete_secret("app/database", mock_vault)

        assert result is None  # No content returned
        mock_vault.__aenter__.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_secret_vault_error(self):
        """Test delete secret with vault error."""
        mock_vault = AsyncMock()
        mock_vault.__aenter__.side_effect = VaultError("Connection failed")

        with patch("dotmac.platform.secrets.api.logger") as mock_logger:
            with pytest.raises(HTTPException) as exc_info:
                await delete_secret("app/database", mock_vault)

            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to delete secret" in str(exc_info.value.detail)
            mock_logger.error.assert_called_once()


class TestListSecretsEndpoint:
    """Test the list secrets endpoint."""

    @pytest.mark.asyncio
    async def test_list_secrets(self):
        """Test list secrets endpoint."""
        mock_vault = AsyncMock()

        with patch("dotmac.platform.secrets.api.logger") as mock_logger:
            result = await list_secrets(mock_vault, prefix="app/")

            assert isinstance(result, SecretListResponse)
            assert result.secrets == []  # Not implemented yet

            mock_logger.warning.assert_called_once_with("List secrets endpoint not fully implemented")

    @pytest.mark.asyncio
    async def test_list_secrets_without_prefix(self):
        """Test list secrets without prefix."""
        mock_vault = AsyncMock()

        with patch("dotmac.platform.secrets.api.logger") as mock_logger:
            result = await list_secrets(mock_vault)

            assert isinstance(result, SecretListResponse)
            assert result.secrets == []

            mock_logger.warning.assert_called_once()


class TestSecretsAPIIntegration:
    """Integration tests for the secrets API router."""

    @pytest.fixture
    def mock_vault_enabled(self):
        """Mock vault as enabled."""
        with patch("dotmac.platform.secrets.api.settings") as mock_settings:
            mock_settings.vault.enabled = True
            mock_settings.vault.url = "http://vault:8200"
            mock_settings.vault.token = "test-token"
            mock_settings.vault.namespace = None
            mock_settings.vault.mount_path = "secret"
            mock_settings.vault.kv_version = 2
            yield mock_settings

    @pytest.fixture
    def mock_vault_client(self):
        """Mock vault client."""
        with patch("dotmac.platform.secrets.api.AsyncVaultClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.health_check.return_value = True
            mock_instance.get_secret.return_value = {"key": "value"}
            mock_instance.set_secret.return_value = None
            mock_client.return_value = mock_instance
            yield mock_instance

    def test_router_tags(self):
        """Test that router has correct tags."""
        # Check that routes have the 'secrets' tag
        for route in router.routes:
            if hasattr(route, 'tags'):
                assert 'secrets' in route.tags

    def test_router_paths(self):
        """Test that router has expected paths."""
        paths = [route.path for route in router.routes if hasattr(route, 'path')]

        expected_paths = [
            "/health",
            "/secrets/{path:path}",
            "/secrets",
        ]

        for path in expected_paths:
            assert path in paths
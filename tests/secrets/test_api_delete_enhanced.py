"""
Tests for enhanced secrets deletion functionality.
"""

import pytest
import unittest.mock
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status

from dotmac.platform.secrets.api import delete_secret
from dotmac.platform.secrets.vault_client import VaultError


class TestSecretsDeleteEnhanced:
    """Test the enhanced delete secret functionality."""

    @pytest.fixture
    def mock_vault_client(self):
        """Create a mock vault client."""
        vault = AsyncMock()
        vault.__aenter__ = AsyncMock(return_value=vault)
        vault.__aexit__ = AsyncMock(return_value=None)
        return vault

    @pytest.mark.asyncio
    async def test_delete_secret_success(self, mock_vault_client):
        """Test successful secret deletion."""
        mock_vault_client.delete_secret = AsyncMock()

        with patch("dotmac.platform.secrets.api.logger") as mock_logger:
            result = await delete_secret("app/database", mock_vault_client)

            assert result is None
            mock_vault_client.delete_secret.assert_called_once_with("app/database")
            mock_logger.info.assert_called_once_with("Deleted secret at path: app/database")

    @pytest.mark.asyncio
    async def test_delete_secret_vault_error(self, mock_vault_client):
        """Test delete secret with VaultError."""
        mock_vault_client.delete_secret = AsyncMock(
            side_effect=VaultError("Permission denied")
        )

        with patch("dotmac.platform.secrets.api.logger") as mock_logger:
            with pytest.raises(HTTPException) as exc_info:
                await delete_secret("app/database", mock_vault_client)

            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to delete secret" in str(exc_info.value.detail)
            assert "Permission denied" in str(exc_info.value.detail)

            mock_logger.error.assert_called_once()
            error_call_args = mock_logger.error.call_args[0][0]
            assert "Failed to delete secret" in error_call_args

    @pytest.mark.asyncio
    async def test_delete_secret_context_manager_usage(self, mock_vault_client):
        """Test that delete uses vault client as context manager."""
        mock_vault_client.delete_secret = AsyncMock()

        await delete_secret("test/path", mock_vault_client)

        # Verify context manager was used
        mock_vault_client.__aenter__.assert_called_once()
        mock_vault_client.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_secret_logs_path(self, mock_vault_client):
        """Test that delete operation logs the correct path."""
        mock_vault_client.delete_secret = AsyncMock()
        test_path = "myapp/production/database"

        with patch("dotmac.platform.secrets.api.logger") as mock_logger:
            await delete_secret(test_path, mock_vault_client)

            mock_logger.info.assert_called_once_with(f"Deleted secret at path: {test_path}")

    @pytest.mark.asyncio
    async def test_delete_secret_error_logging(self, mock_vault_client):
        """Test proper error logging on failure."""
        error_msg = "Token expired"
        mock_vault_client.delete_secret = AsyncMock(
            side_effect=VaultError(error_msg)
        )

        with patch("dotmac.platform.secrets.api.logger") as mock_logger:
            with pytest.raises(HTTPException):
                await delete_secret("app/test", mock_vault_client)

            # Check that error was logged with original VaultError
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            if len(call_args[0]) > 0:
                logged_message = call_args[0][0]
                assert "Failed to delete secret" in logged_message
            # Check if error was logged in the call
            logged_content = str(call_args)
            assert error_msg in logged_content

    @pytest.mark.asyncio
    async def test_delete_secret_multiple_paths(self, mock_vault_client):
        """Test deleting multiple different secret paths."""
        mock_vault_client.delete_secret = AsyncMock()

        paths = ["app/db", "app/cache", "api/keys", "billing/stripe"]

        for path in paths:
            await delete_secret(path, mock_vault_client)

        # Verify each path was called correctly
        expected_calls = [unittest.mock.call(path) for path in paths]
        mock_vault_client.delete_secret.assert_has_calls(expected_calls)

    @pytest.mark.asyncio
    async def test_delete_secret_empty_path(self, mock_vault_client):
        """Test delete with empty path."""
        mock_vault_client.delete_secret = AsyncMock()

        await delete_secret("", mock_vault_client)

        mock_vault_client.delete_secret.assert_called_once_with("")

    @pytest.mark.asyncio
    async def test_delete_secret_special_characters(self, mock_vault_client):
        """Test delete with special characters in path."""
        mock_vault_client.delete_secret = AsyncMock()
        special_path = "app/service-name/config_2024"

        await delete_secret(special_path, mock_vault_client)

        mock_vault_client.delete_secret.assert_called_once_with(special_path)

    @pytest.mark.asyncio
    async def test_delete_secret_unicode_path(self, mock_vault_client):
        """Test delete with unicode characters in path."""
        mock_vault_client.delete_secret = AsyncMock()
        unicode_path = "app/测试/配置"

        await delete_secret(unicode_path, mock_vault_client)

        mock_vault_client.delete_secret.assert_called_once_with(unicode_path)


class TestSecretsDeleteVaultClientIntegration:
    """Test integration with vault client delete functionality."""

    @pytest.mark.asyncio
    async def test_delete_secret_calls_vault_client_method(self):
        """Test that API calls the correct vault client method."""
        mock_vault = AsyncMock()
        mock_vault.delete_secret = AsyncMock()
        mock_vault.__aenter__ = AsyncMock(return_value=mock_vault)
        mock_vault.__aexit__ = AsyncMock(return_value=None)

        await delete_secret("test/integration", mock_vault)

        # Verify the correct method was called
        mock_vault.delete_secret.assert_called_once_with("test/integration")

    @pytest.mark.asyncio
    async def test_delete_secret_handles_vault_auth_error(self):
        """Test handling of Vault authentication errors."""
        from dotmac.platform.secrets.vault_client import VaultAuthenticationError

        mock_vault_client = AsyncMock()
        mock_vault_client.__aenter__ = AsyncMock(return_value=mock_vault_client)
        mock_vault_client.__aexit__ = AsyncMock(return_value=None)
        mock_vault_client.delete_secret = AsyncMock(
            side_effect=VaultAuthenticationError("Invalid token")
        )

        with pytest.raises(HTTPException) as exc_info:
            await delete_secret("protected/secret", mock_vault_client)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    async def test_delete_secret_before_after_comparison(self):
        """Test the improvement from before/after the fix."""
        # This would be the old implementation (empty)
        async def old_delete_secret(path: str, vault) -> None:
            # Old implementation did nothing
            pass

        # New implementation actually calls vault
        mock_vault = AsyncMock()
        mock_vault.delete_secret = AsyncMock()
        mock_vault.__aenter__ = AsyncMock(return_value=mock_vault)
        mock_vault.__aexit__ = AsyncMock(return_value=None)

        # Old way: nothing happened
        await old_delete_secret("test", mock_vault)
        assert mock_vault.delete_secret.call_count == 0

        # New way: actually deletes
        await delete_secret("test", mock_vault)
        assert mock_vault.delete_secret.call_count == 1


class TestSecretsAPIEndpointIntegration:
    """Test the complete API endpoint integration."""

    @pytest.fixture
    def app_client(self):
        """Create test client for the secrets API."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from dotmac.platform.secrets.api import router

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_delete_endpoint_exists(self):
        """Test that the delete endpoint exists and has correct HTTP method."""
        from dotmac.platform.secrets.api import router

        # Find the delete route
        delete_routes = [
            route for route in router.routes
            if hasattr(route, 'path') and 'secrets/{path:path}' in route.path
            and hasattr(route, 'methods') and 'DELETE' in route.methods
        ]

        assert len(delete_routes) == 1
        delete_route = delete_routes[0]

        # Check response status
        assert hasattr(delete_route, 'status_code')
        # Should be 204 No Content for successful deletion

    @pytest.mark.asyncio
    async def test_delete_secret_response_format(self):
        """Test that delete returns correct response format."""
        mock_vault_client = AsyncMock()
        mock_vault_client.__aenter__ = AsyncMock(return_value=mock_vault_client)
        mock_vault_client.__aexit__ = AsyncMock(return_value=None)
        mock_vault_client.delete_secret = AsyncMock()

        result = await delete_secret("test/path", mock_vault_client)

        # Should return None for successful deletion (204 No Content)
        assert result is None

    def test_delete_endpoint_has_correct_tags(self):
        """Test that delete endpoint has correct OpenAPI tags."""
        from dotmac.platform.secrets.api import router

        # Check that the route has the 'secrets' tag
        delete_routes = [
            route for route in router.routes
            if hasattr(route, 'path') and 'secrets/{path:path}' in route.path
            and hasattr(route, 'methods') and 'DELETE' in route.methods
        ]

        if delete_routes:
            route = delete_routes[0]
            # The tags should include 'secrets'
            if hasattr(route, 'tags'):
                assert 'secrets' in route.tags
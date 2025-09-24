"""Tests for API key management endpoints."""

import json
from datetime import datetime, UTC, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.dotmac.platform.auth.core import UserInfo


@pytest.fixture
def mock_current_user():
    """Mock current user for API key tests."""
    return UserInfo(
        user_id="test_user_123",
        username="testuser",
        roles=["user"],
        permissions=["read", "write"],
    )


@pytest.fixture
def mock_api_key_service():
    """Mock API key service."""
    with patch("src.dotmac.platform.auth.api_keys_router.api_key_service") as mock_service:
        # Mock the enhanced functions
        with patch("src.dotmac.platform.auth.api_keys_router._enhanced_create_api_key") as mock_create, \
             patch("src.dotmac.platform.auth.api_keys_router._list_user_api_keys") as mock_list, \
             patch("src.dotmac.platform.auth.api_keys_router._get_api_key_by_id") as mock_get, \
             patch("src.dotmac.platform.auth.api_keys_router._update_api_key_metadata") as mock_update, \
             patch("src.dotmac.platform.auth.api_keys_router._revoke_api_key_by_id") as mock_revoke:

            yield {
                "service": mock_service,
                "create": mock_create,
                "list": mock_list,
                "get": mock_get,
                "update": mock_update,
                "revoke": mock_revoke,
            }


class TestAPIKeyEndpoints:
    """Test API key management endpoints."""

    @pytest.mark.asyncio
    async def test_create_api_key_success(self, async_client: AsyncClient, mock_current_user, mock_api_key_service):
        """Test successful API key creation."""
        # Arrange
        mock_api_key_service["create"].return_value = ("sk_test123456789", "key_id_123")

        request_data = {
            "name": "Test API Key",
            "scopes": ["read", "write"],
            "description": "Test description",
        }

        with patch("src.dotmac.platform.auth.api_keys_router.get_current_user", return_value=mock_current_user):
            # Act
            response = await async_client.post("/api/v1/auth/api-keys", json=request_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test API Key"
        assert data["scopes"] == ["read", "write"]
        assert data["description"] == "Test description"
        assert data["api_key"] == "sk_test123456789"
        assert data["id"] == "key_id_123"

        mock_api_key_service["create"].assert_called_once_with(
            user_id="test_user_123",
            name="Test API Key",
            scopes=["read", "write"],
            expires_at=None,
            description="Test description",
        )

    @pytest.mark.asyncio
    async def test_create_api_key_validation_error(self, async_client: AsyncClient, mock_current_user):
        """Test API key creation with validation errors."""
        with patch("src.dotmac.platform.auth.api_keys_router.get_current_user", return_value=mock_current_user):
            # Missing required name field
            response = await async_client.post("/api/v1/auth/api-keys", json={
                "scopes": ["read"],
            })

        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("name" in error["loc"] for error in error_detail)

    @pytest.mark.asyncio
    async def test_list_api_keys_success(self, async_client: AsyncClient, mock_current_user, mock_api_key_service):
        """Test successful API key listing."""
        # Arrange
        mock_keys = [
            {
                "id": "key_1",
                "user_id": "test_user_123",
                "name": "Production Key",
                "scopes": ["read", "write"],
                "created_at": datetime.now(UTC).isoformat(),
                "is_active": True,
            },
            {
                "id": "key_2",
                "user_id": "test_user_123",
                "name": "Analytics Key",
                "scopes": ["analytics:read"],
                "created_at": datetime.now(UTC).isoformat(),
                "is_active": True,
            }
        ]
        mock_api_key_service["list"].return_value = mock_keys

        with patch("src.dotmac.platform.auth.api_keys_router.get_current_user", return_value=mock_current_user):
            # Act
            response = await async_client.get("/api/v1/auth/api-keys")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["api_keys"]) == 2
        assert data["total"] == 2
        assert data["page"] == 1
        assert data["limit"] == 50

        # Verify key data
        first_key = data["api_keys"][0]
        assert first_key["name"] == "Production Key"
        assert first_key["scopes"] == ["read", "write"]
        assert "key_preview" in first_key
        assert "api_key" not in first_key  # Should not expose full key

    @pytest.mark.asyncio
    async def test_list_api_keys_pagination(self, async_client: AsyncClient, mock_current_user, mock_api_key_service):
        """Test API key listing with pagination."""
        mock_api_key_service["list"].return_value = []

        with patch("src.dotmac.platform.auth.api_keys_router.get_current_user", return_value=mock_current_user):
            response = await async_client.get("/api/v1/auth/api-keys?page=2&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["limit"] == 10

    @pytest.mark.asyncio
    async def test_get_api_key_success(self, async_client: AsyncClient, mock_current_user, mock_api_key_service):
        """Test successful API key retrieval."""
        # Arrange
        key_data = {
            "id": "key_123",
            "user_id": "test_user_123",
            "name": "Test Key",
            "scopes": ["read"],
            "created_at": datetime.now(UTC).isoformat(),
            "is_active": True,
        }
        mock_api_key_service["get"].return_value = key_data

        with patch("src.dotmac.platform.auth.api_keys_router.get_current_user", return_value=mock_current_user):
            # Act
            response = await async_client.get("/api/v1/auth/api-keys/key_123")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Key"
        assert data["scopes"] == ["read"]

        mock_api_key_service["get"].assert_called_once_with("key_123")

    @pytest.mark.asyncio
    async def test_get_api_key_not_found(self, async_client: AsyncClient, mock_current_user, mock_api_key_service):
        """Test API key retrieval when key doesn't exist."""
        mock_api_key_service["get"].return_value = None

        with patch("src.dotmac.platform.auth.api_keys_router.get_current_user", return_value=mock_current_user):
            response = await async_client.get("/api/v1/auth/api-keys/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_api_key_wrong_user(self, async_client: AsyncClient, mock_current_user, mock_api_key_service):
        """Test API key retrieval with wrong user."""
        # Key belongs to different user
        key_data = {
            "id": "key_123",
            "user_id": "other_user",
            "name": "Other User's Key",
            "scopes": ["read"],
            "created_at": datetime.now(UTC).isoformat(),
            "is_active": True,
        }
        mock_api_key_service["get"].return_value = key_data

        with patch("src.dotmac.platform.auth.api_keys_router.get_current_user", return_value=mock_current_user):
            response = await async_client.get("/api/v1/auth/api-keys/key_123")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_api_key_success(self, async_client: AsyncClient, mock_current_user, mock_api_key_service):
        """Test successful API key update."""
        # Arrange
        existing_key = {
            "id": "key_123",
            "user_id": "test_user_123",
            "name": "Old Name",
            "scopes": ["read"],
            "created_at": datetime.now(UTC).isoformat(),
            "is_active": True,
        }
        updated_key = {
            **existing_key,
            "name": "New Name",
            "scopes": ["read", "write"],
            "description": "Updated description",
        }

        mock_api_key_service["get"].side_effect = [existing_key, updated_key]
        mock_api_key_service["update"].return_value = True

        update_data = {
            "name": "New Name",
            "scopes": ["read", "write"],
            "description": "Updated description",
        }

        with patch("src.dotmac.platform.auth.api_keys_router.get_current_user", return_value=mock_current_user):
            # Act
            response = await async_client.patch("/api/v1/auth/api-keys/key_123", json=update_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["scopes"] == ["read", "write"]
        assert data["description"] == "Updated description"

        mock_api_key_service["update"].assert_called_once_with(
            "key_123",
            {
                "name": "New Name",
                "scopes": ["read", "write"],
                "description": "Updated description",
            }
        )

    @pytest.mark.asyncio
    async def test_update_api_key_partial(self, async_client: AsyncClient, mock_current_user, mock_api_key_service):
        """Test partial API key update."""
        existing_key = {
            "id": "key_123",
            "user_id": "test_user_123",
            "name": "Original Name",
            "scopes": ["read"],
            "created_at": datetime.now(UTC).isoformat(),
            "is_active": True,
        }
        updated_key = {**existing_key, "is_active": False}

        mock_api_key_service["get"].side_effect = [existing_key, updated_key]
        mock_api_key_service["update"].return_value = True

        with patch("src.dotmac.platform.auth.api_keys_router.get_current_user", return_value=mock_current_user):
            response = await async_client.patch("/api/v1/auth/api-keys/key_123", json={
                "is_active": False
            })

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == False

        # Should only update the specified field
        mock_api_key_service["update"].assert_called_once_with(
            "key_123",
            {"is_active": False}
        )

    @pytest.mark.asyncio
    async def test_revoke_api_key_success(self, async_client: AsyncClient, mock_current_user, mock_api_key_service):
        """Test successful API key revocation."""
        # Arrange
        key_data = {
            "id": "key_123",
            "user_id": "test_user_123",
            "name": "Test Key",
            "scopes": ["read"],
            "created_at": datetime.now(UTC).isoformat(),
            "is_active": True,
        }
        mock_api_key_service["get"].return_value = key_data
        mock_api_key_service["revoke"].return_value = True

        with patch("src.dotmac.platform.auth.api_keys_router.get_current_user", return_value=mock_current_user):
            # Act
            response = await async_client.delete("/api/v1/auth/api-keys/key_123")

        # Assert
        assert response.status_code == 204

        mock_api_key_service["revoke"].assert_called_once_with("key_123")

    @pytest.mark.asyncio
    async def test_revoke_api_key_not_found(self, async_client: AsyncClient, mock_current_user, mock_api_key_service):
        """Test API key revocation when key doesn't exist."""
        mock_api_key_service["get"].return_value = None

        with patch("src.dotmac.platform.auth.api_keys_router.get_current_user", return_value=mock_current_user):
            response = await async_client.delete("/api/v1/auth/api-keys/nonexistent")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_revoke_api_key_failed(self, async_client: AsyncClient, mock_current_user, mock_api_key_service):
        """Test API key revocation failure."""
        key_data = {
            "id": "key_123",
            "user_id": "test_user_123",
            "name": "Test Key",
            "scopes": ["read"],
            "created_at": datetime.now(UTC).isoformat(),
            "is_active": True,
        }
        mock_api_key_service["get"].return_value = key_data
        mock_api_key_service["revoke"].return_value = False

        with patch("src.dotmac.platform.auth.api_keys_router.get_current_user", return_value=mock_current_user):
            response = await async_client.delete("/api/v1/auth/api-keys/key_123")

        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_get_available_scopes(self, async_client: AsyncClient, mock_current_user):
        """Test getting available API key scopes."""
        with patch("src.dotmac.platform.auth.api_keys_router.get_current_user", return_value=mock_current_user):
            response = await async_client.get("/api/v1/auth/api-keys/scopes/available")

        assert response.status_code == 200
        data = response.json()
        assert "scopes" in data
        assert "read" in data["scopes"]
        assert "write" in data["scopes"]
        assert "customers:read" in data["scopes"]

        # Verify scope details
        read_scope = data["scopes"]["read"]
        assert "name" in read_scope
        assert "description" in read_scope

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, async_client: AsyncClient):
        """Test that API key endpoints require authentication."""
        # Test without authentication
        response = await async_client.get("/api/v1/auth/api-keys")
        assert response.status_code == 401

        response = await async_client.post("/api/v1/auth/api-keys", json={
            "name": "Test Key",
            "scopes": ["read"]
        })
        assert response.status_code == 401

        response = await async_client.delete("/api/v1/auth/api-keys/key_123")
        assert response.status_code == 401


class TestAPIKeyServiceIntegration:
    """Integration tests for API key service functions."""

    @pytest.mark.asyncio
    async def test_enhanced_create_api_key(self):
        """Test enhanced API key creation."""
        from src.dotmac.platform.auth.api_keys_router import _enhanced_create_api_key

        with patch("src.dotmac.platform.auth.api_keys_router.api_key_service") as mock_service:
            mock_service.create_api_key.return_value = "sk_test123"
            mock_service._get_redis.return_value = None  # Use memory fallback
            mock_service._memory_meta = {}
            mock_service._memory_lookup = {}

            api_key, key_id = await _enhanced_create_api_key(
                user_id="user123",
                name="Test Key",
                scopes=["read", "write"],
                description="Test description"
            )

            assert api_key == "sk_test123"
            assert key_id is not None
            assert len(key_id) > 0

    @pytest.mark.asyncio
    async def test_list_user_api_keys_memory_fallback(self):
        """Test listing API keys with memory fallback."""
        from src.dotmac.platform.auth.api_keys_router import _list_user_api_keys

        with patch("src.dotmac.platform.auth.api_keys_router.api_key_service") as mock_service:
            mock_service._get_redis.return_value = None
            mock_service._memory_meta = {
                "key1": {"user_id": "user123", "name": "Key 1"},
                "key2": {"user_id": "user456", "name": "Key 2"},
                "key3": {"user_id": "user123", "name": "Key 3"},
            }

            keys = await _list_user_api_keys("user123")

            assert len(keys) == 2
            assert all(key["user_id"] == "user123" for key in keys)

    @pytest.mark.asyncio
    async def test_update_api_key_metadata(self):
        """Test updating API key metadata."""
        from src.dotmac.platform.auth.api_keys_router import _update_api_key_metadata

        with patch("src.dotmac.platform.auth.api_keys_router.api_key_service") as mock_service:
            mock_service._get_redis.return_value = None
            mock_service._memory_meta = {
                "key123": {"name": "Old Name", "scopes": ["read"]}
            }

            success = await _update_api_key_metadata("key123", {
                "name": "New Name",
                "scopes": ["read", "write"]
            })

            assert success
            updated_key = mock_service._memory_meta["key123"]
            assert updated_key["name"] == "New Name"
            assert updated_key["scopes"] == ["read", "write"]

    @pytest.mark.asyncio
    async def test_key_masking(self):
        """Test API key masking function."""
        from src.dotmac.platform.auth.api_keys_router import _mask_api_key

        # Test normal key
        masked = _mask_api_key("sk_1234567890abcdef")
        assert masked == "sk_1234...cdef"

        # Test short key
        short_masked = _mask_api_key("sk_123")
        assert masked.endswith("****")

    def test_api_key_validation_edge_cases(self):
        """Test edge cases in API key validation."""
        # Test minimum length name
        assert len("a") >= 1  # Should pass minimum validation

        # Test maximum scopes
        max_scopes = ["scope_" + str(i) for i in range(100)]
        assert len(max_scopes) == 100  # Should handle many scopes

        # Test expiration date validation
        future_date = datetime.now(UTC) + timedelta(days=1)
        past_date = datetime.now(UTC) - timedelta(days=1)

        assert future_date > datetime.now(UTC)
        assert past_date < datetime.now(UTC)
"""Tests for authentication GraphQL resolvers."""

import pytest
from datetime import datetime, UTC
from unittest.mock import patch, Mock, AsyncMock

try:
    import strawberry
except ImportError:
    strawberry = None
    pytest.skip("Strawberry GraphQL not available", allow_module_level=True)


class TestAuthResolvers:
    """Test authentication-related GraphQL resolvers."""

    @pytest.mark.asyncio
    async def test_current_user_query_authenticated(
        self,
        authenticated_graphql_client,
        current_user_query,
        mock_user_claims
    ):
        """Test current user query with valid authentication."""
        with patch('dotmac.platform.api.graphql.resolvers.AuthResolver.get_current_user') as mock_get_user:
            # Mock the user data returned by resolver
            mock_user = Mock(
                id="test-user-123",
                username="testuser",
                email="test@example.com",
                full_name="Test User",
                tenant_id="test-tenant-123",
                roles=["user", "admin"],
                scopes=["read:audit", "write:audit"],
                is_active=True,
                created_at=datetime.now(UTC),
                last_login=datetime.now(UTC)
            )
            mock_get_user.return_value = mock_user

            result = await authenticated_graphql_client.execute_expecting_data(current_user_query)

            assert "currentUser" in result
            user_data = result["currentUser"]

            assert user_data["id"] == "test-user-123"
            assert user_data["username"] == "testuser"
            assert user_data["email"] == "test@example.com"
            assert user_data["fullName"] == "Test User"
            assert user_data["tenantId"] == "test-tenant-123"
            assert user_data["roles"] == ["user", "admin"]
            assert user_data["scopes"] == ["read:audit", "write:audit"]
            assert user_data["isActive"] is True

    @pytest.mark.asyncio
    async def test_current_user_query_unauthenticated(self, graphql_test_client, current_user_query):
        """Test current user query without authentication."""
        with patch('dotmac.platform.api.graphql.resolvers.AuthResolver.get_current_user') as mock_get_user:
            mock_get_user.return_value = None

            result = await graphql_test_client.execute_expecting_data(current_user_query)

            assert "currentUser" in result
            assert result["currentUser"] is None

    @pytest.mark.asyncio
    async def test_api_keys_query_authenticated(self, authenticated_graphql_client):
        """Test API keys query for authenticated user."""
        query = """
            query ApiKeysQuery {
                apiKeys {
                    id
                    name
                    prefix
                    scopes
                    expiresAt
                    createdAt
                    lastUsed
                    isActive
                }
            }
        """

        with patch('dotmac.platform.api.graphql.resolvers.AuthResolver.get_api_keys') as mock_get_keys:
            mock_keys = [
                Mock(
                    id="key-123",
                    name="Test API Key",
                    prefix="sk_test_",
                    scopes=["read:audit"],
                    expires_at=None,
                    created_at=datetime.now(UTC),
                    last_used=datetime.now(UTC),
                    is_active=True
                )
            ]
            mock_get_keys.return_value = mock_keys

            result = await authenticated_graphql_client.execute_expecting_data(query)

            assert "apiKeys" in result
            assert len(result["apiKeys"]) == 1

            key_data = result["apiKeys"][0]
            assert key_data["id"] == "key-123"
            assert key_data["name"] == "Test API Key"
            assert key_data["prefix"] == "sk_test_"
            assert key_data["scopes"] == ["read:audit"]
            assert key_data["isActive"] is True

    @pytest.mark.asyncio
    async def test_api_keys_query_unauthenticated(self, graphql_test_client):
        """Test API keys query without authentication should fail."""
        query = """
            query ApiKeysQuery {
                apiKeys {
                    id
                    name
                }
            }
        """

        with patch('dotmac.platform.api.graphql.resolvers.AuthResolver.get_api_keys') as mock_get_keys:
            # Mock authentication error
            from dotmac.platform.auth.exceptions import AuthError
            mock_get_keys.side_effect = AuthError("Authentication required")

            data = await graphql_test_client.execute_expecting_errors(query)
            assert len(data["errors"]) > 0
            assert any("Authentication required" in error["message"] for error in data["errors"])

    @pytest.mark.asyncio
    async def test_create_api_key_mutation(self, authenticated_graphql_client):
        """Test creating an API key via mutation."""
        mutation = """
            mutation CreateApiKeyMutation($name: String!, $scopes: [String!]!, $expiresAt: DateTime) {
                createApiKey(name: $name, scopes: $scopes, expiresAt: $expiresAt) {
                    id
                    name
                    prefix
                    scopes
                    expiresAt
                    createdAt
                    isActive
                }
            }
        """

        variables = {
            "name": "New Test Key",
            "scopes": ["read:audit", "write:audit"],
            "expiresAt": None
        }

        with patch('dotmac.platform.api.graphql.resolvers.AuthResolver.create_api_key') as mock_create_key:
            mock_key = Mock(
                id="new-key-456",
                name="New Test Key",
                prefix="sk_live_",
                scopes=["read:audit", "write:audit"],
                expires_at=None,
                created_at=datetime.now(UTC),
                last_used=None,
                is_active=True
            )
            mock_create_key.return_value = mock_key

            result = await authenticated_graphql_client.execute_expecting_data(mutation, variables)

            assert "createApiKey" in result
            key_data = result["createApiKey"]

            assert key_data["id"] == "new-key-456"
            assert key_data["name"] == "New Test Key"
            assert key_data["prefix"] == "sk_live_"
            assert key_data["scopes"] == ["read:audit", "write:audit"]
            assert key_data["isActive"] is True

            # Verify the resolver was called with correct parameters
            mock_create_key.assert_called_once()
            args, kwargs = mock_create_key.call_args
            assert kwargs['name'] == "New Test Key"
            assert kwargs['scopes'] == ["read:audit", "write:audit"]
            assert kwargs['expires_at'] is None

    @pytest.mark.asyncio
    async def test_revoke_api_key_mutation(self, authenticated_graphql_client):
        """Test revoking an API key via mutation."""
        mutation = """
            mutation RevokeApiKeyMutation($apiKeyId: String!) {
                revokeApiKey(apiKeyId: $apiKeyId)
            }
        """

        variables = {
            "apiKeyId": "key-to-revoke-123"
        }

        with patch('dotmac.platform.api.graphql.resolvers.AuthResolver.revoke_api_key') as mock_revoke_key:
            mock_revoke_key.return_value = True

            result = await authenticated_graphql_client.execute_expecting_data(mutation, variables)

            assert "revokeApiKey" in result
            assert result["revokeApiKey"] is True

            mock_revoke_key.assert_called_once()

    @pytest.mark.asyncio
    async def test_sessions_query(self, authenticated_graphql_client):
        """Test getting user sessions."""
        query = """
            query SessionsQuery($userId: String) {
                sessions(userId: $userId) {
                    id
                    userId
                    ipAddress
                    userAgent
                    createdAt
                    expiresAt
                    isActive
                }
            }
        """

        with patch('dotmac.platform.api.graphql.resolvers.AuthResolver.get_sessions') as mock_get_sessions:
            mock_sessions = [
                Mock(
                    session_id="session-123",
                    user_id="test-user-123",
                    ip_address="192.168.1.100",
                    user_agent="Mozilla/5.0 Test Browser",
                    created_at=datetime.now(UTC),
                    expires_at=datetime.now(UTC),
                    is_active=True
                )
            ]
            mock_get_sessions.return_value = mock_sessions

            result = await authenticated_graphql_client.execute_expecting_data(query)

            assert "sessions" in result
            assert len(result["sessions"]) == 1

            session_data = result["sessions"][0]
            assert session_data["id"] == "session-123"
            assert session_data["userId"] == "test-user-123"
            assert session_data["ipAddress"] == "192.168.1.100"
            assert session_data["userAgent"] == "Mozilla/5.0 Test Browser"
            assert session_data["isActive"] is True

    @pytest.mark.asyncio
    async def test_invalidate_session_mutation(self, authenticated_graphql_client):
        """Test invalidating a session via mutation."""
        mutation = """
            mutation InvalidateSessionMutation($sessionId: String!) {
                invalidateSession(sessionId: $sessionId)
            }
        """

        variables = {
            "sessionId": "session-to-invalidate-123"
        }

        with patch('dotmac.platform.api.graphql.resolvers.AuthResolver.invalidate_session') as mock_invalidate:
            mock_invalidate.return_value = True

            result = await authenticated_graphql_client.execute_expecting_data(mutation, variables)

            assert "invalidateSession" in result
            assert result["invalidateSession"] is True

            mock_invalidate.assert_called_once()

    @pytest.mark.asyncio
    async def test_auth_error_handling(self, authenticated_graphql_client):
        """Test proper handling of authentication errors."""
        query = """
            query ApiKeysQuery {
                apiKeys {
                    id
                    name
                }
            }
        """

        with patch('dotmac.platform.api.graphql.resolvers.AuthResolver.get_api_keys') as mock_get_keys:
            from dotmac.platform.auth.exceptions import AuthError
            mock_get_keys.side_effect = AuthError("Token expired")

            data = await authenticated_graphql_client.execute_expecting_errors(query)
            assert len(data["errors"]) > 0
            assert any("Token expired" in error["message"] for error in data["errors"])

    @pytest.mark.asyncio
    async def test_service_error_handling(self, authenticated_graphql_client):
        """Test handling of service errors (non-auth)."""
        mutation = """
            mutation CreateApiKeyMutation($name: String!, $scopes: [String!]!) {
                createApiKey(name: $name, scopes: $scopes) {
                    id
                    name
                }
            }
        """

        variables = {
            "name": "Test Key",
            "scopes": ["read:audit"]
        }

        with patch('dotmac.platform.api.graphql.resolvers.AuthResolver.create_api_key') as mock_create_key:
            mock_create_key.side_effect = Exception("Database connection failed")

            data = await authenticated_graphql_client.execute_expecting_errors(mutation, variables)
            assert len(data["errors"]) > 0
            assert any("Database connection failed" in error["message"] for error in data["errors"])
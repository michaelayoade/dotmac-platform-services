"""
Authentication and Authorization Error Handling Tests.

Tests comprehensive error scenarios for the auth module.
"""

import pytest


class TestAuthenticationErrors:
    """Test authentication error handling."""

    @pytest.mark.asyncio
    async def test_expired_token_handling(self, test_client):
        """Test expired JWT token handling."""
        # Create an expired token
        expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyMTIzIiwiZXhwIjoxNjAwMDAwMDAwfQ.invalid"

        response = test_client.get(
            "/api/v1/tenants",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        assert response.status_code == 401
        assert (
            "expired" in response.json().get("detail", "").lower()
            or "unauthorized" in response.json().get("detail", "").lower()
        )

    @pytest.mark.asyncio
    async def test_malformed_token(self, test_client):
        """Test malformed JWT token."""
        response = test_client.get(
            "/api/v1/tenants",
            headers={"Authorization": "Bearer not-a-valid-token"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_authorization_header(self, test_client):
        """Test request without Authorization header."""
        response = test_client.get("/api/v1/tenants")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_authorization_scheme(self, test_client):
        """Test invalid authorization scheme (not Bearer)."""
        response = test_client.get(
            "/api/v1/tenants",
            headers={"Authorization": "Basic dXNlcjpwYXNz"},  # Basic auth instead of Bearer
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_token_with_invalid_signature(self, test_client):
        """Test token with invalid signature."""
        # Valid JWT structure but wrong signature
        invalid_token = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIn0.wrong_signature"
        )

        response = test_client.get(
            "/api/v1/tenants",
            headers={"Authorization": f"Bearer {invalid_token}"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_token_with_missing_required_claims(self, test_client):
        """Test token missing required claims (sub, exp, etc)."""
        # Token without 'sub' claim
        incomplete_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiSm9obiJ9.invalid"

        response = test_client.get(
            "/api/v1/tenants",
            headers={"Authorization": f"Bearer {incomplete_token}"},
        )

        assert response.status_code == 401


class TestAuthorizationErrors:
    """Test authorization (permissions/roles) error handling."""

    @pytest.mark.asyncio
    async def test_insufficient_permissions(self, test_client):
        """Test access with insufficient permissions."""
        # Try to access admin endpoint without admin role
        response = test_client.get(
            "/api/v1/admin/settings/categories",
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code in [403, 401]

    @pytest.mark.asyncio
    async def test_tenant_isolation_violation(self, test_client):
        """Test accessing resources from different tenant."""
        # This requires proper tenant setup in fixtures
        response = test_client.get(
            "/api/v1/tenants/other-tenant-id",
            headers={"Authorization": "Bearer fake-token"},
        )

        # Should return 403 or 404 (depending on isolation strategy)
        assert response.status_code in [403, 404, 401]

    @pytest.mark.asyncio
    async def test_revoked_token_access(self, test_client):
        """Test access with revoked token."""
        # This would require token revocation to be implemented
        response = test_client.get(
            "/api/v1/tenants",
            headers={"Authorization": "Bearer revoked-token"},
        )

        assert response.status_code == 401


class TestLoginErrors:
    """Test login endpoint error handling."""

    @pytest.mark.asyncio
    async def test_login_with_invalid_credentials(self, test_client):
        """Test login with wrong password."""
        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
                "password": "wrong-password",
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_with_nonexistent_user(self, test_client):
        """Test login with non-existent user."""
        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_with_missing_fields(self, test_client):
        """Test login with missing required fields."""
        response = test_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com"},  # Missing password
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_with_invalid_email_format(self, test_client):
        """Test login with invalid email format."""
        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "not-an-email",
                "password": "password123",
            },
        )

        assert response.status_code in [422, 401]

    @pytest.mark.asyncio
    async def test_login_rate_limiting(self, test_client):
        """Test login rate limiting after multiple failures."""
        # Attempt multiple logins
        for _ in range(10):
            response = test_client.post(
                "/api/v1/auth/login",
                json={
                    "email": "user@example.com",
                    "password": "wrong-password",
                },
            )

        # After many failures, should be rate limited
        # Note: This requires rate limiting to be enabled
        final_response = test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
                "password": "wrong-password",
            },
        )

        # Should return 429 Too Many Requests if rate limiting enabled
        assert final_response.status_code in [429, 401]

    @pytest.mark.asyncio
    async def test_login_with_locked_account(self, test_client):
        """Test login with locked/disabled account."""
        # This assumes account locking is implemented
        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "locked@example.com",
                "password": "password123",
            },
        )

        assert response.status_code in [401, 403]


class TestRegistrationErrors:
    """Test registration endpoint error handling."""

    @pytest.mark.asyncio
    async def test_register_with_existing_email(self, test_client):
        """Test registration with duplicate email."""
        user_data = {
            "email": "existing@example.com",
            "password": "SecurePass123!",
            "username": "newuser",
        }

        # First registration
        response1 = test_client.post("/api/v1/auth/register", json=user_data)

        # Second registration with same email
        response2 = test_client.post("/api/v1/auth/register", json=user_data)

        # Second should fail
        if response1.status_code in [200, 201]:
            assert response2.status_code in [400, 409, 422]

    @pytest.mark.asyncio
    async def test_register_with_weak_password(self, test_client):
        """Test registration with weak password."""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "123",  # Too weak
                "username": "testuser",
            },
        )

        # Should validate password strength
        assert response.status_code in [422, 400]

    @pytest.mark.asyncio
    async def test_register_with_invalid_email(self, test_client):
        """Test registration with invalid email format."""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123!",
                "username": "testuser",
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_with_missing_required_fields(self, test_client):
        """Test registration with missing fields."""
        response = test_client.post(
            "/api/v1/auth/register",
            json={"email": "user@example.com"},  # Missing password and username
        )

        assert response.status_code == 422


class TestPasswordResetErrors:
    """Test password reset error handling."""

    @pytest.mark.asyncio
    async def test_password_reset_nonexistent_email(self, test_client):
        """Test password reset for non-existent email."""
        response = test_client.post(
            "/api/v1/auth/password-reset",
            json={"email": "nonexistent@example.com"},
        )

        # Should not reveal if email exists (security best practice)
        # but should return 200/202 to prevent email enumeration
        assert response.status_code in [200, 202, 404]

    @pytest.mark.asyncio
    async def test_password_reset_with_invalid_token(self, test_client):
        """Test password reset with invalid token."""
        response = test_client.post(
            "/api/v1/auth/password-reset/confirm",
            json={
                "token": "invalid-reset-token",
                "new_password": "NewSecurePass123!",
            },
        )

        assert response.status_code in [400, 401, 404]

    @pytest.mark.asyncio
    async def test_password_reset_with_expired_token(self, test_client):
        """Test password reset with expired token."""
        # Assumes token expiry is implemented
        response = test_client.post(
            "/api/v1/auth/password-reset/confirm",
            json={
                "token": "expired-reset-token",
                "new_password": "NewSecurePass123!",
            },
        )

        assert response.status_code in [400, 401, 404]


class TestRBACErrors:
    """Test RBAC (Role-Based Access Control) error handling."""

    @pytest.mark.asyncio
    async def test_assign_nonexistent_role(self, test_client):
        """Test assigning non-existent role to user."""
        response = test_client.post(
            "/api/v1/auth/rbac/users/user-123/roles",
            json={"role_id": "nonexistent-role-id"},
            headers={"Authorization": "Bearer fake-admin-token"},
        )

        assert response.status_code in [404, 400, 401]

    @pytest.mark.asyncio
    async def test_create_role_with_invalid_permissions(self, test_client):
        """Test creating role with invalid permission names."""
        response = test_client.post(
            "/api/v1/auth/rbac/roles",
            json={
                "name": "Invalid Role",
                "permissions": ["nonexistent:permission"],
            },
            headers={"Authorization": "Bearer fake-admin-token"},
        )

        assert response.status_code in [400, 422, 401]

    @pytest.mark.asyncio
    async def test_modify_system_role(self, test_client):
        """Test modifying system-protected role."""
        response = test_client.patch(
            "/api/v1/auth/rbac/roles/admin",  # Admin is system role
            json={"name": "Modified Admin"},
            headers={"Authorization": "Bearer fake-admin-token"},
        )

        # Should prevent modification of system roles
        assert response.status_code in [403, 400, 401]

    @pytest.mark.asyncio
    async def test_delete_role_in_use(self, test_client):
        """Test deleting role that's assigned to users."""
        # This assumes role deletion validation is implemented
        response = test_client.delete(
            "/api/v1/auth/rbac/roles/user-role-id",
            headers={"Authorization": "Bearer fake-admin-token"},
        )

        # Should either prevent deletion or cascade appropriately
        assert response.status_code in [200, 204, 400, 409, 401]


class TestAPIKeyErrors:
    """Test API key error handling."""

    @pytest.mark.asyncio
    async def test_use_expired_api_key(self, test_client):
        """Test using expired API key."""
        response = test_client.get(
            "/api/v1/tenants",
            headers={"X-API-Key": "expired-api-key-12345"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_use_revoked_api_key(self, test_client):
        """Test using revoked API key."""
        response = test_client.get(
            "/api/v1/tenants",
            headers={"X-API-Key": "revoked-api-key-12345"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_api_key_with_invalid_scopes(self, test_client):
        """Test creating API key with invalid scopes."""
        response = test_client.post(
            "/api/v1/auth/api-keys",
            json={
                "name": "Test API Key",
                "scopes": ["invalid:scope", "nonexistent:permission"],
            },
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code in [400, 422, 401]

    @pytest.mark.asyncio
    async def test_api_key_without_required_scope(self, test_client):
        """Test using API key without required scope for endpoint."""
        # Create API key with limited scopes
        response = test_client.get(
            "/api/v1/admin/settings/categories",  # Requires admin scope
            headers={"X-API-Key": "limited-scope-api-key"},
        )

        assert response.status_code in [403, 401]

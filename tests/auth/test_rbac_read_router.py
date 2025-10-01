"""Tests for RBAC read-only endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.models import Role, Permission
from dotmac.platform.user_management.models import User
from dotmac.platform.auth.core import JWTService


@pytest.fixture
async def test_user_with_roles(async_session: AsyncSession):
    """Create a test user with roles and permissions."""
    # Create test user
    user = User(
        email="rbac_test@example.com",
        username="rbac_test",
        hashed_password="hashed_test",
        is_active=True,
        is_superuser=False
    )
    async_session.add(user)

    # Create roles
    admin_role = Role(
        name="admin",
        display_name="Administrator",
        description="Full system access",
        is_system=True,
        is_active=True
    )

    viewer_role = Role(
        name="viewer",
        display_name="Viewer",
        description="Read-only access",
        is_system=False,
        is_active=True
    )

    inactive_role = Role(
        name="deprecated",
        display_name="Deprecated Role",
        description="No longer used",
        is_system=False,
        is_active=False
    )

    async_session.add_all([admin_role, viewer_role, inactive_role])

    # Create permissions
    read_perm = Permission(
        name="user.profile.read",
        display_name="Read User Profile",
        description="Can read user profiles"
    )

    write_perm = Permission(
        name="user.profile.write",
        display_name="Write User Profile",
        description="Can modify user profiles"
    )

    async_session.add_all([read_perm, write_perm])

    await async_session.commit()
    await async_session.refresh(user)

    return user, [admin_role, viewer_role], [read_perm, write_perm]


@pytest.fixture
async def auth_headers(test_user_with_roles):
    """Create auth headers with roles and permissions."""
    user, roles, permissions = test_user_with_roles

    # Create JWT service
    jwt_service = JWTService(secret="test-secret")

    # Create token with roles and permissions
    token = jwt_service.create_access_token(
        subject=str(user.id),
        additional_claims={
            "email": user.email,
            "roles": ["admin", "viewer"],
            "permissions": ["user.profile.read", "user.profile.write"]
        }
    )

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def superuser_headers(async_session: AsyncSession):
    """Create auth headers for a superuser."""
    # Create superuser
    superuser = User(
        email="super@example.com",
        username="superuser",
        hashed_password="hashed_test",
        is_active=True,
        is_superuser=True
    )
    async_session.add(superuser)
    await async_session.commit()
    await async_session.refresh(superuser)

    # Create JWT service
    jwt_service = JWTService(secret="test-secret")

    token = jwt_service.create_access_token(
        subject=str(superuser.id),
        additional_claims={
            "email": superuser.email,
            "roles": ["superuser"],
            "permissions": []
        }
    )

    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
class TestRBACReadEndpoints:
    """Test RBAC read-only endpoints."""

    async def test_get_my_permissions(self, async_client: AsyncClient, auth_headers: dict):
        """Test getting current user's permissions."""
        response = await async_client.get(
            "/api/v1/auth/rbac/my-permissions",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "user_id" in data
        assert "roles" in data
        assert "direct_permissions" in data
        assert "effective_permissions" in data
        assert "is_superuser" in data

        # Check roles
        assert len(data["roles"]) == 2
        role_names = [r["name"] for r in data["roles"]]
        assert "admin" in role_names
        assert "viewer" in role_names

        # Check permissions
        assert len(data["direct_permissions"]) == 2
        perm_names = [p["name"] for p in data["direct_permissions"]]
        assert "user.profile.read" in perm_names
        assert "user.profile.write" in perm_names

        # Check permission details
        read_perm = next(p for p in data["direct_permissions"] if p["name"] == "user.profile.read")
        assert read_perm["category"] == "user"
        assert read_perm["resource"] == "profile"
        assert read_perm["action"] == "read"

        # Not a superuser
        assert data["is_superuser"] is False

    async def test_get_my_permissions_superuser(self, async_client: AsyncClient, superuser_headers: dict):
        """Test getting superuser's permissions."""
        response = await async_client.get(
            "/api/v1/auth/rbac/my-permissions",
            headers=superuser_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Check superuser flag
        assert data["is_superuser"] is True

        # Check roles
        role_names = [r["name"] for r in data["roles"]]
        assert "superuser" in role_names

    async def test_get_roles_authenticated(self, async_client: AsyncClient, auth_headers: dict):
        """Test getting available roles."""
        response = await async_client.get(
            "/api/v1/auth/rbac/roles",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should return active roles only by default
        assert len(data) >= 2  # At least admin and viewer

        role_names = [r["name"] for r in data]
        assert "admin" in role_names
        assert "viewer" in role_names
        assert "deprecated" not in role_names  # Inactive role not included

        # Check role details
        admin_role = next(r for r in data if r["name"] == "admin")
        assert admin_role["display_name"] == "Administrator"
        assert admin_role["description"] == "Full system access"
        assert admin_role["is_active"] is True

    async def test_get_roles_include_inactive(self, async_client: AsyncClient, auth_headers: dict):
        """Test getting all roles including inactive."""
        response = await async_client.get(
            "/api/v1/auth/rbac/roles?active_only=false",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should include inactive roles
        role_names = [r["name"] for r in data]
        assert "deprecated" in role_names

        # Check inactive role
        deprecated = next(r for r in data if r["name"] == "deprecated")
        assert deprecated["is_active"] is False

    async def test_get_my_roles(self, async_client: AsyncClient, auth_headers: dict):
        """Test getting current user's roles only."""
        response = await async_client.get(
            "/api/v1/auth/rbac/my-roles",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should return list of role names
        assert isinstance(data, list)
        assert len(data) == 2
        assert "admin" in data
        assert "viewer" in data

    async def test_endpoints_require_auth(self, async_client: AsyncClient):
        """Test that all endpoints require authentication."""
        endpoints = [
            "/api/v1/auth/rbac/my-permissions",
            "/api/v1/auth/rbac/roles",
            "/api/v1/auth/rbac/my-roles"
        ]

        for endpoint in endpoints:
            response = await async_client.get(endpoint)
            assert response.status_code == 401

    async def test_my_permissions_handles_missing_user_data(self, async_client: AsyncClient):
        """Test my-permissions handles user with no roles/permissions."""
        # Create JWT service
        jwt_service = JWTService(secret="test-secret")

        # Create token with minimal data
        token = jwt_service.create_access_token(
            subject="test-user-123",
            additional_claims={
                "email": "minimal@example.com"
            }
        )

        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.get(
            "/api/v1/auth/rbac/my-permissions",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should handle empty roles/permissions
        assert data["roles"] == []
        assert data["direct_permissions"] == []
        assert data["effective_permissions"] == []
        assert data["is_superuser"] is False

    async def test_role_info_structure(self, async_client: AsyncClient, auth_headers: dict):
        """Test that RoleInfo has expected structure for frontend."""
        response = await async_client.get(
            "/api/v1/auth/rbac/roles",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Check each role has expected fields
        for role in data:
            assert "name" in role
            assert "display_name" in role
            assert "description" in role
            assert "is_active" in role
            # parent_role is optional in response but should be present
            assert "parent_role" in role or role.get("parent_role") == ""

    async def test_permission_info_structure(self, async_client: AsyncClient, auth_headers: dict):
        """Test that PermissionInfo has expected structure for frontend."""
        response = await async_client.get(
            "/api/v1/auth/rbac/my-permissions",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Check each permission has expected fields
        for perm in data["direct_permissions"]:
            assert "name" in perm
            assert "display_name" in perm
            assert "description" in perm
            assert "category" in perm
            assert "resource" in perm
            assert "action" in perm
            assert "is_system" in perm
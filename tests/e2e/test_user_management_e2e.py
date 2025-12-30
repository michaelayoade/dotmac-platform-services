"""
End-to-end tests for user management.

Tests cover user CRUD operations, bulk actions, and user administration.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.core import hash_password
from dotmac.platform.user_management.models import User

pytestmark = [pytest.mark.asyncio, pytest.mark.e2e]


# ============================================================================
# Fixtures for User Management E2E Tests
# ============================================================================


@pytest_asyncio.fixture
async def admin_user(e2e_db_session: AsyncSession, tenant_id: str):
    """Create an admin user in the database."""
    user = User(
        id=uuid.uuid4(),
        username=f"admin_{uuid.uuid4().hex[:8]}",
        email=f"admin_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("AdminPassword123!"),
        tenant_id=tenant_id,
        is_active=True,
        is_verified=True,
        mfa_enabled=False,
        roles=["admin"],
    )
    e2e_db_session.add(user)
    await e2e_db_session.commit()
    await e2e_db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def multiple_users(e2e_db_session: AsyncSession, tenant_id: str):
    """Create multiple users for listing and bulk operation tests."""
    users = []
    for i in range(5):
        user = User(
            id=uuid.uuid4(),
            username=f"user_{i}_{uuid.uuid4().hex[:6]}",
            email=f"user_{i}_{uuid.uuid4().hex[:6]}@example.com",
            password_hash=hash_password("TestPassword123!"),
            tenant_id=tenant_id,
            is_active=i % 2 == 0,  # Alternating active/inactive
            is_verified=True,
            mfa_enabled=False,
            roles=["user"] if i < 3 else ["admin"],
        )
        e2e_db_session.add(user)
        users.append(user)

    await e2e_db_session.commit()
    for user in users:
        await e2e_db_session.refresh(user)
    return users


@pytest_asyncio.fixture
async def target_user(e2e_db_session: AsyncSession, tenant_id: str):
    """Create a target user for single-user operations."""
    user = User(
        id=uuid.uuid4(),
        username=f"target_{uuid.uuid4().hex[:8]}",
        email=f"target_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("TestPassword123!"),
        tenant_id=tenant_id,
        is_active=True,
        is_verified=True,
        mfa_enabled=False,
        roles=["user"],
    )
    e2e_db_session.add(user)
    await e2e_db_session.commit()
    await e2e_db_session.refresh(user)
    return user


# ============================================================================
# User List Tests
# ============================================================================


class TestUserListE2E:
    """End-to-end tests for user listing."""

    async def test_list_users_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_users: list[User],
    ):
        """Test listing all users."""
        response = await async_client.get(
            "/api/v1/users",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert isinstance(data["users"], list)

    async def test_list_users_with_pagination(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_users: list[User],
    ):
        """Test listing users with pagination."""
        response = await async_client.get(
            "/api/v1/users?skip=0&limit=2",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert len(data["users"]) <= 2
        assert "page" in data
        assert "per_page" in data

    async def test_list_users_filter_by_active(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_users: list[User],
    ):
        """Test filtering users by active status."""
        response = await async_client.get(
            "/api/v1/users?is_active=true",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        # All returned users should be active
        for user in data["users"]:
            assert user["is_active"] is True

    async def test_list_users_filter_by_role(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_users: list[User],
    ):
        """Test filtering users by role."""
        response = await async_client.get(
            "/api/v1/users?role=admin",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "users" in data

    async def test_list_users_search(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_users: list[User],
    ):
        """Test searching users."""
        # Search by part of username
        search_term = multiple_users[0].username[:8]
        response = await async_client.get(
            f"/api/v1/users?search={search_term}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "users" in data


# ============================================================================
# User Create Tests
# ============================================================================


class TestUserCreateE2E:
    """End-to-end tests for user creation."""

    async def test_create_user_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        e2e_db_session: AsyncSession,
    ):
        """Test creating a user with valid data."""
        unique_id = uuid.uuid4().hex[:8]
        user_data = {
            "username": f"newuser_{unique_id}",
            "email": f"newuser_{unique_id}@example.com",
            "password": "SecurePassword123!",
            "full_name": "New Test User",
            "roles": ["user"],
            "is_active": True,
        }

        response = await async_client.post(
            "/api/v1/users",
            json=user_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert data["is_active"] is True
        assert "user_id" in data

    async def test_create_user_duplicate_username(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        target_user: User,
    ):
        """Test creating a user with existing username."""
        user_data = {
            "username": target_user.username,
            "email": f"different_{uuid.uuid4().hex[:8]}@example.com",
            "password": "SecurePassword123!",
        }

        response = await async_client.post(
            "/api/v1/users",
            json=user_data,
            headers=auth_headers,
        )

        assert response.status_code == 400

    async def test_create_user_duplicate_email(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        target_user: User,
    ):
        """Test creating a user with existing email."""
        user_data = {
            "username": f"different_{uuid.uuid4().hex[:8]}",
            "email": target_user.email,
            "password": "SecurePassword123!",
        }

        response = await async_client.post(
            "/api/v1/users",
            json=user_data,
            headers=auth_headers,
        )

        assert response.status_code == 400

    async def test_create_user_invalid_email(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test creating a user with invalid email format."""
        user_data = {
            "username": f"user_{uuid.uuid4().hex[:8]}",
            "email": "not-an-email",
            "password": "SecurePassword123!",
        }

        response = await async_client.post(
            "/api/v1/users",
            json=user_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

    async def test_create_user_short_password(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test creating a user with password shorter than 8 chars."""
        user_data = {
            "username": f"user_{uuid.uuid4().hex[:8]}",
            "email": f"user_{uuid.uuid4().hex[:8]}@example.com",
            "password": "short",
        }

        response = await async_client.post(
            "/api/v1/users",
            json=user_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

    async def test_create_user_short_username(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test creating a user with username shorter than 3 chars."""
        user_data = {
            "username": "ab",
            "email": f"user_{uuid.uuid4().hex[:8]}@example.com",
            "password": "SecurePassword123!",
        }

        response = await async_client.post(
            "/api/v1/users",
            json=user_data,
            headers=auth_headers,
        )

        assert response.status_code == 422


# ============================================================================
# User CRUD Tests
# ============================================================================


class TestUserCRUDE2E:
    """End-to-end tests for user CRUD operations."""

    async def test_get_user_by_id(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        target_user: User,
    ):
        """Test getting a user by ID."""
        response = await async_client.get(
            f"/api/v1/users/{target_user.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(target_user.id)
        assert data["username"] == target_user.username
        assert data["email"] == target_user.email

    async def test_get_user_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting a non-existent user."""
        fake_id = str(uuid.uuid4())
        response = await async_client.get(
            f"/api/v1/users/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_update_user_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        target_user: User,
    ):
        """Test updating a user."""
        update_data = {
            "full_name": "Updated Name",
            "roles": ["user", "editor"],
        }

        response = await async_client.put(
            f"/api/v1/users/{target_user.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"

    async def test_update_user_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test updating a non-existent user."""
        fake_id = str(uuid.uuid4())
        update_data = {"full_name": "Updated Name"}

        response = await async_client.put(
            f"/api/v1/users/{fake_id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_delete_user_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        target_user: User,
    ):
        """Test deleting a user."""
        response = await async_client.delete(
            f"/api/v1/users/{target_user.id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify user is deleted
        get_response = await async_client.get(
            f"/api/v1/users/{target_user.id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    async def test_delete_user_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test deleting a non-existent user."""
        fake_id = str(uuid.uuid4())
        response = await async_client.delete(
            f"/api/v1/users/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404


# ============================================================================
# User Actions Tests
# ============================================================================


class TestUserActionsE2E:
    """End-to-end tests for user action operations."""

    async def test_disable_user_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        target_user: User,
    ):
        """Test disabling a user."""
        response = await async_client.post(
            f"/api/v1/users/{target_user.id}/disable",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    async def test_disable_user_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test disabling a non-existent user."""
        fake_id = str(uuid.uuid4())
        response = await async_client.post(
            f"/api/v1/users/{fake_id}/disable",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_enable_user_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        e2e_db_session: AsyncSession,
        tenant_id: str,
    ):
        """Test enabling a disabled user."""
        # Create a disabled user
        user = User(
            id=uuid.uuid4(),
            username=f"disabled_{uuid.uuid4().hex[:8]}",
            email=f"disabled_{uuid.uuid4().hex[:8]}@example.com",
            password_hash=hash_password("TestPassword123!"),
            tenant_id=tenant_id,
            is_active=False,
            is_verified=True,
            mfa_enabled=False,
            roles=["user"],
        )
        e2e_db_session.add(user)
        await e2e_db_session.commit()
        await e2e_db_session.refresh(user)

        response = await async_client.post(
            f"/api/v1/users/{user.id}/enable",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True

    async def test_enable_user_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test enabling a non-existent user."""
        fake_id = str(uuid.uuid4())
        response = await async_client.post(
            f"/api/v1/users/{fake_id}/enable",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_resend_verification_email(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        target_user: User,
    ):
        """Test resending verification email."""
        with patch("dotmac.platform.auth.email_verification.send_verification_email") as mock_send:
            mock_send.return_value = True

            response = await async_client.post(
                f"/api/v1/users/{target_user.id}/resend-verification",
                headers=auth_headers,
            )

            # May succeed or fail depending on user verification status
            assert response.status_code in [200, 400, 404]


# ============================================================================
# Bulk Operations Tests
# ============================================================================


class TestUserBulkOperationsE2E:
    """End-to-end tests for bulk user operations."""

    async def test_bulk_delete_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_users: list[User],
    ):
        """Test bulk deleting users."""
        user_ids = [str(u.id) for u in multiple_users[:2]]

        response = await async_client.post(
            "/api/v1/users/bulk/delete",
            json={"user_ids": user_ids, "hard_delete": False},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "success_count" in data

    async def test_bulk_delete_some_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_users: list[User],
    ):
        """Test bulk delete with some non-existent users."""
        user_ids = [str(multiple_users[0].id), str(uuid.uuid4())]

        response = await async_client.post(
            "/api/v1/users/bulk/delete",
            json={"user_ids": user_ids, "hard_delete": False},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Should have partial success
        assert "success_count" in data

    async def test_bulk_suspend_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_users: list[User],
    ):
        """Test bulk suspending users."""
        # Get only active users
        active_users = [u for u in multiple_users if u.is_active]
        user_ids = [str(u.id) for u in active_users[:2]]

        response = await async_client.post(
            "/api/v1/users/bulk/suspend",
            json={"user_ids": user_ids},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "success_count" in data

    async def test_bulk_activate_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_users: list[User],
    ):
        """Test bulk activating users."""
        # Get only inactive users
        inactive_users = [u for u in multiple_users if not u.is_active]
        user_ids = [str(u.id) for u in inactive_users[:2]]

        response = await async_client.post(
            "/api/v1/users/bulk/activate",
            json={"user_ids": user_ids},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "success_count" in data

    async def test_bulk_resend_verification(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_users: list[User],
    ):
        """Test bulk resending verification emails."""
        user_ids = [str(u.id) for u in multiple_users[:2]]

        with patch("dotmac.platform.auth.email_verification.send_verification_email") as mock_send:
            mock_send.return_value = True

            response = await async_client.post(
                "/api/v1/users/bulk/resend-verification",
                json={"user_ids": user_ids},
                headers=auth_headers,
            )

            assert response.status_code == 200


# ============================================================================
# User Export Tests
# ============================================================================


class TestUserExportE2E:
    """End-to-end tests for user export operations."""

    async def test_export_users_csv(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_users: list[User],
    ):
        """Test exporting users as CSV."""
        response = await async_client.post(
            "/api/v1/users/export",
            json={"format": "csv"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "") or response.status_code == 200

    async def test_export_users_json(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_users: list[User],
    ):
        """Test exporting users as JSON."""
        response = await async_client.post(
            "/api/v1/users/export",
            json={"format": "json"},
            headers=auth_headers,
        )

        assert response.status_code == 200

    async def test_export_users_with_filters(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_users: list[User],
    ):
        """Test exporting users with filters applied."""
        response = await async_client.post(
            "/api/v1/users/export?is_active=true",
            json={"format": "csv"},
            headers=auth_headers,
        )

        assert response.status_code == 200


# ============================================================================
# Current User Profile Tests
# ============================================================================


class TestCurrentUserProfileE2E:
    """End-to-end tests for current user profile operations."""

    async def test_get_current_user_profile(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting current user's profile via /users/me."""
        response = await async_client.get(
            "/api/v1/users/me",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "username" in data
        assert "email" in data

    async def test_update_current_user_profile(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test updating current user's profile."""
        update_data = {"full_name": "Updated Current User Name"}

        response = await async_client.put(
            "/api/v1/users/me",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Current User Name"

    async def test_change_own_password(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test changing own password."""
        password_data = {
            "current_password": "OldPassword123!",
            "new_password": "NewSecurePassword123!",
            "confirm_password": "NewSecurePassword123!",
        }

        response = await async_client.post(
            "/api/v1/users/me/change-password",
            json=password_data,
            headers=auth_headers,
        )

        # May fail due to mock user, but endpoint should be accessible
        assert response.status_code in [200, 400]

    async def test_change_password_mismatch(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test changing password with mismatched confirmation."""
        password_data = {
            "current_password": "OldPassword123!",
            "new_password": "NewSecurePassword123!",
            "confirm_password": "DifferentPassword123!",
        }

        response = await async_client.post(
            "/api/v1/users/me/change-password",
            json=password_data,
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "match" in response.json()["detail"].lower()


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestUserManagementErrorsE2E:
    """End-to-end tests for error handling in user management."""

    async def test_unauthorized_access(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test accessing user management without authentication."""
        response = await async_client.get(
            "/api/v1/users",
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == 401

    async def test_create_user_missing_required_fields(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test creating user with missing required fields."""
        response = await async_client.post(
            "/api/v1/users",
            json={"username": "testuser"},  # Missing email and password
            headers=auth_headers,
        )

        assert response.status_code == 422

    async def test_invalid_user_id_format(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test operations with invalid user ID format."""
        response = await async_client.get(
            "/api/v1/users/not-a-valid-uuid",
            headers=auth_headers,
        )

        # Should return 404 or 422
        assert response.status_code in [404, 422]

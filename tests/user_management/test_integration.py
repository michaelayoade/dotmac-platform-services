"""Integration tests for user management."""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from dotmac.platform.auth.core import UserInfo
from dotmac.platform.user_management.models import User
from dotmac.platform.user_management.service import UserService
from dotmac.platform.user_management.router import (
    get_current_user_profile,
    create_user,
    update_user,
    delete_user,
    change_password,
    UserCreateRequest,
    UserUpdateRequest,
    PasswordChangeRequest,
)


class TestUserManagementIntegration:
    """Integration tests for complete user management flow."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        return AsyncMock()

    @pytest.fixture
    def user_service(self, mock_session):
        """UserService instance."""
        return UserService(mock_session)

    @pytest.fixture
    def admin_user(self):
        """Mock admin user."""
        return UserInfo(
            user_id=str(uuid.uuid4()),
            username="admin",
            email="admin@example.com",
            roles=["admin"],
            tenant_id="tenant-123",
        )

    async def test_complete_user_lifecycle(self, user_service, admin_user):
        """Test complete user lifecycle: create, read, update, delete."""

        # Mock database interactions
        created_user = User(
            id=uuid.uuid4(),
            username="testuser",
            email="test@example.com",
            password_hash="$2b$12$hashedpassword",
            full_name="Test User",
            roles=["user"],
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tenant_id="tenant-123",
        )

        # Step 1: Create user
        create_request = UserCreateRequest(
            username="testuser",
            email="test@example.com",
            password="password123",
            full_name="Test User",
            roles=["user"],
            is_active=True,
        )

        with patch.object(user_service, 'create_user', return_value=created_user):
            created_response = await create_user(create_request, admin_user, user_service)

        assert created_response.username == "testuser"
        assert created_response.email == "test@example.com"
        assert created_response.full_name == "Test User"
        assert created_response.roles == ["user"]
        assert created_response.is_active is True

        # Step 2: Read user (simulate get current user profile)
        current_user = UserInfo(
            user_id=str(created_user.id),
            username=created_user.username,
            email=created_user.email,
            roles=created_user.roles,
            tenant_id=created_user.tenant_id,
        )

        with patch.object(user_service, 'get_user_by_id', return_value=created_user):
            profile_response = await get_current_user_profile(current_user, user_service)

        assert profile_response.user_id == str(created_user.id)
        assert profile_response.username == "testuser"

        # Step 3: Update user
        update_request = UserUpdateRequest(
            full_name="Updated Test User",
            roles=["user", "editor"],
            is_active=True,
        )

        updated_user = User(
            id=created_user.id,
            username=created_user.username,
            email=created_user.email,
            password_hash=created_user.password_hash,
            full_name="Updated Test User",
            roles=["user", "editor"],
            is_active=True,
            created_at=created_user.created_at,
            updated_at=datetime.now(timezone.utc),
            tenant_id=created_user.tenant_id,
        )

        with patch.object(user_service, 'update_user', return_value=updated_user):
            update_response = await update_user(
                str(created_user.id), update_request, admin_user, user_service
            )

        assert update_response.full_name == "Updated Test User"
        assert update_response.roles == ["user", "editor"]

        # Step 4: Change password
        password_request = PasswordChangeRequest(
            current_password="password123",
            new_password="newpassword456",
            confirm_password="newpassword456",
        )

        with patch.object(user_service, 'change_password', return_value=True):
            password_response = await change_password(password_request, current_user, user_service)

        assert password_response["message"] == "Password changed successfully"

        # Step 5: Delete user
        with patch.object(user_service, 'delete_user', return_value=True):
            delete_response = await delete_user(str(created_user.id), admin_user, user_service)

        assert delete_response is None  # 204 No Content

    async def test_user_authentication_flow(self, user_service):
        """Test complete user authentication flow."""
        # Create a user for authentication
        user = User(
            id=uuid.uuid4(),
            username="authuser",
            email="auth@example.com",
            password_hash="$2b$12$hashedpassword",
            is_active=True,
            failed_login_attempts=0,
            locked_until=None,
        )

        # Test successful authentication
        with patch.object(user_service, 'get_user_by_username', return_value=user):
            with patch.object(user_service, 'verify_password', return_value=True):
                with patch.object(user_service.session, 'commit'):
                    authenticated_user = await user_service.authenticate("authuser", "password123")

        assert authenticated_user == user
        assert user.failed_login_attempts == 0
        assert user.last_login is not None

        # Test failed authentication
        with patch.object(user_service, 'get_user_by_username', return_value=user):
            with patch.object(user_service, 'verify_password', return_value=False):
                with patch.object(user_service.session, 'commit'):
                    failed_auth = await user_service.authenticate("authuser", "wrongpassword")

        assert failed_auth is None
        assert user.failed_login_attempts == 1

    async def test_user_role_management_flow(self, user_service):
        """Test user role management operations."""
        user = User(
            id=uuid.uuid4(),
            username="roleuser",
            email="role@example.com",
            password_hash="$2b$12$hashedpassword",
            roles=["user"],
        )

        # Test adding role
        with patch.object(user_service, 'get_user_by_id', return_value=user):
            with patch.object(user_service.session, 'commit'):
                result = await user_service.add_role(str(user.id), "admin")

        assert result == user
        assert "admin" in user.roles
        assert "user" in user.roles

        # Test removing role
        with patch.object(user_service, 'get_user_by_id', return_value=user):
            with patch.object(user_service.session, 'commit'):
                result = await user_service.remove_role(str(user.id), "user")

        assert result == user
        assert "admin" in user.roles
        assert "user" not in user.roles

    async def test_user_mfa_flow(self, user_service):
        """Test MFA enable/disable flow."""
        user = User(
            id=uuid.uuid4(),
            username="mfauser",
            email="mfa@example.com",
            password_hash="$2b$12$hashedpassword",
            mfa_enabled=False,
            mfa_secret=None,
        )

        # Test enabling MFA
        with patch.object(user_service, 'get_user_by_id', return_value=user):
            with patch.object(user_service.session, 'commit'):
                secret = await user_service.enable_mfa(str(user.id))

        assert isinstance(secret, str)
        assert len(secret) == 40  # 20 bytes as hex
        assert user.mfa_enabled is True
        assert user.mfa_secret == secret

        # Test disabling MFA
        with patch.object(user_service, 'get_user_by_id', return_value=user):
            with patch.object(user_service.session, 'commit'):
                result = await user_service.disable_mfa(str(user.id))

        assert result is True
        assert user.mfa_enabled is False
        assert user.mfa_secret is None

    async def test_user_search_and_filtering(self, user_service):
        """Test user search and filtering functionality."""
        users = [
            User(
                id=uuid.uuid4(),
                username="alice",
                email="alice@example.com",
                full_name="Alice Smith",
                roles=["user"],
                is_active=True,
                tenant_id="tenant-123",
            ),
            User(
                id=uuid.uuid4(),
                username="bob",
                email="bob@example.com",
                full_name="Bob Johnson",
                roles=["admin"],
                is_active=True,
                tenant_id="tenant-123",
            ),
            User(
                id=uuid.uuid4(),
                username="charlie",
                email="charlie@example.com",
                full_name="Charlie Brown",
                roles=["user"],
                is_active=False,
                tenant_id="tenant-123",
            ),
        ]

        # Mock the database query results
        from unittest.mock import MagicMock

        # Test search by name
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [users[0]]  # Alice Smith
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        user_service.session.execute.side_effect = [mock_count_result, mock_result]

        filtered_users, total = await user_service.list_users(search="Alice", tenant_id="tenant-123")

        assert len(filtered_users) == 1
        assert total == 1

        # Reset mock for next test
        user_service.session.execute.reset_mock()

        # Test filter by role
        mock_result.scalars.return_value.all.return_value = [users[1]]  # Bob (admin)
        mock_count_result.scalar.return_value = 1

        user_service.session.execute.side_effect = [mock_count_result, mock_result]

        admin_users, total = await user_service.list_users(role="admin", tenant_id="tenant-123")

        assert len(admin_users) == 1
        assert total == 1

        # Reset mock for next test
        user_service.session.execute.reset_mock()

        # Test filter by active status
        mock_result.scalars.return_value.all.return_value = [users[2]]  # Charlie (inactive)
        mock_count_result.scalar.return_value = 1

        user_service.session.execute.side_effect = [mock_count_result, mock_result]

        inactive_users, total = await user_service.list_users(is_active=False, tenant_id="tenant-123")

        assert len(inactive_users) == 1
        assert total == 1

    async def test_user_validation_edge_cases(self, user_service):
        """Test user validation and edge cases."""
        # Test creating user with duplicate username
        existing_user = User(
            id=uuid.uuid4(),
            username="existing",
            email="existing@example.com",
            password_hash="$2b$12$hashedpassword",
        )

        with patch.object(user_service, 'get_user_by_username', return_value=existing_user):
            with pytest.raises(ValueError, match="Username existing already exists"):
                await user_service.create_user(
                    username="existing",
                    email="new@example.com",
                    password="password123",
                )

        # Test creating user with duplicate email
        with patch.object(user_service, 'get_user_by_username', return_value=None):
            with patch.object(user_service, 'get_user_by_email', return_value=existing_user):
                with pytest.raises(ValueError, match="Email existing@example.com already exists"):
                    await user_service.create_user(
                        username="newuser",
                        email="existing@example.com",
                        password="password123",
                    )

        # Test account lockout after failed attempts
        user = User(
            id=uuid.uuid4(),
            username="locktest",
            email="lock@example.com",
            password_hash="$2b$12$hashedpassword",
            is_active=True,
            failed_login_attempts=4,  # One away from lockout
        )

        with patch.object(user_service, 'get_user_by_username', return_value=user):
            with patch.object(user_service, 'verify_password', return_value=False):
                with patch.object(user_service.session, 'commit'):
                    result = await user_service.authenticate("locktest", "wrongpassword")

        assert result is None
        assert user.failed_login_attempts == 5
        assert user.locked_until is not None

        # Test authentication with locked account
        with patch.object(user_service, 'get_user_by_username', return_value=user):
            result = await user_service.authenticate("locktest", "correctpassword")

        assert result is None  # Should still be locked

    def test_user_model_serialization(self):
        """Test user model serialization to dictionary."""
        user = User(
            id=uuid.uuid4(),
            username="serialize",
            email="serialize@example.com",
            password_hash="$2b$12$hashedpassword",
            full_name="Serialize User",
            roles=["user", "tester"],
            permissions=["read", "write"],
            is_active=True,
            is_verified=True,
            is_superuser=False,
            mfa_enabled=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_login=datetime.now(timezone.utc),
            tenant_id="tenant-123",
        )

        user_dict = user.to_dict()

        # Verify all required fields are present
        required_fields = {
            "user_id", "username", "email", "full_name", "roles",
            "permissions", "is_active", "is_verified", "is_superuser",
            "mfa_enabled", "created_at", "updated_at", "last_login", "tenant_id"
        }

        assert set(user_dict.keys()) == required_fields
        assert user_dict["user_id"] == str(user.id)
        assert user_dict["roles"] == ["user", "tester"]
        assert user_dict["permissions"] == ["read", "write"]

        # Verify sensitive fields are NOT included
        assert "password_hash" not in user_dict
        assert "mfa_secret" not in user_dict
        assert "failed_login_attempts" not in user_dict
        assert "locked_until" not in user_dict
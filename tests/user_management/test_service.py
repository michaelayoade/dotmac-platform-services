"""Tests for user management service."""

import pytest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from dotmac.platform.user_management.service import UserService
from dotmac.platform.user_management.models import User


class TestUserService:
    """Test UserService functionality."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    def user_service(self, mock_session):
        """Create UserService with mock session."""
        return UserService(mock_session)

    @pytest.fixture
    def sample_user(self):
        """Create a sample user for testing."""
        return User(
            id=uuid.uuid4(),
            username="testuser",
            email="test@example.com",
            password_hash="$2b$12$hashedpassword",
            full_name="Test User",
            roles=["user"],
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )

    async def test_get_user_by_id_success(self, user_service, mock_session, sample_user):
        """Test getting user by ID successfully."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        # Act
        user = await user_service.get_user_by_id(str(sample_user.id))

        # Assert
        assert user == sample_user
        mock_session.execute.assert_called_once()

    async def test_get_user_by_id_uuid_input(self, user_service, mock_session, sample_user):
        """Test getting user by ID with UUID input."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        # Act
        user = await user_service.get_user_by_id(sample_user.id)

        # Assert
        assert user == sample_user
        mock_session.execute.assert_called_once()

    async def test_get_user_by_id_invalid_uuid(self, user_service):
        """Test getting user by ID with invalid UUID string."""
        # Act
        user = await user_service.get_user_by_id("invalid-uuid")

        # Assert
        assert user is None

    async def test_get_user_by_id_not_found(self, user_service, mock_session):
        """Test getting user by ID when user doesn't exist."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        user = await user_service.get_user_by_id(str(uuid.uuid4()))

        # Assert
        assert user is None

    async def test_get_user_by_username_success(self, user_service, mock_session, sample_user):
        """Test getting user by username successfully."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        # Act
        user = await user_service.get_user_by_username("testuser")

        # Assert
        assert user == sample_user
        mock_session.execute.assert_called_once()

    async def test_get_user_by_username_not_found(self, user_service, mock_session):
        """Test getting user by username when user doesn't exist."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        user = await user_service.get_user_by_username("nonexistent")

        # Assert
        assert user is None

    async def test_get_user_by_email_success(self, user_service, mock_session, sample_user):
        """Test getting user by email successfully."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        # Act
        user = await user_service.get_user_by_email("test@example.com")

        # Assert
        assert user == sample_user
        mock_session.execute.assert_called_once()

    async def test_get_user_by_email_case_insensitive(self, user_service, mock_session, sample_user):
        """Test getting user by email is case insensitive."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        # Act
        user = await user_service.get_user_by_email("TEST@EXAMPLE.COM")

        # Assert
        assert user == sample_user
        # Check that email was converted to lowercase in the query
        mock_session.execute.assert_called_once()

    async def test_create_user_success(self, user_service, mock_session):
        """Test creating user successfully."""
        # Arrange
        mock_session.execute.return_value = MagicMock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Act
        with patch.object(user_service, '_hash_password', return_value='hashed_pwd'):
            user = await user_service.create_user(
                username="newuser",
                email="new@example.com",
                password="password123",
                full_name="New User",
                roles=["user"],
            )

        # Assert
        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.password_hash == "hashed_pwd"
        assert user.full_name == "New User"
        assert user.roles == ["user"]
        assert user.is_active is True
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    async def test_create_user_username_exists(self, user_service, mock_session, sample_user):
        """Test creating user fails when username already exists."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(ValueError, match="Username testuser already exists"):
            await user_service.create_user(
                username="testuser",
                email="new@example.com",
                password="password123",
            )

    async def test_create_user_email_exists(self, user_service, mock_session, sample_user):
        """Test creating user fails when email already exists."""
        # Arrange
        # First call for username check returns None
        # Second call for email check returns existing user
        mock_results = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=sample_user)),
        ]
        mock_session.execute.side_effect = mock_results

        # Act & Assert
        with pytest.raises(ValueError, match="Email test@example.com already exists"):
            await user_service.create_user(
                username="newuser",
                email="test@example.com",
                password="password123",
            )

    async def test_create_user_integrity_error(self, user_service, mock_session):
        """Test creating user handles database integrity error."""
        # Arrange
        mock_session.execute.return_value = MagicMock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        mock_session.commit = AsyncMock(side_effect=IntegrityError("", "", ""))
        mock_session.rollback = AsyncMock()

        # Act & Assert
        with patch.object(user_service, '_hash_password', return_value='hashed_pwd'):
            with pytest.raises(ValueError, match="User creation failed"):
                await user_service.create_user(
                    username="newuser",
                    email="new@example.com",
                    password="password123",
                )

        mock_session.rollback.assert_called_once()

    async def test_update_user_success(self, user_service, mock_session, sample_user):
        """Test updating user successfully."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Act
        updated_user = await user_service.update_user(
            user_id=str(sample_user.id),
            full_name="Updated Name",
            roles=["admin", "user"],
            is_active=False,
        )

        # Assert
        assert updated_user == sample_user
        assert sample_user.full_name == "Updated Name"
        assert sample_user.roles == ["admin", "user"]
        assert sample_user.is_active is False
        assert sample_user.updated_at is not None
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    async def test_update_user_not_found(self, user_service, mock_session):
        """Test updating non-existent user returns None."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        result = await user_service.update_user(
            user_id=str(uuid.uuid4()),
            full_name="Updated Name",
        )

        # Assert
        assert result is None

    async def test_update_user_email_conflict(self, user_service, mock_session, sample_user):
        """Test updating user email to existing email fails."""
        # Arrange
        another_user = User(id=uuid.uuid4(), username="other", email="other@example.com")

        # First call returns the user to update
        # Second call returns existing user with the email
        mock_results = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=sample_user)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=another_user)),
        ]
        mock_session.execute.side_effect = mock_results

        # Act & Assert
        with pytest.raises(ValueError, match="Email other@example.com is already in use"):
            await user_service.update_user(
                user_id=str(sample_user.id),
                email="other@example.com",
            )

    async def test_delete_user_success(self, user_service, mock_session, sample_user):
        """Test deleting user successfully."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result
        mock_session.delete = AsyncMock()
        mock_session.commit = AsyncMock()

        # Act
        result = await user_service.delete_user(str(sample_user.id))

        # Assert
        assert result is True
        mock_session.delete.assert_called_once_with(sample_user)
        mock_session.commit.assert_called_once()

    async def test_delete_user_not_found(self, user_service, mock_session):
        """Test deleting non-existent user returns False."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        result = await user_service.delete_user(str(uuid.uuid4()))

        # Assert
        assert result is False

    async def test_list_users_no_filters(self, user_service, mock_session, sample_user):
        """Test listing users without filters."""
        # Arrange
        users = [sample_user]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = users
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_session.execute.side_effect = [mock_count_result, mock_result]

        # Act
        returned_users, total = await user_service.list_users()

        # Assert
        assert returned_users == users
        assert total == 1
        assert mock_session.execute.call_count == 2

    async def test_list_users_with_filters(self, user_service, mock_session, sample_user):
        """Test listing users with filters."""
        # Arrange
        users = [sample_user]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = users
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_session.execute.side_effect = [mock_count_result, mock_result]

        # Act
        returned_users, total = await user_service.list_users(
            skip=10,
            limit=20,
            is_active=True,
            role="admin",
            tenant_id="tenant-123",
            search="test",
        )

        # Assert
        assert returned_users == users
        assert total == 1
        assert mock_session.execute.call_count == 2

    async def test_list_users_pagination(self, user_service, mock_session):
        """Test listing users respects pagination."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_session.execute.side_effect = [mock_count_result, mock_result]

        # Act
        users, total = await user_service.list_users(skip=50, limit=25)

        # Assert
        assert users == []
        assert total == 0

    async def test_verify_password_success(self, user_service, sample_user):
        """Test password verification succeeds."""
        # Arrange
        with patch.object(user_service.pwd_context, 'verify', return_value=True):
            # Act
            result = await user_service.verify_password(sample_user, "password123")

        # Assert
        assert result is True

    async def test_verify_password_failure(self, user_service, sample_user):
        """Test password verification fails."""
        # Arrange
        with patch.object(user_service.pwd_context, 'verify', return_value=False):
            # Act
            result = await user_service.verify_password(sample_user, "wrongpassword")

        # Assert
        assert result is False

    async def test_change_password_success(self, user_service, mock_session, sample_user):
        """Test changing password successfully."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        with patch.object(user_service, 'verify_password', return_value=True):
            with patch.object(user_service, '_hash_password', return_value='new_hash'):
                # Act
                result = await user_service.change_password(
                    user_id=str(sample_user.id),
                    current_password="oldpassword",
                    new_password="newpassword",
                )

        # Assert
        assert result is True
        assert sample_user.password_hash == "new_hash"
        mock_session.commit.assert_called_once()

    async def test_change_password_user_not_found(self, user_service, mock_session):
        """Test changing password for non-existent user."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        result = await user_service.change_password(
            user_id=str(uuid.uuid4()),
            current_password="oldpassword",
            new_password="newpassword",
        )

        # Assert
        assert result is False

    async def test_change_password_wrong_current_password(self, user_service, mock_session, sample_user):
        """Test changing password with wrong current password."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        with patch.object(user_service, 'verify_password', return_value=False):
            # Act
            result = await user_service.change_password(
                user_id=str(sample_user.id),
                current_password="wrongpassword",
                new_password="newpassword",
            )

        # Assert
        assert result is False

    async def test_authenticate_success(self, user_service, mock_session, sample_user):
        """Test user authentication succeeds."""
        # Arrange
        sample_user.is_active = True
        sample_user.locked_until = None
        sample_user.failed_login_attempts = 0

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        with patch.object(user_service, 'verify_password', return_value=True):
            # Act
            result = await user_service.authenticate("testuser", "password123")

        # Assert
        assert result == sample_user
        assert sample_user.failed_login_attempts == 0
        assert sample_user.locked_until is None
        assert sample_user.last_login is not None
        mock_session.commit.assert_called_once()

    async def test_authenticate_by_email(self, user_service, mock_session, sample_user):
        """Test user authentication by email."""
        # Arrange
        sample_user.is_active = True
        sample_user.locked_until = None

        # First call (username) returns None, second call (email) returns user
        mock_results = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=sample_user)),
        ]
        mock_session.execute.side_effect = mock_results
        mock_session.commit = AsyncMock()

        with patch.object(user_service, 'verify_password', return_value=True):
            # Act
            result = await user_service.authenticate("test@example.com", "password123")

        # Assert
        assert result == sample_user

    async def test_authenticate_user_not_found(self, user_service, mock_session):
        """Test authentication fails when user not found."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        result = await user_service.authenticate("nonexistent", "password123")

        # Assert
        assert result is None

    async def test_authenticate_account_locked(self, user_service, mock_session, sample_user):
        """Test authentication fails when account is locked."""
        # Arrange
        sample_user.locked_until = datetime.now(timezone.utc) + timedelta(hours=1)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        # Act
        result = await user_service.authenticate("testuser", "password123")

        # Assert
        assert result is None

    async def test_authenticate_wrong_password(self, user_service, mock_session, sample_user):
        """Test authentication fails with wrong password and increments attempts."""
        # Arrange
        sample_user.is_active = True
        sample_user.locked_until = None
        sample_user.failed_login_attempts = 2

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        with patch.object(user_service, 'verify_password', return_value=False):
            # Act
            result = await user_service.authenticate("testuser", "wrongpassword")

        # Assert
        assert result is None
        assert sample_user.failed_login_attempts == 3
        mock_session.commit.assert_called_once()

    async def test_authenticate_locks_account_after_failed_attempts(self, user_service, mock_session, sample_user):
        """Test authentication locks account after 5 failed attempts."""
        # Arrange
        sample_user.is_active = True
        sample_user.locked_until = None
        sample_user.failed_login_attempts = 4

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        with patch.object(user_service, 'verify_password', return_value=False):
            # Act
            result = await user_service.authenticate("testuser", "wrongpassword")

        # Assert
        assert result is None
        assert sample_user.failed_login_attempts == 5
        assert sample_user.locked_until is not None
        assert sample_user.locked_until > datetime.now(timezone.utc)

    async def test_authenticate_inactive_user(self, user_service, mock_session, sample_user):
        """Test authentication fails for inactive user."""
        # Arrange
        sample_user.is_active = False
        sample_user.locked_until = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        with patch.object(user_service, 'verify_password', return_value=True):
            # Act
            result = await user_service.authenticate("testuser", "password123")

        # Assert
        assert result is None

    async def test_enable_mfa_success(self, user_service, mock_session, sample_user):
        """Test enabling MFA successfully."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        # Act
        secret = await user_service.enable_mfa(str(sample_user.id))

        # Assert
        assert isinstance(secret, str)
        assert len(secret) == 40  # 20 bytes as hex = 40 chars
        assert sample_user.mfa_enabled is True
        assert sample_user.mfa_secret == secret
        mock_session.commit.assert_called_once()

    async def test_enable_mfa_user_not_found(self, user_service, mock_session):
        """Test enabling MFA for non-existent user."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(ValueError, match="User not found"):
            await user_service.enable_mfa(str(uuid.uuid4()))

    async def test_disable_mfa_success(self, user_service, mock_session, sample_user):
        """Test disabling MFA successfully."""
        # Arrange
        sample_user.mfa_enabled = True
        sample_user.mfa_secret = "secret123"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        # Act
        result = await user_service.disable_mfa(str(sample_user.id))

        # Assert
        assert result is True
        assert sample_user.mfa_enabled is False
        assert sample_user.mfa_secret is None
        mock_session.commit.assert_called_once()

    async def test_disable_mfa_user_not_found(self, user_service, mock_session):
        """Test disabling MFA for non-existent user."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        result = await user_service.disable_mfa(str(uuid.uuid4()))

        # Assert
        assert result is False

    async def test_add_role_success(self, user_service, mock_session, sample_user):
        """Test adding role to user successfully."""
        # Arrange
        sample_user.roles = ["user"]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        # Act
        result = await user_service.add_role(str(sample_user.id), "admin")

        # Assert
        assert result == sample_user
        assert "admin" in sample_user.roles
        assert "user" in sample_user.roles
        mock_session.commit.assert_called_once()

    async def test_add_role_already_exists(self, user_service, mock_session, sample_user):
        """Test adding role that user already has."""
        # Arrange
        sample_user.roles = ["user", "admin"]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        # Act
        result = await user_service.add_role(str(sample_user.id), "admin")

        # Assert
        assert result == sample_user
        assert sample_user.roles == ["user", "admin"]
        # Should not call commit if role already exists
        mock_session.commit.assert_not_called()

    async def test_add_role_user_not_found(self, user_service, mock_session):
        """Test adding role to non-existent user."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        result = await user_service.add_role(str(uuid.uuid4()), "admin")

        # Assert
        assert result is None

    async def test_remove_role_success(self, user_service, mock_session, sample_user):
        """Test removing role from user successfully."""
        # Arrange
        sample_user.roles = ["user", "admin"]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        # Act
        result = await user_service.remove_role(str(sample_user.id), "admin")

        # Assert
        assert result == sample_user
        assert sample_user.roles == ["user"]
        mock_session.commit.assert_called_once()

    async def test_remove_role_not_exists(self, user_service, mock_session, sample_user):
        """Test removing role that user doesn't have."""
        # Arrange
        sample_user.roles = ["user"]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        # Act
        result = await user_service.remove_role(str(sample_user.id), "admin")

        # Assert
        assert result == sample_user
        assert sample_user.roles == ["user"]
        # Should not call commit if role doesn't exist
        mock_session.commit.assert_not_called()

    async def test_remove_role_user_not_found(self, user_service, mock_session):
        """Test removing role from non-existent user."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        result = await user_service.remove_role(str(uuid.uuid4()), "admin")

        # Assert
        assert result is None

    def test_hash_password(self, user_service):
        """Test password hashing."""
        # Act
        hashed = user_service._hash_password("password123")

        # Assert
        assert isinstance(hashed, str)
        assert hashed != "password123"
        assert hashed.startswith("$2b$")  # bcrypt format
"""Tests to improve user management service coverage."""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from dotmac.platform.user_management.service import UserService
from dotmac.platform.user_management.models import User


class TestUserServiceCoverage:
    """Test UserService edge cases for better coverage."""

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
            is_verified=True,
            phone_number="+1234567890",
            metadata_={"key": "value"}
        )

    async def test_update_user_with_full_name_none(self, user_service, mock_session, sample_user):
        """Test update_user with full_name=None (line 124-125)."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        # Act
        result = await user_service.update_user(
            user_id=str(sample_user.id),
            full_name=None  # This should test line 124-125
        )

        # Assert
        assert result == sample_user
        mock_session.commit.assert_called_once()

    async def test_update_user_with_roles_none(self, user_service, mock_session, sample_user):
        """Test update_user with roles=None (line 126-127)."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        # Act
        result = await user_service.update_user(
            user_id=str(sample_user.id),
            roles=None  # This should test line 126-127
        )

        # Assert
        assert result == sample_user
        mock_session.commit.assert_called_once()

    async def test_update_user_with_permissions_none(self, user_service, mock_session, sample_user):
        """Test update_user with permissions=None (line 128-129)."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        # Act
        result = await user_service.update_user(
            user_id=str(sample_user.id),
            permissions=None  # This should test line 128-129
        )

        # Assert
        assert result == sample_user
        mock_session.commit.assert_called_once()

    async def test_update_user_with_is_active_none(self, user_service, mock_session, sample_user):
        """Test update_user with is_active=None (line 130-131)."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        # Act
        result = await user_service.update_user(
            user_id=str(sample_user.id),
            is_active=None  # This should test line 130-131
        )

        # Assert
        assert result == sample_user
        mock_session.commit.assert_called_once()

    async def test_update_user_with_is_verified_none(self, user_service, mock_session, sample_user):
        """Test update_user with is_verified=None (line 132-133)."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        # Act
        result = await user_service.update_user(
            user_id=str(sample_user.id),
            is_verified=None  # This should test line 132-133
        )

        # Assert
        assert result == sample_user
        mock_session.commit.assert_called_once()

    async def test_update_user_with_phone_number_none(self, user_service, mock_session, sample_user):
        """Test update_user with phone_number=None (line 134-135)."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        # Act
        result = await user_service.update_user(
            user_id=str(sample_user.id),
            phone_number=None  # This should test line 134-135
        )

        # Assert
        assert result == sample_user
        mock_session.commit.assert_called_once()

    async def test_update_user_with_metadata_none(self, user_service, mock_session, sample_user):
        """Test update_user with metadata=None (line 136-137)."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        # Act
        result = await user_service.update_user(
            user_id=str(sample_user.id),
            metadata=None  # This should test line 136-137
        )

        # Assert
        assert result == sample_user
        mock_session.commit.assert_called_once()

    async def test_update_user_integrity_error_exception(self, user_service, mock_session, sample_user):
        """Test update_user with IntegrityError exception (line 146-149)."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result
        mock_session.commit.side_effect = IntegrityError("test", "test", "test")

        # Act & Assert
        with pytest.raises(IntegrityError):
            await user_service.update_user(
                user_id=str(sample_user.id),
                email="newemail@example.com"
            )

        # Verify rollback was called
        mock_session.rollback.assert_called_once()

    async def test_update_user_with_all_optional_params_set(self, user_service, mock_session, sample_user):
        """Test update_user with all optional parameters set to test various branches."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        # Act
        result = await user_service.update_user(
            user_id=str(sample_user.id),
            email="updated@example.com",
            full_name="Updated User",
            roles=["admin", "user"],
            permissions=["read", "write"],
            is_active=False,
            is_verified=False,
            phone_number="+0987654321",
            metadata={"updated": True}
        )

        # Assert
        assert result == sample_user
        assert sample_user.email == "updated@example.com"
        assert sample_user.full_name == "Updated User"
        assert sample_user.roles == ["admin", "user"]
        assert sample_user.permissions == ["read", "write"]
        assert sample_user.is_active is False
        assert sample_user.is_verified is False
        assert sample_user.phone_number == "+0987654321"
        assert sample_user.metadata_ == {"updated": True}
        mock_session.commit.assert_called_once()

    async def test_update_user_email_with_no_existing_conflict(self, user_service, mock_session, sample_user):
        """Test update_user with email change when no existing user with that email."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [sample_user, None]  # user exists, no email conflict
        mock_session.execute.return_value = mock_result

        # Act
        result = await user_service.update_user(
            user_id=str(sample_user.id),
            email="newemail@example.com"
        )

        # Assert
        assert result == sample_user
        assert sample_user.email == "newemail@example.com"
        mock_session.commit.assert_called_once()

    async def test_list_users_with_additional_filters(self, user_service, mock_session):
        """Test list_users functionality with different filter combinations."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        # Test with various filter combinations
        await user_service.list_users(is_active=True, tenant_id="test-tenant")
        await user_service.list_users(role="admin", tenant_id="test-tenant")
        await user_service.list_users(limit=10, skip=5, tenant_id="test-tenant")
        await user_service.list_users(search="test", tenant_id="tenant-123")

        # Assert execute was called multiple times
        assert mock_session.execute.call_count >= 3

    async def test_user_service_password_operations_edge_cases(self, user_service, mock_session, sample_user):
        """Test password-related operations edge cases."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        # Test with password verification (correct parameters)
        with patch.object(user_service.pwd_context, 'verify', return_value=True):
            result = await user_service.verify_password(sample_user, "correct_password")
            assert result is True

        with patch.object(user_service.pwd_context, 'verify', return_value=False):
            result = await user_service.verify_password(sample_user, "wrong_password")
            assert result is False
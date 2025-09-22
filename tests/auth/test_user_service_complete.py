"""Comprehensive User Service Tests - Developer Coverage Task.

This test suite provides extensive coverage for the user service functionality,
including user registration, creation, validation, sanitization, and health checks.
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch
from typing import Any

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.dotmac.platform.auth.user_service import (
    BaseUserService,
    UserCreateSchema,
    UserService,
    UserType,
    _MASKED_VALUE,
    _SENSITIVE_KEYS,
)
from dotmac.platform.domain import (
    AuthorizationError,
    EntityNotFoundError,
    ValidationError,
)


class TestUserType:
    """Test UserType enum."""

    def test_user_type_enum_values(self):
        """Test all user type enum values."""
        assert UserType.TENANT_USER.value == "tenant_user"
        assert UserType.CUSTOMER.value == "customer"
        assert UserType.PLATFORM_ADMIN.value == "platform_admin"

        # Test enum comparison
        assert UserType.CUSTOMER == "customer"
        assert UserType.TENANT_USER != UserType.CUSTOMER

    def test_user_type_enum_membership(self):
        """Test user type enum membership."""
        assert "customer" in [ut.value for ut in UserType]
        assert "invalid_type" not in [ut.value for ut in UserType]


class TestUserCreateSchema:
    """Test UserCreateSchema Pydantic model."""

    def test_user_create_schema_minimal(self):
        """Test minimal user creation schema."""
        schema = UserCreateSchema(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            password="password123"
        )

        assert schema.username == "testuser"
        assert schema.email == "test@example.com"
        assert schema.first_name == "Test"
        assert schema.last_name is None
        assert schema.user_type == UserType.CUSTOMER
        assert schema.password == "password123"
        assert schema.terms_accepted is False
        assert schema.privacy_accepted is False
        assert schema.roles == []
        assert schema.permissions == []
        assert schema.platform_metadata == {}
        assert schema.timezone is None
        assert schema.language is None
        assert schema.tenant_id is None

    def test_user_create_schema_full(self):
        """Test full user creation schema with all fields."""
        schema = UserCreateSchema(
            username="fulluser",
            email="full@example.com",
            first_name="Full",
            last_name="User",
            user_type=UserType.TENANT_USER,
            password="securepassword",
            terms_accepted=True,
            privacy_accepted=True,
            roles=["admin", "user"],
            permissions=["read:users", "write:users"],
            platform_metadata={"source": "api", "version": "1.0"},
            timezone="UTC",
            language="en",
            tenant_id="tenant-123"
        )

        assert schema.username == "fulluser"
        assert schema.email == "full@example.com"
        assert schema.first_name == "Full"
        assert schema.last_name == "User"
        assert schema.user_type == UserType.TENANT_USER
        assert schema.password == "securepassword"
        assert schema.terms_accepted is True
        assert schema.privacy_accepted is True
        assert schema.roles == ["admin", "user"]
        assert schema.permissions == ["read:users", "write:users"]
        assert schema.platform_metadata == {"source": "api", "version": "1.0"}
        assert schema.timezone == "UTC"
        assert schema.language == "en"
        assert schema.tenant_id == "tenant-123"

    def test_user_create_schema_default_factories(self):
        """Test default factory fields are independent instances."""
        schema1 = UserCreateSchema(
            username="user1",
            email="user1@example.com",
            first_name="User1",
            password="pass1"
        )
        schema2 = UserCreateSchema(
            username="user2",
            email="user2@example.com",
            first_name="User2",
            password="pass2"
        )

        # Modify one instance
        schema1.roles.append("admin")
        schema1.platform_metadata["key"] = "value"

        # Verify the other instance is unaffected
        assert schema2.roles == []
        assert schema2.platform_metadata == {}

    def test_user_create_schema_user_type_validation(self):
        """Test user type validation in schema."""
        # Valid user type
        schema = UserCreateSchema(
            username="test",
            email="test@example.com",
            first_name="Test",
            password="pass",
            user_type=UserType.PLATFORM_ADMIN
        )
        assert schema.user_type == UserType.PLATFORM_ADMIN


class TestBaseUserService:
    """Test BaseUserService functionality."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return MagicMock()

    @pytest.fixture
    def base_service(self, mock_db_session):
        """BaseUserService instance for testing."""
        return BaseUserService(db_session=mock_db_session, tenant_id=None)

    @pytest.fixture
    def base_service_with_tenant(self, mock_db_session):
        """BaseUserService instance with tenant ID."""
        return BaseUserService(db_session=mock_db_session, tenant_id="tenant-123")

    def test_base_service_initialization(self, mock_db_session):
        """Test base service initialization."""
        service = BaseUserService(db_session=mock_db_session, tenant_id="tenant-456")

        assert service.db_session == mock_db_session
        assert service.tenant_id == "tenant-456"

    def test_base_service_initialization_no_tenant(self, mock_db_session):
        """Test base service initialization without tenant."""
        service = BaseUserService(db_session=mock_db_session)

        assert service.db_session == mock_db_session
        assert service.tenant_id is None

    def test_sanitize_user_data_basic(self, base_service):
        """Test basic user data sanitization."""
        payload = {
            "username": "  TestUser  ",
            "email": "  TEST@Example.COM  ",
            "first_name": "  john  ",
            "last_name": "  DOE  ",
            "description": "  Some description  ",
            "empty_field": "",
            "whitespace_field": "   ",
            "none_field": None,
            "number_field": 42
        }

        result = base_service._sanitize_user_data(payload)

        # Username and email should be lowercase and trimmed
        assert result["username"] == "testuser"
        assert result["email"] == "test@example.com"

        # First name should be capitalized and trimmed
        assert result["first_name"] == "John"

        # Other string fields should be trimmed but not modified
        assert result["last_name"] == "DOE"
        assert result["description"] == "Some description"

        # Empty/whitespace/None fields should be excluded
        assert "empty_field" not in result
        assert "whitespace_field" not in result
        assert "none_field" not in result

        # Non-string fields should be preserved
        assert result["number_field"] == 42

    def test_sanitize_user_data_edge_cases(self, base_service):
        """Test edge cases in data sanitization."""
        payload = {
            "username": "UPPERCASE",
            "email": "Mixed.Case@DOMAIN.COM",
            "first_name": "lowercase",
            "boolean_field": True,
            "list_field": ["item1", "item2"],
            "dict_field": {"key": "value"}
        }

        result = base_service._sanitize_user_data(payload)

        assert result["username"] == "uppercase"
        assert result["email"] == "mixed.case@domain.com"
        assert result["first_name"] == "Lowercase"
        assert result["boolean_field"] is True
        assert result["list_field"] == ["item1", "item2"]
        assert result["dict_field"] == {"key": "value"}

    def test_mask_sensitive_data(self, base_service):
        """Test sensitive data masking."""
        payload = {
            "username": "testuser",
            "password": "secret123",
            "password_hash": "hashed_value",
            "token": "jwt_token",
            "access_token": "access_123",
            "refresh_token": "refresh_456",
            "secret": "api_secret",
            "public_field": "visible_data",
            "api_key": "should_remain"
        }

        result = base_service._mask_sensitive_data(payload)

        # Sensitive fields should be masked
        for sensitive_key in _SENSITIVE_KEYS:
            if sensitive_key in payload:
                assert result[sensitive_key] == _MASKED_VALUE

        # Non-sensitive fields should remain unchanged
        assert result["username"] == "testuser"
        assert result["public_field"] == "visible_data"
        assert result["api_key"] == "should_remain"

    def test_mask_sensitive_data_empty_payload(self, base_service):
        """Test masking sensitive data with empty payload."""
        result = base_service._mask_sensitive_data({})
        assert result == {}

    def test_mask_sensitive_data_no_sensitive_fields(self, base_service):
        """Test masking when no sensitive fields are present."""
        payload = {
            "username": "testuser",
            "email": "test@example.com",
            "public_data": "visible"
        }

        result = base_service._mask_sensitive_data(payload)
        assert result == payload

    def test_validate_tenant_access_no_tenant_constraint(self, base_service):
        """Test tenant access validation when service has no tenant constraint."""
        # Should not raise when service has no tenant ID
        base_service._validate_tenant_access("any-tenant", "test_action")
        base_service._validate_tenant_access(None, "test_action")

    def test_validate_tenant_access_matching_tenant(self, base_service_with_tenant):
        """Test tenant access validation with matching tenant."""
        # Should not raise when tenant IDs match
        base_service_with_tenant._validate_tenant_access("tenant-123", "test_action")

    def test_validate_tenant_access_mismatched_tenant(self, base_service_with_tenant):
        """Test tenant access validation with mismatched tenant."""
        with pytest.raises(AuthorizationError) as exc_info:
            base_service_with_tenant._validate_tenant_access("wrong-tenant", "test_action")

        assert "Tenant mismatch" in str(exc_info.value)
        assert "test_action" in str(exc_info.value)
        assert "wrong-tenant" in str(exc_info.value)
        assert "tenant-123" in str(exc_info.value)

    def test_validate_tenant_access_none_tenant_with_constraint(self, base_service_with_tenant):
        """Test tenant access validation with None tenant when constraint exists."""
        with pytest.raises(AuthorizationError) as exc_info:
            base_service_with_tenant._validate_tenant_access(None, "test_action")

        assert "Tenant mismatch" in str(exc_info.value)

    def test_validate_entity_exists_found(self, base_service):
        """Test entity existence validation when entity exists."""
        mock_entity = Mock()
        # Should not raise when entity exists
        base_service._validate_entity_exists(mock_entity, "User", "123")

    def test_validate_entity_exists_not_found(self, base_service):
        """Test entity existence validation when entity is None."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            base_service._validate_entity_exists(None, "User", "123")

        assert "User with identifier '123' was not found" in str(exc_info.value)

    def test_validate_required_fields_all_present(self, base_service):
        """Test required field validation when all fields are present."""
        payload = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "secret"
        }
        required_fields = ["username", "email", "password"]

        # Should not raise when all required fields are present
        base_service._validate_required_fields(payload, required_fields)

    def test_validate_required_fields_missing_single(self, base_service):
        """Test required field validation with single missing field."""
        payload = {
            "username": "testuser",
            "email": "test@example.com"
        }
        required_fields = ["username", "email", "password"]

        with pytest.raises(ValidationError) as exc_info:
            base_service._validate_required_fields(payload, required_fields)

        assert "Missing required fields: password" in str(exc_info.value)

    def test_validate_required_fields_missing_multiple(self, base_service):
        """Test required field validation with multiple missing fields."""
        payload = {
            "username": "testuser"
        }
        required_fields = ["username", "email", "password", "first_name"]

        with pytest.raises(ValidationError) as exc_info:
            base_service._validate_required_fields(payload, required_fields)

        error_message = str(exc_info.value)
        assert "Missing required fields:" in error_message
        assert "email" in error_message
        assert "first_name" in error_message
        assert "password" in error_message

    def test_validate_required_fields_empty_values(self, base_service):
        """Test required field validation with empty string values."""
        payload = {
            "username": "",
            "email": "test@example.com",
            "password": "   "  # Whitespace only
        }
        required_fields = ["username", "email", "password"]

        with pytest.raises(ValidationError) as exc_info:
            base_service._validate_required_fields(payload, required_fields)

        error_message = str(exc_info.value)
        assert "Missing required fields:" in error_message
        # The implementation checks for truthy values, so "" and "   " are both falsy
        assert "username" in error_message or "password" in error_message

    def test_handle_database_error_unique_constraint(self, base_service):
        """Test database error handling for unique constraint violations."""
        error = IntegrityError("statement", "params", "UNIQUE constraint failed: users.email")

        with pytest.raises(ValidationError) as exc_info:
            base_service._handle_database_error(error, "user_creation")

        assert "Email address is already in use" in str(exc_info.value)

    def test_handle_database_error_duplicate_key(self, base_service):
        """Test database error handling for duplicate key violations."""
        error = IntegrityError("statement", "params", "duplicate key value violates unique constraint")

        with pytest.raises(ValidationError) as exc_info:
            base_service._handle_database_error(error, "user_creation")

        assert "Email address is already in use" in str(exc_info.value)

    def test_handle_database_error_general_sqlalchemy(self, base_service):
        """Test database error handling for general SQLAlchemy errors."""
        error = SQLAlchemyError("Connection timeout")

        with pytest.raises(ValidationError) as exc_info:
            base_service._handle_database_error(error, "user_update")

        assert "Database error during user_update: Connection timeout" in str(exc_info.value)

    def test_handle_database_error_runtime_error(self, base_service):
        """Test database error handling for non-SQLAlchemy errors."""
        error = RuntimeError("General runtime error")

        with pytest.raises(RuntimeError) as exc_info:
            base_service._handle_database_error(error, "operation")

        assert "General runtime error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_health_check_success(self, base_service):
        """Test successful health check."""
        # Mock successful database execution
        base_service.db_session.execute = AsyncMock()

        result = await base_service.health_check()

        assert result["status"] == "healthy"
        assert result["checks"]["database"] == "connected"
        base_service.db_session.execute.assert_called_once_with("SELECT 1")

    @pytest.mark.asyncio
    async def test_health_check_database_failure(self, base_service):
        """Test health check with database failure."""
        # Mock database execution failure
        base_service.db_session.execute = AsyncMock(side_effect=Exception("Connection failed"))

        with patch('src.dotmac.platform.auth.user_service.logger') as mock_logger:
            result = await base_service.health_check()

        assert result["status"] == "unhealthy"
        assert result["checks"]["database"] == "disconnected"
        mock_logger.error.assert_called_once()


class TestUserService:
    """Test UserService functionality."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return MagicMock()

    @pytest.fixture
    def mock_user_repo(self):
        """Mock user repository."""
        repo = MagicMock()
        repo.check_username_available = AsyncMock(return_value=True)
        repo.check_email_available = AsyncMock(return_value=True)
        repo.create_user = AsyncMock(return_value={"id": "user-123", "username": "testuser"})
        return repo

    @pytest.fixture
    def user_service(self, mock_db_session, mock_user_repo):
        """UserService instance for testing."""
        return UserService(
            db_session=mock_db_session,
            tenant_id=None,
            user_repo=mock_user_repo
        )

    @pytest.fixture
    def user_service_with_tenant(self, mock_db_session, mock_user_repo):
        """UserService instance with tenant ID."""
        return UserService(
            db_session=mock_db_session,
            tenant_id="tenant-123",
            user_repo=mock_user_repo
        )

    @pytest.fixture
    def valid_user_data(self):
        """Valid user creation data."""
        return UserCreateSchema(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="securepassword123",
            terms_accepted=True,
            privacy_accepted=True,
            user_type=UserType.CUSTOMER
        )

    def test_user_service_initialization(self, mock_db_session, mock_user_repo):
        """Test user service initialization."""
        service = UserService(
            db_session=mock_db_session,
            tenant_id="tenant-456",
            user_repo=mock_user_repo
        )

        assert service.db_session == mock_db_session
        assert service.tenant_id == "tenant-456"
        assert service.user_repo == mock_user_repo

    def test_user_service_initialization_no_repo(self, mock_db_session):
        """Test user service initialization without repository."""
        service = UserService(db_session=mock_db_session, tenant_id=None)

        assert service.db_session == mock_db_session
        assert service.tenant_id is None
        assert service.user_repo is None

    @pytest.mark.asyncio
    async def test_register_user_success(self, user_service, valid_user_data, mock_user_repo):
        """Test successful user registration."""
        result = await user_service.register_user(valid_user_data, auto_activate=True)

        assert result["id"] == "user-123"
        assert result["username"] == "testuser"

        # Verify repository calls
        mock_user_repo.check_username_available.assert_called_once_with("testuser")
        mock_user_repo.check_email_available.assert_called_once_with("test@example.com")
        mock_user_repo.create_user.assert_called_once_with(valid_user_data, auto_activate=True)

    @pytest.mark.asyncio
    async def test_register_user_terms_not_accepted(self, user_service, valid_user_data):
        """Test user registration when terms are not accepted."""
        valid_user_data.terms_accepted = False

        with pytest.raises(ValidationError) as exc_info:
            await user_service.register_user(valid_user_data)

        assert "must accept terms of service and privacy policy" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_register_user_privacy_not_accepted(self, user_service, valid_user_data):
        """Test user registration when privacy policy is not accepted."""
        valid_user_data.privacy_accepted = False

        with pytest.raises(ValidationError) as exc_info:
            await user_service.register_user(valid_user_data)

        assert "must accept terms of service and privacy policy" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_register_user_platform_admin_downgrade(self, user_service, valid_user_data, mock_user_repo):
        """Test that platform admin user type is downgraded to customer during registration."""
        valid_user_data.user_type = UserType.PLATFORM_ADMIN

        result = await user_service.register_user(valid_user_data)

        # Verify user type was changed to customer
        call_args = mock_user_repo.create_user.call_args[0][0]
        assert call_args.user_type == UserType.CUSTOMER

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service, valid_user_data, mock_user_repo):
        """Test successful user creation."""
        result = await user_service.create_user(valid_user_data, auto_activate=False)

        assert result["id"] == "user-123"
        assert result["username"] == "testuser"

        # Verify repository calls
        mock_user_repo.check_username_available.assert_called_once_with("testuser")
        mock_user_repo.check_email_available.assert_called_once_with("test@example.com")
        mock_user_repo.create_user.assert_called_once_with(valid_user_data, auto_activate=False)

    @pytest.mark.asyncio
    async def test_create_user_no_repository(self, mock_db_session, valid_user_data):
        """Test user creation when repository is not configured."""
        service = UserService(db_session=mock_db_session, user_repo=None)

        with pytest.raises(RuntimeError) as exc_info:
            await service.create_user(valid_user_data)

        assert "User repository is not configured" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_user_username_taken(self, user_service, valid_user_data, mock_user_repo):
        """Test user creation when username is already taken."""
        mock_user_repo.check_username_available.return_value = False

        with pytest.raises(ValidationError) as exc_info:
            await user_service.create_user(valid_user_data)

        assert "Username is already taken" in str(exc_info.value)
        mock_user_repo.check_username_available.assert_called_once_with("testuser")

    @pytest.mark.asyncio
    async def test_create_user_email_taken(self, user_service, valid_user_data, mock_user_repo):
        """Test user creation when email is already in use."""
        mock_user_repo.check_email_available.return_value = False

        with pytest.raises(ValidationError) as exc_info:
            await user_service.create_user(valid_user_data)

        assert "Email address is already in use" in str(exc_info.value)
        mock_user_repo.check_email_available.assert_called_once_with("test@example.com")

    @pytest.mark.asyncio
    async def test_create_user_repository_error(self, user_service, valid_user_data, mock_user_repo):
        """Test user creation when repository raises an error."""
        mock_user_repo.create_user.side_effect = Exception("Database connection failed")

        with pytest.raises(Exception) as exc_info:
            await user_service.create_user(valid_user_data)

        assert "Database connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_user_with_tenant_isolation(self, user_service_with_tenant, valid_user_data, mock_user_repo):
        """Test user creation with tenant isolation."""
        valid_user_data.tenant_id = "tenant-123"

        result = await user_service_with_tenant.create_user(valid_user_data)

        assert result["id"] == "user-123"
        # Verify the service tenant ID is preserved
        assert user_service_with_tenant.tenant_id == "tenant-123"


class TestUserServiceIntegration:
    """Integration-style tests for user service components."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session for integration tests."""
        return MagicMock()

    @pytest.fixture
    def mock_user_repo(self):
        """Mock user repository for integration tests."""
        repo = MagicMock()
        repo.check_username_available = AsyncMock(return_value=True)
        repo.check_email_available = AsyncMock(return_value=True)
        repo.create_user = AsyncMock()
        return repo

    @pytest.mark.asyncio
    async def test_full_user_registration_workflow(self, mock_db_session, mock_user_repo):
        """Test complete user registration workflow."""
        # Setup service
        service = UserService(
            db_session=mock_db_session,
            tenant_id="tenant-123",
            user_repo=mock_user_repo
        )

        # Create user data with raw input (unsanitized)
        user_data = UserCreateSchema(
            username="  TestUser  ",
            email="  TEST@EXAMPLE.COM  ",
            first_name="  john  ",
            last_name="  doe  ",
            password="securepassword123",
            terms_accepted=True,
            privacy_accepted=True,
            user_type=UserType.CUSTOMER,
            roles=["user"],
            permissions=["read:profile"],
            platform_metadata={"source": "registration_form"},
            timezone="America/New_York",
            language="en"
        )

        # Mock successful creation
        created_user = {
            "id": "user-456",
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "doe",
            "user_type": "customer",
            "created_at": "2023-01-01T00:00:00Z"
        }
        mock_user_repo.create_user.return_value = created_user

        # Register user
        result = await service.register_user(user_data, auto_activate=True)

        # Verify result
        assert result["id"] == "user-456"
        assert result["username"] == "testuser"
        assert result["email"] == "test@example.com"

        # Verify repository interactions
        mock_user_repo.check_username_available.assert_called_once_with("  TestUser  ")
        mock_user_repo.check_email_available.assert_called_once_with("  TEST@EXAMPLE.COM  ")
        mock_user_repo.create_user.assert_called_once()

        # Verify the user data passed to create_user
        create_call_args = mock_user_repo.create_user.call_args[0][0]
        assert create_call_args.username == "  TestUser  "  # Raw data passed through
        assert create_call_args.email == "  TEST@EXAMPLE.COM  "
        assert create_call_args.user_type == UserType.CUSTOMER

    @pytest.mark.asyncio
    async def test_user_service_data_sanitization_workflow(self, mock_db_session):
        """Test data sanitization workflow in user service."""
        service = BaseUserService(db_session=mock_db_session)

        # Test data with various edge cases
        raw_data = {
            "username": "  MIXED_case_USER  ",
            "email": "  Email@DOMAIN.COM  ",
            "first_name": "  jane  ",
            "password": "sensitive_password",
            "secret": "api_secret",
            "empty_field": "",
            "none_field": None,
            "number_field": 42,
            "boolean_field": True
        }

        # Sanitize data
        sanitized = service._sanitize_user_data(raw_data)

        # Mask sensitive data
        masked = service._mask_sensitive_data(sanitized)

        # Verify sanitization
        assert sanitized["username"] == "mixed_case_user"
        assert sanitized["email"] == "email@domain.com"
        assert sanitized["first_name"] == "Jane"
        assert sanitized["number_field"] == 42
        assert sanitized["boolean_field"] is True
        assert "empty_field" not in sanitized
        assert "none_field" not in sanitized

        # Verify masking
        assert masked["password"] == _MASKED_VALUE
        assert masked["secret"] == _MASKED_VALUE
        assert masked["username"] == "mixed_case_user"  # Non-sensitive preserved

    @pytest.mark.asyncio
    async def test_error_handling_cascade(self, mock_db_session, mock_user_repo):
        """Test error handling cascade through service layers."""
        service = UserService(
            db_session=mock_db_session,
            user_repo=mock_user_repo
        )

        user_data = UserCreateSchema(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            password="password123",
            terms_accepted=True,
            privacy_accepted=True
        )

        # Test username availability check failure
        mock_user_repo.check_username_available.side_effect = Exception("Database error")

        with pytest.raises(Exception) as exc_info:
            await service.create_user(user_data)

        assert "Database error" in str(exc_info.value)

        # Reset mock and test email availability check failure
        mock_user_repo.check_username_available.side_effect = None
        mock_user_repo.check_username_available.return_value = True
        mock_user_repo.check_email_available.side_effect = Exception("Connection timeout")

        with pytest.raises(Exception) as exc_info:
            await service.create_user(user_data)

        assert "Connection timeout" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_service_health_check_integration(self, mock_db_session, mock_user_repo):
        """Test health check integration across service layers."""
        service = UserService(
            db_session=mock_db_session,
            tenant_id="tenant-123",
            user_repo=mock_user_repo
        )

        # Mock successful database connection
        mock_db_session.execute = AsyncMock()

        health_result = await service.health_check()

        assert health_result["status"] == "healthy"
        assert health_result["checks"]["database"] == "connected"
        mock_db_session.execute.assert_called_once_with("SELECT 1")


class TestUserServiceEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def base_service(self):
        """Base service for edge case testing."""
        return BaseUserService(db_session=MagicMock())

    def test_sanitize_user_data_unicode_handling(self, base_service):
        """Test sanitization with Unicode characters."""
        payload = {
            "username": "  üser_nämé  ",
            "email": "  EMAIL@DÖMÄIN.COM  ",
            "first_name": "  josé  ",
            "description": "  Descripción con acentos  "
        }

        result = base_service._sanitize_user_data(payload)

        assert result["username"] == "üser_nämé"
        assert result["email"] == "email@dömäin.com"
        assert result["first_name"] == "José"
        assert result["description"] == "Descripción con acentos"

    def test_mask_sensitive_data_case_sensitivity(self, base_service):
        """Test that masking is case-sensitive."""
        payload = {
            "PASSWORD": "should_not_be_masked",  # Uppercase
            "password": "should_be_masked",      # Lowercase
            "Password": "should_not_be_masked",  # Mixed case
            "token": "should_be_masked"
        }

        result = base_service._mask_sensitive_data(payload)

        assert result["PASSWORD"] == "should_not_be_masked"
        assert result["password"] == _MASKED_VALUE
        assert result["Password"] == "should_not_be_masked"
        assert result["token"] == _MASKED_VALUE

    def test_validate_required_fields_empty_requirements(self, base_service):
        """Test validation with empty requirements list."""
        payload = {"field1": "value1", "field2": "value2"}

        # Should not raise when no fields are required
        base_service._validate_required_fields(payload, [])

    def test_constants_and_module_exports(self):
        """Test module constants and exports."""
        # Test that sensitive keys constant is properly defined
        assert isinstance(_SENSITIVE_KEYS, tuple)
        assert "password" in _SENSITIVE_KEYS
        assert "token" in _SENSITIVE_KEYS

        # Test masked value constant
        assert _MASKED_VALUE == "***MASKED***"

        # Test that all expected classes are importable
        from src.dotmac.platform.auth.user_service import (
            BaseUserService,
            UserService,
            UserType,
            UserCreateSchema,
        )

        assert BaseUserService is not None
        assert UserService is not None
        assert UserType is not None
        assert UserCreateSchema is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
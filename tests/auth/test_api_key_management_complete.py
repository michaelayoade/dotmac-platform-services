"""Comprehensive API Key Management Tests - Developer Coverage Task.

This test suite provides extensive coverage for the API key management system,
including all CRUD operations, authentication flows, rate limiting, security
controls, and usage tracking.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from src.dotmac.platform.auth.api_keys import (
    APIKey,
    APIKeyCreateRequest,
    APIKeyCreateResponse,
    APIKeyRateLimit,
    APIKeyResponse,
    APIKeyScope,
    APIKeyService,
    APIKeyServiceConfig,
    APIKeyStatus,
    APIKeyUpdateRequest,
    APIKeyUsage,
    APIKeyValidation,
    RateLimitWindow,
    api_key_dependency,
    api_key_required,
    extract_api_key_from_request,
    generate_api_key,
    hash_api_key,
    verify_api_key,
)
from src.dotmac.platform.auth.exceptions import (
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    ValidationError as AuthValidationError,
)
from src.dotmac.platform.db import Base


class TestAPIKeyModelsComprehensive:
    """Comprehensive tests for API key Pydantic models."""

    def test_api_key_status_enum_complete(self):
        """Test all API key status values."""
        assert APIKeyStatus.ACTIVE.value == "active"
        assert APIKeyStatus.SUSPENDED.value == "suspended"
        assert APIKeyStatus.REVOKED.value == "revoked"
        assert APIKeyStatus.EXPIRED.value == "expired"

        # Test enum comparison
        assert APIKeyStatus.ACTIVE == "active"
        assert APIKeyStatus.SUSPENDED != APIKeyStatus.ACTIVE

    def test_api_key_scope_enum_complete(self):
        """Test all API key scope values."""
        # Read permissions
        assert APIKeyScope.READ_USERS.value == "read:users"
        assert APIKeyScope.READ_BILLING.value == "read:billing"
        assert APIKeyScope.READ_ANALYTICS.value == "read:analytics"
        assert APIKeyScope.READ_SERVICES.value == "read:services"
        assert APIKeyScope.READ_NETWORK.value == "read:network"
        assert APIKeyScope.READ_TICKETS.value == "read:tickets"

        # Write permissions
        assert APIKeyScope.WRITE_USERS.value == "write:users"
        assert APIKeyScope.WRITE_BILLING.value == "write:billing"
        assert APIKeyScope.WRITE_SERVICES.value == "write:services"
        assert APIKeyScope.WRITE_NETWORK.value == "write:network"
        assert APIKeyScope.WRITE_TICKETS.value == "write:tickets"

        # Admin permissions
        assert APIKeyScope.ADMIN_USERS.value == "admin:users"
        assert APIKeyScope.ADMIN_BILLING.value == "admin:billing"
        assert APIKeyScope.ADMIN_SERVICES.value == "admin:services"
        assert APIKeyScope.ADMIN_NETWORK.value == "admin:network"
        assert APIKeyScope.ADMIN_SYSTEM.value == "admin:system"

        # Special scopes
        assert APIKeyScope.WEBHOOK_RECEIVE.value == "webhook:receive"
        assert APIKeyScope.API_INTERNAL.value == "api:internal"

    def test_rate_limit_window_enum_complete(self):
        """Test all rate limit window values."""
        assert RateLimitWindow.MINUTE.value == "minute"
        assert RateLimitWindow.HOUR.value == "hour"
        assert RateLimitWindow.DAY.value == "day"

    def test_api_key_create_request_validation_comprehensive(self):
        """Test comprehensive validation for APIKeyCreateRequest."""
        # Valid minimal request
        request = APIKeyCreateRequest(
            name="Test Key",
            scopes=[APIKeyScope.READ_USERS.value]
        )
        assert request.name == "Test Key"
        assert request.scopes == [APIKeyScope.READ_USERS.value]
        assert request.description is None
        assert request.expires_in_days is None
        assert request.rate_limit_requests == 1000
        assert request.rate_limit_window == RateLimitWindow.HOUR
        assert request.allowed_ips is None
        assert request.require_https is True
        assert request.tenant_id is None

    def test_api_key_create_request_full_configuration(self):
        """Test APIKeyCreateRequest with all fields."""
        request = APIKeyCreateRequest(
            name="Full Configuration Key",
            description="Comprehensive test key",
            scopes=[APIKeyScope.READ_USERS.value, APIKeyScope.WRITE_USERS.value],
            expires_in_days=30,
            rate_limit_requests=5000,
            rate_limit_window=RateLimitWindow.DAY,
            allowed_ips=["192.168.1.1", "10.0.0.0/24"],
            require_https=False,
            tenant_id="tenant-123"
        )

        assert request.name == "Full Configuration Key"
        assert request.description == "Comprehensive test key"
        assert len(request.scopes) == 2
        assert request.expires_in_days == 30
        assert request.rate_limit_requests == 5000
        assert request.rate_limit_window == RateLimitWindow.DAY
        assert len(request.allowed_ips) == 2
        assert request.require_https is False
        assert request.tenant_id == "tenant-123"

    def test_api_key_create_request_invalid_scopes(self):
        """Test APIKeyCreateRequest with invalid scopes."""
        with pytest.raises(ValidationError) as exc_info:
            APIKeyCreateRequest(
                name="Invalid Scopes",
                scopes=["invalid:scope", "another:bad:scope"]
            )

        error_detail = str(exc_info.value)
        assert "Invalid scopes" in error_detail

    def test_api_key_create_request_boundary_values(self):
        """Test APIKeyCreateRequest boundary value validation."""
        # Minimum name length
        request_min = APIKeyCreateRequest(
            name="A",
            scopes=[APIKeyScope.READ_USERS.value]
        )
        assert request_min.name == "A"

        # Maximum name length
        long_name = "A" * 100
        request_max = APIKeyCreateRequest(
            name=long_name,
            scopes=[APIKeyScope.READ_USERS.value]
        )
        assert request_max.name == long_name

        # Name too long
        with pytest.raises(ValidationError):
            APIKeyCreateRequest(
                name="A" * 101,
                scopes=[APIKeyScope.READ_USERS.value]
            )

        # Empty scopes
        with pytest.raises(ValidationError):
            APIKeyCreateRequest(
                name="Test",
                scopes=[]
            )

        # Rate limit boundaries
        request_min_rate = APIKeyCreateRequest(
            name="Min Rate",
            scopes=[APIKeyScope.READ_USERS.value],
            rate_limit_requests=1
        )
        assert request_min_rate.rate_limit_requests == 1

        request_max_rate = APIKeyCreateRequest(
            name="Max Rate",
            scopes=[APIKeyScope.READ_USERS.value],
            rate_limit_requests=100000
        )
        assert request_max_rate.rate_limit_requests == 100000

    def test_api_key_update_request_validation(self):
        """Test APIKeyUpdateRequest validation."""
        # All None values (valid)
        request = APIKeyUpdateRequest()
        assert request.name is None
        assert request.description is None
        assert request.scopes is None
        assert request.status is None

        # Partial update
        request_partial = APIKeyUpdateRequest(
            name="Updated Name",
            status=APIKeyStatus.SUSPENDED
        )
        assert request_partial.name == "Updated Name"
        assert request_partial.status == APIKeyStatus.SUSPENDED
        assert request_partial.description is None

    def test_api_key_validation_model(self):
        """Test APIKeyValidation model."""
        validation = APIKeyValidation(
            key="dm_test_key_123",
            required_scopes=[APIKeyScope.READ_USERS.value]
        )
        assert validation.key == "dm_test_key_123"
        assert validation.required_scopes == [APIKeyScope.READ_USERS.value]

        # With None scopes
        validation_no_scopes = APIKeyValidation(key="dm_key_456")
        assert validation_no_scopes.key == "dm_key_456"
        assert validation_no_scopes.required_scopes is None

    def test_api_key_response_models(self):
        """Test API key response models."""
        now = datetime.now(UTC)

        # Standard response
        response = APIKeyResponse(
            id="key-123",
            name="Test Key",
            description="Test description",
            key_id="kid_123",
            key_prefix="dm_abc",
            status=APIKeyStatus.ACTIVE,
            scopes=[APIKeyScope.READ_USERS.value],
            created_at=now,
            expires_at=now + timedelta(days=90),
            last_used=now - timedelta(hours=1),
            total_requests=150,
            failed_requests=5,
            rate_limit_requests=1000,
            rate_limit_window=RateLimitWindow.HOUR,
            tenant_id="tenant-123"
        )

        assert response.id == "key-123"
        assert response.status == APIKeyStatus.ACTIVE
        assert response.total_requests == 150
        assert response.failed_requests == 5

        # Create response (includes API key)
        create_response = APIKeyCreateResponse(
            id="key-456",
            name="New Key",
            description=None,
            key_id="kid_456",
            key_prefix="dm_xyz",
            status=APIKeyStatus.ACTIVE,
            scopes=[APIKeyScope.API_INTERNAL.value],
            created_at=now,
            expires_at=None,
            last_used=None,
            total_requests=0,
            failed_requests=0,
            rate_limit_requests=5000,
            rate_limit_window=RateLimitWindow.DAY,
            tenant_id=None,
            api_key="dm_secret_full_key_123456789"
        )

        assert create_response.api_key == "dm_secret_full_key_123456789"
        assert create_response.expires_at is None


class TestAPIKeyServiceConfiguration:
    """Test API key service configuration."""

    def test_service_config_defaults(self):
        """Test service configuration defaults."""
        config = settings.APIKeyService.model_copy()

        assert config.key_length == 32
        assert config.default_expiry_days == 90
        assert config.max_keys_per_user == 10
        assert config.rate_limit_cleanup_interval_hours == 24
        assert config.usage_log_retention_days == 90
        assert config.require_scope_validation is True

    def test_service_config_custom_values(self):
        """Test service configuration with custom values."""
        config = settings.APIKeyService.model_copy(update={
            key_length=64,
            default_expiry_days=365,
            max_keys_per_user=20,
            rate_limit_cleanup_interval_hours=12,
            usage_log_retention_days=180,
            require_scope_validation=False
        })

        assert config.key_length == 64
        assert config.default_expiry_days == 365
        assert config.max_keys_per_user == 20
        assert config.rate_limit_cleanup_interval_hours == 12
        assert config.usage_log_retention_days == 180
        assert config.require_scope_validation is False


class TestAPIKeyHelperFunctions:
    """Test module-level helper functions."""

    def test_generate_api_key_format(self):
        """Test API key generation format and uniqueness."""
        key1 = generate_api_key()
        key2 = generate_api_key()

        # Format check
        assert key1.startswith("sk_")
        assert key2.startswith("sk_")

        # Length check (sk_ + base64 encoded bytes)
        assert len(key1) > 35
        assert len(key2) > 35

        # Uniqueness
        assert key1 != key2

    def test_hash_api_key_consistency(self):
        """Test API key hashing consistency."""
        key = "dm_test_key_12345"
        expected_hash = hashlib.sha256(key.encode()).hexdigest()

        # Test multiple calls return same hash
        hash1 = hash_api_key(key)
        hash2 = hash_api_key(key)

        assert hash1 == hash2 == expected_hash
        assert len(hash1) == 64  # SHA-256 hex length

    def test_verify_api_key_scenarios(self):
        """Test API key verification scenarios."""
        key = "dm_test_verification_key"
        correct_hash = hash_api_key(key)
        wrong_hash = hash_api_key("dm_different_key")

        # Correct verification
        assert verify_api_key(key, correct_hash) is True

        # Wrong verification
        assert verify_api_key(key, wrong_hash) is False

        # Edge cases
        assert verify_api_key("", hash_api_key("")) is True
        assert verify_api_key("key", "invalid_hash") is False


class TestAPIKeyServiceCore:
    """Test core API key service functionality."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = Mock()
        return db

    @pytest.fixture
    def mock_rbac(self):
        """Mock RBAC service."""
        rbac = MagicMock()
        rbac.check_permission = AsyncMock(return_value=True)
        return rbac

    @pytest.fixture
    def service_config(self):
        """Service configuration for testing."""
        return settings.APIKeyService.model_copy(update={
            key_length=32,
            default_expiry_days=90,
            max_keys_per_user=5,
            require_scope_validation=True
        })

    @pytest.fixture
    def api_key_service(self, mock_db, service_config, mock_rbac):
        """API key service instance for testing."""
        return APIKeyService(
            database_session=mock_db,
            config=service_config,
            rbac_service=mock_rbac
        )

    def test_service_initialization(self, mock_db, service_config):
        """Test service initialization."""
        service = APIKeyService(
            database_session=mock_db,
            config=service_config
        )

        assert service.db == mock_db
        assert service.config == service_config
        assert service.rbac is None

    def test_service_initialization_defaults(self):
        """Test service initialization with defaults."""
        service = APIKeyService()

        assert service.db is None
        assert isinstance(service.config, APIKeyServiceConfig)
        assert service.rbac is None

    def test_generate_api_key_method(self, api_key_service):
        """Test internal API key generation method."""
        key = api_key_service._generate_api_key()

        assert key.startswith("dm_")
        assert len(key) > len("dm_")

    def test_generate_key_id_method(self, api_key_service):
        """Test internal key ID generation method."""
        key_id1 = api_key_service._generate_key_id()
        key_id2 = api_key_service._generate_key_id()

        assert isinstance(key_id1, str)
        assert isinstance(key_id2, str)
        assert len(key_id1) > 0
        assert len(key_id2) > 0
        assert key_id1 != key_id2  # Should be unique

    def test_hash_api_key_method(self, api_key_service):
        """Test internal key hashing method."""
        key = "test_key_hash"
        expected = hashlib.sha256(key.encode()).hexdigest()

        result = api_key_service._hash_api_key(key)

        assert result == expected
        assert len(result) == 64

    def test_ip_allowlist_validation(self, api_key_service):
        """Test IP allowlist validation logic."""
        # Exact match
        assert api_key_service._is_ip_allowed("192.168.1.100", ["192.168.1.100"]) is True
        assert api_key_service._is_ip_allowed("192.168.1.100", ["192.168.1.101"]) is False

        # Wildcard
        assert api_key_service._is_ip_allowed("192.168.1.100", ["*"]) is True
        assert api_key_service._is_ip_allowed("10.0.0.1", ["*"]) is True

        # Multiple IPs
        allowed_ips = ["192.168.1.100", "10.0.0.1", "172.16.0.1"]
        assert api_key_service._is_ip_allowed("192.168.1.100", allowed_ips) is True
        assert api_key_service._is_ip_allowed("10.0.0.1", allowed_ips) is True
        assert api_key_service._is_ip_allowed("203.0.113.1", allowed_ips) is False

        # Empty allowlist
        assert api_key_service._is_ip_allowed("192.168.1.1", []) is False

    def test_create_key_sync_helper(self, api_key_service):
        """Test synchronous create_key helper method."""
        key = api_key_service.create_key(
            user_id="user-123",
            name="Sync Test Key",
            scopes=[APIKeyScope.READ_USERS.value]
        )

        assert key.startswith("dm_")
        assert len(key) > len("dm_")

    @pytest.mark.asyncio
    async def test_validate_user_scopes_no_rbac(self, api_key_service):
        """Test scope validation without RBAC service."""
        api_key_service.rbac = None

        # Should not raise when RBAC is None
        await api_key_service._validate_user_scopes(
            "user-123",
            [APIKeyScope.READ_USERS.value, APIKeyScope.WRITE_USERS.value]
        )

    @pytest.mark.asyncio
    async def test_validate_user_scopes_with_rbac_success(self, api_key_service, mock_rbac):
        """Test successful scope validation with RBAC."""
        scopes = [APIKeyScope.READ_USERS.value, APIKeyScope.WRITE_USERS.value]

        await api_key_service._validate_user_scopes("user-123", scopes)

        # Should check each scope
        assert mock_rbac.check_permission.call_count == 2

    @pytest.mark.asyncio
    async def test_validate_user_scopes_with_rbac_failure(self, api_key_service, mock_rbac):
        """Test scope validation failure with RBAC."""
        mock_rbac.check_permission = AsyncMock(side_effect=[True, False])

        with pytest.raises(AuthorizationError) as exc_info:
            await api_key_service._validate_user_scopes(
                "user-123",
                [APIKeyScope.READ_USERS.value, APIKeyScope.ADMIN_SYSTEM.value]
            )

        assert "does not have permission for scope" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_user_api_keys_filtering(self, api_key_service, mock_db):
        """Test user API keys retrieval with filtering."""
        # Mock database query
        mock_keys = [
            Mock(status=APIKeyStatus.ACTIVE.value),
            Mock(status=APIKeyStatus.ACTIVE.value),
            Mock(status=APIKeyStatus.REVOKED.value),
            Mock(status=APIKeyStatus.SUSPENDED.value)
        ]

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_keys
        mock_db.query.return_value = mock_query

        # Test active only
        result_active = await api_key_service._get_user_api_keys("user-123", active_only=True)
        # Test all keys
        result_all = await api_key_service._get_user_api_keys("user-123", active_only=False)

        # Should call query with appropriate filters
        assert mock_db.query.called


class TestAPIKeyServiceAuthentication:
    """Test API key authentication and authorization."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = MagicMock()
        db.commit = AsyncMock()
        db.add = Mock()
        return db

    @pytest.fixture
    def api_key_service(self, mock_db):
        """API key service for authentication tests."""
        config = settings.APIKeyService.model_copy(update={require_scope_validation=False})
        return APIKeyService(database_session=mock_db, config=config)

    @pytest.mark.asyncio
    async def test_authenticate_api_key_success(self, api_key_service, mock_db):
        """Test successful API key authentication."""
        # Create mock API key
        test_key = "dm_test_key_12345"
        key_hash = hash_api_key(test_key)

        mock_key = Mock()
        mock_key.key_hash = key_hash
        mock_key.status = APIKeyStatus.ACTIVE.value
        mock_key.expires_at = None
        mock_key.allowed_ips = None
        mock_key.require_https = True
        mock_key.key_id = "kid_123"
        mock_key.user_id = uuid4()
        mock_key.tenant_id = uuid4()
        mock_key.scopes = [APIKeyScope.READ_USERS.value]
        mock_key.name = "Test Key"
        mock_key.last_used = None
        mock_key.total_requests = 0

        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_key
        mock_db.query.return_value = mock_query

        # Mock rate limit check
        with patch.object(api_key_service, '_check_rate_limit', new_callable=AsyncMock):
            with patch.object(api_key_service, '_log_failed_authentication', new_callable=AsyncMock):
                result = await api_key_service.authenticate_api_key(
                    test_key,
                    {"ip_address": "192.168.1.1", "is_https": True}
                )

        assert result["key_id"] == "kid_123"
        assert result["user_id"] == str(mock_key.user_id)
        assert result["scopes"] == [APIKeyScope.READ_USERS.value]

    @pytest.mark.asyncio
    async def test_authenticate_api_key_invalid(self, api_key_service, mock_db):
        """Test authentication with invalid API key."""
        # Mock database query returning None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        with patch.object(api_key_service, '_log_failed_authentication', new_callable=AsyncMock):
            with pytest.raises(AuthenticationError) as exc_info:
                await api_key_service.authenticate_api_key("invalid_key")

        assert "Invalid API key" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_authenticate_api_key_suspended(self, api_key_service, mock_db):
        """Test authentication with suspended API key."""
        test_key = "dm_suspended_key"
        key_hash = hash_api_key(test_key)

        mock_key = Mock()
        mock_key.key_hash = key_hash
        mock_key.status = APIKeyStatus.SUSPENDED.value

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_key
        mock_db.query.return_value = mock_query

        with patch.object(api_key_service, '_log_failed_authentication', new_callable=AsyncMock):
            with pytest.raises(AuthenticationError) as exc_info:
                await api_key_service.authenticate_api_key(test_key)

        assert "suspended" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_authenticate_api_key_expired(self, api_key_service, mock_db):
        """Test authentication with expired API key."""
        test_key = "dm_expired_key"
        key_hash = hash_api_key(test_key)

        mock_key = Mock()
        mock_key.key_hash = key_hash
        mock_key.status = APIKeyStatus.ACTIVE.value
        mock_key.expires_at = datetime.now(UTC) - timedelta(hours=1)  # Expired

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_key
        mock_db.query.return_value = mock_query

        with patch.object(api_key_service, '_log_failed_authentication', new_callable=AsyncMock):
            with pytest.raises(AuthenticationError) as exc_info:
                await api_key_service.authenticate_api_key(test_key)

        assert "expired" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_authenticate_api_key_ip_restriction(self, api_key_service, mock_db):
        """Test authentication with IP restrictions."""
        test_key = "dm_ip_restricted_key"
        key_hash = hash_api_key(test_key)

        mock_key = Mock()
        mock_key.key_hash = key_hash
        mock_key.status = APIKeyStatus.ACTIVE.value
        mock_key.expires_at = None
        mock_key.allowed_ips = ["192.168.1.100"]  # Specific IP only
        mock_key.require_https = True

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_key
        mock_db.query.return_value = mock_query

        with patch.object(api_key_service, '_log_failed_authentication', new_callable=AsyncMock):
            with pytest.raises(AuthenticationError) as exc_info:
                await api_key_service.authenticate_api_key(
                    test_key,
                    {"ip_address": "192.168.1.200"}  # Different IP
                )

        assert "IP address not allowed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_authenticate_api_key_https_required(self, api_key_service, mock_db):
        """Test authentication with HTTPS requirement."""
        test_key = "dm_https_required_key"
        key_hash = hash_api_key(test_key)

        mock_key = Mock()
        mock_key.key_hash = key_hash
        mock_key.status = APIKeyStatus.ACTIVE.value
        mock_key.expires_at = None
        mock_key.allowed_ips = None
        mock_key.require_https = True

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_key
        mock_db.query.return_value = mock_query

        with patch.object(api_key_service, '_log_failed_authentication', new_callable=AsyncMock):
            with pytest.raises(AuthenticationError) as exc_info:
                await api_key_service.authenticate_api_key(
                    test_key,
                    {"is_https": False}  # Not HTTPS
                )

        assert "HTTPS required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_check_permission_scenarios(self, api_key_service):
        """Test permission checking scenarios."""
        key_info = {
            "key_id": "kid_123",
            "user_id": "user-123",
            "tenant_id": "tenant-123",
            "scopes": [APIKeyScope.READ_USERS.value, APIKeyScope.WRITE_USERS.value],
            "key_name": "Test Key"
        }

        # Has permission
        assert await api_key_service.check_permission(
            key_info, APIKeyScope.READ_USERS.value
        ) is True

        # No permission
        assert await api_key_service.check_permission(
            key_info, APIKeyScope.ADMIN_SYSTEM.value
        ) is False

        # Tenant isolation - same tenant
        assert await api_key_service.check_permission(
            key_info, APIKeyScope.READ_USERS.value, "tenant-123"
        ) is True

        # Tenant isolation - different tenant
        assert await api_key_service.check_permission(
            key_info, APIKeyScope.READ_USERS.value, "tenant-456"
        ) is False


class TestAPIKeyServiceRateLimiting:
    """Test API key rate limiting functionality."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = MagicMock()
        db.commit = AsyncMock()
        db.add = Mock()
        return db

    @pytest.fixture
    def api_key_service(self, mock_db):
        """API key service for rate limiting tests."""
        return APIKeyService(database_session=mock_db)

    @pytest.mark.asyncio
    async def test_rate_limit_new_window(self, api_key_service, mock_db):
        """Test rate limiting with new time window."""
        mock_key = Mock()
        mock_key.id = uuid4()
        mock_key.rate_limit_requests = 100
        mock_key.rate_limit_window = RateLimitWindow.HOUR.value

        # No existing rate limit record
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        # Should not raise (creates new record)
        await api_key_service._check_rate_limit(mock_key, {})

        # Should add new rate limit record
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limit_under_limit(self, api_key_service, mock_db):
        """Test rate limiting when under the limit."""
        mock_key = Mock()
        mock_key.id = uuid4()
        mock_key.rate_limit_requests = 100
        mock_key.rate_limit_window = RateLimitWindow.HOUR.value

        # Existing rate limit record under limit
        mock_rate_limit = Mock()
        mock_rate_limit.request_count = 50

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_rate_limit
        mock_db.query.return_value = mock_query

        # Should not raise
        await api_key_service._check_rate_limit(mock_key, {})

        # Should increment counter
        assert mock_rate_limit.request_count == 51

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, api_key_service, mock_db):
        """Test rate limiting when limit is exceeded."""
        mock_key = Mock()
        mock_key.id = uuid4()
        mock_key.rate_limit_requests = 100
        mock_key.rate_limit_window = RateLimitWindow.HOUR.value

        # Existing rate limit record at limit
        mock_rate_limit = Mock()
        mock_rate_limit.request_count = 100

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_rate_limit
        mock_db.query.return_value = mock_query

        with patch.object(api_key_service, '_log_failed_authentication', new_callable=AsyncMock):
            with pytest.raises(RateLimitError) as exc_info:
                await api_key_service._check_rate_limit(mock_key, {})

        assert "Rate limit exceeded" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rate_limit_window_calculations(self, api_key_service, mock_db):
        """Test rate limit window calculations."""
        mock_key = Mock()
        mock_key.id = uuid4()
        mock_key.rate_limit_requests = 100

        # Test different window types
        for window in [RateLimitWindow.MINUTE, RateLimitWindow.HOUR, RateLimitWindow.DAY]:
            mock_key.rate_limit_window = window.value

            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = None
            mock_db.query.return_value = mock_query

            # Should not raise
            await api_key_service._check_rate_limit(mock_key, {})


class TestAPIKeyServiceCRUDOperations:
    """Test CRUD operations for API keys."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = Mock()
        return db

    @pytest.fixture
    def api_key_service(self, mock_db):
        """API key service for CRUD tests."""
        config = settings.APIKeyService.model_copy(update={max_keys_per_user=5})
        return APIKeyService(database_session=mock_db, config=config)

    @pytest.mark.asyncio
    async def test_create_api_key_success(self, api_key_service, mock_db):
        """Test successful API key creation."""
        # Mock user has no existing keys
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        # Mock database key creation
        mock_db_key = Mock()
        mock_db_key.id = uuid4()
        mock_db_key.name = "Test Key"
        mock_db_key.description = "Test description"
        mock_db_key.key_id = "kid_123"
        mock_db_key.key_prefix = "dm_abc123"
        mock_db_key.status = APIKeyStatus.ACTIVE.value
        mock_db_key.scopes = [APIKeyScope.READ_USERS.value]
        mock_db_key.created_at = datetime.now(UTC)
        mock_db_key.expires_at = None
        mock_db_key.last_used = None
        mock_db_key.total_requests = 0
        mock_db_key.failed_requests = 0
        mock_db_key.rate_limit_requests = 1000
        mock_db_key.rate_limit_window = RateLimitWindow.HOUR.value
        mock_db_key.tenant_id = None

        mock_db.refresh = AsyncMock(side_effect=lambda obj: setattr(obj, 'id', mock_db_key.id))

        request = APIKeyCreateRequest(
            name="Test Key",
            description="Test description",
            scopes=[APIKeyScope.READ_USERS.value]
        )

        with patch.object(api_key_service.db, 'add') as mock_add:
            # Mock the APIKey constructor to return our mock
            with patch('src.dotmac.platform.auth.api_keys.APIKey', return_value=mock_db_key):
                result = await api_key_service.create_api_key(
                    user_id="user-123",
                    created_by="admin-456",
                    request=request
                )

        assert isinstance(result, APIKeyCreateResponse)
        assert result.name == "Test Key"
        assert result.api_key.startswith("dm_")

    @pytest.mark.asyncio
    async def test_create_api_key_max_limit(self, api_key_service, mock_db):
        """Test API key creation when max limit reached."""
        # Mock user has maximum keys
        existing_keys = [Mock() for _ in range(5)]  # Max is 5

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = existing_keys
        mock_db.query.return_value = mock_query

        request = APIKeyCreateRequest(
            name="Over Limit Key",
            scopes=[APIKeyScope.READ_USERS.value]
        )

        with pytest.raises(AuthValidationError) as exc_info:
            await api_key_service.create_api_key(
                user_id="user-123",
                created_by="admin-456",
                request=request
            )

        assert "Maximum API keys limit" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_api_keys_filtering(self, api_key_service, mock_db):
        """Test getting API keys with filtering."""
        # Create proper mock objects with actual values (not nested Mocks)
        key1_id = uuid4()
        key2_id = uuid4()

        mock_key1 = Mock()
        mock_key1.id = key1_id
        mock_key1.name = "Active Key 1"
        mock_key1.description = "Description 1"
        mock_key1.key_id = "kid_1"
        mock_key1.key_prefix = "dm_abc"
        mock_key1.status = APIKeyStatus.ACTIVE.value
        mock_key1.scopes = [APIKeyScope.READ_USERS.value]
        mock_key1.created_at = datetime.now(UTC)
        mock_key1.expires_at = None
        mock_key1.last_used = None
        mock_key1.total_requests = 100
        mock_key1.failed_requests = 5
        mock_key1.rate_limit_requests = 1000
        mock_key1.rate_limit_window = RateLimitWindow.HOUR.value
        mock_key1.tenant_id = None

        mock_key2 = Mock()
        mock_key2.id = key2_id
        mock_key2.name = "Suspended Key"
        mock_key2.description = "Description 2"
        mock_key2.key_id = "kid_2"
        mock_key2.key_prefix = "dm_def"
        mock_key2.status = APIKeyStatus.SUSPENDED.value
        mock_key2.scopes = [APIKeyScope.WRITE_USERS.value]
        mock_key2.created_at = datetime.now(UTC)
        mock_key2.expires_at = None
        mock_key2.last_used = None
        mock_key2.total_requests = 50
        mock_key2.failed_requests = 2
        mock_key2.rate_limit_requests = 500
        mock_key2.rate_limit_window = RateLimitWindow.DAY.value
        mock_key2.tenant_id = None

        mock_keys = [mock_key1, mock_key2]

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_keys
        mock_db.query.return_value = mock_query

        # Test getting all keys
        result_all = await api_key_service.get_api_keys("user-123", include_inactive=True)
        assert len(result_all) == 2

        # Test getting active only - reset the mock to return only active key
        mock_query_active = Mock()
        mock_query_active.filter.return_value = mock_query_active
        mock_query_active.order_by.return_value = mock_query_active
        mock_query_active.all.return_value = [mock_key1]  # Only active
        mock_db.query.return_value = mock_query_active

        result_active = await api_key_service.get_api_keys("user-123", include_inactive=False)
        assert len(result_active) == 1
        assert result_active[0].status == "active"

    @pytest.mark.asyncio
    async def test_update_api_key_success(self, api_key_service, mock_db):
        """Test successful API key update."""
        # Mock existing key
        mock_key = Mock()
        mock_key.id = uuid4()
        mock_key.name = "Original Name"
        mock_key.description = "Original description"
        mock_key.key_id = "kid_123"
        mock_key.key_prefix = "dm_abc"
        mock_key.status = APIKeyStatus.ACTIVE.value
        mock_key.scopes = [APIKeyScope.READ_USERS.value]
        mock_key.created_at = datetime.now(UTC)
        mock_key.expires_at = None
        mock_key.last_used = None
        mock_key.total_requests = 100
        mock_key.failed_requests = 5
        mock_key.rate_limit_requests = 1000
        mock_key.rate_limit_window = RateLimitWindow.HOUR.value
        mock_key.tenant_id = None

        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_key
        mock_db.query.return_value = mock_query

        update_request = APIKeyUpdateRequest(
            name="Updated Name",
            description="Updated description",
            status=APIKeyStatus.SUSPENDED
        )

        result = await api_key_service.update_api_key(
            user_id="user-123",
            key_id="kid_123",
            request=update_request
        )

        assert isinstance(result, APIKeyResponse)
        # The mock object should have been updated
        assert mock_key.name == "Updated Name"
        assert mock_key.description == "Updated description"
        assert mock_key.status == APIKeyStatus.SUSPENDED.value

    @pytest.mark.asyncio
    async def test_update_api_key_not_found(self, api_key_service, mock_db):
        """Test updating non-existent API key."""
        # Mock database query returning None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        update_request = APIKeyUpdateRequest(name="Updated Name")

        with pytest.raises(AuthenticationError) as exc_info:
            await api_key_service.update_api_key(
                user_id="user-123",
                key_id="nonexistent",
                request=update_request
            )

        assert "API key not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rotate_api_key_success(self, api_key_service, mock_db):
        """Test successful API key rotation."""
        # Mock existing key
        old_key = Mock()
        old_key.id = uuid4()
        old_key.name = "Rotated Key"
        old_key.description = "Key to rotate"
        old_key.status = APIKeyStatus.ACTIVE.value
        old_key.scopes = [APIKeyScope.READ_USERS.value]
        old_key.expires_at = None
        old_key.rate_limit_requests = 1000
        old_key.rate_limit_window = RateLimitWindow.HOUR.value
        old_key.allowed_ips = None
        old_key.require_https = True
        old_key.tenant_id = None
        old_key.user_id = uuid4()
        old_key.created_by = uuid4()

        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = old_key
        mock_db.query.return_value = mock_query

        # Mock new key creation
        new_key = Mock()
        new_key.id = uuid4()
        new_key.name = old_key.name
        new_key.description = old_key.description
        new_key.key_id = "new_kid_123"
        new_key.key_prefix = "dm_xyz"
        new_key.status = APIKeyStatus.ACTIVE.value
        new_key.scopes = old_key.scopes
        new_key.created_at = datetime.now(UTC)
        new_key.expires_at = old_key.expires_at
        new_key.last_used = None
        new_key.total_requests = 0
        new_key.failed_requests = 0
        new_key.rate_limit_requests = old_key.rate_limit_requests
        new_key.rate_limit_window = old_key.rate_limit_window
        new_key.tenant_id = old_key.tenant_id

        with patch('src.dotmac.platform.auth.api_keys.APIKey', return_value=new_key):
            result = await api_key_service.rotate_api_key(
                user_id=str(old_key.user_id),
                key_id="old_kid_123"
            )

        assert isinstance(result, APIKeyCreateResponse)
        assert result.api_key.startswith("dm_")
        assert old_key.status == APIKeyStatus.REVOKED.value

    @pytest.mark.asyncio
    async def test_revoke_api_key_success(self, api_key_service, mock_db):
        """Test successful API key revocation."""
        # Mock existing key
        mock_key = Mock()
        mock_key.id = uuid4()
        mock_key.status = APIKeyStatus.ACTIVE.value

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_key
        mock_db.query.return_value = mock_query

        result = await api_key_service.revoke_api_key(
            user_id="user-123",
            key_id="kid_123"
        )

        assert result is True
        assert mock_key.status == APIKeyStatus.REVOKED.value


class TestAPIKeyServiceUsageTracking:
    """Test API key usage tracking and analytics."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = MagicMock()
        db.commit = AsyncMock()
        db.add = Mock()
        return db

    @pytest.fixture
    def api_key_service(self, mock_db):
        """API key service for usage tracking tests."""
        return APIKeyService(database_session=mock_db)

    @pytest.mark.asyncio
    async def test_get_api_key_usage(self, api_key_service, mock_db):
        """Test getting API key usage statistics."""
        # Mock existing key
        mock_key = Mock()
        mock_key.id = uuid4()

        mock_usage_logs = [
            Mock(
                timestamp=datetime.now(UTC),
                method="GET",
                path="/api/users",
                status_code=200,
                response_time_ms=150,
                ip_address="192.168.1.1",
                error_message=None
            ),
            Mock(
                timestamp=datetime.now(UTC) - timedelta(hours=1),
                method="POST",
                path="/api/users",
                status_code=201,
                response_time_ms=250,
                ip_address="192.168.1.2",
                error_message=None
            )
        ]

        # Mock database queries
        user_query = Mock()
        user_query.filter.return_value = user_query
        user_query.first.return_value = mock_key

        usage_query = Mock()
        usage_query.filter.return_value = usage_query
        usage_query.order_by.return_value = usage_query
        usage_query.limit.return_value = usage_query
        usage_query.all.return_value = mock_usage_logs

        mock_db.query.side_effect = [user_query, usage_query]

        result = await api_key_service.get_api_key_usage(
            user_id="user-123",
            key_id="kid_123",
            days=30
        )

        assert len(result) == 2
        assert result[0]["method"] == "GET"
        assert result[0]["path"] == "/api/users"
        assert result[0]["status_code"] == 200

    @pytest.mark.asyncio
    async def test_log_api_key_usage_success(self, api_key_service, mock_db):
        """Test logging API key usage."""
        # Mock existing key
        mock_key = Mock()
        mock_key.id = uuid4()
        mock_key.failed_requests = 5

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_key
        mock_db.query.return_value = mock_query

        key_info = {
            "key_id": "kid_123",
            "tenant_id": "tenant-123"
        }

        request_info = {
            "method": "GET",
            "path": "/api/users",
            "ip_address": "192.168.1.1",
            "user_agent": "Test Agent"
        }

        response_info = {
            "status_code": 200,
            "response_time_ms": 150
        }

        await api_key_service.log_api_key_usage(
            key_info=key_info,
            request_info=request_info,
            response_info=response_info
        )

        # Should add usage log
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_api_key_usage_error_response(self, api_key_service, mock_db):
        """Test logging API key usage for error response."""
        # Mock existing key
        mock_key = Mock()
        mock_key.id = uuid4()
        mock_key.failed_requests = 5

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_key
        mock_db.query.return_value = mock_query

        key_info = {"key_id": "kid_123"}
        request_info = {"method": "POST", "path": "/api/users"}
        response_info = {
            "status_code": 400,  # Error response
            "error_message": "Validation failed"
        }

        await api_key_service.log_api_key_usage(
            key_info=key_info,
            request_info=request_info,
            response_info=response_info
        )

        # Should increment failed requests
        assert mock_key.failed_requests == 6

    @pytest.mark.asyncio
    async def test_log_api_key_usage_missing_key(self, api_key_service, mock_db):
        """Test logging usage for non-existent key."""
        # Mock database query returning None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        key_info = {"key_id": "nonexistent"}
        request_info = {"method": "GET", "path": "/api/test"}
        response_info = {"status_code": 200}

        # Should not raise error, just return
        await api_key_service.log_api_key_usage(
            key_info=key_info,
            request_info=request_info,
            response_info=response_info
        )

        # Should not add anything
        mock_db.add.assert_not_called()


class TestAPIKeyHelperDecoratorsAndDependencies:
    """Test API key helper functions, decorators, and FastAPI dependencies."""

    def test_api_key_required_decorator(self):
        """Test API key required decorator."""
        @api_key_required(scopes=[APIKeyScope.READ_USERS.value])
        async def test_function():
            return "success"

        # Decorator should wrap function without error
        assert callable(test_function)

    def test_extract_api_key_from_authorization_header(self):
        """Test extracting API key from Authorization header."""
        # Mock request with Authorization header
        mock_request = Mock()
        mock_request.headers = {"Authorization": "ApiKey dm_test_key_123"}

        result = extract_api_key_from_request(mock_request)
        assert result == "dm_test_key_123"

    def test_extract_api_key_from_x_api_key_header(self):
        """Test extracting API key from X-API-Key header."""
        # Mock request with X-API-Key header
        mock_request = Mock()
        mock_request.headers = {"X-API-Key": "dm_test_key_456"}

        result = extract_api_key_from_request(mock_request)
        assert result == "dm_test_key_456"

    def test_extract_api_key_from_x_api_key_alternative(self):
        """Test extracting API key from X-Api-Key header (alternative casing)."""
        # Mock request with X-Api-Key header
        mock_request = Mock()
        mock_request.headers = {"X-Api-Key": "dm_test_key_789"}

        result = extract_api_key_from_request(mock_request)
        assert result == "dm_test_key_789"

    def test_extract_api_key_no_header(self):
        """Test extracting API key when no header is present."""
        # Mock request with no API key headers
        mock_request = Mock()
        mock_request.headers = {"Content-Type": "application/json"}

        result = extract_api_key_from_request(mock_request)
        assert result is None

    def test_extract_api_key_malformed_authorization(self):
        """Test extracting API key from malformed Authorization header."""
        # Mock request with malformed Authorization header
        mock_request = Mock()
        mock_request.headers = {"Authorization": "Bearer token123"}  # Wrong format

        result = extract_api_key_from_request(mock_request)
        assert result is None

    @pytest.mark.asyncio
    async def test_api_key_dependency_success(self):
        """Test successful API key dependency validation."""
        # Create dependency function
        dependency = api_key_dependency(required_scopes=[APIKeyScope.READ_USERS.value])

        # Mock request
        mock_request = Mock()
        mock_request.headers = {"X-API-Key": "dm_test_key_123"}
        mock_request.method = "GET"
        mock_request.url.path = "/api/users"
        mock_request.client.host = "192.168.1.1"
        mock_request.state = Mock()

        # Mock app with API key service
        mock_service = Mock()
        mock_service.authenticate_api_key = AsyncMock(return_value={
            "key_id": "kid_123",
            "user_id": "user-123",
            "scopes": [APIKeyScope.READ_USERS.value, APIKeyScope.WRITE_USERS.value],
            "key_name": "Test Key"
        })

        mock_app = Mock()
        mock_app.state.api_key_service = mock_service
        mock_request.app = mock_app

        # Test dependency
        result = await dependency(mock_request)

        assert result["key_id"] == "kid_123"
        assert result["user_id"] == "user-123"
        assert hasattr(mock_request.state, 'api_key_info')

    @pytest.mark.asyncio
    async def test_api_key_dependency_missing_key(self):
        """Test API key dependency when key is missing."""
        dependency = api_key_dependency()

        # Mock request without API key
        mock_request = Mock()
        mock_request.headers = {}

        # Should raise HTTPException
        with pytest.raises(Exception):  # HTTPException if FastAPI is available
            await dependency(mock_request)

    @pytest.mark.asyncio
    async def test_api_key_dependency_insufficient_scopes(self):
        """Test API key dependency with insufficient scopes."""
        dependency = api_key_dependency(required_scopes=[APIKeyScope.ADMIN_SYSTEM.value])

        # Mock request
        mock_request = Mock()
        mock_request.headers = {"X-API-Key": "dm_test_key_123"}
        mock_request.method = "GET"
        mock_request.url.path = "/api/admin"
        mock_request.client.host = "192.168.1.1"

        # Mock app with API key service
        mock_service = Mock()
        mock_service.authenticate_api_key = AsyncMock(return_value={
            "key_id": "kid_123",
            "user_id": "user-123",
            "scopes": [APIKeyScope.READ_USERS.value],  # Insufficient scopes
            "key_name": "Test Key"
        })

        mock_app = Mock()
        mock_app.state.api_key_service = mock_service
        mock_request.app = mock_app

        # Should raise HTTPException for insufficient scopes
        with pytest.raises(Exception):  # HTTPException if FastAPI is available
            await dependency(mock_request)


class TestAPIKeyServiceEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.fixture
    def api_key_service(self):
        """Basic API key service for edge case testing."""
        return APIKeyService()

    @pytest.mark.asyncio
    async def test_log_failed_authentication(self, api_key_service):
        """Test logging failed authentication attempts."""
        with patch('src.dotmac.platform.auth.api_keys.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            await api_key_service._log_failed_authentication(
                api_key="dm_test_key_123",
                reason="Invalid key",
                request_info={"ip_address": "192.168.1.1", "user_agent": "Test Agent"}
            )

            # Should log warning
            mock_logger.warning.assert_called_once()

    def test_check_api_rate_limit_helper(self):
        """Test check_api_rate_limit helper function."""
        from src.dotmac.platform.auth.api_keys import check_api_rate_limit

        key_info = {"key_id": "kid_123"}
        result = check_api_rate_limit(key_info)

        # Currently returns True (placeholder implementation)
        assert result is True

    def test_service_with_none_database(self):
        """Test service behavior with None database session."""
        service = APIKeyService(database_session=None)

        assert service.db is None
        assert isinstance(service.config, APIKeyServiceConfig)

    def test_generate_functions_randomness(self):
        """Test that generation functions produce random results."""
        # Test generate_api_key randomness
        keys = [generate_api_key() for _ in range(10)]
        assert len(set(keys)) == 10  # All unique

        # Test service key generation randomness
        service = APIKeyService()
        service_keys = [service._generate_api_key() for _ in range(10)]
        assert len(set(service_keys)) == 10  # All unique

        # Test key ID generation randomness
        key_ids = [service._generate_key_id() for _ in range(10)]
        assert len(set(key_ids)) == 10  # All unique


class TestDatabaseModels:
    """Test database model definitions."""

    def test_api_key_model_relationships(self):
        """Test APIKey model structure."""
        # Test that model is defined
        assert hasattr(APIKey, '__tablename__')
        assert APIKey.__tablename__ == "api_keys"

        # Test key fields exist
        assert hasattr(APIKey, 'id')
        assert hasattr(APIKey, 'name')
        assert hasattr(APIKey, 'key_id')
        assert hasattr(APIKey, 'key_hash')
        assert hasattr(APIKey, 'scopes')
        assert hasattr(APIKey, 'status')
        assert hasattr(APIKey, 'usage_logs')

    def test_api_key_usage_model_structure(self):
        """Test APIKeyUsage model structure."""
        assert hasattr(APIKeyUsage, '__tablename__')
        assert APIKeyUsage.__tablename__ == "api_key_usage"

        # Test key fields exist
        assert hasattr(APIKeyUsage, 'id')
        assert hasattr(APIKeyUsage, 'api_key_id')
        assert hasattr(APIKeyUsage, 'timestamp')
        assert hasattr(APIKeyUsage, 'method')
        assert hasattr(APIKeyUsage, 'path')
        assert hasattr(APIKeyUsage, 'status_code')
        assert hasattr(APIKeyUsage, 'api_key')

    def test_api_key_rate_limit_model_structure(self):
        """Test APIKeyRateLimit model structure."""
        assert hasattr(APIKeyRateLimit, '__tablename__')
        assert APIKeyRateLimit.__tablename__ == "api_key_rate_limits"

        # Test key fields exist
        assert hasattr(APIKeyRateLimit, 'id')
        assert hasattr(APIKeyRateLimit, 'api_key_id')
        assert hasattr(APIKeyRateLimit, 'window_start')
        assert hasattr(APIKeyRateLimit, 'window_type')
        assert hasattr(APIKeyRateLimit, 'request_count')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
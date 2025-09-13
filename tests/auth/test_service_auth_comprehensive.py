"""
Comprehensive tests for auth.service_auth module.

Tests ServiceIdentity, ServiceTokenManager, ServiceAuthMiddleware, and factory functions.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import jwt
import pytest
from fastapi import Request
from starlette.responses import JSONResponse

from dotmac.platform.auth.exceptions import (
    ConfigurationError,
    InvalidServiceToken,
    TokenExpired,
    UnauthorizedService,
)
from dotmac.platform.auth.service_auth import (
    ServiceAuthMiddleware,
    ServiceIdentity,
    ServiceTokenManager,
    create_service_token_manager,
)


class TestServiceIdentity:
    """Test ServiceIdentity class."""

    def test_service_identity_initialization(self):
        """Test ServiceIdentity initialization."""
        service_info = {"version": "1.0.0", "description": "Test service"}
        allowed_targets = ["service-a", "service-b"]
        allowed_operations = ["read", "write"]
        metadata = {"environment": "test"}

        identity = ServiceIdentity(
            service_name="test-service",
            service_info=service_info,
            allowed_targets=allowed_targets,
            allowed_operations=allowed_operations,
            metadata=metadata,
        )

        assert identity.service_name == "test-service"
        assert identity.service_info == service_info
        assert identity.allowed_targets == {"service-a", "service-b"}
        assert identity.allowed_operations == {"read", "write"}
        assert identity.metadata == metadata
        assert isinstance(identity.created_at, datetime)
        assert len(identity.identity_id) > 0

    def test_service_identity_default_metadata(self):
        """Test ServiceIdentity with default metadata."""
        identity = ServiceIdentity(
            service_name="test-service",
            service_info={},
            allowed_targets=[],
            allowed_operations=[],
        )

        assert identity.metadata == {}

    def test_can_access_target_specific(self):
        """Test can_access_target with specific target."""
        identity = ServiceIdentity(
            service_name="test-service",
            service_info={},
            allowed_targets=["service-a", "service-b"],
            allowed_operations=[],
        )

        assert identity.can_access_target("service-a") is True
        assert identity.can_access_target("service-b") is True
        assert identity.can_access_target("service-c") is False

    def test_can_access_target_wildcard(self):
        """Test can_access_target with wildcard."""
        identity = ServiceIdentity(
            service_name="test-service",
            service_info={},
            allowed_targets=["*"],
            allowed_operations=[],
        )

        assert identity.can_access_target("any-service") is True
        assert identity.can_access_target("another-service") is True

    def test_can_perform_operation_specific(self):
        """Test can_perform_operation with specific operations."""
        identity = ServiceIdentity(
            service_name="test-service",
            service_info={},
            allowed_targets=[],
            allowed_operations=["read", "write"],
        )

        assert identity.can_perform_operation("read") is True
        assert identity.can_perform_operation("write") is True
        assert identity.can_perform_operation("delete") is False

    def test_can_perform_operation_wildcard(self):
        """Test can_perform_operation with wildcard."""
        identity = ServiceIdentity(
            service_name="test-service",
            service_info={},
            allowed_targets=[],
            allowed_operations=["*"],
        )

        assert identity.can_perform_operation("any-operation") is True
        assert identity.can_perform_operation("another-operation") is True


class TestServiceTokenManager:
    """Test ServiceTokenManager class."""

    @pytest.fixture
    def hs256_manager(self):
        """Create ServiceTokenManager with HS256."""
        return ServiceTokenManager(
            signing_secret="test-secret-key-32-chars-long!",
            algorithm="HS256",
        )

    @pytest.fixture
    def rs256_manager(self):
        """Create ServiceTokenManager with RS256."""
        # Simple mock keys for testing
        private_key = "mock-private-key"
        public_key = "mock-public-key"
        return ServiceTokenManager(
            keypair=(private_key, public_key),
            algorithm="RS256",
        )

    @pytest.fixture
    def service_identity(self, hs256_manager):
        """Create test service identity."""
        return hs256_manager.register_service(
            service_name="test-service",
            service_info={"version": "1.0.0"},
            allowed_targets=["target-service"],
            allowed_operations=["read", "write"],
        )

    def test_hs256_manager_initialization(self):
        """Test ServiceTokenManager initialization with HS256."""
        manager = ServiceTokenManager(
            signing_secret="test-secret",
            algorithm="HS256",
        )

        assert manager.algorithm == "HS256"
        assert manager.signing_key == "test-secret"
        assert manager.verification_key == "test-secret"

    def test_rs256_manager_initialization(self):
        """Test ServiceTokenManager initialization with RS256."""
        private_key = "private-key"
        public_key = "public-key"
        manager = ServiceTokenManager(
            keypair=(private_key, public_key),
            algorithm="RS256",
        )

        assert manager.algorithm == "RS256"
        assert manager.signing_key == private_key
        assert manager.verification_key == public_key

    def test_hs256_no_secret_error(self):
        """Test HS256 initialization without secret."""
        with pytest.raises(ConfigurationError, match="HS256 requires signing_secret"):
            ServiceTokenManager(algorithm="HS256")

    def test_rs256_no_keypair_error(self):
        """Test RS256 initialization without keypair."""
        with pytest.raises(ConfigurationError, match="RS256 requires keypair"):
            ServiceTokenManager(algorithm="RS256")

    def test_unsupported_algorithm_error(self):
        """Test initialization with unsupported algorithm."""
        with pytest.raises(ConfigurationError, match="Unsupported algorithm"):
            ServiceTokenManager(
                signing_secret="secret",
                algorithm="ES256",
            )

    def test_hs256_with_secrets_provider(self):
        """Test HS256 initialization with secrets provider."""
        mock_provider = Mock()
        mock_provider.get_service_signing_secret.return_value = "provider-secret"

        manager = ServiceTokenManager(
            algorithm="HS256",
            secrets_provider=mock_provider,
        )

        assert manager.signing_key == "provider-secret"

    def test_register_service(self, hs256_manager):
        """Test service registration."""
        service_info = {"version": "1.0.0", "description": "Test service"}
        allowed_targets = ["target-a", "target-b"]
        allowed_operations = ["read", "write"]

        identity = hs256_manager.register_service(
            service_name="test-service",
            service_info=service_info,
            allowed_targets=allowed_targets,
            allowed_operations=allowed_operations,
        )

        assert isinstance(identity, ServiceIdentity)
        assert identity.service_name == "test-service"
        assert "test-service" in hs256_manager.services

    def test_register_service_default_operations(self, hs256_manager):
        """Test service registration with default operations."""
        identity = hs256_manager.register_service(
            service_name="test-service",
            service_info={},
            allowed_targets=[],
        )

        assert "*" in identity.allowed_operations

    def test_get_service(self, hs256_manager, service_identity):
        """Test getting registered service."""
        retrieved = hs256_manager.get_service("test-service")
        assert retrieved is service_identity

    def test_get_service_not_found(self, hs256_manager):
        """Test getting non-existent service."""
        retrieved = hs256_manager.get_service("non-existent")
        assert retrieved is None

    def test_create_service_identity(self, hs256_manager):
        """Test convenience method for creating service identity."""
        identity = hs256_manager.create_service_identity(
            service_name="test-service",
            version="2.0.0",
            description="Test service",
            allowed_targets=["target"],
            allowed_operations=["read"],
        )

        assert identity.service_name == "test-service"
        assert identity.service_info["version"] == "2.0.0"
        assert identity.service_info["description"] == "Test service"

    def test_issue_service_token_success(self, hs256_manager, service_identity):
        """Test successful service token issuance."""
        token = hs256_manager.issue_service_token(
            service_identity=service_identity,
            target_service="target-service",
            allowed_operations=["read"],
        )

        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token can be decoded
        claims = jwt.decode(
            token,
            "test-secret-key-32-chars-long!",
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        assert claims["iss"] == "test-service"
        assert claims["aud"] == "target-service"
        assert claims["type"] == "service"

    def test_issue_service_token_unauthorized_target(self, hs256_manager, service_identity):
        """Test token issuance for unauthorized target."""
        with pytest.raises(UnauthorizedService, match="not authorized to access"):
            hs256_manager.issue_service_token(
                service_identity=service_identity,
                target_service="unauthorized-service",
            )

    def test_issue_service_token_unauthorized_operation(self, hs256_manager, service_identity):
        """Test token issuance for unauthorized operation."""
        with pytest.raises(UnauthorizedService, match="not authorized for operation"):
            hs256_manager.issue_service_token(
                service_identity=service_identity,
                target_service="target-service",
                allowed_operations=["delete"],  # Not allowed
            )

    def test_issue_service_token_with_tenant_context(self, hs256_manager, service_identity):
        """Test token issuance with tenant context."""
        token = hs256_manager.issue_service_token(
            service_identity=service_identity,
            target_service="target-service",
            tenant_context="tenant-123",
        )

        claims = jwt.decode(
            token,
            "test-secret-key-32-chars-long!",
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        assert claims["tenant_id"] == "tenant-123"

    def test_issue_service_token_with_extra_claims(self, hs256_manager, service_identity):
        """Test token issuance with extra claims."""
        extra_claims = {"custom_claim": "custom_value"}
        token = hs256_manager.issue_service_token(
            service_identity=service_identity,
            target_service="target-service",
            extra_claims=extra_claims,
        )

        claims = jwt.decode(
            token,
            "test-secret-key-32-chars-long!",
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        assert claims["custom_claim"] == "custom_value"

    def test_issue_service_token_custom_expiration(self, hs256_manager, service_identity):
        """Test token issuance with custom expiration."""
        token = hs256_manager.issue_service_token(
            service_identity=service_identity,
            target_service="target-service",
            expires_in=30,  # 30 minutes
        )

        claims = jwt.decode(
            token,
            "test-secret-key-32-chars-long!",
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        exp = datetime.fromtimestamp(claims["exp"], UTC)
        now = datetime.now(UTC)
        diff = exp - now

        # Should be approximately 30 minutes (within 1 minute tolerance)
        assert 29 <= diff.total_seconds() / 60 <= 31

    def test_verify_service_token_success(self, hs256_manager, service_identity):
        """Test successful service token verification."""
        token = hs256_manager.issue_service_token(
            service_identity=service_identity,
            target_service="target-service",
        )

        claims = hs256_manager.verify_service_token(
            token=token,
            expected_target="target-service",
        )

        assert claims["sub"] == "test-service"
        assert claims["target_service"] == "target-service"
        assert claims["type"] == "service"

    def test_verify_service_token_wrong_target(self, hs256_manager, service_identity):
        """Test token verification with wrong target."""
        token = hs256_manager.issue_service_token(
            service_identity=service_identity,
            target_service="target-service",
        )

        with pytest.raises(UnauthorizedService, match="Token not valid for service"):
            hs256_manager.verify_service_token(
                token=token,
                expected_target="wrong-service",
            )

    def test_verify_service_token_insufficient_operations(self, hs256_manager, service_identity):
        """Test token verification with insufficient operations."""
        token = hs256_manager.issue_service_token(
            service_identity=service_identity,
            target_service="target-service",
            allowed_operations=["read"],
        )

        with pytest.raises(UnauthorizedService, match="missing required operations"):
            hs256_manager.verify_service_token(
                token=token,
                required_operations=["read", "write", "delete"],
            )

    def test_verify_service_token_with_wildcard_operations(self, hs256_manager, service_identity):
        """Test token verification with wildcard operations."""
        token = hs256_manager.issue_service_token(
            service_identity=service_identity,
            target_service="target-service",
            allowed_operations=["*"],
        )

        # Should succeed with wildcard
        claims = hs256_manager.verify_service_token(
            token=token,
            required_operations=["read", "write", "delete"],
        )

        assert claims is not None

    def test_verify_service_token_invalid_type(self, hs256_manager):
        """Test token verification with wrong token type."""
        # Create a user token instead of service token
        claims = {
            "sub": "user123",
            "type": "access",  # Not "service"
            "exp": datetime.now(UTC) + timedelta(hours=1),
        }
        token = jwt.encode(claims, "test-secret-key-32-chars-long!", algorithm="HS256")

        with pytest.raises(InvalidServiceToken, match="Not a service token"):
            hs256_manager.verify_service_token(token)

    def test_verify_service_token_unregistered_service(self, hs256_manager):
        """Test token verification for unregistered service."""
        # Create token for service not in registry
        claims = {
            "sub": "unregistered-service",
            "type": "service",
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "target_service": "any-service",
            "allowed_operations": ["*"],
        }
        token = jwt.encode(claims, "test-secret-key-32-chars-long!", algorithm="HS256")

        with pytest.raises(UnauthorizedService, match="no longer registered"):
            hs256_manager.verify_service_token(token)

    def test_verify_service_token_expired(self, hs256_manager, service_identity):
        """Test verification of expired token."""
        # Create expired token
        claims = {
            "sub": "test-service",
            "type": "service",
            "exp": datetime.now(UTC) - timedelta(hours=1),  # Expired
            "target_service": "target-service",
            "allowed_operations": ["*"],
        }
        token = jwt.encode(claims, "test-secret-key-32-chars-long!", algorithm="HS256")

        with pytest.raises(TokenExpired, match="Service token has expired"):
            hs256_manager.verify_service_token(token)

    def test_verify_service_token_invalid_signature(self, hs256_manager, service_identity):
        """Test verification with invalid signature."""
        # Create token with wrong secret
        claims = {
            "sub": "test-service",
            "type": "service",
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "target_service": "target-service",
            "allowed_operations": ["*"],
        }
        token = jwt.encode(claims, "wrong-secret", algorithm="HS256")

        with pytest.raises(InvalidServiceToken, match="Invalid service token signature"):
            hs256_manager.verify_service_token(token)

    def test_revoke_service_tokens(self, hs256_manager, service_identity):
        """Test revoking service tokens."""
        assert "test-service" in hs256_manager.services

        hs256_manager.revoke_service_tokens("test-service")

        assert "test-service" not in hs256_manager.services

    def test_revoke_nonexistent_service(self, hs256_manager):
        """Test revoking tokens for non-existent service."""
        # Should not raise error
        hs256_manager.revoke_service_tokens("non-existent")

    def test_list_services(self, hs256_manager, service_identity):
        """Test listing registered services."""
        services = hs256_manager.list_services()
        assert "test-service" in services

    def test_get_service_info(self, hs256_manager, service_identity):
        """Test getting service information."""
        info = hs256_manager.get_service_info("test-service")

        assert info is not None
        assert info["service_name"] == "test-service"
        assert info["allowed_targets"] == ["target-service"]
        assert info["allowed_operations"] == ["read", "write"]
        assert "created_at" in info
        assert "identity_id" in info

    def test_get_service_info_not_found(self, hs256_manager):
        """Test getting info for non-existent service."""
        info = hs256_manager.get_service_info("non-existent")
        assert info is None


class TestServiceAuthMiddleware:
    """Test ServiceAuthMiddleware class."""

    @pytest.fixture
    def token_manager(self):
        """Create ServiceTokenManager for testing."""
        return ServiceTokenManager(
            signing_secret="test-secret-key-32-chars-long!",
            algorithm="HS256",
        )

    @pytest.fixture
    def service_identity(self, token_manager):
        """Create service identity."""
        return token_manager.register_service(
            service_name="calling-service",
            service_info={"version": "1.0.0"},
            allowed_targets=["target-service"],
            allowed_operations=["*"],
        )

    @pytest.fixture
    def middleware(self, token_manager):
        """Create ServiceAuthMiddleware."""
        return ServiceAuthMiddleware(
            app=Mock(),
            token_manager=token_manager,
            service_name="target-service",
        )

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/internal/api"
        request.headers = Mock()
        request.headers.get = Mock(return_value=None)
        request.headers.update = Mock()
        request.state = Mock()
        return request

    def test_middleware_initialization(self, token_manager):
        """Test middleware initialization."""
        middleware = ServiceAuthMiddleware(
            app=Mock(),
            token_manager=token_manager,
            service_name="test-service",
            required_operations=["read"],
            protected_paths=["/api"],
        )

        assert middleware.token_manager is token_manager
        assert middleware.service_name == "test-service"
        assert middleware.required_operations == ["read"]
        assert middleware.protected_paths == ["/api"]

    def test_middleware_default_values(self, token_manager):
        """Test middleware initialization with defaults."""
        middleware = ServiceAuthMiddleware(
            app=Mock(),
            token_manager=token_manager,
            service_name="test-service",
        )

        assert middleware.required_operations == []
        assert middleware.protected_paths == ["/internal"]

    @pytest.mark.asyncio
    async def test_dispatch_unprotected_path(self, middleware, mock_request):
        """Test middleware skips authentication for unprotected paths."""
        mock_request.url.path = "/public/api"
        call_next = AsyncMock(return_value=JSONResponse({"status": "ok"}))

        response = await middleware.dispatch(mock_request, call_next)

        # Should bypass authentication
        call_next.assert_called_once_with(mock_request)
        mock_request.headers.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_protected_path_no_token(self, middleware, mock_request):
        """Test protected path without service token."""
        mock_request.headers.get.return_value = None
        call_next = AsyncMock()

        response = await middleware.dispatch(mock_request, call_next)

        # Should return error response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_protected_path_valid_token(
        self, middleware, mock_request, token_manager, service_identity
    ):
        """Test protected path with valid service token."""
        # Create valid service token
        token = token_manager.issue_service_token(
            service_identity=service_identity,
            target_service="target-service",
        )

        mock_request.headers.get.return_value = token
        call_next = AsyncMock(return_value=JSONResponse({"status": "ok"}))

        response = await middleware.dispatch(mock_request, call_next)

        # Should succeed and set request state
        assert response.status_code == 200
        call_next.assert_called_once_with(mock_request)

        # Verify state is set
        assert mock_request.state.service_authenticated is True
        assert mock_request.state.calling_service == "calling-service"

        # Verify headers are updated
        mock_request.headers.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_protected_path_invalid_token(self, middleware, mock_request):
        """Test protected path with invalid service token."""
        mock_request.headers.get.return_value = "invalid-token"
        call_next = AsyncMock()

        response = await middleware.dispatch(mock_request, call_next)

        # Should return error response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_with_custom_error_handler(self, token_manager):
        """Test middleware with custom error handler."""
        custom_handler = AsyncMock(return_value=JSONResponse({"custom": "error"}))
        middleware = ServiceAuthMiddleware(
            app=Mock(),
            token_manager=token_manager,
            service_name="target-service",
            error_handler=custom_handler,
        )

        mock_request = Mock(spec=Request)
        mock_request.url = Mock(path="/internal/api")
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value=None)  # No token

        response = await middleware.dispatch(mock_request, Mock())

        # Custom handler should be called
        custom_handler.assert_called_once()
        assert response.body == b'{"custom":"error"}'

    @pytest.mark.asyncio
    async def test_default_error_handler(self, middleware, mock_request):
        """Test default error handler."""
        error = InvalidServiceToken("Test error")

        response = await middleware._default_error_handler(mock_request, error)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 401
        assert "X-Service-Auth-Error" in response.headers

    @pytest.mark.asyncio
    async def test_dispatch_unexpected_error(self, middleware, mock_request, token_manager):
        """Test middleware handling unexpected errors."""
        # Mock token verification to raise unexpected error
        with patch.object(
            token_manager, "verify_service_token", side_effect=Exception("Unexpected")
        ):
            mock_request.headers.get.return_value = "some-token"
            call_next = AsyncMock()

            response = await middleware.dispatch(mock_request, call_next)

            # Should convert to InvalidServiceToken and return error
            assert isinstance(response, JSONResponse)
            assert response.status_code == 401


class TestCreateServiceTokenManager:
    """Test create_service_token_manager factory function."""

    def test_create_hs256_manager(self):
        """Test creating HS256 service token manager."""
        manager = create_service_token_manager(
            algorithm="HS256",
            signing_secret="test-secret",
        )

        assert isinstance(manager, ServiceTokenManager)
        assert manager.algorithm == "HS256"

    def test_create_rs256_manager(self):
        """Test creating RS256 service token manager."""
        keypair = ("private-key", "public-key")
        manager = create_service_token_manager(
            algorithm="RS256",
            keypair=keypair,
        )

        assert isinstance(manager, ServiceTokenManager)
        assert manager.algorithm == "RS256"

    def test_create_manager_with_kwargs(self):
        """Test creating manager with additional kwargs."""
        manager = create_service_token_manager(
            algorithm="HS256",
            signing_secret="test-secret",
            default_token_expire_minutes=120,
        )

        assert manager.default_token_expire_minutes == 120

    def test_create_manager_defaults(self):
        """Test creating manager with default algorithm."""
        manager = create_service_token_manager(
            signing_secret="test-secret",
        )

        assert manager.algorithm == "HS256"


class TestServiceAuthIntegration:
    """Test integration scenarios."""

    @pytest.fixture
    def full_setup(self):
        """Set up complete service auth system."""
        manager = ServiceTokenManager(
            signing_secret="test-secret-key-32-chars-long!",
            algorithm="HS256",
        )

        # Register services
        service_a = manager.register_service(
            service_name="service-a",
            service_info={"version": "1.0.0"},
            allowed_targets=["service-b"],
            allowed_operations=["read", "write"],
        )

        service_b = manager.register_service(
            service_name="service-b",
            service_info={"version": "1.0.0"},
            allowed_targets=["service-a"],
            allowed_operations=["*"],
        )

        return {
            "manager": manager,
            "service_a": service_a,
            "service_b": service_b,
        }

    def test_full_service_communication_flow(self, full_setup):
        """Test complete service-to-service communication flow."""
        manager = full_setup["manager"]
        service_a = full_setup["service_a"]

        # Service A creates token for Service B
        token = manager.issue_service_token(
            service_identity=service_a,
            target_service="service-b",
            allowed_operations=["read"],
        )

        # Service B verifies token
        claims = manager.verify_service_token(
            token=token,
            expected_target="service-b",
            required_operations=["read"],
        )

        assert claims["sub"] == "service-a"
        assert claims["target_service"] == "service-b"
        assert "read" in claims["allowed_operations"]

    @pytest.mark.asyncio
    async def test_middleware_integration(self, full_setup):
        """Test middleware integration with token manager."""
        manager = full_setup["manager"]
        service_a = full_setup["service_a"]

        # Create middleware for service-b
        middleware = ServiceAuthMiddleware(
            app=Mock(),
            token_manager=manager,
            service_name="service-b",
            required_operations=["read"],
        )

        # Create token
        token = manager.issue_service_token(
            service_identity=service_a,
            target_service="service-b",
            allowed_operations=["read"],
        )

        # Test middleware
        mock_request = Mock(spec=Request)
        mock_request.url = Mock(path="/internal/api")
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value=token)
        mock_request.headers.update = Mock()
        mock_request.state = Mock()

        call_next = AsyncMock(return_value=JSONResponse({"status": "ok"}))

        response = await middleware.dispatch(mock_request, call_next)

        assert response.status_code == 200
        assert mock_request.state.service_authenticated is True
        assert mock_request.state.calling_service == "service-a"

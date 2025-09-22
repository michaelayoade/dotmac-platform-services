"""
Comprehensive tests for Service-to-Service Authentication.
"""

import hashlib
import hmac
import json
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import jwt
import pytest
from fastapi import Request
from starlette.responses import Response

from dotmac.platform.auth.exceptions import (
    InvalidServiceToken,
    TokenExpired,
    UnauthorizedService,
)
from dotmac.platform.auth.service_auth import (
    ServiceAuthMiddleware,
    ServiceIdentity,
    ServiceTokenManager,
)


@pytest.mark.asyncio
class TestServiceIdentity:
    """Test ServiceIdentity class."""

    def test_service_identity_creation(self):
        """Test creating a service identity."""
        identity = ServiceIdentity(
            service_name="test-service",
            service_info={"version": "1.0", "environment": "production"},
            allowed_targets=["api-service", "db-service"],
            allowed_operations=["read", "write"],
            metadata={"owner": "platform-team"},
        )

        assert identity.service_name == "test-service"
        assert identity.service_info["version"] == "1.0"
        assert "api-service" in identity.allowed_targets
        assert "read" in identity.allowed_operations
        assert identity.metadata["owner"] == "platform-team"
        assert identity.identity_id is not None
        assert identity.created_at is not None

    def test_can_access_target_specific(self):
        """Test checking access to specific target."""
        identity = ServiceIdentity(
            service_name="test-service",
            service_info={},
            allowed_targets=["api-service", "db-service"],
            allowed_operations=["read"],
        )

        assert identity.can_access_target("api-service") is True
        assert identity.can_access_target("db-service") is True
        assert identity.can_access_target("other-service") is False

    def test_can_access_target_wildcard(self):
        """Test checking access with wildcard target."""
        identity = ServiceIdentity(
            service_name="admin-service",
            service_info={},
            allowed_targets=["*"],
            allowed_operations=["read"],
        )

        assert identity.can_access_target("any-service") is True
        assert identity.can_access_target("another-service") is True

    def test_can_perform_operation_specific(self):
        """Test checking specific operations."""
        identity = ServiceIdentity(
            service_name="test-service",
            service_info={},
            allowed_targets=["api-service"],
            allowed_operations=["read", "list"],
        )

        assert identity.can_perform_operation("read") is True
        assert identity.can_perform_operation("list") is True
        assert identity.can_perform_operation("write") is False
        assert identity.can_perform_operation("delete") is False

    def test_can_perform_operation_wildcard(self):
        """Test checking operations with wildcard."""
        identity = ServiceIdentity(
            service_name="admin-service",
            service_info={},
            allowed_targets=["api-service"],
            allowed_operations=["*"],
        )

        assert identity.can_perform_operation("read") is True
        assert identity.can_perform_operation("write") is True
        assert identity.can_perform_operation("delete") is True
        assert identity.can_perform_operation("any-operation") is True


@pytest.mark.asyncio
class TestServiceTokenManager:
    """Test ServiceTokenManager class."""

    @pytest.fixture
    def manager_hs256(self):
        """Create token manager with HS256."""
        return ServiceTokenManager(
            signing_secret="test-secret-key",
            algorithm="HS256",
            default_token_expire_minutes=60,
        )

    @pytest.fixture
    def manager_rs256(self):
        """Create token manager with RS256."""
        # Generate test RSA key pair
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        return ServiceTokenManager(
            keypair=(private_pem, public_pem),
            algorithm="RS256",
            default_token_expire_minutes=30,
        )

    def test_initialization_hs256(self, manager_hs256):
        """Test HS256 initialization."""
        assert manager_hs256.algorithm == "HS256"
        assert manager_hs256.default_token_expire_minutes == 60
        assert manager_hs256.signing_secret is not None
        assert len(manager_hs256.services) == 0

    def test_initialization_rs256(self, manager_rs256):
        """Test RS256 initialization."""
        assert manager_rs256.algorithm == "RS256"
        assert manager_rs256.default_token_expire_minutes == 30
        assert manager_rs256.private_key is not None
        assert manager_rs256.public_key is not None

    def test_register_service(self, manager_hs256):
        """Test registering a service."""
        service_id = manager_hs256.register_service(
            service_name="test-service",
            allowed_targets=["api-service"],
            allowed_operations=["read"],
            metadata={"tier": "standard"},
        )

        assert service_id is not None
        assert "test-service" in manager_hs256.services
        identity = manager_hs256.services["test-service"]
        assert identity.service_name == "test-service"
        assert "api-service" in identity.allowed_targets

    def test_register_duplicate_service(self, manager_hs256):
        """Test registering duplicate service updates existing."""
        # First registration
        id1 = manager_hs256.register_service(
            service_name="test-service",
            allowed_targets=["api-service"],
            allowed_operations=["read"],
        )

        # Second registration (update)
        id2 = manager_hs256.register_service(
            service_name="test-service",
            allowed_targets=["db-service"],
            allowed_operations=["write"],
        )

        # Should have different IDs but same service name
        assert id1 != id2
        assert len(manager_hs256.services) == 1
        identity = manager_hs256.services["test-service"]
        assert "db-service" in identity.allowed_targets
        assert "write" in identity.allowed_operations

    def test_issue_service_token(self, manager_hs256):
        """Test issuing a service token."""
        # Register service first
        manager_hs256.register_service(
            service_name="test-service",
            allowed_targets=["api-service"],
            allowed_operations=["read"],
        )

        token = manager_hs256.issue_service_token(
            source_service="test-service",
            target_service="api-service",
            operation="read",
            expire_minutes=15,
        )

        assert token is not None
        # Verify token structure
        decoded = jwt.decode(token, "test-secret-key", algorithms=["HS256"])
        assert decoded["source_service"] == "test-service"
        assert decoded["target_service"] == "api-service"
        assert decoded["operation"] == "read"

    def test_issue_token_unregistered_service(self, manager_hs256):
        """Test issuing token for unregistered service."""
        with pytest.raises(UnauthorizedService):
            manager_hs256.issue_service_token(
                source_service="unknown-service",
                target_service="api-service",
                operation="read",
            )

    def test_issue_token_unauthorized_target(self, manager_hs256):
        """Test issuing token for unauthorized target."""
        manager_hs256.register_service(
            service_name="test-service",
            allowed_targets=["api-service"],
            allowed_operations=["read"],
        )

        with pytest.raises(UnauthorizedService):
            manager_hs256.issue_service_token(
                source_service="test-service",
                target_service="forbidden-service",
                operation="read",
            )

    def test_issue_token_unauthorized_operation(self, manager_hs256):
        """Test issuing token for unauthorized operation."""
        manager_hs256.register_service(
            service_name="test-service",
            allowed_targets=["api-service"],
            allowed_operations=["read"],
        )

        with pytest.raises(UnauthorizedService):
            manager_hs256.issue_service_token(
                source_service="test-service",
                target_service="api-service",
                operation="delete",  # Not allowed
            )

    def test_verify_service_token_success(self, manager_hs256):
        """Test successful token verification."""
        # Register and issue token
        manager_hs256.register_service(
            service_name="test-service",
            allowed_targets=["api-service"],
            allowed_operations=["read"],
        )

        token = manager_hs256.issue_service_token(
            source_service="test-service",
            target_service="api-service",
            operation="read",
        )

        # Verify token
        claims = manager_hs256.verify_service_token(token)

        assert claims["source_service"] == "test-service"
        assert claims["target_service"] == "api-service"
        assert claims["operation"] == "read"

    def test_verify_invalid_token(self, manager_hs256):
        """Test verifying invalid token."""
        with pytest.raises(InvalidServiceToken):
            manager_hs256.verify_service_token("invalid.token.here")

    def test_verify_expired_token(self, manager_hs256):
        """Test verifying expired token."""
        manager_hs256.register_service(
            service_name="test-service",
            allowed_targets=["api-service"],
            allowed_operations=["read"],
        )

        # Issue token with very short expiry
        token = manager_hs256.issue_service_token(
            source_service="test-service",
            target_service="api-service",
            operation="read",
            expire_minutes=-1,  # Already expired
        )

        with pytest.raises(TokenExpired):
            manager_hs256.verify_service_token(token)

    def test_verify_token_wrong_algorithm(self, manager_hs256):
        """Test verifying token with wrong algorithm."""
        # Create token with different algorithm
        token = jwt.encode(
            {"source_service": "test", "exp": datetime.now(UTC) + timedelta(hours=1)},
            "different-secret",
            algorithm="HS512",
        )

        with pytest.raises(InvalidServiceToken):
            manager_hs256.verify_service_token(token)

    def test_authorize_request(self, manager_hs256):
        """Test authorizing a service request."""
        # Register service
        manager_hs256.register_service(
            service_name="test-service",
            allowed_targets=["api-service"],
            allowed_operations=["read"],
        )

        # Issue token
        token = manager_hs256.issue_service_token(
            source_service="test-service",
            target_service="api-service",
            operation="read",
        )

        # Authorize request
        authorized = manager_hs256.authorize_request(
            token=token,
            target_service="api-service",
            operation="read",
        )

        assert authorized is True

    def test_authorize_request_wrong_target(self, manager_hs256):
        """Test authorizing request for wrong target."""
        manager_hs256.register_service(
            service_name="test-service",
            allowed_targets=["api-service"],
            allowed_operations=["read"],
        )

        token = manager_hs256.issue_service_token(
            source_service="test-service",
            target_service="api-service",
            operation="read",
        )

        with pytest.raises(UnauthorizedService):
            manager_hs256.authorize_request(
                token=token,
                target_service="different-service",  # Wrong target
                operation="read",
            )

    def test_authorize_request_wrong_operation(self, manager_hs256):
        """Test authorizing request for wrong operation."""
        manager_hs256.register_service(
            service_name="test-service",
            allowed_targets=["api-service"],
            allowed_operations=["read"],
        )

        token = manager_hs256.issue_service_token(
            source_service="test-service",
            target_service="api-service",
            operation="read",
        )

        with pytest.raises(UnauthorizedService):
            manager_hs256.authorize_request(
                token=token,
                target_service="api-service",
                operation="write",  # Wrong operation
            )

    def test_generate_service_key(self, manager_hs256):
        """Test generating service key."""
        key = manager_hs256.generate_service_key("test-service")
        assert key is not None
        assert len(key) == 64  # SHA256 hex digest length

    def test_validate_service_key(self, manager_hs256):
        """Test validating service key."""
        # Register service
        manager_hs256.register_service(
            service_name="test-service",
            allowed_targets=["api-service"],
            allowed_operations=["read"],
        )

        # Generate and validate key
        key = manager_hs256.generate_service_key("test-service")
        is_valid = manager_hs256.validate_service_key("test-service", key)

        assert is_valid is True

    def test_validate_invalid_service_key(self, manager_hs256):
        """Test validating invalid service key."""
        manager_hs256.register_service(
            service_name="test-service",
            allowed_targets=["api-service"],
            allowed_operations=["read"],
        )

        is_valid = manager_hs256.validate_service_key("test-service", "invalid-key")
        assert is_valid is False

    def test_validate_key_unregistered_service(self, manager_hs256):
        """Test validating key for unregistered service."""
        is_valid = manager_hs256.validate_service_key("unknown-service", "any-key")
        assert is_valid is False

    def test_rotate_service_key(self, manager_hs256):
        """Test rotating service key."""
        # Register service
        manager_hs256.register_service(
            service_name="test-service",
            allowed_targets=["api-service"],
            allowed_operations=["read"],
        )

        # Generate initial key
        old_key = manager_hs256.generate_service_key("test-service")

        # Rotate key
        new_key = manager_hs256.rotate_service_key("test-service")

        assert new_key != old_key
        assert manager_hs256.validate_service_key("test-service", new_key) is True
        # Old key should still be valid (implementation dependent)

    def test_revoke_service(self, manager_hs256):
        """Test revoking a service."""
        # Register service
        manager_hs256.register_service(
            service_name="test-service",
            allowed_targets=["api-service"],
            allowed_operations=["read"],
        )

        # Revoke service
        manager_hs256.revoke_service("test-service")

        assert "test-service" not in manager_hs256.services

    def test_list_services(self, manager_hs256):
        """Test listing registered services."""
        # Register multiple services
        manager_hs256.register_service(
            service_name="service1",
            allowed_targets=["api"],
            allowed_operations=["read"],
        )
        manager_hs256.register_service(
            service_name="service2",
            allowed_targets=["db"],
            allowed_operations=["write"],
        )

        services = manager_hs256.list_services()

        assert len(services) == 2
        assert "service1" in services
        assert "service2" in services


@pytest.mark.asyncio
class TestServiceAuthMiddleware:
    """Test ServiceAuthMiddleware class."""

    @pytest.fixture
    def token_manager(self):
        """Create token manager."""
        manager = ServiceTokenManager(
            signing_secret="test-secret",
            algorithm="HS256",
        )
        manager.register_service(
            service_name="client-service",
            allowed_targets=["api-service"],
            allowed_operations=["read", "write"],
        )
        return manager

    @pytest.fixture
    def middleware(self, token_manager):
        """Create middleware."""
        app = Mock()
        return ServiceAuthMiddleware(
            app=app,
            token_manager=token_manager,
            service_name="api-service",
            required=True,
        )

    async def test_middleware_with_valid_token(self, middleware, token_manager):
        """Test middleware with valid service token."""
        # Create valid token
        token = token_manager.issue_service_token(
            source_service="client-service",
            target_service="api-service",
            operation="read",
        )

        # Mock request
        request = Mock(spec=Request)
        request.headers = {"X-Service-Token": token}
        request.method = "GET"

        # Mock call_next
        async def call_next(req):
            return Response("Success", status_code=200)

        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 200
        assert hasattr(request.state, "service_auth")
        assert request.state.service_auth["source_service"] == "client-service"

    async def test_middleware_without_token_required(self, middleware):
        """Test middleware without token when required."""
        request = Mock(spec=Request)
        request.headers = {}
        request.method = "GET"

        async def call_next(req):
            return Response("Success", status_code=200)

        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 401
        body = json.loads(response.body)
        assert "Service token required" in body["detail"]

    async def test_middleware_without_token_optional(self, token_manager):
        """Test middleware without token when optional."""
        app = Mock()
        middleware = ServiceAuthMiddleware(
            app=app,
            token_manager=token_manager,
            service_name="api-service",
            required=False,  # Optional
        )

        request = Mock(spec=Request)
        request.headers = {}

        async def call_next(req):
            return Response("Success", status_code=200)

        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 200

    async def test_middleware_with_invalid_token(self, middleware):
        """Test middleware with invalid token."""
        request = Mock(spec=Request)
        request.headers = {"X-Service-Token": "invalid.token.here"}
        request.method = "GET"

        async def call_next(req):
            return Response("Success", status_code=200)

        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 401
        body = json.loads(response.body)
        assert "Invalid service token" in body["detail"]

    async def test_middleware_with_expired_token(self, middleware, token_manager):
        """Test middleware with expired token."""
        # Create expired token
        token = token_manager.issue_service_token(
            source_service="client-service",
            target_service="api-service",
            operation="read",
            expire_minutes=-1,  # Expired
        )

        request = Mock(spec=Request)
        request.headers = {"X-Service-Token": token}
        request.method = "GET"

        async def call_next(req):
            return Response("Success", status_code=200)

        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 401
        body = json.loads(response.body)
        assert "Token has expired" in body["detail"]

    async def test_middleware_unauthorized_operation(self, middleware, token_manager):
        """Test middleware with unauthorized operation."""
        # Token for read operation
        token = token_manager.issue_service_token(
            source_service="client-service",
            target_service="api-service",
            operation="read",
        )

        # But request is for write operation (DELETE method)
        request = Mock(spec=Request)
        request.headers = {"X-Service-Token": token}
        request.method = "DELETE"

        async def call_next(req):
            return Response("Success", status_code=200)

        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 403
        body = json.loads(response.body)
        assert "not authorized" in body["detail"]

    async def test_middleware_maps_http_methods(self, middleware, token_manager):
        """Test middleware correctly maps HTTP methods to operations."""
        test_cases = [
            ("GET", "read"),
            ("POST", "write"),
            ("PUT", "write"),
            ("PATCH", "write"),
            ("DELETE", "delete"),
        ]

        for http_method, expected_operation in test_cases:
            # Create token for expected operation
            if expected_operation == "delete":
                # Register delete permission
                token_manager.services["client-service"].allowed_operations.add("delete")

            token = token_manager.issue_service_token(
                source_service="client-service",
                target_service="api-service",
                operation=expected_operation,
            )

            request = Mock(spec=Request)
            request.headers = {"X-Service-Token": token}
            request.method = http_method

            async def call_next(req):
                return Response("Success", status_code=200)

            response = await middleware.dispatch(request, call_next)

            # Should succeed with correct operation
            assert response.status_code == 200, f"Failed for {http_method} -> {expected_operation}"
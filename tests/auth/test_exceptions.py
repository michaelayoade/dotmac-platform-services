"""Tests for auth exceptions module."""

import pytest
from typing import Dict, Any

from dotmac.platform.auth.exceptions import (
    AuthError,
    TokenError,
    TokenExpired,
    TokenNotFound,
    InvalidToken,
    InvalidSignature,
    InvalidAlgorithm,
    InvalidAudience,
    InvalidIssuer,
    InsufficientScope,
    InsufficientRole,
    TenantMismatch,
    ServiceTokenError,
    UnauthorizedService,
    InvalidServiceToken,
    SecretsProviderError,
    ConfigurationError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    ConnectionError,
    TimeoutError,
    get_http_status,
    EXCEPTION_STATUS_MAP,
)


class TestBaseExceptions:
    """Test base exception classes."""

    def test_auth_error_basic(self):
        """Test basic AuthError functionality."""
        error = AuthError()
        assert error.message == "Authentication failed"
        assert error.error_code == "AUTH_ERROR"
        assert error.details == {}
        assert str(error) == "Authentication failed"

    def test_auth_error_with_params(self):
        """Test AuthError with custom parameters."""
        details = {"user_id": "123", "reason": "expired"}
        error = AuthError(
            message="Custom message",
            error_code="CUSTOM_ERROR",
            details=details,
        )

        assert error.message == "Custom message"
        assert error.error_code == "CUSTOM_ERROR"
        assert error.details == details

    def test_auth_error_to_dict(self):
        """Test AuthError to_dict method."""
        details = {"key": "value"}
        error = AuthError(
            message="Test message",
            error_code="TEST_ERROR",
            details=details,
        )

        result = error.to_dict()
        expected = {
            "error": "TEST_ERROR",
            "message": "Test message",
            "details": details,
        }
        assert result == expected

    def test_token_error_inheritance(self):
        """Test TokenError inherits from AuthError."""
        error = TokenError()
        assert isinstance(error, AuthError)
        assert error.error_code == "TOKEN_ERROR"
        assert error.message == "Token error"

    def test_token_error_with_custom_params(self):
        """Test TokenError with custom parameters."""
        error = TokenError(
            message="Custom token error",
            error_code="CUSTOM_TOKEN_ERROR",
            details={"token_type": "access"},
        )

        assert error.message == "Custom token error"
        assert error.error_code == "CUSTOM_TOKEN_ERROR"
        assert error.details == {"token_type": "access"}


class TestTokenExceptions:
    """Test token-related exceptions."""

    def test_token_expired_basic(self):
        """Test TokenExpired basic functionality."""
        error = TokenExpired()
        assert error.message == "Token has expired"
        assert error.error_code == "TOKEN_EXPIRED"
        assert error.details == {}

    def test_token_expired_with_time(self):
        """Test TokenExpired with expiration time."""
        expired_at = "2024-01-01T00:00:00Z"
        error = TokenExpired(
            message="Custom expired message",
            expired_at=expired_at,
        )

        assert error.message == "Custom expired message"
        assert error.details == {"expired_at": expired_at}

    def test_token_not_found(self):
        """Test TokenNotFound exception."""
        error = TokenNotFound()
        assert error.message == "Authentication token required"
        assert error.error_code == "TOKEN_NOT_FOUND"

        error_custom = TokenNotFound("Custom token required message")
        assert error_custom.message == "Custom token required message"

    def test_invalid_token_basic(self):
        """Test InvalidToken basic functionality."""
        error = InvalidToken()
        assert error.message == "Invalid authentication token"
        assert error.error_code == "INVALID_TOKEN"
        assert error.details == {}

    def test_invalid_token_with_reason(self):
        """Test InvalidToken with reason."""
        error = InvalidToken(
            message="Token malformed",
            reason="missing signature",
        )

        assert error.message == "Token malformed"
        assert error.details == {"reason": "missing signature"}

    def test_invalid_signature(self):
        """Test InvalidSignature exception."""
        error = InvalidSignature()
        assert error.message == "Token signature verification failed"
        assert error.error_code == "INVALID_SIGNATURE"

        error_custom = InvalidSignature("Custom signature error")
        assert error_custom.message == "Custom signature error"

    def test_invalid_algorithm_basic(self):
        """Test InvalidAlgorithm basic functionality."""
        error = InvalidAlgorithm()
        assert error.message == "Invalid JWT algorithm"
        assert error.error_code == "INVALID_ALGORITHM"
        assert error.details == {}

    def test_invalid_algorithm_with_algorithm(self):
        """Test InvalidAlgorithm with algorithm specified."""
        error = InvalidAlgorithm(
            message="Unsupported algorithm",
            algorithm="RS512",
        )

        assert error.message == "Unsupported algorithm"
        assert error.details == {"algorithm": "RS512"}

    def test_invalid_audience_basic(self):
        """Test InvalidAudience basic functionality."""
        error = InvalidAudience()
        assert error.message == "Token audience mismatch"
        assert error.error_code == "INVALID_AUDIENCE"
        assert error.details == {}

    def test_invalid_audience_with_details(self):
        """Test InvalidAudience with expected and actual values."""
        error = InvalidAudience(
            message="Audience validation failed",
            expected="api.example.com",
            actual="wrong.example.com",
        )

        assert error.message == "Audience validation failed"
        assert error.details == {
            "expected_audience": "api.example.com",
            "actual_audience": "wrong.example.com",
        }

    def test_invalid_issuer_basic(self):
        """Test InvalidIssuer basic functionality."""
        error = InvalidIssuer()
        assert error.message == "Token issuer mismatch"
        assert error.error_code == "INVALID_ISSUER"
        assert error.details == {}

    def test_invalid_issuer_with_details(self):
        """Test InvalidIssuer with expected and actual values."""
        error = InvalidIssuer(
            message="Issuer validation failed",
            expected="auth.example.com",
            actual="wrong.example.com",
        )

        assert error.message == "Issuer validation failed"
        assert error.details == {
            "expected_issuer": "auth.example.com",
            "actual_issuer": "wrong.example.com",
        }


class TestAuthorizationExceptions:
    """Test authorization-related exceptions."""

    def test_insufficient_scope_basic(self):
        """Test InsufficientScope basic functionality."""
        error = InsufficientScope()
        assert error.message == "Insufficient permissions"
        assert error.error_code == "INSUFFICIENT_SCOPE"
        assert error.details == {}

    def test_insufficient_scope_with_scopes(self):
        """Test InsufficientScope with scope details."""
        required_scopes = ["read:users", "write:users"]
        user_scopes = ["read:users"]

        error = InsufficientScope(
            message="Missing write permission",
            required_scopes=required_scopes,
            user_scopes=user_scopes,
        )

        assert error.message == "Missing write permission"
        assert error.details == {
            "required_scopes": required_scopes,
            "user_scopes": user_scopes,
        }

    def test_insufficient_role_basic(self):
        """Test InsufficientRole basic functionality."""
        error = InsufficientRole()
        assert error.message == "Insufficient role permissions"
        assert error.error_code == "INSUFFICIENT_ROLE"
        assert error.details == {}

    def test_insufficient_role_with_roles(self):
        """Test InsufficientRole with role details."""
        required_roles = ["admin", "moderator"]
        user_roles = ["user"]

        error = InsufficientRole(
            message="Admin access required",
            required_roles=required_roles,
            user_roles=user_roles,
        )

        assert error.message == "Admin access required"
        assert error.details == {
            "required_roles": required_roles,
            "user_roles": user_roles,
        }

    def test_tenant_mismatch_basic(self):
        """Test TenantMismatch basic functionality."""
        error = TenantMismatch()
        assert error.message == "Tenant context mismatch"
        assert error.error_code == "TENANT_MISMATCH"
        assert error.details == {}

    def test_tenant_mismatch_with_tenants(self):
        """Test TenantMismatch with tenant details."""
        error = TenantMismatch(
            message="Wrong tenant context",
            expected_tenant="tenant-a",
            token_tenant="tenant-b",
        )

        assert error.message == "Wrong tenant context"
        assert error.details == {
            "expected_tenant": "tenant-a",
            "token_tenant": "tenant-b",
        }


class TestServiceExceptions:
    """Test service-related exceptions."""

    def test_service_token_error_basic(self):
        """Test ServiceTokenError basic functionality."""
        error = ServiceTokenError()
        assert error.message == "Service token error"
        assert error.error_code == "SERVICE_TOKEN_ERROR"
        assert error.details == {}

    def test_unauthorized_service_basic(self):
        """Test UnauthorizedService basic functionality."""
        error = UnauthorizedService()
        assert error.message == "Service not authorized"
        assert error.error_code == "UNAUTHORIZED_SERVICE"
        assert error.details == {}

    def test_unauthorized_service_with_details(self):
        """Test UnauthorizedService with service details."""
        error = UnauthorizedService(
            message="Service access denied",
            service_name="user-service",
            target_service="admin-service",
            operation="delete_user",
        )

        assert error.message == "Service access denied"
        assert error.details == {
            "service_name": "user-service",
            "target_service": "admin-service",
            "operation": "delete_user",
        }

    def test_invalid_service_token_basic(self):
        """Test InvalidServiceToken basic functionality."""
        error = InvalidServiceToken()
        assert error.message == "Invalid service token"
        assert error.error_code == "INVALID_SERVICE_TOKEN"
        assert error.details == {}

    def test_invalid_service_token_with_reason(self):
        """Test InvalidServiceToken with reason."""
        error = InvalidServiceToken(
            message="Service token malformed",
            reason="missing service claim",
        )

        assert error.message == "Service token malformed"
        assert error.details == {"reason": "missing service claim"}


class TestSystemExceptions:
    """Test system-related exceptions."""

    def test_secrets_provider_error_basic(self):
        """Test SecretsProviderError basic functionality."""
        error = SecretsProviderError()
        assert error.message == "Secrets provider error"
        assert error.error_code == "SECRETS_PROVIDER_ERROR"
        assert error.details == {}

    def test_secrets_provider_error_with_details(self):
        """Test SecretsProviderError with provider and operation."""
        error = SecretsProviderError(
            message="Vault connection failed",
            provider="vault",
            operation="get_secret",
        )

        assert error.message == "Vault connection failed"
        assert error.details == {
            "provider": "vault",
            "operation": "get_secret",
        }

    def test_configuration_error_basic(self):
        """Test ConfigurationError basic functionality."""
        error = ConfigurationError()
        assert error.message == "Authentication configuration error"
        assert error.error_code == "CONFIGURATION_ERROR"
        assert error.details == {}

    def test_configuration_error_with_component(self):
        """Test ConfigurationError with component."""
        error = ConfigurationError(
            message="JWT secret not configured",
            component="jwt_service",
        )

        assert error.message == "JWT secret not configured"
        assert error.details == {"component": "jwt_service"}

    def test_authentication_error(self):
        """Test AuthenticationError."""
        error = AuthenticationError()
        assert error.message == "Authentication failed"
        assert error.error_code == "AUTHENTICATION_ERROR"

        error_custom = AuthenticationError(
            message="Login failed",
            error_code="LOGIN_FAILED",
            details={"attempts": 3},
        )
        assert error_custom.message == "Login failed"
        assert error_custom.error_code == "LOGIN_FAILED"
        assert error_custom.details == {"attempts": 3}

    def test_authorization_error(self):
        """Test AuthorizationError."""
        error = AuthorizationError()
        assert error.message == "Authorization failed"
        assert error.error_code == "AUTHORIZATION_ERROR"

        error_custom = AuthorizationError(
            message="Access denied",
            error_code="ACCESS_DENIED",
            details={"resource": "admin_panel"},
        )
        assert error_custom.message == "Access denied"
        assert error_custom.error_code == "ACCESS_DENIED"
        assert error_custom.details == {"resource": "admin_panel"}


class TestNetworkExceptions:
    """Test network-related exceptions."""

    def test_rate_limit_error(self):
        """Test RateLimitError."""
        error = RateLimitError()
        assert error.message == "Rate limit exceeded"
        assert error.error_code == "RATE_LIMIT_ERROR"

        error_custom = RateLimitError(
            message="Too many requests",
            details={"limit": 100, "window": "1h"},
        )
        assert error_custom.message == "Too many requests"
        assert error_custom.details == {"limit": 100, "window": "1h"}

    def test_connection_error(self):
        """Test ConnectionError."""
        error = ConnectionError()
        assert error.message == "Connection failed"
        assert error.error_code == "CONNECTION_ERROR"

        error_custom = ConnectionError(
            message="Redis connection failed",
            details={"host": "redis.example.com", "port": 6379},
        )
        assert error_custom.message == "Redis connection failed"
        assert error_custom.details == {"host": "redis.example.com", "port": 6379}

    def test_timeout_error(self):
        """Test TimeoutError."""
        error = TimeoutError()
        assert error.message == "Operation timed out"
        assert error.error_code == "TIMEOUT_ERROR"

        error_custom = TimeoutError(
            message="Request timeout",
            details={"timeout": 30, "operation": "token_verification"},
        )
        assert error_custom.message == "Request timeout"
        assert error_custom.details == {"timeout": 30, "operation": "token_verification"}


class TestHttpStatusMapping:
    """Test HTTP status code mapping."""

    def test_get_http_status_known_exceptions(self):
        """Test get_http_status for known exceptions."""
        test_cases = [
            (TokenNotFound(), 401),
            (TokenExpired(), 401),
            (InvalidToken(), 401),
            (InvalidSignature(), 401),
            (InvalidAlgorithm(), 401),
            (InvalidAudience(), 401),
            (InvalidIssuer(), 401),
            (InsufficientScope(), 403),
            (InsufficientRole(), 403),
            (TenantMismatch(), 403),
            (UnauthorizedService(), 403),
            (InvalidServiceToken(), 401),
            (SecretsProviderError(), 500),
            (ConfigurationError(), 500),
            (AuthenticationError(), 401),
            (AuthorizationError(), 403),
            (RateLimitError(), 429),
            (ConnectionError(), 503),
            (TimeoutError(), 504),
        ]

        for exception, expected_status in test_cases:
            assert get_http_status(exception) == expected_status

    def test_get_http_status_base_auth_error(self):
        """Test get_http_status for base AuthError."""
        error = AuthError("Generic auth error")
        assert get_http_status(error) == 401

    def test_get_http_status_unknown_exception(self):
        """Test get_http_status for unknown exception type."""
        class CustomAuthError(AuthError):
            pass

        error = CustomAuthError("Custom error")
        assert get_http_status(error) == 401  # Should default to 401

    def test_exception_status_map_completeness(self):
        """Test that EXCEPTION_STATUS_MAP contains expected mappings."""
        expected_mappings = {
            TokenNotFound: 401,
            TokenExpired: 401,
            InvalidToken: 401,
            InvalidSignature: 401,
            InvalidAlgorithm: 401,
            InvalidAudience: 401,
            InvalidIssuer: 401,
            InsufficientScope: 403,
            InsufficientRole: 403,
            TenantMismatch: 403,
            UnauthorizedService: 403,
            InvalidServiceToken: 401,
            SecretsProviderError: 500,
            ConfigurationError: 500,
            AuthenticationError: 401,
            AuthorizationError: 403,
            RateLimitError: 429,
            ConnectionError: 503,
            TimeoutError: 504,
            AuthError: 401,
        }

        for exception_class, expected_status in expected_mappings.items():
            assert EXCEPTION_STATUS_MAP[exception_class] == expected_status


class TestExceptionInheritance:
    """Test exception inheritance hierarchy."""

    def test_inheritance_chain(self):
        """Test that exceptions inherit correctly."""
        # Token exceptions should inherit from TokenError
        assert issubclass(TokenExpired, TokenError)
        assert issubclass(TokenNotFound, TokenError)
        assert issubclass(InvalidToken, TokenError)
        assert issubclass(InvalidSignature, TokenError)
        assert issubclass(InvalidAlgorithm, TokenError)
        assert issubclass(InvalidAudience, TokenError)
        assert issubclass(InvalidIssuer, TokenError)

        # TokenError should inherit from AuthError
        assert issubclass(TokenError, AuthError)

        # Service exceptions should inherit correctly
        assert issubclass(UnauthorizedService, ServiceTokenError)
        assert issubclass(InvalidServiceToken, ServiceTokenError)
        assert issubclass(ServiceTokenError, AuthError)

        # All custom exceptions should inherit from AuthError
        assert issubclass(InsufficientScope, AuthError)
        assert issubclass(InsufficientRole, AuthError)
        assert issubclass(TenantMismatch, AuthError)
        assert issubclass(SecretsProviderError, AuthError)
        assert issubclass(ConfigurationError, AuthError)
        assert issubclass(AuthenticationError, AuthError)
        assert issubclass(AuthorizationError, AuthError)
        assert issubclass(RateLimitError, AuthError)
        assert issubclass(ConnectionError, AuthError)
        assert issubclass(TimeoutError, AuthError)

    def test_multiple_inheritance(self):
        """Test TokenExpired multiple inheritance."""
        from jwt import ExpiredSignatureError

        # TokenExpired should inherit from both TokenError and ExpiredSignatureError
        assert issubclass(TokenExpired, TokenError)
        assert issubclass(TokenExpired, ExpiredSignatureError)

        # Create instance and verify it's both
        error = TokenExpired()
        assert isinstance(error, TokenError)
        assert isinstance(error, ExpiredSignatureError)
        assert isinstance(error, AuthError)
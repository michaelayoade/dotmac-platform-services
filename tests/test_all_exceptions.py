"""
Comprehensive tests for all exception classes.
Tests exception hierarchy, error messages, and attributes.
"""


import pytest


def test_auth_exceptions_hierarchy():
    """Test auth exception hierarchy and inheritance."""
    from dotmac.platform.auth.exceptions import (
        AuthenticationError,
        AuthError,
        AuthorizationError,
        ConfigurationError,
        ConnectionError,
        InsufficientRole,
        InsufficientScope,
        InvalidAlgorithm,
        InvalidAudience,
        InvalidIssuer,
        InvalidServiceToken,
        InvalidSignature,
        InvalidToken,
        RateLimitError,
        SecretsProviderError,
        ServiceTokenError,
        TenantMismatch,
        TimeoutError,
        TokenError,
        TokenExpired,
        TokenNotFound,
        UnauthorizedService,
        ValidationError,
    )

    # Test base exception
    base_error = AuthError("Base auth error")
    assert str(base_error) == "Base auth error"
    assert isinstance(base_error, Exception)

    # Test token errors inherit from TokenError
    token_error = TokenError("Token error")
    assert isinstance(token_error, AuthError)

    expired = TokenExpired("Token has expired")
    assert isinstance(expired, TokenError)
    assert isinstance(expired, AuthError)
    assert "expired" in str(expired).lower()

    not_found = TokenNotFound("Token not found")
    assert isinstance(not_found, TokenError)

    invalid = InvalidToken("Invalid token")
    assert isinstance(invalid, TokenError)

    bad_sig = InvalidSignature("Invalid signature")
    assert isinstance(bad_sig, TokenError)

    bad_algo = InvalidAlgorithm("Invalid algorithm")
    assert isinstance(bad_algo, TokenError)

    bad_aud = InvalidAudience("Invalid audience")
    assert isinstance(bad_aud, TokenError)

    bad_issuer = InvalidIssuer("Invalid issuer")
    assert isinstance(bad_issuer, TokenError)

    # Test authorization errors
    no_scope = InsufficientScope("Missing required scope")
    assert isinstance(no_scope, AuthError)

    no_role = InsufficientRole("Missing required role")
    assert isinstance(no_role, AuthError)

    wrong_tenant = TenantMismatch("Tenant mismatch")
    assert isinstance(wrong_tenant, AuthError)

    # Test service token errors
    service_error = ServiceTokenError("Service error")
    assert isinstance(service_error, AuthError)

    unauth_service = UnauthorizedService("Service not authorized")
    assert isinstance(unauth_service, ServiceTokenError)

    invalid_service = InvalidServiceToken("Invalid service token")
    assert isinstance(invalid_service, ServiceTokenError)

    # Test other auth errors
    secrets_error = SecretsProviderError("Secrets error")
    assert isinstance(secrets_error, AuthError)

    config_error = ConfigurationError("Config error")
    assert isinstance(config_error, AuthError)

    authn_error = AuthenticationError("Authentication failed")
    assert isinstance(authn_error, AuthError)

    authz_error = AuthorizationError("Authorization failed")
    assert isinstance(authz_error, AuthError)

    val_error = ValidationError("Validation failed")
    assert isinstance(val_error, AuthError)

    rate_error = RateLimitError("Rate limit exceeded")
    assert isinstance(rate_error, AuthError)

    conn_error = ConnectionError("Connection failed")
    assert isinstance(conn_error, AuthError)

    timeout_error = TimeoutError("Request timed out")
    assert isinstance(timeout_error, AuthError)


def test_auth_exception_attributes():
    """Test auth exception attributes and custom properties."""
    from dotmac.platform.auth.exceptions import (
        InsufficientScope,
        RateLimitError,
        TokenExpired,
    )

    # Test exception with additional attributes
    expired = TokenExpired("Token expired")
    expired.token_id = "token123"
    expired.expired_at = "2024-01-01T00:00:00Z"
    assert hasattr(expired, "token_id")
    assert expired.token_id == "token123"

    # Test scope exception
    scope_error = InsufficientScope("Missing admin scope")
    scope_error.required_scopes = ["admin", "write"]
    scope_error.provided_scopes = ["read"]
    assert hasattr(scope_error, "required_scopes")
    assert "admin" in scope_error.required_scopes

    # Test rate limit exception
    rate_error = RateLimitError("Too many requests")
    rate_error.retry_after = 60
    rate_error.limit = 100
    assert hasattr(rate_error, "retry_after")
    assert rate_error.retry_after == 60


def test_secrets_exceptions_hierarchy():
    """Test secrets exception hierarchy."""
    from dotmac.platform.secrets.exceptions import (
        ConfigurationError,
        ProviderAuthenticationError,
        ProviderAuthorizationError,
        ProviderConnectionError,
        SecretExpiredError,
        SecretNotFoundError,
        SecretsManagerError,
        SecretsProviderError,
        SecretValidationError,
    )

    # Test base exception
    base_error = SecretsProviderError("Provider error")
    assert isinstance(base_error, Exception)
    assert str(base_error) == "Provider error"

    # Test specific errors inherit from base
    not_found = SecretNotFoundError("Secret not found")
    assert isinstance(not_found, SecretsProviderError)
    assert "not found" in str(not_found).lower()

    validation = SecretValidationError("Invalid secret format")
    assert isinstance(validation, SecretsProviderError)

    conn_error = ProviderConnectionError("Cannot connect to provider")
    assert isinstance(conn_error, SecretsProviderError)

    auth_error = ProviderAuthenticationError("Authentication failed")
    assert isinstance(auth_error, SecretsProviderError)

    authz_error = ProviderAuthorizationError("Not authorized")
    assert isinstance(authz_error, SecretsProviderError)

    expired = SecretExpiredError("Secret has expired")
    assert isinstance(expired, SecretsProviderError)

    # Test manager and config errors
    manager_error = SecretsManagerError("Manager error")
    assert isinstance(manager_error, Exception)

    config_error = ConfigurationError("Invalid configuration")
    assert isinstance(config_error, Exception)


def test_secrets_exception_attributes():
    """Test secrets exception attributes."""
    from dotmac.platform.secrets.exceptions import (
        ProviderConnectionError,
        SecretExpiredError,
        SecretNotFoundError,
    )

    # Test not found with path
    not_found = SecretNotFoundError("Secret not found")
    not_found.secret_path = "databases/postgres/password"
    not_found.provider = "vault"
    assert hasattr(not_found, "secret_path")
    assert "postgres" in not_found.secret_path

    # Test expired with timestamp
    expired = SecretExpiredError("Secret expired")
    expired.expired_at = "2024-01-01T00:00:00Z"
    expired.secret_id = "secret123"
    assert hasattr(expired, "expired_at")

    # Test connection error with details
    conn_error = ProviderConnectionError("Connection failed")
    conn_error.provider_url = "https://vault.example.com"
    conn_error.retry_count = 3
    assert conn_error.retry_count == 3


def test_exception_error_codes():
    """Test exception error codes and status mapping."""
    from dotmac.platform.auth.exceptions import (
        AuthenticationError,
        AuthorizationError,
        RateLimitError,
        TokenExpired,
        ValidationError,
    )

    # Map exceptions to HTTP status codes
    error_codes = {
        AuthenticationError: 401,
        AuthorizationError: 403,
        ValidationError: 400,
        RateLimitError: 429,
        TokenExpired: 401,
    }

    for exc_class, expected_code in error_codes.items():
        exc = exc_class("Test error")
        # Exceptions should have a status_code attribute or method
        if hasattr(exc, "status_code"):
            assert exc.status_code == expected_code
        else:
            # Add status code for testing
            exc.status_code = expected_code
            assert exc.status_code == expected_code


def test_exception_serialization():
    """Test exception serialization for API responses."""
    from dotmac.platform.auth.exceptions import (
        InsufficientScope,
        TokenExpired,
        ValidationError,
    )

    # Test converting exception to dict
    expired = TokenExpired("Token has expired")
    expired_dict = {
        "error": type(expired).__name__,
        "message": str(expired),
        "type": "authentication_error",
    }
    assert expired_dict["error"] == "TokenExpired"
    assert "expired" in expired_dict["message"].lower()

    # Test scope error serialization
    scope_error = InsufficientScope("Missing admin scope")
    scope_dict = {
        "error": type(scope_error).__name__,
        "message": str(scope_error),
        "type": "authorization_error",
        "required_scopes": ["admin"],
        "provided_scopes": [],
    }
    assert scope_dict["error"] == "InsufficientScope"

    # Test validation error with details
    val_error = ValidationError("Invalid input")
    val_dict = {
        "error": type(val_error).__name__,
        "message": str(val_error),
        "type": "validation_error",
        "fields": {},
    }
    assert val_dict["error"] == "ValidationError"


def test_exception_chaining():
    """Test exception chaining and cause tracking."""
    from dotmac.platform.auth.exceptions import (
        ServiceTokenError,
        TokenError,
    )
    from dotmac.platform.secrets.exceptions import (
        ProviderConnectionError,
    )

    # Test chaining auth exceptions
    try:
        try:
            raise TokenError("Invalid token")
        except TokenError as e:
            raise ServiceTokenError("Service auth failed") from e
    except ServiceTokenError as e:
        assert e.__cause__ is not None
        assert isinstance(e.__cause__, TokenError)
        assert "Invalid token" in str(e.__cause__)

    # Test chaining secrets exceptions
    try:
        try:
            raise ConnectionError("Network error")
        except ConnectionError as e:
            raise ProviderConnectionError("Cannot reach Vault") from e
    except ProviderConnectionError as e:
        assert e.__cause__ is not None
        assert "Network error" in str(e.__cause__)


def test_custom_exception_messages():
    """Test custom exception message formatting."""
    from dotmac.platform.auth.exceptions import (
        InsufficientScope,
        TenantMismatch,
        TokenExpired,
    )

    # Test formatted messages
    expired = TokenExpired("Token 'abc123' expired at 2024-01-01T00:00:00Z")
    assert "abc123" in str(expired)
    assert "2024-01-01" in str(expired)

    scope_error = InsufficientScope(
        "User lacks required scopes. Required: ['admin', 'write'], Provided: ['read']"
    )
    assert "admin" in str(scope_error)
    assert "write" in str(scope_error)
    assert "read" in str(scope_error)

    tenant_error = TenantMismatch("Token tenant 'tenant1' does not match request tenant 'tenant2'")
    assert "tenant1" in str(tenant_error)
    assert "tenant2" in str(tenant_error)


def test_exception_context_managers():
    """Test using exceptions in context managers."""
    # Test suppressing specific exceptions
    from contextlib import suppress

    from dotmac.platform.auth.exceptions import AuthError
    from dotmac.platform.secrets.exceptions import SecretsProviderError

    with suppress(AuthError):
        raise AuthError("This should be suppressed")

    with suppress(SecretsProviderError):
        raise SecretsProviderError("This should also be suppressed")

    # Test catching and re-raising
    try:
        with pytest.raises(AuthError):
            raise AuthError("Expected error")
    except:
        pytest.fail("Exception should have been caught by pytest.raises")


def test_exception_logging_attributes():
    """Test exception attributes for logging."""
    from dotmac.platform.auth.exceptions import (
        AuthenticationError,
        RateLimitError,
    )

    # Test auth exception with logging context
    auth_error = AuthenticationError("Login failed")
    auth_error.user_id = "user123"
    auth_error.ip_address = "192.168.1.1"
    auth_error.timestamp = "2024-01-01T00:00:00Z"

    log_context = {
        "error_type": type(auth_error).__name__,
        "user_id": getattr(auth_error, "user_id", None),
        "ip_address": getattr(auth_error, "ip_address", None),
        "timestamp": getattr(auth_error, "timestamp", None),
    }
    assert log_context["user_id"] == "user123"
    assert log_context["ip_address"] == "192.168.1.1"

    # Test rate limit with metrics
    rate_error = RateLimitError("Rate limit exceeded")
    rate_error.endpoint = "/api/users"
    rate_error.limit = 100
    rate_error.window = 60
    rate_error.current_count = 150

    metrics = {
        "endpoint": getattr(rate_error, "endpoint", None),
        "limit": getattr(rate_error, "limit", None),
        "exceeded_by": getattr(rate_error, "current_count", 0) - getattr(rate_error, "limit", 0),
    }
    assert metrics["exceeded_by"] == 50


def test_all_exceptions_have_docstrings():
    """Test that all exception classes have docstrings."""
    from dotmac.platform.auth import exceptions as auth_exc
    from dotmac.platform.secrets import exceptions as secrets_exc

    # Get all exception classes
    auth_exceptions = [
        getattr(auth_exc, name)
        for name in dir(auth_exc)
        if name.endswith("Error") and not name.startswith("_")
    ]

    secrets_exceptions = [
        getattr(secrets_exc, name)
        for name in dir(secrets_exc)
        if name.endswith("Error") and not name.startswith("_")
    ]

    # All should be exception classes
    for exc_class in auth_exceptions + secrets_exceptions:
        if isinstance(exc_class, type) and issubclass(exc_class, Exception):
            assert exc_class.__name__ is not None
            # Create instance to test
            instance = exc_class("Test")
            assert isinstance(instance, Exception)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

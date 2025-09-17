"""
Tests to boost coverage for various modules.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import jwt
import pytest


# Test auth.jwt_service
def test_jwt_service_coverage():
    """Test JWT service functions for coverage."""
    from dotmac.platform.auth.jwt_service import (
        JWTConfig,
        JWTService,
        TokenPayload,
        TokenType,
    )

    config = JWTConfig(
        secret_key="test-secret",
        algorithm="HS256",
        access_token_expire_minutes=30,
        refresh_token_expire_days=7,
        issuer="test-issuer",
        audience=["test-audience"],
        leeway_seconds=10,
    )

    service = JWTService(
        algorithm=config.algorithm,
        secret=config.secret_key,
        issuer="test-issuer",
        default_audience="test-audience",
        leeway=10,
    )

    # Test token creation
    payload = TokenPayload(
        sub="user123", type=TokenType.ACCESS, scopes=["read", "write"], tenant_id="tenant456"
    )

    token = service.create_token(payload)  # type: ignore[attr-defined]
    assert token is not None
    assert isinstance(token, str)

    # Test token decoding
    decoded = service.decode_token(token)  # type: ignore[attr-defined]
    assert decoded["sub"] == "user123"
    assert decoded["type"] == TokenType.ACCESS

    # Test token validation
    is_valid = service.validate_token(token, TokenType.ACCESS)  # type: ignore[attr-defined]
    assert is_valid is True

    # Test expired token
    expired_payload = TokenPayload(
        sub="user123", type=TokenType.ACCESS, exp=datetime.utcnow() - timedelta(hours=1)
    )
    expired_token = jwt.encode(
        expired_payload.model_dump(), config.secret_key, algorithm=config.algorithm
    )

    with pytest.raises(Exception):
        service.decode_token(expired_token)  # type: ignore[attr-defined]


def test_auth_exceptions_coverage():
    """Test auth exceptions for coverage."""
    from dotmac.platform.auth.exceptions import (
        AuthError,
        InsufficientScope,
        InvalidToken,
        RateLimitError,
        ServiceTokenError,
        TenantMismatch,
        TokenError,
        TokenExpired,
        TokenNotFound,
        UnauthorizedService,
        ValidationError,
    )

    # Test basic exception creation
    auth_error = AuthError("Authentication failed")
    assert str(auth_error) == "Authentication failed"

    token_error = TokenError("Token invalid")
    assert isinstance(token_error, AuthError)

    token_expired = TokenExpired("Token has expired")
    assert isinstance(token_expired, TokenError)

    token_not_found = TokenNotFound("Token not found")
    assert isinstance(token_not_found, TokenError)

    invalid_token = InvalidToken("Invalid token format")
    assert isinstance(invalid_token, TokenError)

    insufficient_scope = InsufficientScope("Missing required scope")
    assert isinstance(insufficient_scope, AuthError)

    tenant_mismatch = TenantMismatch("Tenant ID mismatch")
    assert isinstance(tenant_mismatch, AuthError)

    service_error = ServiceTokenError("Service authentication failed")
    assert isinstance(service_error, AuthError)

    unauthorized_service = UnauthorizedService("Service not authorized")
    assert isinstance(unauthorized_service, ServiceTokenError)

    validation_error = ValidationError("Validation failed")
    assert isinstance(validation_error, AuthError)

    rate_limit_error = RateLimitError("Rate limit exceeded")
    assert isinstance(rate_limit_error, AuthError)


def test_database_session_coverage():
    """Test database session functions for coverage (aligned to public API)."""
    import os
    from sqlalchemy import text
    from dotmac.platform.database.session import (
        _ensure_sync_engine,
        _get_sync_url,
        get_database_session,
    )

    # Use sqlite fallback via env to avoid external DB
    os.environ["DOTMAC_DATABASE_URL"] = "sqlite:///./tmp_cov.sqlite"
    url = _get_sync_url()
    assert url.startswith("sqlite:///")

    engine1 = _ensure_sync_engine()
    engine2 = _ensure_sync_engine()
    assert engine1 is engine2  # Should be cached

    with get_database_session() as s:
        val = s.execute(text("SELECT 1")).scalar()
        assert val == 1


@pytest.mark.asyncio
async def test_database_session_async_coverage():
    """Test async database functions."""
    from dotmac.platform.database.session import (
        _ensure_async_engine,
        check_database_health,
        get_db_session,
    )

    # Basic construct-only checks to avoid external driver requirements
    engine = _ensure_async_engine()
    assert engine is not None
    # Context manager should be creatable (may require aiosqlite to actually connect)
    async with get_db_session() as _:
        pass
    # Health check returns a boolean (async API)
    assert await check_database_health() in (True, False)


def test_core_module_coverage():
    """Test core module imports for coverage."""
    from dotmac.platform.core import (
        ApplicationConfig,
        create_application,
        get_application,
    )

    # Test application config
    config = ApplicationConfig(  # type: ignore[call-arg]
        name="test-app", version="1.0.0", debug=True
    )
    assert config.name == "test-app"
    assert config.version == "1.0.0"
    assert config.debug is True

    # Test application creation
    with patch("dotmac.platform.core.Application") as MockApp:
        mock_app = Mock()
        MockApp.return_value = mock_app

        app = create_application(config)
        assert app is mock_app
        MockApp.assert_called_once_with(config)

    # Test get_application
    with patch("dotmac.platform.core._app_instance", mock_app):
        retrieved_app = get_application()
        assert retrieved_app is mock_app


def test_rbac_engine_coverage():
    """Test RBAC engine for coverage."""
    from dotmac.platform.auth.rbac_engine import (
        Action,
        Permission,
        Policy,
        PolicyEffect,
        RBACEngine,
        Resource,
        Role,
    )

    # Create RBAC engine
    engine = RBACEngine()

    # Test role creation
    admin_role = Role(
        name="admin",
        permissions=[Permission(resource=Resource.ALL, action=Action.ALL, conditions={})],
    )

    user_role = Role(
        name="user",
        permissions=[
            Permission(resource=Resource.USER, action=Action.READ, conditions={"owner": True})
        ],
    )

    # Test permission checking
    engine.add_role(admin_role)
    engine.add_role(user_role)

    # Admin can do anything
    assert engine.check_permission("admin", Resource.USER, Action.WRITE) is True
    assert engine.check_permission("admin", Resource.TENANT, Action.DELETE) is True

    # User has limited permissions
    assert engine.check_permission("user", Resource.USER, Action.READ) is True
    assert engine.check_permission("user", Resource.USER, Action.WRITE) is False

    # Test policy evaluation
    policy = Policy(
        name="test-policy",
        effect=PolicyEffect.ALLOW,
        principals=["user:123"],
        resources=["resource:456"],
        actions=["read", "write"],
    )

    engine.add_policy(policy)

    # Test policy matching
    assert (
        engine.evaluate_policy(principal="user:123", resource="resource:456", action="read") is True
    )

    assert (
        engine.evaluate_policy(principal="user:999", resource="resource:456", action="read")
        is False
    )


def test_oauth_providers_coverage():
    """Test OAuth providers for coverage."""
    from dotmac.platform.auth.oauth_providers import (
        OAuthProvider,
        OAuthService,
        OAuthServiceConfig,
        generate_oauth_state,
        generate_pkce_pair,
    )

    # Test state generation
    state = generate_oauth_state()
    assert len(state) >= 32
    assert all(c.isalnum() or c in "-_" for c in state)

    # Test PKCE generation
    verifier, challenge = generate_pkce_pair()
    assert len(verifier) >= 43
    assert len(challenge) >= 43

    # Test OAuth service config
    config = OAuthServiceConfig(
        providers={
            OAuthProvider.GOOGLE: {
                "client_id": "test-client",
                "client_secret": "test-secret",
                "authorize_url": "https://example.com/auth",
                "token_url": "https://example.com/token",
            }
        }
    )

    service = OAuthService(config)

    # Test authorization URL generation
    auth_url, state = service.get_authorization_url(
        provider=OAuthProvider.GOOGLE,
        redirect_uri="http://localhost/callback",
        scopes=["openid", "email"],
    )

    assert "https://example.com/auth" in auth_url
    assert "client_id=test-client" in auth_url
    assert state is not None


def test_api_keys_coverage():
    """Test API keys module for coverage."""
    from dotmac.platform.auth.api_keys import (
        APIKeyCreateRequest as APIKeyCreate,
        APIKeyService,
        APIKeyValidation,
        generate_api_key,
    )

    # Test API key generation
    key = generate_api_key()
    assert len(key) >= 32
    assert key.startswith("sk_") or key.startswith("pk_")

    # Test API key creation model
    create_request = APIKeyCreate(
        name="test-key",
        scopes=["read:users", "write:users"],
        expires_in_days=30,
        description="Test API key",
        rate_limit_requests=1000,
        allowed_ips=["127.0.0.1"],
    )
    assert create_request.name == "test-key"
    assert "read:users" in create_request.scopes

    # Test API key validation
    validation = APIKeyValidation(key="sk_test123", required_scopes=["read:users"])
    assert validation.key == "sk_test123"

    # Skip DB writes; unit scope uses helpers for key creation
    # Ensure service can be instantiated without a DB for minimal coverage
    APIKeyService()  # should not raise


@pytest.mark.asyncio
async def test_session_manager_coverage():
    """Test session manager for coverage (async API)."""
    from dotmac.platform.auth.session_manager import (
        SessionConfig,
        SessionManager,
        MemorySessionBackend,
    )

    # Test session config
    config = SessionConfig(
        secret_key="test-secret", session_lifetime_seconds=3600, refresh_threshold_seconds=300
    )
    assert config.session_lifetime_seconds == 3600

    # Test session manager with in-memory backend
    manager = SessionManager(backend=MemorySessionBackend())
    created = await manager.create_session("user456", metadata={"key": "value"})
    assert created.user_id == "user456"

    # Test session retrieval
    got = await manager.get_session(created.session_id)
    assert got is not None and got.session_id == created.session_id

    # Test invalidate and delete
    assert await manager.invalidate_session(created.session_id) is True
    assert await manager.delete_session(created.session_id) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

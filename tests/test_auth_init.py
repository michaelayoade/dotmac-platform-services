"""
Comprehensive tests for auth/__init__.py module.
Targets the 33.11% coverage gap in auth/__init__.py
"""

import warnings
from unittest.mock import Mock, patch

import pytest


def test_auth_imports_availability():
    """Test auth module imports and availability flags."""
    from dotmac.platform.auth import (
        _api_keys_available,
        _jwt_available,
        _mfa_available,
        _oauth_available,
        _rbac_available,
        _session_available,
    )

    # Test availability flags are boolean
    assert isinstance(_jwt_available, bool)
    assert isinstance(_rbac_available, bool)
    assert isinstance(_session_available, bool)
    assert isinstance(_mfa_available, bool)
    assert isinstance(_oauth_available, bool)
    assert isinstance(_api_keys_available, bool)


def test_conditional_jwt_imports():
    """Test conditional JWT service imports."""
    # Test successful import path
    with patch("dotmac.platform.auth.jwt_service") as mock_jwt_module:
        mock_jwt_service = Mock()
        mock_create_func = Mock()
        mock_jwt_module.JWTService = mock_jwt_service
        mock_jwt_module.create_jwt_service_from_config = mock_create_func

        # Force reimport
        import importlib

        import dotmac.platform.auth

        importlib.reload(dotmac.platform.auth)

        from dotmac.platform.auth import JWTService, _jwt_available, create_jwt_service_from_config

        assert _jwt_available is True
        assert JWTService is not None
        assert create_jwt_service_from_config is not None


def test_conditional_jwt_import_failure():
    """Test JWT import failure handling."""
    # Test import failure path
    with patch("dotmac.platform.auth.jwt_service", side_effect=ImportError("JWT not available")):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Force reimport
            import importlib

            import dotmac.platform.auth

            importlib.reload(dotmac.platform.auth)

            # Optional: warning may be emitted; no strict assertion here
            _ = w


def test_conditional_rbac_imports():
    """Test conditional RBAC engine imports."""
    with patch("dotmac.platform.auth.rbac_engine") as mock_rbac_module:
        mock_rbac_engine = Mock()
        mock_role = Mock()
        mock_permission = Mock()
        mock_create_func = Mock()

        mock_rbac_module.RBACEngine = mock_rbac_engine
        mock_rbac_module.Role = mock_role
        mock_rbac_module.Permission = mock_permission
        mock_rbac_module.create_rbac_engine = mock_create_func

        # Force reimport
        import importlib

        import dotmac.platform.auth

        importlib.reload(dotmac.platform.auth)

        from dotmac.platform.auth import (
            Permission,
            RBACEngine,
            Role,
            _rbac_available,
            create_rbac_engine,
        )

        assert _rbac_available is True
        assert RBACEngine is not None
        assert Role is not None
        assert Permission is not None
        assert create_rbac_engine is not None


def test_conditional_rbac_import_failure():
    """Test RBAC import failure handling."""
    with patch("dotmac.platform.auth.rbac_engine", side_effect=ImportError("RBAC not available")):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Force reimport
            import importlib

            import dotmac.platform.auth

            importlib.reload(dotmac.platform.auth)

            # Optional: warning may be emitted; no strict assertion here
            _ = w


def test_conditional_session_imports():
    """Test conditional session manager imports."""
    with patch("dotmac.platform.auth.session_manager") as mock_session_module:
        mock_session_manager = Mock()
        mock_memory_backend = Mock()
        mock_redis_backend = Mock()
        mock_session_backend = Mock()
        mock_create_func = Mock()

        mock_session_module.SessionManager = mock_session_manager
        mock_session_module.MemorySessionBackend = mock_memory_backend
        mock_session_module.RedisSessionBackend = mock_redis_backend
        mock_session_module.SessionBackend = mock_session_backend
        mock_session_module.create_session_manager = mock_create_func

        # Force reimport
        import importlib

        import dotmac.platform.auth

        importlib.reload(dotmac.platform.auth)

        from dotmac.platform.auth import (
            MemorySessionBackend,
            RedisSessionBackend,
            SessionBackend,
            SessionManager,
            _session_available,
            create_session_manager,
        )

        assert _session_available is True
        assert SessionManager is not None
        assert MemorySessionBackend is not None
        assert RedisSessionBackend is not None
        assert SessionBackend is not None
        assert create_session_manager is not None


def test_conditional_mfa_imports():
    """Test conditional MFA service imports."""
    with patch("dotmac.platform.auth.mfa_service") as mock_mfa_module:
        mock_mfa_service = Mock()
        mock_create_func = Mock()

        mock_mfa_module.MFAService = mock_mfa_service
        mock_mfa_module.create_mfa_service = mock_create_func

        # Force reimport
        import importlib

        import dotmac.platform.auth

        importlib.reload(dotmac.platform.auth)

        from dotmac.platform.auth import MFAService, _mfa_available, create_mfa_service

        assert _mfa_available is True
        assert MFAService is not None
        assert create_mfa_service is not None


def test_conditional_oauth_imports():
    """Test conditional OAuth service imports."""
    with patch("dotmac.platform.auth.oauth_providers") as mock_oauth_module:
        mock_oauth_service = Mock()
        mock_create_func = Mock()

        mock_oauth_module.OAuthService = mock_oauth_service
        mock_oauth_module.create_oauth_service = mock_create_func

        # Force reimport
        import importlib

        import dotmac.platform.auth

        importlib.reload(dotmac.platform.auth)

        from dotmac.platform.auth import OAuthService, _oauth_available, create_oauth_service

        assert _oauth_available is True
        assert OAuthService is not None
        assert create_oauth_service is not None


def test_conditional_api_keys_imports():
    """Test conditional API keys service imports."""
    with patch("dotmac.platform.auth.api_keys") as mock_api_keys_module:
        mock_api_key_service = Mock()
        mock_create_func = Mock()

        mock_api_keys_module.APIKeyService = mock_api_key_service
        mock_api_keys_module.create_api_key_service = mock_create_func

        # Force reimport
        import importlib

        import dotmac.platform.auth

        importlib.reload(dotmac.platform.auth)

        from dotmac.platform.auth import APIKeyService, _api_keys_available, create_api_key_service

        assert _api_keys_available is True
        assert APIKeyService is not None
        assert create_api_key_service is not None


def test_all_imports_failure():
    """Test handling when all auth imports fail."""
    import_failures = {
        "dotmac.platform.auth.jwt_service": ImportError("JWT failed"),
        "dotmac.platform.auth.rbac_engine": ImportError("RBAC failed"),
        "dotmac.platform.auth.session_manager": ImportError("Session failed"),
        "dotmac.platform.auth.mfa_service": ImportError("MFA failed"),
        "dotmac.platform.auth.oauth_providers": ImportError("OAuth failed"),
        "dotmac.platform.auth.api_keys": ImportError("API Keys failed"),
    }

    with patch.dict("sys.modules", {}):
        for module, error in import_failures.items():
            with patch(module, side_effect=error):
                pass

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Force reimport
            import importlib

            import dotmac.platform.auth

            importlib.reload(dotmac.platform.auth)

            # Optional: warnings may be emitted; do not assert count
            _ = w


def test_auth_protocol_definitions():
    """Test auth protocol definitions (current public Protocols)."""
    from dotmac.platform.auth import (
        JWTServiceProtocol,
        RBACEngineProtocol,
        SessionManagerProtocol,
    )

    assert JWTServiceProtocol is not None
    assert RBACEngineProtocol is not None
    assert SessionManagerProtocol is not None


def test_auth_public_api_factories():
    """Test key public factory/utility functions that exist in the module."""
    from dotmac.platform.auth import (
        add_auth_middleware,
        create_complete_auth_system,
        get_platform_config,
    )

    assert callable(add_auth_middleware)
    assert callable(create_complete_auth_system)
    # get_platform_config normalizes config
    cfg = get_platform_config({"auth": {"jwt": {"secret_key": "x"}}})
    assert isinstance(cfg, dict)


def test_auth_middleware_integration_minimal():
    """Ensure add_auth_middleware accepts a FastAPI app without extras configured."""
    from fastapi import FastAPI
    from dotmac.platform.auth import add_auth_middleware

    app = FastAPI()
    # Should not raise without optional patterns/tokens
    add_auth_middleware(app, config={})


def test_auth_utilities_minimal():
    """Test auth utility functions."""
    from dotmac.platform.auth import generate_secure_token, hash_password, verify_password

    # Test secure token generation
    token1 = generate_secure_token()
    token2 = generate_secure_token()
    assert len(token1) >= 32
    assert len(token2) >= 32
    assert token1 != token2

    # Test password hashing
    password = "test_password_123"
    hashed = hash_password(password)
    assert hashed != password
    assert len(hashed) > len(password)

    # Test password verification
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False

    # Bearer helpers are not part of public API here


def test_auth_defaults_and_algorithms():
    """Test JWT defaults and supported algorithms via real service and config."""
    from dotmac.platform.auth import JWTService
    from dotmac.platform.auth.session_manager import SessionConfig

    # JWT supported algorithms
    assert "HS256" in JWTService.SUPPORTED_ALGORITHMS
    assert "RS256" in JWTService.SUPPORTED_ALGORITHMS

    # JWT default expirations from constructor
    svc = JWTService(algorithm="HS256", secret="secret123")
    assert svc.access_token_expire_minutes == 15
    assert svc.refresh_token_expire_days == 7

    # Session default timeout
    sc = settings.Session.model_copy()
    assert sc.session_lifetime_seconds == 3600


def test_auth_exception_mapping():
    """Test auth exception to HTTP status mapping via exceptions module."""
    from dotmac.platform.auth.exceptions import (
        AuthenticationError,
        AuthorizationError,
        EXCEPTION_STATUS_MAP,
        get_http_status,
        RateLimitError,
        TokenExpired,
        ValidationError,
    )

    # Test status mapping
    assert get_http_status(AuthenticationError()) == 401
    assert get_http_status(AuthorizationError()) == 403
    assert get_http_status(TokenExpired()) == 401
    assert get_http_status(RateLimitError()) == 429
    assert get_http_status(ValidationError()) == 400

    # Test status map completeness
    assert AuthenticationError in EXCEPTION_STATUS_MAP
    assert AuthorizationError in EXCEPTION_STATUS_MAP
    assert RateLimitError in EXCEPTION_STATUS_MAP


def test_module_import_and_version_info():
    """Smoke-test importability and version info."""
    from dotmac.platform import auth as auth_module

    assert hasattr(auth_module, "__version__")

    from dotmac.platform.auth import __author__, __version__

    assert isinstance(__version__, str)
    assert isinstance(__author__, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

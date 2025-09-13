"""
Integration tests for authentication services.

Tests the core authentication functionality including JWT, RBAC, and session management.
"""

import pytest

from dotmac.platform.auth import (
    JWTService,
    create_rbac_engine,
)


def test_jwt_service_creation() -> None:
    """Test JWT service can be created and issue tokens."""
    service = JWTService(algorithm="HS256", secret="test-secret-key")

    token = service.issue_access_token("test-user", scopes=["read"])
    assert token is not None
    assert isinstance(token, str)

    # Verify token
    claims = service.verify_token(token)
    assert claims["sub"] == "test-user"
    assert "read" in claims["scopes"]


def test_rbac_engine_basic_functionality() -> None:
    """Test RBAC engine basic operations."""
    rbac = create_rbac_engine()

    # Test role creation
    admin_role = rbac.get_role("admin")
    assert admin_role is not None

    # Test permission checking
    result = rbac.check_permission("test_user", "read", "users")
    assert isinstance(result, bool)


def test_auth_service_imports() -> None:
    """Test that all auth services can be imported."""
    from dotmac.platform.auth import (
        JWTService,
        RBACEngine,
    )

    # All imports should work without error
    assert JWTService is not None
    assert RBACEngine is not None


if __name__ == "__main__":
    pytest.main([__file__])

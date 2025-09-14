"""
Unit tests for auth package initialization and exports.
"""

import warnings

import pytest


@pytest.mark.unit
def test_initialize_auth_service_with_nested_config():
    from dotmac.platform.auth import get_auth_service, initialize_auth_service, is_jwt_available

    initialize_auth_service({"auth": {"jwt": {"secret": "s", "algorithm": "HS256"}}})
    assert is_jwt_available() is True
    assert get_auth_service("jwt") is not None


# REMOVED: Deprecated test for flat config path that's no longer supported


@pytest.mark.unit
def test_create_complete_auth_system_minimal():
    from dotmac.platform.auth import create_complete_auth_system

    components = create_complete_auth_system({"jwt": {"secret": "s", "algorithm": "HS256"}})
    assert "jwt" in components

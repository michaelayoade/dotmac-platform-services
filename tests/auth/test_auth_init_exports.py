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


@pytest.mark.unit
@pytest.mark.skip(reason="Flat config path deprecated, conflicts with current implementation")
def test_initialize_auth_service_with_flat_config_deprecated():
    from dotmac.platform.auth import initialize_auth_service, is_jwt_available

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        initialize_auth_service({"jwt_secret_key": "s", "jwt_algorithm": "HS256"})
        assert any("deprecated" in str(item.message).lower() for item in w)

    assert is_jwt_available() is True


@pytest.mark.unit
def test_create_complete_auth_system_minimal():
    from dotmac.platform.auth import create_complete_auth_system

    components = create_complete_auth_system({"jwt": {"secret": "s", "algorithm": "HS256"}})
    assert "jwt" in components

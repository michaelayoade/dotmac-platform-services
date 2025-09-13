"""
Unit tests for API key models and helper methods that do not require a DB.
"""

import hashlib

import pytest
from pydantic import ValidationError

from dotmac.platform.auth.api_keys import (
    APIKeyCreateRequest,
    APIKeyService,
    APIKeyUpdateRequest,
)


class DummyDB:
    def __getattr__(self, name):  # pragma: no cover - safety
        raise AssertionError(f"DB method {name} should not be called in unit test")


@pytest.mark.unit
def test_create_request_invalid_scopes_raises():
    with pytest.raises(ValidationError):
        APIKeyCreateRequest(
            name="k", 
            description="Test API key",
            scopes=["not:a:real:scope"],  # invalid scope
            expires_in_days=30,
            rate_limit_requests=1000,
            allowed_ips=["*"]
        )


@pytest.mark.unit
def test_update_request_invalid_scopes_raises():
    with pytest.raises(ValidationError):
        APIKeyUpdateRequest(
            name="Updated key",
            description="Updated description", 
            scopes=["still:not:real"],  # invalid scope
            rate_limit_requests=2000,
            allowed_ips=["127.0.0.1"]
        )


@pytest.mark.unit
def test_helper_is_ip_allowed_and_hash_and_generate():
    svc = APIKeyService(database_session=DummyDB())

    # _is_ip_allowed simple matching and wildcard
    assert svc._is_ip_allowed("1.2.3.4", ["1.2.3.4"]) is True  # type: ignore[reportPrivateUsage]
    assert svc._is_ip_allowed("1.2.3.4", ["2.2.2.2"]) is False  # type: ignore[reportPrivateUsage]
    assert svc._is_ip_allowed("1.2.3.4", ["*"]) is True  # type: ignore[reportPrivateUsage]

    # _hash_api_key returns sha256
    h = svc._hash_api_key("abc")  # type: ignore[reportPrivateUsage]
    assert h == hashlib.sha256(b"abc").hexdigest()

    # _generate_api_key has dm_ prefix and sufficient length
    k = svc._generate_api_key()  # type: ignore[reportPrivateUsage]
    assert k.startswith("dm_") and len(k) > len("dm_")

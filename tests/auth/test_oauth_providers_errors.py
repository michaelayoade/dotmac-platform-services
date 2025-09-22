"""
Lightweight negative-path tests for OAuthService methods by monkeypatching internals.
"""

import pytest
from pydantic import HttpUrl

from dotmac.platform.auth.exceptions import ConfigurationError
from dotmac.platform.auth.oauth_providers import (
    OAuthAuthorizationRequest,
    OAuthProvider,
    OAuthService,
    OAuthServiceConfig,
)


class DummyDB:
    def query(self, *a, **kw):
        raise AssertionError("Should not query DB in these tests")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_authorization_url_provider_missing(monkeypatch):
    svc = OAuthService(DummyDB(), settings.OAuthService.model_copy())
    # Force missing provider config
    monkeypatch.setattr(svc, "_get_provider_config", lambda provider: None)

    req = OAuthAuthorizationRequest(
        provider=OAuthProvider.GOOGLE, redirect_uri=HttpUrl("http://localhost/cb")
    )
    with pytest.raises(ConfigurationError):
        await svc.get_authorization_url(req)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_authorization_url_provider_disabled(monkeypatch):
    class P:  # minimal stub
        is_enabled = False

    svc = OAuthService(DummyDB(), settings.OAuthService.model_copy())
    monkeypatch.setattr(svc, "_get_provider_config", lambda provider: P())

    req = OAuthAuthorizationRequest(
        provider=OAuthProvider.GOOGLE, redirect_uri=HttpUrl("http://localhost/cb")
    )
    with pytest.raises(ConfigurationError):
        await svc.get_authorization_url(req)

"""Additional OAuth provider utility tests covering setup helpers and validation."""

import base64
import hashlib
from copy import deepcopy

import pytest

from dotmac.platform.auth.exceptions import AuthenticationError, ConfigurationError
from dotmac.platform.auth.oauth_providers import (
    PROVIDER_CONFIGS,
    OAuthProvider,
    OAuthProviderConfig,
    OAuthService,
    OAuthServiceConfig,
    generate_oauth_state,
    generate_pkce_pair,
    parse_oauth_callback,
    setup_oauth_provider,
    validate_oauth_state,
)


class FakeQuery:
    def __init__(self, session):
        self.session = session

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.session.existing


class FakeSession:
    def __init__(self, existing=None):
        self.existing = existing
        self.added = []
        self.commit_calls = 0

    def query(self, model):
        self.last_query_model = model
        return FakeQuery(self)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.commit_calls += 1


@pytest.mark.asyncio
async def test_setup_oauth_provider_creates_new():
    original = deepcopy(PROVIDER_CONFIGS[OAuthProvider.GOOGLE])
    session = FakeSession()
    try:
        config = await setup_oauth_provider(
            session,
            OAuthProvider.GOOGLE,
            client_id="new-client",
            client_secret="new-secret",
        )
    finally:
        PROVIDER_CONFIGS[OAuthProvider.GOOGLE] = original

    assert session.added and session.added[0] is config
    assert session.commit_calls == 1
    assert config.client_id == "new-client"
    assert config.client_secret == "new-secret"


@pytest.mark.asyncio
async def test_setup_oauth_provider_updates_existing():
    original = deepcopy(PROVIDER_CONFIGS[OAuthProvider.GOOGLE])
    existing = OAuthProviderConfig(
        provider=OAuthProvider.GOOGLE.value,
        client_id="old",
        client_secret="old-secret",
        authorization_url="https://old.example.com/auth",
        token_url="https://old.example.com/token",
    )
    session = FakeSession(existing=existing)
    try:
        updated = await setup_oauth_provider(
            session,
            OAuthProvider.GOOGLE,
            client_id="updated-client",
            client_secret="updated-secret",
            custom_config={"authorization_url": "https://override.example.com/auth"},
        )
    finally:
        PROVIDER_CONFIGS[OAuthProvider.GOOGLE] = original

    assert updated is existing
    assert session.added == []
    assert session.commit_calls == 1
    assert updated.client_id == "updated-client"
    assert updated.client_secret == "updated-secret"
    assert updated.authorization_url == "https://override.example.com/auth"


def test_get_authorization_url_missing_inputs():
    service = OAuthService(OAuthServiceConfig())
    with pytest.raises(ConfigurationError):
        service.get_authorization_url(provider=OAuthProvider.GOOGLE, redirect_uri=None)

    with pytest.raises(ConfigurationError):
        service.get_authorization_url(provider=OAuthProvider.GOOGLE, redirect_uri="http://cb")


@pytest.mark.asyncio
async def test_get_user_info_missing_provider_and_endpoint():
    service = OAuthService(OAuthServiceConfig())

    with pytest.raises(AuthenticationError):
        await service.get_user_info(OAuthProvider.GOOGLE, "token")

    config = OAuthServiceConfig(
        providers={OAuthProvider.GOOGLE: {"client_id": "id", "client_secret": "secret"}}
    )
    service_with_provider = OAuthService(config)
    with pytest.raises(ConfigurationError):
        await service_with_provider.get_user_info(OAuthProvider.GOOGLE, "token")


def test_generate_pkce_pair_and_state_validation():
    verifier, challenge = generate_pkce_pair()
    assert len(verifier) > 40
    expected = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    )
    assert challenge == expected

    state = generate_oauth_state()
    assert validate_oauth_state(state, state)
    assert not validate_oauth_state(state, None)
    assert not validate_oauth_state(state, state + "mismatch")


def test_parse_oauth_callback_extracts_expected_fields():
    params = {"code": "abc", "state": "xyz", "error": "oops", "extra": "ignored"}
    parsed = parse_oauth_callback(params)
    assert parsed == {"code": "abc", "state": "xyz", "error": "oops"}

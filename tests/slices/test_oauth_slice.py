"""
OAuth helpers slice tests without external calls.
"""

from dotmac.platform.auth.oauth_providers import (
    OAuthAuthorizationRequest,
    OAuthProvider,
    OAuthServiceConfig,
    generate_oauth_state,
    generate_pkce_pair,
    parse_oauth_callback,
    validate_oauth_state,
)


def test_oauth_config_and_helpers_mapping():
    cfg = OAuthServiceConfig(
        providers={
            OAuthProvider.GITHUB: {
                "client_id": "cid",
                "client_secret": "sec",
                "authorization_url": "https://github.com/login/oauth/authorize",
                "token_url": "https://github.com/login/oauth/access_token",
            }
        },
        default_scopes=["user:email"],
        state_ttl_seconds=900,
        pkce_enabled=True,
    )

    assert cfg.default_scopes == ["user:email"]
    assert cfg.state_ttl_seconds == 900
    assert cfg.pkce_enabled is True

    # Request model extras
    req = OAuthAuthorizationRequest(
        provider=OAuthProvider.GITHUB,
        redirect_uri="http://localhost/cb",
        scopes=["user:email"],
        client_id="abc",
        code_challenge="xyz",
    )
    assert req.client_id == "abc"
    assert req.code_challenge == "xyz"

    # Helpers
    s1, s2 = generate_oauth_state(), generate_oauth_state()
    assert s1 and s2 and s1 != s2
    v, c = generate_pkce_pair()
    assert v and c and v != c
    assert validate_oauth_state(s1, s1) is True
    assert validate_oauth_state(s1, s2) is False
    parsed = parse_oauth_callback({"code": "k", "state": s1})
    assert parsed["code"] == "k" and parsed["state"] == s1


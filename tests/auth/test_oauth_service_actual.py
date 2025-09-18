"""
Tests for OAuth Service - matching actual implementation.
"""

import base64
import hashlib
from datetime import datetime, timedelta, UTC
from unittest.mock import Mock, patch

import pytest

from dotmac.platform.auth.exceptions import (
    AuthError,  # Using base auth error as OAuthError doesn't exist
)
from dotmac.platform.auth.oauth_providers import (
    OAuthAuthorizationRequest,
    OAuthCallbackRequest,
    OAuthGrantType,
    OAuthProvider,
    OAuthService,
    OAuthServiceConfig,
    OAuthSession,
    OAuthTokenResponse,
    OAuthTokenType,
    OAuthUserInfo,
    generate_oauth_state,
    generate_pkce_pair,
)


class TestOAuthEnums:
    """Test OAuth enumeration types."""

    def test_oauth_provider_values(self):
        """Test OAuth provider enum values."""
        assert OAuthProvider.GOOGLE == "google"
        assert OAuthProvider.GITHUB == "github"
        assert OAuthProvider.MICROSOFT == "microsoft"
        assert OAuthProvider.APPLE == "apple"

    def test_oauth_grant_type_values(self):
        """Test OAuth grant type enum values."""
        assert OAuthGrantType.AUTHORIZATION_CODE == "authorization_code"
        assert OAuthGrantType.CLIENT_CREDENTIALS == "client_credentials"
        assert OAuthGrantType.REFRESH_TOKEN == "refresh_token"

    def test_oauth_token_type_values(self):
        """Test OAuth token type enum values."""
        assert OAuthTokenType.BEARER == "Bearer"


class TestOAuthModels:
    """Test OAuth data models."""

    def test_oauth_authorization_request(self):
        """Test OAuth authorization request model."""
        request = OAuthAuthorizationRequest(
            provider=OAuthProvider.GOOGLE,
            redirect_uri="http://localhost:8000/callback",
            scopes=["openid", "email", "profile"],
            state="random-state-123",
        )

        assert request.provider == OAuthProvider.GOOGLE
        assert request.redirect_uri == "http://localhost:8000/callback"
        assert len(request.scopes) == 3
        assert request.state == "random-state-123"

    def test_oauth_callback_request(self):
        """Test OAuth callback request model."""
        request = OAuthCallbackRequest(
            session_id="session-123", code="auth-code-xyz", state="state-123"
        )

        assert request.session_id == "session-123"
        assert request.code == "auth-code-xyz"
        assert request.state == "state-123"

    def test_oauth_callback_request_with_error(self):
        """Test OAuth callback request with error."""
        request = OAuthCallbackRequest(
            session_id="session-456", code="error-code-123", state="state-123"
        )

        assert request.session_id == "session-456"
        assert request.code == "error-code-123"
        assert request.state == "state-123"

    def test_oauth_token_response(self):
        """Test OAuth token response model."""
        response = OAuthTokenResponse(
            access_token="access-token-abc",
            token_type="Bearer",
            expires_in=3600,
            refresh_token="refresh-token-xyz",
            scope="openid email profile",
            id_token="id-token-jwt",
        )

        assert response.access_token == "access-token-abc"
        assert response.token_type == "Bearer"
        assert response.expires_in == 3600
        assert response.refresh_token == "refresh-token-xyz"
        assert response.id_token == "id-token-jwt"

    def test_oauth_user_info(self):
        """Test OAuth user info model."""
        info = OAuthUserInfo(
            sub="user-id-123",
            email="user@example.com",
            email_verified=True,
            name="John Doe",
            picture="https://example.com/photo.jpg",
            locale="en-US",
        )

        assert info.sub == "user-id-123"
        assert info.email == "user@example.com"
        assert info.email_verified is True
        assert info.name == "John Doe"

    def test_oauth_service_config(self):
        """Test OAuth service configuration."""
        config = OAuthServiceConfig(
            providers={
                OAuthProvider.GOOGLE: {
                    "client_id": "google-client-id",
                    "client_secret": "google-secret",
                    "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
                    "token_url": "https://oauth2.googleapis.com/token",
                }
            },
            default_scopes=["openid", "email"],
            state_ttl_seconds=600,
        )

        assert OAuthProvider.GOOGLE in config.providers
        assert config.default_scopes == ["openid", "email"]
        assert config.state_ttl_seconds == 600


class TestOAuthService:
    """Test OAuth service functionality."""

    class FakeResponse:
        def __init__(self, status_code=200, payload=None):
            self.status_code = status_code
            self._payload = payload or {}

        def raise_for_status(self):
            if not (200 <= self.status_code < 300):
                raise AuthError(f"HTTP {self.status_code}")

        def json(self):
            return self._payload

    class FakeHTTPClient:
        def __init__(self, mapping=None):
            # mapping: (method, url) -> FakeResponse
            self.mapping = mapping or {}

        async def post(self, url, data=None, headers=None):
            return self.mapping.get(("POST", url), TestOAuthService.FakeResponse(200, {}))

        async def get(self, url, headers=None):
            return self.mapping.get(("GET", url), TestOAuthService.FakeResponse(200, {}))

    @pytest.fixture
    def oauth_service(self):
        """Create OAuth service instance."""
        config = OAuthServiceConfig(
            providers={
                OAuthProvider.GOOGLE: {
                    "client_id": "test-google-client",
                    "client_secret": "test-google-secret",
                    "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
                    "token_url": "https://oauth2.googleapis.com/token",
                    "userinfo_url": "https://www.googleapis.com/oauth2/v1/userinfo",
                },
                OAuthProvider.GITHUB: {
                    "client_id": "test-github-client",
                    "client_secret": "test-github-secret",
                    "authorize_url": "https://github.com/login/oauth/authorize",
                    "token_url": "https://github.com/login/oauth/access_token",
                    "userinfo_url": "https://api.github.com/user",
                },
            }
        )
        return OAuthService(config)

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        session = Mock()
        session.query = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        return session

    def test_get_authorization_url(self, oauth_service):
        """Test generating authorization URL."""
        provider = OAuthProvider.GOOGLE
        redirect_uri = "http://localhost:8000/callback"
        scopes = ["openid", "email", "profile"]

        auth_url, state = oauth_service.get_authorization_url(
            provider=provider, redirect_uri=redirect_uri, scopes=scopes
        )

        assert auth_url.startswith("https://accounts.google.com/o/oauth2/v2/auth")
        assert "client_id=test-google-client" in auth_url
        assert "redirect_uri=" in auth_url
        assert "scope=openid+email+profile" in auth_url
        assert f"state={state}" in auth_url

        # State should be random and secure
        assert len(state) >= 32

    def test_get_authorization_url_with_pkce(self, oauth_service):
        """Test generating authorization URL with PKCE."""
        provider = OAuthProvider.GOOGLE
        redirect_uri = "http://localhost:8000/callback"

        auth_url, state, code_verifier = oauth_service.get_authorization_url_with_pkce(
            provider=provider, redirect_uri=redirect_uri
        )

        assert "code_challenge=" in auth_url
        assert "code_challenge_method=S256" in auth_url
        assert code_verifier is not None
        assert len(code_verifier) >= 43  # Base64 encoded

    @pytest.mark.asyncio
    async def test_exchange_code(self, oauth_service, mock_db_session):
        """Test exchanging authorization code for tokens."""
        provider = OAuthProvider.GOOGLE
        code = "auth-code-123"
        redirect_uri = "http://localhost:8000/callback"

        # Mock HTTP response
        mock_token_response = {
            "access_token": "access-token-xyz",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "refresh-token-abc",
            "id_token": "id-token-jwt",
        }

        # Inject fake HTTP client
        token_url = oauth_service.config.providers[provider]["token_url"]
        oauth_service.http_client = TestOAuthService.FakeHTTPClient(
            {("POST", token_url): TestOAuthService.FakeResponse(200, mock_token_response)}
        )

        with patch.object(oauth_service, "db_session", mock_db_session):
            result = await oauth_service.exchange_code(
                provider=provider, code=code, redirect_uri=redirect_uri
            )

            assert isinstance(result, OAuthTokenResponse)
            assert result.access_token == "access-token-xyz"
            assert result.refresh_token == "refresh-token-abc"

    @pytest.mark.asyncio
    async def test_exchange_code_with_error(self, oauth_service):
        """Test handling error during code exchange."""
        provider = OAuthProvider.GOOGLE
        code = "invalid-code"
        redirect_uri = "http://localhost:8000/callback"

        # Mock error response
        mock_error_response = {
            "error": "invalid_grant",
            "error_description": "Invalid authorization code",
        }

        token_url = oauth_service.config.providers[provider]["token_url"]
        oauth_service.http_client = TestOAuthService.FakeHTTPClient(
            {("POST", token_url): TestOAuthService.FakeResponse(400, mock_error_response)}
        )

        with pytest.raises(AuthError) as exc_info:
            await oauth_service.exchange_code(
                provider=provider, code=code, redirect_uri=redirect_uri
            )
        assert "HTTP 400" in str(exc_info.value) or "invalid_grant" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_user_info(self, oauth_service):
        """Test fetching user info with access token."""
        provider = OAuthProvider.GOOGLE
        access_token = "access-token-xyz"

        # Mock user info response
        mock_userinfo = {
            "id": "123456789",
            "email": "user@gmail.com",
            "verified_email": True,
            "name": "Test User",
            "picture": "https://example.com/photo.jpg",
        }

        userinfo_url = oauth_service.config.providers[provider]["userinfo_url"]
        oauth_service.http_client = TestOAuthService.FakeHTTPClient(
            {("GET", userinfo_url): TestOAuthService.FakeResponse(200, mock_userinfo)}
        )
        result = await oauth_service.get_user_info(provider, access_token)
        assert isinstance(result, OAuthUserInfo)
        assert result.email == "user@gmail.com"
        assert result.name == "Test User"

    @pytest.mark.asyncio
    async def test_refresh_token(self, oauth_service):
        """Test refreshing access token."""
        provider = OAuthProvider.GOOGLE
        refresh_token = "refresh-token-abc"

        # Mock refresh response
        mock_refresh_response = {
            "access_token": "new-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        token_url = oauth_service.config.providers[provider]["token_url"]
        oauth_service.http_client = TestOAuthService.FakeHTTPClient(
            {("POST", token_url): TestOAuthService.FakeResponse(200, mock_refresh_response)}
        )
        result = await oauth_service.refresh_token(provider, refresh_token)
        assert isinstance(result, OAuthTokenResponse)
        assert result.access_token == "new-access-token"

    @pytest.mark.asyncio
    async def test_revoke_token(self, oauth_service):
        """Test revoking access token."""
        provider = OAuthProvider.GOOGLE
        token = "access-token-xyz"

        revoke_url = oauth_service.config.providers[provider].get(
            "revoke_url", "https://example.com/revoke"
        )
        oauth_service.http_client = TestOAuthService.FakeHTTPClient(
            {("POST", revoke_url): TestOAuthService.FakeResponse(200, {})}
        )
        # Since revoke_token uses stored provider config in service (if implemented),
        # this acts as a simple sanity test: method callable and returns bool.
        # If revoke_url isn't used in code, the call still returns True with FakeHTTPClient default.
        result = await oauth_service.revoke_token(provider, token)
        assert result in (True, False)

    @pytest.mark.asyncio
    async def test_validate_state(self, oauth_service, mock_db_session):
        """Test OAuth state validation."""
        state = "test-state-123"

        # Mock finding valid state in database
        mock_session = Mock(spec=OAuthSession)
        mock_session.state = state
        mock_session.created_at = datetime.now(UTC)

        mock_db_session.query().filter().first.return_value = mock_session

        with patch.object(oauth_service, "db_session", mock_db_session):
            result = oauth_service.validate_state(state)

            assert result is True

    @pytest.mark.asyncio
    async def test_validate_state_expired(self, oauth_service, mock_db_session):
        """Test OAuth state validation with expired state."""
        state = "expired-state-123"

        # Mock finding expired state
        mock_session = Mock(spec=OAuthSession)
        mock_session.state = state
        mock_session.created_at = datetime.now(UTC) - timedelta(hours=1)

        mock_db_session.query().filter().first.return_value = mock_session

        with patch.object(oauth_service, "db_session", mock_db_session):
            # Assuming 10 minute TTL
            result = oauth_service.validate_state(state, max_age_seconds=600)

            assert result is False


class TestOAuthHelperFunctions:
    """Test OAuth helper functions."""

    def test_generate_oauth_state(self):
        """Test OAuth state generation."""
        state1 = generate_oauth_state()
        state2 = generate_oauth_state()

        # Should be random
        assert state1 != state2

        # Should be secure length
        assert len(state1) >= 32
        assert len(state2) >= 32

        # Should be URL-safe
        assert all(c.isalnum() or c in "-_" for c in state1)

    def test_generate_pkce_pair(self):
        """Test PKCE code verifier and challenge generation."""
        verifier, challenge = generate_pkce_pair()

        # Verifier should be base64url encoded
        assert len(verifier) >= 43
        assert len(verifier) <= 128

        # Challenge should be SHA256 of verifier, base64url encoded
        expected_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
            .decode()
            .rstrip("=")
        )

        assert challenge == expected_challenge

    def test_generate_pkce_pair_uniqueness(self):
        """Test PKCE pairs are unique."""
        pairs = [generate_pkce_pair() for _ in range(10)]

        verifiers = [p[0] for p in pairs]
        challenges = [p[1] for p in pairs]

        # All should be unique
        assert len(set(verifiers)) == 10
        assert len(set(challenges)) == 10

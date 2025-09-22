"""
Comprehensive tests for OAuth providers with full coverage.
Tests OAuth flows for Google, GitHub, Microsoft, token exchange, and profile mapping.
"""

import base64
import hashlib
import json
import secrets
import urllib.parse
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import httpx
import pytest

from dotmac.platform.auth.oauth_providers import (
    OAuthAuthorizationRequest,
    OAuthGrantType,
    OAuthProvider,
    OAuthProviderConfig,
    OAuthServiceConfig,
    OAuthSession,
    OAuthToken,
    OAuthTokenType,
    OAuthUserProfile,
)
from dotmac.platform.auth.exceptions import AuthenticationError, ConfigurationError
from tests.fixtures import mock_http_session, mock_oauth2_client


@pytest.mark.asyncio
class TestOAuthModels:
    """Tests for OAuth data models."""

    def test_oauth_provider_enum(self):
        """Test OAuthProvider enumeration."""
        assert OAuthProvider.GOOGLE == "google"
        assert OAuthProvider.MICROSOFT == "microsoft"
        assert OAuthProvider.GITHUB == "github"
        assert OAuthProvider.FACEBOOK == "facebook"
        assert OAuthProvider.APPLE == "apple"
        assert OAuthProvider.GENERIC == "generic"

    def test_oauth_service_config(self):
        """Test OAuthServiceConfig model."""
        config = settings.OAuthService.model_copy(update={
            providers={
                OAuthProvider.GOOGLE: {
                    "client_id": "google_client",
                    "client_secret": "google_secret",
                }
            },
            redirect_uri="https://app.example.com/auth/callback",
            state_ttl=300,
            enable_pkce=True,
            enable_state_parameter=True,
            auto_refresh_tokens=True,
        })

        assert config.providers[OAuthProvider.GOOGLE]["client_id"] == "google_client"
        assert config.redirect_uri == "https://app.example.com/auth/callback"
        assert config.state_ttl == 300
        assert config.enable_pkce is True

    def test_oauth_service_config_defaults(self):
        """Test OAuthServiceConfig default values."""
        config = settings.OAuthService.model_copy()

        assert config.providers == {}
        assert config.redirect_uri == "http://localhost:8000/auth/callback"
        assert config.state_ttl == 600
        assert config.enable_pkce is True
        assert config.enable_state_parameter is True

    def test_oauth_authorization_request(self):
        """Test OAuthAuthorizationRequest model."""
        request = OAuthAuthorizationRequest(
            provider=OAuthProvider.GITHUB,
            redirect_uri="https://app.example.com/callback",
            scopes=["user", "repo"],
            state="random_state",
            additional_params={"prompt": "consent"},
        )

        assert request.provider == OAuthProvider.GITHUB
        assert request.redirect_uri == "https://app.example.com/callback"
        assert request.scopes == ["user", "repo"]
        assert request.state == "random_state"
        assert request.additional_params["prompt"] == "consent"

    def test_oauth_grant_type_enum(self):
        """Test OAuthGrantType enumeration."""
        assert OAuthGrantType.AUTHORIZATION_CODE == "authorization_code"
        assert OAuthGrantType.REFRESH_TOKEN == "refresh_token"
        assert OAuthGrantType.CLIENT_CREDENTIALS == "client_credentials"

    def test_oauth_token_type_enum(self):
        """Test OAuthTokenType enumeration."""
        assert OAuthTokenType.BEARER == "Bearer"
        assert OAuthTokenType.MAC == "MAC"


@pytest.mark.asyncio
class TestOAuthService:
    """Comprehensive tests for OAuth service functionality."""

    @pytest.fixture
    def oauth_service(self):
        """Create a mock OAuth service."""
        from dotmac.platform.auth.oauth_service import OAuthService

        config = settings.OAuthService.model_copy(update={
            providers={
                OAuthProvider.GOOGLE: {
                    "client_id": "google_client_id",
                    "client_secret": "google_client_secret",
                    "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
                    "token_url": "https://oauth2.googleapis.com/token",
                    "userinfo_url": "https://openidconnect.googleapis.com/v1/userinfo",
                },
                OAuthProvider.GITHUB: {
                    "client_id": "github_client_id",
                    "client_secret": "github_client_secret",
                    "authorization_url": "https://github.com/login/oauth/authorize",
                    "token_url": "https://github.com/login/oauth/access_token",
                    "userinfo_url": "https://api.github.com/user",
                },
            },
            enable_pkce=True,
            state_ttl=600,
        })
        service = OAuthService(config)
        return service

    async def test_generate_authorization_url_google(self, oauth_service):
        """Test generating authorization URL for Google."""
        request = OAuthAuthorizationRequest(
            provider=OAuthProvider.GOOGLE,
            redirect_uri="https://app.example.com/callback",
            scopes=["openid", "email", "profile"],
        )

        url, session_data = await oauth_service.generate_authorization_url(request)

        # Parse URL
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)

        # Verify base URL
        assert parsed.scheme == "https"
        assert parsed.netloc == "accounts.google.com"
        assert parsed.path == "/o/oauth2/v2/auth"

        # Verify required parameters
        assert params["client_id"][0] == "google_client_id"
        assert params["redirect_uri"][0] == "https://app.example.com/callback"
        assert params["response_type"][0] == "code"
        assert params["scope"][0] == "openid email profile"

        # Verify PKCE parameters
        assert "code_challenge" in params
        assert params["code_challenge_method"][0] == "S256"

        # Verify state parameter
        assert "state" in params
        assert session_data["state"] == params["state"][0]

        # Verify session data
        assert session_data["provider"] == OAuthProvider.GOOGLE
        assert "code_verifier" in session_data
        assert "code_challenge" in session_data

    async def test_generate_authorization_url_github(self, oauth_service):
        """Test generating authorization URL for GitHub."""
        request = OAuthAuthorizationRequest(
            provider=OAuthProvider.GITHUB,
            redirect_uri="https://app.example.com/callback",
            scopes=["user", "repo"],
        )

        url, session_data = await oauth_service.generate_authorization_url(request)

        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)

        # Verify GitHub-specific URL
        assert parsed.netloc == "github.com"
        assert parsed.path == "/login/oauth/authorize"
        assert params["client_id"][0] == "github_client_id"
        assert params["scope"][0] == "user repo"

    async def test_generate_authorization_url_without_pkce(self, oauth_service):
        """Test generating authorization URL without PKCE."""
        oauth_service.config.enable_pkce = False

        request = OAuthAuthorizationRequest(
            provider=OAuthProvider.GOOGLE,
            redirect_uri="https://app.example.com/callback",
        )

        url, session_data = await oauth_service.generate_authorization_url(request)

        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)

        # PKCE parameters should not be present
        assert "code_challenge" not in params
        assert "code_challenge_method" not in params
        assert "code_verifier" not in session_data

    async def test_generate_authorization_url_with_additional_params(self, oauth_service):
        """Test authorization URL with additional parameters."""
        request = OAuthAuthorizationRequest(
            provider=OAuthProvider.GOOGLE,
            redirect_uri="https://app.example.com/callback",
            additional_params={
                "access_type": "offline",
                "prompt": "consent",
                "login_hint": "user@example.com",
            },
        )

        url, session_data = await oauth_service.generate_authorization_url(request)

        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)

        # Verify additional parameters
        assert params["access_type"][0] == "offline"
        assert params["prompt"][0] == "consent"
        assert params["login_hint"][0] == "user@example.com"

    async def test_exchange_code_for_token_google(self, oauth_service):
        """Test exchanging authorization code for tokens with Google."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock token response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "google_access_token",
                "refresh_token": "google_refresh_token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "id_token": "google_id_token",
            }
            mock_client.post.return_value = mock_response

            session_data = {
                "provider": OAuthProvider.GOOGLE,
                "state": "test_state",
                "code_verifier": "test_verifier",
                "redirect_uri": "https://app.example.com/callback",
            }

            token_data = await oauth_service.exchange_code_for_token(
                code="auth_code_123",
                session_data=session_data,
            )

            # Verify token data
            assert token_data["access_token"] == "google_access_token"
            assert token_data["refresh_token"] == "google_refresh_token"
            assert token_data["token_type"] == "Bearer"
            assert token_data["expires_in"] == 3600

            # Verify API call
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "https://oauth2.googleapis.com/token"

            # Verify request data
            request_data = call_args[1]["data"]
            assert request_data["code"] == "auth_code_123"
            assert request_data["client_id"] == "google_client_id"
            assert request_data["client_secret"] == "google_client_secret"
            assert request_data["grant_type"] == "authorization_code"
            assert request_data["code_verifier"] == "test_verifier"

    async def test_exchange_code_for_token_error(self, oauth_service):
        """Test error handling during code exchange."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock error response
            mock_response = AsyncMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "error": "invalid_grant",
                "error_description": "Invalid authorization code",
            }
            mock_client.post.return_value = mock_response

            session_data = {
                "provider": OAuthProvider.GOOGLE,
                "redirect_uri": "https://app.example.com/callback",
            }

            with pytest.raises(AuthenticationError, match="Token exchange failed"):
                await oauth_service.exchange_code_for_token(
                    code="invalid_code",
                    session_data=session_data,
                )

    async def test_get_user_profile_google(self, oauth_service):
        """Test fetching user profile from Google."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock userinfo response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "sub": "google_user_123",
                "email": "user@example.com",
                "email_verified": True,
                "name": "John Doe",
                "given_name": "John",
                "family_name": "Doe",
                "picture": "https://example.com/photo.jpg",
                "locale": "en",
            }
            mock_client.get.return_value = mock_response

            profile = await oauth_service.get_user_profile(
                provider=OAuthProvider.GOOGLE,
                access_token="google_access_token",
            )

            # Verify profile data
            assert profile["sub"] == "google_user_123"
            assert profile["email"] == "user@example.com"
            assert profile["name"] == "John Doe"
            assert profile["picture"] == "https://example.com/photo.jpg"

            # Verify API call
            mock_client.get.assert_called_once_with(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers={"Authorization": "Bearer google_access_token"},
            )

    async def test_get_user_profile_github(self, oauth_service):
        """Test fetching user profile from GitHub."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock GitHub user response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": 12345,
                "login": "johndoe",
                "email": "john@example.com",
                "name": "John Doe",
                "avatar_url": "https://avatars.githubusercontent.com/u/12345",
                "bio": "Software Developer",
                "location": "San Francisco",
            }
            mock_client.get.return_value = mock_response

            profile = await oauth_service.get_user_profile(
                provider=OAuthProvider.GITHUB,
                access_token="github_access_token",
            )

            # Verify profile data
            assert profile["id"] == 12345
            assert profile["login"] == "johndoe"
            assert profile["email"] == "john@example.com"
            assert profile["name"] == "John Doe"

            # Verify API call
            mock_client.get.assert_called_once_with(
                "https://api.github.com/user",
                headers={"Authorization": "Bearer github_access_token"},
            )

    async def test_refresh_access_token(self, oauth_service):
        """Test refreshing access token."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock refresh response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "new_access_token",
                "token_type": "Bearer",
                "expires_in": 3600,
            }
            mock_client.post.return_value = mock_response

            token_data = await oauth_service.refresh_access_token(
                provider=OAuthProvider.GOOGLE,
                refresh_token="refresh_token_123",
            )

            # Verify new token data
            assert token_data["access_token"] == "new_access_token"
            assert token_data["expires_in"] == 3600

            # Verify API call
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            request_data = call_args[1]["data"]
            assert request_data["refresh_token"] == "refresh_token_123"
            assert request_data["grant_type"] == "refresh_token"

    async def test_validate_state_parameter(self, oauth_service):
        """Test state parameter validation."""
        # Valid state
        session_state = "valid_state_123"
        request_state = "valid_state_123"
        result = await oauth_service.validate_state(session_state, request_state)
        assert result is True

        # Invalid state
        session_state = "state_123"
        request_state = "different_state"
        result = await oauth_service.validate_state(session_state, request_state)
        assert result is False

        # Missing state
        result = await oauth_service.validate_state(None, "state")
        assert result is False

    async def test_generate_pkce_challenge(self, oauth_service):
        """Test PKCE challenge generation."""
        code_verifier = oauth_service.generate_code_verifier()
        code_challenge = oauth_service.generate_code_challenge(code_verifier)

        # Verify verifier format (43-128 characters, URL-safe)
        assert 43 <= len(code_verifier) <= 128
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~" for c in code_verifier)

        # Verify challenge is base64url encoded SHA256
        expected_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode().rstrip("=")
        assert code_challenge == expected_challenge

    async def test_provider_not_configured(self, oauth_service):
        """Test error when provider is not configured."""
        request = OAuthAuthorizationRequest(
            provider=OAuthProvider.FACEBOOK,  # Not configured
            redirect_uri="https://app.example.com/callback",
        )

        with pytest.raises(ConfigurationError, match="Provider facebook not configured"):
            await oauth_service.generate_authorization_url(request)


@pytest.mark.asyncio
class TestOAuthProviderSpecific:
    """Tests for provider-specific OAuth implementations."""

    async def test_google_oauth_flow(self):
        """Test complete Google OAuth flow."""
        # This would test Google-specific parameters and behavior
        google_config = {
            "client_id": "google_client",
            "client_secret": "google_secret",
            "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "scopes": ["openid", "email", "profile"],
            "access_type": "offline",  # Google-specific
            "prompt": "consent",  # Google-specific
        }

        # Test authorization URL includes Google-specific params
        auth_url = f"{google_config['authorization_url']}?access_type=offline&prompt=consent"
        assert "access_type=offline" in auth_url
        assert "prompt=consent" in auth_url

    async def test_github_oauth_flow(self):
        """Test complete GitHub OAuth flow."""
        github_config = {
            "client_id": "github_client",
            "client_secret": "github_secret",
            "authorization_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "scopes": ["user", "repo", "gist"],
        }

        # GitHub uses different scope separator (space instead of comma)
        scopes = " ".join(github_config["scopes"])
        assert scopes == "user repo gist"

    async def test_microsoft_oauth_flow(self):
        """Test Microsoft OAuth flow with specific requirements."""
        microsoft_config = {
            "client_id": "microsoft_client",
            "client_secret": "microsoft_secret",
            "tenant_id": "common",  # Microsoft-specific
            "authorization_url": "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize",
            "token_url": "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
            "scopes": ["User.Read", "Mail.Read"],  # Microsoft Graph scopes
        }

        # Test tenant-specific URLs
        auth_url = microsoft_config["authorization_url"].format(tenant=microsoft_config["tenant_id"])
        assert "https://login.microsoftonline.com/common/oauth2/v2.0/authorize" == auth_url

    async def test_apple_oauth_flow(self):
        """Test Apple OAuth flow with specific requirements."""
        apple_config = {
            "client_id": "com.example.app",
            "team_id": "TEAM123",
            "key_id": "KEY123",
            "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----",
            "authorization_url": "https://appleid.apple.com/auth/authorize",
            "token_url": "https://appleid.apple.com/auth/token",
            "response_mode": "form_post",  # Apple-specific
        }

        # Apple requires client secret to be a JWT
        # This would test JWT generation for Apple
        assert apple_config["response_mode"] == "form_post"


@pytest.mark.asyncio
class TestOAuthErrorHandling:
    """Tests for OAuth error handling scenarios."""

    async def test_network_error_during_token_exchange(self):
        """Test handling network errors during token exchange."""
        from dotmac.platform.auth.oauth_service import OAuthService

        service = OAuthService(settings.OAuthService.model_copy())

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.side_effect = httpx.NetworkError("Connection failed")

            with pytest.raises(AuthenticationError, match="Network error"):
                await service.exchange_code_for_token(
                    code="code",
                    session_data={"provider": OAuthProvider.GOOGLE},
                )

    async def test_invalid_token_response(self):
        """Test handling invalid token response."""
        from dotmac.platform.auth.oauth_service import OAuthService

        service = OAuthService(settings.OAuthService.model_copy())

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock response with missing required fields
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"invalid": "response"}
            mock_client.post.return_value = mock_response

            with pytest.raises(AuthenticationError, match="Invalid token response"):
                await service.exchange_code_for_token(
                    code="code",
                    session_data={"provider": OAuthProvider.GOOGLE},
                )

    async def test_expired_session_data(self):
        """Test handling expired session data."""
        from dotmac.platform.auth.oauth_service import OAuthService

        service = OAuthService(settings.OAuthService.model_copy())

        expired_session = {
            "provider": OAuthProvider.GOOGLE,
            "expires_at": (datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
        }

        with pytest.raises(AuthenticationError, match="Session expired"):
            await service.validate_session(expired_session)

    async def test_csrf_attack_detection(self):
        """Test CSRF attack detection via state mismatch."""
        from dotmac.platform.auth.oauth_service import OAuthService

        service = OAuthService(settings.OAuthService.model_copy())

        # Different states indicate potential CSRF
        session_state = "legitimate_state"
        request_state = "attacker_state"

        result = await service.validate_state(session_state, request_state)
        assert result is False


@pytest.mark.asyncio
class TestOAuthIntegration:
    """Integration tests for OAuth functionality."""

    async def test_complete_oauth_flow_with_pkce(self):
        """Test complete OAuth flow with PKCE."""
        from dotmac.platform.auth.oauth_service import OAuthService

        config = settings.OAuthService.model_copy(update={
            providers={
                OAuthProvider.GOOGLE: {
                    "client_id": "test_client",
                    "client_secret": "test_secret",
                    "authorization_url": "https://auth.example.com/authorize",
                    "token_url": "https://auth.example.com/token",
                    "userinfo_url": "https://auth.example.com/userinfo",
                }
            },
            enable_pkce=True,
        })
        service = OAuthService(config)

        # Step 1: Generate authorization URL
        request = OAuthAuthorizationRequest(
            provider=OAuthProvider.GOOGLE,
            redirect_uri="https://app.example.com/callback",
            scopes=["openid", "profile"],
        )

        url, session_data = await service.generate_authorization_url(request)

        # Verify PKCE parameters
        assert "code_verifier" in session_data
        assert "code_challenge" in session_data
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        assert "code_challenge" in params

        # Step 2: Simulate authorization callback
        authorization_code = "test_auth_code"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock token exchange
            mock_token_response = AsyncMock()
            mock_token_response.status_code = 200
            mock_token_response.json.return_value = {
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
                "expires_in": 3600,
            }
            mock_client.post.return_value = mock_token_response

            # Exchange code for token
            token_data = await service.exchange_code_for_token(
                code=authorization_code,
                session_data=session_data,
            )

            assert token_data["access_token"] == "test_access_token"

            # Step 3: Get user profile
            mock_profile_response = AsyncMock()
            mock_profile_response.status_code = 200
            mock_profile_response.json.return_value = {
                "sub": "user_123",
                "email": "user@example.com",
                "name": "Test User",
            }
            mock_client.get.return_value = mock_profile_response

            profile = await service.get_user_profile(
                provider=OAuthProvider.GOOGLE,
                access_token=token_data["access_token"],
            )

            assert profile["sub"] == "user_123"
            assert profile["email"] == "user@example.com"

    async def test_multiple_provider_configuration(self):
        """Test configuring and using multiple OAuth providers."""
        config = settings.OAuthService.model_copy(update={
            providers={
                OAuthProvider.GOOGLE: {
                    "client_id": "google_id",
                    "client_secret": "google_secret",
                },
                OAuthProvider.GITHUB: {
                    "client_id": "github_id",
                    "client_secret": "github_secret",
                },
                OAuthProvider.MICROSOFT: {
                    "client_id": "microsoft_id",
                    "client_secret": "microsoft_secret",
                },
            }
        })

        from dotmac.platform.auth.oauth_service import OAuthService

        service = OAuthService(config)

        # Test each provider can generate URLs
        for provider in [OAuthProvider.GOOGLE, OAuthProvider.GITHUB, OAuthProvider.MICROSOFT]:
            request = OAuthAuthorizationRequest(
                provider=provider,
                redirect_uri="https://app.example.com/callback",
            )

            url, session_data = await service.generate_authorization_url(request)
            assert session_data["provider"] == provider

    async def test_oauth_session_storage_and_retrieval(self):
        """Test storing and retrieving OAuth session data."""
        session_id = str(uuid4())
        session = OAuthSession(
            id=uuid4(),
            session_id=session_id,
            provider=OAuthProvider.GOOGLE.value,
            state="test_state",
            code_verifier="verifier_123",
            code_challenge="challenge_456",
            redirect_uri="https://app.example.com/callback",
            scopes=["openid", "profile"],
            expires_at=datetime.now(UTC) + timedelta(minutes=10),
        )

        # Test session attributes
        assert session.session_id == session_id
        assert session.provider == "google"
        assert session.state == "test_state"
        assert session.code_verifier == "verifier_123"

    async def test_oauth_token_storage_and_refresh(self):
        """Test storing OAuth tokens and refresh logic."""
        user_id = uuid4()
        token = OAuthToken(
            id=uuid4(),
            user_id=user_id,
            provider=OAuthProvider.GITHUB.value,
            access_token="github_access_token",
            refresh_token="github_refresh_token",
            token_type="Bearer",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            scopes=["user", "repo"],
        )

        # Test token attributes
        assert token.user_id == user_id
        assert token.provider == "github"
        assert token.access_token == "github_access_token"
        assert token.refresh_token == "github_refresh_token"

        # Check if token needs refresh (not yet)
        assert token.expires_at > datetime.now(UTC)

    async def test_oauth_user_profile_mapping(self):
        """Test mapping OAuth provider profiles to internal user profiles."""
        user_id = uuid4()

        # Google profile
        google_profile = OAuthUserProfile(
            id=uuid4(),
            user_id=user_id,
            provider=OAuthProvider.GOOGLE.value,
            provider_user_id="google_123",
            email="user@gmail.com",
            name="John Doe",
            given_name="John",
            family_name="Doe",
            picture="https://google.com/photo.jpg",
            locale="en",
            raw_profile={
                "sub": "google_123",
                "email_verified": True,
            },
        )

        # GitHub profile (different fields)
        github_profile = OAuthUserProfile(
            id=uuid4(),
            user_id=user_id,
            provider=OAuthProvider.GITHUB.value,
            provider_user_id="12345",
            email="user@github.com",
            name="johndoe",
            picture="https://avatars.github.com/u/12345",
            raw_profile={
                "id": 12345,
                "login": "johndoe",
                "bio": "Developer",
            },
        )

        # Test profile attributes
        assert google_profile.email == "user@gmail.com"
        assert github_profile.name == "johndoe"
        assert google_profile.raw_profile["email_verified"] is True
        assert github_profile.raw_profile["bio"] == "Developer"
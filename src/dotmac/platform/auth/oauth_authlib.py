"""
Modern OAuth implementation using Authlib.

Replaces the custom OAuth implementation with the industry-standard Authlib library.
Provides cleaner, more maintainable OAuth 2.0 and OpenID Connect support.
"""

from typing import Any, Dict, Optional, List
from enum import Enum
from datetime import datetime, UTC, timedelta
import secrets

from authlib.integrations.httpx_client import OAuth2Session
from authlib.integrations.base_client import OAuthError
from authlib.oauth2 import OAuth2Token
from authlib.oidc.core import UserInfo
from pydantic import BaseModel, HttpUrl
import httpx

from .exceptions import AuthenticationError, ConfigurationError


class OAuthProvider(str, Enum):
    """Supported OAuth providers."""
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    GITHUB = "github"
    FACEBOOK = "facebook"
    APPLE = "apple"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    DISCORD = "discord"
    SLACK = "slack"


class OAuthConfig(BaseModel):
    """OAuth provider configuration using Authlib patterns."""
    client_id: str
    client_secret: str
    authorize_url: str
    token_url: str
    userinfo_url: Optional[str] = None
    scopes: List[str] = []
    additional_params: Dict[str, Any] = {}


class OAuthRequest(BaseModel):
    """OAuth authorization request."""
    provider: OAuthProvider
    redirect_uri: str
    scopes: Optional[List[str]] = None
    state: Optional[str] = None


class OAuthUserInfo(BaseModel):
    """Standardized OAuth user information."""
    provider: str
    provider_user_id: str
    email: Optional[str] = None
    email_verified: Optional[bool] = None
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None
    locale: Optional[str] = None
    raw_profile: Dict[str, Any] = {}


# Provider configurations using well-known endpoints
PROVIDER_CONFIGS = {
    OAuthProvider.GOOGLE: OAuthConfig(
        client_id="",  # Set from environment/config
        client_secret="",
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        userinfo_url="https://www.googleapis.com/oauth2/v2/userinfo",
        scopes=["openid", "email", "profile"],
    ),
    OAuthProvider.MICROSOFT: OAuthConfig(
        client_id="",
        client_secret="",
        authorize_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
        userinfo_url="https://graph.microsoft.com/v1.0/me",
        scopes=["openid", "email", "profile"],
    ),
    OAuthProvider.GITHUB: OAuthConfig(
        client_id="",
        client_secret="",
        authorize_url="https://github.com/login/oauth/authorize",
        token_url="https://github.com/login/oauth/access_token",
        userinfo_url="https://api.github.com/user",
        scopes=["user:email"],
    ),
    OAuthProvider.FACEBOOK: OAuthConfig(
        client_id="",
        client_secret="",
        authorize_url="https://www.facebook.com/v18.0/dialog/oauth",
        token_url="https://graph.facebook.com/v18.0/oauth/access_token",
        userinfo_url="https://graph.facebook.com/v18.0/me",
        scopes=["email", "public_profile"],
        additional_params={"fields": "id,name,email,first_name,last_name,picture"},
    ),
}


class AuthlibOAuthService:
    """
    Modern OAuth service using Authlib.

    Replaces the complex custom implementation with Authlib's battle-tested OAuth client.
    """

    def __init__(
        self,
        providers: Dict[OAuthProvider, OAuthConfig],
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        """Initialize OAuth service with provider configurations."""
        self.providers = providers
        self.http_client = http_client or httpx.AsyncClient()
        self._sessions: Dict[str, OAuth2Session] = {}

    def _get_provider_config(self, provider: OAuthProvider) -> OAuthConfig:
        """Get provider configuration."""
        if provider not in self.providers:
            raise ConfigurationError(f"Provider {provider} not configured")
        return self.providers[provider]

    def _create_oauth_session(self, provider: OAuthProvider, redirect_uri: str) -> OAuth2Session:
        """Create OAuth2Session using Authlib."""
        config = self._get_provider_config(provider)

        return OAuth2Session(
            client_id=config.client_id,
            client_secret=config.client_secret,
            redirect_uri=redirect_uri,
            scope=config.scopes,
        )

    def get_authorization_url(
        self,
        provider: OAuthProvider,
        redirect_uri: str,
        scopes: Optional[List[str]] = None,
        state: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        Generate authorization URL using Authlib.

        Returns:
            Tuple of (authorization_url, state)
        """
        config = self._get_provider_config(provider)
        session = self._create_oauth_session(provider, redirect_uri)

        # Override scopes if provided
        if scopes:
            session.scope = scopes

        # Generate state if not provided
        if not state:
            state = secrets.token_urlsafe(32)

        # Generate authorization URL with Authlib
        authorization_url = session.create_authorization_url(
            config.authorize_url,
            state=state,
            **config.additional_params
        )

        # Store session for later token exchange
        self._sessions[state] = session

        return authorization_url, state

    def get_authorization_url_with_pkce(
        self,
        provider: OAuthProvider,
        redirect_uri: str,
        scopes: Optional[List[str]] = None,
    ) -> tuple[str, str, str]:
        """
        Generate authorization URL with PKCE using Authlib.

        Returns:
            Tuple of (authorization_url, state, code_verifier)
        """
        config = self._get_provider_config(provider)
        session = self._create_oauth_session(provider, redirect_uri)

        if scopes:
            session.scope = scopes

        state = secrets.token_urlsafe(32)

        # Authlib handles PKCE automatically when supported
        authorization_url, code_verifier = session.create_authorization_url(
            config.authorize_url,
            state=state,
            code_challenge_method='S256',  # Enable PKCE
            **config.additional_params
        )

        self._sessions[state] = session

        return authorization_url, state, code_verifier

    async def exchange_code(
        self,
        provider: OAuthProvider,
        code: str,
        redirect_uri: str,
        state: Optional[str] = None,
        code_verifier: Optional[str] = None,
    ) -> OAuth2Token:
        """
        Exchange authorization code for tokens using Authlib.
        """
        config = self._get_provider_config(provider)

        # Get session if we have state
        session = self._sessions.get(state) if state else None
        if not session:
            session = self._create_oauth_session(provider, redirect_uri)

        try:
            # Exchange code for token using Authlib
            token = await session.fetch_token(
                config.token_url,
                code=code,
                code_verifier=code_verifier,
            )
            return token
        except OAuthError as e:
            raise AuthenticationError(f"Token exchange failed: {e}") from e
        finally:
            # Clean up stored session
            if state and state in self._sessions:
                del self._sessions[state]

    async def refresh_token(
        self,
        provider: OAuthProvider,
        refresh_token: str,
    ) -> OAuth2Token:
        """
        Refresh OAuth token using Authlib.
        """
        config = self._get_provider_config(provider)
        session = OAuth2Session(
            client_id=config.client_id,
            client_secret=config.client_secret,
        )

        try:
            token = await session.refresh_token(
                config.token_url,
                refresh_token=refresh_token,
            )
            return token
        except OAuthError as e:
            raise AuthenticationError(f"Token refresh failed: {e}") from e

    async def get_user_info(
        self,
        provider: OAuthProvider,
        access_token: str,
    ) -> OAuthUserInfo:
        """
        Get user information using access token and Authlib.
        """
        config = self._get_provider_config(provider)

        if not config.userinfo_url:
            raise ConfigurationError(f"Provider {provider} does not support userinfo")

        session = OAuth2Session(token={'access_token': access_token, 'token_type': 'Bearer'})

        try:
            # Use Authlib to make authenticated request
            response = await session.get(config.userinfo_url)
            response.raise_for_status()
            user_data = response.json()

            # Normalize user data based on provider
            return self._normalize_user_info(provider, user_data)

        except Exception as e:
            raise AuthenticationError(f"Failed to get user info: {e}") from e

    def _normalize_user_info(self, provider: OAuthProvider, user_data: Dict[str, Any]) -> OAuthUserInfo:
        """Normalize user data from different providers."""

        if provider == OAuthProvider.GOOGLE:
            return OAuthUserInfo(
                provider=provider.value,
                provider_user_id=user_data.get("sub", ""),
                email=user_data.get("email"),
                email_verified=user_data.get("email_verified"),
                name=user_data.get("name"),
                given_name=user_data.get("given_name"),
                family_name=user_data.get("family_name"),
                picture=user_data.get("picture"),
                locale=user_data.get("locale"),
                raw_profile=user_data,
            )

        elif provider == OAuthProvider.GITHUB:
            return OAuthUserInfo(
                provider=provider.value,
                provider_user_id=str(user_data.get("id", "")),
                email=user_data.get("email"),
                name=user_data.get("name"),
                given_name=user_data.get("login"),
                picture=user_data.get("avatar_url"),
                raw_profile=user_data,
            )

        elif provider == OAuthProvider.MICROSOFT:
            return OAuthUserInfo(
                provider=provider.value,
                provider_user_id=user_data.get("id", ""),
                email=user_data.get("userPrincipalName"),
                name=user_data.get("displayName"),
                given_name=user_data.get("givenName"),
                family_name=user_data.get("surname"),
                raw_profile=user_data,
            )

        elif provider == OAuthProvider.FACEBOOK:
            picture_url = None
            if "picture" in user_data and isinstance(user_data["picture"], dict):
                picture_url = user_data["picture"].get("data", {}).get("url")

            return OAuthUserInfo(
                provider=provider.value,
                provider_user_id=str(user_data.get("id", "")),
                email=user_data.get("email"),
                name=user_data.get("name"),
                given_name=user_data.get("first_name"),
                family_name=user_data.get("last_name"),
                picture=picture_url,
                raw_profile=user_data,
            )

        else:
            # Generic fallback
            return OAuthUserInfo(
                provider=provider.value,
                provider_user_id=str(user_data.get("id") or user_data.get("sub", "")),
                email=user_data.get("email"),
                name=user_data.get("name"),
                given_name=user_data.get("given_name"),
                family_name=user_data.get("family_name"),
                picture=user_data.get("picture"),
                locale=user_data.get("locale"),
                raw_profile=user_data,
            )

    async def revoke_token(
        self,
        provider: OAuthProvider,
        token: str,
        token_type: str = "access_token",
    ) -> bool:
        """
        Revoke OAuth token with provider.
        """
        # Most providers support token revocation, but endpoints vary
        # This is a simplified implementation
        revoke_urls = {
            OAuthProvider.GOOGLE: "https://oauth2.googleapis.com/revoke",
            OAuthProvider.MICROSOFT: "https://login.microsoftonline.com/common/oauth2/v2.0/logout",
        }

        revoke_url = revoke_urls.get(provider)
        if not revoke_url:
            return False  # Provider doesn't support revocation

        try:
            response = await self.http_client.post(
                revoke_url,
                data={"token": token}
            )
            return response.status_code == 200
        except Exception:
            return False

    def validate_state(self, state: str) -> bool:
        """Validate OAuth state parameter."""
        return bool(state) and len(state) >= 16


def create_oauth_service(
    provider_configs: Dict[OAuthProvider, Dict[str, str]]
) -> AuthlibOAuthService:
    """
    Factory function to create OAuth service with provider configurations.

    Args:
        provider_configs: Dict mapping providers to their config dicts
                         e.g., {OAuthProvider.GOOGLE: {"client_id": "...", "client_secret": "..."}}
    """
    providers = {}

    for provider, config_dict in provider_configs.items():
        base_config = PROVIDER_CONFIGS.get(provider)
        if not base_config:
            raise ConfigurationError(f"Unsupported provider: {provider}")

        # Update base config with provided credentials
        config = base_config.model_copy()
        config.client_id = config_dict["client_id"]
        config.client_secret = config_dict["client_secret"]

        # Override any other settings
        for key, value in config_dict.items():
            if hasattr(config, key):
                setattr(config, key, value)

        providers[provider] = config

    return AuthlibOAuthService(providers)
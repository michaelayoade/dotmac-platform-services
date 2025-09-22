"""
Simple OAuth integration using Authlib - replaces 1,212 lines with ~50 lines.
"""

from enum import Enum
from typing import Dict, Any, Optional
from authlib.integrations.httpx_client import OAuth2Session
from authlib.common.security import generate_token

class OAuthProvider(str, Enum):
    """Supported OAuth providers."""
    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"

# Provider configurations
PROVIDERS = {
    OAuthProvider.GOOGLE: {
        "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_endpoint": "https://oauth2.googleapis.com/token",
        "userinfo_endpoint": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scopes": ["openid", "email", "profile"],
    },
    OAuthProvider.GITHUB: {
        "authorization_endpoint": "https://github.com/login/oauth/authorize",
        "token_endpoint": "https://github.com/login/oauth/access_token",
        "userinfo_endpoint": "https://api.github.com/user",
        "scopes": ["user:email"],
    },
    OAuthProvider.MICROSOFT: {
        "authorization_endpoint": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_endpoint": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "userinfo_endpoint": "https://graph.microsoft.com/v1.0/me",
        "scopes": ["openid", "email", "profile"],
    },
}

class SimpleOAuthClient:
    """Simple OAuth client using Authlib."""

    def __init__(self, provider: OAuthProvider, client_id: str, client_secret: str, redirect_uri: str):
        self.provider = provider
        self.config = PROVIDERS[provider]
        self.client = OAuth2Session(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=self.config["scopes"]
        )

    def get_authorization_url(self) -> tuple[str, str]:
        """Get authorization URL and state."""
        authorization_url, state = self.client.create_authorization_url(
            self.config["authorization_endpoint"]
        )
        return authorization_url, state

    async def exchange_code(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        token = await self.client.fetch_token(
            self.config["token_endpoint"],
            authorization_response=f"?code={code}"
        )
        return token

    async def get_user_info(self, token: Dict[str, Any]) -> Dict[str, Any]:
        """Get user information using access token."""
        self.client.token = token
        response = await self.client.get(self.config["userinfo_endpoint"])
        return response.json()

# Factory function
def create_oauth_client(provider: str, client_id: str, client_secret: str, redirect_uri: str) -> SimpleOAuthClient:
    """Create OAuth client for provider."""
    return SimpleOAuthClient(OAuthProvider(provider), client_id, client_secret, redirect_uri)
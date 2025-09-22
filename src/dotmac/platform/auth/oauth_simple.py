"""
Simple OAuth 2.0/OpenID Connect using Authlib - no bloat.

Replace 1,212 lines of custom OAuth with ~50 lines using Authlib.
"""

from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.integrations.fastapi_client import OAuth
from authlib.oauth2 import OAuth2Error
from authlib.oidc.core import CodeIDToken
import httpx
from typing import Dict, Any, Optional

from dotmac.platform.settings import settings
from dotmac.platform.logging import get_logger

logger = get_logger(__name__)

# Initialize OAuth with Authlib
oauth = OAuth()

# Register common providers using Authlib's built-in support
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
    client_kwargs={'scope': 'openid email profile'}
)

oauth.register(
    name='github',
    access_token_url='https://github.com/login/oauth/access_token',
    access_token_params=None,
    authorize_url='https://github.com/login/oauth/authorize',
    authorize_params=None,
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'},
)

oauth.register(
    name='microsoft',
    server_metadata_url='https://login.microsoftonline.com/common/v2.0/.well-known/openid_configuration',
    client_kwargs={'scope': 'openid email profile'}
)


async def get_oauth_user_info(provider: str, token: Dict[str, Any]) -> Dict[str, Any]:
    """Get user info from OAuth provider using token."""
    try:
        client = oauth.create_client(provider)
        async with AsyncOAuth2Client(
            client_id=client.client_id,
            client_secret=client.client_secret,
            token=token
        ) as session:
            if provider == 'google':
                resp = await session.get('https://www.googleapis.com/oauth2/v2/userinfo')
            elif provider == 'github':
                resp = await session.get('https://api.github.com/user')
            elif provider == 'microsoft':
                resp = await session.get('https://graph.microsoft.com/v1.0/me')
            else:
                raise ValueError(f"Unsupported provider: {provider}")

            resp.raise_for_status()
            return resp.json()

    except Exception as e:
        logger.error("Failed to get OAuth user info", provider=provider, error=str(e))
        raise OAuth2Error(f"Failed to get user info: {e}")


# For advanced use cases, use Authlib directly:
#
# from authlib.integrations.httpx_client import AsyncOAuth2Client
#
# client = AsyncOAuth2Client(
#     client_id='your_client_id',
#     client_secret='your_secret'
# )
#
# # Get authorization URL
# uri, state = client.create_authorization_url('https://provider.com/auth')
#
# # Exchange code for token
# token = await client.fetch_token(
#     'https://provider.com/token',
#     authorization_response=request.url
# )
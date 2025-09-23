"""
Simplified Auth Core - Replaces multiple complex files.

This module provides all auth functionality using standard libraries:
- JWT with Authlib
- Sessions with Redis
- OAuth with Authlib
- API keys with Redis
- Password hashing with Passlib
"""

import json
import secrets
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog
from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.jose import JoseError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    APIKeyHeader,
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
)
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict, EmailStr, Field

try:
    import redis.asyncio as redis

    _redis_available = True
except ImportError:
    _redis_available = False
    redis = None

REDIS_AVAILABLE = _redis_available

logger = structlog.get_logger(__name__)

# ============================================
# Configuration
# ============================================

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# FastAPI Security schemes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)

# Configuration from settings or defaults
try:
    from ..settings import settings

    _jwt_secret = settings.jwt.secret_key
    _jwt_algorithm = settings.jwt.algorithm
    _access_token_expire_minutes = settings.jwt.access_token_expire_minutes
    _refresh_token_expire_days = settings.jwt.refresh_token_expire_days
    _redis_url = settings.redis.redis_url
except ImportError:
    # Fallback values if settings not available
    _jwt_secret = "default-secret-change-this"
    _jwt_algorithm = "HS256"
    _access_token_expire_minutes = 15
    _refresh_token_expire_days = 7
    _redis_url = "redis://localhost:6379"

# Module constants
JWT_SECRET = _jwt_secret
JWT_ALGORITHM = _jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = _access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = _refresh_token_expire_days
REDIS_URL = _redis_url

# ============================================
# Models
# ============================================


class TokenType(str, Enum):
    """Token types."""

    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"


class UserInfo(BaseModel):
    """User information from auth."""

    model_config = ConfigDict(extra="forbid")

    user_id: str
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    tenant_id: Optional[str] = None


class TokenData(BaseModel):
    """Token response."""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


class OAuthProvider(str, Enum):
    """Supported OAuth providers."""

    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"


# OAuth configurations
OAUTH_CONFIGS = {
    OAuthProvider.GOOGLE: {
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scope": "openid email profile",
    },
    OAuthProvider.GITHUB: {
        "authorize_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
        "scope": "user:email",
    },
    OAuthProvider.MICROSOFT: {
        "authorize_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "userinfo_url": "https://graph.microsoft.com/v1.0/me",
        "scope": "openid email profile",
    },
}

# ============================================
# JWT Service
# ============================================


class JWTService:
    """Simplified JWT service using Authlib."""

    def __init__(self, secret: str | None = None, algorithm: str | None = None):
        self.secret = secret or JWT_SECRET
        self.algorithm = algorithm or JWT_ALGORITHM
        self.header = {"alg": self.algorithm}

    def create_access_token(
        self,
        subject: str,
        additional_claims: Dict[str, Any] | None = None,
        expire_minutes: int | None = None,
    ) -> str:
        """Create access token."""
        data = {"sub": subject, "type": TokenType.ACCESS.value}
        if additional_claims:
            data.update(additional_claims)

        expires_delta = timedelta(minutes=expire_minutes or ACCESS_TOKEN_EXPIRE_MINUTES)
        return self._create_token(data, expires_delta)

    def create_refresh_token(
        self, subject: str, additional_claims: Dict[str, Any] | None = None
    ) -> str:
        """Create refresh token."""
        data = {"sub": subject, "type": TokenType.REFRESH.value}
        if additional_claims:
            data.update(additional_claims)

        expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        return self._create_token(data, expires_delta)

    def _create_token(self, data: dict, expires_delta: timedelta) -> str:
        """Internal token creation."""
        to_encode = data.copy()
        expire = datetime.now(UTC) + expires_delta

        to_encode.update(
            {"exp": expire, "iat": datetime.now(UTC), "jti": secrets.token_urlsafe(16)}
        )

        token = jwt.encode(self.header, to_encode, self.secret)
        return token.decode("utf-8") if isinstance(token, bytes) else token

    def verify_token(self, token: str) -> dict:
        """Verify and decode token."""
        try:
            claims = jwt.decode(token, self.secret)
            claims.validate()
            return claims
        except JoseError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {e}",
                headers={"WWW-Authenticate": "Bearer"},
            )


# ============================================
# Session Management
# ============================================


class SessionManager:
    """Redis-based session manager."""

    def __init__(self, redis_url: str | None = None):
        self.redis_url = redis_url or REDIS_URL
        self._redis = None

    async def _get_redis(self):
        """Get Redis connection."""
        if not REDIS_AVAILABLE:
            raise HTTPException(
                status_code=500, detail="Redis not available. Install with: pip install redis"
            )

        if self._redis is None:
            self._redis = await redis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    async def create_session(self, user_id: str, data: dict, ttl: int = 3600) -> str:
        """Create new session."""
        session_id = secrets.token_urlsafe(32)
        session_key = f"session:{session_id}"

        session_data = {
            "user_id": user_id,
            "created_at": datetime.now(UTC).isoformat(),
            "data": data,
        }

        client = await self._get_redis()
        await client.setex(session_key, ttl, json.dumps(session_data))

        # Track user sessions
        user_key = f"user_sessions:{user_id}"
        # These Redis operations may not be awaitable in this context
        client.sadd(user_key, session_id)
        client.expire(user_key, ttl)

        return session_id

    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get session data."""
        try:
            client = await self._get_redis()
            data = await client.get(f"session:{session_id}")
            return json.loads(data) if data else None
        except Exception as e:
            logger.error("Failed to get session", session_id=session_id, error=str(e))
            return None

    async def delete_session(self, session_id: str) -> bool:
        """Delete session."""
        try:
            client = await self._get_redis()

            # Get session to find user_id
            session = await self.get_session(session_id)
            if session:
                user_id = session.get("user_id")
                if user_id:
                    # Remove session from user's session set
                    client.srem(f"user_sessions:{user_id}", session_id)

            deleted_count = await client.delete(f"session:{session_id}")
            return bool(deleted_count)
        except Exception as e:
            logger.error("Failed to delete session", session_id=session_id, error=str(e))
            return False


# ============================================
# OAuth Service
# ============================================


class OAuthService:
    """OAuth service using Authlib."""

    def __init__(self, client_id: str | None = None, client_secret: str | None = None):
        self.client_id = client_id or ""
        self.client_secret = client_secret or ""

    def get_authorization_url(
        self, provider: OAuthProvider, redirect_uri: str, state: str | None = None
    ) -> tuple[str, str]:
        """Get authorization URL."""
        config = OAUTH_CONFIGS[provider]
        state = state or secrets.token_urlsafe(32)

        client = AsyncOAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            scope=config["scope"],
            redirect_uri=redirect_uri,
        )

        url = client.create_authorization_url(config["authorize_url"], state=state)
        return url, state

    async def exchange_code(self, provider: OAuthProvider, code: str, redirect_uri: str) -> dict:
        """Exchange code for tokens."""
        config = OAUTH_CONFIGS[provider]

        client = AsyncOAuth2Client(
            client_id=self.client_id, client_secret=self.client_secret, redirect_uri=redirect_uri
        )

        token = await client.fetch_token(config["token_url"], code=code)
        return token

    async def get_user_info(self, provider: OAuthProvider, access_token: str) -> dict:
        """Get user info from provider."""
        config = OAUTH_CONFIGS[provider]

        client = AsyncOAuth2Client(token={"access_token": access_token})
        resp = await client.get(config["userinfo_url"])
        return resp.json()


# ============================================
# API Key Service
# ============================================


class APIKeyService:
    """API key management with Redis."""

    def __init__(self, redis_url: str | None = None):
        self.redis_url = redis_url or REDIS_URL
        self._redis = None
        self._memory_keys: dict = {}  # Initialize for type checker

    async def _get_redis(self):
        """Get Redis connection."""
        if not REDIS_AVAILABLE:
            # Fallback to in-memory storage
            if not hasattr(self, "_memory_keys"):
                self._memory_keys = {}
            return None

        if self._redis is None:
            self._redis = await redis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    async def create_api_key(self, user_id: str, name: str, scopes: List[str] | None = None) -> str:
        """Create API key."""
        api_key = f"sk_{secrets.token_urlsafe(32)}"

        data = {
            "user_id": user_id,
            "name": name,
            "scopes": scopes or [],
            "created_at": datetime.now(UTC).isoformat(),
        }

        client = await self._get_redis()
        if client:
            await client.set(f"api_key:{api_key}", json.dumps(data))
        else:
            # Fallback to memory
            self._memory_keys[api_key] = data

        return api_key

    async def verify_api_key(self, api_key: str) -> Optional[dict]:
        """Verify API key."""
        try:
            client = await self._get_redis()
            if client:
                data = await client.get(f"api_key:{api_key}")
                return json.loads(data) if data else None
            else:
                # Fallback to memory
                return getattr(self, "_memory_keys", {}).get(api_key)
        except Exception as e:
            logger.error("Failed to verify API key", error=str(e))
            return None

    async def revoke_api_key(self, api_key: str) -> bool:
        """Revoke API key."""
        try:
            client = await self._get_redis()
            if client:
                deleted_count = await client.delete(f"api_key:{api_key}")
                return bool(deleted_count)
            else:
                # Fallback to memory
                return bool(getattr(self, "_memory_keys", {}).pop(api_key, None))
        except Exception as e:
            logger.error("Failed to revoke API key", error=str(e))
            return False


# ============================================
# Service Instances
# ============================================

# Global service instances
jwt_service = JWTService()
session_manager = SessionManager()
oauth_service = OAuthService()
api_key_service = APIKeyService()

# ============================================
# Dependencies
# ============================================


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Depends(api_key_header),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> UserInfo:
    """Get current authenticated user."""

    # Try Bearer token first
    if credentials and credentials.credentials:
        try:
            claims = jwt_service.verify_token(credentials.credentials)
            return _claims_to_user_info(claims)
        except HTTPException:
            pass

    # Try OAuth2 token
    if token:
        try:
            claims = jwt_service.verify_token(token)
            return _claims_to_user_info(claims)
        except HTTPException:
            pass

    # Try API key
    if api_key:
        key_data = await api_key_service.verify_api_key(api_key)
        if key_data:
            return UserInfo(
                user_id=key_data["user_id"],
                username=key_data["name"],
                roles=["api_user"],
                permissions=key_data.get("scopes", []),
            )

    # No valid auth
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Depends(api_key_header),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[UserInfo]:
    """Get current user if authenticated, None otherwise."""
    try:
        return await get_current_user(token, api_key, credentials)
    except HTTPException:
        return None


def _claims_to_user_info(claims: dict) -> UserInfo:
    """Convert JWT claims to UserInfo."""
    return UserInfo(
        user_id=claims.get("sub", ""),
        email=claims.get("email"),
        username=claims.get("username"),
        roles=claims.get("roles", []),
        permissions=claims.get("permissions", []),
        tenant_id=claims.get("tenant_id"),
    )


# ============================================
# Utility Functions
# ============================================


def hash_password(password: str) -> str:
    """Hash password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, **kwargs) -> str:
    """Create access token."""
    return jwt_service.create_access_token(user_id, kwargs)


def create_refresh_token(user_id: str, **kwargs) -> str:
    """Create refresh token."""
    return jwt_service.create_refresh_token(user_id, kwargs)


# ============================================
# Configuration Function
# ============================================


def configure_auth(
    jwt_secret: str | None = None,
    jwt_algorithm: str | None = None,
    access_token_expire_minutes: int | None = None,
    refresh_token_expire_days: int | None = None,
    redis_url: str | None = None,
):
    """Configure auth services."""
    global JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, REDIS_URL
    global jwt_service, session_manager, oauth_service, api_key_service

    # Dynamic configuration requires "constant" reassignment
    if jwt_secret:
        JWT_SECRET = jwt_secret  # type: ignore[misc]
    if jwt_algorithm:
        JWT_ALGORITHM = jwt_algorithm  # type: ignore[misc]
    if access_token_expire_minutes:
        ACCESS_TOKEN_EXPIRE_MINUTES = access_token_expire_minutes  # type: ignore[misc]
    if refresh_token_expire_days:
        REFRESH_TOKEN_EXPIRE_DAYS = refresh_token_expire_days  # type: ignore[misc]
    if redis_url:
        REDIS_URL = redis_url  # type: ignore[misc]

    # Recreate services with new config
    jwt_service = JWTService(JWT_SECRET, JWT_ALGORITHM)
    session_manager = SessionManager(REDIS_URL)
    oauth_service = OAuthService()
    api_key_service = APIKeyService(REDIS_URL)

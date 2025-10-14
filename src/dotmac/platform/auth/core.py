"""
Simplified Auth Core - Replaces multiple complex files.

This module provides all auth functionality using standard libraries:
- JWT with Authlib
- Sessions with Redis
- OAuth with Authlib
- API keys with Redis
- Password hashing with Passlib
"""

import inspect
import json
import os
import secrets
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, cast
from uuid import UUID

import structlog
from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.jose import JoseError, jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import (
    APIKeyHeader,
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
)
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict, EmailStr, Field

redis_async: Any | None
try:
    import redis.asyncio as redis_async
except ImportError:  # pragma: no cover - optional dependency
    redis_async = None

REDIS_AVAILABLE = redis_async is not None

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
    # Get default role from settings (now has proper field with default="user")
    _default_user_role = settings.default_user_role
except ImportError:
    # Fallback values if settings not available
    _jwt_secret = "default-secret-change-this"
    _jwt_algorithm = "HS256"
    _access_token_expire_minutes = 15
    _refresh_token_expire_days = 7
    _redis_url = "redis://localhost:6379"
    _default_user_role = "user"  # Standard user role as fallback

# Module constants
JWT_SECRET = _jwt_secret
JWT_ALGORITHM = _jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = _access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = _refresh_token_expire_days
REDIS_URL = _redis_url
DEFAULT_USER_ROLE = _default_user_role

# ============================================
# Models
# ============================================


class TokenType(str, Enum):
    """Token types."""

    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"


class UserInfo(BaseModel):
    """User information from auth.

    This model is used in JWT tokens and API authentication.
    User IDs are stored as strings for JWT/HTTP compatibility.

    Platform Admin Support:
        - is_platform_admin=True: User can access ALL tenants (SaaS admin)
        - tenant_id=None: Platform admins are not assigned to any specific tenant
        - Platform admins can set X-Target-Tenant-ID header to impersonate tenants

    Important: When using user_id with database models that expect UUID,
    convert using UUID(user_info.user_id) or the ensure_uuid() helper.

    Example:
        >>> from uuid import UUID
        >>> user = await db.get(User, UUID(current_user.user_id))
        >>> # Or using helper:
        >>> user = await db.get(User, ensure_uuid(current_user.user_id))

        >>> # Platform admin checking:
        >>> if current_user.is_platform_admin:
        >>>     # Can access all tenants
        >>>     pass
    """

    model_config = ConfigDict(extra="forbid")

    user_id: str  # String representation of UUID for JWT/API compatibility
    email: EmailStr | None = None
    username: str | None = None
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    tenant_id: str | None = None  # None for platform admins
    is_platform_admin: bool = Field(
        default=False, description="Platform admin with cross-tenant access"
    )


class TokenData(BaseModel):
    """Token response."""

    model_config = ConfigDict()

    access_token: str
    refresh_token: str | None = None
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
        "token_url": "https://github.com/login/oauth/access_token",
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
# Helper Functions
# ============================================


def ensure_uuid(value: str | UUID) -> UUID:
    """Convert string to UUID if needed.

    This helper ensures consistent UUID handling across the auth layer.
    UserInfo stores user_id as string (for JWT/API compatibility), but
    database models use UUID type (for type safety).

    Args:
        value: Either a string representation of UUID or UUID object

    Returns:
        UUID object

    Raises:
        ValueError: If string is not a valid UUID format

    Example:
        >>> from dotmac.platform.auth.core import UserInfo, ensure_uuid
        >>> user_info = UserInfo(user_id="550e8400-e29b-41d4-a716-446655440000", ...)
        >>> user = await db.get(User, ensure_uuid(user_info.user_id))
    """
    if isinstance(value, str):
        return UUID(value)
    return value


# ============================================
# JWT Service
# ============================================


class JWTService:
    """Simplified JWT service using Authlib with token revocation support."""

    def __init__(
        self, secret: str | None = None, algorithm: str | None = None, redis_url: str | None = None
    ):
        self.secret = secret or JWT_SECRET
        self.algorithm = algorithm or JWT_ALGORITHM
        self.header = {"alg": self.algorithm}
        self.redis_url = redis_url or REDIS_URL
        self._redis: Any | None = None

    def create_access_token(
        self,
        subject: str,
        additional_claims: dict[str, Any] | None = None,
        expire_minutes: int | None = None,
    ) -> str:
        """Create access token."""
        data = {"sub": subject, "type": TokenType.ACCESS.value}
        if additional_claims:
            data.update(additional_claims)

        expires_delta = timedelta(minutes=expire_minutes or ACCESS_TOKEN_EXPIRE_MINUTES)
        return self._create_token(data, expires_delta)

    def create_refresh_token(
        self, subject: str, additional_claims: dict[str, Any] | None = None
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

    def verify_token(self, token: str, expected_type: TokenType | None = None) -> dict[str, Any]:
        """Verify and decode token with sync blacklist check.

        Args:
            token: JWT token to verify
            expected_type: Optional expected token type (ACCESS, REFRESH, or API_KEY)

        Returns:
            Token claims dictionary

        Raises:
            HTTPException: If token is invalid, revoked, or has wrong type
        """
        try:
            claims_raw = jwt.decode(token, self.secret)
            claims_raw.validate()
            claims = cast(dict[str, Any], dict(claims_raw))

            # Validate token type if specified
            if expected_type:
                token_type = claims.get("type")
                if token_type != expected_type.value:
                    raise JoseError(
                        f"Invalid token type. Expected {expected_type.value}, got {token_type}"
                    )

            # Check if token is revoked (sync version)
            jti = claims.get("jti")
            if jti and self.is_token_revoked_sync(jti):
                raise JoseError("Token has been revoked")

            return claims
        except JoseError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {e}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def _get_redis(self) -> Any | None:
        """Get Redis connection."""
        if not REDIS_AVAILABLE:
            return None
        if self._redis is None and redis_async is not None:
            self._redis = await redis_async.from_url(self.redis_url, decode_responses=True)
        return self._redis

    async def revoke_token(self, token: str) -> bool:
        """Revoke a token by adding its JTI to blacklist."""
        try:
            redis_client = await self._get_redis()
            if not redis_client:
                logger.warning("Redis not available, cannot revoke tokens")
                return False

            claims = jwt.decode(token, self.secret)
            jti = claims.get("jti")
            if not jti:
                return False

            # Calculate TTL based on token expiry
            exp = claims.get("exp")
            if exp:
                ttl = max(0, exp - int(datetime.now(UTC).timestamp()))
                await redis_client.setex(f"blacklist:{jti}", ttl, "1")
            else:
                await redis_client.set(f"blacklist:{jti}", "1")

            logger.info(f"Revoked token with JTI: {jti}")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            return False

    def is_token_revoked_sync(self, jti: str) -> bool:
        """Check if token is revoked (sync version)."""
        try:
            from dotmac.platform.core.caching import get_redis

            redis_client = get_redis()
            if not redis_client:
                return False
            return bool(redis_client.exists(f"blacklist:{jti}"))
        except Exception as e:
            logger.error(f"Failed to check token revocation status: {e}")
            return False

    async def is_token_revoked(self, jti: str) -> bool:
        """Check if a token is revoked."""
        try:
            redis_client = await self._get_redis()
            if not redis_client:
                return False
            return bool(await redis_client.exists(f"blacklist:{jti}"))
        except Exception:
            return False

    async def verify_token_async(
        self, token: str, expected_type: TokenType | None = None
    ) -> dict[str, Any]:
        """Verify and decode token with revocation check (async version).

        Args:
            token: JWT token to verify
            expected_type: Optional expected token type (ACCESS, REFRESH, or API_KEY)

        Returns:
            Token claims dictionary

        Raises:
            HTTPException: If token is invalid, revoked, or has wrong type
        """
        try:
            claims_raw = jwt.decode(token, self.secret)
            claims_raw.validate()
            claims = cast(dict[str, Any], dict(claims_raw))

            # Validate token type if specified
            if expected_type:
                token_type = claims.get("type")
                if token_type != expected_type.value:
                    raise JoseError(
                        f"Invalid token type. Expected {expected_type.value}, got {token_type}"
                    )

            # Check if token is revoked
            jti = claims.get("jti")
            if jti and await self.is_token_revoked(jti):
                raise JoseError("Token has been revoked")

            return claims
        except JoseError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {e}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def revoke_user_tokens(self, user_id: str) -> int:
        """Revoke all tokens associated with a user by removing any active JTIs.

        This scans the redis blacklist/current tokens namespace for keys tagged with
        the user ID and deletes them. Returns the count of revoked tokens.
        """
        redis_client = await self._get_redis()
        if not redis_client:
            logger.warning("Redis not available, cannot revoke user tokens")
            return 0

        revoked = 0
        try:
            pattern = f"tokens:{user_id}:*"
            async for key in redis_client.scan_iter(match=pattern):
                jti = await redis_client.get(key)
                if jti:
                    await redis_client.delete(f"blacklist:{jti}")
                await redis_client.delete(key)
                revoked += 1
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to revoke user tokens", user_id=user_id, error=str(exc))

        return revoked


# ============================================
# Session Management
# ============================================


class SessionManager:
    """Redis-based session manager with fallback support."""

    def __init__(self, redis_url: str | None = None, fallback_enabled: bool = True) -> None:
        self.redis_url = redis_url or REDIS_URL
        self._redis: Any | None = None
        self._fallback_store: dict[str, dict[str, Any]] = {}  # In-memory fallback
        self._fallback_enabled = fallback_enabled
        self._redis_healthy = True

    async def _get_redis(self) -> Any | None:
        """Get Redis connection with health check."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis library not available, using in-memory fallback")
            self._redis_healthy = False
            return None

        if self._redis is None and redis_async is not None:
            try:
                self._redis = await redis_async.from_url(self.redis_url, decode_responses=True)
                # Verify connection
                await self._redis.ping()
                self._redis_healthy = True
                logger.info("Redis connection established")
            except Exception as e:
                logger.error("Redis connection failed", error=str(e))
                self._redis_healthy = False
                self._redis = None

                if not self._fallback_enabled:
                    raise HTTPException(
                        status_code=503,
                        detail="Session service unavailable (Redis connection failed)",
                    )
        return self._redis

    async def create_session(self, user_id: str, data: dict[str, Any], ttl: int = 3600) -> str:
        """Create new session with Redis or fallback."""
        session_id = secrets.token_urlsafe(32)
        session_key = f"session:{session_id}"

        session_data = {
            "user_id": user_id,
            "created_at": datetime.now(UTC).isoformat(),
            "data": data,
        }

        client = await self._get_redis()
        if client:
            try:
                await client.setex(session_key, ttl, json.dumps(session_data))
                # Track user sessions
                user_key = f"user_sessions:{user_id}"
                await client.sadd(user_key, session_id)
                await client.expire(user_key, ttl)
            except Exception as e:
                logger.warning("Redis session write failed, using fallback", error=str(e))
                if self._fallback_enabled:
                    self._fallback_store[session_id] = session_data
                else:
                    raise HTTPException(status_code=503, detail="Session service unavailable")
        else:
            # Use fallback
            if self._fallback_enabled:
                logger.info("Using in-memory session store (single-server only)")
                self._fallback_store[session_id] = session_data
            else:
                raise HTTPException(
                    status_code=503, detail="Session service unavailable (Redis not available)"
                )

        return session_id

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Get session data from Redis or fallback."""
        client = await self._get_redis()
        if client:
            try:
                data = await client.get(f"session:{session_id}")
                if data:
                    return cast(dict[str, Any], json.loads(data))
            except Exception as e:
                logger.warning(
                    "Failed to get session from Redis", session_id=session_id, error=str(e)
                )

        # Check fallback store
        if self._fallback_enabled and session_id in self._fallback_store:
            logger.debug("Session retrieved from fallback store", session_id=session_id)
            return self._fallback_store[session_id]

        return None

    async def delete_session(self, session_id: str) -> bool:
        """Delete session."""
        try:
            client = await self._get_redis()
            if client:
                # Get session to find user_id
                session = await self.get_session(session_id)
                if session:
                    user_id = session.get("user_id")
                    if user_id:
                        # Remove session from user's session set
                        await client.srem(f"user_sessions:{user_id}", session_id)

                deleted_count = await client.delete(f"session:{session_id}")
                return bool(deleted_count)

            # Fallback cleanup
            self._fallback_store.pop(session_id, None)
            return True
        except Exception as e:
            logger.error("Failed to delete session", session_id=session_id, error=str(e))
            return False

    async def get_user_sessions(self, user_id: str) -> dict[str, dict[str, Any]]:
        """Get all sessions for a user."""
        try:
            client = await self._get_redis()
            if not client:
                # Return empty dict if Redis not available
                return {}

            user_sessions_key = f"user_sessions:{user_id}"

            # Get all session IDs for this user
            session_ids = await client.smembers(user_sessions_key)

            sessions: dict[str, dict[str, Any]] = {}
            for session_id in session_ids:
                session_key = f"session:{session_id}"
                session_data = await client.get(session_key)
                if session_data:
                    sessions[session_key] = cast(dict[str, Any], json.loads(session_data))

            return sessions
        except Exception as e:
            logger.error(f"Failed to get user sessions for {user_id}: {e}")
            return {}

    async def delete_user_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user."""
        try:
            client = await self._get_redis()
            if not client:
                self._fallback_store = {
                    sid: data
                    for sid, data in self._fallback_store.items()
                    if data.get("user_id") != user_id
                }
                return 0
            user_sessions_key = f"user_sessions:{user_id}"

            # Get all session IDs for this user
            session_ids = await client.smembers(user_sessions_key)

            deleted_count = 0
            for session_id in session_ids:
                session_key = f"session:{session_id}"
                if await client.delete(session_key):
                    deleted_count += 1

            # Clean up the user sessions set
            await client.delete(user_sessions_key)

            logger.info(f"Deleted {deleted_count} sessions for user {user_id}")
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to delete user sessions for {user_id}: {e}")
            return 0


# ============================================
# OAuth Service
# ============================================


class OAuthService:
    """OAuth service using Authlib."""

    def __init__(self, client_id: str | None = None, client_secret: str | None = None) -> None:
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

    async def exchange_code(
        self, provider: OAuthProvider, code: str, redirect_uri: str
    ) -> dict[str, Any]:
        """Exchange code for tokens."""
        config = OAUTH_CONFIGS[provider]

        client = AsyncOAuth2Client(
            client_id=self.client_id, client_secret=self.client_secret, redirect_uri=redirect_uri
        )

        token = await client.fetch_token(config["token_url"], code=code)
        return cast(dict[str, Any], token)

    async def get_user_info(self, provider: OAuthProvider, access_token: str) -> dict[str, Any]:
        """Get user info from provider."""
        config = OAUTH_CONFIGS[provider]

        client = AsyncOAuth2Client(token={"access_token": access_token})
        resp = await client.get(config["userinfo_url"])
        return cast(dict[str, Any], resp.json())


# ============================================
# API Key Service
# ============================================


class APIKeyService:
    """API key management with Redis."""

    def __init__(self, redis_url: str | None = None) -> None:
        self.redis_url = redis_url or REDIS_URL
        self._redis: Any | None = None
        self._memory_keys: dict[str, dict[str, Any]] = {}
        self._memory_meta: dict[str, dict[str, Any]] = {}
        self._memory_lookup: dict[str, str] = {}
        self._serialize: Callable[[dict[str, Any]], str] = json.dumps
        self._deserialize: Callable[[str], dict[str, Any]] = json.loads

    async def _get_redis(self) -> Any | None:
        """Get Redis connection."""
        if not REDIS_AVAILABLE:
            return None

        if self._redis is None and redis_async is not None:
            self._redis = await redis_async.from_url(self.redis_url, decode_responses=True)
        return self._redis

    async def create_api_key(
        self, user_id: str, name: str, scopes: list[str] | None = None, tenant_id: str | None = None
    ) -> str:
        """
        Create API key with tenant binding.

        SECURITY: API keys MUST be bound to a tenant to prevent cross-tenant access.
        The tenant_id is stored with the key and populated in UserInfo during verification.

        NOTE: This method stores minimal data for backwards compatibility.
        For production use, prefer the enhanced API key creation in api_keys_router.py
        which includes hashing, metadata, and expiration.

        Args:
            user_id: User ID (UUID as string)
            name: Human-readable key name
            scopes: Optional permission scopes
            tenant_id: Tenant ID for multi-tenant isolation (REQUIRED for production)

        Returns:
            The generated API key (plaintext - only shown once)
        """
        import hashlib

        api_key = f"sk_{secrets.token_urlsafe(32)}"

        data = {
            "user_id": user_id,
            "name": name,
            "scopes": scopes or [],
            "tenant_id": tenant_id,  # SECURITY: Bind API key to tenant
            "created_at": datetime.now(UTC).isoformat(),
        }

        # SECURITY: Hash the API key before storing
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        client = await self._get_redis()
        if client:
            # Store with hash as key instead of plaintext
            await client.set(f"api_key:{api_key_hash}", json.dumps(data))
        else:
            # Fallback to memory (also use hash)
            self._memory_keys[api_key_hash] = data

        return api_key

    async def verify_api_key(self, api_key: str) -> dict | None:
        """
        Verify API key by hashing and looking up.

        SECURITY: The API key is hashed before lookup to prevent
        plaintext credential exposure in Redis. Also validates is_active
        and expires_at from metadata to prevent disabled/expired keys from working.
        """
        try:
            import hashlib

            # Hash the provided API key for lookup
            api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

            client = await self._get_redis()
            if client:
                data = await client.get(f"api_key:{api_key_hash}")
                if not data:
                    return None

                key_data: dict[str, Any] = json.loads(data)

                # SECURITY: Load metadata to check is_active and expires_at
                # First get the key_id from the lookup table
                key_id = await client.get(f"api_key_lookup:{api_key_hash}")
                if key_id:
                    if isinstance(key_id, bytes):
                        key_id = key_id.decode('utf-8')

                    # Load metadata
                    metadata_str = await client.get(f"api_key_meta:{key_id}")
                    if metadata_str:
                        metadata = self._deserialize(metadata_str)

                        # Check if key is active
                        if not metadata.get("is_active", True):
                            logger.warning(f"API key {key_id} is disabled")
                            return None

                        # Check if key is expired
                        expires_at_str = metadata.get("expires_at")
                        if expires_at_str:
                            expires_at = datetime.fromisoformat(expires_at_str)
                            if expires_at < datetime.now(UTC):
                                logger.warning(f"API key {key_id} is expired")
                                return None

                        # Merge metadata into key_data for backward compatibility
                        key_data.update(metadata)

                return key_data

            # Fallback to memory (also uses hash)
            return self._memory_keys.get(api_key_hash)
        except Exception as e:
            logger.error("Failed to verify API key", error=str(e))
            return None

    async def revoke_api_key(self, api_key: str) -> bool:
        """
        Revoke API key by hashing and deleting.

        SECURITY: The API key is hashed before deletion lookup.

        Args:
            api_key: The plaintext API key to revoke

        Returns:
            True if the key was revoked, False otherwise
        """
        try:
            import hashlib

            # Hash the API key for lookup
            api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

            client = await self._get_redis()
            if client:
                deleted_count = await client.delete(f"api_key:{api_key_hash}")
                return bool(deleted_count)
            # Fallback to memory (also uses hash)
            return bool(self._memory_keys.pop(api_key_hash, None))
        except Exception as e:
            logger.error("Failed to revoke API key", error=str(e))
            return False

    async def revoke_api_key_by_hash(self, api_key_hash: str) -> bool:
        """
        Revoke API key using an already-computed hash.

        SECURITY: This method is for internal use when the hash is already available.
        Use revoke_api_key() when you have the plaintext key.

        Args:
            api_key_hash: The SHA-256 hash of the API key

        Returns:
            True if the key was revoked, False otherwise
        """
        try:
            client = await self._get_redis()
            if client:
                deleted_count = await client.delete(f"api_key:{api_key_hash}")
                return bool(deleted_count)
            # Fallback to memory
            return bool(self._memory_keys.pop(api_key_hash, None))
        except Exception as e:
            logger.error("Failed to revoke API key by hash", error=str(e))
            return False


# ============================================
# Service Instances
# ============================================

# Global service instances
jwt_service = JWTService()

# SECURITY: Disable session fallback in production to ensure revocation works across workers
# In production, Redis is mandatory for proper session management
# Use settings.environment instead of os.getenv to respect .env files
try:
    _is_production = settings.environment.lower() in ("production", "prod")
except (ImportError, AttributeError):
    # Fallback if settings not available
    _is_production = os.getenv("ENVIRONMENT", "development").lower() in ("production", "prod")

_require_redis_for_sessions = (
    os.getenv("REQUIRE_REDIS_SESSIONS", str(_is_production)).lower() == "true"
)

session_manager = SessionManager(fallback_enabled=not _require_redis_for_sessions)

oauth_service = OAuthService()
api_key_service = APIKeyService()

# ============================================
# Dependencies
# ============================================


async def _verify_token_with_fallback(
    token: str, expected_type: TokenType | None = None
) -> dict[str, Any]:
    """Verify tokens using async path when available, falling back to the sync method.

    Args:
        token: JWT token to verify
        expected_type: Optional expected token type for validation

    Returns:
        Token claims dictionary
    """
    verify_async = getattr(jwt_service, "verify_token_async", None)
    if verify_async:
        try:
            result = verify_async(token, expected_type)
            if inspect.isawaitable(result):
                resolved = await result
                return cast(dict[str, Any], resolved)
            if isinstance(result, dict):
                return cast(dict[str, Any], result)
        except TypeError:
            # Mocked objects (MagicMock) may not support awaiting
            pass

    return jwt_service.verify_token(token, expected_type)


async def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    api_key: str | None = Depends(api_key_header),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserInfo:
    """Get current authenticated user from Bearer token, OAuth2, API key, or HttpOnly cookie.

    SECURITY: All JWT tokens are validated for ACCESS token type to prevent
    refresh token reuse attacks. API keys are handled separately.
    """

    # Try Bearer token first - must be ACCESS token
    if credentials and credentials.credentials:
        try:
            claims = await _verify_token_with_fallback(credentials.credentials, TokenType.ACCESS)
            return _claims_to_user_info(claims)
        except HTTPException:
            pass

    # Try OAuth2 token - must be ACCESS token
    if token:
        try:
            claims = await _verify_token_with_fallback(token, TokenType.ACCESS)
            return _claims_to_user_info(claims)
        except HTTPException:
            pass

    # Try HttpOnly cookie access token - must be ACCESS token
    access_token = request.cookies.get("access_token")
    if access_token:
        try:
            claims = await _verify_token_with_fallback(access_token, TokenType.ACCESS)
            return _claims_to_user_info(claims)
        except HTTPException:
            pass

    # Try API key (no token type check needed - different auth mechanism)
    if api_key:
        key_data = await api_key_service.verify_api_key(api_key)
        if key_data:
            return UserInfo(
                user_id=key_data["user_id"],
                username=key_data["name"],
                roles=["api_user"],
                permissions=key_data.get("scopes", []),
                tenant_id=key_data.get("tenant_id"),  # SECURITY: Populate tenant_id for isolation
            )

    # No valid auth
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user_optional(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    api_key: str | None = Depends(api_key_header),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserInfo | None:
    """Get current user if authenticated, None otherwise."""
    try:
        return await get_current_user(request, token, api_key, credentials)
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
        is_platform_admin=claims.get("is_platform_admin", False),
    )


# ============================================
# Utility Functions
# ============================================


def hash_password(password: str) -> str:
    """Hash password."""
    return str(pwd_context.hash(password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password."""
    return bool(pwd_context.verify(plain_password, hashed_password))


def create_access_token(user_id: str, **kwargs: Any) -> str:
    """Create access token."""
    return jwt_service.create_access_token(user_id, kwargs)


def create_refresh_token(user_id: str, **kwargs: Any) -> str:
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
) -> None:
    """Configure auth services."""
    global JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, REDIS_URL
    global jwt_service, session_manager, oauth_service, api_key_service

    # Dynamic configuration requires "constant" reassignment
    if jwt_secret is not None:
        JWT_SECRET = jwt_secret
    if jwt_algorithm is not None:
        JWT_ALGORITHM = jwt_algorithm
    if access_token_expire_minutes is not None:
        ACCESS_TOKEN_EXPIRE_MINUTES = access_token_expire_minutes
    if refresh_token_expire_days is not None:
        REFRESH_TOKEN_EXPIRE_DAYS = refresh_token_expire_days
    if redis_url is not None:
        REDIS_URL = redis_url

    # Recreate services with new config
    jwt_service = JWTService(JWT_SECRET, JWT_ALGORITHM)
    session_manager = SessionManager(REDIS_URL)
    oauth_service = OAuthService()
    api_key_service = APIKeyService(REDIS_URL)

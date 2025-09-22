"""
Authentication manager for WebSocket connections.
"""

import asyncio

import time
from typing import Any, Optional

import aiohttp

from .types import AuthResult, UserInfo

from dotmac.platform.logging import get_logger
logger = get_logger(__name__)

# Try to import JWT support (optional dependency)
try:
    import jwt

    JWT_AVAILABLE = True
except ImportError:
    jwt = None
    JWT_AVAILABLE = False

class AuthManager:
    """Manages WebSocket authentication."""

    def __init__(self, config):
        self.config = config
        self._user_cache: dict[str, tuple[UserInfo, float]] = {}  # user_id -> (info, expire_time)
        self._token_cache: dict[str, tuple[AuthResult, float]] = (
            {}
        )  # token -> (result, expire_time)

        if config.require_token and not JWT_AVAILABLE:
            logger.warning("JWT authentication required but PyJWT not available")

    async def authenticate_token(self, token: str) -> AuthResult:
        """Authenticate a JWT token."""
        if not self.config.enabled:
            return AuthResult.success_result(
                UserInfo(user_id="anonymous", tenant_id=self.config.default_tenant_id)
            )

        # Check cache first
        if token in self._token_cache:
            cached_result, expire_time = self._token_cache[token]
            if time.time() < expire_time:
                return cached_result
            else:
                # Remove expired entry
                del self._token_cache[token]

        try:
            if not JWT_AVAILABLE:
                return AuthResult.failure_result("JWT library not available")

            if not self.config.jwt_secret_key:
                return AuthResult.failure_result("JWT secret not configured")

            # Decode JWT token
            payload = jwt.decode(
                token, self.config.jwt_secret_key, algorithms=[self.config.jwt_algorithm]
            )

            # Extract user information
            user_id = payload.get("sub") or payload.get("user_id")
            if not user_id:
                return AuthResult.failure_result("Token missing user ID")

            user_info = UserInfo(
                user_id=str(user_id),
                username=payload.get("username"),
                email=payload.get("email"),
                tenant_id=payload.get("tenant_id"),
                roles=payload.get("roles", []),
                permissions=payload.get("permissions", []),
                extra_data={
                    k: v
                    for k, v in payload.items()
                    if k
                    not in [
                        "sub",
                        "user_id",
                        "username",
                        "email",
                        "tenant_id",
                        "roles",
                        "permissions",
                        "exp",
                        "iat",
                        "iss",
                    ]
                },
            )

            # Check required permissions
            if self.config.require_permissions:
                missing_perms = [
                    perm
                    for perm in self.config.require_permissions
                    if not user_info.has_permission(perm)
                ]
                if missing_perms:
                    return AuthResult.failure_result(f"Missing permissions: {missing_perms}")

            result = AuthResult.success_result(
                user_info,
                token_type="jwt",
                expires_at=payload.get("exp"),
                auth_method="jwt",  # nosec B106
            )

            # Cache result
            cache_ttl = min(
                self.config.user_cache_ttl_seconds,
                (payload.get("exp", time.time() + 3600) - time.time()),
            )
            if cache_ttl > 0:
                self._token_cache[token] = (result, time.time() + cache_ttl)

            return result

        except jwt.ExpiredSignatureError:
            return AuthResult.failure_result("Token expired")
        except jwt.InvalidTokenError as e:
            return AuthResult.failure_result(f"Invalid token: {e}")
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return AuthResult.failure_result("Authentication failed")

    async def authenticate_api_key(self, api_key: str) -> AuthResult:
        """Authenticate using API key.

        API keys are validated against:
        1. Static keys in configuration
        2. External API key service (if configured)
        3. Database (if available)
        """
        if not self.config.enabled:
            return AuthResult.success_result(
                UserInfo(user_id="api-anonymous", tenant_id=self.config.default_tenant_id)
            )

        # Check cache first
        cache_key = f"api:{api_key}"
        if cache_key in self._token_cache:
            cached_result, expire_time = self._token_cache[cache_key]
            if time.time() < expire_time:
                return cached_result
            else:
                del self._token_cache[cache_key]

        try:
            # 1. Check static API keys from configuration
            if hasattr(self.config, 'api_keys') and self.config.api_keys:
                result = self._validate_static_api_key(api_key)
                if result.is_authenticated:
                    # Cache successful result
                    self._token_cache[cache_key] = (
                        result,
                        time.time() + self.config.user_cache_ttl_seconds
                    )
                    return result

            # 2. Check external API key service
            if hasattr(self.config, 'api_key_validator_url') and self.config.api_key_validator_url:
                result = await self._validate_api_key_external(api_key)
                if result.is_authenticated:
                    # Cache successful result
                    self._token_cache[cache_key] = (
                        result,
                        time.time() + self.config.user_cache_ttl_seconds
                    )
                    return result

            # 3. Check database (if API key service is available)
            result = await self._validate_api_key_database(api_key)
            if result.is_authenticated:
                # Cache successful result
                self._token_cache[cache_key] = (
                    result,
                    time.time() + self.config.user_cache_ttl_seconds
                )
                return result

            return AuthResult.failure_result("Invalid API key")

        except Exception as e:
            logger.error(f"API key authentication error: {e}")
            return AuthResult.failure_result("API key authentication failed")

    def _validate_static_api_key(self, api_key: str) -> AuthResult:
        """Validate API key against static configuration."""
        if not hasattr(self.config, 'api_keys'):
            return AuthResult.failure_result("No API keys configured")

        for key_config in self.config.api_keys:
            if isinstance(key_config, dict):
                if key_config.get('key') == api_key:
                    # Found matching key
                    user_info = UserInfo(
                        user_id=key_config.get('user_id', f"api-{api_key[:8]}"),
                        username=key_config.get('username', 'api-user'),
                        tenant_id=key_config.get('tenant_id', self.config.default_tenant_id),
                        roles=key_config.get('roles', []),
                        permissions=key_config.get('permissions', []),
                        extra_data={
                            'api_key_name': key_config.get('name', 'unnamed'),
                            'api_key_id': key_config.get('id', api_key[:8])
                        }
                    )
                    return AuthResult.success_result(
                        user_info,
                        token_type="api_key",
                        auth_method="api_key"
                    )
            elif api_key == key_config:  # Simple string comparison
                user_info = UserInfo(
                    user_id=f"api-{api_key[:8]}",
                    tenant_id=self.config.default_tenant_id
                )
                return AuthResult.success_result(
                    user_info,
                    token_type="api_key",
                    auth_method="api_key"
                )

        return AuthResult.failure_result("API key not found")

    async def _validate_api_key_external(self, api_key: str) -> AuthResult:
        """Validate API key via external HTTP service."""
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = self.config.api_key_validator_url
                headers = {'X-API-Key': api_key}

                async with session.post(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        user_info = UserInfo(
                            user_id=data.get('user_id', f"api-{api_key[:8]}"),
                            username=data.get('username'),
                            email=data.get('email'),
                            tenant_id=data.get('tenant_id', self.config.default_tenant_id),
                            roles=data.get('roles', []),
                            permissions=data.get('permissions', []),
                            extra_data=data.get('metadata', {})
                        )
                        return AuthResult.success_result(
                            user_info,
                            token_type="api_key",
                            expires_at=data.get('expires_at'),
                            auth_method="api_key"
                        )
                    else:
                        return AuthResult.failure_result(f"API key validation failed: {response.status}")

        except asyncio.TimeoutError:
            logger.warning("API key validation timed out")
            return AuthResult.failure_result("API key validation timeout")
        except Exception as e:
            logger.error(f"External API key validation error: {e}")
            return AuthResult.failure_result("External validation failed")

    async def _validate_api_key_database(self, api_key: str) -> AuthResult:
        """Validate API key against database.

        This would integrate with the platform's API key service.
        """
        try:
            # Try to import the API key service if available
            from ...auth.api_keys import APIKeyService

            # This would need proper database session injection
            # For now, return not implemented
            return AuthResult.failure_result("Database API key validation not configured")

        except ImportError:
            # API key service not available
            return AuthResult.failure_result("API key service not available")

    async def resolve_user(self, user_id: str) -> Optional[UserInfo]:
        """Resolve user information by ID."""
        # Check cache first
        if user_id in self._user_cache:
            user_info, expire_time = self._user_cache[user_id]
            if time.time() < expire_time:
                return user_info
            else:
                # Remove expired entry
                del self._user_cache[user_id]

        # Try to resolve via external service
        if self.config.user_resolver_url:
            try:
                user_info = await self._resolve_user_external(user_id)
                if user_info:
                    # Cache result
                    expire_time = time.time() + self.config.user_cache_ttl_seconds
                    self._user_cache[user_id] = (user_info, expire_time)
                    return user_info
            except Exception as e:
                logger.error(f"Error resolving user {user_id}: {e}")

        return None

    async def _resolve_user_external(self, user_id: str) -> Optional[UserInfo]:
        """Resolve user via external HTTP service."""
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = f"{self.config.user_resolver_url.rstrip('/')}/users/{user_id}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return UserInfo(
                            user_id=data["user_id"],
                            username=data.get("username"),
                            email=data.get("email"),
                            tenant_id=data.get("tenant_id"),
                            roles=data.get("roles", []),
                            permissions=data.get("permissions", []),
                            extra_data=data.get("extra_data", {}),
                        )
                    else:
                        logger.warning(
                            f"User resolver returned status {response.status} for user {user_id}"
                        )

        except asyncio.TimeoutError:
            logger.warning(f"User resolver timeout for user {user_id}")
        except Exception as e:
            logger.error(f"User resolver error for user {user_id}: {e}")

        return None

    def extract_token_from_headers(self, headers: dict[str, str]) -> Optional[str]:
        """Extract token from request headers."""
        auth_header = headers.get(self.config.token_header, "")

        if auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer " prefix
        elif auth_header.startswith("Token "):
            return auth_header[6:]  # Remove "Token " prefix
        elif auth_header:
            return auth_header  # Use as-is

        return None

    def extract_token_from_query(self, query_params: dict[str, str]) -> Optional[str]:
        """Extract token from query parameters."""
        return query_params.get(self.config.token_query_param)

    async def validate_websocket_auth(self, websocket, path: str) -> AuthResult:
        """Validate authentication for WebSocket connection.

        Supports multiple authentication methods:
        1. JWT Bearer token in Authorization header
        2. API key in X-API-Key header
        3. Token in query parameters
        4. API key in query parameters
        """
        if not self.config.enabled:
            return AuthResult.success_result(UserInfo(user_id="anonymous", tenant_id="default"))

        # Extract authentication credentials
        token = None
        api_key = None
        headers = {}
        query_params = {}

        # Extract headers
        if hasattr(websocket, "request_headers"):
            headers = {k: v for k, v in websocket.request_headers.raw}

            # Check for JWT token in Authorization header
            token = self.extract_token_from_headers(headers)

            # Check for API key in X-API-Key header
            api_key = headers.get('X-API-Key') or headers.get('x-api-key')

        # Extract query parameters
        if hasattr(websocket, "path"):
            try:
                from urllib.parse import parse_qs, urlparse

                parsed_url = urlparse(websocket.path)
                query_params = {k: v[0] for k, v in parse_qs(parsed_url.query).items()}

                # Check for token in query params if not in headers
                if not token:
                    token = self.extract_token_from_query(query_params)

                # Check for API key in query params if not in headers
                if not api_key:
                    api_key = query_params.get('api_key') or query_params.get('apikey')

            except Exception:
                # Ignore query parsing errors
                pass  # nosec B110

        # Prioritize authentication methods
        # 1. Try API key first (if provided)
        if api_key:
            result = await self.authenticate_api_key(api_key)
            if result.is_authenticated:
                logger.info(f"WebSocket authenticated via API key for user: {result.user_info.user_id}")
                return result
            # Continue to try token if API key fails

        # 2. Try JWT token
        if token:
            result = await self.authenticate_token(token)
            if result.is_authenticated:
                logger.info(f"WebSocket authenticated via JWT for user: {result.user_info.user_id}")
                return result

        # 3. Check if authentication is required
        if self.config.require_token:
            return AuthResult.failure_result("Authentication required (provide JWT token or API key)")
        else:
            # Allow anonymous connection
            logger.info("WebSocket connection allowed as anonymous")
            return AuthResult.success_result(UserInfo(user_id="anonymous", tenant_id="default"))

    def cleanup_cache(self):
        """Clean up expired cache entries."""
        current_time = time.time()

        # Clean token cache
        expired_tokens = [
            token
            for token, (_, expire_time) in self._token_cache.items()
            if expire_time < current_time
        ]
        for token in expired_tokens:
            del self._token_cache[token]

        # Clean user cache
        expired_users = [
            user_id
            for user_id, (_, expire_time) in self._user_cache.items()
            if expire_time < current_time
        ]
        for user_id in expired_users:
            del self._user_cache[user_id]

        if expired_tokens or expired_users:
            logger.debug(
                f"Cleaned up {len(expired_tokens)} expired tokens and {len(expired_users)} expired users"
            )

    def get_stats(self) -> dict[str, Any]:
        """Get authentication manager statistics."""
        return {
            "enabled": self.config.enabled,
            "require_token": self.config.require_token,
            "cached_tokens": len(self._token_cache),
            "cached_users": len(self._user_cache),
            "jwt_available": JWT_AVAILABLE,
            "user_resolver_configured": bool(self.config.user_resolver_url),
        }

"""
DotMac Platform Auth Services

Comprehensive authentication and authorization services including:
- JWT token management (access/refresh tokens, RS256/HS256)
- Role-Based Access Control (RBAC) engine
- Multi-factor authentication (TOTP, SMS, Email)
- Session management with Redis backend
- Edge JWT validation with sensitivity patterns
- Service-to-service authentication
- API key management
- OAuth2/OIDC provider integration

Design Principles:
- Production-ready with battle-tested components
- Extensible with plugin architecture
- Multi-tenant aware
- Security-first approach
- DRY leveraging dotmac-core utilities
"""

import contextlib
import warnings
from typing import Any, Protocol, runtime_checkable
import base64
import hashlib
import hmac
import json
import secrets

from .cache_config import CacheConfig

try:
    from .jwt_service import JWTService, create_jwt_service_from_config

    _jwt_available = True
except ImportError as e:
    warnings.warn(f"JWT service not available: {e}", stacklevel=2)
    JWTService = None
    create_jwt_service_from_config = None
    _jwt_available = False

try:
    from .rbac_engine import Permission, RBACEngine, Role, create_rbac_engine

    _rbac_available = True
except ImportError as e:
    warnings.warn(f"RBAC engine not available: {e}", stacklevel=2)
    RBACEngine = Role = Permission = create_rbac_engine = None
    _rbac_available = False

try:
    from .session_manager import (
        MemorySessionBackend,
        RedisSessionBackend,
        SessionBackend,
        SessionManager,
    )

    _session_available = True
except ImportError as e:
    warnings.warn(f"Session management not available: {e}", stacklevel=2)
    SessionManager = SessionBackend = RedisSessionBackend = MemorySessionBackend = None
    _session_available = False

try:
    from .mfa_service import (
        EmailProvider,
        MFAEnrollmentRequest,
        MFAMethod,
        MFAService,
        MFAServiceConfig,
        MFAStatus,
        MFAVerificationRequest,
        SMSProvider,
        TOTPSetupResponse,
        extract_mfa_claims,
        is_mfa_required_for_scope,
        is_mfa_token_valid,
    )

    _mfa_available = True
except ImportError as e:
    warnings.warn(f"MFA service not available: {e}", stacklevel=2)
    MFAService = MFAServiceConfig = MFAEnrollmentRequest = MFAVerificationRequest = None
    MFAMethod = MFAStatus = TOTPSetupResponse = SMSProvider = EmailProvider = None
    extract_mfa_claims = is_mfa_required_for_scope = is_mfa_token_valid = None
    _mfa_available = False

try:
    from .edge_validation import (
        COMMON_SENSITIVITY_PATTERNS,
        DEVELOPMENT_PATTERNS,
        PRODUCTION_PATTERNS,
        EdgeAuthMiddleware,
        EdgeJWTValidator,
        SensitivityLevel,
        create_edge_validator,
    )

    _edge_validation_available = True
except ImportError as e:
    warnings.warn(f"Edge validation not available: {e}", stacklevel=2)
    EdgeJWTValidator = EdgeAuthMiddleware = SensitivityLevel = None
    # Do not reassign imported constants in except path to avoid pyright constant redefinition
    # COMMON_SENSITIVITY_PATTERNS, DEVELOPMENT_PATTERNS, PRODUCTION_PATTERNS are not reassigned
    create_edge_validator = None
    _edge_validation_available = False

try:
    from .service_auth import (
        ServiceAuthMiddleware,
        ServiceIdentity,
        ServiceTokenManager,
        create_service_token_manager,
    )

    _service_auth_available = True
except ImportError as e:
    warnings.warn(f"Service auth not available: {e}", stacklevel=2)
    ServiceIdentity = ServiceTokenManager = ServiceAuthMiddleware = None
    create_service_token_manager = None
    _service_auth_available = False

# Compatibility aliases for service_tokens
with contextlib.suppress(ImportError):
    from .service_auth import (
        ServiceAuthMiddleware,
    )

try:
    from .current_user import (
        RequireAdmin,
        RequireAdminAccess,
        RequireAdminRole,
        RequireAuthenticated,
        RequireModeratorRole,
        RequireReadAccess,
        RequireUserRole,
        RequireWriteAccess,
        ServiceClaims,
        UserClaims,
        get_current_service,
        get_current_tenant,
        get_current_user,
        get_optional_user,
        require_admin,
        require_roles,
        require_scopes,
        require_service_operation,
        require_tenant_access,
    )

    _current_user_available = True
except ImportError as e:
    warnings.warn(f"Current user dependencies not available: {e}", stacklevel=2)
    UserClaims = ServiceClaims = get_current_user = get_current_tenant = None
    get_current_service = get_optional_user = require_scopes = require_roles = None
    require_admin = require_tenant_access = require_service_operation = None
    RequireAuthenticated = RequireAdmin = RequireReadAccess = RequireWriteAccess = None
    RequireAdminAccess = RequireUserRole = RequireModeratorRole = RequireAdminRole = None
    _current_user_available = False

try:
    from .api_keys import (
        APIKeyCreateRequest,
        APIKeyCreateResponse,
        APIKeyResponse,
        APIKeyScope,
        APIKeyService,
        APIKeyServiceConfig,
        APIKeyStatus,
        APIKeyUpdateRequest,
        RateLimitWindow,
        api_key_required,
        check_api_rate_limit,
    )

    _api_keys_available = True
except ImportError as e:
    warnings.warn(f"API keys not available: {e}", stacklevel=2)
    APIKeyService = APIKeyServiceConfig = APIKeyCreateRequest = APIKeyUpdateRequest = None
    APIKeyResponse = APIKeyCreateResponse = APIKeyScope = APIKeyStatus = RateLimitWindow = None
    api_key_required = check_api_rate_limit = None
    _api_keys_available = False

try:
    from .oauth_providers import (
        PROVIDER_CONFIGS,
        OAuthAuthorizationRequest,
        OAuthCallbackRequest,
        OAuthProvider,
        OAuthService,
        OAuthServiceConfig,
        OAuthTokenResponse,
        OAuthUserInfo,
        generate_oauth_state,
        generate_pkce_pair,
        setup_oauth_provider,
    )

    _oauth_available = True
except ImportError as e:
    warnings.warn(f"OAuth providers not available: {e}", stacklevel=2)
    OAuthService = OAuthServiceConfig = OAuthAuthorizationRequest = OAuthCallbackRequest = None
    OAuthProvider = OAuthTokenResponse = OAuthUserInfo = None
    setup_oauth_provider = generate_oauth_state = generate_pkce_pair = None
    # Do not reassign PROVIDER_CONFIGS constant in except block
    _oauth_available = False

# Exception handling
try:
    from .exceptions import (
        AuthError,
        ConfigurationError,
        InsufficientRole,
        InsufficientScope,
        InvalidAlgorithm,
        InvalidAudience,
        InvalidIssuer,
        InvalidServiceToken,
        InvalidSignature,
        InvalidToken,
        ServiceTokenError,
        TenantMismatch,
        TokenError,
        TokenExpired,
        TokenNotFound,
        UnauthorizedService,
        get_http_status,
    )

    _exceptions_available = True
except ImportError as e:
    warnings.warn(f"Auth exceptions not available: {e}", stacklevel=2)
    AuthError = TokenError = TokenExpired = TokenNotFound = InvalidToken = None
    InvalidSignature = InvalidAlgorithm = InvalidAudience = InvalidIssuer = None
    InsufficientScope = InsufficientRole = TenantMismatch = ServiceTokenError = None
    UnauthorizedService = InvalidServiceToken = ConfigurationError = None
    get_http_status = None
    _exceptions_available = False


# Factory functions for creating services
def create_mfa_service(config: dict[str, Any] = None) -> Any:
    """Create MFA service instance."""
    if not _mfa_available:
        raise ImportError("MFA service not available")
    if config is None:
        config = {}
    return MFAService(MFAServiceConfig(**config))


def create_oauth_service(config: dict[str, Any] = None) -> Any:
    """Create OAuth service instance."""
    if not _oauth_available:
        raise ImportError("OAuth service not available")
    if config is None:
        config = {}
    return OAuthService(OAuthServiceConfig(**config))


def create_api_key_service(config: dict[str, Any] = None) -> Any:
    """Create API key service instance."""
    if not _api_keys_available:
        raise ImportError("API key service not available")
    if config is None:
        config = {}
    return APIKeyService(APIKeyServiceConfig(**config))


def create_session_manager(config: dict[str, Any] = None) -> Any:
    """Create session manager instance."""
    if not _session_available:
        raise ImportError("Session manager not available")
    if config is None:
        config = {}
    return SessionManager(config)


# Typed protocols for optional services
@runtime_checkable
class JWTServiceProtocol(Protocol):
    """Protocol for JWT service implementations."""

    def create_access_token(self, data: dict[str, Any]) -> str:
        ...

    def verify_token(self, token: str) -> dict[str, Any]:
        ...


@runtime_checkable
class RBACEngineProtocol(Protocol):
    """Protocol for RBAC engine implementations."""

    def check_permission(self, user_roles: list[str], required_permission: str) -> bool:
        ...

    def add_role(self, role_name: str, permissions: list[str]) -> None:
        ...


@runtime_checkable
class SessionManagerProtocol(Protocol):
    """Protocol for session manager implementations."""

    async def create_session(self, user_id: str, data: dict[str, Any]) -> str:
        ...

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        ...

    async def delete_session(self, session_id: str) -> bool:
        ...


# Service initialization and management
_auth_service_registry: dict[str, Any] = {}


def initialize_auth_service(config: dict[str, Any]) -> None:
    """Initialize authentication services with configuration.

    Supports both nested config structure (recommended):
        config = {"auth": {"jwt": {"secret_key": "..."}}, ...}

    And flat structure (legacy):
        config = {"jwt_secret_key": "...", ...}
    """
    # Normalize config structure - prefer nested auth config
    auth_config = config.get("auth", {})

    # Handle legacy flat config with deprecation warning
    if "jwt_secret_key" in config and not auth_config.get("jwt"):
        import warnings

        warnings.warn(
            "Flat auth config is deprecated. Use nested structure: "
            "config = {'auth': {'jwt': {'secret_key': '...'}}}",
            DeprecationWarning,
            stacklevel=2,
        )
        # Convert flat to nested format for internal use
        auth_config = {
            "jwt": {
                "secret_key": config["jwt_secret_key"],
                "algorithm": config.get("jwt_algorithm", "HS256"),
                "access_token_expire_minutes": config.get("jwt_expiration_minutes", 15),
            }
        }

    if _jwt_available and auth_config.get("jwt") and create_jwt_service_from_config is not None:
        jwt_service = create_jwt_service_from_config(auth_config["jwt"])
        _auth_service_registry["jwt"] = jwt_service

    if _rbac_available and create_rbac_engine is not None:
        rbac_engine = create_rbac_engine()
        _auth_service_registry["rbac"] = rbac_engine

    if _session_available:
        session_config = auth_config.get("sessions") or config.get("session") or {}
        backend_type = session_config.get("backend", "memory")

        if (
            backend_type == "redis"
            and isinstance(session_config, dict)
            and "redis_url" in session_config
            and RedisSessionBackend is not None
        ):
            backend = RedisSessionBackend(session_config["redis_url"])
        elif MemorySessionBackend is not None:
            backend = MemorySessionBackend()
        else:
            backend = None

        if backend is not None and SessionManager is not None:
            session_manager = SessionManager(backend)
            _auth_service_registry["sessions"] = session_manager

    if _mfa_available and "mfa" in auth_config and MFAServiceConfig is not None:
        # MFA requires JWT service and database session - skip if not available
        jwt_service = _auth_service_registry.get("jwt")
        if jwt_service:  # Only initialize MFA if JWT is available
            try:
                mfa_config = MFAServiceConfig(**auth_config["mfa"])
                # Note: MFA service requires database session which should be provided by caller
                # For now, we register the config for later instantiation
                _auth_service_registry["mfa_config"] = mfa_config
            except Exception:
                # Skip MFA initialization if config is invalid
                pass

    if _api_keys_available:
        try:
            from .api_keys import create_api_key_manager

            api_key_config = auth_config.get("api_keys", config.get("api_keys", {}))
            api_key_manager = create_api_key_manager(api_key_config)
            _auth_service_registry["api_keys"] = api_key_manager
        except ImportError:
            # API key manager not available
            pass


def get_auth_service(name: str) -> Any | None:
    """Get an initialized auth service."""
    return _auth_service_registry.get(name)


def is_auth_service_available(name: str) -> bool:
    """Check if auth service is available."""
    return name in _auth_service_registry


# Service availability helpers
def is_jwt_available() -> bool:
    """Check if JWT service is available and initialized."""
    return _jwt_available and "jwt" in _auth_service_registry


def is_rbac_available() -> bool:
    """Check if RBAC engine is available and initialized."""
    return _rbac_available and "rbac" in _auth_service_registry


def is_session_available() -> bool:
    """Check if session management is available and initialized."""
    return _session_available and "sessions" in _auth_service_registry


def is_mfa_available() -> bool:
    """Check if MFA service is available and initialized."""
    return _mfa_available and (
        "mfa" in _auth_service_registry or "mfa_config" in _auth_service_registry
    )


def is_api_keys_available() -> bool:
    """Check if API key service is available and initialized."""
    return _api_keys_available and "api_keys" in _auth_service_registry


def is_edge_validation_available() -> bool:
    """Check if edge validation is available."""
    return _edge_validation_available


def is_service_auth_available() -> bool:
    """Check if service auth is available."""
    return _service_auth_available


def get_platform_config(config: dict[str, Any]) -> dict[str, Any]:
    """Normalize and validate platform auth configuration.

    Args:
        config: Raw configuration dictionary

    Returns:
        Normalized configuration with proper structure

    Example:
        >>> config = get_platform_config({
        ...     "auth": {
        ...         "jwt": {"secret_key": "secret123"},
        ...         "sessions": {"backend": "redis", "redis_url": "redis://localhost"},
        ...         "mfa": {"enabled": True}
        ...     }
        ... })
    """
    auth_config = config.get("auth", {})

    # Validate JWT config
    jwt_config = auth_config.get("jwt", {})
    if jwt_config and "secret_key" in jwt_config:
        secret_key = jwt_config["secret_key"]
        if len(secret_key) < 32:
            import warnings

            warnings.warn(
                "JWT secret key should be at least 32 characters for security",
                UserWarning,
                stacklevel=2,
            )

    # Set secure defaults
    normalized = {
        "auth": {
            "jwt": {
                "algorithm": "HS256",
                "access_token_expire_minutes": 15,
                "refresh_token_expire_days": 7,
                **jwt_config,
            },
            "sessions": {
                "backend": "memory",
                "expire_minutes": 1440,  # 24 hours
                **auth_config.get("sessions", {}),
            },
            "mfa": {"enabled": False, "issuer_name": "DotMac", **auth_config.get("mfa", {})},
            "api_keys": {
                "default_rate_limit": 1000,
                "default_window": "hour",
                **auth_config.get("api_keys", {}),
            },
        }
    }

    return normalized


# FastAPI integration helpers
def add_auth_middleware(app, config: dict[str, Any] | None = None, service_name: str = "dotmac-platform") -> None:
    """Add authentication middleware to FastAPI app."""
    from fastapi import FastAPI

    if not isinstance(app, FastAPI):
        raise TypeError("app must be a FastAPI instance")

    config = config or {}

    # Add edge auth middleware if available
    if (
        _edge_validation_available
        and create_edge_validator is not None
        and EdgeAuthMiddleware is not None
        and "edge_patterns" in config
    ):
        edge_validator = create_edge_validator(
            jwt_service=get_auth_service("jwt"), patterns=config["edge_patterns"]
        )
        if edge_validator:
            app.add_middleware(EdgeAuthMiddleware, validator=edge_validator, service_name=service_name)

    # Add service auth middleware if available
    if _service_auth_available and ServiceAuthMiddleware is not None and "service_tokens" in config:
        service_manager = get_auth_service("service_tokens")
        if service_manager:
            app.add_middleware(ServiceAuthMiddleware, token_manager=service_manager, service_name=service_name)


# Utility functions for creating services
def create_complete_auth_system(config: dict[str, Any]):
    """Create a complete authentication system with all components."""
    components = {}

    if _jwt_available and create_jwt_service_from_config is not None:
        components["jwt"] = create_jwt_service_from_config(config.get("jwt", {}))

    if _rbac_available and create_rbac_engine is not None:
        components["rbac"] = create_rbac_engine()

    if _session_available:
        session_config = config.get("sessions", {})
        backend_type = session_config.get("backend", "memory")

        if backend_type == "redis" and RedisSessionBackend is not None:
            backend = RedisSessionBackend(session_config.get("redis_url", "redis://localhost:6379"))
        elif MemorySessionBackend is not None:
            backend = MemorySessionBackend()
        else:
            backend = None

        if backend is not None and SessionManager is not None:
            components["sessions"] = SessionManager(backend)

    # MFA requires runtime dependencies and DB; skip generic creation here

    # API Key manager requires DB; expose service factory elsewhere

    return components


# Version and metadata
__version__ = "1.0.0"
__author__ = "DotMac Team"
__email__ = "dev@dotmac.com"

# Export everything that's available
__all__ = [
    # Version
    "__version__",
    "add_auth_middleware",
    "create_complete_auth_system",
    "get_auth_service",
    # Service management
    "initialize_auth_service",
    "is_auth_service_available",
    # Availability helpers
    "is_jwt_available",
    "is_rbac_available",
    "is_session_available",
    "is_mfa_available",
    "is_api_keys_available",
    "is_edge_validation_available",
    "is_service_auth_available",
    # Configuration helpers
    "get_platform_config",
    # Configuration classes
    "CacheConfig",
    # Protocols
    "JWTServiceProtocol",
    "RBACEngineProtocol",
    "SessionManagerProtocol",
]

# Lightweight utility functions expected by tests
def constant_time_compare(a: str | bytes, b: str | bytes) -> bool:
    a_b = a.encode() if isinstance(a, str) else a
    b_b = b.encode() if isinstance(b, str) else b
    return hmac.compare_digest(a_b, b_b)


def encode_base64url(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode()
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def decode_base64url(data: str) -> str:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding).decode()


def generate_salt(length: int = 16) -> str:
    return secrets.token_hex(max(8, length // 2))


def generate_secure_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def hash_password(password: str, *, salt: str | None = None) -> str:
    salt = salt or generate_salt(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, hashed: str) -> bool:
    try:
        salt, _ = hashed.split("$", 1)
    except ValueError:
        return False
    return constant_time_compare(hash_password(password, salt=salt), hashed)


# Minimal middleware stubs expected by tests
class AuthMiddleware:  # pragma: no cover - simple stub
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...


class RBACMiddleware:  # pragma: no cover - simple stub
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...


class SessionMiddleware:  # pragma: no cover - simple stub
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...


def create_auth_middleware_stack() -> list[type]:  # pragma: no cover - simple stub
    return [AuthMiddleware, SessionMiddleware, RBACMiddleware]


# Config helpers and basic error utilities
def create_default_auth_config() -> dict[str, Any]:
    return {
        "jwt": {"algorithm": "HS256", "access_token_expire_minutes": 15, "refresh_token_expire_days": 7},
        "session": {"backend": "memory", "expire_minutes": 1440},
        "rbac": {"cache_enabled": True},
    }


def merge_auth_configs(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    def merge(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
        out = dict(a)
        for k, v in b.items():
            if isinstance(v, dict) and isinstance(out.get(k), dict):
                out[k] = merge(out[k], v)  # type: ignore[index]
            else:
                out[k] = v
        return out

    return merge(base, override)


def validate_auth_config(cfg: dict[str, Any]) -> bool:
    if not isinstance(cfg, dict):
        return False
    if "jwt" in cfg and not isinstance(cfg["jwt"], dict):
        return False
    if "session" in cfg and not isinstance(cfg["session"], dict):
        return False
    return True


def create_error_response(message: str, status_code: int = 400) -> dict[str, Any]:
    return {"status": status_code, "error": message}


def handle_auth_error(exc: Exception) -> dict[str, Any]:
    msg = str(exc)
    return create_error_response(f"auth_error: {msg}", status_code=401)


def log_security_event(event: str, **details: Any) -> str:
    return json.dumps({"event": event, **details})

# Add available components to exports
if _jwt_available:
    __all__.extend(
        [
            "JWTService",
            "create_jwt_service_from_config",
        ]
    )

if _rbac_available:
    __all__.extend(
        [
            "Permission",
            "RBACEngine",
            "Role",
            "create_rbac_engine",
        ]
    )

if _session_available:
    __all__.extend(
        [
            "MemorySessionBackend",
            "RedisSessionBackend",
            "SessionBackend",
            "SessionManager",
        ]
    )

if _mfa_available:
    __all__.extend(
        [
            "EmailProvider",
            "MFAEnrollmentRequest",
            "MFAMethod",
            "MFAService",
            "MFAServiceConfig",
            "MFAStatus",
            "MFAVerificationRequest",
            "SMSProvider",
            "TOTPSetupResponse",
            "extract_mfa_claims",
            "is_mfa_required_for_scope",
            "is_mfa_token_valid",
        ]
    )

if _edge_validation_available:
    __all__.extend(
        [
            "COMMON_SENSITIVITY_PATTERNS",
            "DEVELOPMENT_PATTERNS",
            "PRODUCTION_PATTERNS",
            "EdgeAuthMiddleware",
            "EdgeJWTValidator",
            "SensitivityLevel",
            "create_edge_validator",
        ]
    )

if _service_auth_available:
    __all__.extend(
        [
            "ServiceAuthMiddleware",
            "ServiceIdentity",
            "ServiceTokenManager",
            "create_service_token_manager",
        ]
    )

if _current_user_available:
    __all__.extend(
        [
            "RequireAdmin",
            "RequireAdminAccess",
            "RequireAdminRole",
            "RequireAuthenticated",
            "RequireModeratorRole",
            "RequireReadAccess",
            "RequireUserRole",
            "RequireWriteAccess",
            "ServiceClaims",
            "UserClaims",
            "get_current_service",
            "get_current_tenant",
            "get_current_user",
            "get_optional_user",
            "require_admin",
            "require_roles",
            "require_scopes",
            "require_service_operation",
            "require_tenant_access",
        ]
    )

if _api_keys_available:
    __all__.extend(
        [
            "APIKeyCreateRequest",
            "APIKeyCreateResponse",
            "APIKeyResponse",
            "APIKeyScope",
            "APIKeyService",
            "APIKeyServiceConfig",
            "APIKeyStatus",
            "APIKeyUpdateRequest",
            "RateLimitWindow",
            "api_key_required",
            "check_api_rate_limit",
        ]
    )

if _oauth_available:
    __all__.extend(
        [
            "PROVIDER_CONFIGS",
            "OAuthAuthorizationRequest",
            "OAuthCallbackRequest",
            "OAuthProvider",
            "OAuthService",
            "OAuthServiceConfig",
            "OAuthTokenResponse",
            "OAuthUserInfo",
            "generate_oauth_state",
            "generate_pkce_pair",
            "setup_oauth_provider",
        ]
    )

if _exceptions_available:
    __all__.extend(
        [
            "AuthError",
            "ConfigurationError",
            "InsufficientRole",
            "InsufficientScope",
            "InvalidAlgorithm",
            "InvalidAudience",
            "InvalidIssuer",
            "InvalidServiceToken",
            "InvalidSignature",
            "InvalidToken",
            "ServiceTokenError",
            "TenantMismatch",
            "TokenError",
            "TokenExpired",
            "TokenNotFound",
            "UnauthorizedService",
            "get_http_status",
        ]
    )

# Compatibility aliases for migration
if _current_user_available and get_current_user is not None:
    get_current_user_with_tenant = get_current_user  # Legacy alias
else:
    get_current_user_with_tenant = None

# Export new helpers added above
__all__.extend(
    [
        "constant_time_compare",
        "decode_base64url",
        "encode_base64url",
        "generate_salt",
        "generate_secure_token",
        "hash_password",
        "verify_password",
        "AuthMiddleware",
        "RBACMiddleware",
        "SessionMiddleware",
        "create_auth_middleware_stack",
        "create_default_auth_config",
        "merge_auth_configs",
        "validate_auth_config",
        "create_error_response",
        "handle_auth_error",
        "log_security_event",
    ]
)

"""
Edge JWT Validation

Edge validation system for request sensitivity patterns, middleware integration,
and tenant-aware authentication.
"""

import re
from collections.abc import Awaitable, Callable
from re import Pattern
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .exceptions import (
    AuthError,
    InsufficientRole,
    InsufficientScope,
    TenantMismatch,
    TokenNotFound,
    get_http_status,
)
from .jwt_service import JWTService


class SensitivityLevel:
    """Sensitivity levels for route protection"""

    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    SENSITIVE = "sensitive"
    ADMIN = "admin"
    INTERNAL = "internal"


class EdgeJWTValidator:
    """
    Edge JWT validator with configurable sensitivity patterns.

    Provides fine-grained control over authentication requirements based on
    request patterns (path, method, headers) and tenant context validation.
    """

    def __init__(
        self,
        jwt_service: JWTService,
        tenant_resolver: Callable[[Request], str | None] | None = None,
        default_sensitivity: str = SensitivityLevel.AUTHENTICATED,
        require_https: bool = True,
    ) -> None:
        """
        Initialize edge JWT validator.

        Args:
            jwt_service: JWT service for token validation
            tenant_resolver: Optional function to extract tenant from request
            default_sensitivity: Default sensitivity level
            require_https: Whether to require HTTPS in production
        """
        self.jwt_service = jwt_service
        self.tenant_resolver = tenant_resolver
        self.default_sensitivity = default_sensitivity
        self.require_https = require_https

        # Sensitivity patterns as raw strings (pattern, method) -> sensitivity
        self.sensitivity_patterns: list[tuple[str, str, str]] = []

        # Compiled patterns for better performance
        self._compiled_patterns: list[tuple[Pattern, Pattern, str]] = []

    def configure_sensitivity_patterns(self, patterns: dict[tuple[str, str], str]) -> None:
        """
        Configure sensitivity patterns for routes.

        Args:
            patterns: Dict mapping (path_regex, method_regex) to sensitivity level

        Example:
            {
                (r"/api/public/.*", r"GET|POST"): "public",
                (r"/api/admin/.*", r".*"): "admin",
                (r"/api/internal/.*", r".*"): "internal",
                (r"/health", r"GET"): "public",
            }
        """
        self.sensitivity_patterns = []
        self._compiled_patterns = []

        for (path_pattern, method_pattern), sensitivity in patterns.items():
            path_regex = re.compile(path_pattern, re.IGNORECASE)
            method_regex = re.compile(method_pattern, re.IGNORECASE)

            self.sensitivity_patterns.append((path_pattern, method_pattern, sensitivity))
            self._compiled_patterns.append((path_regex, method_regex, sensitivity))

    def add_sensitivity_pattern(
        self, path_pattern: str, method_pattern: str, sensitivity: str
    ) -> None:
        """
        Add a single sensitivity pattern.

        Args:
            path_pattern: Regex pattern for path matching
            method_pattern: Regex pattern for method matching
            sensitivity: Sensitivity level
        """
        path_regex = re.compile(path_pattern, re.IGNORECASE)
        method_regex = re.compile(method_pattern, re.IGNORECASE)

        self.sensitivity_patterns.append((path_pattern, method_pattern, sensitivity))
        self._compiled_patterns.append((path_regex, method_regex, sensitivity))

    def get_route_sensitivity(self, path: str, method: str) -> str:
        """
        Get sensitivity level for a route.

        Args:
            path: Request path
            method: Request method

        Returns:
            Sensitivity level
        """
        for path_regex, method_regex, sensitivity in self._compiled_patterns:
            if path_regex.match(path) and method_regex.match(method):
                return sensitivity

        return self.default_sensitivity

    def extract_token_from_request(self, request: Request) -> str | None:
        """
        Extract JWT token from request.

        Supports:
        - Authorization header (Bearer token)
        - Cookie-based tokens
        - Custom headers

        Args:
            request: FastAPI request object

        Returns:
            JWT token string or None
        """
        # Check Authorization header first
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer " prefix

        # Check for token in cookies
        token = request.cookies.get("access_token")
        if token:
            return token

        # Check custom headers
        token = request.headers.get("X-Auth-Token")
        if token:
            return token

        return None

    def extract_service_token(self, request: Request) -> str | None:
        """
        Extract service-to-service token from request.

        Args:
            request: FastAPI request object

        Returns:
            Service token string or None
        """
        # Service tokens typically come from X-Service-Token header
        return request.headers.get("X-Service-Token")

    async def validate(self, request: Request) -> dict[str, Any]:
        """
        Validate request authentication based on sensitivity patterns.

        Args:
            request: FastAPI request object

        Returns:
            User claims dictionary

        Raises:
            Various authentication exceptions
        """
        path = request.url.path
        method = request.method
        sensitivity = self.get_route_sensitivity(path, method)

        # Check HTTPS requirement
        if self.require_https and request.url.scheme != "https":
            # Allow HTTP for local development and health checks
            if not (
                (request.client and request.client.host in ["127.0.0.1", "localhost"])
                or path in ["/health", "/ready", "/metrics"]
            ):
                raise AuthError("HTTPS required", error_code="HTTPS_REQUIRED")

        # Public routes don't need authentication
        if sensitivity == SensitivityLevel.PUBLIC:
            return {"user_id": None, "scopes": [], "authenticated": False}

        # Internal routes require service tokens
        if sensitivity == SensitivityLevel.INTERNAL:
            return await self._validate_internal_request(request)

        # All other routes require user authentication
        return await self._validate_user_request(request, sensitivity)

    async def _validate_internal_request(self, request: Request) -> dict[str, Any]:
        """Validate internal service-to-service request"""
        service_token = self.extract_service_token(request)
        if not service_token:
            raise TokenNotFound("Service token required for internal endpoints")

        # This will be handled by service token manager
        # For now, return basic service claims
        return {
            "service_name": "unknown",
            "target_service": "current",
            "allowed_operations": [],
            "authenticated": True,
            "is_service": True,
        }

    async def _validate_user_request(self, request: Request, sensitivity: str) -> dict[str, Any]:
        """Validate user authentication request"""
        token = self.extract_token_from_request(request)
        if not token:
            raise TokenNotFound("Authentication token required")

        # Verify token
        try:
            claims = self.jwt_service.verify_token(token, expected_type="access")
        except Exception as e:
            if isinstance(e, AuthError):
                raise
            # Allow configuration errors to propagate
            if isinstance(e, (AttributeError, TypeError)):
                raise
            raise AuthError(f"Token validation failed: {e}") from e

        # Validate tenant context if resolver provided
        if self.tenant_resolver:
            expected_tenant = self.tenant_resolver(request)
            token_tenant = claims.get("tenant_id")

            if expected_tenant and token_tenant != expected_tenant:
                raise TenantMismatch(expected_tenant=expected_tenant, token_tenant=token_tenant)

        # Check sensitivity-specific requirements
        await self._check_sensitivity_requirements(claims, sensitivity)

        # Add authentication flag
        claims["authenticated"] = True
        claims["is_service"] = False

        return claims

    async def _check_sensitivity_requirements(
        self, claims: dict[str, Any], sensitivity: str
    ) -> None:
        """Check if claims meet sensitivity requirements"""
        user_scopes = claims.get("scopes", [])
        user_roles = claims.get("roles", [])

        if sensitivity == SensitivityLevel.AUTHENTICATED:
            # Just need valid token - already verified
            return

        if sensitivity == SensitivityLevel.SENSITIVE:
            # Require specific scopes for sensitive operations
            required_scopes = ["read:sensitive"]
            if not any(scope in user_scopes for scope in required_scopes):
                raise InsufficientScope(required_scopes=required_scopes, user_scopes=user_scopes)

        elif sensitivity == SensitivityLevel.ADMIN:
            # Require admin role or admin scopes
            admin_roles = ["admin", "super_admin"]
            admin_scopes = ["admin:read", "admin:write"]

            has_admin_role = any(role in user_roles for role in admin_roles)
            has_admin_scope = any(scope in user_scopes for scope in admin_scopes)

            if not (has_admin_role or has_admin_scope):
                raise InsufficientRole(required_roles=admin_roles, user_roles=user_roles)


class EdgeAuthMiddleware(BaseHTTPMiddleware):
    """
    Edge authentication middleware for FastAPI applications.

    Automatically validates requests based on configured sensitivity patterns
    and sets user claims in request state.
    """

    def __init__(
        self,
        app,
        validator: EdgeJWTValidator,
        service_name: str,
        skip_paths: list[str] | None = None,
        error_handler: Callable[[Request, AuthError], Awaitable[Response]] | None = None,
    ) -> None:
        """
        Initialize edge auth middleware.

        Args:
            app: FastAPI application
            validator: EdgeJWTValidator instance
            service_name: Name of the service
            skip_paths: Paths to skip authentication
            error_handler: Custom error handler
        """
        super().__init__(app)
        self.validator = validator
        self.service_name = service_name
        self.skip_paths = skip_paths or ["/docs", "/openapi.json", "/favicon.ico"]
        self.error_handler = error_handler or self._default_error_handler

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request through authentication middleware"""

        # Skip authentication for certain paths
        if any(request.url.path.startswith(path) for path in self.skip_paths):
            return await call_next(request)

        try:
            # Validate request
            claims = await self.validator.validate(request)

            # Store claims in request state
            request.state.user_claims = claims
            request.state.authenticated = claims.get("authenticated", False)

            # Downstream can access request.state for claims; do not mutate headers (immutable)

            # Continue to next middleware/route
            return await call_next(request)

        except AuthError as e:
            return await self.error_handler(request, e)

        except Exception as e:
            # Convert unexpected errors to ConfigurationError (500 status)
            from .exceptions import ConfigurationError
            auth_error = ConfigurationError(f"Authentication middleware error: {e}")
            return await self.error_handler(request, auth_error)

    async def _default_error_handler(self, request: Request, error: AuthError) -> Response:
        """Default error handler for authentication errors"""
        from starlette.responses import JSONResponse

        status_code = get_http_status(error)

        return JSONResponse(
            status_code=status_code,
            content=error.to_dict(),
            headers={"WWW-Authenticate": "Bearer", "X-Auth-Error": error.error_code},
        )


# Predefined sensitivity pattern sets
COMMON_SENSITIVITY_PATTERNS = {
    # Public endpoints
    (r"/health", r"GET"): SensitivityLevel.PUBLIC,
    (r"/ready", r"GET"): SensitivityLevel.PUBLIC,
    (r"/metrics", r"GET"): SensitivityLevel.PUBLIC,
    (r"/docs.*", r"GET"): SensitivityLevel.PUBLIC,
    (r"/openapi\.json", r"GET"): SensitivityLevel.PUBLIC,
    # Authentication endpoints
    (r"/api/v1/auth/login", r"POST"): SensitivityLevel.PUBLIC,
    (r"/api/v1/auth/register", r"POST"): SensitivityLevel.PUBLIC,
    (r"/api/v1/auth/refresh", r"POST"): SensitivityLevel.PUBLIC,
    # Admin endpoints
    (r"/api/v1/admin/.*", r".*"): SensitivityLevel.ADMIN,
    # Internal endpoints
    (r"/internal/.*", r".*"): SensitivityLevel.INTERNAL,
    # Sensitive data endpoints
    (r"/api/v1/.*/sensitive/.*", r".*"): SensitivityLevel.SENSITIVE,
    (r"/api/v1/billing/.*", r".*"): SensitivityLevel.SENSITIVE,
    (r"/api/v1/users/.*/personal/.*", r".*"): SensitivityLevel.SENSITIVE,
}

DEVELOPMENT_PATTERNS = {
    # More permissive patterns for development
    **COMMON_SENSITIVITY_PATTERNS,
    (r"/api/v1/debug/.*", r".*"): SensitivityLevel.PUBLIC,
    (r"/api/v1/test/.*", r".*"): SensitivityLevel.AUTHENTICATED,
}

PRODUCTION_PATTERNS = {
    # Stricter patterns for production
    **COMMON_SENSITIVITY_PATTERNS,
}


def create_edge_validator(
    jwt_service: JWTService,
    patterns: dict[tuple[str, str], str] | None = None,
    tenant_resolver: Callable[[Request], str | None] | None = None,
    environment: str = "production",
) -> EdgeJWTValidator:
    """
    Factory function to create edge validator with common patterns.

    Args:
        jwt_service: JWT service instance
        patterns: Custom sensitivity patterns
        tenant_resolver: Tenant resolution function
        environment: Environment ("development" or "production")

    Returns:
        Configured EdgeJWTValidator
    """
    validator = EdgeJWTValidator(
        jwt_service=jwt_service,
        tenant_resolver=tenant_resolver,
        require_https=(environment == "production"),
    )

    # Use appropriate default patterns
    if patterns is None:
        patterns = DEVELOPMENT_PATTERNS if environment == "development" else PRODUCTION_PATTERNS

    validator.configure_sensitivity_patterns(patterns)

    return validator

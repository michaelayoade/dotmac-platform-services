"""
Service-to-Service Token Management

Manages service authentication, token issuance, and inter-service authorization.
"""

import contextlib
import hashlib
import hmac
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .exceptions import (
    AuthError,
    ConfigurationError,
    InvalidServiceToken,
    TokenExpired,
    UnauthorizedService,
    get_http_status,
)

try:
    from .jwt_service import JWTService  # for test patching
except Exception:  # pragma: no cover
    JWTService = None  # type: ignore


class ServiceIdentity:
    """Represents a registered service identity"""

    def __init__(
        self,
        service_name: str,
        service_info: dict[str, Any],
        allowed_targets: list[str],
        allowed_operations: list[str],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.service_name = service_name
        self.service_info = service_info
        # Store as sets for efficient membership and consistent semantics
        self.allowed_targets = set(allowed_targets)
        self.allowed_operations = set(allowed_operations)
        self.metadata = metadata or {}
        self.created_at = datetime.now(UTC)
        self.identity_id = str(uuid.uuid4())

    def can_access_target(self, target_service: str) -> bool:
        """Check if service can access target service"""
        return target_service in self.allowed_targets or "*" in self.allowed_targets

    def can_perform_operation(self, operation: str) -> bool:
        """Check if service can perform operation"""
        return operation in self.allowed_operations or "*" in self.allowed_operations


class ServiceTokenManager:
    """
    Service-to-service token management.

    Handles service registration, token issuance, and verification for
    inter-service communication.
    """

    def __init__(
        self,
        signing_secret: str | None = None,
        keypair: tuple | None = None,
        algorithm: str = "HS256",
        default_token_expire_minutes: int = 60,
        secrets_provider=None,
    ) -> None:
        """
        Initialize service token manager.

        Args:
            signing_secret: Secret for HS256 signing
            keypair: (private_key, public_key) tuple for RS256
            algorithm: Signing algorithm ("HS256" or "RS256")
            default_token_expire_minutes: Default token expiration
            secrets_provider: Optional secrets provider
        """
        self.algorithm = algorithm
        self.default_token_expire_minutes = default_token_expire_minutes
        self.secrets_provider = secrets_provider

        # Service registry
        self.services: dict[str, ServiceIdentity] = {}

        # Initialize signing credentials
        if algorithm == "HS256":
            if not signing_secret and secrets_provider:
                with contextlib.suppress(Exception):
                    signing_secret = secrets_provider.get_service_signing_secret()

            if not signing_secret:
                raise ConfigurationError("HS256 requires signing_secret")

            self.signing_key = signing_secret
            self.verification_key = signing_secret

        elif algorithm == "RS256":
            if not keypair:
                raise ConfigurationError("RS256 requires keypair (private_key, public_key)")

            self.signing_key = keypair[0]
            self.verification_key = keypair[1]

        else:
            raise ConfigurationError(f"Unsupported algorithm: {algorithm}")

    def register_service(
        self,
        service_name: str,
        service_info: dict[str, Any],
        allowed_targets: list[str],
        allowed_operations: list[str] | None = None,
    ) -> ServiceIdentity:
        """
        Register a service identity.

        Args:
            service_name: Unique service name
            service_info: Service metadata (version, description, etc.)
            allowed_targets: List of services this service can call
            allowed_operations: List of operations this service can perform

        Returns:
            ServiceIdentity object
        """
        if not allowed_operations:
            allowed_operations = ["*"]  # Default to all operations

        identity = ServiceIdentity(
            service_name=service_name,
            service_info=service_info,
            allowed_targets=allowed_targets,
            allowed_operations=allowed_operations,
        )

        self.services[service_name] = identity
        return identity

    def get_service(self, service_name: str) -> ServiceIdentity | None:
        """Get registered service identity"""
        return self.services.get(service_name)

    def create_service_identity(
        self,
        service_name: str,
        version: str = "1.0.0",
        description: str = "",
        allowed_targets: list[str] | None = None,
        allowed_operations: list[str] | None = None,
    ) -> ServiceIdentity:
        """
        Convenience method to create and register service identity.

        Args:
            service_name: Service name
            version: Service version
            description: Service description
            allowed_targets: Target services
            allowed_operations: Allowed operations

        Returns:
            ServiceIdentity object
        """
        service_info = {
            "version": version,
            "description": description,
            "registered_at": datetime.now(UTC).isoformat(),
        }

        return self.register_service(
            service_name=service_name,
            service_info=service_info,
            allowed_targets=allowed_targets or [],
            allowed_operations=allowed_operations or ["*"],
        )

    def issue_service_token(
        self,
        service_identity: ServiceIdentity,
        target_service: str,
        allowed_operations: list[str] | None = None,
        tenant_context: str | None = None,
        expires_in: int | None = None,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        """
        Issue service-to-service token.

        Args:
            service_identity: Source service identity
            target_service: Target service name
            allowed_operations: Operations allowed with this token
            tenant_context: Optional tenant context
            expires_in: Token expiration in minutes
            extra_claims: Additional claims

        Returns:
            Encoded service token
        """
        # Validate service can access target
        if not service_identity.can_access_target(target_service):
            raise UnauthorizedService(
                f"Service {service_identity.service_name} not authorized "
                f"to access {target_service}",
                service_name=service_identity.service_name,
                target_service=target_service,
            )

        # Validate operations
        token_operations = allowed_operations or ["*"]
        for operation in token_operations:
            if operation != "*" and not service_identity.can_perform_operation(operation):
                raise UnauthorizedService(
                    f"Service {service_identity.service_name} not authorized "
                    f"for operation {operation}",
                    service_name=service_identity.service_name,
                    operation=operation,
                )

        # Create token claims
        now = datetime.now(UTC)
        expires_in = expires_in or self.default_token_expire_minutes
        exp = now + timedelta(minutes=expires_in)

        claims = {
            "iss": service_identity.service_name,
            "sub": service_identity.service_name,
            "aud": target_service,
            "iat": now,
            "exp": exp,
            "jti": str(uuid.uuid4()),
            "type": "service",
            "target_service": target_service,
            "allowed_operations": token_operations,
            "identity_id": service_identity.identity_id,
        }

        # Add optional claims
        if tenant_context:
            claims["tenant_id"] = tenant_context

        if extra_claims:
            claims.update(extra_claims)

        # Remove None values
        claims = {k: v for k, v in claims.items() if v is not None}

        try:
            return jwt.encode(claims, self.signing_key, algorithm=self.algorithm)
        except Exception as e:
            raise InvalidServiceToken(f"Failed to encode service token: {e}") from e

    def verify_service_token(
        self,
        token: str,
        expected_target: str | None = None,
        required_operations: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Verify service token.

        Args:
            token: Service token to verify
            expected_target: Expected target service
            required_operations: Operations that must be allowed

        Returns:
            Token claims
        """
        try:
            # Decode and verify token
            claims = jwt.decode(
                token,
                self.verification_key,
                algorithms=[self.algorithm],
                options={"verify_aud": False},  # We'll verify manually
            )

            # Verify token type
            if claims.get("type") != "service":
                raise InvalidServiceToken("Not a service token")

            # Verify target service if specified
            if expected_target and claims.get("target_service") != expected_target:
                raise UnauthorizedService(
                    f"Token not valid for service {expected_target}", target_service=expected_target
                )

            # Verify required operations
            if required_operations:
                token_operations = set(claims.get("allowed_operations", []))
                required_ops = set(required_operations)

                # Check if token allows all required operations
                if "*" not in token_operations and not required_ops.issubset(token_operations):
                    missing_ops = required_ops - token_operations
                    raise UnauthorizedService(
                        f"Token missing required operations: {missing_ops}",
                        service_name=claims.get("sub"),
                        operation=", ".join(missing_ops),
                    )

            # Verify service is still registered
            service_name = claims.get("sub")
            if service_name not in self.services:
                raise UnauthorizedService(
                    f"Service {service_name} no longer registered", service_name=service_name
                )

            return claims

        except jwt.ExpiredSignatureError:
            raise TokenExpired("Service token has expired")

        except jwt.InvalidSignatureError:
            raise InvalidServiceToken("Invalid service token signature")

        except jwt.InvalidTokenError as e:
            raise InvalidServiceToken(f"Service token validation failed: {e!s}") from e

        except Exception as e:
            if isinstance(e, UnauthorizedService | InvalidServiceToken | TokenExpired):
                raise
            raise InvalidServiceToken(f"Unexpected service token validation error: {e!s}") from e

    def revoke_service_tokens(self, service_name: str) -> None:
        """
        Revoke all tokens for a service (by removing from registry).

        Note: This is a simple implementation. In production, you might
        want a token blacklist or shorter token lifetimes.

        Args:
            service_name: Service to revoke tokens for
        """
        if service_name in self.services:
            del self.services[service_name]

    def list_services(self) -> list[str]:
        """List all registered service names"""
        return list(self.services.keys())

    def get_service_info(self, service_name: str) -> dict[str, Any] | None:
        """Get service information"""
        service = self.services.get(service_name)
        if not service:
            return None

        return {
            "service_name": service.service_name,
            "service_info": service.service_info,
            "allowed_targets": list(service.allowed_targets),
            "allowed_operations": list(service.allowed_operations),
            "created_at": service.created_at.isoformat(),
            "identity_id": service.identity_id,
            "metadata": service.metadata,
        }


class ServiceAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware for service-to-service authentication.

    Validates service tokens for internal endpoints and enforces
    operation-level authorization.
    """

    def __init__(
        self,
        app,
        token_manager: ServiceTokenManager,
        service_name: str,
        required_operations: list[str] | None = None,
        protected_paths: list[str] | None = None,
        error_handler: Callable[[Request, AuthError], Awaitable[Response]] | None = None,
        signing_secret: str | None = None,
        require_request_signature: bool = False,
    ) -> None:
        """
        Initialize service auth middleware.

        Args:
            app: FastAPI application
            token_manager: ServiceTokenManager instance
            service_name: Name of this service
            required_operations: Default required operations
            protected_paths: Paths that require service authentication
            error_handler: Custom error handler
        """
        super().__init__(app)
        self.token_manager = token_manager
        self.service_name = service_name
        self.required_operations = required_operations or []
        self.protected_paths = protected_paths or ["/internal"]
        self.error_handler = error_handler or self._default_error_handler
        self._signing_secret = signing_secret
        self._require_request_signature = require_request_signature

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request through service authentication"""

        # Check if path requires service authentication
        path = request.url.path
        requires_service_auth = any(
            path.startswith(protected_path) for protected_path in self.protected_paths
        )

        if not requires_service_auth:
            return await call_next(request)

        try:
            # Optional request signing verification
            if self._require_request_signature and self._signing_secret:
                sig = request.headers.get("X-Signature")
                ts = request.headers.get("X-Timestamp")
                body = await request.body()
                if (
                    not sig
                    or not ts
                    or not verify_request_signature(
                        self._signing_secret, sig, request.method, request.url.path, body, ts
                    )
                ):
                    raise InvalidServiceToken("Invalid request signature")

            # Extract service token
            service_token = request.headers.get("X-Service-Token")
            if not service_token:
                raise InvalidServiceToken("Service token required")

            # Verify token
            claims = self.token_manager.verify_service_token(
                service_token,
                expected_target=self.service_name,
                required_operations=self.required_operations,
            )

            # Store service claims in request state
            request.state.service_claims = claims
            request.state.service_authenticated = True
            request.state.calling_service = claims.get("sub")

            # Optionally surface caller in headers for downstream services (tests expect update call)
            if hasattr(request.headers, "update"):
                try:
                    request.headers.update({"X-Calling-Service": request.state.calling_service})
                except Exception:
                    pass

            return await call_next(request)

        except (InvalidServiceToken, UnauthorizedService, TokenExpired) as e:
            return await self.error_handler(request, e)

        except Exception as e:
            error = InvalidServiceToken(f"Service authentication error: {e}")
            return await self.error_handler(request, error)

    async def _default_error_handler(self, request: Request, error: AuthError) -> Response:
        """Default error handler for service authentication errors"""
        from starlette.responses import JSONResponse

        status_code = get_http_status(error)

        return JSONResponse(
            status_code=status_code,
            content=error.to_dict(),
            headers={"X-Service-Auth-Error": error.error_code},
        )


def create_service_token_manager(
    algorithm: str = "HS256",
    signing_secret: str | None = None,
    keypair: tuple | None = None,
    **kwargs,
) -> ServiceTokenManager:
    """
    Factory function to create service token manager.

    Args:
        algorithm: Signing algorithm
        signing_secret: Secret for HS256
        keypair: Keys for RS256
        **kwargs: Additional configuration

    Returns:
        Configured ServiceTokenManager
    """
    return ServiceTokenManager(
        algorithm=algorithm, signing_secret=signing_secret, keypair=keypair, **kwargs
    )


# Request signing utilities for service-to-service calls
def _canon(method: str, path: str, body: bytes, timestamp: str) -> bytes:
    return b"\n".join(
        [
            method.upper().encode(),
            path.encode(),
            timestamp.encode(),
            hashlib.sha256(body or b"").hexdigest().encode(),
        ]
    )


def sign_request(secret: str, method: str, path: str, body: bytes, timestamp: str) -> str:
    msg = _canon(method, path, body or b"", timestamp)
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()


def verify_request_signature(
    secret: str,
    signature: str,
    method: str,
    path: str,
    body: bytes,
    timestamp: str,
    max_skew_seconds: int = 300,
) -> bool:
    try:
        import time

        # Basic replay protection
        if abs(int(time.time()) - int(timestamp)) > max_skew_seconds:
            return False
        expected = sign_request(secret, method, path, body or b"", timestamp)
        return hmac.compare_digest(expected, signature)
    except Exception:
        return False

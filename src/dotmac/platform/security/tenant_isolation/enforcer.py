from dotmac.platform.observability.unified_logging import get_logger

"""
Tenant security enforcer for request-level tenant isolation.
"""

import base64
import hashlib
import hmac
import json
import time
from typing import Optional
from uuid import UUID

import structlog
from fastapi import HTTPException, Request, status

from .manager import TenantSecurityManager
from .models import TenantContext

logger = get_logger(__name__)

class TenantSecurityEnforcer:
    """Enhanced tenant security enforcer with multi-source validation."""

    def __init__(
        self,
        tenant_security_manager: Optional[TenantSecurityManager] = None,
        jwt_secret_key: Optional[str] = None,
    ):
        """Initialize tenant security enforcer.

        Args:
            tenant_security_manager: Tenant security manager for validation
            jwt_secret_key: Secret key for JWT validation
        """
        self.tenant_security = tenant_security_manager or TenantSecurityManager()
        self.jwt_secret_key = jwt_secret_key or "your-secret-key"  # Should come from config
        self.exempt_paths: set[str] = {
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/metrics",
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/refresh",
        }

    async def enforce_tenant_boundary(self, request: Request) -> Optional[TenantContext]:
        """Enforce tenant boundary with multi-source validation.

        Args:
            request: FastAPI request object

        Returns:
            TenantContext if valid, raises HTTPException if invalid
        """
        # Skip exempt paths
        if self._is_exempt_path(request.url.path):
            return None

        # Extract tenant context from multiple sources
        contexts = await self._extract_tenant_contexts(request)

        if not contexts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant context required but not found",
            )

        # Validate consistency across sources
        primary_context = await self._validate_context_consistency(contexts)

        # Store original JWT payload if available for additional context
        jwt_context = next((ctx for ctx in contexts if ctx.source == "jwt_token"), None)
        if jwt_context:
            try:
                auth_header = request.headers.get("Authorization", "")
                if auth_header.startswith("Bearer "):
                    token = auth_header[7:]
                    payload = self._decode_and_validate_jwt(token)
                    primary_context.jwt_payload = payload
            except Exception as e:
                logger.debug("Failed to store JWT payload context", error=str(e))

        # Validate against tenant manager
        if not await self.tenant_security.validate_tenant(primary_context.tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid tenant access"
            )

        # Gateway validation if available
        if await self._validate_gateway_header(request, primary_context.tenant_id):
            primary_context.gateway_validated = True

        primary_context.validated = True

        # Set request state
        request.state.tenant_context = primary_context
        request.state.tenant_id = primary_context.tenant_id

        return primary_context

    async def _extract_tenant_contexts(self, request: Request) -> list[TenantContext]:
        """Extract tenant contexts from all available sources."""
        contexts = []

        # 1. Gateway header (highest priority)
        gateway_tenant = self._extract_from_gateway_header(request)
        if gateway_tenant:
            contexts.append(TenantContext(tenant_id=gateway_tenant, source="gateway_header"))

        # 2. Container context
        container_tenant = self._extract_from_container_context(request)
        if container_tenant:
            contexts.append(TenantContext(tenant_id=container_tenant, source="container_context"))

        # 3. JWT token
        jwt_tenant = await self._extract_from_jwt(request)
        if jwt_tenant:
            contexts.append(TenantContext(tenant_id=jwt_tenant, source="jwt_token"))

        # 4. Subdomain
        subdomain_tenant = self._extract_from_subdomain(request)
        if subdomain_tenant:
            contexts.append(TenantContext(tenant_id=subdomain_tenant, source="subdomain"))

        return contexts

    def _extract_from_gateway_header(self, request: Request) -> Optional[str]:
        """Extract tenant ID from gateway header."""
        # Gateway should set X-Tenant-ID header
        tenant_id = request.headers.get("X-Tenant-ID") or request.headers.get("x-tenant-id")

        if tenant_id and self._is_valid_tenant_id(tenant_id):
            logger.debug("Tenant ID from gateway header", tenant_id=tenant_id)
            return tenant_id

        return None

    def _extract_from_container_context(self, request: Request) -> Optional[str]:
        """Extract tenant ID from container context."""
        # Container should set X-Container-Tenant header
        tenant_id = request.headers.get("X-Container-Tenant") or request.headers.get(
            "x-container-tenant"
        )

        if tenant_id and self._is_valid_tenant_id(tenant_id):
            logger.debug("Tenant ID from container context", tenant_id=tenant_id)
            return tenant_id

        return None

    async def _extract_from_jwt(self, request: Request) -> Optional[str]:
        """Extract tenant ID from JWT token."""
        try:
            authorization = request.headers.get("Authorization")
            if not authorization or not authorization.startswith("Bearer "):
                return None

            token = authorization[7:]  # Remove "Bearer " prefix

            # Decode and validate JWT
            payload = self._decode_and_validate_jwt(token)

            # Extract tenant_id from payload
            tenant_id = payload.get("tenant_id")

            if tenant_id:
                logger.debug("Successfully extracted tenant from JWT", tenant_id=tenant_id)
                return str(tenant_id)

            logger.debug("No tenant_id found in JWT payload")
            return None

        except Exception as e:
            logger.warning("Failed to extract tenant from JWT", error=str(e))
            return None

    def _decode_and_validate_jwt(self, token: str) -> dict:
        """Decode and validate JWT token."""
        try:
            # Split token into parts
            parts = token.split(".")
            if len(parts) != 3:
                raise ValueError("Invalid JWT format - must have 3 parts")

            header, payload, signature = parts

            # Decode header
            header_data = self._decode_base64_json(header)
            algorithm = header_data.get("alg")

            # Validate algorithm
            if algorithm not in ["HS256", "HS512"]:
                raise ValueError(f"Unsupported algorithm: {algorithm}")

            # Verify signature
            if not self._verify_jwt_signature(f"{header}.{payload}", signature, algorithm):
                raise ValueError("Invalid JWT signature")

            # Decode payload
            payload_data = self._decode_base64_json(payload)

            # Validate expiration
            if not self._is_token_valid(payload_data):
                raise ValueError("Token has expired")

            return payload_data

        except Exception as e:
            raise ValueError(f"JWT validation failed: {e}") from e

    def _decode_base64_json(self, data: str) -> dict:
        """Decode base64-encoded JSON data."""
        # Add padding if needed
        missing_padding = len(data) % 4
        if missing_padding:
            data += "=" * (4 - missing_padding)

        decoded_bytes = base64.urlsafe_b64decode(data)
        return json.loads(decoded_bytes.decode("utf-8"))

    def _verify_jwt_signature(self, message: str, signature: str, algorithm: str) -> bool:
        """Verify JWT signature."""
        try:
            if algorithm == "HS256":
                expected_signature = (
                    base64.urlsafe_b64encode(
                        hmac.new(
                            self.jwt_secret_key.encode("utf-8"),
                            message.encode("utf-8"),
                            hashlib.sha256,
                        ).digest()
                    )
                    .decode("utf-8")
                    .rstrip("=")
                )

            elif algorithm == "HS512":
                expected_signature = (
                    base64.urlsafe_b64encode(
                        hmac.new(
                            self.jwt_secret_key.encode("utf-8"),
                            message.encode("utf-8"),
                            hashlib.sha512,
                        ).digest()
                    )
                    .decode("utf-8")
                    .rstrip("=")
                )
            else:
                return False

            return hmac.compare_digest(signature, expected_signature)

        except Exception as e:
            logger.debug("JWT signature verification failed", error=str(e))
            return False

    def _is_token_valid(self, payload: dict) -> bool:
        """Check if token is still valid (not expired)."""
        exp = payload.get("exp")
        if not exp:
            return True  # No expiration claim

        try:
            exp_timestamp = int(exp)
            current_timestamp = int(time.time())

            # Add small buffer (30 seconds) for clock skew
            return current_timestamp <= (exp_timestamp + 30)

        except (ValueError, TypeError):
            logger.debug("Invalid exp claim format")
            return False

    def _extract_from_subdomain(self, request: Request) -> Optional[str]:
        """Extract tenant ID from subdomain."""
        try:
            host = request.headers.get("Host") or request.headers.get("host", "")
            if not host or "." not in host:
                return None

            subdomain = host.split(".")[0]

            # Validate subdomain format (could be tenant slug)
            if len(subdomain) >= 3 and subdomain.replace("-", "").replace("_", "").isalnum():
                # This might be a tenant slug - would need to resolve to tenant_id
                logger.debug("Potential tenant subdomain", subdomain=subdomain)
                return subdomain

        except Exception as e:
            logger.warning("Failed to extract tenant from subdomain", error=str(e))

        return None

    async def _validate_context_consistency(self, contexts: list[TenantContext]) -> TenantContext:
        """Validate consistency across tenant contexts and return primary."""
        if len(contexts) == 1:
            return contexts[0]

        # Priority order: gateway_header > container_context > jwt_token > subdomain
        priority_order = ["gateway_header", "container_context", "jwt_token", "subdomain"]

        # Find highest priority context
        primary_context = None
        for source in priority_order:
            for context in contexts:
                if context.source == source:
                    primary_context = context
                    break
            if primary_context:
                break

        if not primary_context:
            primary_context = contexts[0]

        # Validate all contexts match the primary
        for context in contexts:
            if context.tenant_id != primary_context.tenant_id:
                logger.error(
                    "Tenant context mismatch",
                    primary_source=primary_context.source,
                    primary_tenant=primary_context.tenant_id,
                    context_source=context.source,
                    context_tenant=context.tenant_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context mismatch detected"
                )

        return primary_context

    async def _validate_gateway_header(self, request: Request, tenant_id: str) -> bool:
        """Validate gateway header matches tenant."""
        gateway_tenant = request.headers.get("X-Tenant-ID") or request.headers.get("x-tenant-id")

        if not gateway_tenant:
            # No gateway header - might be direct access
            logger.debug("No gateway header present")
            return False

        if gateway_tenant != tenant_id:
            logger.error(
                "Gateway tenant mismatch", gateway_tenant=gateway_tenant, expected_tenant=tenant_id
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Gateway tenant validation failed"
            )

        return True

    def _is_valid_tenant_id(self, tenant_id: str) -> bool:
        """Validate tenant ID format."""
        if not tenant_id or len(tenant_id) < 3:
            return False

        try:
            # Try UUID format
            UUID(tenant_id)
            return True
        except ValueError:
            # Allow alphanumeric slugs
            return tenant_id.replace("-", "").replace("_", "").isalnum()

    def _is_exempt_path(self, path: str) -> bool:
        """Check if path is exempt from tenant enforcement."""
        return any(path.startswith(exempt_path) for exempt_path in self.exempt_paths)

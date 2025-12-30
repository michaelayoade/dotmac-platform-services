"""
OIDC Discovery Endpoints.

Provides RFC 8414 compliant endpoints for OpenID Connect discovery:
- /.well-known/jwks.json - JSON Web Key Set for token verification
- /.well-known/openid-configuration - OpenID Connect discovery document
"""

from typing import Any

import structlog
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .keys import get_key_manager

logger = structlog.get_logger(__name__)

# Router for OIDC discovery endpoints
# NOTE: This router should be registered at the app root (no prefix)
oidc_router = APIRouter(tags=["OIDC Discovery"])


@oidc_router.get(
    "/.well-known/jwks.json",
    response_class=JSONResponse,
    summary="JSON Web Key Set",
    description="Returns the public keys used to verify JWT signatures. "
    "External services use this endpoint to validate tokens issued by this platform.",
)
async def get_jwks() -> dict[str, list[dict[str, Any]]]:
    """Return JSON Web Key Set for token verification.

    The JWKS includes:
    - Current signing key (identified by 'kid')
    - Previous keys still in rotation window (for graceful key rotation)

    Returns:
        JWK Set with 'keys' array containing public keys in JWK format.
    """
    try:
        key_manager = get_key_manager()
        jwks = key_manager.get_jwks()

        logger.debug(
            "jwks.served",
            key_count=len(jwks.get("keys", [])),
        )

        return jwks
    except Exception as e:
        logger.error("jwks.error", error=str(e))
        # Return empty key set on error (service still available)
        return {"keys": []}


@oidc_router.get(
    "/.well-known/openid-configuration",
    response_class=JSONResponse,
    summary="OpenID Connect Discovery",
    description="Returns the OpenID Connect discovery document with metadata about this authorization server.",
)
async def get_openid_configuration(request: Request) -> dict[str, Any]:
    """Return OpenID Connect discovery document.

    Provides metadata for clients to discover:
    - Token endpoint location
    - JWKS URI for key retrieval
    - Supported algorithms and response types

    Returns:
        OpenID Provider Configuration Information.
    """
    try:
        from ..settings import settings

        # Determine base URL from request
        base_url = str(request.base_url).rstrip("/")

        # Build discovery document per RFC 8414
        config = {
            # Required metadata
            "issuer": settings.auth.jwt_issuer,
            "jwks_uri": f"{base_url}/.well-known/jwks.json",
            # Token endpoint
            "token_endpoint": f"{base_url}/api/v1/auth/token",
            # Supported features
            "response_types_supported": ["token"],
            "subject_types_supported": ["public"],
            "id_token_signing_alg_values_supported": [
                settings.auth.jwt_asymmetric_algorithm,
                "HS256",
            ],
            "token_endpoint_auth_methods_supported": [
                "client_secret_post",
                "client_secret_basic",
            ],
            # Claims supported
            "claims_supported": [
                "sub",
                "iss",
                "aud",
                "exp",
                "iat",
                "jti",
                "type",
                "roles",
                "permissions",
                "tenant_id",
            ],
            # Scopes supported
            "scopes_supported": ["openid", "profile", "email"],
        }

        logger.debug("openid_configuration.served", issuer=settings.auth.jwt_issuer)

        return config
    except Exception as e:
        logger.error("openid_configuration.error", error=str(e))
        # Return minimal config on error
        base_url = str(request.base_url).rstrip("/")
        return {
            "issuer": "dotmac-platform",
            "jwks_uri": f"{base_url}/.well-known/jwks.json",
        }

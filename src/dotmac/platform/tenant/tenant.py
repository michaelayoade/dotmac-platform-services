"""
Tenant identity resolution and middleware for single/multi-tenant applications.

Provides configurable tenant resolution supporting both:
- Single-tenant: Always uses default tenant ID
- Multi-tenant: Resolves from headers, query parameters, or state
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from .config import TenantConfiguration, get_tenant_config


class TenantIdentityResolver:
    """Resolve tenant identity from request based on configuration.

    In single-tenant mode: Always returns configured default tenant ID
    In multi-tenant mode: Resolves from header, query param, or state
    """

    def __init__(self, config: Optional[TenantConfiguration] = None):
        """Initialize resolver with configuration."""
        self.config = config or get_tenant_config()
        self.header_name = self.config.tenant_header_name
        self.query_param = self.config.tenant_query_param

    async def resolve(self, request: Request) -> str | None:
        """Resolve tenant ID based on configuration mode."""
        # Single-tenant mode: always return default
        if self.config.is_single_tenant:
            return self.config.default_tenant_id

        # Multi-tenant mode: resolve from request
        # Header
        try:
            tenant_id = request.headers.get(self.header_name)
            if tenant_id:
                return tenant_id
        except Exception:
            pass

        # Query param
        try:
            tenant_id = request.query_params.get(self.query_param)
            if tenant_id:
                return tenant_id
        except Exception:
            pass

        # Request state (set by upstream or router). Avoid Mock auto-creation.
        try:
            state = request.state
            state_dict = getattr(state, "__dict__", {})
            return state_dict.get("tenant_id") if isinstance(state_dict, dict) else None
        except Exception:
            return None


class TenantMiddleware(BaseHTTPMiddleware):
    """Populate request.state.tenant_id based on deployment configuration.

    Single-tenant mode: Always sets default tenant ID
    Multi-tenant mode: Resolves and validates tenant ID from request
    """

    def __init__(
        self,
        app: Any,
        config: Optional[TenantConfiguration] = None,
        resolver: Optional[TenantIdentityResolver] = None,
        exempt_paths: Optional[set[str]] = None,
        require_tenant: Optional[bool] = None,
    ) -> None:
        super().__init__(app)
        self.config = config or get_tenant_config()
        self.resolver = resolver or TenantIdentityResolver(self.config)
        self.exempt_paths = exempt_paths or {
            "/health",
            "/ready",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/login",  # Auth endpoints don't need tenant
            "/api/v1/auth/register",
        }
        # Override config's require_tenant if explicitly provided
        if require_tenant is not None:
            self.require_tenant = require_tenant
        else:
            self.require_tenant = self.config.require_tenant_header

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Any]]
    ) -> Any:
        """Process request and set tenant context."""
        # Skip tenant validation for exempt paths
        if request.url.path in self.exempt_paths:
            # In single-tenant mode, still set default tenant for consistency
            if self.config.is_single_tenant:
                request.state.tenant_id = self.config.default_tenant_id
            return await call_next(request)

        # Resolve tenant ID
        resolved_id = await self.resolver.resolve(request)

        # Get final tenant ID based on configuration
        tenant_id = self.config.get_tenant_id_for_request(resolved_id)

        if tenant_id:
            # Set tenant ID on request state
            request.state.tenant_id = tenant_id
        elif self.require_tenant:
            # Only raise error if tenant is required (multi-tenant mode)
            from fastapi import status
            from starlette.responses import JSONResponse

            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "detail": f"Tenant ID is required. Provide via {self.config.tenant_header_name} header or {self.config.tenant_query_param} query param."
                },
            )
        else:
            # Fall back to default if available
            request.state.tenant_id = self.config.default_tenant_id

        return await call_next(request)

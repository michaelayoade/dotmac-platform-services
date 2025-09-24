"""
Tenant identity resolution and middleware for multi-tenant applications.

Provides simple tenant resolution from request headers, query parameters, and state,
plus middleware to automatically set tenant context on requests.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class TenantIdentityResolver:
    """Resolve tenant identity from request.

    Order of resolution:
    - Header: X-Tenant-ID
    - Query param: tenant_id
    - Path state: request.state.tenant_id (if set by upstream middleware)
    """

    header_name: str = "X-Tenant-ID"
    query_param: str = "tenant_id"

    async def resolve(self, request: Request) -> str | None:
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
    """Populate request.state.tenant_id using TenantIdentityResolver."""

    def __init__(
        self,
        app: Any,
        resolver: TenantIdentityResolver | None = None,
        require_tenant: bool = True,
        exempt_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.resolver = resolver or TenantIdentityResolver()
        self.require_tenant = require_tenant
        self.exempt_paths = exempt_paths or {"/health", "/metrics", "/docs", "/openapi.json"}

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Any]]
    ) -> Any:
        # Skip tenant validation for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        tenant_id = await self.resolver.resolve(request)

        if tenant_id:
            # Set tenant ID on request state
            request.state.tenant_id = tenant_id
        elif self.require_tenant:
            # Require tenant ID for multi-tenant endpoints
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant ID is required. Provide via X-Tenant-ID header or tenant_id query param.",
            )

        return await call_next(request)

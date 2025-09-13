"""
Tenant middleware for setting tenant context on requests.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from .identity import TenantIdentityResolver


class TenantMiddleware(BaseHTTPMiddleware):
    """Populate request.state.tenant_id using TenantIdentityResolver."""

    def __init__(self, app: Any, resolver: TenantIdentityResolver | None = None) -> None:
        super().__init__(app)
        self.resolver = resolver or TenantIdentityResolver()

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Any]]
    ) -> Any:
        tenant_id = await self.resolver.resolve(request)
        if tenant_id:
            try:
                request.state.tenant_id = tenant_id
            except Exception:
                # Read-only or restricted state; ignore setting
                pass
        return await call_next(request)

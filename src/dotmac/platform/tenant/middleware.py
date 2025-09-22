"""
Tenant middleware for setting tenant context on requests.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

try:
    from fastapi import Request
    from starlette.middleware.base import BaseHTTPMiddleware
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    Request = None
    BaseHTTPMiddleware = object

from .identity import TenantIdentityResolver


if FASTAPI_AVAILABLE:
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
                # If request.state is None, surface error as tests expect
                if request.state is None:
                    raise AttributeError("request.state is None")
                # Attempt to set; allow AttributeError to propagate for read-only state
                request.state.tenant_id = tenant_id
            return await call_next(request)

else:
    class TenantMiddleware:
        """No-op middleware when FastAPI not available."""
        def __init__(self, *args, **kwargs):
            pass

        async def dispatch(self, request, call_next):
            return await call_next(request)
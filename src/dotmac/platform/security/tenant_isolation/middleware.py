from dotmac.platform.observability.unified_logging import get_logger

"""
FastAPI middleware for tenant security enforcement.
"""

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .enforcer import TenantSecurityEnforcer
from .manager import TenantSecurityManager

logger = get_logger(__name__)

class TenantSecurityMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for tenant security enforcement."""

    def __init__(
        self,
        app,
        enforcer: TenantSecurityEnforcer = None,
        manager: TenantSecurityManager = None,
    ):
        super().__init__(app)
        self.manager = manager or TenantSecurityManager()
        self.enforcer = enforcer or TenantSecurityEnforcer(self.manager)

    async def dispatch(self, request: Request, call_next):
        """Enforce tenant boundary for each request."""
        try:
            # Enforce tenant boundary
            tenant_context = await self.enforcer.enforce_tenant_boundary(request)

            # Process request
            response = await call_next(request)

            # Add tenant context to response headers for debugging
            if tenant_context:
                response.headers["X-Tenant-Context"] = (
                    f"{tenant_context.tenant_id}:{tenant_context.source}"
                )

            return response

        except Exception as e:
            logger.error("Tenant security middleware error", error=str(e))

            # Return appropriate error response
            if hasattr(e, "status_code"):
                return JSONResponse(
                    status_code=e.status_code,
                    content={"detail": str(e.detail) if hasattr(e, "detail") else str(e)},
                )
            else:
                return JSONResponse(
                    status_code=500, content={"detail": "Tenant security validation failed"}
                )

def add_tenant_security_middleware(
    app: FastAPI, enforcer: TenantSecurityEnforcer = None, manager: TenantSecurityManager = None
) -> None:
    """Add tenant security middleware to FastAPI app.

    Args:
        app: FastAPI application
        enforcer: Optional custom enforcer instance
        manager: Optional custom manager instance
    """
    app.add_middleware(TenantSecurityMiddleware, enforcer=enforcer, manager=manager)
    logger.info("Tenant security middleware added to application")

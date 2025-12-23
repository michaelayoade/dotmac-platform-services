"""
Row-Level Security (RLS) Middleware

This middleware automatically sets PostgreSQL session variables for Row-Level Security
policies. It ensures that all database queries are automatically filtered by tenant_id
at the database level, providing an additional layer of security beyond application-level
filtering.

Architecture:
- Extracts tenant from authenticated request context
- Sets PostgreSQL session variables before each request
- Resets session variables after request completion
- Provides bypass mechanisms for superusers and system operations

Usage:
    Add to your FastAPI application:

    from dotmac.platform.core.rls_middleware import RLSMiddleware

    app.add_middleware(RLSMiddleware)
"""

import logging
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


def _get_session_info(session: AsyncSession) -> dict[str, Any] | None:
    info = getattr(session, "info", None)
    if isinstance(info, dict):
        return info
    sync_session = getattr(session, "sync_session", None)
    if sync_session is not None:
        sync_info = getattr(sync_session, "info", None)
        if isinstance(sync_info, dict):
            return sync_info
    return None


def _snapshot_session_rls_context(session: AsyncSession) -> dict[str, Any]:
    info = _get_session_info(session)
    if not info:
        return {}
    return {
        "rls_tenant_id": info.get("rls_tenant_id"),
        "rls_is_superuser": info.get("rls_is_superuser"),
        "rls_bypass": info.get("rls_bypass"),
        "rls_context_configured": info.get("rls_context_configured"),
    }


def _restore_session_rls_context(session: AsyncSession, snapshot: dict[str, Any]) -> None:
    info = _get_session_info(session)
    if info is None:
        return
    if not snapshot:
        for key in (
            "rls_tenant_id",
            "rls_is_superuser",
            "rls_bypass",
            "rls_context_configured",
        ):
            info.pop(key, None)
        return
    info["rls_tenant_id"] = snapshot.get("rls_tenant_id")
    info["rls_is_superuser"] = bool(snapshot.get("rls_is_superuser", False))
    info["rls_bypass"] = bool(snapshot.get("rls_bypass", False))
    if snapshot.get("rls_context_configured"):
        info["rls_context_configured"] = True
    else:
        info.pop("rls_context_configured", None)


def _set_session_rls_context(
    session: AsyncSession,
    tenant_id: str | None,
    is_superuser: bool = False,
    bypass_rls: bool = False,
) -> None:
    info = _get_session_info(session)
    if info is None:
        return
    info["rls_tenant_id"] = tenant_id
    info["rls_is_superuser"] = bool(is_superuser)
    info["rls_bypass"] = bool(bypass_rls)
    info["rls_context_configured"] = True


class RLSMiddleware(BaseHTTPMiddleware):
    """
    Middleware to set Row-Level Security context for PostgreSQL.

    This middleware:
    1. Extracts tenant_id from authenticated request
    2. Sets app.current_tenant_id session variable
    3. Sets app.is_superuser for admin users
    4. Ensures RLS policies filter all database queries
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process each request and set RLS context.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware/route handler

        Returns:
            Response from the route handler
        """
        # Skip RLS for health checks and public endpoints
        if self._should_skip_rls(request):
            return await call_next(request)

        # Extract tenant and user context
        tenant_id: str | None = None
        is_superuser: bool = False

        try:
            # Get tenant from request context
            tenant_id = await self._get_tenant_id(request)

            # Check if user is superuser
            is_superuser = await self._is_superuser(request)

            # Set RLS context in database session
            if tenant_id or is_superuser:
                await self._set_rls_context(
                    request=request,
                    tenant_id=tenant_id,
                    is_superuser=is_superuser,
                )

                logger.debug(
                    f"RLS context set: tenant_id={tenant_id}, "
                    f"is_superuser={is_superuser}, path={request.url.path}"
                )
            else:
                logger.warning(f"No tenant context found for request: {request.url.path}")

        except Exception as e:
            logger.error(f"Failed to set RLS context: {e}", exc_info=True)
            # Continue with request even if RLS setup fails
            # RLS policies will restrict access if context not set

        # Process the request
        response = await call_next(request)

        # Reset RLS context after request (optional, as each request gets new session)
        # await self._reset_rls_context(request)

        return response

    def _should_skip_rls(self, request: Request) -> bool:
        """
        Determine if RLS should be skipped for this request.

        Skip RLS for:
        - Health check endpoints
        - Public API endpoints
        - Static file requests
        - Metrics endpoints

        Args:
            request: The HTTP request

        Returns:
            True if RLS should be skipped
        """
        skip_paths = [
            "/health",
            "/healthz",
            "/ready",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/static/",
            "/public/",
            # Auth endpoints need to work before tenant selection. They rely on strict user/role checks
            # rather than tenant-scoped queries, so we can safely skip RLS to avoid noisy warnings.
            "/api/v1/auth/login",
            "/api/v1/auth/logout",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/api/v1/auth/password-reset",
            "/api/v1/auth/password-reset/confirm",
            "/api/v1/auth/me",
        ]

        path = request.url.path
        return any(path.startswith(skip_path) for skip_path in skip_paths)

    async def _get_tenant_id(self, request: Request) -> str | None:
        """
        Extract tenant ID from request context.

        Priority order:
        1. Tenant from authenticated user's token
        2. Tenant from TenantContext
        3. X-Tenant-ID header (for admin operations)
        4. None (will trigger RLS denial)

        Args:
            request: The HTTP request

        Returns:
            Tenant ID or None
        """
        # Try to get tenant from user token
        try:
            if hasattr(request.state, "tenant_id"):
                return request.state.tenant_id
        except AttributeError:
            pass

        # Try to get from tenant middleware (if it set it)
        try:
            if hasattr(request.state, "tenant"):
                tenant = request.state.tenant
                if tenant and hasattr(tenant, "id"):
                    return tenant.id
        except Exception:
            pass

        # Try to get from header (for admin operations)
        tenant_header = request.headers.get("X-Tenant-ID")
        if tenant_header:
            return tenant_header

        return None

    async def _is_superuser(self, request: Request) -> bool:
        """
        Check if the current user is a superuser/platform admin.

        Superusers can bypass RLS to perform cross-tenant operations.

        Args:
            request: The HTTP request

        Returns:
            True if user is superuser
        """
        try:
            # Check request-scoped user info first
            user = getattr(request.state, "user", None)
            if user and getattr(user, "is_platform_admin", False):
                return True

            claims = getattr(request.state, "jwt_claims", None)
            if isinstance(claims, dict):
                return bool(claims.get("is_platform_admin", False))

            header_superuser = request.headers.get("X-Superuser-Mode") == "true"

            # Fall back to verifying the token when claims aren't cached
            token = None
            auth_header = request.headers.get("Authorization")
            if isinstance(auth_header, str) and auth_header.lower().startswith("bearer "):
                token = auth_header.split(" ", 1)[1].strip()

            if not token:
                cookies = getattr(request, "cookies", None)
                if cookies:
                    try:
                        cookie_token = cookies.get("access_token")
                    except Exception:
                        cookie_token = None
                    if isinstance(cookie_token, str) and cookie_token:
                        token = cookie_token.strip()

            if token:
                try:
                    from dotmac.platform.auth.core import TokenType, jwt_service

                    verified = jwt_service.verify_token(token, TokenType.ACCESS)
                    return bool(verified.get("is_platform_admin", False))
                except Exception as exc:
                    if header_superuser:
                        logger.warning(
                            "superuser_header_rejected",
                            path=request.url.path,
                            error=str(exc),
                        )
            elif header_superuser:
                logger.warning(
                    "superuser_header_rejected",
                    path=request.url.path,
                    reason="missing_token",
                )
        except Exception as e:
            logger.debug(f"Error checking superuser status: {e}")

        return False

    async def _set_rls_context(
        self,
        request: Request,
        tenant_id: str | None = None,
        is_superuser: bool = False,
    ) -> None:
        """
        Store RLS context in request state for later use by database session.

        This function stores:
        - rls_tenant_id: The tenant ID for filtering
        - rls_is_superuser: Whether user can bypass RLS

        The actual PostgreSQL session variables are set when the database
        session is created (see core/database.py dependency).

        Args:
            request: The HTTP request
            tenant_id: Tenant ID to set
            is_superuser: Whether user is superuser
        """
        try:
            # Store RLS context in request state
            # Database session creation will use these values
            request.state.rls_tenant_id = tenant_id
            request.state.rls_is_superuser = is_superuser
            request.state.rls_bypass = False  # Default to false

            logger.debug(
                f"RLS context stored in request state: "
                f"tenant_id={tenant_id}, is_superuser={is_superuser}"
            )

        except Exception as e:
            logger.error(f"Failed to store RLS context: {e}", exc_info=True)

    async def _reset_rls_context(self, request: Request) -> None:
        """
        Reset RLS context after request completion.

        Note: This is not needed as request.state is automatically
        discarded after the request completes.

        Args:
            request: The HTTP request
        """
        # No-op: request.state is discarded automatically
        pass


class RLSContextManager:
    """
    Context manager for setting RLS context in background tasks and scripts.

    Usage:
        async with RLSContextManager(db, tenant_id="tenant-123"):
            # All queries in this block are filtered by tenant_id
            customers = await db.execute(select(Customer))
    """

    def __init__(
        self,
        db: AsyncSession,
        tenant_id: str | None = None,
        is_superuser: bool = False,
        bypass_rls: bool = False,
    ):
        """
        Initialize RLS context manager.

        Args:
            db: Database session
            tenant_id: Tenant ID to set
            is_superuser: Whether to enable superuser mode
            bypass_rls: Whether to bypass RLS completely
        """
        self.db = db
        self.tenant_id = tenant_id
        self.is_superuser = is_superuser
        self.bypass_rls = bypass_rls

    async def __aenter__(self):
        """Set RLS context when entering context."""
        self._previous_context = _snapshot_session_rls_context(self.db)
        _set_session_rls_context(
            self.db,
            tenant_id=self.tenant_id,
            is_superuser=self.is_superuser,
            bypass_rls=self.bypass_rls,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Reset RLS context when exiting context."""
        _restore_session_rls_context(self.db, getattr(self, "_previous_context", {}))


# Utility functions for common RLS operations


async def set_superuser_context(db: AsyncSession) -> None:
    """
    Set superuser context to bypass RLS for admin operations.

    Usage:
        await set_superuser_context(db)
        # Perform admin operations
        await reset_rls_context(db)

    Args:
        db: Database session
    """
    _set_session_rls_context(db, tenant_id=None, is_superuser=True, bypass_rls=False)


async def bypass_rls_for_migration(db: AsyncSession) -> None:
    """
    Bypass RLS completely for migration and system operations.

    Usage:
        await bypass_rls_for_migration(db)
        # Perform migration operations
        await reset_rls_context(db)

    Args:
        db: Database session
    """
    _set_session_rls_context(db, tenant_id=None, is_superuser=False, bypass_rls=True)


async def reset_rls_context(db: AsyncSession) -> None:
    """
    Reset all RLS session variables.

    Args:
        db: Database session
    """
    _restore_session_rls_context(db, {})

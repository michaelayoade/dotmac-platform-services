"""CSRF protection for cookie-based authentication."""

from __future__ import annotations

import secrets
from collections.abc import Awaitable, Callable

import structlog
from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)

CallNext = Callable[[Request], Awaitable[Response]]


class CSRFMiddleware(BaseHTTPMiddleware):
    """Require a CSRF token header when cookie-authenticated."""

    _SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}

    async def dispatch(self, request: Request, call_next: CallNext) -> Response:
        method = request.method.upper()
        if method in self._SAFE_METHODS:
            return await call_next(request)

        # Skip CSRF check for non-cookie auth (e.g., Bearer/API key clients).
        auth_header = request.headers.get("Authorization")
        if isinstance(auth_header, str) and auth_header.lower().startswith("bearer "):
            return await call_next(request)

        access_cookie = request.cookies.get("access_token")
        if not access_cookie:
            return await call_next(request)

        csrf_cookie = request.cookies.get("csrf_token")
        csrf_header = request.headers.get("X-CSRF-Token")

        if not csrf_cookie or not csrf_header:
            logger.warning(
                "csrf_validation_failed",
                path=request.url.path,
                method=method,
                reason="missing_token",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token missing",
            )

        if not secrets.compare_digest(csrf_cookie, csrf_header):
            logger.warning(
                "csrf_validation_failed",
                path=request.url.path,
                method=method,
                reason="token_mismatch",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid CSRF token",
            )

        return await call_next(request)

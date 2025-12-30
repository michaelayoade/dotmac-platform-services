"""CSRF protection for cookie-based authentication."""

from __future__ import annotations

import json
import secrets
from urllib.parse import parse_qs
from collections.abc import Awaitable, Callable

import structlog
from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)

CallNext = Callable[[Request], Awaitable[Response]]


class CSRFMiddleware(BaseHTTPMiddleware):
    """Require a CSRF token header when cookie-authenticated."""

    _SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
    _REFRESH_PATHS = {"/api/v1/auth/refresh", "/auth/refresh"}

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

        if request.url.path in self._REFRESH_PATHS:
            body = await request.body()
            request._body = body  # allow downstream handlers to read the body
            refresh_token = None
            if body:
                content_type = (request.headers.get("Content-Type") or "").lower()
                if "application/json" in content_type:
                    try:
                        payload = json.loads(body)
                        if isinstance(payload, dict):
                            refresh_token = payload.get("refresh_token")
                    except json.JSONDecodeError:
                        refresh_token = None
                elif "application/x-www-form-urlencoded" in content_type:
                    parsed = parse_qs(body.decode("utf-8", errors="ignore"))
                    refresh_token = parsed.get("refresh_token", [None])[0]
            if isinstance(refresh_token, str) and refresh_token.strip():
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

"""
Simple CSRF protection middleware using the double-submit cookie pattern.

- Issues a CSRF cookie (csrf_token) on safe methods if missing
- Requires X-CSRF-Token header to match cookie on unsafe methods
- Designed to work without server-side session; can be combined with SessionManager
"""

from __future__ import annotations

import secrets

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


class CSRFMiddleware(BaseHTTPMiddleware):
    """Double-submit CSRF middleware."""

    def __init__(
        self,
        app,
        cookie_name: str = "csrf_token",
        header_name: str = "X-CSRF-Token",
        secure: bool = True,
        samesite: str = "lax",
    ) -> None:
        super().__init__(app)
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.secure = secure
        self.samesite = samesite

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Safe methods: ensure cookie exists
        method = request.method.upper()
        csrf_cookie = request.cookies.get(self.cookie_name)

        if method in {"GET", "HEAD", "OPTIONS"}:
            response: Response = await call_next(request)
            if not csrf_cookie:
                token = secrets.token_urlsafe(32)
                response.set_cookie(
                    self.cookie_name,
                    token,
                    secure=self.secure,
                    httponly=False,
                    samesite=self.samesite,
                )
            return response

        # Unsafe methods: enforce header matches cookie
        header_token = request.headers.get(self.header_name)
        if not csrf_cookie or not header_token or header_token != csrf_cookie:
            from starlette.responses import JSONResponse

            return JSONResponse({"detail": "CSRF validation failed"}, status_code=403)

        return await call_next(request)

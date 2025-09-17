"""Helpers for exposing FastAPI documentation endpoints."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse

from dotmac.platform.observability.unified_logging import get_logger

logger = get_logger(__name__)


def _route_exists(app: FastAPI, path: str) -> bool:
    return any(getattr(route, "path", None) == path for route in app.router.routes)


def ensure_api_docs(
    app: FastAPI,
    *,
    title: str = "DotMac API",
    docs_path: str = "/docs",
    redoc_path: str = "/redoc",
    openapi_path: str | None = None,
) -> None:
    """Ensure interactive documentation routes exist for the FastAPI application."""

    openapi_url = openapi_path or app.openapi_url or "/openapi.json"
    if app.openapi_url is None:
        app.openapi_url = openapi_url

    if not _route_exists(app, docs_path):

        @app.get(docs_path, include_in_schema=False)
        async def swagger_ui() -> HTMLResponse:  # pragma: no cover - thin wrapper
            return get_swagger_ui_html(openapi_url=openapi_url, title=f"{title} - Swagger UI")

        logger.info("Swagger UI available at %s", docs_path)

    if not _route_exists(app, redoc_path):

        @app.get(redoc_path, include_in_schema=False)
        async def redoc() -> HTMLResponse:  # pragma: no cover - thin wrapper
            return get_redoc_html(openapi_url=openapi_url, title=f"{title} - ReDoc")

        logger.info("ReDoc available at %s", redoc_path)

__all__ = ["ensure_api_docs"]

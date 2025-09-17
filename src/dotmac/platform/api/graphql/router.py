"""Utilities for mounting the GraphQL endpoint."""

from __future__ import annotations

from fastapi import FastAPI

from dotmac.platform.observability.unified_logging import get_logger

from .schema import schema

logger = get_logger(__name__)


def mount_graphql(app: FastAPI, path: str = "/graphql") -> bool:
    """Mount the GraphQL router on the provided FastAPI application.

    Returns ``True`` if the router was mounted successfully, ``False`` if the
    GraphQL dependency is unavailable.
    """

    if schema is None:
        logger.warning(
            "GraphQL endpoint requested but Strawberry is not installed; skipping mount."
        )
        return False

    try:  # pragma: no cover - thin wrapper around strawberry router
        from strawberry.fastapi import GraphQLRouter

        graphql_router = GraphQLRouter(schema, path=path)
        app.include_router(graphql_router, prefix="")
        logger.info("GraphQL endpoint mounted at %s", path)
        return True
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Failed to mount GraphQL endpoint: %s", exc)
        return False

__all__ = ["mount_graphql"]

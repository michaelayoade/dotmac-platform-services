"""Shared service layer primitives.

This module provides lightweight base classes that higher-level services can
inherit from without pulling in optional dependencies required by the full user
management stack. It preserves the legacy ``dotmac.platform.services.BaseService``
import path that some modules still rely on during test collection.
"""

from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar

from dotmac.platform.observability.unified_logging import get_logger


ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")
ResponseType = TypeVar("ResponseType")


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType, ResponseType]):
    """Minimal async-friendly service base class used in tests.

    The implementation intentionally keeps behaviour focused on the pieces that
    our test doubles require: storing the database session, tracking the tenant
    context, and exposing a reusable logger. Concrete services can extend this
    class and override or extend the helper methods as needed.
    """

    def __init__(
        self,
        db_session: Any,
        tenant_id: Optional[str] = None,
        *,
        create_schema: Any | None = None,
        update_schema: Any | None = None,
        response_schema: Any | None = None,
        **_: Any,
    ) -> None:
        self.db = db_session
        self.db_session = db_session  # Backwards compatibility alias
        self.tenant_id = tenant_id
        self.create_schema = create_schema
        self.update_schema = update_schema
        self.response_schema = response_schema
        self._logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    @property
    def logger(self):
        """Expose the structured logger for subclasses."""
        return self._logger

    async def health_check(self) -> dict[str, Any]:
        """Basic health check hook for subclasses to extend."""
        return {
            "status": "unknown",
            "service": self.__class__.__name__,
        }


__all__ = ["BaseService"]

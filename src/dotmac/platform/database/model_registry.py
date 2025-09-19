"""Central registry for platform SQLAlchemy models."""

from __future__ import annotations

from dotmac.platform.observability.unified_logging import get_logger
from importlib import import_module
from typing import Iterable, List

from .base import Base

logger = get_logger(__name__)

# Modules containing SQLAlchemy model definitions that rely on Base
MODEL_MODULES: Iterable[str] = (
    "dotmac.platform.feature_flags.db_models",
)

def import_model_modules() -> None:
    """Import model modules so models register with the shared Base metadata."""

    for module_name in MODEL_MODULES:
        try:
            import_module(module_name)
        except ModuleNotFoundError:
            logger.debug("Model module %s not found", module_name)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to import model module %s: %s", module_name, exc)

def get_metadata() -> List:
    """Return a list containing the primary SQLAlchemy metadata objects."""

    import_model_modules()
    return [Base.metadata]

__all__ = ["import_model_modules", "get_metadata", "MODEL_MODULES"]

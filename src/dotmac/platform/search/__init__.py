"""Search service for business entities."""

from .interfaces import SearchQuery, SearchResult
from .service import (
    InMemorySearchBackend,
    MeilisearchBackend,
    SearchService,
    create_search_backend_from_env,
)

__all__ = [
    "SearchService",
    "SearchQuery",
    "SearchResult",
    "InMemorySearchBackend",
    "MeilisearchBackend",
    "create_search_backend_from_env",
]

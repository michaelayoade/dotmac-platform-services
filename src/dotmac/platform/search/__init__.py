"""Search service for business entities."""

from .factory import create_search_backend_from_env
from .interfaces import SearchBackend, SearchQuery, SearchResponse, SearchResult
from .service import (
    InMemorySearchBackend,
    MeilisearchBackend,
    SearchService,
)

__all__ = [
    "SearchService",
    "SearchQuery",
    "SearchResult",
    "SearchResponse",
    "SearchBackend",
    "InMemorySearchBackend",
    "MeilisearchBackend",
    "create_search_backend_from_env",
]

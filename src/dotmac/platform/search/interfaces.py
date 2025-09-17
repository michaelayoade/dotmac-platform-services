"""Search service interfaces."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class SearchType(str, Enum):
    """Search types."""

    FULL_TEXT = "full_text"
    EXACT = "exact"
    PREFIX = "prefix"
    FUZZY = "fuzzy"
    REGEX = "regex"


class SortOrder(str, Enum):
    """Sort order."""

    ASC = "asc"
    DESC = "desc"


@dataclass
class SearchFilter:
    """Search filter criteria."""

    field: str
    value: Any
    operator: str = "eq"  # eq, ne, gt, lt, gte, lte, in, contains


@dataclass
class SearchQuery:
    """Search query parameters."""

    query: str
    search_type: SearchType = SearchType.FULL_TEXT
    filters: List[SearchFilter] = field(default_factory=list)
    fields: Optional[List[str]] = None  # Fields to search in
    limit: int = 10
    offset: int = 0
    sort_by: Optional[str] = None
    sort_order: SortOrder = SortOrder.DESC
    include_score: bool = False
    highlight: bool = False


@dataclass
class SearchResult:
    """Search result item."""

    id: str
    type: str
    data: Dict[str, Any]
    score: Optional[float] = None
    highlights: Optional[Dict[str, List[str]]] = None


@dataclass
class SearchResponse:
    """Search response with results and metadata."""

    results: List[SearchResult]
    total: int
    query: SearchQuery
    took_ms: Optional[int] = None


class SearchBackend(ABC):
    """Abstract search backend interface."""

    @abstractmethod
    async def index(self, index_name: str, doc_id: str, document: Dict[str, Any]) -> bool:
        """Index a document."""
        pass

    @abstractmethod
    async def search(self, index_name: str, query: SearchQuery) -> SearchResponse:
        """Search documents."""
        pass

    @abstractmethod
    async def delete(self, index_name: str, doc_id: str) -> bool:
        """Delete a document."""
        pass

    @abstractmethod
    async def update(self, index_name: str, doc_id: str, document: Dict[str, Any]) -> bool:
        """Update a document."""
        pass

    @abstractmethod
    async def bulk_index(self, index_name: str, documents: List[Dict[str, Any]]) -> int:
        """Bulk index documents."""
        pass

    @abstractmethod
    async def create_index(
        self, index_name: str, mappings: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Create an index."""
        pass

    @abstractmethod
    async def delete_index(self, index_name: str) -> bool:
        """Delete an index."""
        pass

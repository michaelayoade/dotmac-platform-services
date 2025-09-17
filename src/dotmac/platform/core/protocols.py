"""
Service and repository protocols for consistent architecture patterns.

Provides standard interfaces for:
- Repository pattern with CRUD operations
- Service layer pattern
- Unit of Work for transaction management
- Pagination support
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, Protocol, TypeVar

from pydantic import BaseModel

# Type variables for generic protocols
T = TypeVar("T")  # Entity type
CreateT = TypeVar("CreateT", bound=BaseModel)  # Create schema type
UpdateT = TypeVar("UpdateT", bound=BaseModel)  # Update schema type
ID = TypeVar("ID")  # ID type


class RepositoryProtocol(Protocol, Generic[T, CreateT, UpdateT]):
    """
    Standard repository protocol for data access.

    Defines consistent CRUD operations for all repositories.
    """

    async def get(self, id: ID) -> T | None:
        """Get entity by ID."""
        ...

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[T]:
        """Get all entities with pagination."""
        ...

    async def create(self, data: CreateT) -> T:
        """Create new entity."""
        ...

    async def update(self, id: ID, data: UpdateT) -> T | None:
        """Update existing entity."""
        ...

    async def delete(self, id: ID) -> bool:
        """Delete entity by ID."""
        ...

    async def exists(self, id: ID) -> bool:
        """Check if entity exists."""
        ...

    async def count(self) -> int:
        """Count total entities."""
        ...


class TenantAwareRepository(RepositoryProtocol[T, CreateT, UpdateT]):
    """Repository protocol with multi-tenant support."""

    async def get_by_tenant(self, tenant_id: str, skip: int = 0, limit: int = 100) -> list[T]:
        """Get entities for a specific tenant."""
        ...

    async def get_all_by_tenant(self, tenant_id: str) -> list[T]:
        """Get all entities for a specific tenant."""
        ...

    async def count_by_tenant(self, tenant_id: str) -> int:
        """Count entities for a specific tenant."""
        ...


class CacheableRepository(RepositoryProtocol[T, CreateT, UpdateT]):
    """Repository protocol with caching support."""

    async def invalidate_cache(self, id: ID) -> None:
        """Invalidate cache for specific entity."""
        ...

    async def warm_cache(self, ids: list[ID]) -> None:
        """Pre-load entities into cache."""
        ...

    async def get_cached(self, id: ID) -> T | None:
        """Get entity from cache if available."""
        ...


class ServiceProtocol(Protocol):
    """
    Marker protocol for service layer.

    Services should implement business logic and coordinate
    between repositories and other services.
    """

    async def initialize(self) -> None: ...

    async def shutdown(self) -> None: ...

    async def health_check(self) -> dict[str, Any]: ...


class UnitOfWork(Protocol):
    """
    Unit of Work protocol for transaction management.

    Ensures all operations within a unit are committed or rolled back together.
    """

    async def __aenter__(self):
        """Begin unit of work."""
        ...

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """End unit of work."""
        ...

    # Tests also expect sync context manager methods to exist on the protocol
    def __enter__(self): ...

    def __exit__(self, exc_type, exc_val, exc_tb): ...

    async def commit(self) -> None:
        """Commit all changes."""
        ...

    async def rollback(self) -> None:
        """Rollback all changes."""
        ...


class EventPublisher(Protocol):
    """Protocol for publishing domain events."""

    async def publish(self, event_type: str, data: dict[str, Any]) -> None:
        """Publish a domain event."""
        ...

    async def publish_batch(self, events: list[tuple[str, dict[str, Any]]]) -> None:
        """Publish a batch of events."""
        ...


class QueryBuilder(Protocol[T]):
    """Protocol for building database queries."""

    def filter(self, **kwargs) -> "QueryBuilder[T]":
        """Add filter conditions."""
        ...

    def order_by(self, field: str, desc: bool = False) -> "QueryBuilder[T]":
        """Add ordering."""
        ...

    def limit(self, count: int) -> "QueryBuilder[T]":
        """Limit results."""
        ...

    def offset(self, count: int) -> "QueryBuilder[T]":
        """Skip results."""
        ...

    async def execute(self) -> list[T]:
        """Execute query and return results."""
        ...

    async def first(self) -> T | None:
        """Get first result."""
        ...

    async def count(self) -> int:
        """Count matching results."""
        ...

    def build(self) -> Any:
        """Build the query structure."""
        ...

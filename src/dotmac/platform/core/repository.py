"""
Repository pattern implementation for DotMac Platform Services.

Provides base repository classes and interfaces for data access.
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ..database import Base

# Type variables for generic repository
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class RepositoryError(Exception):
    """Base exception for repository operations."""

    pass


class EntityNotFoundError(RepositoryError):
    """Raised when entity is not found."""

    pass


class DuplicateEntityError(RepositoryError):
    """Raised when attempting to create duplicate entity."""

    pass


class IRepository(ABC, Generic[ModelType]):
    """Abstract base repository interface."""

    @abstractmethod
    async def get(self, id: Any) -> ModelType | None:
        """Get entity by ID."""
        pass

    @abstractmethod
    async def get_all(
        self, skip: int = 0, limit: int = 100
    ) -> list[ModelType]:
        """Get all entities with pagination."""
        pass

    @abstractmethod
    async def create(self, obj_in: Any) -> ModelType:
        """Create new entity."""
        pass

    @abstractmethod
    async def update(self, id: Any, obj_in: Any) -> ModelType | None:
        """Update existing entity."""
        pass

    @abstractmethod
    async def delete(self, id: Any) -> bool:
        """Delete entity by ID."""
        pass

    @abstractmethod
    async def exists(self, id: Any) -> bool:
        """Check if entity exists."""
        pass


class AsyncRepository(
    IRepository[ModelType], Generic[ModelType, CreateSchemaType, UpdateSchemaType]
):
    """
    Base async repository with CRUD operations.

    Provides standard CRUD operations for SQLAlchemy models.
    """

    def __init__(self, model: type[ModelType], session: AsyncSession):
        """
        Initialize repository.

        Args:
            model: SQLAlchemy model class
            session: Async database session
        """
        self.model = model
        self.session = session

    async def get(self, id: Any) -> ModelType | None:
        """
        Get entity by ID.

        Args:
            id: Entity ID

        Returns:
            Entity or None if not found
        """
        return await self.session.get(self.model, id)

    async def get_all(
        self, skip: int = 0, limit: int = 100
    ) -> list[ModelType]:
        """
        Get all entities with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of entities
        """
        stmt = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_field(
        self, field_name: str, field_value: Any
    ) -> ModelType | None:
        """
        Get entity by field value.

        Args:
            field_name: Field name to filter by
            field_value: Field value to match

        Returns:
            Entity or None if not found
        """
        stmt = select(self.model).where(
            getattr(self.model, field_name) == field_value
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi_by_field(
        self,
        field_name: str,
        field_value: Any,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        """
        Get multiple entities by field value.

        Args:
            field_name: Field name to filter by
            field_value: Field value to match
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of entities
        """
        stmt = (
            select(self.model)
            .where(getattr(self.model, field_name) == field_value)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """
        Create new entity.

        Args:
            obj_in: Pydantic schema with creation data

        Returns:
            Created entity
        """
        db_obj = self.model(**obj_in.model_dump())
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(
        self, id: Any, obj_in: UpdateSchemaType
    ) -> ModelType | None:
        """
        Update existing entity.

        Args:
            id: Entity ID
            obj_in: Pydantic schema with update data

        Returns:
            Updated entity or None if not found
        """
        db_obj = await self.get(id)
        if db_obj is None:
            return None

        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, id: Any) -> bool:
        """
        Delete entity by ID.

        Args:
            id: Entity ID

        Returns:
            True if deleted, False if not found
        """
        db_obj = await self.get(id)
        if db_obj is None:
            return False

        await self.session.delete(db_obj)
        await self.session.commit()
        return True

    async def exists(self, id: Any) -> bool:
        """
        Check if entity exists.

        Args:
            id: Entity ID

        Returns:
            True if exists
        """
        db_obj = await self.get(id)
        return db_obj is not None

    async def count(self) -> int:
        """
        Count total entities.

        Returns:
            Total count
        """
        from sqlalchemy import func

        stmt = select(func.count()).select_from(self.model)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def count_by_field(self, field_name: str, field_value: Any) -> int:
        """
        Count entities by field value.

        Args:
            field_name: Field name to filter by
            field_value: Field value to match

        Returns:
            Count of matching entities
        """
        from sqlalchemy import func

        stmt = (
            select(func.count())
            .select_from(self.model)
            .where(getattr(self.model, field_name) == field_value)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    def build_query(self) -> Select:
        """
        Build base query for the model.

        Returns:
            SQLAlchemy Select statement
        """
        return select(self.model)

    async def execute_query(self, stmt: Select) -> list[ModelType]:
        """
        Execute custom query.

        Args:
            stmt: SQLAlchemy Select statement

        Returns:
            List of entities
        """
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class SyncRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base sync repository with CRUD operations.

    Provides standard CRUD operations for SQLAlchemy models in sync context.
    """

    def __init__(self, model: type[ModelType], session: Session):
        """
        Initialize repository.

        Args:
            model: SQLAlchemy model class
            session: Database session
        """
        self.model = model
        self.session = session

    def get(self, id: Any) -> ModelType | None:
        """
        Get entity by ID.

        Args:
            id: Entity ID

        Returns:
            Entity or None if not found
        """
        return self.session.get(self.model, id)

    def get_all(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        """
        Get all entities with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of entities
        """
        return (
            self.session.query(self.model)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(self, obj_in: CreateSchemaType) -> ModelType:
        """
        Create new entity.

        Args:
            obj_in: Pydantic schema with creation data

        Returns:
            Created entity
        """
        db_obj = self.model(**obj_in.model_dump())
        self.session.add(db_obj)
        self.session.commit()
        self.session.refresh(db_obj)
        return db_obj

    def update(
        self, id: Any, obj_in: UpdateSchemaType
    ) -> ModelType | None:
        """
        Update existing entity.

        Args:
            id: Entity ID
            obj_in: Pydantic schema with update data

        Returns:
            Updated entity or None if not found
        """
        db_obj = self.get(id)
        if db_obj is None:
            return None

        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.session.add(db_obj)
        self.session.commit()
        self.session.refresh(db_obj)
        return db_obj

    def delete(self, id: Any) -> bool:
        """
        Delete entity by ID.

        Args:
            id: Entity ID

        Returns:
            True if deleted, False if not found
        """
        db_obj = self.get(id)
        if db_obj is None:
            return False

        self.session.delete(db_obj)
        self.session.commit()
        return True

    def exists(self, id: Any) -> bool:
        """
        Check if entity exists.

        Args:
            id: Entity ID

        Returns:
            True if exists
        """
        return self.get(id) is not None


# Unit of Work pattern
class IUnitOfWork(ABC):
    """Abstract Unit of Work interface."""

    @abstractmethod
    async def __aenter__(self):
        """Enter context."""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        pass

    @abstractmethod
    async def commit(self):
        """Commit transaction."""
        pass

    @abstractmethod
    async def rollback(self):
        """Rollback transaction."""
        pass


class AsyncUnitOfWork(IUnitOfWork):
    """
    Async Unit of Work implementation.

    Manages database transactions and repository instances.
    """

    def __init__(self, session_factory):
        """
        Initialize Unit of Work.

        Args:
            session_factory: Async session factory
        """
        self.session_factory = session_factory
        self.session: AsyncSession | None = None

    async def __aenter__(self):
        """Enter context and start transaction."""
        self.session = self.session_factory()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context and handle transaction."""
        if exc_type:
            await self.rollback()
        else:
            await self.commit()

        await self.session.close()
        self.session = None

    async def commit(self):
        """Commit transaction."""
        if self.session:
            await self.session.commit()

    async def rollback(self):
        """Rollback transaction."""
        if self.session:
            await self.session.rollback()

    def get_repository(
        self, model: type[ModelType]
    ) -> AsyncRepository[ModelType, Any, Any]:
        """
        Get repository for model.

        Args:
            model: SQLAlchemy model class

        Returns:
            Repository instance
        """
        if not self.session:
            raise RuntimeError("Unit of Work not initialized")
        return AsyncRepository(model, self.session)


# Export all
__all__ = [
    "IRepository",
    "AsyncRepository",
    "SyncRepository",
    "IUnitOfWork",
    "AsyncUnitOfWork",
    "RepositoryError",
    "EntityNotFoundError",
    "DuplicateEntityError",
    "ModelType",
    "CreateSchemaType",
    "UpdateSchemaType",
]
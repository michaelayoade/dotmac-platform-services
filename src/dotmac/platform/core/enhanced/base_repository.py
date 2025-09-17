"""
Enhanced Base Repository implementing standardized database patterns.
Provides consistent CRUD operations, query optimization, and error handling.
"""

from __future__ import annotations


from typing import Any, Generic, Optional, Sequence, Type, TypeVar
from uuid import UUID

from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from .exceptions import RepositoryError, EntityNotFoundError, DuplicateEntityError, ValidationError

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

# Type variables for generic repository
ModelType = TypeVar("ModelType", bound=DeclarativeBase)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base repository providing standardized database operations.

    Implements:
    - Consistent CRUD operations
    - Query optimization with eager loading
    - Tenant isolation support
    - Comprehensive error handling
    - Audit logging
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session
        self.logger = get_logger(f"{__name__}.{model.__name__}Repository")

    async def create(
        self, obj_in: CreateSchemaType, tenant_id: str | None = None, commit: bool = True
    ) -> ModelType:
        """Create a new entity with validation and audit logging."""
        try:
            # Convert schema to dict if needed
            if hasattr(obj_in, "model_dump"):
                obj_data = obj_in.model_dump(exclude_unset=True)
            elif hasattr(obj_in, "dict"):
                obj_data = obj_in.dict(exclude_unset=True)
            else:
                obj_data = obj_in

            # Add tenant_id if supported
            if tenant_id and hasattr(self.model, "tenant_id"):
                obj_data["tenant_id"] = tenant_id

            # Create entity
            db_obj = self.model(**obj_data)
            self.session.add(db_obj)

            if commit:
                await self.session.commit()
                await self.session.refresh(db_obj)

            self.logger.info(
                f"Created {self.model.__name__} with ID: {getattr(db_obj, 'id', 'unknown')}"
            )
            return db_obj

        except IntegrityError as e:
            await self.session.rollback()
            self.logger.error(f"Integrity error creating {self.model.__name__}: {e}")
            raise DuplicateEntityError(f"Entity already exists: {e}") from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(f"Database error creating {self.model.__name__}: {e}")
            raise RepositoryError(f"Failed to create entity: {e}") from e

    async def get(self, id: UUID | str | int, tenant_id: str | None = None) -> Optional[ModelType]:
        """Get entity by ID with tenant isolation."""
        try:
            query = select(self.model).where(self.model.id == id)

            # Add tenant filtering if supported
            if tenant_id and hasattr(self.model, "tenant_id"):
                query = query.where(self.model.tenant_id == tenant_id)

            result = await self.session.execute(query)
            entity = result.scalar_one_or_none()

            if entity:
                self.logger.debug(f"Retrieved {self.model.__name__} ID: {id}")

            return entity

        except SQLAlchemyError as e:
            self.logger.error(f"Database error retrieving {self.model.__name__} ID {id}: {e}")
            raise RepositoryError(f"Failed to retrieve entity: {e}") from e

    async def get_or_raise(self, id: UUID | str | int, tenant_id: str | None = None) -> ModelType:
        """Get entity by ID or raise EntityNotFoundError."""
        entity = await self.get(id, tenant_id)
        if not entity:
            raise EntityNotFoundError(f"{self.model.__name__} with ID {id} not found")
        return entity

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        tenant_id: str | None = None,
        filters: dict[str, Any] | None = None,
        order_by: str | None = None,
    ) -> Sequence[ModelType]:
        """Get multiple entities with pagination and filtering."""
        try:
            query = select(self.model)

            # Add tenant filtering
            if tenant_id and hasattr(self.model, "tenant_id"):
                query = query.where(self.model.tenant_id == tenant_id)

            # Apply filters
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key) and value is not None:
                        column = getattr(self.model, key)
                        query = query.where(column == value)

            # Add ordering
            if order_by and hasattr(self.model, order_by):
                column = getattr(self.model, order_by)
                query = query.order_by(column)
            elif hasattr(self.model, "created_at"):
                query = query.order_by(self.model.created_at.desc())

            # Add pagination
            query = query.offset(skip).limit(limit)

            result = await self.session.execute(query)
            entities = result.scalars().all()

            self.logger.debug(f"Retrieved {len(entities)} {self.model.__name__} entities")
            return entities

        except SQLAlchemyError as e:
            self.logger.error(f"Database error retrieving {self.model.__name__} entities: {e}")
            raise RepositoryError(f"Failed to retrieve entities: {e}") from e

    async def update(
        self,
        id: UUID | str | int,
        obj_in: UpdateSchemaType | dict[str, Any],
        tenant_id: str | None = None,
        commit: bool = True,
    ) -> Optional[ModelType]:
        """Update entity with validation and audit logging."""
        try:
            # Get existing entity
            entity = await self.get(id, tenant_id)
            if not entity:
                return None

            # Convert schema to dict if needed
            if hasattr(obj_in, "model_dump"):
                update_data = obj_in.model_dump(exclude_unset=True)
            elif hasattr(obj_in, "dict"):
                update_data = obj_in.dict(exclude_unset=True)
            else:
                update_data = obj_in

            # Update entity attributes
            for field, value in update_data.items():
                if hasattr(entity, field) and field != "id":
                    setattr(entity, field, value)

            if commit:
                await self.session.commit()
                await self.session.refresh(entity)

            self.logger.info(f"Updated {self.model.__name__} ID: {id}")
            return entity

        except IntegrityError as e:
            await self.session.rollback()
            self.logger.error(f"Integrity error updating {self.model.__name__} ID {id}: {e}")
            raise DuplicateEntityError(f"Update would create duplicate: {e}") from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(f"Database error updating {self.model.__name__} ID {id}: {e}")
            raise RepositoryError(f"Failed to update entity: {e}") from e

    async def delete(
        self, id: UUID | str | int, tenant_id: str | None = None, commit: bool = True
    ) -> bool:
        """Delete entity with audit logging."""
        try:
            query = select(self.model).where(self.model.id == id)

            if tenant_id and hasattr(self.model, "tenant_id"):
                query = query.where(self.model.tenant_id == tenant_id)

            result = await self.session.execute(query)
            entity = result.scalar_one_or_none()

            if not entity:
                return False

            await self.session.delete(entity)

            if commit:
                await self.session.commit()

            self.logger.info(f"Deleted {self.model.__name__} ID: {id}")
            return True

        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(f"Database error deleting {self.model.__name__} ID {id}: {e}")
            raise RepositoryError(f"Failed to delete entity: {e}") from e

    async def count(
        self, tenant_id: str | None = None, filters: dict[str, Any] | None = None
    ) -> int:
        """Count entities with filtering."""
        try:
            query = select(func.count(self.model.id))

            # Add tenant filtering
            if tenant_id and hasattr(self.model, "tenant_id"):
                query = query.where(self.model.tenant_id == tenant_id)

            # Apply filters
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key) and value is not None:
                        column = getattr(self.model, key)
                        query = query.where(column == value)

            result = await self.session.execute(query)
            return result.scalar() or 0

        except SQLAlchemyError as e:
            self.logger.error(f"Database error counting {self.model.__name__} entities: {e}")
            raise RepositoryError(f"Failed to count entities: {e}") from e

    async def exists(self, id: UUID | str | int, tenant_id: str | None = None) -> bool:
        """Check if entity exists."""
        try:
            query = select(func.count(self.model.id)).where(self.model.id == id)

            if tenant_id and hasattr(self.model, "tenant_id"):
                query = query.where(self.model.tenant_id == tenant_id)

            result = await self.session.execute(query)
            count = result.scalar() or 0
            return count > 0

        except SQLAlchemyError as e:
            self.logger.error(
                f"Database error checking {self.model.__name__} existence ID {id}: {e}"
            )
            raise RepositoryError(f"Failed to check entity existence: {e}") from e

    async def bulk_create(
        self, objs_in: list[CreateSchemaType], tenant_id: str | None = None, commit: bool = True
    ) -> list[ModelType]:
        """Create multiple entities efficiently."""
        try:
            db_objs = []

            for obj_in in objs_in:
                if hasattr(obj_in, "model_dump"):
                    obj_data = obj_in.model_dump(exclude_unset=True)
                elif hasattr(obj_in, "dict"):
                    obj_data = obj_in.dict(exclude_unset=True)
                else:
                    obj_data = obj_in

                if tenant_id and hasattr(self.model, "tenant_id"):
                    obj_data["tenant_id"] = tenant_id

                db_obj = self.model(**obj_data)
                db_objs.append(db_obj)

            self.session.add_all(db_objs)

            if commit:
                await self.session.commit()
                for db_obj in db_objs:
                    await self.session.refresh(db_obj)

            self.logger.info(f"Bulk created {len(db_objs)} {self.model.__name__} entities")
            return db_objs

        except IntegrityError as e:
            await self.session.rollback()
            self.logger.error(f"Integrity error bulk creating {self.model.__name__}: {e}")
            raise DuplicateEntityError(f"Bulk create contains duplicates: {e}") from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(f"Database error bulk creating {self.model.__name__}: {e}")
            raise RepositoryError(f"Failed to bulk create entities: {e}") from e

# Export the base repository
__all__ = ["BaseRepository", "ModelType", "CreateSchemaType", "UpdateSchemaType"]

"""
Base repository class with DRY patterns.
Provides common functionality for all repositories.
"""


from abc import ABC
from datetime import datetime, timezone
from typing import Any, Generic, Optional, TypeVar
from uuid import UUID

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, selectinload
from sqlalchemy.sql import Select

from dotmac.platform.core.enhanced.exceptions import (

    EntityNotFoundError,
    ValidationError,
)
from dotmac.platform.observability.unified_logging import get_logger


logger = get_logger(__name__)

ModelType = TypeVar("ModelType", bound=DeclarativeBase)

class BaseRepository(Generic[ModelType], ABC):
    """
    Abstract base repository with common CRUD operations.
    Enforces DRY patterns across all repositories.
    """

    def __init__(
        self,
        db_session: AsyncSession,
        model_class: type[ModelType],
        tenant_id: Optional[UUID] = None,
    ):
        """Initialize repository with database session and model class."""
        self.db = db_session
        self.model_class = model_class
        self.tenant_id = tenant_id
        self._logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    # === Core CRUD Operations ===

    async def create(self, **kwargs) -> ModelType:
        """Create a new entity."""
        try:
            entity = self.model_class(**kwargs)
            self.db.add(entity)
            await self.db.commit()
            await self.db.refresh(entity)

            self._logger.debug(f"Created {self.model_class.__name__} with ID: {entity.id}")
            return entity

        except Exception as e:
            await self.db.rollback()
            self._logger.error(f"Failed to create {self.model_class.__name__}: {e}")
            raise ValidationError(f"Failed to create entity: {str(e)}") from e

    async def get_by_id(self, entity_id: UUID) -> Optional[ModelType]:
        """Get entity by ID."""
        try:
            query = select(self.model_class).where(self.model_class.id == entity_id)
            result = await self.db.execute(query)
            entity = result.scalar_one_or_none()

            if entity:
                self._logger.debug(f"Found {self.model_class.__name__} with ID: {entity_id}")

            return entity

        except Exception as e:
            self._logger.error(f"Failed to get {self.model_class.__name__} by ID {entity_id}: {e}")
            raise

    async def get_by_id_or_raise(self, entity_id: UUID) -> ModelType:
        """Get entity by ID or raise EntityNotFoundError."""
        entity = await self.get_by_id(entity_id)
        if not entity:
            raise EntityNotFoundError(f"{self.model_class.__name__} not found with ID: {entity_id}")
        return entity

    async def update(self, entity_id: UUID, **kwargs) -> ModelType:
        """Update entity by ID."""
        try:
            entity = await self.get_by_id_or_raise(entity_id)

            # Update fields
            for key, value in kwargs.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)

            # Update timestamp if available
            if hasattr(entity, "updated_at"):
                entity.updated_at = datetime.now(timezone.utc)

            await self.db.commit()
            await self.db.refresh(entity)

            self._logger.debug(f"Updated {self.model_class.__name__} with ID: {entity_id}")
            return entity

        except EntityNotFoundError:
            raise
        except Exception as e:
            await self.db.rollback()
            self._logger.error(f"Failed to update {self.model_class.__name__} {entity_id}: {e}")
            raise ValidationError(f"Failed to update entity: {str(e)}") from e

    async def delete(self, entity_id: UUID, soft_delete: bool = True) -> bool:
        """Delete entity by ID."""
        try:
            entity = await self.get_by_id_or_raise(entity_id)

            if soft_delete and hasattr(entity, "is_active"):
                # Soft delete
                entity.is_active = False
                if hasattr(entity, "deleted_at"):
                    entity.deleted_at = datetime.now(timezone.utc)
                if hasattr(entity, "updated_at"):
                    entity.updated_at = datetime.now(timezone.utc)
                await self.db.commit()
                self._logger.debug(f"Soft deleted {self.model_class.__name__} with ID: {entity_id}")
            else:
                # Hard delete
                await self.db.delete(entity)
                await self.db.commit()
                self._logger.debug(f"Hard deleted {self.model_class.__name__} with ID: {entity_id}")

            return True

        except EntityNotFoundError:
            raise
        except Exception as e:
            await self.db.rollback()
            self._logger.error(f"Failed to delete {self.model_class.__name__} {entity_id}: {e}")
            raise

    async def list_with_pagination(
        self,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[dict[str, Any]] = None,
        order_by: str = "created_at",
        order_desc: bool = True,
        include_inactive: bool = False,
    ) -> tuple[list[ModelType], int]:
        """List entities with pagination and filtering."""
        try:
            # Build base query
            query = select(self.model_class)

            # Apply filters
            query = self._apply_filters(query, filters, include_inactive)

            # Get total count
            count_query = select(func.count(self.model_class.id))
            count_query = self._apply_filters(count_query, filters, include_inactive)
            count_result = await self.db.execute(count_query)
            total_count = count_result.scalar()

            # Apply ordering
            if hasattr(self.model_class, order_by):
                order_column = getattr(self.model_class, order_by)
                if order_desc:
                    query = query.order_by(order_column.desc())
                else:
                    query = query.order_by(order_column.asc())

            # Apply pagination
            query = query.offset(skip).limit(limit)

            # Execute query
            result = await self.db.execute(query)
            entities = result.scalars().all()

            self._logger.debug(f"Retrieved {len(entities)} {self.model_class.__name__} entities")
            return list(entities), total_count

        except Exception as e:
            self._logger.error(f"Failed to list {self.model_class.__name__}: {e}")
            raise

    async def count(
        self, filters: Optional[dict[str, Any]] = None, include_inactive: bool = False
    ) -> int:
        """Count entities with optional filters."""
        try:
            query = select(func.count(self.model_class.id))
            query = self._apply_filters(query, filters, include_inactive)

            result = await self.db.execute(query)
            count = result.scalar()

            self._logger.debug(f"Counted {count} {self.model_class.__name__} entities")
            return count

        except Exception as e:
            self._logger.error(f"Failed to count {self.model_class.__name__}: {e}")
            raise

    async def exists(self, **kwargs) -> bool:
        """Check if entity exists with given criteria."""
        try:
            query = select(self.model_class.id)

            # Add where conditions
            conditions = []
            for key, value in kwargs.items():
                if hasattr(self.model_class, key):
                    conditions.append(getattr(self.model_class, key) == value)

            if conditions:
                query = query.where(and_(*conditions))

            result = await self.db.execute(query)
            entity_id = result.scalar_one_or_none()

            exists = entity_id is not None
            self._logger.debug(f"Entity exists check for {self.model_class.__name__}: {exists}")
            return exists

        except Exception as e:
            self._logger.error(f"Failed to check existence of {self.model_class.__name__}: {e}")
            raise

    async def bulk_create(self, entities_data: list[dict[str, Any]]) -> list[ModelType]:
        """Create multiple entities in bulk."""
        try:
            entities = []
            for data in entities_data:
                entity = self.model_class(**data)
                entities.append(entity)
                self.db.add(entity)

            await self.db.commit()

            # Refresh all entities
            for entity in entities:
                await self.db.refresh(entity)

            self._logger.debug(f"Bulk created {len(entities)} {self.model_class.__name__} entities")
            return entities

        except Exception as e:
            await self.db.rollback()
            self._logger.error(f"Failed to bulk create {self.model_class.__name__}: {e}")
            raise ValidationError(f"Failed to bulk create entities: {str(e)}") from e

    async def bulk_update(self, updates: dict[UUID, dict[str, Any]]) -> int:
        """Update multiple entities in bulk."""
        try:
            updated_count = 0

            for entity_id, update_data in updates.items():
                # Add updated_at timestamp if available
                if hasattr(self.model_class, "updated_at"):
                    update_data["updated_at"] = datetime.now(timezone.utc)

                # Build update query
                query = (
                    update(self.model_class)
                    .where(self.model_class.id == entity_id)
                    .values(**update_data)
                )

                result = await self.db.execute(query)
                updated_count += result.rowcount

            await self.db.commit()

            self._logger.debug(f"Bulk updated {updated_count} {self.model_class.__name__} entities")
            return updated_count

        except Exception as e:
            await self.db.rollback()
            self._logger.error(f"Failed to bulk update {self.model_class.__name__}: {e}")
            raise ValidationError(f"Failed to bulk update entities: {str(e)}") from e

    async def bulk_delete(self, entity_ids: list[UUID], soft_delete: bool = True) -> int:
        """Delete multiple entities in bulk."""
        try:
            if soft_delete and hasattr(self.model_class, "is_active"):
                # Soft delete
                update_data = {"is_active": False}
                if hasattr(self.model_class, "deleted_at"):
                    update_data["deleted_at"] = datetime.now(timezone.utc)
                if hasattr(self.model_class, "updated_at"):
                    update_data["updated_at"] = datetime.now(timezone.utc)

                query = (
                    update(self.model_class)
                    .where(self.model_class.id.in_(entity_ids))
                    .values(**update_data)
                )

                result = await self.db.execute(query)
                deleted_count = result.rowcount

            else:
                # Hard delete
                query = delete(self.model_class).where(self.model_class.id.in_(entity_ids))
                result = await self.db.execute(query)
                deleted_count = result.rowcount

            await self.db.commit()

            self._logger.debug(f"Bulk deleted {deleted_count} {self.model_class.__name__} entities")
            return deleted_count

        except Exception as e:
            await self.db.rollback()
            self._logger.error(f"Failed to bulk delete {self.model_class.__name__}: {e}")
            raise

    # === Search Operations ===

    async def search(
        self,
        query: str,
        search_fields: list[str],
        skip: int = 0,
        limit: int = 20,
        filters: Optional[dict[str, Any]] = None,
        include_inactive: bool = False,
    ) -> tuple[list[ModelType], int]:
        """Search entities across specified fields."""
        try:
            # Build search conditions
            search_conditions = []
            for field in search_fields:
                if hasattr(self.model_class, field):
                    column = getattr(self.model_class, field)
                    search_conditions.append(column.ilike(f"%{query}%"))

            if not search_conditions:
                return [], 0

            # Build base query with search
            base_query = select(self.model_class).where(or_(*search_conditions))

            # Apply additional filters
            base_query = self._apply_filters(base_query, filters, include_inactive)

            # Get total count
            count_query = select(func.count(self.model_class.id)).where(or_(*search_conditions))
            count_query = self._apply_filters(count_query, filters, include_inactive)
            count_result = await self.db.execute(count_query)
            total_count = count_result.scalar()

            # Apply pagination and ordering
            query_with_pagination = (
                base_query.order_by(self.model_class.created_at.desc()).offset(skip).limit(limit)
            )

            # Execute query
            result = await self.db.execute(query_with_pagination)
            entities = result.scalars().all()

            self._logger.debug(
                f"Search returned {len(entities)} {self.model_class.__name__} entities"
            )
            return list(entities), total_count

        except Exception as e:
            self._logger.error(f"Failed to search {self.model_class.__name__}: {e}")
            raise

    # === Helper Methods ===

    def _apply_filters(
        self, query: Select, filters: Optional[dict[str, Any]], include_inactive: bool
    ) -> Select:
        """Apply common filters to query."""
        # Apply active filter unless explicitly including inactive
        if not include_inactive and hasattr(self.model_class, "is_active"):
            query = query.where(self.model_class.is_active is True)

        # Apply custom filters
        if filters:
            conditions = []

            for key, value in filters.items():
                if not hasattr(self.model_class, key):
                    continue

                column = getattr(self.model_class, key)

                # Handle different filter types
                if isinstance(value, list):
                    conditions.append(column.in_(value))
                elif isinstance(value, dict):
                    # Handle range filters
                    if "gte" in value:
                        conditions.append(column >= value["gte"])
                    if "lte" in value:
                        conditions.append(column <= value["lte"])
                    if "gt" in value:
                        conditions.append(column > value["gt"])
                    if "lt" in value:
                        conditions.append(column < value["lt"])
                elif isinstance(value, str) and "%" in value:
                    # Handle LIKE patterns
                    conditions.append(column.ilike(value))
                else:
                    # Exact match
                    conditions.append(column == value)

            if conditions:
                query = query.where(and_(*conditions))

        return query

    async def get_with_relations(
        self, entity_id: UUID, relations: list[str]
    ) -> Optional[ModelType]:
        """Get entity with specified relationships loaded."""
        try:
            query = select(self.model_class).where(self.model_class.id == entity_id)

            # Add relationship loading
            for relation in relations:
                if hasattr(self.model_class, relation):
                    query = query.options(selectinload(getattr(self.model_class, relation)))

            result = await self.db.execute(query)
            entity = result.scalar_one_or_none()

            return entity

        except Exception as e:
            self._logger.error(f"Failed to get {self.model_class.__name__} with relations: {e}")
            raise

    async def refresh_entity(self, entity: ModelType) -> ModelType:
        """Refresh entity from database."""
        await self.db.refresh(entity)
        return entity

    def get_model_class(self) -> type[ModelType]:
        """Get the model class for this repository."""
        return self.model_class

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(model={self.model_class.__name__})>"

__all__ = ["BaseRepository"]

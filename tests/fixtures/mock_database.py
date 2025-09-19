"""
Mock Database Fixtures for Testing
Provides SQLAlchemy mocks and database-related test utilities.
"""

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any, AsyncGenerator, Dict, List, Optional, Type
from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeMeta, declarative_base

Base = declarative_base()


class MockModel(Base):
    """Generic mock SQLAlchemy model for testing."""

    __tablename__ = "mock_table"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    created_at = Column(String)
    updated_at = Column(String)
    tenant_id = Column(String)


class MockAsyncSession:
    """Mock SQLAlchemy async session with common operations."""

    def __init__(self):
        self.data: Dict[str, List[Any]] = {}
        self.committed = False
        self.rolled_back = False
        self.closed = False
        self.flushed = False
        self._deleted = []
        self._added = []
        self._dirty = []
        self.execute = AsyncMock(return_value=MockResult([]))
        self.scalar = AsyncMock()
        self.scalars = AsyncMock(return_value=MockScalars([]))

    async def commit(self):
        self.committed = True
        for item in self._added:
            if not hasattr(item, 'id') or item.id is None:
                item.id = len(self.data.get(item.__class__.__name__, [])) + 1
            class_name = item.__class__.__name__
            if class_name not in self.data:
                self.data[class_name] = []
            self.data[class_name].append(item)
        self._added.clear()
        self._dirty.clear()

    async def rollback(self):
        self.rolled_back = True
        self._added.clear()
        self._dirty.clear()
        self._deleted.clear()

    async def close(self):
        self.closed = True

    async def flush(self):
        self.flushed = True

    def add(self, instance):
        self._added.append(instance)

    def add_all(self, instances):
        self._added.extend(instances)

    async def refresh(self, instance):
        pass

    def delete(self, instance):
        self._deleted.append(instance)

    async def get(self, entity: Type, ident):
        class_name = entity.__name__
        items = self.data.get(class_name, [])
        for item in items:
            if getattr(item, 'id', None) == ident:
                return item
        return None

    def query(self, *entities):
        return MockQuery(self, entities)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.rollback()
        else:
            await self.commit()
        await self.close()


class MockResult:
    """Mock result object for SQLAlchemy execute."""

    def __init__(self, data: List[Any]):
        self._data = data
        self.rowcount = len(data)

    def all(self):
        return self._data

    def first(self):
        return self._data[0] if self._data else None

    def one(self):
        if not self._data:
            raise Exception("No results found")
        return self._data[0]

    def scalar(self):
        if self._data and len(self._data) > 0:
            row = self._data[0]
            if hasattr(row, '__getitem__'):
                return row[0]
            return row
        return None

    def scalars(self):
        return MockScalars(self._data)


class MockScalars:
    """Mock scalars result for SQLAlchemy."""

    def __init__(self, data: List[Any]):
        self._data = data

    def all(self):
        return self._data

    def first(self):
        return self._data[0] if self._data else None

    def one(self):
        if not self._data:
            raise Exception("No results found")
        return self._data[0]

    def unique(self):
        return MockScalars(list(set(self._data)))


class MockQuery:
    """Mock query object for SQLAlchemy-style queries."""

    def __init__(self, session: MockAsyncSession, entities):
        self.session = session
        self.entities = entities
        self._filters = []
        self._limit = None
        self._offset = None
        self._order_by = None

    def filter(self, *args):
        self._filters.extend(args)
        return self

    def filter_by(self, **kwargs):
        self._filters.append(kwargs)
        return self

    def limit(self, limit: int):
        self._limit = limit
        return self

    def offset(self, offset: int):
        self._offset = offset
        return self

    def order_by(self, *args):
        self._order_by = args
        return self

    async def all(self):
        if self.entities:
            class_name = self.entities[0].__name__
            results = self.session.data.get(class_name, [])
            if self._limit:
                results = results[:self._limit]
            return results
        return []

    async def first(self):
        results = await self.all()
        return results[0] if results else None

    async def one(self):
        results = await self.all()
        if not results:
            raise Exception("No results found")
        return results[0]

    async def count(self):
        results = await self.all()
        return len(results)

    def exists(self):
        return MockExists(self)


class MockExists:
    """Mock exists query."""

    def __init__(self, query: MockQuery):
        self.query = query

    async def scalar(self):
        results = await self.query.all()
        return len(results) > 0


class MockSessionMaker:
    """Mock sessionmaker for database session creation."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.sessions: List[MockAsyncSession] = []

    def __call__(self) -> MockAsyncSession:
        session = MockAsyncSession()
        self.sessions.append(session)
        return session

    async def __aenter__(self) -> MockAsyncSession:
        return self()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    @asynccontextmanager
    async def begin(self) -> AsyncGenerator[MockAsyncSession, None]:
        session = self()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class MockRepository:
    """Base mock repository for testing repository patterns."""

    def __init__(self, session: Optional[MockAsyncSession] = None):
        self.session = session or MockAsyncSession()
        self.call_history: List[Dict[str, Any]] = []

    async def get_by_id(self, entity_id: Any) -> Optional[Any]:
        self.call_history.append({"method": "get_by_id", "args": {"id": entity_id}})
        return await self.session.get(MockModel, entity_id)

    async def create(self, **kwargs) -> Any:
        self.call_history.append({"method": "create", "args": kwargs})
        entity = MockModel(**kwargs)
        self.session.add(entity)
        await self.session.commit()
        return entity

    async def update(self, entity_id: Any, **kwargs) -> Optional[Any]:
        self.call_history.append({"method": "update", "args": {"id": entity_id, **kwargs}})
        entity = await self.get_by_id(entity_id)
        if entity:
            for key, value in kwargs.items():
                setattr(entity, key, value)
            await self.session.commit()
        return entity

    async def delete(self, entity_id: Any) -> bool:
        self.call_history.append({"method": "delete", "args": {"id": entity_id}})
        entity = await self.get_by_id(entity_id)
        if entity:
            self.session.delete(entity)
            await self.session.commit()
            return True
        return False

    async def list(self, limit: int = 100, offset: int = 0) -> List[Any]:
        self.call_history.append({"method": "list", "args": {"limit": limit, "offset": offset}})
        return self.session.data.get(MockModel.__name__, [])[offset:offset + limit]


class MockDatabaseModule:
    """Mock for the entire database module."""

    def __init__(self):
        self.session_maker = MockSessionMaker()
        self.engine = Mock()
        self.Base = Base

    async def initialize(self):
        """Mock database initialization."""
        pass

    async def cleanup(self):
        """Mock database cleanup."""
        pass

    def get_session(self) -> MockAsyncSession:
        """Get a mock database session."""
        return self.session_maker()


@pytest.fixture
def mock_session():
    """Fixture providing a mock async session."""
    return MockAsyncSession()


@pytest.fixture
def mock_session_maker():
    """Fixture providing a mock session maker."""
    return MockSessionMaker()


@pytest.fixture
def mock_repository(mock_session):
    """Fixture providing a mock repository."""
    return MockRepository(mock_session)


@pytest.fixture
def mock_db_module():
    """Fixture providing a complete mock database module."""
    return MockDatabaseModule()


def create_mock_entity(
    entity_class: Type = MockModel,
    **kwargs
) -> Any:
    """
    Helper to create mock entities with default values.

    Args:
        entity_class: The entity class to instantiate
        **kwargs: Override default values

    Returns:
        Mock entity instance
    """
    defaults = {
        "id": kwargs.get("id", str(uuid4())),
        "created_at": kwargs.get("created_at", datetime.now(UTC).isoformat()),
        "updated_at": kwargs.get("updated_at", datetime.now(UTC).isoformat()),
        "tenant_id": kwargs.get("tenant_id", "test-tenant"),
    }

    if entity_class == MockModel:
        defaults["name"] = kwargs.get("name", "test-entity")

    defaults.update(kwargs)
    return entity_class(**defaults)


class MockTransaction:
    """Mock database transaction context manager."""

    def __init__(self, session: MockAsyncSession):
        self.session = session
        self.started = False
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self):
        self.started = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.rollback()
        else:
            await self.commit()

    async def commit(self):
        self.committed = True
        await self.session.commit()

    async def rollback(self):
        self.rolled_back = True
        await self.session.rollback()
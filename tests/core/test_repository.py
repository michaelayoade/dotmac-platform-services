"""Tests for core repository module."""

from datetime import datetime
from typing import Any, Optional
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.core.repository import (
    AsyncRepository,
    AsyncUnitOfWork,
    DuplicateEntityError,
    EntityNotFoundError,
    IRepository,
    IUnitOfWork,
    RepositoryError,
    SyncRepository,
)
from dotmac.platform.database import Base
from sqlalchemy import Column, Integer, String as SQLString


# Mock model for testing
class TestModel(Base):
    """Test model for repository tests."""

    __tablename__ = "test_model"

    id = Column(Integer, primary_key=True)
    name = Column(SQLString)


@pytest.mark.unit
class TestRepositoryExceptions:
    """Test repository exceptions."""

    def test_repository_error(self):
        """Test RepositoryError exception."""
        error = RepositoryError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_entity_not_found_error(self):
        """Test EntityNotFoundError exception."""
        error = EntityNotFoundError("Entity not found")
        assert str(error) == "Entity not found"
        assert isinstance(error, RepositoryError)

    def test_duplicate_entity_error(self):
        """Test DuplicateEntityError exception."""
        error = DuplicateEntityError("Duplicate entity")
        assert str(error) == "Duplicate entity"
        assert isinstance(error, RepositoryError)


@pytest.mark.unit
class TestIRepository:
    """Test IRepository abstract base class."""

    def test_irepository_is_abstract(self):
        """Test that IRepository cannot be instantiated."""
        with pytest.raises(TypeError):
            IRepository()

    def test_irepository_defines_interface(self):
        """Test that IRepository defines the required interface."""

        class TestRepo(IRepository):
            """Test repository implementation."""

            async def get(self, id: Any) -> Any:
                return {"id": id}

            async def get_all(self, skip: int = 0, limit: int = 100) -> list:
                return []

            async def get_by(self, **filters) -> list:
                return []

            async def create(self, data: Any) -> Any:
                return data

            async def update(self, id: Any, data: Any) -> Any:
                return data

            async def delete(self, id: Any) -> bool:
                return True

            async def exists(self, id: Any) -> bool:
                return True

            async def count(self, **filters) -> int:
                return 0

        repo = TestRepo()
        assert isinstance(repo, IRepository)


@pytest.mark.unit
class TestAsyncRepository:
    """Test AsyncRepository class."""

    @pytest.mark.asyncio
    async def test_async_repository_init(self):
        """Test AsyncRepository initialization."""
        session = AsyncMock(spec=AsyncSession)
        repo = AsyncRepository(session, TestModel, TestModel, TestModel)

        assert repo.session == session
        assert repo.model == TestModel

    @pytest.mark.asyncio
    async def test_get(self):
        """Test get method."""
        session = AsyncMock(spec=AsyncSession)
        mock_result = Mock()
        test_obj = TestModel()
        test_obj.id = 1
        test_obj.name = "test"
        mock_result.unique.return_value.scalar_one_or_none.return_value = test_obj
        session.execute.return_value = mock_result

        repo = AsyncRepository(session, TestModel, TestModel, TestModel)
        result = await repo.get(1)

        assert result is not None
        assert result.id == 1
        session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_not_found(self):
        """Test get with non-existent ID."""
        session = AsyncMock(spec=AsyncSession)
        mock_result = Mock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        repo = AsyncRepository(session, TestModel, TestModel, TestModel)
        result = await repo.get(999)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_all(self):
        """Test get_all method."""
        session = AsyncMock(spec=AsyncSession)
        mock_result = Mock()
        test_obj1 = TestModel()
        test_obj1.id = 1
        test_obj1.name = "test1"
        test_obj2 = TestModel()
        test_obj2.id = 2
        test_obj2.name = "test2"
        mock_result.unique.return_value.scalars.return_value.all.return_value = [
            test_obj1,
            test_obj2,
        ]
        session.execute.return_value = mock_result

        repo = AsyncRepository(session, TestModel, TestModel, TestModel)
        results = await repo.get_all()

        assert len(results) == 2
        session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create(self):
        """Test create method."""
        session = AsyncMock(spec=AsyncSession)
        repo = AsyncRepository(session, TestModel, dict, TestModel)

        data = {"name": "test"}
        result = await repo.create(data)

        session.add.assert_called_once()
        session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_update(self):
        """Test update method."""
        session = AsyncMock(spec=AsyncSession)
        mock_result = Mock()
        mock_obj = TestModel()
        mock_obj.id = 1
        mock_obj.name = "old"
        mock_result.unique.return_value.scalar_one_or_none.return_value = mock_obj
        session.execute.return_value = mock_result

        repo = AsyncRepository(session, TestModel, TestModel, dict)
        result = await repo.update(1, {"name": "new"})

        assert result is not None
        session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_not_found_raises(self):
        """Test update with non-existent ID raises error."""
        session = AsyncMock(spec=AsyncSession)
        mock_result = Mock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        repo = AsyncRepository(session, TestModel, TestModel, dict)

        with pytest.raises(EntityNotFoundError):
            await repo.update(999, {"name": "new"})

    @pytest.mark.asyncio
    async def test_delete(self):
        """Test delete method."""
        session = AsyncMock(spec=AsyncSession)
        mock_result = Mock()
        mock_obj = TestModel()
        mock_obj.id = 1
        mock_obj.name = "test"
        mock_result.unique.return_value.scalar_one_or_none.return_value = mock_obj
        session.execute.return_value = mock_result

        repo = AsyncRepository(session, TestModel, TestModel, TestModel)
        result = await repo.delete(1)

        assert result is True
        session.delete.assert_called_once_with(mock_obj)
        session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self):
        """Test delete with non-existent ID."""
        session = AsyncMock(spec=AsyncSession)
        mock_result = Mock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        repo = AsyncRepository(session, TestModel, TestModel, TestModel)
        result = await repo.delete(999)

        assert result is False
        session.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_exists(self):
        """Test exists method."""
        session = AsyncMock(spec=AsyncSession)
        mock_result = Mock()
        mock_result.scalar.return_value = True
        session.execute.return_value = mock_result

        repo = AsyncRepository(session, TestModel, TestModel, TestModel)
        exists = await repo.exists(1)

        assert exists is True

    @pytest.mark.asyncio
    async def test_count(self):
        """Test count method."""
        session = AsyncMock(spec=AsyncSession)
        mock_result = Mock()
        mock_result.scalar.return_value = 5
        session.execute.return_value = mock_result

        repo = AsyncRepository(session, TestModel, TestModel, TestModel)
        count = await repo.count()

        assert count == 5


@pytest.mark.unit
class TestSyncRepository:
    """Test SyncRepository class."""

    def test_sync_repository_init(self):
        """Test SyncRepository initialization."""
        session = Mock()
        repo = SyncRepository(session, TestModel, TestModel, TestModel)

        assert repo.session == session
        assert repo.model == TestModel

    def test_get(self):
        """Test get method."""
        session = Mock()
        mock_result = Mock()
        test_obj = TestModel()
        test_obj.id = 1
        test_obj.name = "test"
        mock_result.unique.return_value.scalar_one_or_none.return_value = test_obj
        session.execute.return_value = mock_result

        repo = SyncRepository(session, TestModel, TestModel, TestModel)
        result = repo.get(1)

        assert result is not None
        assert result.id == 1
        session.execute.assert_called_once()

    def test_create(self):
        """Test create method."""
        session = Mock()
        repo = SyncRepository(session, TestModel, dict, TestModel)

        data = {"name": "test"}
        result = repo.create(data)

        session.add.assert_called_once()
        session.flush.assert_called_once()

    def test_update(self):
        """Test update method."""
        session = Mock()
        mock_result = Mock()
        mock_obj = TestModel()
        mock_obj.id = 1
        mock_obj.name = "old"
        mock_result.unique.return_value.scalar_one_or_none.return_value = mock_obj
        session.execute.return_value = mock_result

        # Create a mock Pydantic model for update
        update_data = Mock()
        update_data.model_dump.return_value = {"name": "new"}

        repo = SyncRepository(session, TestModel, TestModel, Mock)
        result = repo.update(1, update_data)

        assert result is not None
        session.flush.assert_called_once()

    def test_delete(self):
        """Test delete method."""
        session = Mock()
        mock_result = Mock()
        mock_obj = TestModel()
        mock_obj.id = 1
        mock_obj.name = "test"
        mock_result.unique.return_value.scalar_one_or_none.return_value = mock_obj
        session.execute.return_value = mock_result

        repo = SyncRepository(session, TestModel, TestModel, TestModel)
        result = repo.delete(1)

        assert result is True
        session.delete.assert_called_once_with(mock_obj)
        session.flush.assert_called_once()


@pytest.mark.unit
class TestIUnitOfWork:
    """Test IUnitOfWork abstract base class."""

    def test_iunit_of_work_is_abstract(self):
        """Test that IUnitOfWork cannot be instantiated."""
        with pytest.raises(TypeError):
            IUnitOfWork()

    def test_iunit_of_work_defines_interface(self):
        """Test that IUnitOfWork defines the required interface."""

        class TestUoW(IUnitOfWork):
            """Test unit of work implementation."""

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

            async def commit(self):
                pass

            async def rollback(self):
                pass

        uow = TestUoW()
        assert isinstance(uow, IUnitOfWork)


@pytest.mark.unit
class TestAsyncUnitOfWork:
    """Test AsyncUnitOfWork class."""

    @pytest.mark.asyncio
    async def test_unit_of_work_context_manager(self):
        """Test unit of work as context manager."""
        session_factory = AsyncMock()
        session = AsyncMock(spec=AsyncSession)
        session_factory.return_value = session

        uow = AsyncUnitOfWork(session_factory)

        async with uow:
            assert uow.session == session

        session.commit.assert_called_once()
        session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_unit_of_work_rollback_on_error(self):
        """Test unit of work rollback on error."""
        session_factory = AsyncMock()
        session = AsyncMock(spec=AsyncSession)
        session_factory.return_value = session

        uow = AsyncUnitOfWork(session_factory)

        with pytest.raises(ValueError):
            async with uow:
                raise ValueError("Test error")

        session.rollback.assert_called_once()
        session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_unit_of_work_explicit_commit(self):
        """Test explicit commit."""
        session_factory = AsyncMock()
        session = AsyncMock(spec=AsyncSession)
        session_factory.return_value = session

        uow = AsyncUnitOfWork(session_factory)

        async with uow:
            await uow.commit()

        # Commit called twice: once explicitly, once on exit
        assert session.commit.call_count == 2

    @pytest.mark.asyncio
    async def test_unit_of_work_explicit_rollback(self):
        """Test explicit rollback."""
        session_factory = AsyncMock()
        session = AsyncMock(spec=AsyncSession)
        session_factory.return_value = session

        uow = AsyncUnitOfWork(session_factory)

        async with uow:
            await uow.rollback()

        session.rollback.assert_called_once()
        # Commit still called on exit
        session.commit.assert_called_once()
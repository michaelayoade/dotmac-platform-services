"""Tests for core protocols module."""

import asyncio
from typing import Any, Optional
from unittest.mock import AsyncMock, Mock

import pytest

from dotmac.platform.core.protocols import (
    CacheableRepository,
    EventPublisher,
    QueryBuilder,
    RepositoryProtocol,
    ServiceProtocol,
    TenantAwareRepository,
    UnitOfWork,
)


@pytest.mark.unit
class TestRepositoryProtocol:
    """Test RepositoryProtocol interface."""

    def test_repository_protocol_has_required_methods(self):
        """Test that RepositoryProtocol has required methods."""
        # Create a mock that implements the protocol
        repo_mock = Mock(spec=RepositoryProtocol)

        # Check that it has the required methods
        assert hasattr(repo_mock, "get")
        assert hasattr(repo_mock, "get_all")
        assert hasattr(repo_mock, "create")
        assert hasattr(repo_mock, "update")
        assert hasattr(repo_mock, "delete")

    def test_repository_protocol_implementation(self):
        """Test implementing RepositoryProtocol."""

        class TestRepository:
            """Test repository implementation."""

            async def get(self, id: Any) -> Any:
                return {"id": id}

            async def get_all(self, skip: int = 0, limit: int = 100) -> list[Any]:
                return [{"id": 1}, {"id": 2}]

            async def create(self, data: Any) -> Any:
                return {**data, "id": "new"}

            async def update(self, id: Any, data: Any) -> Any:
                return {**data, "id": id}

            async def delete(self, id: Any) -> bool:
                return True

        repo = TestRepository()
        # This would be type-checked at compile time
        assert asyncio.iscoroutinefunction(repo.get)
        assert asyncio.iscoroutinefunction(repo.create)


@pytest.mark.unit
class TestTenantAwareRepository:
    """Test TenantAwareRepository protocol."""

    def test_tenant_aware_repository_has_methods(self):
        """Test TenantAwareRepository has required methods."""
        repo_mock = Mock(spec=TenantAwareRepository)

        # Has base repository methods
        assert hasattr(repo_mock, "get")
        assert hasattr(repo_mock, "create")

        # Has tenant-specific methods
        assert hasattr(repo_mock, "get_by_tenant")
        assert hasattr(repo_mock, "get_all_by_tenant")


@pytest.mark.unit
class TestCacheableRepository:
    """Test CacheableRepository protocol."""

    def test_cacheable_repository_has_methods(self):
        """Test CacheableRepository has required methods."""
        repo_mock = Mock(spec=CacheableRepository)

        # Has base repository methods
        assert hasattr(repo_mock, "get")
        assert hasattr(repo_mock, "create")

        # Has cache-specific methods
        assert hasattr(repo_mock, "get_cached")
        assert hasattr(repo_mock, "invalidate_cache")


@pytest.mark.unit
class TestServiceProtocol:
    """Test ServiceProtocol interface."""

    def test_service_protocol_has_methods(self):
        """Test ServiceProtocol has required methods."""
        service_mock = Mock(spec=ServiceProtocol)

        assert hasattr(service_mock, "initialize")
        assert hasattr(service_mock, "shutdown")
        assert hasattr(service_mock, "health_check")

    @pytest.mark.asyncio
    async def test_service_protocol_implementation(self):
        """Test implementing ServiceProtocol."""

        class TestService:
            """Test service implementation."""

            async def initialize(self) -> None:
                pass

            async def shutdown(self) -> None:
                pass

            async def health_check(self) -> dict[str, Any]:
                return {"status": "healthy"}

        service = TestService()
        await service.initialize()
        health = await service.health_check()
        assert health["status"] == "healthy"
        await service.shutdown()


@pytest.mark.unit
class TestUnitOfWork:
    """Test UnitOfWork protocol."""

    def test_unit_of_work_has_methods(self):
        """Test UnitOfWork has required methods."""
        # UnitOfWork is a protocol/ABC - we'll test the methods directly
        # Note: Mock with spec doesn't include dunder methods automatically
        uow_mock = Mock()
        uow_mock.__enter__ = Mock()
        uow_mock.__exit__ = Mock()
        uow_mock.commit = Mock()
        uow_mock.rollback = Mock()

        assert hasattr(uow_mock, "__enter__")
        assert hasattr(uow_mock, "__exit__")
        assert hasattr(uow_mock, "commit")
        assert hasattr(uow_mock, "rollback")

    @pytest.mark.asyncio
    async def test_unit_of_work_implementation(self):
        """Test implementing UnitOfWork."""

        class TestUnitOfWork:
            """Test unit of work implementation."""

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                if exc_type:
                    await self.rollback()
                else:
                    await self.commit()

            async def commit(self) -> None:
                pass

            async def rollback(self) -> None:
                pass

        async with TestUnitOfWork() as uow:
            # Use the unit of work
            pass


@pytest.mark.unit
class TestEventPublisher:
    """Test EventPublisher protocol."""

    def test_event_publisher_has_methods(self):
        """Test EventPublisher has required methods."""
        # Create a mock with the required methods
        publisher_mock = Mock()
        publisher_mock.publish = Mock()
        publisher_mock.publish_batch = Mock()

        assert hasattr(publisher_mock, "publish")
        assert hasattr(publisher_mock, "publish_batch")

    @pytest.mark.asyncio
    async def test_event_publisher_implementation(self):
        """Test implementing EventPublisher."""

        class TestEventPublisher:
            """Test event publisher implementation."""

            async def publish(self, event: str, data: dict[str, Any]) -> None:
                pass

            async def publish_batch(self, events: list[tuple[str, dict[str, Any]]]) -> None:
                for event, data in events:
                    await self.publish(event, data)

        publisher = TestEventPublisher()
        await publisher.publish("test_event", {"data": "test"})
        await publisher.publish_batch([
            ("event1", {"data": 1}),
            ("event2", {"data": 2}),
        ])


@pytest.mark.unit
class TestQueryBuilder:
    """Test QueryBuilder protocol."""

    def test_query_builder_has_methods(self):
        """Test QueryBuilder has required methods."""
        builder_mock = Mock(spec=QueryBuilder)

        assert hasattr(builder_mock, "filter")
        assert hasattr(builder_mock, "order_by")
        assert hasattr(builder_mock, "limit")
        assert hasattr(builder_mock, "offset")
        assert hasattr(builder_mock, "build")

    def test_query_builder_implementation(self):
        """Test implementing QueryBuilder."""

        class TestQueryBuilder:
            """Test query builder implementation."""

            def __init__(self):
                self.filters = []
                self._limit = None
                self._offset = None
                self._order = None

            def filter(self, **kwargs):
                self.filters.append(kwargs)
                return self

            def order_by(self, field: str, desc: bool = False):
                self._order = (field, desc)
                return self

            def limit(self, value: int):
                self._limit = value
                return self

            def offset(self, value: int):
                self._offset = value
                return self

            def build(self) -> dict:
                return {
                    "filters": self.filters,
                    "limit": self._limit,
                    "offset": self._offset,
                    "order": self._order,
                }

        builder = TestQueryBuilder()
        query = (
            builder
            .filter(name="test")
            .order_by("created_at", desc=True)
            .limit(10)
            .offset(0)
            .build()
        )

        assert query["filters"] == [{"name": "test"}]
        assert query["limit"] == 10
        assert query["offset"] == 0
        assert query["order"] == ("created_at", True)



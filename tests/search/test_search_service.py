"""Tests for the search service abstractions and in-memory backend."""

from unittest.mock import AsyncMock

import pytest

from dotmac.platform.search.interfaces import SearchFilter, SearchQuery, SearchType, SortOrder
from dotmac.platform.search.service import (
    InMemorySearchBackend,
    SearchService,
    create_search_backend_from_env,
)


@pytest.mark.asyncio
async def test_inmemory_backend_filters_sorting_and_pagination():
    backend = InMemorySearchBackend()
    await backend.index("business_customer", "1", {"name": "Alice", "status": "active"})
    await backend.index("business_customer", "2", {"name": "Bob", "status": "inactive"})
    await backend.index("business_customer", "3", {"name": "Charlie", "status": "active"})

    query = SearchQuery(
        query="",
        filters=[SearchFilter(field="status", value="active", operator="eq")],
        sort_by="name",
        sort_order=SortOrder.ASC,
        limit=1,
        offset=0,
    )

    first_page = await backend.search("business_customer", query)

    assert first_page.total == 2
    assert [result.id for result in first_page.results] == ["1"]

    query.offset = 1
    second_page = await backend.search("business_customer", query)
    assert [result.id for result in second_page.results] == ["3"]


@pytest.mark.asyncio
async def test_inmemory_backend_scoring_orders_results():
    backend = InMemorySearchBackend()
    await backend.index(
        "business_article",
        "a",
        {"title": "alpha alpha", "body": "alpha beta"},
    )
    await backend.index(
        "business_article",
        "b",
        {"title": "alpha", "body": "gamma"},
    )

    query = SearchQuery(
        query="alpha",
        search_type=SearchType.FULL_TEXT,
        include_score=True,
        fields=["title", "body"],
    )

    response = await backend.search("business_article", query)

    assert response.total == 2
    assert [res.id for res in response.results] == ["a", "b"]
    assert response.results[0].score >= response.results[1].score


@pytest.mark.asyncio
async def test_search_service_delegates_to_backend():
    backend = AsyncMock()
    backend.index = AsyncMock(return_value=True)
    backend.search = AsyncMock(return_value="results")
    backend.delete = AsyncMock(return_value=True)

    service = SearchService(backend=backend)

    await service.index_business_entity("customer", "42", {"name": "Alice"})
    backend.index.assert_awaited_once_with("business_customer", "42", {"name": "Alice"})

    query = SearchQuery(query="alice")
    await service.search_business_entities("customer", query)
    backend.search.assert_awaited_once_with("business_customer", query)

    await service.delete_business_entity("customer", "42")
    backend.delete.assert_awaited_once_with("business_customer", "42")


@pytest.mark.asyncio
async def test_inmemory_backend_bulk_and_delete_index():
    backend = InMemorySearchBackend()
    payloads = [
        {"id": "1", "name": "one"},
        {"id": "2", "name": "two"},
    ]

    count = await backend.bulk_index("business_order", payloads)
    assert count == 2

    query = SearchQuery(query="", limit=10, offset=0)
    response = await backend.search("business_order", query)
    assert response.total == 2

    await backend.delete_index("business_order")
    empty = await backend.search("business_order", query)
    assert empty.total == 0


def test_create_search_backend_from_env_defaults(monkeypatch):
    monkeypatch.delenv("SEARCH_BACKEND", raising=False)
    backend = create_search_backend_from_env()
    assert isinstance(backend, InMemorySearchBackend)

    monkeypatch.setenv("SEARCH_BACKEND", "memory")
    backend = create_search_backend_from_env()
    assert isinstance(backend, InMemorySearchBackend)

    monkeypatch.setenv("SEARCH_BACKEND", "unknown")
    backend = create_search_backend_from_env()
    assert isinstance(backend, InMemorySearchBackend)

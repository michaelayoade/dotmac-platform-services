"""
Tests for search service implementation.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch

from dotmac.platform.search.service import (
    InMemorySearchBackend,
    MeilisearchBackend,
    SearchService,
)
from dotmac.platform.search.interfaces import (
    SearchFilter,
    SearchQuery,
    SearchResponse,
    SearchResult,
    SearchType,
    SortOrder,
)


class TestInMemorySearchBackend:
    """Test InMemorySearchBackend class."""

    @pytest.fixture
    def backend(self):
        """Create in-memory search backend."""
        return InMemorySearchBackend()

    @pytest.fixture
    async def populated_backend(self, backend):
        """Create backend with test data."""
        await backend.create_index("test_index")
        test_docs = [
            {"id": "1", "title": "Python Programming", "content": "Learn Python basics", "category": "tech", "score": 10},
            {"id": "2", "title": "Data Science", "content": "Advanced data analysis", "category": "tech", "score": 8},
            {"id": "3", "title": "Web Development", "content": "Build web applications", "category": "tech", "score": 9},
            {"id": "4", "title": "Marketing Tips", "content": "Digital marketing strategies", "category": "business", "score": 7},
        ]

        for doc in test_docs:
            doc_id = doc.pop("id")
            await backend.index("test_index", doc_id, doc)

        return backend

    async def test_index_document(self, backend):
        """Test indexing a document."""
        doc = {"title": "Test Doc", "content": "Test content"}
        result = await backend.index("test_index", "doc1", doc)

        assert result is True
        assert "test_index" in backend.indices
        assert "doc1" in backend.indices["test_index"]
        assert backend.indices["test_index"]["doc1"] == doc

    async def test_search_basic_query(self, populated_backend):
        """Test basic text search."""
        query = SearchQuery(query="Python", limit=10)
        response = await populated_backend.search("test_index", query)

        assert isinstance(response, SearchResponse)
        assert len(response.results) == 1
        assert response.results[0].id == "1"
        assert response.total == 1
        assert response.took_ms >= 0

    async def test_search_multiple_results(self, populated_backend):
        """Test search returning multiple results."""
        query = SearchQuery(query="tech", limit=10)
        response = await populated_backend.search("test_index", query)

        assert len(response.results) >= 1  # Should find documents with "tech" category
        assert response.total >= 1

    async def test_search_with_filters(self, populated_backend):
        """Test search with filters."""
        filter_tech = SearchFilter(field="category", operator="eq", value="tech")
        query = SearchQuery(query="", filters=[filter_tech], limit=10)
        response = await populated_backend.search("test_index", query)

        assert len(response.results) == 3  # 3 tech documents
        for result in response.results:
            assert result.data["category"] == "tech"

    async def test_search_filter_operators(self, populated_backend):
        """Test different filter operators."""
        # Test greater than
        filter_gt = SearchFilter(field="score", operator="gt", value=8)
        query = SearchQuery(query="", filters=[filter_gt], limit=10)
        response = await populated_backend.search("test_index", query)

        assert len(response.results) == 2  # docs with score > 8 (10, 9)

        # Test less than equal
        filter_lte = SearchFilter(field="score", operator="lte", value=8)
        query = SearchQuery(query="", filters=[filter_lte], limit=10)
        response = await populated_backend.search("test_index", query)

        assert len(response.results) == 2  # docs with score <= 8 (8, 7)

    async def test_search_with_sorting(self, populated_backend):
        """Test search with sorting."""
        query = SearchQuery(
            query="",
            sort_by="score",
            sort_order=SortOrder.DESC,
            limit=10
        )
        response = await populated_backend.search("test_index", query)

        scores = [result.data["score"] for result in response.results]
        assert scores == sorted(scores, reverse=True)

    async def test_search_with_pagination(self, populated_backend):
        """Test search pagination."""
        query = SearchQuery(query="", limit=2, offset=0)
        response1 = await populated_backend.search("test_index", query)

        query.offset = 2
        response2 = await populated_backend.search("test_index", query)

        assert len(response1.results) == 2
        assert len(response2.results) == 2
        assert response1.results != response2.results

    async def test_search_empty_index(self, backend):
        """Test search on empty index."""
        query = SearchQuery(query="test", limit=10)
        response = await backend.search("nonexistent", query)

        assert response.results == []
        assert response.total == 0

    async def test_search_types(self, populated_backend):
        """Test different search types."""
        # Exact search
        query = SearchQuery(query="Python", search_type=SearchType.EXACT, limit=10)
        response = await populated_backend.search("test_index", query)
        assert len(response.results) >= 1

        # Prefix search
        query = SearchQuery(query="Pyth", search_type=SearchType.PREFIX, limit=10)
        response = await populated_backend.search("test_index", query)
        assert len(response.results) >= 1

        # Regex search
        query = SearchQuery(query="P.*n", search_type=SearchType.REGEX, limit=10)
        response = await populated_backend.search("test_index", query)
        assert len(response.results) >= 1

    async def test_delete_document(self, populated_backend):
        """Test deleting a document."""
        result = await populated_backend.delete("test_index", "1")
        assert result is True

        # Verify document is gone
        query = SearchQuery(query="Python", limit=10)
        response = await populated_backend.search("test_index", query)
        assert len(response.results) == 0

    async def test_delete_nonexistent_document(self, backend):
        """Test deleting non-existent document."""
        result = await backend.delete("test_index", "nonexistent")
        assert result is False

    async def test_update_document(self, populated_backend):
        """Test updating a document."""
        updates = {"title": "Updated Python Programming", "new_field": "new_value"}
        result = await populated_backend.update("test_index", "1", updates)
        assert result is True

        # Verify update
        doc = populated_backend.indices["test_index"]["1"]
        assert doc["title"] == "Updated Python Programming"
        assert doc["new_field"] == "new_value"
        assert "content" in doc  # Original field should remain

    async def test_update_nonexistent_document(self, backend):
        """Test updating non-existent document."""
        result = await backend.update("test_index", "nonexistent", {"title": "Test"})
        assert result is False

    async def test_bulk_index(self, backend):
        """Test bulk indexing documents."""
        docs = [
            {"id": "bulk1", "title": "Bulk Doc 1"},
            {"id": "bulk2", "title": "Bulk Doc 2"},
            {"id": "bulk3", "title": "Bulk Doc 3"},
        ]

        count = await backend.bulk_index("bulk_index", docs)
        assert count == 3

        # Verify documents were indexed
        query = SearchQuery(query="Bulk", limit=10)
        response = await backend.search("bulk_index", query)
        assert len(response.results) == 3

    async def test_bulk_index_missing_id(self, backend):
        """Test bulk indexing with missing IDs."""
        docs = [
            {"title": "No ID Doc 1"},
            {"id": "bulk2", "title": "Bulk Doc 2"},
        ]

        count = await backend.bulk_index("bulk_index", docs)
        assert count == 1  # Only one document with ID should be indexed

    async def test_create_index(self, backend):
        """Test creating an index."""
        result = await backend.create_index("new_index")
        assert result is True
        assert "new_index" in backend.indices

    async def test_create_existing_index(self, backend):
        """Test creating an existing index."""
        await backend.create_index("existing_index")
        result = await backend.create_index("existing_index")
        assert result is True  # Should not fail

    async def test_delete_index(self, populated_backend):
        """Test deleting an index."""
        result = await populated_backend.delete_index("test_index")
        assert result is True
        assert "test_index" not in populated_backend.indices

    async def test_delete_nonexistent_index(self, backend):
        """Test deleting non-existent index."""
        result = await backend.delete_index("nonexistent")
        assert result is False

    async def test_score_calculation(self, populated_backend):
        """Test relevance score calculation."""
        query = SearchQuery(query="Python", include_score=True, limit=10)
        response = await populated_backend.search("test_index", query)

        assert len(response.results) >= 1
        for result in response.results:
            assert result.score is not None
            assert 0 <= result.score <= 1.0

    async def test_field_specific_search(self, populated_backend):
        """Test searching specific fields."""
        query = SearchQuery(query="Python", fields=["title"], limit=10)
        response = await populated_backend.search("test_index", query)

        assert len(response.results) >= 1
        # Should find document with "Python" in title

    async def test_complex_filters(self, populated_backend):
        """Test complex filter combinations."""
        # Multiple filters
        filter1 = SearchFilter(field="category", operator="eq", value="tech")
        filter2 = SearchFilter(field="score", operator="gte", value=9)

        query = SearchQuery(query="", filters=[filter1, filter2], limit=10)
        response = await populated_backend.search("test_index", query)

        # Should find documents that are tech AND have score >= 9
        for result in response.results:
            assert result.data["category"] == "tech"
            assert result.data["score"] >= 9


class TestMeilisearchBackend:
    """Test MeilisearchBackend class."""

    @pytest.fixture
    def mock_client(self):
        """Create mock Meilisearch client."""
        return Mock()

    @pytest.fixture
    def mock_index(self):
        """Create mock Meilisearch index."""
        return Mock()

    @patch('dotmac.platform.search.service.require_meilisearch')
    @patch('os.getenv')
    def test_meilisearch_backend_init(self, mock_getenv, mock_require):
        """Test MeilisearchBackend initialization."""
        mock_meilisearch = Mock()
        mock_client = Mock()
        mock_meilisearch.Client.return_value = mock_client
        mock_require.return_value = mock_meilisearch

        mock_getenv.side_effect = lambda key, default=None: {
            "MEILISEARCH_HOST": "http://test:7700",
            "MEILISEARCH_API_KEY": "test-key"
        }.get(key, default)

        backend = MeilisearchBackend()

        assert backend.host == "http://test:7700"
        assert backend.api_key == "test-key"
        assert backend.primary_key == "id"
        assert backend.client == mock_client
        mock_meilisearch.Client.assert_called_once_with("http://test:7700", "test-key")

    @patch('dotmac.platform.search.service.require_meilisearch')
    def test_meilisearch_backend_custom_config(self, mock_require):
        """Test MeilisearchBackend with custom configuration."""
        mock_meilisearch = Mock()
        mock_client = Mock()
        mock_meilisearch.Client.return_value = mock_client
        mock_require.return_value = mock_meilisearch

        backend = MeilisearchBackend(
            host="http://custom:8700",
            api_key="custom-key",
            primary_key="custom_id"
        )

        assert backend.host == "http://custom:8700"
        assert backend.api_key == "custom-key"
        assert backend.primary_key == "custom_id"

    @patch('dotmac.platform.search.service.require_meilisearch')
    async def test_meilisearch_index(self, mock_require):
        """Test MeilisearchBackend index method."""
        mock_meilisearch = Mock()
        mock_client = Mock()
        mock_index = Mock()

        mock_meilisearch.Client.return_value = mock_client
        mock_client.get_index.return_value = mock_index
        mock_require.return_value = mock_meilisearch

        backend = MeilisearchBackend()

        doc = {"title": "Test Document", "content": "Test content"}
        result = await backend.index("test_index", "doc1", doc)

        assert result is True
        mock_index.add_documents.assert_called_once()
        call_args = mock_index.add_documents.call_args
        assert call_args[0][0][0]["id"] == "doc1"
        assert call_args[0][0][0]["title"] == "Test Document"

    @patch('dotmac.platform.search.service.require_meilisearch')
    async def test_meilisearch_search(self, mock_require):
        """Test MeilisearchBackend search method."""
        mock_meilisearch = Mock()
        mock_client = Mock()
        mock_index = Mock()

        mock_search_response = {
            "hits": [
                {
                    "id": "doc1",
                    "title": "Test Document",
                    "_rankingScore": 0.95,
                    "_formatted": {"title": "Test <mark>Document</mark>"}
                }
            ],
            "estimatedTotalHits": 1,
            "processingTimeMs": 5
        }

        mock_meilisearch.Client.return_value = mock_client
        mock_client.get_index.return_value = mock_index
        mock_index.search.return_value = mock_search_response
        mock_require.return_value = mock_meilisearch

        backend = MeilisearchBackend()

        query = SearchQuery(query="test", limit=10)
        response = await backend.search("test_index", query)

        assert isinstance(response, SearchResponse)
        assert len(response.results) == 1
        assert response.results[0].id == "doc1"
        assert response.results[0].score == 0.95
        assert response.total == 1
        assert response.took_ms == 5

    @patch('dotmac.platform.search.service.require_meilisearch')
    async def test_meilisearch_delete(self, mock_require):
        """Test MeilisearchBackend delete method."""
        mock_meilisearch = Mock()
        mock_client = Mock()
        mock_index = Mock()

        mock_meilisearch.Client.return_value = mock_client
        mock_client.get_index.return_value = mock_index
        mock_require.return_value = mock_meilisearch

        backend = MeilisearchBackend()

        result = await backend.delete("test_index", "doc1")

        assert result is True
        mock_index.delete_document.assert_called_once_with("doc1")

    @patch('dotmac.platform.search.service.require_meilisearch')
    async def test_meilisearch_filters(self, mock_require):
        """Test MeilisearchBackend filter conversion."""
        mock_meilisearch = Mock()
        mock_client = Mock()
        mock_require.return_value = mock_meilisearch

        backend = MeilisearchBackend()

        # Test filter conversion
        filters = [
            SearchFilter(field="category", operator="eq", value="tech"),
            SearchFilter(field="tags", operator="in", value=["python", "web"]),
        ]

        expression = backend._filters_to_expression(filters)
        expected = 'category = "tech" AND tags IN ["python", "web"]'
        assert expression == expected

    def test_meilisearch_filter_expression_empty(self):
        """Test empty filter expression."""
        with patch('dotmac.platform.search.service.require_meilisearch') as mock_require:
            mock_meilisearch = Mock()
            mock_require.return_value = mock_meilisearch

            backend = MeilisearchBackend()
            expression = backend._filters_to_expression([])
            assert expression is None


class TestSearchService:
    """Test SearchService class."""

    @pytest.fixture
    def mock_backend(self):
        """Create mock search backend."""
        backend = AsyncMock()
        backend.index = AsyncMock(return_value=True)
        backend.search = AsyncMock(return_value=SearchResponse(results=[], total=0, query=SearchQuery(query="test")))
        backend.delete = AsyncMock(return_value=True)
        backend.update = AsyncMock(return_value=True)
        backend.bulk_index = AsyncMock(return_value=5)
        backend.create_index = AsyncMock(return_value=True)
        backend.delete_index = AsyncMock(return_value=True)
        return backend

    @pytest.fixture
    def search_service(self, mock_backend):
        """Create search service with mock backend."""
        return SearchService(backend=mock_backend)

    async def test_index_business_entity(self, search_service, mock_backend):
        """Test indexing a business entity."""
        entity_data = {"name": "Test Customer", "email": "test@example.com"}
        result = await search_service.index_business_entity("customer", "cust1", entity_data)

        assert result is True
        mock_backend.index.assert_called_once_with("business_customer", "cust1", entity_data)

    async def test_search_business_entities(self, search_service, mock_backend):
        """Test searching business entities."""
        query = SearchQuery(query="test customer", limit=10)
        response = await search_service.search_business_entities("customer", query)

        assert isinstance(response, SearchResponse)
        mock_backend.search.assert_called_once_with("business_customer", query)

    async def test_delete_business_entity(self, search_service, mock_backend):
        """Test deleting a business entity."""
        result = await search_service.delete_business_entity("customer", "cust1")

        assert result is True
        mock_backend.delete.assert_called_once_with("business_customer", "cust1")

    async def test_update_business_entity(self, search_service, mock_backend):
        """Test updating a business entity."""
        updates = {"email": "updated@example.com"}
        result = await search_service.update_business_entity("customer", "cust1", updates)

        assert result is True
        mock_backend.update.assert_called_once_with("business_customer", "cust1", updates)

    async def test_reindex_entity_type(self, search_service, mock_backend):
        """Test reindexing all entities of a type."""
        entities = [
            {"id": "cust1", "name": "Customer 1"},
            {"id": "cust2", "name": "Customer 2"},
        ]

        count = await search_service.reindex_entity_type("customer", entities)

        assert count == 5  # Mock returns 5
        mock_backend.delete_index.assert_called_once_with("business_customer")
        mock_backend.create_index.assert_called_once_with("business_customer", None)
        mock_backend.bulk_index.assert_called_once_with("business_customer", entities)

    async def test_setup_indices(self, search_service, mock_backend):
        """Test setting up search indices."""
        await search_service.setup_indices()

        # Should create indices for all entity types
        expected_calls = [
            "business_customer",
            "business_invoice",
            "business_subscription",
            "business_payment",
            "business_workflow",
            "business_task",
            "business_notification",
            "business_audit",
        ]

        assert mock_backend.create_index.call_count == len(expected_calls)
        for call in mock_backend.create_index.call_args_list:
            assert call[0][0] in expected_calls

    @patch('dotmac.platform.search.factory.create_search_backend_from_env')
    def test_search_service_init_string_backend(self, mock_create):
        """Test SearchService initialization with string backend."""
        mock_backend = Mock()
        mock_create.return_value = mock_backend

        service = SearchService(backend="memory")

        assert service.backend == mock_backend
        mock_create.assert_called_once_with("memory")

    @patch('dotmac.platform.search.factory.create_search_backend_from_env')
    def test_search_service_init_none_backend(self, mock_create):
        """Test SearchService initialization with None backend."""
        mock_backend = Mock()
        mock_create.return_value = mock_backend

        service = SearchService(backend=None)

        assert service.backend == mock_backend
        mock_create.assert_called_once_with()

    def test_search_service_init_backend_object(self, mock_backend):
        """Test SearchService initialization with backend object."""
        service = SearchService(backend=mock_backend)

        assert service.backend == mock_backend


class TestSearchServiceIntegration:
    """Integration tests for search service with real backend."""

    @pytest.fixture
    def memory_service(self):
        """Create search service with in-memory backend."""
        backend = InMemorySearchBackend()
        return SearchService(backend=backend)

    async def test_complete_workflow(self, memory_service):
        """Test complete search workflow."""
        # Setup indices
        await memory_service.setup_indices()

        # Index some entities
        customer_data = {"name": "John Doe", "email": "john@example.com", "status": "active"}
        await memory_service.index_business_entity("customer", "cust1", customer_data)

        invoice_data = {"number": "INV-001", "amount": 100.0, "customer_id": "cust1"}
        await memory_service.index_business_entity("invoice", "inv1", invoice_data)

        # Search for customers
        query = SearchQuery(query="John", limit=10)
        response = await memory_service.search_business_entities("customer", query)

        assert len(response.results) == 1
        assert response.results[0].id == "cust1"
        assert response.results[0].data["name"] == "John Doe"

        # Update customer
        updates = {"status": "inactive"}
        await memory_service.update_business_entity("customer", "cust1", updates)

        # Search again to verify update
        response = await memory_service.search_business_entities("customer", query)
        assert response.results[0].data["status"] == "inactive"

        # Delete customer
        await memory_service.delete_business_entity("customer", "cust1")

        # Search should return no results
        response = await memory_service.search_business_entities("customer", query)
        assert len(response.results) == 0

    async def test_bulk_reindexing(self, memory_service):
        """Test bulk reindexing functionality."""
        # Create initial data
        entities = [
            {"id": "cust1", "name": "Customer 1", "status": "active"},
            {"id": "cust2", "name": "Customer 2", "status": "active"},
            {"id": "cust3", "name": "Customer 3", "status": "inactive"},
        ]

        # Bulk reindex
        count = await memory_service.reindex_entity_type("customer", entities)
        assert count == 3

        # Verify all entities are indexed
        query = SearchQuery(query="Customer", limit=10)
        response = await memory_service.search_business_entities("customer", query)
        assert len(response.results) == 3

        # Test filtered search
        filter_active = SearchFilter(field="status", operator="eq", value="active")
        query = SearchQuery(query="", filters=[filter_active], limit=10)
        response = await memory_service.search_business_entities("customer", query)
        assert len(response.results) == 2
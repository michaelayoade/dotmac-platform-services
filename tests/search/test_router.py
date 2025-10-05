"""
Tests for search API router.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from dotmac.platform.search.router import search_router, SearchResult, SearchResponse
from dotmac.platform.auth.core import UserInfo


@pytest.fixture
def app():
    """Create FastAPI app with search router."""
    app = FastAPI()
    app.include_router(search_router, prefix="/search")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Create mock user."""
    return UserInfo(
        user_id="test-user-123",
        username="testuser",
        email="test@example.com",
        tenant_id="test-tenant",
        roles=["user"],
        permissions=["read", "write"],
    )


class TestSearchRouter:
    """Test search router endpoints."""

    def test_search_endpoint_success(self, client, mock_user):
        """Test successful search request."""
        # Need to mock as a dependency override
        from dotmac.platform.search.router import get_current_user

        client.app.dependency_overrides[get_current_user] = lambda: mock_user

        response = client.get("/search/?q=test+query&limit=5&page=1")

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "query" in data
        assert "results" in data
        assert "total" in data
        assert "page" in data
        assert "facets" in data

        assert data["query"] == "test query"
        assert data["page"] == 1
        assert isinstance(data["results"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["facets"], dict)

        # Check mock result
        if data["results"]:
            result = data["results"][0]
            assert "id" in result
            assert "type" in result
            assert "title" in result
            assert "content" in result
            assert "score" in result
            assert "metadata" in result

    def test_search_endpoint_with_type_filter(self, client, mock_user):
        """Test search with type filter."""
        from dotmac.platform.search.router import get_current_user

        client.app.dependency_overrides[get_current_user] = lambda: mock_user

        response = client.get("/search/?q=test&type=document&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test"

    def test_search_endpoint_pagination_limits(self, client, mock_user):
        """Test search pagination limits."""
        from dotmac.platform.search.router import get_current_user

        client.app.dependency_overrides[get_current_user] = lambda: mock_user

        # Test minimum limit
        response = client.get("/search/?q=test&limit=1&page=1")
        assert response.status_code == 200

        # Test maximum limit
        response = client.get("/search/?q=test&limit=100&page=1")
        assert response.status_code == 200

        # Test limit too high (should fail validation)
        response = client.get("/search/?q=test&limit=101")
        assert response.status_code == 422

        # Test limit too low (should fail validation)
        response = client.get("/search/?q=test&limit=0")
        assert response.status_code == 422

        # Test page too low (should fail validation)
        response = client.get("/search/?q=test&page=0")
        assert response.status_code == 422

    def test_search_endpoint_missing_query(self, client, mock_user):
        """Test search without required query parameter."""
        from dotmac.platform.search.router import get_current_user

        client.app.dependency_overrides[get_current_user] = lambda: mock_user

        response = client.get("/search/")
        assert response.status_code == 422  # Missing required 'q' parameter

    def test_search_endpoint_default_values(self, client, mock_user):
        """Test search with default parameter values."""
        from dotmac.platform.search.router import get_current_user

        client.app.dependency_overrides[get_current_user] = lambda: mock_user

        response = client.get("/search/?q=test")

        assert response.status_code == 200
        data = response.json()

        # Should use default values: limit=10, page=1
        assert data["page"] == 1

    def test_search_endpoint_unauthorized(self, client):
        """Test search endpoint without authentication."""
        # No mock for get_current_user - should fail authentication
        response = client.get("/search/?q=test")

        # Depending on auth implementation, this might be 401 or 403
        assert response.status_code in [401, 403]

    @patch("dotmac.platform.search.router.logger")
    def test_search_endpoint_logging(self, mock_logger, client, mock_user):
        """Test that search requests are logged."""
        from dotmac.platform.search.router import get_current_user

        client.app.dependency_overrides[get_current_user] = lambda: mock_user

        response = client.get("/search/?q=important+search&limit=5")

        assert response.status_code == 200

        # Verify logging was called
        mock_logger.info.assert_called_once()
        log_call = mock_logger.info.call_args[0][0]
        assert "test-user-123" in log_call
        assert "important search" in log_call

    def test_index_content_authenticated(self, client, mock_user):
        """Test indexing content with authenticated user."""
        from dotmac.platform.search.router import get_current_user

        client.app.dependency_overrides[get_current_user] = lambda: mock_user

        content = {
            "title": "Test Document",
            "content": "This is test content for indexing",
            "category": "test",
        }

        response = client.post("/search/index", json=content)

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "id" in data
        assert data["message"] == "Content indexed"
        assert data["id"] == "new-id"

    def test_index_content_anonymous(self, client):
        """Test indexing content without authentication."""
        content = {"title": "Test Document", "content": "This is test content"}

        # This endpoint requires authentication, so should return 401
        response = client.post("/search/index", json=content)

        assert response.status_code == 401

    def test_index_content_logging_anonymous(self, client):
        """Test indexing content logging for anonymous user."""
        content = {"title": "Test Document"}

        # This endpoint requires authentication, so should return 401
        response = client.post("/search/index", json=content)

        assert response.status_code == 401

    @patch("dotmac.platform.search.router.logger")
    def test_index_content_logging_authenticated(self, mock_logger, client, mock_user):
        """Test indexing content logging for authenticated user."""
        from dotmac.platform.search.router import get_current_user

        client.app.dependency_overrides[get_current_user] = lambda: mock_user
        content = {"title": "Test Document"}

        response = client.post("/search/index", json=content)

        assert response.status_code == 200
        mock_logger.info.assert_called_once()
        log_call = mock_logger.info.call_args[0][0]
        assert "test-user-123" in log_call
        assert "indexing content" in log_call

    def test_index_content_invalid_json(self, client):
        """Test indexing with invalid JSON."""
        response = client.post(
            "/search/index", content="invalid json", headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_remove_from_index_authenticated(self, client, mock_user):
        """Test removing content from index with authenticated user."""
        from dotmac.platform.search.router import get_current_user

        client.app.dependency_overrides[get_current_user] = lambda: mock_user

        response = client.delete("/search/index/test-content-id")

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert data["message"] == "Content test-content-id removed from index"

    def test_remove_from_index_anonymous(self, client):
        """Test removing content from index without authentication."""
        response = client.delete("/search/index/test-content-id")

        # This endpoint requires authentication, so should return 401
        assert response.status_code == 401

    def test_remove_from_index_logging_anonymous(self, client):
        """Test removing content logging for anonymous user."""
        response = client.delete("/search/index/test-id")

        # This endpoint requires authentication, so should return 401
        assert response.status_code == 401

    @patch("dotmac.platform.search.router.logger")
    def test_remove_from_index_logging_authenticated(self, mock_logger, client, mock_user):
        """Test removing content logging for authenticated user."""
        from dotmac.platform.search.router import get_current_user

        client.app.dependency_overrides[get_current_user] = lambda: mock_user

        response = client.delete("/search/index/test-id")

        assert response.status_code == 200
        mock_logger.info.assert_called_once()
        log_call = mock_logger.info.call_args[0][0]
        assert "test-user-123" in log_call
        assert "removing test-id from index" in log_call

    def test_remove_from_index_special_characters(self, client, mock_user):
        """Test removing content with special characters in ID."""
        from dotmac.platform.search.router import get_current_user

        client.app.dependency_overrides[get_current_user] = lambda: mock_user

        content_id = "test-id-with-special@chars"  # Some special chars get URL encoded
        response = client.delete(f"/search/index/{content_id}")

        assert response.status_code == 200
        data = response.json()
        assert content_id in data["message"]


class TestSearchResponseModels:
    """Test search response models."""

    def test_search_result_model(self):
        """Test SearchResult model validation."""
        result_data = {
            "id": "test-123",
            "type": "document",
            "title": "Test Document",
            "content": "This is test content snippet",
            "score": 0.95,
            "metadata": {"category": "test", "tags": ["python", "search"]},
        }

        result = SearchResult(**result_data)

        assert result.id == "test-123"
        assert result.type == "document"
        assert result.title == "Test Document"
        assert result.content == "This is test content snippet"
        assert result.score == 0.95
        assert result.metadata == {"category": "test", "tags": ["python", "search"]}

    def test_search_result_model_defaults(self):
        """Test SearchResult model with default values."""
        result_data = {
            "id": "test-123",
            "type": "document",
            "title": "Test Document",
            "content": "Test content",
            "score": 0.85,
            # metadata should use default empty dict
        }

        result = SearchResult(**result_data)

        assert result.metadata == {}

    def test_search_response_model(self):
        """Test SearchResponse model validation."""
        result = SearchResult(id="1", type="doc", title="Test", content="Content", score=0.9)

        response_data = {
            "query": "test search",
            "results": [result],
            "total": 1,
            "page": 1,
            "facets": {"types": {"document": 1}, "categories": {"tech": 1}},
        }

        response = SearchResponse(**response_data)

        assert response.query == "test search"
        assert len(response.results) == 1
        assert response.results[0] == result
        assert response.total == 1
        assert response.page == 1
        assert response.facets == {"types": {"document": 1}, "categories": {"tech": 1}}

    def test_search_response_model_defaults(self):
        """Test SearchResponse model with default values."""
        response_data = {
            "query": "test",
            "results": [],
            "total": 0,
            "page": 1,
            # facets should use default empty dict
        }

        response = SearchResponse(**response_data)

        assert response.facets == {}

    def test_search_result_model_validation_errors(self):
        """Test SearchResult model validation errors."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SearchResult()  # Missing required fields

        # Test that all required fields work when provided
        result = SearchResult(id="test-123", type="doc", title="Test", content="Content", score=0.9)
        assert result.id == "test-123"

    def test_search_response_model_validation_errors(self):
        """Test SearchResponse model validation errors."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SearchResponse()  # Missing required fields

        with pytest.raises(ValidationError):
            SearchResponse(query="test", results="not a list", total=0, page=1)  # Should be list


class TestRouterIntegration:
    """Integration tests for search router."""

    def test_complete_search_flow(self, client, mock_user):
        """Test complete search workflow."""
        from dotmac.platform.search.router import get_current_user

        client.app.dependency_overrides[get_current_user] = lambda: mock_user

        # Index some content
        content1 = {"title": "Python Tutorial", "content": "Learn Python programming"}
        content2 = {"title": "Web Development", "content": "Build web applications"}

        response1 = client.post("/search/index", json=content1)
        response2 = client.post("/search/index", json=content2)

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Search for content
        search_response = client.get("/search/?q=Python&limit=10")

        assert search_response.status_code == 200
        search_data = search_response.json()
        assert search_data["query"] == "Python"

        # Remove content from index
        remove_response = client.delete("/search/index/content-id-1")

        assert remove_response.status_code == 200
        remove_data = remove_response.json()
        assert "removed from index" in remove_data["message"]

    def test_router_exports(self):
        """Test that router exports are correct."""
        from dotmac.platform.search.router import __all__

        assert "search_router" in __all__
        assert len(__all__) == 1

    def test_search_query_encoding(self, client, mock_user):
        """Test search with URL-encoded queries."""
        from dotmac.platform.search.router import get_current_user

        client.app.dependency_overrides[get_current_user] = lambda: mock_user

        # Test with spaces and special characters
        query = "python programming & web development"
        encoded_query = query.replace(" ", "+").replace("&", "%26")

        response = client.get(f"/search/?q={encoded_query}")

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == query

    def test_search_edge_cases(self, client, mock_user):
        """Test search edge cases."""
        from dotmac.platform.search.router import get_current_user

        client.app.dependency_overrides[get_current_user] = lambda: mock_user

        # Empty query
        response = client.get("/search/?q=")
        assert response.status_code == 200

        # Very long query
        long_query = "a" * 1000
        response = client.get(f"/search/?q={long_query}")
        assert response.status_code == 200

        # Special characters in query
        special_query = "test@#$%^&*()_+{}|:<>?[]\\;'\",./"
        response = client.get(f"/search/?q={special_query}")
        assert response.status_code == 200

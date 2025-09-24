"""
Tests for tenant isolation security fixes.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import HTTPException, Request
from starlette.applications import Starlette
from starlette.responses import JSONResponse

from dotmac.platform.tenant.tenant import TenantIdentityResolver, TenantMiddleware
from dotmac.platform.db import BaseModel


class TestTenantIdentityResolver:
    """Test tenant identity resolution."""

    @pytest.fixture
    def resolver(self):
        """Create resolver instance."""
        return TenantIdentityResolver()

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = Mock(spec=Request)
        request.headers = Mock()
        request.headers.get = Mock(return_value=None)
        request.query_params = Mock()
        request.query_params.get = Mock(return_value=None)

        # Create a simple state object that behaves like request.state
        class SimpleState:
            def __init__(self):
                self.__dict__ = {}

        request.state = SimpleState()
        return request

    @pytest.mark.asyncio
    async def test_resolve_from_header(self, resolver, mock_request):
        """Test resolving tenant from X-Tenant-ID header."""
        mock_request.headers.get.return_value = "tenant-123"

        result = await resolver.resolve(mock_request)

        assert result == "tenant-123"

    @pytest.mark.asyncio
    async def test_resolve_from_query_param(self, resolver, mock_request):
        """Test resolving tenant from query parameter."""
        mock_request.query_params.get.return_value = "tenant-456"

        result = await resolver.resolve(mock_request)

        assert result == "tenant-456"

    @pytest.mark.asyncio
    async def test_resolve_from_request_state(self, resolver, mock_request):
        """Test resolving tenant from request state."""
        mock_request.state.__dict__ = {"tenant_id": "tenant-789"}

        result = await resolver.resolve(mock_request)

        assert result == "tenant-789"

    @pytest.mark.asyncio
    async def test_resolve_priority_order(self, resolver, mock_request):
        """Test that header takes precedence over query param."""
        mock_request.headers.get.return_value = "from-header"
        mock_request.query_params.get.return_value = "from-query"
        mock_request.state.__dict__ = {"tenant_id": "from-state"}

        result = await resolver.resolve(mock_request)

        # Header should win
        assert result == "from-header"

    @pytest.mark.asyncio
    async def test_resolve_query_over_state(self, resolver, mock_request):
        """Test that query param takes precedence over state."""
        mock_request.query_params.get.return_value = "from-query"
        mock_request.state.__dict__ = {"tenant_id": "from-state"}

        result = await resolver.resolve(mock_request)

        # Query should win over state
        assert result == "from-query"

    @pytest.mark.asyncio
    async def test_resolve_none_when_not_found(self, resolver, mock_request):
        """Test returning None when tenant ID not found."""
        result = await resolver.resolve(mock_request)

        assert result is None

    @pytest.mark.asyncio
    async def test_resolve_handles_exceptions(self, resolver, mock_request):
        """Test handling exceptions gracefully."""
        # Mock headers to raise exception
        mock_request.headers.get = Mock(side_effect=Exception("Header error"))
        mock_request.query_params.get = Mock(side_effect=Exception("Query error"))

        result = await resolver.resolve(mock_request)

        assert result is None


class TestTenantMiddleware:
    """Test tenant middleware functionality."""

    @pytest.fixture
    def mock_app(self):
        """Create mock ASGI app."""
        async def app(request):
            return JSONResponse({"status": "ok"})
        return app

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = Mock(spec=Request)
        request.headers = Mock()
        request.headers.get = Mock(return_value=None)
        request.query_params = Mock()
        request.query_params.get = Mock(return_value=None)

        # Create a simple state object that allows attribute setting
        class SimpleState:
            def __init__(self):
                self.__dict__ = {}

        request.state = SimpleState()
        request.url = Mock()
        request.url.path = "/api/v1/users"
        return request

    @pytest.fixture
    def mock_call_next(self):
        """Create mock call_next function."""
        async def call_next(request):
            return JSONResponse({"processed": True})
        return call_next

    @pytest.mark.asyncio
    async def test_middleware_sets_tenant_id(self, mock_app, mock_request, mock_call_next):
        """Test middleware sets tenant ID on request state."""
        mock_request.headers.get.return_value = "tenant-123"

        middleware = TenantMiddleware(mock_app)

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert mock_request.state.tenant_id == "tenant-123"
        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_exempt_paths(self, mock_app, mock_request, mock_call_next):
        """Test middleware skips exempt paths."""
        mock_request.url.path = "/health"
        # No tenant ID provided

        middleware = TenantMiddleware(mock_app, require_tenant=True)

        # Should not raise exception for exempt path
        result = await middleware.dispatch(mock_request, mock_call_next)

        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_requires_tenant_by_default(self, mock_app, mock_request, mock_call_next):
        """Test middleware requires tenant ID by default."""
        # No tenant ID provided and not exempt path

        middleware = TenantMiddleware(mock_app, require_tenant=True)

        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(mock_request, mock_call_next)

        assert exc_info.value.status_code == 400
        assert "Tenant ID is required" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_middleware_optional_tenant_mode(self, mock_app, mock_request, mock_call_next):
        """Test middleware with optional tenant mode."""
        # No tenant ID provided

        middleware = TenantMiddleware(mock_app, require_tenant=False)

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert result.status_code == 200
        # tenant_id should not be set on state
        assert not hasattr(mock_request.state, 'tenant_id')

    @pytest.mark.asyncio
    async def test_middleware_custom_exempt_paths(self, mock_app, mock_request, mock_call_next):
        """Test middleware with custom exempt paths."""
        mock_request.url.path = "/custom/exempt"

        middleware = TenantMiddleware(
            mock_app,
            require_tenant=True,
            exempt_paths={"/custom/exempt", "/health"}
        )

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_custom_resolver(self, mock_app, mock_request, mock_call_next):
        """Test middleware with custom tenant resolver."""
        mock_resolver = Mock()
        mock_resolver.resolve = AsyncMock(return_value="custom-tenant")

        middleware = TenantMiddleware(mock_app, resolver=mock_resolver)

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert mock_request.state.tenant_id == "custom-tenant"
        mock_resolver.resolve.assert_called_once_with(mock_request)


class TestBaseModelTenantSupport:
    """Test BaseModel tenant_id field."""

    def test_base_model_has_tenant_id_field(self):
        """Test that BaseModel has tenant_id field."""
        # Check the column exists
        assert hasattr(BaseModel, 'tenant_id')

        # Check it's a SQLAlchemy column (legacy style)
        from sqlalchemy import Column
        assert isinstance(BaseModel.tenant_id, Column)

        # Check the column type and properties
        column = BaseModel.tenant_id
        assert hasattr(column.type, 'python_type') or hasattr(column.type, 'impl')
        assert column.index is True  # Should be indexed
        assert column.nullable is True  # Should be nullable

    def test_base_model_tenant_id_in_dict(self):
        """Test that tenant_id appears in model dict representation."""
        # Create a concrete model for testing
        from sqlalchemy import String, Column

        class TestModel(BaseModel):
            __tablename__ = 'test_model'
            name = Column(String(100))

        # Check that tenant_id is included in columns
        column_names = [col.name for col in TestModel.__table__.columns]
        assert 'tenant_id' in column_names

    def test_base_model_to_dict_includes_tenant_id(self):
        """Test that to_dict method includes tenant_id."""
        # Create a concrete model for testing
        from sqlalchemy import String, Column

        class TestModel(BaseModel):
            __tablename__ = 'test_model_dict'
            name = Column(String(100))

        # Create instance (won't save to DB in test)
        instance = TestModel()
        instance.tenant_id = "test-tenant"
        instance.name = "test"

        # Check to_dict includes tenant_id
        result = instance.to_dict()
        assert 'tenant_id' in result


class TestTenantIsolationIntegration:
    """Integration tests for tenant isolation."""

    @pytest.mark.asyncio
    async def test_end_to_end_tenant_isolation(self):
        """Test complete tenant isolation flow."""
        # Create a mock FastAPI app with tenant middleware
        from fastapi import FastAPI
        from starlette.testclient import TestClient

        app = FastAPI()

        # Add tenant middleware
        app.add_middleware(TenantMiddleware, require_tenant=True)

        @app.get("/api/users")
        async def get_users(request: Request):
            return {"tenant_id": getattr(request.state, 'tenant_id', None)}

        client = TestClient(app)

        # Test with tenant ID - should work
        response = client.get("/api/users", headers={"X-Tenant-ID": "tenant-123"})
        assert response.status_code == 200
        assert response.json()["tenant_id"] == "tenant-123"

        # Test without tenant ID - should fail
        try:
            response = client.get("/api/users")
            # If we get here, check that it's a 400
            assert response.status_code == 400
            assert "Tenant ID is required" in response.json()["detail"]
        except Exception as e:
            # If the exception is raised, that's also valid behavior
            assert "Tenant ID is required" in str(e)

        # Test exempt path - should work without tenant ID
        response = client.get("/health")
        assert response.status_code == 404  # Route doesn't exist, but middleware didn't block it

    def test_tenant_middleware_configuration_options(self):
        """Test various middleware configuration scenarios."""
        app = Mock()

        # Test default configuration
        middleware1 = TenantMiddleware(app)
        assert middleware1.require_tenant is True
        assert "/health" in middleware1.exempt_paths
        assert "/docs" in middleware1.exempt_paths

        # Test custom configuration
        custom_exempt = {"/custom", "/special"}
        middleware2 = TenantMiddleware(
            app,
            require_tenant=False,
            exempt_paths=custom_exempt
        )
        assert middleware2.require_tenant is False
        assert middleware2.exempt_paths == custom_exempt

    def test_resolver_edge_cases(self):
        """Test edge cases in tenant resolution."""
        resolver = TenantIdentityResolver()

        # Test custom header name
        resolver.header_name = "Custom-Tenant"
        resolver.query_param = "custom_tenant"

        # Check the configuration was updated
        assert resolver.header_name == "Custom-Tenant"
        assert resolver.query_param == "custom_tenant"
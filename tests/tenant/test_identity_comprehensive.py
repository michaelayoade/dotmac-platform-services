"""
Comprehensive tests for tenant.identity module.

Tests the TenantIdentityResolver class for extracting tenant context from requests.
"""

from unittest.mock import Mock

import pytest
from fastapi import Request

from dotmac.platform.tenant.identity import TenantIdentityResolver


class TestTenantIdentityResolver:
    """Test TenantIdentityResolver functionality."""

    @pytest.fixture
    def resolver(self):
        """Create a TenantIdentityResolver instance."""
        return TenantIdentityResolver()

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        request = Mock(spec=Request)
        request.headers = {}
        request.query_params = {}
        request.state = Mock()
        return request

    def test_resolver_initialization(self, resolver):
        """Test resolver initialization with default values."""
        assert resolver.header_name == "X-Tenant-ID"
        assert resolver.query_param == "tenant_id"

    def test_resolver_custom_initialization(self):
        """Test resolver initialization with custom values."""
        resolver = TenantIdentityResolver()
        resolver.header_name = "X-Custom-Tenant"
        resolver.query_param = "custom_tenant"

        assert resolver.header_name == "X-Custom-Tenant"
        assert resolver.query_param == "custom_tenant"

    @pytest.mark.asyncio
    async def test_resolve_from_header(self, resolver, mock_request):
        """Test resolving tenant ID from request header."""
        # Set up request with tenant ID in header
        mock_request.headers = {"X-Tenant-ID": "tenant-123"}
        mock_request.query_params = {}
        mock_request.state = Mock()

        tenant_id = await resolver.resolve(mock_request)

        assert tenant_id == "tenant-123"

    @pytest.mark.asyncio
    async def test_resolve_from_query_param(self, resolver, mock_request):
        """Test resolving tenant ID from query parameter."""
        # Set up request with tenant ID in query params (no header)
        mock_request.headers = {}
        mock_request.query_params = {"tenant_id": "tenant-456"}
        mock_request.state = Mock()

        tenant_id = await resolver.resolve(mock_request)

        assert tenant_id == "tenant-456"

    @pytest.mark.asyncio
    async def test_resolve_from_request_state(self, resolver, mock_request):
        """Test resolving tenant ID from request state."""
        # Set up request with tenant ID in state (no header or query)
        mock_request.headers = {}
        mock_request.query_params = {}
        mock_request.state = Mock()
        mock_request.state.tenant_id = "tenant-789"

        tenant_id = await resolver.resolve(mock_request)

        assert tenant_id == "tenant-789"

    @pytest.mark.asyncio
    async def test_resolve_priority_order(self, resolver, mock_request):
        """Test that header takes priority over query param and state."""
        # Set up request with tenant ID in all three places
        mock_request.headers = {"X-Tenant-ID": "header-tenant"}
        mock_request.query_params = {"tenant_id": "query-tenant"}
        mock_request.state = Mock()
        mock_request.state.tenant_id = "state-tenant"

        tenant_id = await resolver.resolve(mock_request)

        # Header should take priority
        assert tenant_id == "header-tenant"

    @pytest.mark.asyncio
    async def test_resolve_query_over_state(self, resolver, mock_request):
        """Test that query param takes priority over state."""
        # Set up request with tenant ID in query and state (no header)
        mock_request.headers = {}
        mock_request.query_params = {"tenant_id": "query-tenant"}
        mock_request.state = Mock()
        mock_request.state.tenant_id = "state-tenant"

        tenant_id = await resolver.resolve(mock_request)

        # Query should take priority over state
        assert tenant_id == "query-tenant"

    @pytest.mark.asyncio
    async def test_resolve_no_tenant_found(self, resolver, mock_request):
        """Test resolving when no tenant ID is found."""
        # Set up request with no tenant ID anywhere
        mock_request.headers = {}
        mock_request.query_params = {}
        mock_request.state = Mock()

        tenant_id = await resolver.resolve(mock_request)

        assert tenant_id is None

    @pytest.mark.asyncio
    async def test_resolve_empty_header_value(self, resolver, mock_request):
        """Test resolving with empty header value."""
        # Set up request with empty header value
        mock_request.headers = {"X-Tenant-ID": ""}
        mock_request.query_params = {"tenant_id": "query-tenant"}
        mock_request.state = Mock()

        tenant_id = await resolver.resolve(mock_request)

        # Empty header should fallback to query param
        assert tenant_id == "query-tenant"

    @pytest.mark.asyncio
    async def test_resolve_empty_query_value(self, resolver, mock_request):
        """Test resolving with empty query parameter value."""
        # Set up request with empty query value
        mock_request.headers = {}
        mock_request.query_params = {"tenant_id": ""}
        mock_request.state = Mock()
        mock_request.state.tenant_id = "state-tenant"

        tenant_id = await resolver.resolve(mock_request)

        # Empty query should fallback to state
        assert tenant_id == "state-tenant"

    @pytest.mark.asyncio
    async def test_resolve_none_header_value(self, resolver, mock_request):
        """Test resolving with None header value."""
        # Set up request where header returns None
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value=None)
        mock_request.query_params = {"tenant_id": "query-tenant"}
        mock_request.state = Mock()

        tenant_id = await resolver.resolve(mock_request)

        # None header should fallback to query param
        assert tenant_id == "query-tenant"

    @pytest.mark.asyncio
    async def test_resolve_custom_header_name(self, mock_request):
        """Test resolving with custom header name."""
        resolver = TenantIdentityResolver()
        resolver.header_name = "X-Custom-Tenant"

        # Set up request with custom header
        mock_request.headers = {"X-Custom-Tenant": "custom-tenant"}
        mock_request.query_params = {}
        mock_request.state = Mock()

        tenant_id = await resolver.resolve(mock_request)

        assert tenant_id == "custom-tenant"

    @pytest.mark.asyncio
    async def test_resolve_custom_query_param(self, mock_request):
        """Test resolving with custom query parameter name."""
        resolver = TenantIdentityResolver()
        resolver.query_param = "custom_tenant"

        # Set up request with custom query param
        mock_request.headers = {}
        mock_request.query_params = {"custom_tenant": "custom-tenant"}
        mock_request.state = Mock()

        tenant_id = await resolver.resolve(mock_request)

        assert tenant_id == "custom-tenant"

    @pytest.mark.asyncio
    async def test_resolve_with_getattr_missing_state(self, resolver, mock_request):
        """Test resolving when request.state doesn't have tenant_id attribute."""
        # Set up request with no tenant_id attribute on state
        mock_request.headers = {}
        mock_request.query_params = {}
        mock_request.state = Mock()
        # Don't set tenant_id attribute, so getattr should return None

        tenant_id = await resolver.resolve(mock_request)

        assert tenant_id is None

    @pytest.mark.asyncio
    async def test_resolve_case_sensitive_header(self, resolver, mock_request):
        """Test that header matching is case-sensitive."""
        # Set up request with different case header
        mock_request.headers = {"x-tenant-id": "tenant-123"}  # lowercase
        mock_request.query_params = {"tenant_id": "query-tenant"}
        mock_request.state = Mock()

        tenant_id = await resolver.resolve(mock_request)

        # Should fallback to query param since header case doesn't match
        assert tenant_id == "query-tenant"

    @pytest.mark.asyncio
    async def test_resolve_whitespace_values(self, resolver, mock_request):
        """Test resolving with whitespace-only values."""
        # Set up request with whitespace values
        mock_request.headers = {"X-Tenant-ID": "   "}  # only spaces
        mock_request.query_params = {"tenant_id": "\t\n"}  # tabs and newlines
        mock_request.state = Mock()
        mock_request.state.tenant_id = "state-tenant"

        tenant_id = await resolver.resolve(mock_request)

        # Whitespace values should be treated as valid (not empty)
        assert tenant_id == "   "

    @pytest.mark.asyncio
    async def test_resolve_special_characters(self, resolver, mock_request):
        """Test resolving with special characters in tenant ID."""
        special_tenant_id = "tenant-123_abc.def@domain.com"

        # Set up request with special characters
        mock_request.headers = {"X-Tenant-ID": special_tenant_id}
        mock_request.query_params = {}
        mock_request.state = Mock()

        tenant_id = await resolver.resolve(mock_request)

        assert tenant_id == special_tenant_id

    @pytest.mark.asyncio
    async def test_resolve_unicode_values(self, resolver, mock_request):
        """Test resolving with unicode characters."""
        unicode_tenant = "tenant-🏢-αβγ"

        # Set up request with unicode characters
        mock_request.headers = {"X-Tenant-ID": unicode_tenant}
        mock_request.query_params = {}
        mock_request.state = Mock()

        tenant_id = await resolver.resolve(mock_request)

        assert tenant_id == unicode_tenant


class TestTenantIdentityResolverEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_resolve_with_exception_in_headers(self):
        """Test handling exceptions when accessing headers."""
        resolver = TenantIdentityResolver()

        # Create request that raises exception on header access
        mock_request = Mock(spec=Request)
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(side_effect=Exception("Header access failed"))
        mock_request.query_params = {"tenant_id": "fallback-tenant"}
        mock_request.state = Mock()

        # Should handle the exception and fallback to query params
        tenant_id = await resolver.resolve(mock_request)

        assert tenant_id == "fallback-tenant"

    @pytest.mark.asyncio
    async def test_resolve_with_exception_in_query(self):
        """Test handling exceptions when accessing query params."""
        resolver = TenantIdentityResolver()

        # Create request that raises exception on query access
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        mock_request.query_params = Mock()
        mock_request.query_params.get = Mock(side_effect=Exception("Query access failed"))
        mock_request.state = Mock()
        mock_request.state.tenant_id = "fallback-tenant"

        # Should handle the exception and fallback to state
        tenant_id = await resolver.resolve(mock_request)

        assert tenant_id == "fallback-tenant"

    @pytest.mark.asyncio
    async def test_resolve_with_exception_in_state(self):
        """Test handling exceptions when accessing state."""
        resolver = TenantIdentityResolver()

        # Create request that raises exception on state access
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        mock_request.query_params = {}
        mock_request.state = Mock()

        # Mock getattr to raise exception
        import builtins

        original_getattr = builtins.getattr

        def mock_getattr(obj, name, default=None):
            if name == "tenant_id":
                raise Exception("State access failed")
            return original_getattr(obj, name, default)

        with pytest.MonkeyPatch().context() as m:
            m.setattr(builtins, "getattr", mock_getattr)

            # Should handle the exception and return None
            tenant_id = await resolver.resolve(mock_request)

            assert tenant_id is None

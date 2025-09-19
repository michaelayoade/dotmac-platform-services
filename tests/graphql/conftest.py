"""GraphQL test fixtures and configuration."""

import pytest
from typing import Any, Dict, Optional
from unittest.mock import Mock, AsyncMock

try:  # optional dependency: strawberry is not always installed locally
    import strawberry
    from strawberry.fastapi import GraphQLRouter
    from strawberry.test import BaseGraphQLTestClient
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient
except ImportError:  # pragma: no cover - handled via graceful skips below
    strawberry = None
    GraphQLRouter = None  # type: ignore
    BaseGraphQLTestClient = None  # type: ignore
    FastAPI = None  # type: ignore
    ASGITransport = None  # type: ignore
    AsyncClient = None  # type: ignore

if strawberry is not None:
    from dotmac.platform.api.graphql.schema import schema
    from dotmac.platform.api.graphql.router import mount_graphql
else:  # pragma: no cover - executed when GraphQL stack missing
    schema = None  # type: ignore
    mount_graphql = None  # type: ignore

from dotmac.platform.auth.current_user import UserClaims


def _require_strawberry() -> None:
    """Skip a test when Strawberry GraphQL is unavailable."""

    if strawberry is None or FastAPI is None or AsyncClient is None or schema is None:
        pytest.skip("Strawberry GraphQL not available")


@pytest.fixture
def mock_user_claims():
    """Mock user claims for authentication testing."""
    return UserClaims(
        user_id="test-user-123",
        tenant_id="test-tenant-123",
        scopes=["read:audit", "write:audit", "admin:feature_flags"],
        roles=["user", "admin"],
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        issued_at=1234567890,
        expires_at=1234567890 + 3600,
        token_id="token-123",
        issuer="test-issuer",
        audience="test-audience",
        authenticated=True,
        is_service=False,
        extra_claims={}
    )


@pytest.fixture
def mock_auth_context(mock_user_claims):
    """Mock authentication context."""
    mock_request = Mock()
    mock_request.headers = {"Authorization": "Bearer test-token"}

    return {
        "request": mock_request,
        "user": mock_user_claims,
    }


@pytest.fixture
def graphql_app():
    """Create FastAPI app with GraphQL endpoint mounted."""
    _require_strawberry()

    if not schema or not mount_graphql or not FastAPI:
        pytest.skip("GraphQL schema not available")

    app = FastAPI(title="Test GraphQL API")
    mount_graphql(app, path="/graphql")
    return app


@pytest.fixture
async def graphql_client(graphql_app):
    """Create async GraphQL test client."""
    _require_strawberry()

    transport = ASGITransport(app=graphql_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


class GraphQLTestClient:
    """Enhanced GraphQL test client with utility methods."""

    def __init__(self, client: AsyncClient):
        self.client = client
        self.default_headers = {}

    def set_auth_header(self, token: str):
        """Set authentication header for requests."""
        self.default_headers["Authorization"] = f"Bearer {token}"

    async def execute(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        expected_status: int = 200
    ) -> Dict[str, Any]:
        """Execute GraphQL query and return response data."""
        request_headers = {**self.default_headers, **(headers or {})}

        response = await self.client.post(
            "/graphql",
            json={
                "query": query,
                "variables": variables or {},
            },
            headers=request_headers
        )

        assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text}"

        data = response.json()
        return data

    async def execute_expecting_errors(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Execute GraphQL query expecting errors."""
        data = await self.execute(query, variables, headers)
        assert "errors" in data, "Expected errors in GraphQL response"
        return data

    async def execute_expecting_data(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Any:
        """Execute GraphQL query expecting successful data response."""
        data = await self.execute(query, variables, headers)
        assert "errors" not in data or not data["errors"], f"Unexpected errors: {data.get('errors')}"
        assert "data" in data, "Expected data in GraphQL response"
        return data["data"]


@pytest.fixture
async def graphql_test_client(graphql_client):
    """Enhanced GraphQL test client with utility methods."""
    _require_strawberry()
    return GraphQLTestClient(graphql_client)


@pytest.fixture
async def authenticated_graphql_client(graphql_test_client):
    """GraphQL test client with authentication."""
    _require_strawberry()
    graphql_test_client.set_auth_header("test-token")
    return graphql_test_client


# Mock service fixtures
@pytest.fixture
def mock_jwt_service():
    """Mock JWT service."""
    mock = Mock()
    mock.verify_token = Mock(return_value={
        "sub": "test-user-123",
        "tenant_id": "test-tenant-123",
        "scopes": ["read:audit", "write:audit"],
        "roles": ["user"],
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "iat": 1234567890,
        "exp": 1234567890 + 3600,
        "jti": "token-123",
        "iss": "test-issuer",
        "aud": "test-audience"
    })
    return mock


@pytest.fixture
def mock_feature_flag_service():
    """Mock feature flag service."""
    mock = Mock()
    mock.list_flags = AsyncMock(return_value=[])
    mock.get_flag = AsyncMock(return_value=None)
    mock.evaluate_flag = AsyncMock(return_value=Mock(enabled=True, variant=None, reason="default"))
    mock.upsert_flag = AsyncMock()
    mock.delete_flag = AsyncMock()
    mock.toggle_flag = AsyncMock()
    return mock


@pytest.fixture
def mock_secrets_manager():
    """Mock secrets manager."""
    mock = Mock()
    mock.list_secrets = AsyncMock(return_value=[])
    mock.get_secret_history = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def mock_metrics_registry():
    """Mock metrics registry."""
    mock = Mock()
    mock.get_metrics = AsyncMock(return_value=[])
    return mock


# GraphQL query fixtures
@pytest.fixture
def health_query():
    """Health check GraphQL query."""
    return """
        query HealthQuery {
            health {
                status
                version
                timestamp
                services
            }
        }
    """


@pytest.fixture
def current_user_query():
    """Current user GraphQL query."""
    return """
        query CurrentUserQuery {
            currentUser {
                id
                username
                email
                fullName
                tenantId
                roles
                scopes
                isActive
                createdAt
                lastLogin
            }
        }
    """


@pytest.fixture
def feature_flags_query():
    """Feature flags GraphQL query."""
    return """
        query FeatureFlagsQuery($first: Int, $after: String) {
            featureFlags(first: $first, after: $after) {
                nodes {
                    key
                    name
                    description
                    enabled
                    strategy
                    config
                    createdAt
                    updatedAt
                    createdBy
                }
                pageInfo {
                    hasNextPage
                    hasPreviousPage
                    startCursor
                    endCursor
                    totalCount
                }
            }
        }
    """


@pytest.fixture
def audit_events_query():
    """Audit events GraphQL query."""
    return """
        query AuditEventsQuery($filter: AuditEventFilter, $first: Int, $after: String) {
            auditEvents(filter: $filter, first: $first, after: $after) {
                nodes {
                    id
                    timestamp
                    category
                    level
                    action
                    resource
                    actor
                    tenantId
                    ipAddress
                    userAgent
                    details
                    outcome
                }
                pageInfo {
                    hasNextPage
                    hasPreviousPage
                    startCursor
                    endCursor
                    totalCount
                }
            }
        }
    """


@pytest.fixture
def log_audit_event_mutation():
    """Log audit event GraphQL mutation."""
    return """
        mutation LogAuditEventMutation(
            $category: AuditCategory!,
            $level: AuditLevel!,
            $action: String!,
            $resource: String!,
            $details: JSON
        ) {
            logAuditEvent(
                category: $category,
                level: $level,
                action: $action,
                resource: $resource,
                details: $details
            ) {
                id
                timestamp
                category
                level
                action
                resource
                actor
                details
                outcome
            }
        }
    """

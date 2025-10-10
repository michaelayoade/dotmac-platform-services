"""Test logs endpoint to reproduce and fix 500 error."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.audit.models import ActivitySeverity, AuditActivity
from dotmac.platform.auth.core import UserInfo, get_current_user
from dotmac.platform.db import get_session_dependency
from dotmac.platform.monitoring.logs_router import logs_router


@pytest.fixture
def app():
    """Create FastAPI app with logs router."""
    app = FastAPI()
    app.include_router(logs_router, prefix="/api/v1/monitoring")
    return app


@pytest.fixture
def client(app, async_db_session):
    """Create test client with database dependency."""
    mock_user = UserInfo(
        user_id=str(uuid4()),
        username="testuser",
        email="test@example.com",
        tenant_id="test-tenant",
        roles=["admin"],
        permissions=[],
    )

    app.dependency_overrides[get_session_dependency] = lambda: async_db_session
    app.dependency_overrides[get_current_user] = lambda: mock_user
    return TestClient(app)


@pytest.fixture
async def sample_audit_logs(async_db_session: AsyncSession):
    """Create sample audit activities for testing."""
    activities = [
        AuditActivity(
            id=uuid4(),
            activity_type="user.login",
            description="User logged in successfully",
            severity=ActivitySeverity.LOW.value,
            user_id=str(uuid4()),
            tenant_id=str(uuid4()),  # Convert to string for SQLite compatibility
            action="login",  # Required field
            ip_address="192.168.1.1",  # Use the correct ip_address field
            created_at=datetime.now(UTC),
        ),
        AuditActivity(
            id=uuid4(),
            activity_type="billing.payment",
            description="Payment processed",
            severity=ActivitySeverity.MEDIUM.value,
            user_id=str(uuid4()),
            tenant_id=str(uuid4()),
            action="payment_process",
            ip_address="10.0.0.1",
            created_at=datetime.now(UTC),
        ),
        AuditActivity(
            id=uuid4(),
            activity_type="api.error",
            description="Internal server error occurred",
            severity=ActivitySeverity.HIGH.value,
            user_id=str(uuid4()),
            tenant_id=str(uuid4()),
            action="api_request",
            ip_address="172.16.0.1",
            created_at=datetime.now(UTC),
        ),
    ]

    for activity in activities:
        async_db_session.add(activity)
    await async_db_session.commit()

    return activities


class TestLogsEndpoint:
    """Test logs endpoint functionality."""

    @pytest.mark.asyncio
    async def test_get_logs_basic(self, client, sample_audit_logs):
        """Test basic logs retrieval."""
        response = client.get("/api/v1/monitoring/logs")

        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")

        assert response.status_code == 200
        data = response.json()

        assert "logs" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "has_more" in data

        assert len(data["logs"]) == 3
        assert data["total"] == 3

    @pytest.mark.asyncio
    async def test_get_logs_with_level_filter(self, client, sample_audit_logs):
        """Test logs filtering by level."""
        response = client.get("/api/v1/monitoring/logs?level=ERROR")

        assert response.status_code == 200
        data = response.json()

        # Should return only HIGH severity (ERROR level)
        assert len(data["logs"]) == 1
        assert data["logs"][0]["level"] == "ERROR"

    @pytest.mark.asyncio
    async def test_get_logs_with_search(self, client, sample_audit_logs):
        """Test logs search functionality."""
        response = client.get("/api/v1/monitoring/logs?search=payment")

        assert response.status_code == 200
        data = response.json()

        assert len(data["logs"]) == 1
        assert "payment" in data["logs"][0]["message"].lower()

    @pytest.mark.asyncio
    async def test_get_logs_pagination(self, client, sample_audit_logs):
        """Test logs pagination."""
        response = client.get("/api/v1/monitoring/logs?page=1&page_size=2")

        assert response.status_code == 200
        data = response.json()

        assert len(data["logs"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["has_more"] is True

    @pytest.mark.asyncio
    async def test_get_logs_empty(self, client):
        """Test logs retrieval when no logs exist."""
        response = client.get("/api/v1/monitoring/logs")

        assert response.status_code == 200
        data = response.json()

        assert data["logs"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_log_stats(self, client, sample_audit_logs):
        """Test log statistics endpoint."""
        response = client.get("/api/v1/monitoring/logs/stats")

        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "by_level" in data
        assert "by_service" in data
        assert "time_range" in data

        assert data["total"] == 3
        assert data["by_level"]["INFO"] == 1
        assert data["by_level"]["WARNING"] == 1
        assert data["by_level"]["ERROR"] == 1

    @pytest.mark.asyncio
    async def test_get_available_services(self, client, sample_audit_logs):
        """Test available services endpoint."""
        response = client.get("/api/v1/monitoring/logs/services")

        assert response.status_code == 200
        services = response.json()

        assert isinstance(services, list)
        assert "user" in services
        assert "billing" in services
        assert "api" in services


class TestLogsEndpointErrors:
    """Test error scenarios."""

    @pytest.mark.asyncio
    async def test_invalid_log_level(self, client):
        """Test with invalid log level."""
        response = client.get("/api/v1/monitoring/logs?level=INVALID")

        # Should return 422 validation error
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_page_number(self, client):
        """Test with invalid page number."""
        response = client.get("/api/v1/monitoring/logs?page=0")

        # Should return 422 validation error
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_page_size_too_large(self, client):
        """Test with page size exceeding maximum."""
        response = client.get("/api/v1/monitoring/logs?page_size=2000")

        # Should return 422 validation error
        assert response.status_code == 422

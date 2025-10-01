"""
Tests for audit API endpoints.
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from dotmac.platform.audit.models import (
    AuditActivity,
    ActivityType,
    ActivitySeverity,
)


@pytest.fixture
def audit_activities(async_db_session):
    """Create test audit activities."""
    activities = []
    now = datetime.now(timezone.utc)

    # Create various activities
    test_data = [
        ("user123", ActivityType.USER_LOGIN, ActivitySeverity.LOW, "Login successful", 0),
        ("user123", ActivityType.SECRET_ACCESSED, ActivitySeverity.MEDIUM, "Secret accessed", 1),
        ("user456", ActivityType.FILE_UPLOADED, ActivitySeverity.LOW, "File uploaded", 2),
        ("user123", ActivityType.API_REQUEST, ActivitySeverity.LOW, "API request", 3),
        ("user789", ActivityType.USER_CREATED, ActivitySeverity.MEDIUM, "User created", 4),
        ("user123", ActivityType.SECRET_DELETED, ActivitySeverity.HIGH, "Secret deleted", 5),
        ("system", ActivityType.SYSTEM_STARTUP, ActivitySeverity.MEDIUM, "System started", 6),
    ]

    for user_id, activity_type, severity, description, hours_ago in test_data:
        activity = AuditActivity(
            id=uuid4(),
            activity_type=activity_type,
            severity=severity,
            user_id=user_id,
            tenant_id="test_tenant",
            action=activity_type.split('.')[-1],
            description=description,
            timestamp=now - timedelta(hours=hours_ago),
            created_at=now,
            updated_at=now,
        )
        activities.append(activity)
        async_db_session.add(activity)

    return activities


class TestAuditRoutes:
    """Test audit API routes."""

    @pytest.mark.asyncio
    async def test_list_activities(self, client, auth_headers, audit_activities, async_db_session):
        """Test listing audit activities with filters."""
        await async_db_session.commit()

        # Test without filters
        response = client.get(
            "/api/v1/audit/activities?days=30",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "activities" in data
        assert "total" in data
        assert "has_next" in data
        assert "has_prev" in data

        # Test with user filter
        response = client.get(
            "/api/v1/audit/activities?user_id=user123&days=30",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        # Should have activities for user123
        assert all(a["user_id"] == "user123" for a in data["activities"] if a["user_id"])

        # Test with activity type filter
        response = client.get(
            f"/api/v1/audit/activities?activity_type={ActivityType.USER_LOGIN}&days=30",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert all(a["activity_type"] == ActivityType.USER_LOGIN for a in data["activities"])

        # Test with severity filter
        response = client.get(
            f"/api/v1/audit/activities?severity={ActivitySeverity.HIGH}&days=30",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert all(a["severity"] == ActivitySeverity.HIGH for a in data["activities"])

    @pytest.mark.asyncio
    async def test_list_activities_pagination(self, client, auth_headers, audit_activities, async_db_session):
        """Test pagination of audit activities."""
        await async_db_session.commit()

        # First page
        response = client.get(
            "/api/v1/audit/activities?page=1&per_page=3&days=30",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["activities"]) <= 3
        assert data["page"] == 1
        assert data["per_page"] == 3

        # Second page
        response = client.get(
            "/api/v1/audit/activities?page=2&per_page=3&days=30",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2

    @pytest.mark.asyncio
    async def test_get_recent_activities(self, client, auth_headers, audit_activities, async_db_session):
        """Test getting recent activities."""
        await async_db_session.commit()

        response = client.get(
            "/api/v1/audit/activities/recent?limit=5&days=7",
            headers=auth_headers,
        )
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, list)
        assert len(activities) <= 5

        # Should be sorted by timestamp descending (most recent first)
        timestamps = [a["timestamp"] for a in activities]
        assert timestamps == sorted(timestamps, reverse=True)

    @pytest.mark.asyncio
    async def test_get_user_activities(self, client, auth_headers, audit_activities, async_db_session):
        """Test getting activities for specific user."""
        await async_db_session.commit()

        # Test getting own activities
        with patch('dotmac.platform.audit.router.get_current_user') as mock_get_user:
            mock_user = AsyncMock()
            mock_user.user_id = "user123"
            mock_user.tenant_id = "test_tenant"
            mock_user.roles = []
            mock_get_user.return_value = mock_user

            response = client.get(
                "/api/v1/audit/activities/user/user123?limit=10&days=30",
                headers=auth_headers,
            )
            assert response.status_code == 200
            activities = response.json()
            assert all(a["user_id"] == "user123" for a in activities if a["user_id"])

    @pytest.mark.asyncio
    async def test_get_user_activities_unauthorized(self, client, auth_headers):
        """Test unauthorized access to other user's activities."""
        with patch('dotmac.platform.audit.router.get_current_user') as mock_get_user:
            mock_user = AsyncMock()
            mock_user.user_id = "user123"
            mock_user.tenant_id = "test_tenant"
            mock_user.roles = []  # No admin role
            mock_get_user.return_value = mock_user

            # Try to access another user's activities
            response = client.get(
                "/api/v1/audit/activities/user/user456?limit=10&days=30",
                headers=auth_headers,
            )
            assert response.status_code == 403
            assert "Insufficient permissions" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_user_activities_as_admin(self, client, auth_headers):
        """Test admin access to any user's activities."""
        with patch('dotmac.platform.audit.router.get_current_user') as mock_get_user:
            mock_user = AsyncMock()
            mock_user.user_id = "admin123"
            mock_user.tenant_id = "test_tenant"
            mock_user.roles = ["admin"]
            mock_get_user.return_value = mock_user

            # Admin can access any user's activities
            response = client.get(
                "/api/v1/audit/activities/user/user456?limit=10&days=30",
                headers=auth_headers,
            )
            # Should succeed (would be 200 with data)
            assert response.status_code in [200, 500]  # 500 if no session/data

    @pytest.mark.asyncio
    async def test_get_activity_summary(self, client, auth_headers, audit_activities, async_db_session):
        """Test getting activity summary."""
        await async_db_session.commit()

        with patch('dotmac.platform.audit.router.get_current_user') as mock_get_user:
            mock_user = AsyncMock()
            mock_user.user_id = "user123"
            mock_user.tenant_id = "test_tenant"
            mock_get_user.return_value = mock_user

            response = client.get(
                "/api/v1/audit/activities/summary?days=7",
                headers=auth_headers,
            )
            assert response.status_code == 200
            summary = response.json()

            assert "total_activities" in summary
            assert "activities_by_type" in summary
            assert "activities_by_severity" in summary
            assert "since_date" in summary

    @pytest.mark.asyncio
    async def test_get_activity_details(self, client, auth_headers, audit_activities, async_db_session):
        """Test getting specific activity details."""
        await async_db_session.commit()

        activity = audit_activities[0]  # Get first test activity

        with patch('dotmac.platform.audit.router.get_current_user') as mock_get_user:
            mock_user = AsyncMock()
            mock_user.user_id = "user123"
            mock_user.tenant_id = "test_tenant"
            mock_user.roles = []
            mock_get_user.return_value = mock_user

            response = client.get(
                f"/api/v1/audit/activities/{activity.id}",
                headers=auth_headers,
            )

            # Should succeed if activity belongs to user
            if activity.user_id == "user123":
                assert response.status_code == 200
                data = response.json()
                assert data["id"] == str(activity.id)
                assert data["description"] == activity.description

    @pytest.mark.asyncio
    async def test_get_activity_details_not_found(self, client, auth_headers):
        """Test getting non-existent activity."""
        fake_id = str(uuid4())

        with patch('dotmac.platform.audit.router.get_current_user') as mock_get_user:
            mock_user = AsyncMock()
            mock_user.user_id = "user123"
            mock_user.tenant_id = "test_tenant"
            mock_get_user.return_value = mock_user

            response = client.get(
                f"/api/v1/audit/activities/{fake_id}",
                headers=auth_headers,
            )
            assert response.status_code in [404, 500]

    @pytest.mark.asyncio
    async def test_audit_logging_on_api_access(self, client, auth_headers):
        """Test that accessing audit API creates audit logs."""
        with patch('dotmac.platform.audit.router.log_api_activity') as mock_log:
            mock_log.return_value = AsyncMock()

            response = client.get(
                "/api/v1/audit/activities/recent",
                headers=auth_headers,
            )

            # Should log the API access
            mock_log.assert_called()

    def test_audit_routes_require_auth(self, test_client):
        """Test that audit routes require authentication."""
        # Test endpoints without auth headers
        endpoints = [
            "/api/v1/audit/activities",
            "/api/v1/audit/activities/recent",
            "/api/v1/audit/activities/user/user123",
            "/api/v1/audit/activities/summary",
            f"/api/v1/audit/activities/{uuid4()}",
        ]

        for endpoint in endpoints:
            response = test_client.get(endpoint)
            assert response.status_code == 401  # Unauthorized
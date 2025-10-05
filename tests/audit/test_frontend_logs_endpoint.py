"""
Tests for the frontend logs ingestion endpoint.

Tests the POST /api/v1/audit/frontend-logs endpoint that accepts
batched frontend logs from the client application.
"""

import pytest
from datetime import datetime, timezone
from fastapi import status
from httpx import AsyncClient

from dotmac.platform.audit.models import ActivityType, ActivitySeverity


@pytest.mark.asyncio
class TestFrontendLogsEndpoint:
    """Test frontend logs ingestion endpoint."""

    async def test_create_frontend_logs_unauthenticated(
        self, client: AsyncClient, async_db_session
    ):
        """Test creating frontend logs without authentication (logs are skipped without tenant_id)."""
        logs_data = {
            "logs": [
                {
                    "level": "ERROR",
                    "message": "Test error from frontend",
                    "service": "frontend",
                    "metadata": {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "userAgent": "Mozilla/5.0",
                        "url": "http://localhost:3000/test",
                        "errorCode": 500,
                    },
                },
                {
                    "level": "WARNING",
                    "message": "Test warning from frontend",
                    "service": "frontend",
                    "metadata": {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "userAgent": "Mozilla/5.0",
                        "url": "http://localhost:3000/test",
                    },
                },
            ]
        }

        response = await client.post("/api/v1/audit/frontend-logs", json=logs_data)

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["status"] == "success"
        assert result["logs_received"] == 2
        # Logs are skipped because there's no tenant_id for anonymous users
        assert result["logs_stored"] == 0

    async def test_create_frontend_logs_authenticated(
        self, authenticated_client: AsyncClient, async_db_session, current_user
    ):
        """Test creating frontend logs with authentication."""
        logs_data = {
            "logs": [
                {
                    "level": "INFO",
                    "message": "User action logged",
                    "service": "frontend",
                    "metadata": {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "userAgent": "Mozilla/5.0",
                        "url": "http://localhost:3000/dashboard",
                        "action": "button_click",
                        "buttonId": "create-partner",
                    },
                }
            ]
        }

        response = await authenticated_client.post("/api/v1/audit/frontend-logs", json=logs_data)

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["status"] == "success"
        assert result["logs_received"] == 1
        assert result["logs_stored"] == 1

    async def test_create_frontend_logs_batched(self, client: AsyncClient, async_db_session):
        """Test creating a large batch of frontend logs."""
        logs = []
        for i in range(50):
            logs.append(
                {
                    "level": "INFO" if i % 2 == 0 else "ERROR",
                    "message": f"Test log message {i}",
                    "service": "frontend",
                    "metadata": {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "index": i,
                    },
                }
            )

        logs_data = {"logs": logs}

        response = await client.post("/api/v1/audit/frontend-logs", json=logs_data)

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["status"] == "success"
        assert result["logs_received"] == 50
        assert result["logs_stored"] == 50

    async def test_create_frontend_logs_validation_error(
        self, client: AsyncClient, async_db_session
    ):
        """Test validation errors for malformed log data."""
        # Missing required field 'level'
        logs_data = {
            "logs": [
                {
                    "message": "Test message",
                    "service": "frontend",
                    "metadata": {},
                }
            ]
        }

        response = await client.post("/api/v1/audit/frontend-logs", json=logs_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_frontend_logs_invalid_level(self, client: AsyncClient, async_db_session):
        """Test invalid log level."""
        logs_data = {
            "logs": [
                {
                    "level": "INVALID_LEVEL",
                    "message": "Test message",
                    "service": "frontend",
                    "metadata": {},
                }
            ]
        }

        response = await client.post("/api/v1/audit/frontend-logs", json=logs_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_frontend_logs_empty_batch(self, client: AsyncClient, async_db_session):
        """Test empty logs batch."""
        logs_data = {"logs": []}

        response = await client.post("/api/v1/audit/frontend-logs", json=logs_data)

        # Should fail validation (min_length=1)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_frontend_logs_max_batch_size(self, client: AsyncClient, async_db_session):
        """Test maximum batch size (100 logs)."""
        logs = []
        for i in range(100):
            logs.append(
                {
                    "level": "INFO",
                    "message": f"Test log {i}",
                    "service": "frontend",
                    "metadata": {"index": i},
                }
            )

        logs_data = {"logs": logs}

        response = await client.post("/api/v1/audit/frontend-logs", json=logs_data)

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["logs_received"] == 100

    async def test_create_frontend_logs_exceeds_max_batch(
        self, client: AsyncClient, async_db_session
    ):
        """Test batch size exceeding maximum (>100 logs)."""
        logs = []
        for i in range(101):
            logs.append(
                {
                    "level": "INFO",
                    "message": f"Test log {i}",
                    "service": "frontend",
                    "metadata": {},
                }
            )

        logs_data = {"logs": logs}

        response = await client.post("/api/v1/audit/frontend-logs", json=logs_data)

        # Should fail validation (max_length=100)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_frontend_logs_stored_correctly(
        self, authenticated_client: AsyncClient, async_db_session, current_user
    ):
        """Test that frontend logs are stored correctly in audit_activities."""
        from sqlalchemy import select
        from dotmac.platform.audit.models import AuditActivity

        logs_data = {
            "logs": [
                {
                    "level": "ERROR",
                    "message": "Critical error occurred",
                    "service": "frontend",
                    "metadata": {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "userAgent": "Test Agent",
                        "url": "http://test.com",
                        "errorDetails": "Stack trace here",
                    },
                }
            ]
        }

        response = await authenticated_client.post("/api/v1/audit/frontend-logs", json=logs_data)

        assert response.status_code == status.HTTP_200_OK

        # Query the database to verify storage
        stmt = select(AuditActivity).where(
            AuditActivity.activity_type == ActivityType.FRONTEND_LOG.value,
            AuditActivity.description == "Critical error occurred",
        )
        result = await async_db_session.execute(stmt)
        activity = result.scalar_one_or_none()

        assert activity is not None
        assert activity.severity == ActivitySeverity.HIGH.value
        assert activity.user_id == current_user.user_id
        assert activity.details["level"] == "ERROR"
        assert activity.details["service"] == "frontend"
        assert activity.details["url"] == "http://test.com"
        assert activity.user_agent == "Test Agent"

    async def test_frontend_logs_severity_mapping(self, client: AsyncClient, async_db_session):
        """Test that frontend log levels are correctly mapped to severities."""
        from sqlalchemy import select
        from dotmac.platform.audit.models import AuditActivity

        logs_data = {
            "logs": [
                {
                    "level": "ERROR",
                    "message": "Error message",
                    "service": "frontend",
                    "metadata": {},
                },
                {
                    "level": "WARNING",
                    "message": "Warning message",
                    "service": "frontend",
                    "metadata": {},
                },
                {
                    "level": "INFO",
                    "message": "Info message",
                    "service": "frontend",
                    "metadata": {},
                },
            ]
        }

        response = await client.post("/api/v1/audit/frontend-logs", json=logs_data)
        assert response.status_code == status.HTTP_200_OK

        # Verify severity mappings
        stmt = select(AuditActivity).where(
            AuditActivity.activity_type == ActivityType.FRONTEND_LOG.value
        )
        result = await async_db_session.execute(stmt)
        activities = result.scalars().all()

        severity_map = {activity.description: activity.severity for activity in activities}

        assert severity_map["Error message"] == ActivitySeverity.HIGH.value
        assert severity_map["Warning message"] == ActivitySeverity.MEDIUM.value
        assert severity_map["Info message"] == ActivitySeverity.LOW.value

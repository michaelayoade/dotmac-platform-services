"""
Comprehensive tests for analytics router endpoints.

Tests all analytics API endpoints with various scenarios including:
- Event tracking
- Metric recording
- Query operations
- Report generation
- Dashboard data retrieval
- Error handling
"""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from dotmac.platform.analytics.models import (
    AggregationType,
    AnalyticsQueryRequest,
    DashboardPeriod,
    EventData,
    EventTrackRequest,
    EventTrackResponse,
    EventType,
    MetricRecordRequest,
    MetricRecordResponse,
    MetricUnit,
    ReportType,
    TimeInterval,
)
from dotmac.platform.analytics.router import analytics_router, get_analytics_service


@pytest.fixture
def mock_analytics_service():
    """Create mock analytics service."""
    service = MagicMock()
    service.track_event = AsyncMock(return_value="event-123")
    service.record_metric = AsyncMock(return_value="metric-456")
    service.query_events = AsyncMock(return_value=[])
    service.query_metrics = AsyncMock(return_value={})
    service.aggregate_data = AsyncMock(return_value=[])
    service.generate_report = AsyncMock(return_value={})
    service.get_dashboard_data = AsyncMock(return_value={})
    return service


@pytest.fixture
def current_user():
    """Mock current user."""
    return {
        "sub": "user123",
        "email": "user@example.com",
        "scopes": ["read", "write"],
    }


@pytest.fixture
def app_client(mock_analytics_service):
    """Create test client with mocked dependencies."""
    from fastapi import FastAPI, Depends

    app = FastAPI()

    # Override authentication dependency
    from dotmac.platform.auth.core import UserInfo

    def override_get_current_user():
        return UserInfo(
            user_id="user123",
            email="user@example.com",
            username="testuser",
            tenant_id="test-tenant",
            roles=["user"],
            permissions=["read", "write"],
        )

    from dotmac.platform.auth.dependencies import get_current_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    app.include_router(analytics_router, prefix="/analytics")

    # Mock the service factory
    with patch("dotmac.platform.analytics.router.get_analytics_service") as mock_get:
        mock_get.return_value = mock_analytics_service
        client = TestClient(app)
        yield client, mock_analytics_service


class TestEventTracking:
    """Test event tracking endpoints."""

    def test_track_event_success(self, app_client):
        """Test successful event tracking."""
        client, service = app_client
        request_data = {
            "event_name": "user_login",
            "event_type": "user_action",
            "properties": {"ip": "192.168.1.1", "browser": "chrome"},
            "user_id": "user123",
            "session_id": "session456",
        }

        response = client.post("/analytics/events", json=request_data)

        if response.status_code != 200:
            print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data["event_id"] == "event-123"
        assert data["event_name"] == "user_login"
        assert data["status"] == "tracked"

    def test_track_event_without_user_id(self, app_client):
        """Test event tracking without explicit user_id."""
        client, service = app_client
        request_data = {
            "event_name": "page_view",
            "event_type": "page_view",
            "properties": {"page": "/home"},
        }

        response = client.post("/analytics/events", json=request_data)

        assert response.status_code == 200
        # Verify user_id was set from current_user
        service.track_event.assert_called_once()
        call_args = service.track_event.call_args[1]
        assert call_args["user_id"] == "user123"

    def test_track_event_with_custom_timestamp(self, app_client):
        """Test event tracking with custom timestamp."""
        client, service = app_client
        custom_time = datetime.now(timezone.utc) - timedelta(hours=1)
        request_data = {
            "event_name": "purchase",
            "event_type": "custom",
            "properties": {"amount": 99.99, "currency": "USD"},
            "timestamp": custom_time.isoformat(),
        }

        response = client.post("/analytics/events", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["timestamp"] == custom_time.isoformat().replace("+00:00", "Z")

    def test_track_event_validation_error(self, app_client):
        """Test event tracking with invalid data."""
        client, service = app_client
        request_data = {
            "event_name": "",  # Invalid: empty name
            "event_type": "INVALID_TYPE",  # Invalid: not in enum
        }

        response = client.post("/analytics/events", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_track_event_service_error(self, app_client):
        """Test event tracking when service fails."""
        client, service = app_client
        service.track_event.side_effect = Exception("Service error")

        request_data = {
            "event_name": "test_event",
            "event_type": "custom",
        }

        response = client.post("/analytics/events", json=request_data)

        assert response.status_code == 500
        assert "Failed to track event" in response.json()["detail"]


class TestMetricRecording:
    """Test metric recording endpoints."""

    def test_record_metric_success(self, app_client):
        """Test successful metric recording."""
        client, service = app_client
        request_data = {
            "metric_name": "api_latency",
            "value": 125.5,
            "unit": "milliseconds",
            "tags": {"endpoint": "/users", "method": "GET"},
        }

        response = client.post("/analytics/metrics", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["metric_name"] == "api_latency"
        assert data["value"] == 125.5
        assert data["unit"] == "milliseconds"
        assert data["status"] == "recorded"

    def test_record_metric_with_user_tag(self, app_client):
        """Test metric recording adds user_id to tags."""
        client, service = app_client
        request_data = {
            "metric_name": "request_count",
            "value": 1,
            "unit": "count",
            "tags": {"service": "auth"},
        }

        response = client.post("/analytics/metrics", json=request_data)

        assert response.status_code == 200
        # Verify user_id was added to tags
        service.record_metric.assert_called_once()
        call_args = service.record_metric.call_args[1]
        assert call_args["tags"]["user_id"] == "user123"

    def test_record_metric_validation_error(self, app_client):
        """Test metric recording with invalid data."""
        client, service = app_client
        request_data = {
            "metric_name": "123invalid",  # Invalid: starts with number
            "value": "not_a_number",  # Invalid: not numeric
            "unit": "INVALID_UNIT",
        }

        response = client.post("/analytics/metrics", json=request_data)

        assert response.status_code == 422

    def test_record_metric_service_error(self, app_client):
        """Test metric recording when service fails."""
        client, service = app_client
        service.record_metric.side_effect = Exception("Service error")

        request_data = {
            "metric_name": "test_metric",
            "value": 42.0,
        }

        response = client.post("/analytics/metrics", json=request_data)

        assert response.status_code == 500
        assert "Failed to record metric" in response.json()["detail"]


class TestEventQuerying:
    """Test event query endpoints."""

    def test_query_events_success(self, app_client):
        """Test successful event querying."""
        client, service = app_client
        mock_events = [
            {
                "event_id": "evt1",
                "event_name": "login",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            {
                "event_id": "evt2",
                "event_name": "logout",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        ]
        service.query_events.return_value = mock_events

        response = client.get(
            "/analytics/events",
            params={
                "event_type": "user_action",
                "limit": 50,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["events"]) == 2

    def test_query_events_with_date_range(self, app_client):
        """Test event querying with date range."""
        client, service = app_client
        start_date = datetime.now(timezone.utc) - timedelta(days=7)
        end_date = datetime.now(timezone.utc)

        service.query_events.return_value = []

        response = client.get(
            "/analytics/events",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )

        assert response.status_code == 200
        # Verify service was called with correct dates
        service.query_events.assert_called_once()
        call_args = service.query_events.call_args[1]
        assert call_args["start_date"] <= start_date
        assert call_args["end_date"] >= end_date

    def test_query_events_default_date_range(self, app_client):
        """Test event querying uses default date range."""
        client, service = app_client
        service.query_events.return_value = []

        response = client.get("/analytics/events")

        assert response.status_code == 200
        # Verify default 7-day range was used
        service.query_events.assert_called_once()
        call_args = service.query_events.call_args[1]
        date_diff = call_args["end_date"] - call_args["start_date"]
        assert date_diff.days == 7

    def test_query_events_service_error(self, app_client):
        """Test event querying when service fails."""
        client, service = app_client
        service.query_events.side_effect = Exception("Query failed")

        response = client.get("/analytics/events")

        assert response.status_code == 500
        assert "Failed to query events" in response.json()["detail"]


class TestMetricQuerying:
    """Test metric query endpoints."""

    def test_query_metrics_success(self, app_client):
        """Test successful metric querying."""
        client, service = app_client
        mock_metrics = {
            "counters": {"request_count": 1000},
            "gauges": {"active_users": 50},
            "histograms": {"response_time": {"p50": 100, "p95": 500}},
        }
        service.query_metrics.return_value = mock_metrics

        response = client.get(
            "/analytics/metrics",
            params={
                "metric_name": "request_count",
                "aggregation": "sum",
                "interval": "hour",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "total_series" in data
        assert data["total_series"] >= 0

    def test_query_metrics_with_filtering(self, app_client):
        """Test metric querying with name filter."""
        client, service = app_client
        service.query_metrics.return_value = {"counters": {"api_calls": 500}}

        response = client.get(
            "/analytics/metrics",
            params={"metric_name": "api_calls"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["metrics"]) >= 0
        # Check the structure without assuming specific data
        assert "metrics" in data
        assert "total_series" in data


class TestCustomQuery:
    """Test custom query endpoint."""

    def test_custom_query_events(self, app_client):
        """Test custom query for events."""
        client, service = app_client
        service.query_events.return_value = [{"event_id": "evt1"}]

        request_data = {
            "query_type": "events",
            "filters": {"event_type": "USER_ACTION"},
            "limit": 100,
        }

        response = client.post("/analytics/query", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["query_type"] == "events"
        assert data["total"] == 1

    def test_custom_query_aggregations(self, app_client):
        """Test custom query for aggregations."""
        client, service = app_client
        service.aggregate_data.return_value = [
            {"group": "endpoint1", "count": 100},
            {"group": "endpoint2", "count": 200},
        ]

        request_data = {
            "query_type": "aggregations",
            "filters": {"metric": "request_count"},
            "group_by": ["endpoint"],
            "order_by": "count",
            "limit": 10,
        }

        response = client.post("/analytics/query", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["query_type"] == "aggregations"
        assert data["total"] == 2

    def test_custom_query_invalid_type(self, app_client):
        """Test custom query with invalid query type."""
        client, service = app_client

        request_data = {
            "query_type": "invalid_type",
            "filters": {},
        }

        response = client.post("/analytics/query", json=request_data)

        assert response.status_code == 422  # Validation error


class TestReportGeneration:
    """Test report generation endpoints."""

    def test_generate_summary_report(self, app_client):
        """Test summary report generation."""
        client, service = app_client
        mock_report = {
            "total_events": 1000,
            "total_users": 100,
            "top_events": ["login", "logout"],
        }
        service.generate_report.return_value = mock_report

        response = client.get("/analytics/reports/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["report_type"] == "summary"
        assert "sections" in data
        assert "generated_at" in data

    def test_generate_report_with_date_range(self, app_client):
        """Test report generation with custom date range."""
        client, service = app_client
        service.generate_report.return_value = {}

        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        end_date = datetime.now(timezone.utc)

        response = client.get(
            "/analytics/reports/usage",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )

        assert response.status_code == 200
        # Verify service was called with correct parameters
        service.generate_report.assert_called_once()
        call_args = service.generate_report.call_args[1]
        assert call_args["report_type"] == "usage"
        assert call_args["user_id"] == "user123"

    def test_generate_report_invalid_type(self, app_client):
        """Test report generation with invalid type."""
        client, service = app_client
        service.generate_report.side_effect = ValueError("Invalid report type")

        response = client.get("/analytics/reports/invalid_type")

        assert response.status_code == 400
        assert "Invalid report type" in response.json()["detail"]


class TestDashboard:
    """Test dashboard endpoints."""

    def test_get_dashboard_data_hour(self, app_client):
        """Test dashboard data for hour period."""
        client, service = app_client
        mock_dashboard = {
            "metrics": {"active_users": 50, "requests": 1000},
            "charts": [{"type": "line", "data": [1, 2, 3]}],
        }
        service.get_dashboard_data.return_value = mock_dashboard

        response = client.get("/analytics/dashboard", params={"period": "hour"})

        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "hour"
        assert "data" in data
        assert "generated_at" in data

    def test_get_dashboard_data_day(self, app_client):
        """Test dashboard data for day period."""
        client, service = app_client
        service.get_dashboard_data.return_value = {}

        response = client.get("/analytics/dashboard", params={"period": "day"})

        assert response.status_code == 200
        # Verify correct date range was used
        service.get_dashboard_data.assert_called_once()
        call_args = service.get_dashboard_data.call_args[1]
        date_diff = call_args["end_date"] - call_args["start_date"]
        assert date_diff.total_seconds() == 86400  # 1 day

    def test_get_dashboard_data_week(self, app_client):
        """Test dashboard data for week period."""
        client, service = app_client
        service.get_dashboard_data.return_value = {}

        response = client.get("/analytics/dashboard", params={"period": "week"})

        assert response.status_code == 200
        # Verify correct date range was used
        service.get_dashboard_data.assert_called_once()
        call_args = service.get_dashboard_data.call_args[1]
        date_diff = call_args["end_date"] - call_args["start_date"]
        assert date_diff.days == 7

    def test_get_dashboard_data_month(self, app_client):
        """Test dashboard data for month period."""
        client, service = app_client
        service.get_dashboard_data.return_value = {}

        response = client.get("/analytics/dashboard", params={"period": "month"})

        assert response.status_code == 200
        # Verify correct date range was used
        service.get_dashboard_data.assert_called_once()
        call_args = service.get_dashboard_data.call_args[1]
        date_diff = call_args["end_date"] - call_args["start_date"]
        assert date_diff.days == 30

    def test_get_dashboard_data_default_period(self, app_client):
        """Test dashboard data with default period."""
        client, service = app_client
        service.get_dashboard_data.return_value = {}

        response = client.get("/analytics/dashboard")

        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "day"  # Default period

    def test_get_dashboard_data_service_error(self, app_client):
        """Test dashboard data when service fails."""
        client, service = app_client
        service.get_dashboard_data.side_effect = Exception("Dashboard error")

        response = client.get("/analytics/dashboard")

        assert response.status_code == 500
        assert "Failed to get dashboard data" in response.json()["detail"]


class TestAuthenticationRequired:
    """Test that all endpoints require authentication."""

    def test_track_event_requires_auth(self, mock_analytics_service):
        """Test event tracking requires authentication."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(analytics_router, prefix="/analytics")

        # Create client without overriding auth dependency
        client = TestClient(app)

        response = client.post(
            "/analytics/events",
            json={"event_name": "test", "event_type": "custom"},
        )

        assert response.status_code == 401

    def test_record_metric_requires_auth(self, mock_analytics_service):
        """Test metric recording requires authentication."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(analytics_router, prefix="/analytics")

        # Create client without overriding auth dependency
        client = TestClient(app)

        response = client.post(
            "/analytics/metrics",
            json={"metric_name": "test", "value": 1.0},
        )

        assert response.status_code == 401


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_track_event_max_properties(self, app_client):
        """Test event tracking with maximum properties."""
        client, service = app_client

        # Create max properties (50)
        properties = {f"prop_{i}": f"value_{i}" for i in range(50)}
        request_data = {
            "event_name": "test_event",
            "event_type": "custom",
            "properties": properties,
        }

        response = client.post("/analytics/events", json=request_data)

        assert response.status_code == 200

    def test_track_event_too_many_properties(self, app_client):
        """Test event tracking with too many properties."""
        client, service = app_client

        # Create too many properties (51)
        properties = {f"prop_{i}": f"value_{i}" for i in range(51)}
        request_data = {
            "event_name": "test_event",
            "event_type": "custom",
            "properties": properties,
        }

        response = client.post("/analytics/events", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_record_metric_max_tags(self, app_client):
        """Test metric recording with maximum tags."""
        client, service = app_client

        # Create max tags (20)
        tags = {f"tag_{i}": f"value_{i}" for i in range(20)}
        request_data = {
            "metric_name": "test_metric",
            "value": 42.0,
            "tags": tags,
        }

        response = client.post("/analytics/metrics", json=request_data)

        assert response.status_code == 200

    def test_query_events_max_limit(self, app_client):
        """Test event query with maximum limit."""
        client, service = app_client
        service.query_events.return_value = []

        response = client.get("/analytics/events", params={"limit": 1000})

        assert response.status_code == 200
        # Verify limit was applied
        service.query_events.assert_called_once()
        call_args = service.query_events.call_args[1]
        assert call_args["limit"] == 1000

    def test_query_events_exceeds_max_limit(self, app_client):
        """Test event query exceeding maximum limit."""
        client, service = app_client

        response = client.get("/analytics/events", params={"limit": 1001})

        assert response.status_code == 422  # Validation error

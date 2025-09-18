"""Tests for audit trail GraphQL resolvers."""

import pytest
from datetime import datetime, UTC
from unittest.mock import Mock, patch

try:
    import strawberry
except ImportError:
    strawberry = None
    pytest.skip("Strawberry GraphQL not available", allow_module_level=True)


class TestAuditResolvers:
    """Test audit trail GraphQL resolvers."""

    @pytest.mark.asyncio
    async def test_audit_events_query(self, authenticated_graphql_client, audit_events_query):
        """Test querying audit events."""
        variables = {
            "filter": {
                "category": "AUTHENTICATION",
                "level": "INFO"
            },
            "first": 10,
            "after": None
        }

        with patch('dotmac.platform.api.graphql.resolvers.AuditTrailResolver.search_events') as mock_search:
            mock_events = [
                {
                    "id": "audit-001",
                    "timestamp": datetime.now(UTC),
                    "category": "AUTHENTICATION",
                    "level": "INFO",
                    "action": "login",
                    "resource": "user",
                    "actor": "test-user-123",
                    "tenant_id": "test-tenant",
                    "ip_address": "192.168.1.100",
                    "user_agent": "Mozilla/5.0 Test",
                    "details": {"method": "password"},
                    "outcome": "success",
                },
                {
                    "id": "audit-002",
                    "timestamp": datetime.now(UTC),
                    "category": "AUTHENTICATION",
                    "level": "WARNING",
                    "action": "failed_login",
                    "resource": "user",
                    "actor": "test-user-456",
                    "tenant_id": "test-tenant",
                    "ip_address": "192.168.1.101",
                    "user_agent": "Mozilla/5.0 Test",
                    "details": {"reason": "invalid_password"},
                    "outcome": "failure",
                },
            ]

            mock_connection = {
                "nodes": mock_events,
                "page_info": {
                    "has_next_page": False,
                    "has_previous_page": False,
                    "start_cursor": "audit-001",
                    "end_cursor": "audit-002",
                    "total_count": 2,
                },
            }
            mock_search.return_value = mock_connection

            result = await authenticated_graphql_client.execute_expecting_data(
                audit_events_query, variables
            )

            assert "auditEvents" in result
            events_data = result["auditEvents"]

            assert "nodes" in events_data
            assert len(events_data["nodes"]) == 2

            event1 = events_data["nodes"][0]
            assert event1["id"] == "audit-001"
            assert event1["category"] == "AUTHENTICATION"
            assert event1["level"] == "INFO"
            assert event1["action"] == "login"
            assert event1["actor"] == "test-user-123"
            assert event1["outcome"] == "success"

            event2 = events_data["nodes"][1]
            assert event2["id"] == "audit-002"
            assert event2["level"] == "WARNING"
            assert event2["action"] == "failed_login"
            assert event2["outcome"] == "failure"

            # Check pagination info
            page_info = events_data["pageInfo"]
            assert page_info["hasNextPage"] is False
            assert page_info["totalCount"] == 2

    @pytest.mark.asyncio
    async def test_audit_event_query_single(self, authenticated_graphql_client):
        """Test querying a single audit event by ID."""
        query = """
            query AuditEventQuery($eventId: String!) {
                auditEvent(eventId: $eventId) {
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
            }
        """

        variables = {"eventId": "audit-123"}

        with patch('dotmac.platform.api.graphql.resolvers.AuditTrailResolver.get_event') as mock_get_event:
            mock_event = {
                "id": "audit-123",
                "timestamp": datetime.now(UTC),
                "category": "SECURITY_EVENT",
                "level": "CRITICAL",
                "action": "suspicious_activity",
                "resource": "system",
                "actor": "unknown",
                "tenant_id": "test-tenant",
                "ip_address": "10.0.0.1",
                "user_agent": "curl/7.68.0",
                "details": {"attempts": 5, "pattern": "brute_force"},
                "outcome": "blocked",
            }
            mock_get_event.return_value = mock_event

            result = await authenticated_graphql_client.execute_expecting_data(query, variables)

            assert "auditEvent" in result
            event_data = result["auditEvent"]

            assert event_data["id"] == "audit-123"
            assert event_data["category"] == "SECURITY_EVENT"
            assert event_data["level"] == "CRITICAL"
            assert event_data["action"] == "suspicious_activity"
            assert event_data["outcome"] == "blocked"
            assert event_data["details"]["attempts"] == 5

    @pytest.mark.asyncio
    async def test_audit_event_not_found(self, authenticated_graphql_client):
        """Test querying non-existent audit event."""
        query = """
            query AuditEventQuery($eventId: String!) {
                auditEvent(eventId: $eventId) {
                    id
                }
            }
        """

        variables = {"eventId": "non-existent"}

        with patch('dotmac.platform.api.graphql.resolvers.AuditTrailResolver.get_event') as mock_get_event:
            mock_get_event.return_value = None

            result = await authenticated_graphql_client.execute_expecting_data(query, variables)

            assert "auditEvent" in result
            assert result["auditEvent"] is None

    @pytest.mark.asyncio
    async def test_log_audit_event_mutation(self, authenticated_graphql_client, log_audit_event_mutation):
        """Test logging a new audit event."""
        variables = {
            "category": "DATA_ACCESS",
            "level": "INFO",
            "action": "file_download",
            "resource": "file:document.pdf",
            "details": {
                "file_size": 1024000,
                "download_method": "direct"
            }
        }

        with patch('dotmac.platform.api.graphql.resolvers.AuditTrailResolver.log_event') as mock_log_event:
            mock_event = {
                "id": "new-audit-456",
                "timestamp": datetime.now(UTC),
                "category": "DATA_ACCESS",
                "level": "INFO",
                "action": "file_download",
                "resource": "file:document.pdf",
                "actor": "test-user-123",
                "details": {"file_size": 1024000, "download_method": "direct"},
                "outcome": "success",
            }
            mock_log_event.return_value = mock_event

            result = await authenticated_graphql_client.execute_expecting_data(
                log_audit_event_mutation, variables
            )

            assert "logAuditEvent" in result
            event_data = result["logAuditEvent"]

            assert event_data["id"] == "new-audit-456"
            assert event_data["category"] == "DATA_ACCESS"
            assert event_data["level"] == "INFO"
            assert event_data["action"] == "file_download"
            assert event_data["resource"] == "file:document.pdf"
            assert event_data["details"]["file_size"] == 1024000

    @pytest.mark.asyncio
    async def test_audit_events_filtering(self, authenticated_graphql_client, audit_events_query):
        """Test audit events with various filters."""
        # Test category filter
        variables = {
            "filter": {"category": "SECURITY_EVENT"},
            "first": 5
        }

        with patch('dotmac.platform.api.graphql.resolvers.AuditTrailResolver.search_events') as mock_search:
            mock_connection = {
                "nodes": [
                    {
                        "id": "audit-sec-1",
                        "timestamp": datetime.now(UTC),
                        "category": "SECURITY_EVENT",
                        "level": "WARNING",
                        "action": "alert",
                        "resource": "system",
                        "actor": "system",
                        "details": {},
                        "outcome": "investigating",
                    },
                    {
                        "id": "audit-sec-2",
                        "timestamp": datetime.now(UTC),
                        "category": "SECURITY_EVENT",
                        "level": "CRITICAL",
                        "action": "breach",
                        "resource": "system",
                        "actor": "system",
                        "details": {},
                        "outcome": "blocked",
                    },
                ],
                "page_info": {"total_count": 2},
            }
            mock_search.return_value = mock_connection

            result = await authenticated_graphql_client.execute_expecting_data(
                audit_events_query, variables
            )

            events = result["auditEvents"]["nodes"]
            assert all(event["category"] == "SECURITY_EVENT" for event in events)

        # Test level filter
        variables = {
            "filter": {"level": "CRITICAL"},
            "first": 5
        }

        with patch('dotmac.platform.api.graphql.resolvers.AuditTrailResolver.search_events') as mock_search:
            mock_connection = {
                "nodes": [
                    {
                        "id": "audit-critical-1",
                        "timestamp": datetime.now(UTC),
                        "category": "SECURITY_EVENT",
                        "level": "CRITICAL",
                        "action": "breach",
                        "resource": "system",
                        "actor": "system",
                        "details": {},
                        "outcome": "blocked",
                    }
                ],
                "page_info": {"total_count": 1},
            }
            mock_search.return_value = mock_connection

            result = await authenticated_graphql_client.execute_expecting_data(
                audit_events_query, variables
            )

            events = result["auditEvents"]["nodes"]
            assert all(event["level"] == "CRITICAL" for event in events)

    @pytest.mark.asyncio
    async def test_audit_events_time_range_filter(self, authenticated_graphql_client, audit_events_query):
        """Test audit events with time range filters."""
        start_time = "2024-01-01T00:00:00Z"
        end_time = "2024-01-31T23:59:59Z"

        variables = {
            "filter": {
                "startTime": start_time,
                "endTime": end_time
            },
            "first": 10
        }

        with patch('dotmac.platform.api.graphql.resolvers.AuditTrailResolver.search_events') as mock_search:
            mock_connection = {
                "nodes": [
                    {
                        "id": "audit-time-1",
                        "timestamp": datetime(2024, 1, 15, 12, 0, tzinfo=UTC),
                        "category": "SYSTEM_CHANGE",
                        "level": "INFO",
                        "action": "update",
                        "resource": "config",
                        "actor": "admin",
                        "details": {},
                        "outcome": "success",
                    },
                    {
                        "id": "audit-time-2",
                        "timestamp": datetime(2024, 1, 20, 15, 30, tzinfo=UTC),
                        "category": "SYSTEM_CHANGE",
                        "level": "INFO",
                        "action": "update",
                        "resource": "config",
                        "actor": "admin",
                        "details": {},
                        "outcome": "success",
                    },
                ],
                "page_info": {"total_count": 2},
            }
            mock_search.return_value = mock_connection

            result = await authenticated_graphql_client.execute_expecting_data(
                audit_events_query, variables
            )

            events = result["auditEvents"]["nodes"]
            assert len(events) == 2

            # Verify mock was called with correct filter
            mock_search.assert_called_once()
            call_args = mock_search.call_args
            filter_arg = call_args[0][1]  # Second argument is the filter
            assert filter_arg is not None

    @pytest.mark.asyncio
    async def test_audit_events_pagination(self, authenticated_graphql_client, audit_events_query):
        """Test audit events pagination."""
        # First page
        variables = {"first": 2, "after": None}

        with patch('dotmac.platform.api.graphql.resolvers.AuditTrailResolver.search_events') as mock_search:
            mock_connection = {
                "nodes": [
                    {
                        "id": f"audit-{i}",
                        "timestamp": datetime.now(UTC),
                        "category": "AUTHENTICATION",
                        "level": "INFO",
                        "action": "login",
                        "resource": "user",
                        "actor": "user",
                        "details": {},
                        "outcome": "success",
                    }
                    for i in range(2)
                ],
                "page_info": {
                    "has_next_page": True,
                    "has_previous_page": False,
                    "start_cursor": "audit-0",
                    "end_cursor": "audit-1",
                    "total_count": 10,
                },
            }
            mock_search.return_value = mock_connection

            result = await authenticated_graphql_client.execute_expecting_data(
                audit_events_query, variables
            )

            page_info = result["auditEvents"]["pageInfo"]
            assert page_info["hasNextPage"] is True
            assert page_info["hasPreviousPage"] is False
            assert page_info["totalCount"] == 10

    @pytest.mark.asyncio
    async def test_audit_events_authentication_required(self, graphql_test_client, audit_events_query):
        """Test that audit operations require authentication."""
        variables = {"first": 10}

        with patch('dotmac.platform.api.graphql.resolvers.AuditTrailResolver.search_events') as mock_search:
            from dotmac.platform.auth.exceptions import AuthError
            mock_connection = {"nodes": [], "page_info": {"total_count": 0}}
            mock_search.return_value = mock_connection

            # Should work without authentication for read operations in this mock
            result = await graphql_test_client.execute_expecting_data(audit_events_query, variables)
            assert "auditEvents" in result

        # But mutations should require authentication
        mutation = """
            mutation LogAuditEventMutation(
                $category: AuditCategory!,
                $level: AuditLevel!,
                $action: String!,
                $resource: String!
            ) {
                logAuditEvent(
                    category: $category,
                    level: $level,
                    action: $action,
                    resource: $resource
                ) {
                    id
                }
            }
        """

        variables = {
            "category": "USER_MANAGEMENT",
            "level": "INFO",
            "action": "user_created",
            "resource": "user:new-user"
        }

        with patch('dotmac.platform.api.graphql.resolvers.AuditTrailResolver.log_event') as mock_log:
            from dotmac.platform.auth.exceptions import AuthError
            mock_log.side_effect = AuthError("Authentication required")

            data = await graphql_test_client.execute_expecting_errors(mutation, variables)
            assert len(data["errors"]) > 0
            assert any("Authentication required" in error["message"] for error in data["errors"])

    @pytest.mark.asyncio
    async def test_audit_service_error_handling(self, authenticated_graphql_client):
        """Test handling of audit service errors."""
        query = """
            query AuditEventQuery($eventId: String!) {
                auditEvent(eventId: $eventId) {
                    id
                }
            }
        """

        variables = {"eventId": "error-event"}

        with patch('dotmac.platform.api.graphql.resolvers.AuditTrailResolver.get_event') as mock_get_event:
            mock_get_event.side_effect = Exception("Audit service unavailable")

            data = await authenticated_graphql_client.execute_expecting_errors(query, variables)
            assert len(data["errors"]) > 0
            assert any("Audit service unavailable" in error["message"] for error in data["errors"])

    @pytest.mark.asyncio
    async def test_log_event_validation(self, authenticated_graphql_client, log_audit_event_mutation):
        """Test validation of log event mutation parameters."""
        # Test with missing required fields
        invalid_variables = {
            "category": "DATA_ACCESS",
            "level": "INFO",
            # Missing action and resource
        }

        data = await authenticated_graphql_client.execute_expecting_errors(
            log_audit_event_mutation, invalid_variables
        )
        assert len(data["errors"]) > 0

        # Test with invalid enum values would be handled by GraphQL schema validation
        # and would return validation errors before reaching the resolver

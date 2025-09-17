"""Basic GraphQL schema tests."""

import pytest
from unittest.mock import patch

# Skip if GraphQL dependencies not available
try:
    import strawberry
    from strawberry.test import BaseGraphQLTestClient
except ImportError:
    strawberry = None
    pytest.skip("Strawberry GraphQL not available", allow_module_level=True)

from dotmac.platform.api.graphql.schema import schema


class TestGraphQLSchemaBasic:
    """Basic schema validation and health check tests."""

    def test_schema_exists(self):
        """Test that GraphQL schema is properly defined."""
        assert schema is not None, "GraphQL schema should be available when strawberry is installed"

    @pytest.mark.asyncio
    async def test_health_query(self, graphql_test_client, health_query):
        """Test basic health query."""
        result = await graphql_test_client.execute_expecting_data(health_query)

        assert "health" in result
        health_data = result["health"]

        assert health_data["status"] == "ok"
        assert "version" in health_data
        assert "timestamp" in health_data
        assert "services" in health_data
        assert isinstance(health_data["services"], list)

    @pytest.mark.asyncio
    async def test_health_query_no_auth_required(self, graphql_test_client, health_query):
        """Test that health query works without authentication."""
        # Don't set auth headers
        result = await graphql_test_client.execute_expecting_data(health_query)

        assert "health" in result
        assert result["health"]["status"] == "ok"

    @pytest.mark.asyncio
    async def test_invalid_query_syntax(self, graphql_test_client):
        """Test handling of invalid GraphQL syntax."""
        invalid_query = """
            query InvalidQuery {
                health {
                    status
                    nonExistentField
                }
            }
        """

        data = await graphql_test_client.execute_expecting_errors(invalid_query)
        assert len(data["errors"]) > 0
        assert any("Cannot query field" in error["message"] for error in data["errors"])

    @pytest.mark.asyncio
    async def test_query_depth_and_complexity(self, graphql_test_client):
        """Test that complex queries are handled properly."""
        complex_query = """
            query ComplexQuery {
                health {
                    status
                    version
                    timestamp
                    services
                }
            }
        """

        result = await graphql_test_client.execute_expecting_data(complex_query)
        assert "health" in result

    @pytest.mark.asyncio
    async def test_graphql_introspection(self, graphql_test_client):
        """Test GraphQL introspection query."""
        introspection_query = """
            query IntrospectionQuery {
                __schema {
                    types {
                        name
                        kind
                    }
                    queryType {
                        name
                    }
                    mutationType {
                        name
                    }
                    subscriptionType {
                        name
                    }
                }
            }
        """

        result = await graphql_test_client.execute_expecting_data(introspection_query)
        assert "__schema" in result
        schema_info = result["__schema"]

        # Check that basic types exist
        type_names = [t["name"] for t in schema_info["types"]]
        assert "Query" in type_names
        assert "Mutation" in type_names
        assert "Subscription" in type_names
        assert "HealthInfo" in type_names

        # Check root types
        assert schema_info["queryType"]["name"] == "Query"
        assert schema_info["mutationType"]["name"] == "Mutation"
        assert schema_info["subscriptionType"]["name"] == "Subscription"

    @pytest.mark.asyncio
    async def test_query_field_introspection(self, graphql_test_client):
        """Test introspection of Query type fields."""
        query = """
            query QueryFields {
                __type(name: "Query") {
                    name
                    fields {
                        name
                        description
                        type {
                            name
                        }
                    }
                }
            }
        """

        result = await graphql_test_client.execute_expecting_data(query)
        assert "__type" in result
        query_type = result["__type"]

        field_names = [field["name"] for field in query_type["fields"]]

        # Check that expected query fields exist
        expected_fields = [
            "health",
            "currentUser",
            "apiKeys",
            "sessions",
            "featureFlags",
            "featureFlag",
            "evaluateFlags",
            "secrets",
            "secretHistory",
            "metrics",
            "healthChecks",
            "traces",
            "auditEvents",
            "auditEvent",
            "services",
            "service",
        ]

        for field in expected_fields:
            assert field in field_names, f"Expected field '{field}' not found in Query type"

    @pytest.mark.asyncio
    async def test_mutation_field_introspection(self, graphql_test_client):
        """Test introspection of Mutation type fields."""
        query = """
            query MutationFields {
                __type(name: "Mutation") {
                    name
                    fields {
                        name
                        description
                        type {
                            name
                        }
                    }
                }
            }
        """

        result = await graphql_test_client.execute_expecting_data(query)
        assert "__type" in result
        mutation_type = result["__type"]

        field_names = [field["name"] for field in mutation_type["fields"]]

        # Check that expected mutation fields exist
        expected_mutations = [
            "createApiKey",
            "revokeApiKey",
            "invalidateSession",
            "upsertFeatureFlag",
            "deleteFeatureFlag",
            "toggleFeatureFlag",
            "logAuditEvent",
        ]

        for field in expected_mutations:
            assert field in field_names, f"Expected mutation '{field}' not found in Mutation type"

    @pytest.mark.asyncio
    async def test_subscription_field_introspection(self, graphql_test_client):
        """Test introspection of Subscription type fields."""
        query = """
            query SubscriptionFields {
                __type(name: "Subscription") {
                    name
                    fields {
                        name
                        description
                        type {
                            name
                        }
                    }
                }
            }
        """

        result = await graphql_test_client.execute_expecting_data(query)
        assert "__type" in result
        subscription_type = result["__type"]

        field_names = [field["name"] for field in subscription_type["fields"]]

        # Check that expected subscription fields exist
        expected_subscriptions = [
            "auditEventsStream",
            "metricsStream",
            "serviceHealthStream",
        ]

        for field in expected_subscriptions:
            assert field in field_names, f"Expected subscription '{field}' not found in Subscription type"

    @pytest.mark.asyncio
    async def test_enum_types_introspection(self, graphql_test_client):
        """Test that enum types are properly defined."""
        query = """
            query EnumTypes {
                auditCategory: __type(name: "AuditCategory") {
                    name
                    enumValues {
                        name
                        description
                    }
                }
                auditLevel: __type(name: "AuditLevel") {
                    name
                    enumValues {
                        name
                        description
                    }
                }
                serviceStatus: __type(name: "ServiceStatus") {
                    name
                    enumValues {
                        name
                        description
                    }
                }
                rolloutStrategy: __type(name: "RolloutStrategy") {
                    name
                    enumValues {
                        name
                        description
                    }
                }
            }
        """

        result = await graphql_test_client.execute_expecting_data(query)

        # Check AuditCategory enum
        audit_category = result["auditCategory"]
        assert audit_category["name"] == "AuditCategory"
        category_values = [ev["name"] for ev in audit_category["enumValues"]]
        assert "AUTHENTICATION" in category_values
        assert "SECURITY_EVENT" in category_values

        # Check AuditLevel enum
        audit_level = result["auditLevel"]
        assert audit_level["name"] == "AuditLevel"
        level_values = [ev["name"] for ev in audit_level["enumValues"]]
        assert "DEBUG" in level_values
        assert "INFO" in level_values
        assert "WARNING" in level_values
        assert "ERROR" in level_values
        assert "CRITICAL" in level_values

        # Check ServiceStatus enum
        service_status = result["serviceStatus"]
        assert service_status["name"] == "ServiceStatus"
        status_values = [ev["name"] for ev in service_status["enumValues"]]
        assert "HEALTHY" in status_values
        assert "UNHEALTHY" in status_values

        # Check RolloutStrategy enum
        rollout_strategy = result["rolloutStrategy"]
        assert rollout_strategy["name"] == "RolloutStrategy"
        strategy_values = [ev["name"] for ev in rollout_strategy["enumValues"]]
        assert "ALL_ON" in strategy_values
        assert "ALL_OFF" in strategy_values
        assert "PERCENTAGE" in strategy_values
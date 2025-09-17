"""Tests for feature flag GraphQL resolvers."""

import pytest
from datetime import datetime
from unittest.mock import patch, Mock

try:
    import strawberry
except ImportError:
    strawberry = None
    pytest.skip("Strawberry GraphQL not available", allow_module_level=True)


class TestFeatureFlagResolvers:
    """Test feature flag GraphQL resolvers."""

    @pytest.mark.asyncio
    async def test_feature_flags_query(self, authenticated_graphql_client, feature_flags_query):
        """Test querying feature flags."""
        variables = {"first": 10, "after": None}

        with patch('dotmac.platform.api.graphql.resolvers.FeatureFlagResolver.get_feature_flags') as mock_get_flags:
            # Mock the connection response
            from dotmac.platform.api.graphql.schema import FeatureFlagsConnection, FeatureFlag, PageInfo

            mock_flags = [
                Mock(
                    key="test-flag-1",
                    name="Test Flag 1",
                    description="A test feature flag",
                    enabled=True,
                    strategy="ALL_ON",
                    config={"percentage": 100},
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    created_by="admin"
                ),
                Mock(
                    key="test-flag-2",
                    name="Test Flag 2",
                    description="Another test flag",
                    enabled=False,
                    strategy="ALL_OFF",
                    config={},
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    created_by="admin"
                )
            ]

            mock_connection = Mock()
            mock_connection.nodes = mock_flags
            mock_connection.page_info = Mock(
                has_next_page=False,
                has_previous_page=False,
                start_cursor="test-flag-1",
                end_cursor="test-flag-2",
                total_count=2
            )
            mock_get_flags.return_value = mock_connection

            result = await authenticated_graphql_client.execute_expecting_data(
                feature_flags_query, variables
            )

            assert "featureFlags" in result
            flags_data = result["featureFlags"]

            assert "nodes" in flags_data
            assert len(flags_data["nodes"]) == 2

            flag1 = flags_data["nodes"][0]
            assert flag1["key"] == "test-flag-1"
            assert flag1["name"] == "Test Flag 1"
            assert flag1["enabled"] is True
            assert flag1["strategy"] == "ALL_ON"

            flag2 = flags_data["nodes"][1]
            assert flag2["key"] == "test-flag-2"
            assert flag2["name"] == "Test Flag 2"
            assert flag2["enabled"] is False
            assert flag2["strategy"] == "ALL_OFF"

            # Check pagination info
            page_info = flags_data["pageInfo"]
            assert page_info["hasNextPage"] is False
            assert page_info["totalCount"] == 2

    @pytest.mark.asyncio
    async def test_feature_flag_query_single(self, authenticated_graphql_client):
        """Test querying a single feature flag by key."""
        query = """
            query FeatureFlagQuery($key: String!) {
                featureFlag(key: $key) {
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
            }
        """

        variables = {"key": "test-flag"}

        with patch('dotmac.platform.api.graphql.resolvers.FeatureFlagResolver.get_feature_flag') as mock_get_flag:
            mock_flag = Mock(
                key="test-flag",
                name="Test Flag",
                description="A single test flag",
                enabled=True,
                strategy="PERCENTAGE",
                config={"percentage": 50, "user_list": ["user1", "user2"]},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                created_by="admin"
            )
            mock_get_flag.return_value = mock_flag

            result = await authenticated_graphql_client.execute_expecting_data(query, variables)

            assert "featureFlag" in result
            flag_data = result["featureFlag"]

            assert flag_data["key"] == "test-flag"
            assert flag_data["name"] == "Test Flag"
            assert flag_data["enabled"] is True
            assert flag_data["strategy"] == "PERCENTAGE"
            assert flag_data["config"]["percentage"] == 50
            assert flag_data["config"]["user_list"] == ["user1", "user2"]

    @pytest.mark.asyncio
    async def test_feature_flag_not_found(self, authenticated_graphql_client):
        """Test querying non-existent feature flag."""
        query = """
            query FeatureFlagQuery($key: String!) {
                featureFlag(key: $key) {
                    key
                    name
                }
            }
        """

        variables = {"key": "non-existent-flag"}

        with patch('dotmac.platform.api.graphql.resolvers.FeatureFlagResolver.get_feature_flag') as mock_get_flag:
            mock_get_flag.return_value = None

            result = await authenticated_graphql_client.execute_expecting_data(query, variables)

            assert "featureFlag" in result
            assert result["featureFlag"] is None

    @pytest.mark.asyncio
    async def test_evaluate_flags_query(self, authenticated_graphql_client):
        """Test evaluating feature flags."""
        query = """
            query EvaluateFlagsQuery($flags: [String!]!, $context: JSON) {
                evaluateFlags(flags: $flags, context: $context) {
                    flagKey
                    enabled
                    variant
                    reason
                    context
                }
            }
        """

        variables = {
            "flags": ["flag1", "flag2"],
            "context": {"user_tier": "premium", "region": "us-east-1"}
        }

        with patch('dotmac.platform.api.graphql.resolvers.FeatureFlagResolver.evaluate_flags') as mock_evaluate:
            mock_evaluations = [
                Mock(
                    flag_key="flag1",
                    enabled=True,
                    variant="control",
                    reason="user_in_whitelist",
                    context={"user_id": "test-user", "user_tier": "premium"}
                ),
                Mock(
                    flag_key="flag2",
                    enabled=False,
                    variant=None,
                    reason="flag_disabled",
                    context={"user_id": "test-user", "user_tier": "premium"}
                )
            ]
            mock_evaluate.return_value = mock_evaluations

            result = await authenticated_graphql_client.execute_expecting_data(query, variables)

            assert "evaluateFlags" in result
            evaluations = result["evaluateFlags"]
            assert len(evaluations) == 2

            eval1 = evaluations[0]
            assert eval1["flagKey"] == "flag1"
            assert eval1["enabled"] is True
            assert eval1["variant"] == "control"
            assert eval1["reason"] == "user_in_whitelist"

            eval2 = evaluations[1]
            assert eval2["flagKey"] == "flag2"
            assert eval2["enabled"] is False
            assert eval2["reason"] == "flag_disabled"

    @pytest.mark.asyncio
    async def test_upsert_feature_flag_mutation(self, authenticated_graphql_client):
        """Test creating/updating a feature flag."""
        mutation = """
            mutation UpsertFeatureFlagMutation($input: FeatureFlagInput!) {
                upsertFeatureFlag(input: $input) {
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
            }
        """

        variables = {
            "input": {
                "key": "new-flag",
                "name": "New Feature Flag",
                "description": "A newly created flag",
                "enabled": True,
                "strategy": "PERCENTAGE",
                "config": {"percentage": 25}
            }
        }

        with patch('dotmac.platform.api.graphql.resolvers.FeatureFlagResolver.upsert_feature_flag') as mock_upsert:
            mock_flag = Mock(
                key="new-flag",
                name="New Feature Flag",
                description="A newly created flag",
                enabled=True,
                strategy="PERCENTAGE",
                config={"percentage": 25},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                created_by="test-user-123"
            )
            mock_upsert.return_value = mock_flag

            result = await authenticated_graphql_client.execute_expecting_data(mutation, variables)

            assert "upsertFeatureFlag" in result
            flag_data = result["upsertFeatureFlag"]

            assert flag_data["key"] == "new-flag"
            assert flag_data["name"] == "New Feature Flag"
            assert flag_data["enabled"] is True
            assert flag_data["strategy"] == "PERCENTAGE"
            assert flag_data["config"]["percentage"] == 25

    @pytest.mark.asyncio
    async def test_delete_feature_flag_mutation(self, authenticated_graphql_client):
        """Test deleting a feature flag."""
        mutation = """
            mutation DeleteFeatureFlagMutation($key: String!) {
                deleteFeatureFlag(key: $key)
            }
        """

        variables = {"key": "flag-to-delete"}

        with patch('dotmac.platform.api.graphql.resolvers.FeatureFlagResolver.delete_feature_flag') as mock_delete:
            mock_delete.return_value = True

            result = await authenticated_graphql_client.execute_expecting_data(mutation, variables)

            assert "deleteFeatureFlag" in result
            assert result["deleteFeatureFlag"] is True

            mock_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_toggle_feature_flag_mutation(self, authenticated_graphql_client):
        """Test toggling a feature flag."""
        mutation = """
            mutation ToggleFeatureFlagMutation($key: String!, $enabled: Boolean!) {
                toggleFeatureFlag(key: $key, enabled: $enabled) {
                    key
                    name
                    enabled
                    updatedAt
                }
            }
        """

        variables = {"key": "flag-to-toggle", "enabled": False}

        with patch('dotmac.platform.api.graphql.resolvers.FeatureFlagResolver.toggle_feature_flag') as mock_toggle:
            mock_flag = Mock(
                key="flag-to-toggle",
                name="Toggleable Flag",
                enabled=False,
                strategy="ALL_OFF",
                config={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                created_by="admin"
            )
            mock_toggle.return_value = mock_flag

            result = await authenticated_graphql_client.execute_expecting_data(mutation, variables)

            assert "toggleFeatureFlag" in result
            flag_data = result["toggleFeatureFlag"]

            assert flag_data["key"] == "flag-to-toggle"
            assert flag_data["enabled"] is False

            mock_toggle.assert_called_once()

    @pytest.mark.asyncio
    async def test_feature_flags_pagination(self, authenticated_graphql_client, feature_flags_query):
        """Test feature flags pagination."""
        # First page
        variables = {"first": 2, "after": None}

        with patch('dotmac.platform.api.graphql.resolvers.FeatureFlagResolver.get_feature_flags') as mock_get_flags:
            mock_connection_page1 = Mock()
            mock_connection_page1.nodes = [Mock(key=f"flag-{i}") for i in range(2)]
            mock_connection_page1.page_info = Mock(
                has_next_page=True,
                has_previous_page=False,
                start_cursor="flag-0",
                end_cursor="flag-1",
                total_count=5
            )
            mock_get_flags.return_value = mock_connection_page1

            result = await authenticated_graphql_client.execute_expecting_data(
                feature_flags_query, variables
            )

            page_info = result["featureFlags"]["pageInfo"]
            assert page_info["hasNextPage"] is True
            assert page_info["hasPreviousPage"] is False
            assert page_info["totalCount"] == 5

        # Second page
        variables = {"first": 2, "after": "flag-1"}

        with patch('dotmac.platform.api.graphql.resolvers.FeatureFlagResolver.get_feature_flags') as mock_get_flags:
            mock_connection_page2 = Mock()
            mock_connection_page2.nodes = [Mock(key=f"flag-{i}") for i in range(2, 4)]
            mock_connection_page2.page_info = Mock(
                has_next_page=True,
                has_previous_page=True,
                start_cursor="flag-2",
                end_cursor="flag-3",
                total_count=5
            )
            mock_get_flags.return_value = mock_connection_page2

            result = await authenticated_graphql_client.execute_expecting_data(
                feature_flags_query, variables
            )

            page_info = result["featureFlags"]["pageInfo"]
            assert page_info["hasNextPage"] is True
            assert page_info["hasPreviousPage"] is True

    @pytest.mark.asyncio
    async def test_feature_flags_authentication_required(self, graphql_test_client, feature_flags_query):
        """Test that feature flags operations require authentication."""
        variables = {"first": 10}

        with patch('dotmac.platform.api.graphql.resolvers.FeatureFlagResolver.get_feature_flags') as mock_get_flags:
            from dotmac.platform.auth.exceptions import AuthError
            mock_get_flags.side_effect = AuthError("Authentication required")

            data = await graphql_test_client.execute_expecting_errors(feature_flags_query, variables)
            assert len(data["errors"]) > 0
            assert any("Authentication required" in error["message"] for error in data["errors"])

    @pytest.mark.asyncio
    async def test_feature_flag_service_error_handling(self, authenticated_graphql_client):
        """Test handling of feature flag service errors."""
        query = """
            query FeatureFlagQuery($key: String!) {
                featureFlag(key: $key) {
                    key
                    name
                }
            }
        """

        variables = {"key": "error-flag"}

        with patch('dotmac.platform.api.graphql.resolvers.FeatureFlagResolver.get_feature_flag') as mock_get_flag:
            mock_get_flag.side_effect = Exception("Feature flag service unavailable")

            data = await authenticated_graphql_client.execute_expecting_errors(query, variables)
            assert len(data["errors"]) > 0
            assert any("Feature flag service unavailable" in error["message"] for error in data["errors"])
"""
Tests for WhatsApp Business API plugin.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from dotmac.platform.plugins.builtin.whatsapp_plugin import WhatsAppProvider, register
from dotmac.platform.plugins.schema import FieldType, PluginType


class TestWhatsAppProvider:
    """Test WhatsApp provider plugin."""

    @pytest.fixture
    def provider(self):
        """Create a WhatsApp provider instance."""
        return WhatsAppProvider()

    def test_get_config_schema(self, provider):
        """Test getting configuration schema."""
        schema = provider.get_config_schema()

        assert schema.name == "WhatsApp Business"
        assert schema.type == PluginType.NOTIFICATION
        assert schema.version == "1.0.0"
        assert len(schema.fields) == 13

        # Check for required fields
        field_keys = [field.key for field in schema.fields]
        assert "phone_number" in field_keys
        assert "api_token" in field_keys
        assert "business_account_id" in field_keys

        # Check field types
        phone_field = next(f for f in schema.fields if f.key == "phone_number")
        assert phone_field.type == FieldType.PHONE
        assert phone_field.required is True

        api_field = next(f for f in schema.fields if f.key == "api_token")
        assert api_field.type == FieldType.SECRET
        assert api_field.is_secret is True

    def test_field_groups(self, provider):
        """Test that fields are properly grouped."""
        schema = provider.get_config_schema()

        groups = set()
        for field in schema.fields:
            if field.group:
                groups.add(field.group)

        expected_groups = {"Basic Configuration", "Environment", "Message Settings", "Webhooks", "Advanced"}
        assert groups == expected_groups

    @pytest.mark.asyncio
    async def test_configure_success(self, provider):
        """Test successful configuration."""
        config = {
            "phone_number": "+1234567890",
            "api_token": "test_token_123",
            "business_account_id": "123456",
            "sandbox_mode": True,
        }

        result = await provider.configure(config)

        assert result is True
        assert provider.configured is True
        assert provider.phone_number == "+1234567890"
        assert provider.api_token == "test_token_123"
        assert provider.business_account_id == "123456"
        assert provider.sandbox_mode is True

    @pytest.mark.asyncio
    async def test_configure_missing_required(self, provider):
        """Test configuration with missing required fields."""
        config = {
            "phone_number": "+1234567890",
            # Missing api_token and business_account_id
        }

        result = await provider.configure(config)

        assert result is False
        assert provider.configured is False

    @pytest.mark.asyncio
    async def test_configure_api_version(self, provider):
        """Test configuration with custom API version."""
        config = {
            "phone_number": "+1234567890",
            "api_token": "test_token",
            "business_account_id": "123456",
            "api_version": "v17.0",
        }

        result = await provider.configure(config)

        assert result is True
        assert "v17.0" in provider.base_url

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_send_notification_success(self, mock_client_class, provider):
        """Test successful notification sending."""
        # Configure provider
        await provider.configure({
            "phone_number": "+1234567890",
            "api_token": "test_token",
            "business_account_id": "123456",
        })

        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "messages": [{"id": "message_123"}]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        # Send notification
        result = await provider.send_notification(
            recipient="+9876543210",
            message="Test message",
        )

        assert result is True
        mock_client.post.assert_called_once()

        # Check the call arguments
        call_args = mock_client.post.call_args
        assert "/123456/messages" in call_args[0][0]
        assert call_args[1]["json"]["to"] == "+9876543210"
        assert call_args[1]["json"]["text"]["body"] == "Test message"

    @pytest.mark.asyncio
    async def test_send_notification_not_configured(self, provider):
        """Test sending notification when not configured."""
        with pytest.raises(RuntimeError) as exc_info:
            await provider.send_notification(
                recipient="+9876543210",
                message="Test message",
            )
        assert "not configured" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_send_notification_http_error(self, mock_client_class, provider):
        """Test notification sending with HTTP error."""
        # Configure provider
        await provider.configure({
            "phone_number": "+1234567890",
            "api_token": "test_token",
            "business_account_id": "123456",
        })

        # Mock HTTP error - use RequestError which is a subclass of HTTPError
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.RequestError("Connection failed"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        result = await provider.send_notification(
            recipient="+9876543210",
            message="Test message",
        )

        assert result is False

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_health_check_healthy(self, mock_client_class, provider):
        """Test health check when healthy."""
        # Configure provider
        await provider.configure({
            "phone_number": "+1234567890",
            "api_token": "test_token",
            "business_account_id": "123456",
        })

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.json.return_value = {"name": "Test Business"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        health = await provider.health_check()

        assert health.status == "healthy"
        assert health.details["api_accessible"] is True
        assert health.details["business_name"] == "Test Business"

    @pytest.mark.asyncio
    async def test_health_check_not_configured(self, provider):
        """Test health check when not configured."""
        health = await provider.health_check()

        assert health.status == "unhealthy"
        assert health.details["configured"] is False
        assert "not configured" in health.message.lower()

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_health_check_api_error(self, mock_client_class, provider):
        """Test health check with API error."""
        # Configure provider
        await provider.configure({
            "phone_number": "+1234567890",
            "api_token": "test_token",
            "business_account_id": "123456",
        })

        # Mock API error
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.RequestError("Connection timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        health = await provider.health_check()

        assert health.status == "unhealthy"
        assert health.details["api_accessible"] is False
        assert "Connection timeout" in health.details["error"]

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_test_connection_success(self, mock_client_class, provider):
        """Test successful connection test."""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "name": "Test Business",
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        config = {
            "api_token": "test_token",
            "business_account_id": "123456",
            "api_version": "v18.0",
        }

        result = await provider.test_connection(config)

        assert result.success is True
        assert "successful" in result.message.lower()
        assert result.details["business_name"] == "Test Business"
        assert result.details["api_version"] == "v18.0"

    @pytest.mark.asyncio
    async def test_test_connection_missing_token(self, provider):
        """Test connection test with missing API token."""
        config = {
            "business_account_id": "123456",
            # Missing api_token
        }

        result = await provider.test_connection(config)

        assert result.success is False
        assert "api token" in result.message.lower()
        assert result.details["error"] == "missing_api_token"

    @pytest.mark.asyncio
    async def test_test_connection_missing_account_id(self, provider):
        """Test connection test with missing business account ID."""
        config = {
            "api_token": "test_token",
            # Missing business_account_id
        }

        result = await provider.test_connection(config)

        assert result.success is False
        assert "business account" in result.message.lower()
        assert result.details["error"] == "missing_business_account_id"

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_test_connection_http_error(self, mock_client_class, provider):
        """Test connection test with HTTP error."""
        # Mock HTTP error response
        mock_request = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": {"message": "Invalid token"}}

        http_error = httpx.HTTPStatusError(
            "401 Unauthorized",
            request=mock_request,
            response=mock_response
        )

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=http_error)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        config = {
            "api_token": "invalid_token",
            "business_account_id": "123456",
        }

        result = await provider.test_connection(config)

        assert result.success is False
        assert "401" in result.message
        assert result.details["status_code"] == 401

    def test_register_function(self):
        """Test the register function returns a provider."""
        provider = register()
        assert isinstance(provider, WhatsAppProvider)

    def test_field_validation_rules(self, provider):
        """Test that fields have proper validation rules."""
        schema = provider.get_config_schema()

        # Check phone number validation
        phone_field = next(f for f in schema.fields if f.key == "phone_number")
        assert phone_field.pattern == r'^\+[1-9]\d{1,14}$'
        assert len(phone_field.validation_rules) > 0

        # Check API token has minimum length
        api_field = next(f for f in schema.fields if f.key == "api_token")
        assert api_field.min_length == 50

        # Check integer fields have min/max values
        retry_field = next(f for f in schema.fields if f.key == "message_retry_count")
        assert retry_field.min_value == 0
        assert retry_field.max_value == 5

    def test_select_field_options(self, provider):
        """Test that select fields have proper options."""
        schema = provider.get_config_schema()

        # Check API version options
        version_field = next(f for f in schema.fields if f.key == "api_version")
        assert version_field.type == FieldType.SELECT
        assert len(version_field.options) == 3
        option_values = [opt.value for opt in version_field.options]
        assert "v18.0" in option_values
        assert "v17.0" in option_values

    def test_plugin_metadata(self, provider):
        """Test plugin metadata."""
        schema = provider.get_config_schema()

        assert schema.author == "DotMac Platform"
        assert schema.homepage == "https://developers.facebook.com/docs/whatsapp"
        assert "httpx" in schema.dependencies
        assert "messaging" in schema.tags
        assert schema.supports_health_check is True
        assert schema.supports_test_connection is True
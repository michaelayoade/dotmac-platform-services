"""Tests for webhook service functionality."""

import json
import asyncio
from datetime import datetime, UTC
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

import pytest
import aiohttp

from src.dotmac.platform.communications.webhook_service import WebhookService


@pytest.fixture
def webhook_service():
    """Create webhook service instance for testing."""
    return WebhookService(redis_url="redis://localhost:6379/15")  # Use test database


@pytest.fixture
def sample_subscription():
    """Sample webhook subscription data."""
    return {
        "id": str(uuid4()),
        "user_id": "test_user_123",
        "name": "Test Webhook",
        "url": "https://example.com/webhook",
        "events": ["customer.created", "order.completed"],
        "description": "Test webhook subscription",
        "headers": {"Authorization": "Bearer token"},
        "is_active": True,
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
        "last_delivery_at": None,
        "total_deliveries": 0,
        "failed_deliveries": 0,
        "secret": "webhook_secret_123",
    }


class TestWebhookServiceBasic:
    """Test basic webhook service functionality."""

    @pytest.mark.asyncio
    async def test_create_subscription_memory_fallback(self, webhook_service, sample_subscription):
        """Test creating webhook subscription with memory fallback."""
        # Mock Redis to return None (force memory fallback)
        with patch.object(webhook_service, '_get_redis', return_value=None):
            success = await webhook_service.create_subscription(sample_subscription)

        assert success
        assert sample_subscription["id"] in webhook_service._memory_storage.get("subscriptions", {})

        # Verify user subscription list
        user_subscriptions = webhook_service._memory_storage.get("user_subscriptions", {})
        assert sample_subscription["user_id"] in user_subscriptions
        assert sample_subscription["id"] in user_subscriptions[sample_subscription["user_id"]]

    @pytest.mark.asyncio
    async def test_get_subscription_memory_fallback(self, webhook_service, sample_subscription):
        """Test getting webhook subscription with memory fallback."""
        # Setup memory storage
        webhook_service._memory_storage = {
            "subscriptions": {
                sample_subscription["id"]: sample_subscription
            }
        }

        with patch.object(webhook_service, '_get_redis', return_value=None):
            retrieved = await webhook_service.get_subscription(sample_subscription["id"])

        assert retrieved is not None
        assert retrieved["name"] == sample_subscription["name"]
        assert retrieved["url"] == sample_subscription["url"]

    @pytest.mark.asyncio
    async def test_get_subscription_not_found(self, webhook_service):
        """Test getting non-existent webhook subscription."""
        with patch.object(webhook_service, '_get_redis', return_value=None):
            retrieved = await webhook_service.get_subscription("nonexistent")

        assert retrieved is None

    @pytest.mark.asyncio
    async def test_list_user_subscriptions_memory_fallback(self, webhook_service):
        """Test listing user subscriptions with memory fallback."""
        # Setup test data
        user1_sub1 = {"id": "sub1", "user_id": "user1", "name": "Sub 1", "events": ["event1"]}
        user1_sub2 = {"id": "sub2", "user_id": "user1", "name": "Sub 2", "events": ["event2"]}
        user2_sub1 = {"id": "sub3", "user_id": "user2", "name": "Sub 3", "events": ["event1"]}

        webhook_service._memory_storage = {
            "subscriptions": {
                "sub1": user1_sub1,
                "sub2": user1_sub2,
                "sub3": user2_sub1,
            },
            "user_subscriptions": {
                "user1": {"sub1", "sub2"},
                "user2": {"sub3"},
            }
        }

        with patch.object(webhook_service, '_get_redis', return_value=None):
            result = await webhook_service.list_user_subscriptions("user1")

        assert len(result["subscriptions"]) == 2
        assert result["total"] == 2
        assert all(sub["user_id"] == "user1" for sub in result["subscriptions"])

    @pytest.mark.asyncio
    async def test_list_user_subscriptions_with_filters(self, webhook_service):
        """Test listing user subscriptions with event filter."""
        # Setup test data
        sub1 = {"id": "sub1", "user_id": "user1", "events": ["customer.created"], "is_active": True}
        sub2 = {"id": "sub2", "user_id": "user1", "events": ["order.completed"], "is_active": True}
        sub3 = {"id": "sub3", "user_id": "user1", "events": ["customer.created"], "is_active": False}

        webhook_service._memory_storage = {
            "subscriptions": {"sub1": sub1, "sub2": sub2, "sub3": sub3},
            "user_subscriptions": {"user1": {"sub1", "sub2", "sub3"}},
        }

        with patch.object(webhook_service, '_get_redis', return_value=None):
            # Test event filter
            result = await webhook_service.list_user_subscriptions(
                "user1",
                event_filter="customer.created"
            )

        assert len(result["subscriptions"]) == 2  # sub1 and sub3
        assert all("customer.created" in sub["events"] for sub in result["subscriptions"])

        with patch.object(webhook_service, '_get_redis', return_value=None):
            # Test active filter
            result = await webhook_service.list_user_subscriptions(
                "user1",
                active_only=True
            )

        assert len(result["subscriptions"]) == 2  # sub1 and sub2 (active only)
        assert all(sub["is_active"] for sub in result["subscriptions"])

    @pytest.mark.asyncio
    async def test_list_user_subscriptions_pagination(self, webhook_service):
        """Test pagination in user subscription listing."""
        # Create multiple subscriptions
        subscriptions = {}
        user_subs = set()

        for i in range(25):
            sub_id = f"sub_{i}"
            subscriptions[sub_id] = {
                "id": sub_id,
                "user_id": "user1",
                "name": f"Subscription {i}",
                "created_at": datetime.now(UTC).isoformat(),
                "is_active": True,
                "events": ["test.event"],
            }
            user_subs.add(sub_id)

        webhook_service._memory_storage = {
            "subscriptions": subscriptions,
            "user_subscriptions": {"user1": user_subs},
        }

        with patch.object(webhook_service, '_get_redis', return_value=None):
            # Test first page
            result = await webhook_service.list_user_subscriptions("user1", page=1, limit=10)

        assert len(result["subscriptions"]) == 10
        assert result["total"] == 25
        assert result["page"] == 1
        assert result["limit"] == 10

        with patch.object(webhook_service, '_get_redis', return_value=None):
            # Test last page
            result = await webhook_service.list_user_subscriptions("user1", page=3, limit=10)

        assert len(result["subscriptions"]) == 5  # 25 - 20 = 5 remaining
        assert result["total"] == 25

    @pytest.mark.asyncio
    async def test_update_subscription_memory_fallback(self, webhook_service, sample_subscription):
        """Test updating webhook subscription with memory fallback."""
        # Setup memory storage
        webhook_service._memory_storage = {
            "subscriptions": {
                sample_subscription["id"]: sample_subscription.copy()
            }
        }

        updates = {
            "name": "Updated Name",
            "is_active": False,
            "description": "Updated description",
        }

        with patch.object(webhook_service, '_get_redis', return_value=None):
            success = await webhook_service.update_subscription(sample_subscription["id"], updates)

        assert success

        updated_sub = webhook_service._memory_storage["subscriptions"][sample_subscription["id"]]
        assert updated_sub["name"] == "Updated Name"
        assert updated_sub["is_active"] == False
        assert updated_sub["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_update_subscription_not_found(self, webhook_service):
        """Test updating non-existent webhook subscription."""
        with patch.object(webhook_service, '_get_redis', return_value=None):
            success = await webhook_service.update_subscription("nonexistent", {"name": "New Name"})

        assert not success

    @pytest.mark.asyncio
    async def test_delete_subscription_memory_fallback(self, webhook_service, sample_subscription):
        """Test deleting webhook subscription with memory fallback."""
        # Setup memory storage
        webhook_service._memory_storage = {
            "subscriptions": {
                sample_subscription["id"]: sample_subscription.copy()
            },
            "user_subscriptions": {
                sample_subscription["user_id"]: {sample_subscription["id"]}
            },
            "deliveries": {
                sample_subscription["id"]: ["delivery1", "delivery2"]
            }
        }

        with patch.object(webhook_service, '_get_redis', return_value=None):
            success = await webhook_service.delete_subscription(sample_subscription["id"])

        assert success

        # Verify subscription was deleted
        assert sample_subscription["id"] not in webhook_service._memory_storage["subscriptions"]

        # Verify user subscription list was updated
        user_subs = webhook_service._memory_storage["user_subscriptions"][sample_subscription["user_id"]]
        assert sample_subscription["id"] not in user_subs

        # Verify deliveries were cleaned up
        assert sample_subscription["id"] not in webhook_service._memory_storage["deliveries"]

    @pytest.mark.asyncio
    async def test_delete_subscription_not_found(self, webhook_service):
        """Test deleting non-existent webhook subscription."""
        with patch.object(webhook_service, '_get_redis', return_value=None):
            success = await webhook_service.delete_subscription("nonexistent")

        assert not success


class TestWebhookDelivery:
    """Test webhook delivery functionality."""

    @pytest.mark.asyncio
    async def test_get_subscriptions_for_event(self, webhook_service):
        """Test getting subscriptions for specific event."""
        # Setup test subscriptions
        sub1 = {"id": "sub1", "events": ["customer.created", "order.completed"], "is_active": True}
        sub2 = {"id": "sub2", "events": ["order.completed"], "is_active": True}
        sub3 = {"id": "sub3", "events": ["customer.created"], "is_active": False}  # Inactive

        webhook_service._memory_storage = {
            "subscriptions": {"sub1": sub1, "sub2": sub2, "sub3": sub3}
        }

        with patch.object(webhook_service, '_get_redis', return_value=None):
            subscriptions = await webhook_service.get_subscriptions_for_event("customer.created")

        # Should only return active subscriptions for the event
        assert len(subscriptions) == 1  # Only sub1 (sub3 is inactive)
        assert subscriptions[0]["id"] == "sub1"

        with patch.object(webhook_service, '_get_redis', return_value=None):
            subscriptions = await webhook_service.get_subscriptions_for_event("order.completed")

        assert len(subscriptions) == 2  # sub1 and sub2
        subscription_ids = [sub["id"] for sub in subscriptions]
        assert "sub1" in subscription_ids
        assert "sub2" in subscription_ids

    def test_generate_signature(self, webhook_service):
        """Test webhook signature generation."""
        payload = '{"event": "test", "data": {"id": 123}}'
        secret = "test_secret_key"

        signature = webhook_service._generate_signature(payload, secret)

        assert signature.startswith("sha256=")
        assert len(signature) > 10

        # Same payload and secret should produce same signature
        signature2 = webhook_service._generate_signature(payload, secret)
        assert signature == signature2

        # Different payload should produce different signature
        different_payload = '{"event": "different"}'
        different_signature = webhook_service._generate_signature(different_payload, secret)
        assert signature != different_signature

        # Different secret should produce different signature
        different_secret_signature = webhook_service._generate_signature(payload, "different_secret")
        assert signature != different_secret_signature

    @pytest.mark.asyncio
    async def test_record_delivery_success(self, webhook_service):
        """Test recording successful webhook delivery."""
        with patch.object(webhook_service, '_get_redis', return_value=None):
            await webhook_service._record_delivery(
                subscription_id="sub123",
                delivery_id="delivery123",
                event_type="customer.created",
                status="success",
                response_status=200,
                response_body="OK"
            )

        # Verify delivery was recorded
        deliveries = webhook_service._memory_storage.get("deliveries", {}).get("sub123", [])
        assert len(deliveries) == 1

        delivery = deliveries[0]
        assert delivery["status"] == "success"
        assert delivery["response_status"] == 200
        assert delivery["event_type"] == "customer.created"

    @pytest.mark.asyncio
    async def test_record_delivery_failed_with_retry(self, webhook_service):
        """Test recording failed webhook delivery with retry scheduling."""
        with patch.object(webhook_service, '_get_redis', return_value=None):
            await webhook_service._record_delivery(
                subscription_id="sub123",
                delivery_id="delivery123",
                event_type="customer.created",
                status="failed",
                error_message="Connection timeout",
                retry_count=1
            )

        deliveries = webhook_service._memory_storage.get("deliveries", {}).get("sub123", [])
        assert len(deliveries) == 1

        delivery = deliveries[0]
        assert delivery["status"] == "failed"
        assert delivery["error_message"] == "Connection timeout"
        assert delivery["retry_count"] == 1
        assert delivery["next_retry_at"] is not None  # Should schedule retry

    @pytest.mark.asyncio
    async def test_record_delivery_max_retries(self, webhook_service):
        """Test recording failed delivery that exceeds max retries."""
        with patch.object(webhook_service, '_get_redis', return_value=None):
            await webhook_service._record_delivery(
                subscription_id="sub123",
                delivery_id="delivery123",
                event_type="customer.created",
                status="failed",
                error_message="Max retries exceeded",
                retry_count=6  # Over the limit of 5
            )

        deliveries = webhook_service._memory_storage.get("deliveries", {}).get("sub123", [])
        delivery = deliveries[0]
        assert delivery["next_retry_at"] is None  # Should not schedule retry

    @pytest.mark.asyncio
    async def test_list_deliveries_memory_fallback(self, webhook_service):
        """Test listing webhook deliveries with memory fallback."""
        # Setup test deliveries
        deliveries = [
            {
                "id": "delivery1",
                "status": "success",
                "event_type": "customer.created",
                "delivered_at": datetime.now(UTC).isoformat(),
            },
            {
                "id": "delivery2",
                "status": "failed",
                "event_type": "order.completed",
                "delivered_at": datetime.now(UTC).isoformat(),
            }
        ]

        webhook_service._memory_storage = {
            "deliveries": {"sub123": deliveries}
        }

        with patch.object(webhook_service, '_get_redis', return_value=None):
            result = await webhook_service.list_deliveries("sub123")

        assert len(result["deliveries"]) == 2
        assert result["total"] == 2

        # Test status filter
        with patch.object(webhook_service, '_get_redis', return_value=None):
            result = await webhook_service.list_deliveries("sub123", status_filter="failed")

        assert len(result["deliveries"]) == 1
        assert result["deliveries"][0]["status"] == "failed"

    @pytest.mark.asyncio
    async def test_trigger_event(self, webhook_service):
        """Test triggering webhook deliveries for an event."""
        # Setup test subscriptions
        sub1 = {"id": "sub1", "events": ["customer.created"], "is_active": True}
        sub2 = {"id": "sub2", "events": ["customer.created"], "is_active": True}
        sub3 = {"id": "sub3", "events": ["order.completed"], "is_active": True}

        webhook_service._memory_storage = {
            "subscriptions": {"sub1": sub1, "sub2": sub2, "sub3": sub3}
        }

        with patch.object(webhook_service, '_get_redis', return_value=None), \
             patch.object(webhook_service, 'deliver_webhook', return_value={"success": True}) as mock_deliver:

            count = await webhook_service.trigger_event("customer.created", {"customer_id": 123})

        assert count == 2  # Should deliver to sub1 and sub2
        assert mock_deliver.call_count == 2

        # Verify correct subscriptions were called
        call_args = [call[1]["subscription_id"] for call in mock_deliver.call_args_list]
        assert "sub1" in call_args
        assert "sub2" in call_args
        assert "sub3" not in call_args


class TestWebhookHTTPDelivery:
    """Test HTTP delivery functionality."""

    @pytest.mark.asyncio
    async def test_deliver_webhook_success(self, webhook_service):
        """Test successful webhook HTTP delivery."""
        subscription = {
            "id": "sub123",
            "url": "https://example.com/webhook",
            "is_active": True,
            "headers": {"Authorization": "Bearer token"},
            "secret": "webhook_secret",
            "total_deliveries": 0,
        }

        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="OK")

        mock_session = MagicMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch.object(webhook_service, 'get_subscription', return_value=subscription), \
             patch.object(webhook_service, 'update_subscription'), \
             patch.object(webhook_service, '_record_delivery'), \
             patch('aiohttp.ClientSession', return_value=mock_session):

            result = await webhook_service.deliver_webhook(
                subscription_id="sub123",
                event_type="customer.created",
                payload={"customer_id": 123}
            )

        assert result["success"] == True
        assert result["status_code"] == 200
        assert "delivery_time_ms" in result

    @pytest.mark.asyncio
    async def test_deliver_webhook_http_error(self, webhook_service):
        """Test webhook delivery with HTTP error response."""
        subscription = {
            "id": "sub123",
            "url": "https://example.com/webhook",
            "is_active": True,
            "headers": {},
            "failed_deliveries": 0,
        }

        # Mock HTTP error response
        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")

        mock_session = MagicMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch.object(webhook_service, 'get_subscription', return_value=subscription), \
             patch.object(webhook_service, 'update_subscription'), \
             patch.object(webhook_service, '_record_delivery'), \
             patch('aiohttp.ClientSession', return_value=mock_session):

            result = await webhook_service.deliver_webhook(
                subscription_id="sub123",
                event_type="customer.created",
                payload={"customer_id": 123}
            )

        assert result["success"] == False
        assert result["status_code"] == 500
        assert result["error_message"] == "HTTP 500"

    @pytest.mark.asyncio
    async def test_deliver_webhook_timeout(self, webhook_service):
        """Test webhook delivery with timeout."""
        subscription = {
            "id": "sub123",
            "url": "https://example.com/webhook",
            "is_active": True,
            "headers": {},
        }

        with patch.object(webhook_service, 'get_subscription', return_value=subscription), \
             patch.object(webhook_service, '_record_delivery'), \
             patch('aiohttp.ClientSession') as mock_session_class:

            # Mock timeout error
            mock_session = mock_session_class.return_value
            mock_session.post.side_effect = asyncio.TimeoutError()

            result = await webhook_service.deliver_webhook(
                subscription_id="sub123",
                event_type="customer.created",
                payload={"customer_id": 123}
            )

        assert result["success"] == False
        assert result["error_message"] == "Request timeout"
        assert "delivery_time_ms" in result

    @pytest.mark.asyncio
    async def test_deliver_webhook_inactive_subscription(self, webhook_service):
        """Test webhook delivery to inactive subscription."""
        subscription = {
            "id": "sub123",
            "url": "https://example.com/webhook",
            "is_active": False,  # Inactive
            "headers": {},
        }

        with patch.object(webhook_service, 'get_subscription', return_value=subscription):
            result = await webhook_service.deliver_webhook(
                subscription_id="sub123",
                event_type="customer.created",
                payload={"customer_id": 123}
            )

        assert result["success"] == False
        assert result["error"] == "Subscription is inactive"

    @pytest.mark.asyncio
    async def test_deliver_webhook_not_found(self, webhook_service):
        """Test webhook delivery to non-existent subscription."""
        with patch.object(webhook_service, 'get_subscription', return_value=None):
            result = await webhook_service.deliver_webhook(
                subscription_id="nonexistent",
                event_type="customer.created",
                payload={"customer_id": 123}
            )

        assert result["success"] == False
        assert result["error"] == "Subscription not found"

    @pytest.mark.asyncio
    async def test_test_delivery(self, webhook_service):
        """Test webhook test delivery functionality."""
        subscription = {
            "id": "sub123",
            "url": "https://example.com/webhook",
            "headers": {"Custom": "Header"},
            "secret": "test_secret",
        }

        # Mock successful HTTP response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="Test OK")

        mock_session = MagicMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch.object(webhook_service, 'get_subscription', return_value=subscription), \
             patch('aiohttp.ClientSession', return_value=mock_session):

            result = await webhook_service.test_delivery(
                subscription_id="sub123",
                event_type="customer.created",
                payload={"test": True}
            )

        assert result["success"] == True
        assert result["status_code"] == 200
        assert result["response_body"] == "Test OK"
        assert "delivery_time_ms" in result

    @pytest.mark.asyncio
    async def test_retry_delivery(self, webhook_service):
        """Test webhook delivery retry functionality."""
        # This is a placeholder implementation
        result = await webhook_service.retry_delivery("delivery_123")
        assert result == True  # Current implementation just returns True


class TestWebhookServiceEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_create_subscription_redis_error(self, webhook_service, sample_subscription):
        """Test creating subscription when Redis operations fail."""
        mock_redis = MagicMock()
        mock_redis.set.side_effect = Exception("Redis connection error")

        with patch.object(webhook_service, '_get_redis', return_value=mock_redis):
            success = await webhook_service.create_subscription(sample_subscription)

        # Should fall back gracefully but return False due to error
        assert not success

    @pytest.mark.asyncio
    async def test_list_subscriptions_empty_result(self, webhook_service):
        """Test listing subscriptions when none exist."""
        with patch.object(webhook_service, '_get_redis', return_value=None):
            result = await webhook_service.list_user_subscriptions("nonexistent_user")

        assert result["subscriptions"] == []
        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_webhook_delivery_with_custom_headers(self, webhook_service):
        """Test webhook delivery includes custom headers."""
        subscription = {
            "id": "sub123",
            "url": "https://example.com/webhook",
            "is_active": True,
            "headers": {
                "Authorization": "Bearer secret_token",
                "X-Custom-Header": "custom_value",
            },
            "secret": "webhook_secret",
            "total_deliveries": 0,
        }

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="OK")

        mock_session = MagicMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch.object(webhook_service, 'get_subscription', return_value=subscription), \
             patch.object(webhook_service, 'update_subscription'), \
             patch.object(webhook_service, '_record_delivery'), \
             patch('aiohttp.ClientSession', return_value=mock_session) as mock_session_class:

            await webhook_service.deliver_webhook(
                subscription_id="sub123",
                event_type="customer.created",
                payload={"customer_id": 123}
            )

        # Verify custom headers were included
        mock_session.post.assert_called_once()
        call_kwargs = mock_session.post.call_args[1]
        headers = call_kwargs["headers"]

        assert headers["Authorization"] == "Bearer secret_token"
        assert headers["X-Custom-Header"] == "custom_value"
        assert headers["Content-Type"] == "application/json"
        assert headers["User-Agent"] == "DotMac-Webhooks/1.0"
        assert "X-Webhook-Signature" in headers  # Should include signature

    @pytest.mark.asyncio
    async def test_webhook_payload_structure(self, webhook_service):
        """Test webhook payload has correct structure."""
        subscription = {
            "id": "sub123",
            "url": "https://example.com/webhook",
            "is_active": True,
            "headers": {},
            "total_deliveries": 0,
        }

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="OK")

        mock_session = MagicMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch.object(webhook_service, 'get_subscription', return_value=subscription), \
             patch.object(webhook_service, 'update_subscription'), \
             patch.object(webhook_service, '_record_delivery'), \
             patch('aiohttp.ClientSession', return_value=mock_session):

            await webhook_service.deliver_webhook(
                subscription_id="sub123",
                event_type="customer.created",
                payload={"customer_id": 123, "name": "Test Customer"}
            )

        # Verify payload structure
        mock_session.post.assert_called_once()
        call_kwargs = mock_session.post.call_args[1]
        payload_str = call_kwargs["data"]
        payload = json.loads(payload_str)

        assert "id" in payload
        assert payload["event"] == "customer.created"
        assert "created_at" in payload
        assert "data" in payload
        assert payload["data"]["customer_id"] == 123
        assert payload["data"]["name"] == "Test Customer"

    def test_serialization_methods(self, webhook_service):
        """Test JSON serialization/deserialization methods."""
        test_data = {
            "id": "test123",
            "name": "Test Object",
            "timestamp": datetime.now(UTC).isoformat(),
            "nested": {"key": "value"},
        }

        # Test serialization
        serialized = webhook_service._serialize(test_data)
        assert isinstance(serialized, str)

        # Test deserialization
        deserialized = webhook_service._deserialize(serialized)
        assert deserialized == test_data
        assert deserialized["name"] == "Test Object"

    @pytest.mark.asyncio
    async def test_memory_storage_limits(self, webhook_service):
        """Test that memory storage respects delivery limits."""
        # Create many deliveries to test limit
        webhook_service._memory_storage = {"deliveries": {"sub123": []}}

        with patch.object(webhook_service, '_get_redis', return_value=None):
            # Record 150 deliveries (more than limit of 100)
            for i in range(150):
                await webhook_service._record_delivery(
                    subscription_id="sub123",
                    delivery_id=f"delivery_{i}",
                    event_type="test.event",
                    status="success"
                )

        deliveries = webhook_service._memory_storage["deliveries"]["sub123"]
        assert len(deliveries) == 100  # Should be limited to 100
        # First delivery should be the most recent (delivery_149)
        assert deliveries[0]["id"] == "delivery_149"
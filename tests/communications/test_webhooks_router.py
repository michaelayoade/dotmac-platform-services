"""Tests for webhook subscription management endpoints."""

import json
from datetime import datetime, UTC
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.dotmac.platform.auth.core import UserInfo


@pytest.fixture
def mock_current_user():
    """Mock current user for webhook tests."""
    return UserInfo(
        user_id="test_user_123",
        username="testuser",
        roles=["user"],
        permissions=["webhooks:manage"],
    )


@pytest.fixture
def mock_webhook_service():
    """Mock webhook service."""
    with patch("src.dotmac.platform.communications.webhooks_router.webhook_service") as mock_service:
        yield mock_service


@pytest.fixture
def sample_webhook_subscription():
    """Sample webhook subscription data."""
    return {
        "id": "webhook_123",
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


class TestWebhookEndpoints:
    """Test webhook subscription management endpoints."""

    @pytest.mark.asyncio
    async def test_create_webhook_subscription_success(
        self, async_client: AsyncClient, mock_current_user, mock_webhook_service
    ):
        """Test successful webhook subscription creation."""
        # Arrange
        mock_webhook_service.create_subscription = AsyncMock(return_value=True)

        request_data = {
            "url": "https://example.com/webhook",
            "events": ["customer.created", "order.completed"],
            "name": "Test Webhook",
            "description": "Test webhook description",
            "is_active": True,
        }

        with patch(
            "src.dotmac.platform.communications.webhooks_router.get_current_user",
            return_value=mock_current_user,
        ):
            # Act
            response = await async_client.post("/api/v1/webhooks", json=request_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Webhook"
        assert data["url"] == "https://example.com/webhook"
        assert data["events"] == ["customer.created", "order.completed"]
        assert data["description"] == "Test webhook description"
        assert data["is_active"] == True
        assert data["has_secret"] == True
        assert "id" in data

        # Verify service was called
        mock_webhook_service.create_subscription.assert_called_once()
        call_args = mock_webhook_service.create_subscription.call_args[0][0]
        assert call_args["name"] == "Test Webhook"
        assert call_args["url"] == "https://example.com/webhook"
        assert call_args["user_id"] == "test_user_123"

    @pytest.mark.asyncio
    async def test_create_webhook_subscription_validation_error(
        self, async_client: AsyncClient, mock_current_user
    ):
        """Test webhook subscription creation with validation errors."""
        with patch(
            "src.dotmac.platform.communications.webhooks_router.get_current_user",
            return_value=mock_current_user,
        ):
            # Missing required fields
            response = await async_client.post("/api/v1/webhooks", json={
                "events": ["customer.created"],
                # Missing url and name
            })

        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("url" in error["loc"] for error in error_detail)
        assert any("name" in error["loc"] for error in error_detail)

    @pytest.mark.asyncio
    async def test_create_webhook_subscription_invalid_url(
        self, async_client: AsyncClient, mock_current_user
    ):
        """Test webhook subscription creation with invalid URL."""
        with patch(
            "src.dotmac.platform.communications.webhooks_router.get_current_user",
            return_value=mock_current_user,
        ):
            response = await async_client.post("/api/v1/webhooks", json={
                "url": "not-a-valid-url",
                "events": ["customer.created"],
                "name": "Test Webhook",
            })

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_webhook_subscriptions_success(
        self, async_client: AsyncClient, mock_current_user, mock_webhook_service, sample_webhook_subscription
    ):
        """Test successful webhook subscription listing."""
        # Arrange
        mock_webhook_service.list_user_subscriptions = AsyncMock(return_value={
            "subscriptions": [sample_webhook_subscription],
            "total": 1,
            "page": 1,
            "limit": 50,
        })

        with patch(
            "src.dotmac.platform.communications.webhooks_router.get_current_user",
            return_value=mock_current_user,
        ):
            # Act
            response = await async_client.get("/api/v1/webhooks")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["subscriptions"]) == 1
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["limit"] == 50

        subscription = data["subscriptions"][0]
        assert subscription["name"] == "Test Webhook"
        assert subscription["url"] == "https://example.com/webhook"
        assert subscription["has_secret"] == True
        assert "secret" not in subscription  # Should not expose secret

        # Verify service was called
        mock_webhook_service.list_user_subscriptions.assert_called_once_with(
            user_id="test_user_123",
            event_filter=None,
            active_only=False,
            page=1,
            limit=50,
        )

    @pytest.mark.asyncio
    async def test_list_webhook_subscriptions_with_filters(
        self, async_client: AsyncClient, mock_current_user, mock_webhook_service
    ):
        """Test webhook subscription listing with filters."""
        mock_webhook_service.list_user_subscriptions = AsyncMock(return_value={
            "subscriptions": [],
            "total": 0,
        })

        with patch(
            "src.dotmac.platform.communications.webhooks_router.get_current_user",
            return_value=mock_current_user,
        ):
            response = await async_client.get(
                "/api/v1/webhooks?page=2&limit=10&event_filter=customer.created&active_only=true"
            )

        assert response.status_code == 200
        mock_webhook_service.list_user_subscriptions.assert_called_once_with(
            user_id="test_user_123",
            event_filter="customer.created",
            active_only=True,
            page=2,
            limit=10,
        )

    @pytest.mark.asyncio
    async def test_get_webhook_subscription_success(
        self, async_client: AsyncClient, mock_current_user, mock_webhook_service, sample_webhook_subscription
    ):
        """Test successful webhook subscription retrieval."""
        # Arrange
        mock_webhook_service.get_subscription = AsyncMock(return_value=sample_webhook_subscription)

        with patch(
            "src.dotmac.platform.communications.webhooks_router.get_current_user",
            return_value=mock_current_user,
        ):
            # Act
            response = await async_client.get("/api/v1/webhooks/webhook_123")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Webhook"
        assert data["url"] == "https://example.com/webhook"
        assert data["has_secret"] == True

        mock_webhook_service.get_subscription.assert_called_once_with("webhook_123")

    @pytest.mark.asyncio
    async def test_get_webhook_subscription_not_found(
        self, async_client: AsyncClient, mock_current_user, mock_webhook_service
    ):
        """Test webhook subscription retrieval when subscription doesn't exist."""
        mock_webhook_service.get_subscription = AsyncMock(return_value=None)

        with patch(
            "src.dotmac.platform.communications.webhooks_router.get_current_user",
            return_value=mock_current_user,
        ):
            response = await async_client.get("/api/v1/webhooks/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_webhook_subscription_wrong_user(
        self, async_client: AsyncClient, mock_current_user, mock_webhook_service
    ):
        """Test webhook subscription retrieval with wrong user."""
        # Subscription belongs to different user
        wrong_user_subscription = {
            **sample_webhook_subscription,
            "user_id": "other_user",
        }
        mock_webhook_service.get_subscription = AsyncMock(return_value=wrong_user_subscription)

        with patch(
            "src.dotmac.platform.communications.webhooks_router.get_current_user",
            return_value=mock_current_user,
        ):
            response = await async_client.get("/api/v1/webhooks/webhook_123")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_webhook_subscription_success(
        self, async_client: AsyncClient, mock_current_user, mock_webhook_service, sample_webhook_subscription
    ):
        """Test successful webhook subscription update."""
        # Arrange
        updated_subscription = {
            **sample_webhook_subscription,
            "name": "Updated Webhook Name",
            "is_active": False,
        }

        mock_webhook_service.get_subscription = AsyncMock(return_value=sample_webhook_subscription)
        mock_webhook_service.update_subscription = AsyncMock(return_value=True)
        mock_webhook_service.get_subscription = AsyncMock(side_effect=[
            sample_webhook_subscription,  # First call for authorization check
            updated_subscription,  # Second call for getting updated data
        ])

        update_data = {
            "name": "Updated Webhook Name",
            "is_active": False,
        }

        with patch(
            "src.dotmac.platform.communications.webhooks_router.get_current_user",
            return_value=mock_current_user,
        ):
            # Act
            response = await async_client.patch("/api/v1/webhooks/webhook_123", json=update_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Webhook Name"
        assert data["is_active"] == False

        # Verify service was called
        mock_webhook_service.update_subscription.assert_called_once()
        call_args = mock_webhook_service.update_subscription.call_args[0]
        assert call_args[0] == "webhook_123"  # subscription_id
        updates = call_args[1]
        assert "name" in updates
        assert "is_active" in updates
        assert "updated_at" in updates

    @pytest.mark.asyncio
    async def test_update_webhook_subscription_partial(
        self, async_client: AsyncClient, mock_current_user, mock_webhook_service, sample_webhook_subscription
    ):
        """Test partial webhook subscription update."""
        updated_subscription = {**sample_webhook_subscription, "is_active": False}

        mock_webhook_service.get_subscription = AsyncMock(side_effect=[
            sample_webhook_subscription,
            updated_subscription,
        ])
        mock_webhook_service.update_subscription = AsyncMock(return_value=True)

        with patch(
            "src.dotmac.platform.communications.webhooks_router.get_current_user",
            return_value=mock_current_user,
        ):
            response = await async_client.patch("/api/v1/webhooks/webhook_123", json={
                "is_active": False
            })

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == False

        # Should only update the specified field
        mock_webhook_service.update_subscription.assert_called_once()
        call_args = mock_webhook_service.update_subscription.call_args[0]
        updates = call_args[1]
        assert "is_active" in updates
        assert updates["is_active"] == False
        assert "updated_at" in updates

    @pytest.mark.asyncio
    async def test_delete_webhook_subscription_success(
        self, async_client: AsyncClient, mock_current_user, mock_webhook_service, sample_webhook_subscription
    ):
        """Test successful webhook subscription deletion."""
        # Arrange
        mock_webhook_service.get_subscription = AsyncMock(return_value=sample_webhook_subscription)
        mock_webhook_service.delete_subscription = AsyncMock(return_value=True)

        with patch(
            "src.dotmac.platform.communications.webhooks_router.get_current_user",
            return_value=mock_current_user,
        ):
            # Act
            response = await async_client.delete("/api/v1/webhooks/webhook_123")

        # Assert
        assert response.status_code == 204

        mock_webhook_service.delete_subscription.assert_called_once_with("webhook_123")

    @pytest.mark.asyncio
    async def test_delete_webhook_subscription_not_found(
        self, async_client: AsyncClient, mock_current_user, mock_webhook_service
    ):
        """Test webhook subscription deletion when subscription doesn't exist."""
        mock_webhook_service.get_subscription = AsyncMock(return_value=None)

        with patch(
            "src.dotmac.platform.communications.webhooks_router.get_current_user",
            return_value=mock_current_user,
        ):
            response = await async_client.delete("/api/v1/webhooks/nonexistent")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_webhook_deliveries_success(
        self, async_client: AsyncClient, mock_current_user, mock_webhook_service, sample_webhook_subscription
    ):
        """Test successful webhook delivery listing."""
        # Arrange
        mock_delivery = {
            "id": "delivery_123",
            "subscription_id": "webhook_123",
            "event_type": "customer.created",
            "status": "success",
            "response_status": 200,
            "delivered_at": datetime.now(UTC).isoformat(),
            "retry_count": 0,
        }

        mock_webhook_service.get_subscription = AsyncMock(return_value=sample_webhook_subscription)
        mock_webhook_service.list_deliveries = AsyncMock(return_value={
            "deliveries": [mock_delivery],
            "total": 1,
            "page": 1,
            "limit": 50,
        })

        with patch(
            "src.dotmac.platform.communications.webhooks_router.get_current_user",
            return_value=mock_current_user,
        ):
            # Act
            response = await async_client.get("/api/v1/webhooks/webhook_123/deliveries")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["deliveries"]) == 1
        assert data["total"] == 1

        delivery = data["deliveries"][0]
        assert delivery["event_type"] == "customer.created"
        assert delivery["status"] == "success"
        assert delivery["response_status"] == 200

        mock_webhook_service.list_deliveries.assert_called_once_with(
            subscription_id="webhook_123",
            status_filter=None,
            page=1,
            limit=50,
        )

    @pytest.mark.asyncio
    async def test_list_webhook_deliveries_with_filter(
        self, async_client: AsyncClient, mock_current_user, mock_webhook_service, sample_webhook_subscription
    ):
        """Test webhook delivery listing with status filter."""
        mock_webhook_service.get_subscription = AsyncMock(return_value=sample_webhook_subscription)
        mock_webhook_service.list_deliveries = AsyncMock(return_value={
            "deliveries": [],
            "total": 0,
            "page": 1,
            "limit": 50,
        })

        with patch(
            "src.dotmac.platform.communications.webhooks_router.get_current_user",
            return_value=mock_current_user,
        ):
            response = await async_client.get(
                "/api/v1/webhooks/webhook_123/deliveries?status_filter=failed"
            )

        assert response.status_code == 200
        mock_webhook_service.list_deliveries.assert_called_once_with(
            subscription_id="webhook_123",
            status_filter="failed",
            page=1,
            limit=50,
        )

    @pytest.mark.asyncio
    async def test_test_webhook_subscription_success(
        self, async_client: AsyncClient, mock_current_user, mock_webhook_service, sample_webhook_subscription
    ):
        """Test successful webhook subscription test."""
        # Arrange
        mock_webhook_service.get_subscription = AsyncMock(return_value=sample_webhook_subscription)
        mock_webhook_service.test_delivery = AsyncMock(return_value={
            "success": True,
            "status_code": 200,
            "response_body": "OK",
            "delivery_time_ms": 150,
        })

        test_request = {
            "event_type": "customer.created",
            "payload": {"test": True},
        }

        with patch(
            "src.dotmac.platform.communications.webhooks_router.get_current_user",
            return_value=mock_current_user,
        ):
            # Act
            response = await async_client.post("/api/v1/webhooks/webhook_123/test", json=test_request)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["status_code"] == 200
        assert data["delivery_time_ms"] == 150

        mock_webhook_service.test_delivery.assert_called_once()

    @pytest.mark.asyncio
    async def test_retry_webhook_delivery_success(
        self, async_client: AsyncClient, mock_current_user, mock_webhook_service, sample_webhook_subscription
    ):
        """Test successful webhook delivery retry."""
        # Arrange
        mock_webhook_service.get_subscription = AsyncMock(return_value=sample_webhook_subscription)

        with patch(
            "src.dotmac.platform.communications.webhooks_router.get_current_user",
            return_value=mock_current_user,
        ):
            # Act
            response = await async_client.post("/api/v1/webhooks/webhook_123/retry/delivery_123")

        # Assert
        assert response.status_code == 202
        data = response.json()
        assert data["message"] == "Delivery retry queued"

    @pytest.mark.asyncio
    async def test_get_available_events(self, async_client: AsyncClient, mock_current_user):
        """Test getting available webhook events."""
        with patch(
            "src.dotmac.platform.communications.webhooks_router.get_current_user",
            return_value=mock_current_user,
        ):
            response = await async_client.get("/api/v1/webhooks/events/available")

        assert response.status_code == 200
        data = response.json()
        assert "events" in data

        # Verify some expected events
        events = data["events"]
        assert "customer.created" in events
        assert "order.completed" in events
        assert "payment.success" in events

        # Verify event details
        customer_created = events["customer.created"]
        assert "name" in customer_created
        assert "description" in customer_created

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, async_client: AsyncClient):
        """Test that webhook endpoints require authentication."""
        # Test without authentication
        response = await async_client.get("/api/v1/webhooks")
        assert response.status_code == 401

        response = await async_client.post("/api/v1/webhooks", json={
            "url": "https://example.com/webhook",
            "events": ["customer.created"],
            "name": "Test Webhook",
        })
        assert response.status_code == 401

        response = await async_client.delete("/api/v1/webhooks/webhook_123")
        assert response.status_code == 401


class TestWebhookServiceIntegration:
    """Integration tests for webhook service functionality."""

    @pytest.mark.asyncio
    async def test_webhook_subscription_lifecycle(self, sample_webhook_subscription):
        """Test complete webhook subscription lifecycle."""
        from src.dotmac.platform.communications.webhook_service import WebhookService

        # Test with memory fallback
        service = WebhookService()

        # Create subscription
        success = await service.create_subscription(sample_webhook_subscription)
        assert success

        # Get subscription
        retrieved = await service.get_subscription("webhook_123")
        assert retrieved is not None
        assert retrieved["name"] == "Test Webhook"

        # List subscriptions
        subscriptions = await service.list_user_subscriptions("test_user_123")
        assert len(subscriptions["subscriptions"]) == 1

        # Update subscription
        success = await service.update_subscription("webhook_123", {"name": "Updated Name"})
        assert success

        # Verify update
        updated = await service.get_subscription("webhook_123")
        assert updated["name"] == "Updated Name"

        # Delete subscription
        success = await service.delete_subscription("webhook_123")
        assert success

        # Verify deletion
        deleted = await service.get_subscription("webhook_123")
        assert deleted is None

    @pytest.mark.asyncio
    async def test_webhook_delivery_recording(self):
        """Test webhook delivery recording."""
        from src.dotmac.platform.communications.webhook_service import WebhookService

        service = WebhookService()

        # Record successful delivery
        await service._record_delivery(
            subscription_id="webhook_123",
            delivery_id="delivery_123",
            event_type="customer.created",
            status="success",
            response_status=200,
            response_body="OK"
        )

        # List deliveries
        deliveries = await service.list_deliveries("webhook_123")
        assert len(deliveries["deliveries"]) == 1

        delivery = deliveries["deliveries"][0]
        assert delivery["status"] == "success"
        assert delivery["response_status"] == 200

    @pytest.mark.asyncio
    async def test_webhook_signature_generation(self):
        """Test webhook signature generation."""
        from src.dotmac.platform.communications.webhook_service import WebhookService

        service = WebhookService()

        payload = '{"test": "data"}'
        secret = "test_secret"

        signature = service._generate_signature(payload, secret)

        assert signature.startswith("sha256=")
        assert len(signature) > 10

        # Same payload and secret should generate same signature
        signature2 = service._generate_signature(payload, secret)
        assert signature == signature2

        # Different secret should generate different signature
        different_signature = service._generate_signature(payload, "different_secret")
        assert signature != different_signature

    def test_webhook_event_enum_values(self):
        """Test that webhook event enum has expected values."""
        from src.dotmac.platform.communications.webhooks_router import WebhookEvent

        # Test that expected events exist
        assert hasattr(WebhookEvent, 'CUSTOMER_CREATED')
        assert hasattr(WebhookEvent, 'ORDER_COMPLETED')
        assert hasattr(WebhookEvent, 'PAYMENT_SUCCESS')

        # Test enum values
        assert WebhookEvent.CUSTOMER_CREATED.value == "customer.created"
        assert WebhookEvent.ORDER_COMPLETED.value == "order.completed"
        assert WebhookEvent.PAYMENT_SUCCESS.value == "payment.success"
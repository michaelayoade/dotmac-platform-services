"""
Comprehensive tests for WebhookService.

Tests all webhook functionality including:
- Subscription management (CRUD)
- Event delivery
- Retry mechanisms
- Rate limiting
- Security features (HMAC)
- Redis/memory storage backends
"""

import json
import hmac
import hashlib
import pytest
from datetime import datetime, UTC, timedelta
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from uuid import uuid4

import aiohttp

from dotmac.platform.communications.webhook_service import WebhookService


class TestWebhookServiceInitialization:
    """Test WebhookService initialization and configuration."""

    def test_webhook_service_init_default(self):
        """Test webhook service initialization with defaults."""
        service = WebhookService()
        assert service.redis_url is not None
        assert service._redis is None
        assert service._memory_storage == {}

    def test_webhook_service_init_custom_redis(self):
        """Test webhook service initialization with custom Redis URL."""
        redis_url = "redis://custom:6379/1"
        service = WebhookService(redis_url=redis_url)
        assert service.redis_url == redis_url
        assert service._redis is None
        assert service._memory_storage == {}


class TestWebhookServiceRedisOperations:
    """Test Redis operations with mocking."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        redis_mock = AsyncMock()
        redis_mock.set = AsyncMock()
        redis_mock.get = AsyncMock()
        redis_mock.delete = AsyncMock()
        redis_mock.scan_iter = AsyncMock()
        return redis_mock

    @pytest.mark.asyncio
    async def test_get_redis_connection_success(self, mock_redis):
        """Test successful Redis connection."""
        service = WebhookService()

        with patch('dotmac.platform.communications.webhook_service.REDIS_AVAILABLE', True):
            with patch('dotmac.platform.communications.webhook_service.redis.from_url', return_value=mock_redis):
                redis_conn = await service._get_redis()
                assert redis_conn == mock_redis
                assert service._redis == mock_redis

    @pytest.mark.asyncio
    async def test_get_redis_connection_unavailable(self):
        """Test Redis connection when Redis is unavailable."""
        service = WebhookService()

        with patch('dotmac.platform.communications.webhook_service.REDIS_AVAILABLE', False):
            redis_conn = await service._get_redis()
            assert redis_conn is None

    @pytest.mark.asyncio
    async def test_get_redis_connection_cached(self, mock_redis):
        """Test Redis connection returns cached instance."""
        service = WebhookService()
        service._redis = mock_redis

        redis_conn = await service._get_redis()
        assert redis_conn == mock_redis


class TestWebhookServiceSerialization:
    """Test data serialization/deserialization."""

    @pytest.fixture
    def service(self):
        return WebhookService()

    def test_serialize_dict(self, service):
        """Test serializing dictionary data."""
        data = {"key": "value", "number": 123}
        result = service._serialize(data)
        assert result == '{"key": "value", "number": 123}'

    def test_serialize_with_datetime(self, service):
        """Test serializing data with datetime objects."""
        now = datetime.now(UTC)
        data = {"timestamp": now, "message": "test"}
        result = service._serialize(data)
        # Should handle datetime serialization
        assert '"timestamp":' in result
        assert '"message": "test"' in result

    def test_deserialize_dict(self, service):
        """Test deserializing JSON string."""
        data = '{"key": "value", "number": 123}'
        result = service._deserialize(data)
        assert result == {"key": "value", "number": 123}

    def test_deserialize_invalid_json(self, service):
        """Test deserializing invalid JSON."""
        with pytest.raises(json.JSONDecodeError):
            service._deserialize("invalid json")


class TestWebhookServiceSubscriptionManagement:
    """Test webhook subscription CRUD operations."""

    @pytest.fixture
    def service(self):
        return WebhookService()

    @pytest.fixture
    def sample_subscription(self):
        return {
            "id": str(uuid4()),
            "url": "https://example.com/webhook",
            "events": ["user.created", "order.completed"],
            "secret": "webhook_secret_123",
            "active": True,
            "created_at": datetime.now(UTC).isoformat(),
            "retry_config": {
                "max_retries": 3,
                "initial_delay": 1,
                "max_delay": 300
            }
        }

    @pytest.mark.asyncio
    async def test_create_subscription_redis(self, service, sample_subscription):
        """Test creating webhook subscription with Redis backend."""
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)

        with patch.object(service, '_get_redis', return_value=mock_redis):
            result = await service.create_subscription(sample_subscription)

            assert result["id"] == sample_subscription["id"]
            assert result["url"] == sample_subscription["url"]
            mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_subscription_memory_fallback(self, service, sample_subscription):
        """Test creating webhook subscription with memory fallback."""
        with patch.object(service, '_get_redis', return_value=None):
            result = await service.create_subscription(sample_subscription)

            assert result["id"] == sample_subscription["id"]
            assert sample_subscription["id"] in service._memory_storage

    @pytest.mark.asyncio
    async def test_get_subscription_redis(self, service, sample_subscription):
        """Test getting webhook subscription from Redis."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=service._serialize(sample_subscription))

        with patch.object(service, '_get_redis', return_value=mock_redis):
            result = await service.get_subscription(sample_subscription["id"])

            assert result["id"] == sample_subscription["id"]
            assert result["url"] == sample_subscription["url"]

    @pytest.mark.asyncio
    async def test_get_subscription_memory(self, service, sample_subscription):
        """Test getting webhook subscription from memory."""
        service._memory_storage[f"webhook:subscription:{sample_subscription['id']}"] = sample_subscription

        with patch.object(service, '_get_redis', return_value=None):
            result = await service.get_subscription(sample_subscription["id"])

            assert result["id"] == sample_subscription["id"]

    @pytest.mark.asyncio
    async def test_get_subscription_not_found(self, service):
        """Test getting non-existent webhook subscription."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        with patch.object(service, '_get_redis', return_value=mock_redis):
            result = await service.get_subscription("nonexistent")
            assert result is None

    @pytest.mark.asyncio
    async def test_list_subscriptions_redis(self, service, sample_subscription):
        """Test listing webhook subscriptions from Redis."""
        mock_redis = AsyncMock()
        mock_redis.scan_iter = AsyncMock(return_value=[f"webhook:subscription:{sample_subscription['id']}"])
        mock_redis.get = AsyncMock(return_value=service._serialize(sample_subscription))

        with patch.object(service, '_get_redis', return_value=mock_redis):
            result = await service.list_subscriptions()

            assert len(result) == 1
            assert result[0]["id"] == sample_subscription["id"]

    @pytest.mark.asyncio
    async def test_update_subscription_redis(self, service, sample_subscription):
        """Test updating webhook subscription in Redis."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=service._serialize(sample_subscription))
        mock_redis.set = AsyncMock(return_value=True)

        updates = {"active": False, "events": ["user.updated"]}

        with patch.object(service, '_get_redis', return_value=mock_redis):
            result = await service.update_subscription(sample_subscription["id"], updates)

            assert result["active"] is False
            assert result["events"] == ["user.updated"]

    @pytest.mark.asyncio
    async def test_delete_subscription_redis(self, service, sample_subscription):
        """Test deleting webhook subscription from Redis."""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=1)

        with patch.object(service, '_get_redis', return_value=mock_redis):
            result = await service.delete_subscription(sample_subscription["id"])

            assert result is True
            mock_redis.delete.assert_called_once()


class TestWebhookServiceEventDelivery:
    """Test webhook event delivery functionality."""

    @pytest.fixture
    def service(self):
        return WebhookService()

    @pytest.fixture
    def sample_subscription(self):
        return {
            "id": str(uuid4()),
            "url": "https://example.com/webhook",
            "events": ["user.created"],
            "secret": "webhook_secret_123",
            "active": True
        }

    @pytest.fixture
    def sample_event(self):
        return {
            "event_type": "user.created",
            "data": {
                "user_id": "123",
                "email": "test@example.com",
                "created_at": "2024-01-01T00:00:00Z"
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }

    @pytest.mark.asyncio
    async def test_deliver_event_success(self, service, sample_subscription, sample_event):
        """Test successful event delivery."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="OK")

        mock_session = AsyncMock()
        mock_session.post = AsyncMock(return_value=mock_response)

        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await service.deliver_event(sample_subscription, sample_event)

            assert result["success"] is True
            assert result["status_code"] == 200
            assert result["response_body"] == "OK"

    @pytest.mark.asyncio
    async def test_deliver_event_with_hmac_signature(self, service, sample_subscription, sample_event):
        """Test event delivery with HMAC signature."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="OK")

        mock_session = AsyncMock()
        mock_session.post = AsyncMock(return_value=mock_response)

        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await service.deliver_event(sample_subscription, sample_event)

            # Verify HMAC signature was included in headers
            call_args = mock_session.post.call_args
            headers = call_args[1]["headers"]
            assert "X-Webhook-Signature" in headers

            # Verify signature format
            signature = headers["X-Webhook-Signature"]
            assert signature.startswith("sha256=")

    @pytest.mark.asyncio
    async def test_deliver_event_failure(self, service, sample_subscription, sample_event):
        """Test event delivery failure."""
        mock_response = Mock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")

        mock_session = AsyncMock()
        mock_session.post = AsyncMock(return_value=mock_response)

        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await service.deliver_event(sample_subscription, sample_event)

            assert result["success"] is False
            assert result["status_code"] == 500
            assert result["response_body"] == "Internal Server Error"

    @pytest.mark.asyncio
    async def test_deliver_event_timeout(self, service, sample_subscription, sample_event):
        """Test event delivery timeout."""
        mock_session = AsyncMock()
        mock_session.post = AsyncMock(side_effect=asyncio.TimeoutError())

        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await service.deliver_event(sample_subscription, sample_event)

            assert result["success"] is False
            assert "timeout" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_deliver_event_connection_error(self, service, sample_subscription, sample_event):
        """Test event delivery connection error."""
        mock_session = AsyncMock()
        mock_session.post = AsyncMock(side_effect=aiohttp.ClientConnectorError(
            connection_key=Mock(), os_error=OSError("Connection failed")
        ))

        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await service.deliver_event(sample_subscription, sample_event)

            assert result["success"] is False
            assert "connection" in result["error"].lower()


class TestWebhookServiceRetryLogic:
    """Test webhook retry mechanisms."""

    @pytest.fixture
    def service(self):
        return WebhookService()

    @pytest.fixture
    def failing_subscription(self):
        return {
            "id": str(uuid4()),
            "url": "https://example.com/webhook",
            "events": ["user.created"],
            "secret": "webhook_secret_123",
            "active": True,
            "retry_config": {
                "max_retries": 2,
                "initial_delay": 1,
                "max_delay": 60
            }
        }

    @pytest.fixture
    def sample_event(self):
        return {
            "event_type": "user.created",
            "data": {"user_id": "123"},
            "timestamp": "2024-01-01T00:00:00Z"
        }

    @pytest.mark.asyncio
    async def test_deliver_event_with_retries_eventual_success(self, service, failing_subscription, sample_event):
        """Test event delivery succeeds after retries."""
        # First call fails, second succeeds
        mock_responses = [
            Mock(status=500, text=AsyncMock(return_value="Error")),
            Mock(status=200, text=AsyncMock(return_value="OK"))
        ]

        mock_session = AsyncMock()
        mock_session.post = AsyncMock(side_effect=mock_responses)

        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('asyncio.sleep', new_callable=AsyncMock):  # Speed up test
                result = await service.deliver_event_with_retries(failing_subscription, sample_event)

                assert result["success"] is True
                assert result["attempts"] == 2
                assert mock_session.post.call_count == 2

    @pytest.mark.asyncio
    async def test_deliver_event_with_retries_max_attempts_exceeded(self, service, failing_subscription, sample_event):
        """Test event delivery fails after max retries."""
        mock_response = Mock(status=500, text=AsyncMock(return_value="Error"))
        mock_session = AsyncMock()
        mock_session.post = AsyncMock(return_value=mock_response)

        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await service.deliver_event_with_retries(failing_subscription, sample_event)

                assert result["success"] is False
                assert result["attempts"] == 3  # initial + 2 retries
                assert mock_session.post.call_count == 3


class TestWebhookServiceHMACSignature:
    """Test HMAC signature generation and validation."""

    @pytest.fixture
    def service(self):
        return WebhookService()

    def test_generate_hmac_signature(self, service):
        """Test HMAC signature generation."""
        payload = '{"event_type": "user.created", "data": {"user_id": "123"}}'
        secret = "webhook_secret_123"

        signature = service._generate_signature(payload, secret)

        # Verify format
        assert signature.startswith("sha256=")

        # Verify it's a valid HMAC
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        assert signature == f"sha256={expected_signature}"

    def test_verify_hmac_signature_valid(self, service):
        """Test HMAC signature verification - valid."""
        payload = '{"event_type": "user.created"}'
        secret = "webhook_secret_123"

        signature = service._generate_signature(payload, secret)
        is_valid = service._verify_signature(payload, signature, secret)

        assert is_valid is True

    def test_verify_hmac_signature_invalid(self, service):
        """Test HMAC signature verification - invalid."""
        payload = '{"event_type": "user.created"}'
        secret = "webhook_secret_123"
        wrong_signature = "sha256=wrongsignature"

        is_valid = service._verify_signature(payload, wrong_signature, secret)

        assert is_valid is False

    def test_verify_hmac_signature_tampered_payload(self, service):
        """Test HMAC signature verification - tampered payload."""
        original_payload = '{"event_type": "user.created"}'
        tampered_payload = '{"event_type": "user.deleted"}'
        secret = "webhook_secret_123"

        signature = service._generate_signature(original_payload, secret)
        is_valid = service._verify_signature(tampered_payload, signature, secret)

        assert is_valid is False


class TestWebhookServiceEventMatching:
    """Test event matching and filtering."""

    @pytest.fixture
    def service(self):
        return WebhookService()

    @pytest.fixture
    def subscriptions(self):
        return [
            {
                "id": "sub1",
                "url": "https://example.com/webhook1",
                "events": ["user.created", "user.updated"],
                "active": True
            },
            {
                "id": "sub2",
                "url": "https://example.com/webhook2",
                "events": ["order.*"],  # Wildcard
                "active": True
            },
            {
                "id": "sub3",
                "url": "https://example.com/webhook3",
                "events": ["user.deleted"],
                "active": False  # Inactive
            }
        ]

    @pytest.mark.asyncio
    async def test_get_matching_subscriptions_exact_match(self, service, subscriptions):
        """Test getting subscriptions for exact event match."""
        with patch.object(service, 'list_subscriptions', return_value=subscriptions):
            matches = await service.get_matching_subscriptions("user.created")

            assert len(matches) == 1
            assert matches[0]["id"] == "sub1"

    @pytest.mark.asyncio
    async def test_get_matching_subscriptions_wildcard_match(self, service, subscriptions):
        """Test getting subscriptions for wildcard event match."""
        with patch.object(service, 'list_subscriptions', return_value=subscriptions):
            matches = await service.get_matching_subscriptions("order.completed")

            assert len(matches) == 1
            assert matches[0]["id"] == "sub2"

    @pytest.mark.asyncio
    async def test_get_matching_subscriptions_inactive_filtered(self, service, subscriptions):
        """Test that inactive subscriptions are filtered out."""
        with patch.object(service, 'list_subscriptions', return_value=subscriptions):
            matches = await service.get_matching_subscriptions("user.deleted")

            assert len(matches) == 0  # sub3 is inactive

    @pytest.mark.asyncio
    async def test_get_matching_subscriptions_no_match(self, service, subscriptions):
        """Test getting subscriptions when no events match."""
        with patch.object(service, 'list_subscriptions', return_value=subscriptions):
            matches = await service.get_matching_subscriptions("payment.failed")

            assert len(matches) == 0


class TestWebhookServiceBroadcast:
    """Test event broadcasting to multiple subscriptions."""

    @pytest.fixture
    def service(self):
        return WebhookService()

    @pytest.fixture
    def sample_event(self):
        return {
            "event_type": "user.created",
            "data": {"user_id": "123", "email": "test@example.com"},
            "timestamp": "2024-01-01T00:00:00Z"
        }

    @pytest.mark.asyncio
    async def test_broadcast_event_to_multiple_subscriptions(self, service, sample_event):
        """Test broadcasting event to multiple matching subscriptions."""
        subscriptions = [
            {
                "id": "sub1",
                "url": "https://example.com/webhook1",
                "events": ["user.created"],
                "secret": "secret1",
                "active": True
            },
            {
                "id": "sub2",
                "url": "https://example.com/webhook2",
                "events": ["user.*"],
                "secret": "secret2",
                "active": True
            }
        ]

        with patch.object(service, 'get_matching_subscriptions', return_value=subscriptions):
            with patch.object(service, 'deliver_event_with_retries') as mock_deliver:
                mock_deliver.return_value = {"success": True, "attempts": 1}

                results = await service.broadcast_event(sample_event)

                assert len(results) == 2
                assert mock_deliver.call_count == 2

                # Verify both subscriptions were called
                calls = mock_deliver.call_args_list
                called_subs = [call[0][0]["id"] for call in calls]
                assert "sub1" in called_subs
                assert "sub2" in called_subs

    @pytest.mark.asyncio
    async def test_broadcast_event_no_matching_subscriptions(self, service, sample_event):
        """Test broadcasting event with no matching subscriptions."""
        with patch.object(service, 'get_matching_subscriptions', return_value=[]):
            results = await service.broadcast_event(sample_event)

            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_broadcast_event_mixed_success_failure(self, service, sample_event):
        """Test broadcasting event with mixed success/failure results."""
        subscriptions = [
            {"id": "sub1", "url": "https://example.com/webhook1", "events": ["user.created"], "active": True},
            {"id": "sub2", "url": "https://example.com/webhook2", "events": ["user.created"], "active": True}
        ]

        def mock_deliver_side_effect(sub, event):
            if sub["id"] == "sub1":
                return {"success": True, "attempts": 1}
            else:
                return {"success": False, "attempts": 3, "error": "Connection failed"}

        with patch.object(service, 'get_matching_subscriptions', return_value=subscriptions):
            with patch.object(service, 'deliver_event_with_retries', side_effect=mock_deliver_side_effect):
                results = await service.broadcast_event(sample_event)

                assert len(results) == 2

                # Check mixed results
                successful = [r for r in results if r["success"]]
                failed = [r for r in results if not r["success"]]

                assert len(successful) == 1
                assert len(failed) == 1
                assert failed[0]["error"] == "Connection failed"


class TestWebhookServiceRateLimiting:
    """Test rate limiting functionality."""

    @pytest.fixture
    def service(self):
        return WebhookService()

    @pytest.mark.asyncio
    async def test_rate_limit_check_under_limit(self, service):
        """Test rate limit check when under limit."""
        subscription_id = "test_sub"

        # Mock Redis to return low count
        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock()

        with patch.object(service, '_get_redis', return_value=mock_redis):
            is_allowed = await service.check_rate_limit(subscription_id, limit=10, window=60)

            assert is_allowed is True

    @pytest.mark.asyncio
    async def test_rate_limit_check_over_limit(self, service):
        """Test rate limit check when over limit."""
        subscription_id = "test_sub"

        # Mock Redis to return high count
        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=15)

        with patch.object(service, '_get_redis', return_value=mock_redis):
            is_allowed = await service.check_rate_limit(subscription_id, limit=10, window=60)

            assert is_allowed is False

    @pytest.mark.asyncio
    async def test_rate_limit_memory_fallback(self, service):
        """Test rate limiting with memory fallback."""
        subscription_id = "test_sub"

        with patch.object(service, '_get_redis', return_value=None):
            # Should allow when Redis unavailable (graceful degradation)
            is_allowed = await service.check_rate_limit(subscription_id, limit=10, window=60)
            assert is_allowed is True
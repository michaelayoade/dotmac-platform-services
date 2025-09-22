"""
Comprehensive tests for communications module.
Testing email sending, SMS integration, push notifications, and WebSocket messaging.
Developer 3 - Coverage Task: User Management & Communications
"""

import asyncio
import json
import time
from datetime import datetime, timedelta, UTC
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, Mock, MagicMock, patch, call

import pytest

pytest_plugins = (
    "tests.fixtures.mock_http",
    "tests.fixtures.mock_redis",
)

from dotmac.platform.communications.notifications import (
    NotificationRequest,
    NotificationResponse,
    NotificationStatus,
    NotificationType,
    NotificationPriority,
    NotificationTemplate,
    UnifiedNotificationService,
    BulkNotificationRequest,
    BulkNotificationResponse,
)
from dotmac.platform.communications.websockets import (
    WebSocketGateway,
    WebSocketSession,
    SessionManager,
    Channel,
    ChannelManager,
    BroadcastManager,
    AuthManager,
    AuthMiddleware,
    AuthResult,
    UserInfo,
    WebSocketConfig,
    RedisConfig,
    LocalBackend,
    RedisScalingBackend,
)
from dotmac.platform.communications.webhooks import (
    WebhookClient,
    send_webhook_notification,
)


@pytest.fixture
def notification_service(mock_http_session):
    """Create notification service instance."""
    # Mock the HTTP client if the service uses one
    # For now, just create the service directly
    service = UnifiedNotificationService()
    # Inject mock HTTP session if the service has an http_client attribute
    if hasattr(service, 'http_client'):
        service.http_client = mock_http_session
    elif hasattr(service, '_http_client'):
        service._http_client = mock_http_session
    return service


@pytest.fixture
def websocket_config():
    """Create WebSocket configuration."""
    return settings.WebSocket.model_copy(update={
        max_connections_per_user=10,
        ping_interval=30,
        ping_timeout=10,
        message_size_limit=1024 * 1024,  # 1MB
        enable_compression=True,
    })


@pytest.fixture
def websocket_gateway(websocket_config, mock_redis):
    """Create WebSocket gateway instance."""
    return WebSocketGateway(
        config=websocket_config,
        backend=LocalBackend(),
    )


class TestNotificationService:
    """Test unified notification service."""

    async def test_send_email_notification(self, notification_service, mock_http_session):
        """Test sending email notification."""
        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="user@example.com",
            subject="Test Email",
            body="This is a test email",
            metadata={"campaign": "test"},
        )

        response = await notification_service.send(request)

        assert response.status == NotificationStatus.SENT
        assert response.notification_id is not None
        mock_http_session.post.assert_called()

    async def test_send_sms_notification(self, notification_service, mock_http_session):
        """Test sending SMS notification."""
        request = NotificationRequest(
            type=NotificationType.SMS,
            recipient="+1234567890",
            body="Your verification code is 123456",
            priority=NotificationPriority.HIGH,
        )

        response = await notification_service.send(request)

        assert response.status == NotificationStatus.SENT
        assert response.notification_id is not None

    async def test_send_push_notification(self, notification_service, mock_http_session):
        """Test sending push notification."""
        request = NotificationRequest(
            type=NotificationType.PUSH,
            recipient="device_token_123",
            subject="New Message",
            body="You have a new message",
            data={"badge": 1, "sound": "default"},
        )

        response = await notification_service.send(request)

        assert response.status == NotificationStatus.SENT
        assert response.notification_id is not None

    async def test_send_slack_notification(self, notification_service, mock_http_session):
        """Test sending Slack notification."""
        request = NotificationRequest(
            type=NotificationType.SLACK,
            recipient="#general",
            body="Deployment completed successfully",
            metadata={"icon_emoji": ":rocket:"},
        )

        response = await notification_service.send(request)

        assert response.status == NotificationStatus.SENT

    async def test_bulk_notifications(self, notification_service, mock_http_session):
        """Test sending bulk notifications."""
        requests = [
            NotificationRequest(
                type=NotificationType.EMAIL,
                recipient=f"user{i}@example.com",
                subject="Bulk Email",
                body="Bulk message",
            )
            for i in range(10)
        ]

        bulk_request = BulkNotificationRequest(notifications=requests)
        bulk_response = await notification_service.send_bulk(bulk_request)

        assert bulk_response.total == 10
        assert bulk_response.successful == 10
        assert bulk_response.failed == 0

    async def test_notification_with_template(self, notification_service):
        """Test notification using template."""
        template = NotificationTemplate(
            id="welcome_email",
            name="Welcome Email",
            subject="Welcome to {{app_name}}",
            body="Hello {{user_name}}, welcome to our service!",
            variables={"app_name": "DotMac", "user_name": "John"},
        )

        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="user@example.com",
            template=template,
        )

        response = await notification_service.send(request)

        assert response.status == NotificationStatus.SENT
        # Template should be rendered
        assert "DotMac" in response.rendered_body
        assert "John" in response.rendered_body

    async def test_notification_with_attachments(self, notification_service, mock_http_session):
        """Test notification with attachments."""
        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="user@example.com",
            subject="Invoice",
            body="Please find attached invoice",
            attachments=[
                {"filename": "invoice.pdf", "content": b"PDF content", "mime_type": "application/pdf"}
            ],
        )

        response = await notification_service.send(request)

        assert response.status == NotificationStatus.SENT
        # Verify attachment was included in request
        call_args = mock_http_session.post.call_args
        assert "attachments" in str(call_args)

    async def test_notification_retry_on_failure(self, notification_service, mock_http_session):
        """Test notification retry mechanism."""
        # Make first two calls fail, third succeed
        mock_http_session.post.side_effect = [
            Mock(status_code=500),
            Mock(status_code=500),
            Mock(status_code=200, json=lambda: {"status": "sent"}),
        ]

        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="user@example.com",
            subject="Test",
            body="Test",
            retry_count=3,
        )

        response = await notification_service.send(request)

        assert response.status == NotificationStatus.SENT
        assert mock_http_session.post.call_count == 3

    async def test_notification_priority_queue(self, notification_service):
        """Test priority-based notification queuing."""
        high_priority = NotificationRequest(
            type=NotificationType.SMS,
            recipient="+1234567890",
            body="Urgent",
            priority=NotificationPriority.CRITICAL,
        )

        low_priority = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="user@example.com",
            subject="Newsletter",
            body="Content",
            priority=NotificationPriority.LOW,
        )

        # Send both notifications
        responses = await asyncio.gather(
            notification_service.send(low_priority),
            notification_service.send(high_priority),
        )

        # High priority should be processed first
        assert all(r.status == NotificationStatus.SENT for r in responses)

    async def test_notification_rate_limiting(self, notification_service):
        """Test rate limiting for notifications."""
        # Configure rate limit
        notification_service.configure_rate_limit(
            max_per_minute=5,
            recipient="user@example.com"
        )

        # Try to send 10 notifications rapidly
        requests = [
            NotificationRequest(
                type=NotificationType.EMAIL,
                recipient="user@example.com",
                subject=f"Email {i}",
                body="Content",
            )
            for i in range(10)
        ]

        responses = []
        for req in requests:
            response = await notification_service.send(req)
            responses.append(response)

        # First 5 should succeed, rest should be rate limited
        successful = sum(1 for r in responses if r.status == NotificationStatus.SENT)
        rate_limited = sum(1 for r in responses if r.status == NotificationStatus.RATE_LIMITED)

        assert successful == 5
        assert rate_limited == 5

    async def test_notification_scheduling(self, notification_service):
        """Test scheduled notification delivery."""
        scheduled_time = datetime.now(UTC) + timedelta(minutes=5)

        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="user@example.com",
            subject="Scheduled Email",
            body="This should be sent later",
            scheduled_at=scheduled_time,
        )

        response = await notification_service.send(request)

        assert response.status == NotificationStatus.SCHEDULED
        assert response.scheduled_at == scheduled_time


class TestWebSocketGateway:
    """Test WebSocket gateway functionality."""

    async def test_websocket_connection(self, websocket_gateway, mock_websocket):
        """Test establishing WebSocket connection."""
        user_info = UserInfo(
            user_id="user_123",
            tenant_id="tenant_456",
            roles=["user"],
        )

        session = await websocket_gateway.connect(
            websocket=mock_websocket,
            user_info=user_info,
        )

        assert session is not None
        assert session.user_id == "user_123"
        assert session.tenant_id == "tenant_456"
        assert session.is_active

        mock_websocket.accept.assert_called_once()

    async def test_websocket_message_handling(self, websocket_gateway, mock_websocket):
        """Test WebSocket message handling."""
        user_info = UserInfo(user_id="user_123")
        session = await websocket_gateway.connect(mock_websocket, user_info)

        # Simulate receiving message
        mock_websocket.receive_json.return_value = {
            "type": "message",
            "data": {"text": "Hello"}
        }

        message = await websocket_gateway.receive_message(session)

        assert message["type"] == "message"
        assert message["data"]["text"] == "Hello"

    async def test_websocket_broadcasting(self, websocket_gateway, mock_websocket):
        """Test broadcasting messages to multiple connections."""
        # Connect multiple users
        sessions = []
        for i in range(5):
            ws = AsyncMock()
            ws.send_json = AsyncMock()
            user_info = UserInfo(user_id=f"user_{i}")
            session = await websocket_gateway.connect(ws, user_info)
            sessions.append(session)

        # Broadcast message
        await websocket_gateway.broadcast(
            message={"type": "announcement", "text": "Server maintenance"},
            tenant_id=None,  # Broadcast to all
        )

        # Verify all connections received the message
        for session in sessions:
            session.websocket.send_json.assert_called_with({
                "type": "announcement",
                "text": "Server maintenance"
            })

    async def test_websocket_channel_subscription(self, websocket_gateway, mock_websocket):
        """Test channel subscription and messaging."""
        user_info = UserInfo(user_id="user_123")
        session = await websocket_gateway.connect(mock_websocket, user_info)

        # Subscribe to channel
        await websocket_gateway.subscribe_channel(session, "news")

        # Send message to channel
        await websocket_gateway.send_to_channel(
            "news",
            {"type": "update", "content": "Breaking news"}
        )

        mock_websocket.send_json.assert_called_with({
            "type": "update",
            "content": "Breaking news"
        })

    async def test_websocket_private_messaging(self, websocket_gateway):
        """Test private messaging between users."""
        # Connect two users
        sender_ws = AsyncMock()
        sender_info = UserInfo(user_id="sender")
        sender_session = await websocket_gateway.connect(sender_ws, sender_info)

        receiver_ws = AsyncMock()
        receiver_info = UserInfo(user_id="receiver")
        receiver_session = await websocket_gateway.connect(receiver_ws, receiver_info)

        # Send private message
        await websocket_gateway.send_private_message(
            from_session=sender_session,
            to_user_id="receiver",
            message={"text": "Private message"}
        )

        # Only receiver should get the message
        receiver_ws.send_json.assert_called_with({
            "from": "sender",
            "text": "Private message"
        })
        sender_ws.send_json.assert_not_called()

    async def test_websocket_connection_limits(self, websocket_config):
        """Test connection limits per user."""
        config = settings.WebSocket.model_copy(update={max_connections_per_user=2})
        gateway = WebSocketGateway(config=config, backend=LocalBackend())

        user_info = UserInfo(user_id="user_123")

        # Connect twice (should succeed)
        session1 = await gateway.connect(AsyncMock(), user_info)
        session2 = await gateway.connect(AsyncMock(), user_info)

        assert session1 is not None
        assert session2 is not None

        # Third connection should fail
        with pytest.raises(ConnectionError, match="Connection limit exceeded"):
            await gateway.connect(AsyncMock(), user_info)

    async def test_websocket_ping_pong(self, websocket_gateway, mock_websocket):
        """Test WebSocket ping/pong keepalive."""
        user_info = UserInfo(user_id="user_123")
        session = await websocket_gateway.connect(mock_websocket, user_info)

        # Start ping task
        ping_task = asyncio.create_task(
            websocket_gateway.ping_loop(session)
        )

        # Let it run for a moment
        await asyncio.sleep(0.1)

        # Cancel task
        ping_task.cancel()

        # Should have sent ping
        mock_websocket.send_json.assert_called()
        call_args = mock_websocket.send_json.call_args_list
        assert any("ping" in str(call) for call in call_args)

    async def test_websocket_disconnect_handling(self, websocket_gateway, mock_websocket):
        """Test proper disconnect handling."""
        user_info = UserInfo(user_id="user_123")
        session = await websocket_gateway.connect(mock_websocket, user_info)

        # Subscribe to channel before disconnect
        await websocket_gateway.subscribe_channel(session, "updates")

        # Disconnect
        await websocket_gateway.disconnect(session)

        assert not session.is_active
        mock_websocket.close.assert_called_once()

        # Should be unsubscribed from channels
        subscribers = await websocket_gateway.get_channel_subscribers("updates")
        assert session not in subscribers

    async def test_websocket_error_recovery(self, websocket_gateway, mock_websocket):
        """Test error recovery in WebSocket communication."""
        user_info = UserInfo(user_id="user_123")
        session = await websocket_gateway.connect(mock_websocket, user_info)

        # Simulate connection error
        mock_websocket.send_json.side_effect = ConnectionError("Connection lost")

        # Try to send message
        with pytest.raises(ConnectionError):
            await websocket_gateway.send_message(session, {"data": "test"})

        # Session should be marked as inactive
        assert not session.is_active


class TestWebSocketScaling:
    """Test WebSocket scaling with Redis backend."""

    @pytest.fixture
    def redis_backend(self, mock_redis):
        """Create Redis scaling backend."""
        return RedisScalingBackend(redis_client=mock_redis)

    async def test_redis_pubsub_messaging(self, redis_backend, mock_redis):
        """Test Redis pub/sub for cross-server messaging."""
        # Publish message
        await redis_backend.publish(
            channel="global",
            message={"type": "broadcast", "data": "test"}
        )

        mock_redis.publish.assert_called_with(
            "websocket:global",
            json.dumps({"type": "broadcast", "data": "test"})
        )

    async def test_session_storage_in_redis(self, redis_backend, mock_redis):
        """Test session storage in Redis for scaling."""
        session_data = {
            "session_id": "sess_123",
            "user_id": "user_456",
            "connected_at": datetime.now(UTC).isoformat(),
        }

        # Store session
        await redis_backend.store_session("sess_123", session_data)

        mock_redis.set.assert_called()
        call_args = mock_redis.set.call_args
        assert "sess_123" in str(call_args)

        # Retrieve session
        mock_redis.get.return_value = json.dumps(session_data)
        retrieved = await redis_backend.get_session("sess_123")

        assert retrieved["user_id"] == "user_456"

    async def test_distributed_channel_management(self, redis_backend, mock_redis):
        """Test channel management across multiple servers."""
        # Subscribe to channel
        await redis_backend.subscribe_to_channel("user_123", "news")

        # Check subscription
        mock_redis.sadd = AsyncMock(return_value=1)
        await redis_backend.add_channel_member("news", "user_123")
        mock_redis.sadd.assert_called_with("channel:news", "user_123")

        # List channel members
        mock_redis.smembers = AsyncMock(return_value={"user_123", "user_456"})
        members = await redis_backend.get_channel_members("news")

        assert "user_123" in members
        assert "user_456" in members

    async def test_presence_tracking(self, redis_backend, mock_redis):
        """Test user presence tracking across servers."""
        # Set user online
        await redis_backend.set_user_online("user_123", server_id="server_1")

        # Check presence
        mock_redis.setex = AsyncMock()
        await redis_backend.update_presence("user_123", ttl=60)
        mock_redis.setex.assert_called()

        # Get online users
        mock_redis.keys = AsyncMock(return_value=["presence:user_123", "presence:user_456"])
        online_users = await redis_backend.get_online_users()

        assert len(online_users) == 2


class TestWebhookClient:
    """Test webhook notification functionality."""

    @pytest.fixture
    def webhook_client(self, mock_http_session):
        """Create webhook client."""
        return WebhookClient(http_client=mock_http_session)

    async def test_send_webhook(self, webhook_client, mock_http_session):
        """Test sending webhook notification."""
        result = await webhook_client.send(
            url="https://example.com/webhook",
            payload={"event": "user_signup", "user_id": "123"},
            headers={"X-Signature": "secret"},
        )

        assert result["status"] == "success"
        mock_http_session.post.assert_called_with(
            "https://example.com/webhook",
            json={"event": "user_signup", "user_id": "123"},
            headers={"X-Signature": "secret"}
        )

    async def test_webhook_retry_logic(self, webhook_client, mock_http_session):
        """Test webhook retry on failure."""
        # First call fails, second succeeds
        mock_http_session.post.side_effect = [
            Mock(status_code=500),
            Mock(status_code=200, json=lambda: {"received": True}),
        ]

        result = await webhook_client.send(
            url="https://example.com/webhook",
            payload={"data": "test"},
            retry_count=2,
        )

        assert result["status"] == "success"
        assert mock_http_session.post.call_count == 2

    async def test_webhook_timeout(self, webhook_client, mock_http_session):
        """Test webhook timeout handling."""
        mock_http_session.post.side_effect = asyncio.TimeoutError()

        with pytest.raises(TimeoutError):
            await webhook_client.send(
                url="https://example.com/webhook",
                payload={"data": "test"},
                timeout=1,
            )

    async def test_webhook_signature_verification(self, webhook_client):
        """Test webhook signature generation and verification."""
        payload = {"event": "test", "timestamp": time.time()}
        secret = "webhook_secret"

        # Generate signature
        signature = webhook_client.generate_signature(payload, secret)

        assert signature is not None
        assert len(signature) > 0

        # Verify signature
        is_valid = webhook_client.verify_signature(payload, signature, secret)

        assert is_valid is True

        # Invalid signature should fail
        is_valid = webhook_client.verify_signature(payload, "invalid_sig", secret)

        assert is_valid is False


class TestEmailProvider:
    """Test email provider integration."""

    async def test_sendgrid_integration(self, mock_http_session):
        """Test SendGrid email provider."""
        with patch('sendgrid.SendGridAPIClient') as mock_sendgrid:
            mock_client = MagicMock()
            mock_sendgrid.return_value = mock_client
            mock_client.send.return_value = Mock(status_code=202)

            from dotmac.platform.communications.providers import SendGridProvider

            provider = SendGridProvider(api_key="test_key")

            result = await provider.send_email(
                to="user@example.com",
                subject="Test",
                body="Test email",
                from_email="noreply@example.com",
            )

            assert result["status"] == "sent"

    async def test_smtp_provider(self):
        """Test SMTP email provider."""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            from dotmac.platform.communications.providers import SMTPProvider

            provider = SMTPProvider(
                host="smtp.example.com",
                port=587,
                username="user",
                password="pass",
            )

            result = await provider.send_email(
                to="user@example.com",
                subject="Test",
                body="Test email",
            )

            assert result["status"] == "sent"
            mock_server.send_message.assert_called_once()


class TestSMSProvider:
    """Test SMS provider integration."""

    async def test_twilio_integration(self, mock_http_session):
        """Test Twilio SMS provider."""
        with patch('twilio.rest.Client') as mock_twilio:
            mock_client = MagicMock()
            mock_twilio.return_value = mock_client
            mock_client.messages.create.return_value = Mock(sid="MSG123")

            from dotmac.platform.communications.providers import TwilioProvider

            provider = TwilioProvider(
                account_sid="test_sid",
                auth_token="test_token",
                from_number="+1234567890",
            )

            result = await provider.send_sms(
                to="+9876543210",
                body="Your code is 123456",
            )

            assert result["status"] == "sent"
            assert result["message_id"] == "MSG123"


class TestPushNotifications:
    """Test push notification functionality."""

    async def test_fcm_push_notification(self, mock_http_session):
        """Test Firebase Cloud Messaging."""
        with patch('firebase_admin.messaging.send') as mock_fcm:
            mock_fcm.return_value = "message_id_123"

            from dotmac.platform.communications.providers import FCMProvider

            provider = FCMProvider(credentials_path="firebase.json")

            result = await provider.send_push(
                device_token="token_123",
                title="New Message",
                body="You have a new message",
                data={"badge": 1},
            )

            assert result["status"] == "sent"
            assert result["message_id"] == "message_id_123"

    async def test_apns_push_notification(self):
        """Test Apple Push Notification Service."""
        with patch('apns2.client.APNsClient') as mock_apns:
            mock_client = MagicMock()
            mock_apns.return_value = mock_client
            mock_client.send_notification.return_value = None

            from dotmac.platform.communications.providers import APNSProvider

            provider = APNSProvider(
                key_path="apns_key.p8",
                key_id="KEY123",
                team_id="TEAM123",
            )

            result = await provider.send_push(
                device_token="token_456",
                alert="New notification",
                badge=2,
                sound="default",
            )

            assert result["status"] == "sent"


class TestNotificationTemplates:
    """Test notification template system."""

    async def test_template_rendering(self, notification_service):
        """Test template variable substitution."""
        template = NotificationTemplate(
            id="order_confirmation",
            name="Order Confirmation",
            subject="Order #{{order_id}} Confirmed",
            body="""
            Hi {{customer_name}},

            Your order #{{order_id}} has been confirmed.
            Total: ${{total_amount}}

            Items:
            {{#items}}
            - {{name}}: ${{price}}
            {{/items}}
            """,
            variables={
                "customer_name": "John Doe",
                "order_id": "12345",
                "total_amount": "99.99",
                "items": [
                    {"name": "Widget", "price": "49.99"},
                    {"name": "Gadget", "price": "50.00"},
                ],
            },
        )

        rendered = await notification_service.render_template(template)

        assert "Order #12345 Confirmed" in rendered["subject"]
        assert "John Doe" in rendered["body"]
        assert "$99.99" in rendered["body"]
        assert "Widget" in rendered["body"]

    async def test_template_localization(self, notification_service):
        """Test template localization support."""
        template = NotificationTemplate(
            id="welcome",
            name="Welcome",
            translations={
                "en": {
                    "subject": "Welcome to our service",
                    "body": "Thank you for joining",
                },
                "es": {
                    "subject": "Bienvenido a nuestro servicio",
                    "body": "Gracias por unirte",
                },
            },
        )

        # English version
        rendered_en = await notification_service.render_template(template, locale="en")
        assert "Welcome" in rendered_en["subject"]

        # Spanish version
        rendered_es = await notification_service.render_template(template, locale="es")
        assert "Bienvenido" in rendered_es["subject"]


class TestMessageQueuing:
    """Test message queuing and processing."""

    async def test_message_queue_processing(self, notification_service):
        """Test queued message processing."""
        # Add messages to queue
        for i in range(10):
            await notification_service.queue_notification(
                NotificationRequest(
                    type=NotificationType.EMAIL,
                    recipient=f"user{i}@example.com",
                    subject="Queued",
                    body="Message",
                )
            )

        # Process queue
        processed = await notification_service.process_queue(batch_size=5)

        assert processed == 5  # First batch

        processed = await notification_service.process_queue(batch_size=5)

        assert processed == 5  # Second batch

    async def test_dead_letter_queue(self, notification_service):
        """Test failed message handling."""
        # Create failing notification
        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="invalid@",  # Invalid email
            subject="Test",
            body="Test",
            max_retries=1,
        )

        response = await notification_service.send(request)

        assert response.status == NotificationStatus.FAILED

        # Check dead letter queue
        dlq_items = await notification_service.get_dead_letter_queue()

        assert len(dlq_items) == 1
        assert dlq_items[0]["recipient"] == "invalid@"


class TestPerformanceOptimization:
    """Test performance optimizations."""

    @pytest.mark.slow
    async def test_bulk_notification_performance(self, notification_service):
        """Test bulk notification sending performance."""
        import time

        # Create 1000 notifications
        requests = [
            NotificationRequest(
                type=NotificationType.EMAIL,
                recipient=f"user{i}@example.com",
                subject="Bulk",
                body="Message",
            )
            for i in range(1000)
        ]

        start = time.time()

        bulk_request = BulkNotificationRequest(notifications=requests)
        response = await notification_service.send_bulk(bulk_request)

        elapsed = time.time() - start

        assert response.total == 1000
        # Should complete within reasonable time (< 10 seconds)
        assert elapsed < 10

    async def test_websocket_message_throughput(self, websocket_gateway):
        """Test WebSocket message throughput."""
        # Connect multiple clients
        sessions = []
        for i in range(100):
            ws = AsyncMock()
            user_info = UserInfo(user_id=f"user_{i}")
            session = await websocket_gateway.connect(ws, user_info)
            sessions.append(session)

        import time
        start = time.time()

        # Send 1000 messages
        for i in range(1000):
            await websocket_gateway.broadcast({
                "type": "update",
                "data": f"message_{i}"
            })

        elapsed = time.time() - start

        # Should handle 1000 messages to 100 clients in < 5 seconds
        assert elapsed < 5

    async def test_connection_pooling(self, mock_http_session):
        """Test connection pooling for external services."""
        from dotmac.platform.communications.providers import ConnectionPool

        pool = ConnectionPool(max_size=10)

        # Create multiple concurrent requests
        tasks = []
        for i in range(50):
            tasks.append(pool.execute(
                mock_http_session.post,
                f"https://api.example.com/send",
                json={"message": f"test_{i}"}
            ))

        results = await asyncio.gather(*tasks)

        assert len(results) == 50
        # Pool should reuse connections efficiently
        assert pool.active_connections <= 10

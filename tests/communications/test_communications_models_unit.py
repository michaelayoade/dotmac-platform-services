"""Unit coverage for the lightweight communications models."""

from datetime import datetime, UTC

from dotmac.platform.communications.base import (
    CommunicationResult,
    DeliveryStatus,
    Message,
    MessagePriority,
    MessageType,
    NotificationChannel,
)


def test_message_defaults_and_overrides() -> None:
    """Ensure message models provide sensible defaults and allow overrides."""

    msg = Message(recipient="user@example.com", content="Hi there")
    assert msg.message_type is MessageType.EMAIL
    assert msg.priority is MessagePriority.NORMAL
    assert msg.timestamp.tzinfo is UTC

    custom = Message(
        recipient=["one@example.com", "two@example.com"],
        content="Webhook",
        message_type=MessageType.WEBHOOK,
        priority=MessagePriority.HIGH,
        metadata={"tenant": "acme"},
        tags=["bulk"],
    )
    assert custom.message_type is MessageType.WEBHOOK
    assert custom.priority is MessagePriority.HIGH
    assert custom.metadata["tenant"] == "acme"
    assert custom.tags == ["bulk"]


def test_notification_channel_serialisation() -> None:
    """Notification channel captures configuration and status flags."""

    channel = NotificationChannel(
        name="sms-primary",
        channel_type=MessageType.SMS,
        endpoint="https://sms.example.com",
        configuration={"sender_id": "DOTMAC"},
        enabled=False,
        credentials={"token": "secret"},
        rate_limit_per_minute=120,
        description="Primary SMS gateway",
        tags=["primary", "sms"],
    )

    data = channel.model_dump()
    assert data["endpoint"] == "https://sms.example.com"
    assert data["enabled"] is False
    assert data["rate_limit_per_minute"] == 120
    assert "primary" in data["tags"]


def test_communication_result_success_and_failure_states() -> None:
    """Result model should track timings, retries, and provider payloads."""

    result = CommunicationResult(
        message_id="msg-123",
        status=DeliveryStatus.SENT,
        success=True,
        sent_at=datetime.now(UTC),
        metadata={"attempt": 1},
    )
    assert result.success is True
    assert result.metadata["attempt"] == 1

    failure = result.model_copy(update={
        "status": DeliveryStatus.FAILED,
        "success": False,
        "error_message": "provider timeout",
        "attempts": 3,
    })
    assert failure.success is False
    assert failure.attempts == 3
    assert "timeout" in (failure.error_message or "")

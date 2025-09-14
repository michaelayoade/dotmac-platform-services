import os

import pytest

from dotmac.platform.communications.config import CommunicationsConfig, SMTPConfig, SMSConfig, WebSocketConfig, EventBusConfig, WebhookConfig


@pytest.mark.unit
def test_smtp_config_defaults_and_bounds():
    cfg = SMTPConfig(host="smtp.example.com", from_email="noreply@example.com")
    assert cfg.port == 587 and cfg.use_tls is True and cfg.use_ssl is False and cfg.timeout == 30


@pytest.mark.unit
def test_ws_and_eventbus_defaults():
    ws = WebSocketConfig()
    assert ws.max_connections > 0 and ws.ping_interval > 0

    eb = EventBusConfig()
    assert eb.backend in {"memory", "redis"}


@pytest.mark.unit
def test_webhook_defaults_and_validation():
    wh = WebhookConfig()
    assert wh.timeout > 0 and wh.verify_ssl is True
    assert wh.allowed_schemes == ["https"]


@pytest.mark.unit
def test_communications_config_from_env(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.env.com")
    monkeypatch.setenv("SMTP_FROM_EMAIL", "env@example.com")
    monkeypatch.delenv("SMS_GATEWAY_URL", raising=False)
    monkeypatch.setenv("WS_MAX_CONNECTIONS", "123")
    monkeypatch.setenv("EVENT_BUS_BACKEND", "memory")

    cfg = CommunicationsConfig.from_env()
    assert cfg.smtp is not None and cfg.smtp.host == "smtp.env.com"
    assert cfg.websocket.max_connections == 123
    assert cfg.event_bus.backend == "memory"


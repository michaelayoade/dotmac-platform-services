import types

import pytest

from dotmac.platform.communications.config import SMTPConfig
from dotmac.platform.communications.email import EmailMessage, EmailService


@pytest.mark.unit
def test_email_message_validators():
    em = EmailMessage(to="a@example.com", subject="s", body="b")
    assert em.to == ["a@example.com"]

    em2 = EmailMessage(to=["a@example.com", "b@example.com"], subject="s", body="b", cc=[], bcc=[])
    assert em2.cc is None and em2.bcc is None


@pytest.mark.unit
def test_email_service_create_message_and_recipients(monkeypatch):
    cfg = SMTPConfig(host="smtp.example.com", from_email="noreply@example.com", from_name="No Reply")
    svc = EmailService(cfg)
    msg = EmailMessage(
        to=["to1@example.com", "to2@example.com"],
        subject="Hello",
        body="Hi",
        cc=["cc@example.com"],
        bcc=["bcc@example.com"],
        reply_to="reply@example.com",
        headers={"X-Test": "1"},
    )

    mimemsg = svc._create_message(msg)
    assert mimemsg["From"] == "No Reply <noreply@example.com>"
    assert mimemsg["To"] == "to1@example.com, to2@example.com"
    assert mimemsg["Cc"] == "cc@example.com"
    assert mimemsg["Reply-To"] == "reply@example.com"
    assert mimemsg["X-Test"] == "1"

    recipients = svc._get_all_recipients(msg)
    assert set(recipients) == {"to1@example.com", "to2@example.com", "cc@example.com", "bcc@example.com"}


@pytest.mark.unit
def test_email_service_send_uses_smtp(monkeypatch):
    cfg = SMTPConfig(host="smtp.example.com", from_email="noreply@example.com", use_tls=True)
    svc = EmailService(cfg)

    sent = {"ok": False, "used_tls": False, "logged_in": False, "quit": False}

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            assert host == cfg.host and port == cfg.port and timeout == cfg.timeout

        def starttls(self):
            sent["used_tls"] = True

        def login(self, u, p):
            sent["logged_in"] = True

        def send_message(self, msg, to_addrs=None):
            assert to_addrs and len(to_addrs) == 1
            sent["ok"] = True

        def quit(self):
            sent["quit"] = True

    monkeypatch.setattr("smtplib.SMTP", FakeSMTP)

    # with credentials
    svc.config.username = "u"
    svc.config.password = "p"
    ok = svc.send(EmailMessage(to="user@example.com", subject="s", body="b"))
    assert ok and sent["ok"] and sent["used_tls"] and sent["logged_in"] and sent["quit"]


@pytest.mark.unit
def test_email_service_send_handles_exceptions(monkeypatch):
    cfg = SMTPConfig(host="smtp.example.com", from_email="noreply@example.com")
    svc = EmailService(cfg)

    class BoomSMTP:
        def __init__(self, *a, **k):
            raise RuntimeError("boom")

    monkeypatch.setattr("smtplib.SMTP", BoomSMTP)
    ok = svc.send(EmailMessage(to="user@example.com", subject="s", body="b"))
    assert ok is False


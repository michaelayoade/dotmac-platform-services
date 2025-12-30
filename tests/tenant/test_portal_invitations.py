"""Tests for tenant portal invitation flows."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock

from dotmac.platform.auth.core import UserInfo
from dotmac.platform.tenant.models import TenantInvitation, TenantInvitationStatus


class _FakeResult:
    """Minimal result shim for AsyncSession.execute()."""

    def __init__(self, invitation):
        self._invitation = invitation

    def scalar_one_or_none(self):
        return self._invitation


@pytest.mark.asyncio
async def test_resend_invitation_requires_pending(monkeypatch):
    """Resend should reject invitations that are not pending."""
    from dotmac.platform.tenant.portal_router import resend_invitation

    invitation = TenantInvitation(
        id="inv-1",
        tenant_id="tenant-123",
        email="invitee@example.com",
        role="member",
        invited_by="user-123",
        status=TenantInvitationStatus.REVOKED,
        token="token-123",
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )

    db = AsyncMock()
    db.execute = AsyncMock(return_value=_FakeResult(invitation))
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    send_email_mock = AsyncMock()
    monkeypatch.setattr(
        "dotmac.platform.tenant.portal_router._send_invitation_email",
        send_email_mock,
    )

    user = UserInfo(
        user_id=str(uuid4()),
        email="admin@example.com",
        roles=["tenant_admin"],
        tenant_id="tenant-123",
    )
    tenant = SimpleNamespace(id="tenant-123")

    with pytest.raises(HTTPException) as exc:
        await resend_invitation(
            invitation_id="inv-1",
            user_tenant=(user, tenant),
            service=AsyncMock(),
            db=db,
        )

    assert exc.value.status_code == 400
    send_email_mock.assert_not_called()
    db.commit.assert_not_called()

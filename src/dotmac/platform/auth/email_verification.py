"""
Shared helpers for email verification flows.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode
from uuid import UUID

import structlog
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.email_service import get_auth_email_service
from dotmac.platform.settings import settings
from dotmac.platform.user_management.models import EmailVerificationToken, User

logger = structlog.get_logger(__name__)

DEFAULT_VERIFICATION_TTL_HOURS = 24


def _resolve_frontend_url() -> str:
    try:
        return settings.external_services.frontend_url
    except AttributeError:
        return getattr(settings, "frontend_url", "http://localhost:3000")


def build_verification_url(token: str, email: str | None = None) -> str:
    query = {"token": token}
    if email:
        query["email"] = email
    return f"{_resolve_frontend_url()}/verify-email?{urlencode(query)}"


async def create_verification_token(
    session: AsyncSession,
    user: User,
    email: str,
    ttl_hours: int = DEFAULT_VERIFICATION_TTL_HOURS,
) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    now = datetime.now(UTC)

    verification_token = EmailVerificationToken(
        user_id=user.id,
        token_hash=token_hash,
        email=email,
        expires_at=now + timedelta(hours=ttl_hours),
        used=False,
        tenant_id=user.tenant_id,
        created_at=now,
        updated_at=now,
    )

    session.add(verification_token)
    await session.commit()
    return token


async def invalidate_verification_tokens(
    session: AsyncSession,
    user_id: str | UUID,
    email: str,
) -> None:
    if isinstance(user_id, str):
        user_id = UUID(user_id)
    stmt = (
        update(EmailVerificationToken)
        .where(EmailVerificationToken.user_id == user_id)
        .where(EmailVerificationToken.email == email)
        .where(EmailVerificationToken.used.is_(False))
        .values(used=True, used_at=datetime.now(UTC))
    )
    await session.execute(stmt)
    await session.commit()


async def send_verification_email(
    session: AsyncSession,
    user: User,
    email: str,
    include_email_in_link: bool = True,
) -> bool:
    token = await create_verification_token(session, user, email)
    verification_url = build_verification_url(token, email if include_email_in_link else None)

    email_service = get_auth_email_service()
    user_name = user.username or user.email

    try:
        success = await email_service.send_verification_email(
            email=email,
            user_name=user_name,
            verification_url=verification_url,
        )
    except Exception as exc:
        logger.warning(
            "auth.verification_email.send_failed",
            user_id=str(user.id),
            email=email,
            error=str(exc),
        )
        return False

    if success:
        logger.info(
            "auth.verification_email.sent",
            user_id=str(user.id),
            email=email,
        )
    else:
        logger.warning(
            "auth.verification_email.failed",
            user_id=str(user.id),
            email=email,
        )

    return success

"""
Production-ready authentication repository.
Handles all authentication-related data operations.
"""


from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, desc, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.core.enhanced.exceptions import (

    EntityNotFoundError,
    ValidationError,
)
from dotmac.platform.observability.unified_logging import get_logger


from ..models.auth_models import (
    AuthAuditModel,
    PasswordHistoryModel,
    UserApiKeyModel,
    UserMFAModel,
    UserPasswordModel,
    UserSessionModel,
)
from ..schemas.auth_schemas import AuthProvider, SessionType
from .base_repository import BaseRepository

logger = get_logger(__name__)

class AuthRepository(BaseRepository[AuthAuditModel]):
    """Repository for authentication operations."""

    def __init__(self, db_session: AsyncSession, tenant_id: Optional[UUID] = None):
        super().__init__(db_session, AuthAuditModel, tenant_id)

    # === Password Management ===

    async def store_user_password(
        self, user_id: UUID, password_hash: str, algorithm: str = "bcrypt"
    ) -> UserPasswordModel:
        """Store or update user password."""
        try:
            # Check for existing password
            query = select(UserPasswordModel).where(UserPasswordModel.user_id == user_id)
            result = await self.db.execute(query)
            password_record = result.scalar_one_or_none()

            if password_record:
                # Archive current password to history
                await self._archive_password(password_record)

                # Update existing record
                password_record.password_hash = password_hash
                password_record.algorithm = algorithm
                password_record.updated_at = datetime.now(timezone.utc)
                password_record.must_change = False
                password_record.is_temporary = False

            else:
                # Create new password record
                password_record = UserPasswordModel(
                    user_id=user_id, password_hash=password_hash, algorithm=algorithm
                )
                self.db.add(password_record)

            await self.db.commit()
            await self.db.refresh(password_record)

            logger.info(f"Password stored for user: {user_id}")
            return password_record

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to store password for user {user_id}: {e}")
            raise ValidationError(f"Failed to store password: {str(e)}") from e

    async def get_user_password(self, user_id: UUID) -> Optional[UserPasswordModel]:
        """Get user password record."""
        query = select(UserPasswordModel).where(UserPasswordModel.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def verify_password_not_reused(
        self, user_id: UUID, password_hash: str, history_limit: int = 5
    ) -> bool:
        """Verify password hasn't been used recently."""
        query = (
            select(PasswordHistoryModel.password_hash)
            .where(PasswordHistoryModel.user_id == user_id)
            .order_by(desc(PasswordHistoryModel.created_at))
            .limit(history_limit)
        )

        result = await self.db.execute(query)
        historical_hashes = [row[0] for row in result.fetchall()]

        # In production, you'd use proper password verification
        return password_hash not in historical_hashes

    async def _archive_password(self, password_record: UserPasswordModel) -> None:
        """Archive current password to history."""
        history_entry = PasswordHistoryModel(
            user_id=password_record.user_id,
            password_id=password_record.id,
            password_hash=password_record.password_hash,
            algorithm=password_record.algorithm,
            change_reason="password_update",
        )

        self.db.add(history_entry)

        # Clean up old history (keep only last 10)
        old_history_query = (
            select(PasswordHistoryModel.id)
            .where(PasswordHistoryModel.user_id == password_record.user_id)
            .order_by(desc(PasswordHistoryModel.created_at))
            .offset(10)
        )

        old_history_result = await self.db.execute(old_history_query)
        old_ids = [row[0] for row in old_history_result.fetchall()]

        if old_ids:
            delete_query = (
                update(PasswordHistoryModel)
                .where(PasswordHistoryModel.id.in_(old_ids))
                .values(is_active=False)
            )
            await self.db.execute(delete_query)

    # === Reset Token Management ===

    async def generate_password_reset_token(self, user_id: UUID, expires_in_hours: int = 24) -> str:
        """Generate password reset token."""
        password_record = await self.get_user_password(user_id)
        if not password_record:
            raise EntityNotFoundError(f"No password record found for user: {user_id}")

        # Clear any existing reset token
        password_record.reset_token = None
        password_record.reset_token_expires = None
        password_record.reset_attempts = 0

        # Generate new token
        import secrets

        token = secrets.token_urlsafe(32)
        password_record.reset_token = token
        password_record.reset_token_expires = datetime.now(timezone.utc) + timedelta(
            hours=expires_in_hours
        )

        await self.db.commit()

        logger.info(f"Password reset token generated for user: {user_id}")
        return token

    async def validate_reset_token(self, token: str) -> Optional[UUID]:
        """Validate password reset token and return user ID."""
        query = (
            select(UserPasswordModel)
            .where(UserPasswordModel.reset_token == token)
            .where(UserPasswordModel.reset_token_expires > datetime.now(timezone.utc))
        )

        result = await self.db.execute(query)
        password_record = result.scalar_one_or_none()

        if password_record:
            return password_record.user_id

        return None

    async def clear_reset_token(self, user_id: UUID) -> None:
        """Clear password reset token."""
        password_record = await self.get_user_password(user_id)
        if password_record:
            password_record.reset_token = None
            password_record.reset_token_expires = None
            password_record.reset_attempts = 0
            await self.db.commit()

class SessionRepository(BaseRepository[UserSessionModel]):
    """Repository for session management."""

    def __init__(self, db_session: AsyncSession, tenant_id: Optional[UUID] = None):
        super().__init__(db_session, UserSessionModel, tenant_id)

    async def create_session(
        self,
        user_id: UUID,
        session_token: str,
        session_type: SessionType = SessionType.WEB,
        auth_provider: AuthProvider = AuthProvider.LOCAL,
        expires_at: Optional[datetime] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
    ) -> UserSessionModel:
        """Create new user session."""

        if not expires_at:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=8)

        session = UserSessionModel(
            user_id=user_id,
            session_token=session_token,
            session_type=session_type,
            auth_provider=auth_provider,
            expires_at=expires_at,
            client_ip=client_ip,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        logger.info(f"Session created for user: {user_id}, session: {session.id}")
        return session

    async def get_active_session(self, session_token: str) -> Optional[UserSessionModel]:
        """Get active session by token."""
        query = (
            select(UserSessionModel)
            .where(UserSessionModel.session_token == session_token)
            .where(UserSessionModel.is_active is True)
            .where(UserSessionModel.expires_at > datetime.now(timezone.utc))
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_sessions(
        self, user_id: UUID, active_only: bool = True
    ) -> list[UserSessionModel]:
        """Get all sessions for a user."""
        query = select(UserSessionModel).where(UserSessionModel.user_id == user_id)

        if active_only:
            query = query.where(UserSessionModel.is_active is True)
            query = query.where(UserSessionModel.expires_at > datetime.now(timezone.utc))

        query = query.order_by(desc(UserSessionModel.created_at))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_session_activity(self, session_token: str) -> bool:
        """Update session last activity."""
        query = (
            update(UserSessionModel)
            .where(UserSessionModel.session_token == session_token)
            .where(UserSessionModel.is_active is True)
            .values(last_activity=datetime.now(timezone.utc))
        )

        result = await self.db.execute(query)
        await self.db.commit()

        return result.rowcount > 0

    async def terminate_session(self, session_token: str, reason: str = "logout") -> bool:
        """Terminate a specific session."""
        query = (
            update(UserSessionModel)
            .where(UserSessionModel.session_token == session_token)
            .values(
                is_active=False,
                terminated_at=datetime.now(timezone.utc),
                termination_reason=reason,
            )
        )

        result = await self.db.execute(query)
        await self.db.commit()

        return result.rowcount > 0

    async def terminate_user_sessions(
        self,
        user_id: UUID,
        exclude_session_id: Optional[UUID] = None,
        reason: str = "admin_action",
    ) -> int:
        """Terminate all sessions for a user."""
        query = (
            update(UserSessionModel)
            .where(UserSessionModel.user_id == user_id)
            .where(UserSessionModel.is_active is True)
        )

        if exclude_session_id:
            query = query.where(UserSessionModel.id != exclude_session_id)

        query = query.values(
            is_active=False,
            terminated_at=datetime.now(timezone.utc),
            termination_reason=reason,
        )

        result = await self.db.execute(query)
        await self.db.commit()

        terminated_count = result.rowcount
        logger.info(f"Terminated {terminated_count} sessions for user: {user_id}")

        return terminated_count

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        query = (
            update(UserSessionModel)
            .where(UserSessionModel.expires_at < datetime.now(timezone.utc))
            .where(UserSessionModel.is_active is True)
            .values(
                is_active=False,
                terminated_at=datetime.now(timezone.utc),
                termination_reason="expired",
            )
        )

        result = await self.db.execute(query)
        await self.db.commit()

        cleaned_count = result.rowcount
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} expired sessions")

        return cleaned_count

class MFARepository(BaseRepository[UserMFAModel]):
    """Repository for MFA management."""

    def __init__(self, db_session: AsyncSession, tenant_id: Optional[UUID] = None):
        super().__init__(db_session, UserMFAModel, tenant_id)

    async def get_user_mfa_methods(self, user_id: UUID) -> list[UserMFAModel]:
        """Get all MFA methods for user."""
        query = (
            select(UserMFAModel)
            .where(UserMFAModel.user_id == user_id)
            .where(UserMFAModel.is_enabled is True)
            .order_by(UserMFAModel.is_primary.desc(), UserMFAModel.created_at)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_primary_mfa_method(self, user_id: UUID) -> Optional[UserMFAModel]:
        """Get primary MFA method for user."""
        query = (
            select(UserMFAModel)
            .where(UserMFAModel.user_id == user_id)
            .where(UserMFAModel.is_primary is True)
            .where(UserMFAModel.is_enabled is True)
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def setup_mfa_method(
        self,
        user_id: UUID,
        method: str,
        secret: Optional[str] = None,
        phone_number: Optional[str] = None,
        email: Optional[str] = None,
        is_primary: bool = False,
    ) -> UserMFAModel:
        """Set up new MFA method for user."""

        # If setting as primary, unset other primary methods
        if is_primary:
            query = (
                update(UserMFAModel)
                .where(UserMFAModel.user_id == user_id)
                .where(UserMFAModel.is_primary is True)
                .values(is_primary=False)
            )
            await self.db.execute(query)

        # Create new MFA method
        mfa_method = UserMFAModel(
            user_id=user_id,
            method=method,
            secret=secret,
            phone_number=phone_number,
            email=email,
            is_primary=is_primary,
            is_enabled=True,
            is_verified=False,
        )

        self.db.add(mfa_method)
        await self.db.commit()
        await self.db.refresh(mfa_method)

        logger.info(f"MFA method {method} set up for user: {user_id}")
        return mfa_method

    async def verify_mfa_method(self, mfa_id: UUID) -> UserMFAModel:
        """Mark MFA method as verified."""
        mfa_method = await self.get_by_id_or_raise(mfa_id)

        mfa_method.is_verified = True
        mfa_method.verified_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(mfa_method)

        return mfa_method

    async def record_mfa_usage(self, mfa_id: UUID, success: bool) -> UserMFAModel:
        """Record MFA usage."""
        mfa_method = await self.get_by_id_or_raise(mfa_id)

        if success:
            mfa_method.record_success()
        else:
            mfa_method.record_failure()

        await self.db.commit()
        await self.db.refresh(mfa_method)

        return mfa_method

class ApiKeyRepository(BaseRepository[UserApiKeyModel]):
    """Repository for API key management."""

    def __init__(self, db_session: AsyncSession, tenant_id: Optional[UUID] = None):
        super().__init__(db_session, UserApiKeyModel, tenant_id)

    async def create_api_key(
        self,
        user_id: UUID,
        name: str,
        key_hash: str,
        key_prefix: str,
        permissions: Optional[list[str]] = None,
        expires_at: Optional[datetime] = None,
    ) -> UserApiKeyModel:
        """Create new API key."""

        # Generate unique key ID
        import secrets

        key_id = secrets.token_urlsafe(16)

        api_key = UserApiKeyModel(
            user_id=user_id,
            key_id=key_id,
            name=name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            permissions=permissions or [],
            expires_at=expires_at,
        )

        self.db.add(api_key)
        await self.db.commit()
        await self.db.refresh(api_key)

        logger.info(f"API key created for user: {user_id}, key_id: {key_id}")
        return api_key

    async def get_by_key_id(self, key_id: str) -> Optional[UserApiKeyModel]:
        """Get API key by key ID."""
        query = select(UserApiKeyModel).where(UserApiKeyModel.key_id == key_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_api_keys(self, user_id: UUID) -> list[UserApiKeyModel]:
        """Get all API keys for user."""
        query = (
            select(UserApiKeyModel)
            .where(UserApiKeyModel.user_id == user_id)
            .where(UserApiKeyModel.is_active is True)
            .order_by(desc(UserApiKeyModel.created_at))
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def record_api_key_usage(
        self,
        key_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """Record API key usage."""
        api_key = await self.get_by_key_id(key_id)
        if not api_key or not api_key.is_valid:
            return False

        api_key.record_usage(ip_address, user_agent)
        await self.db.commit()

        return True

    async def revoke_api_key(self, key_id: str) -> bool:
        """Revoke API key."""
        api_key = await self.get_by_key_id(key_id)
        if not api_key:
            return False

        api_key.revoke()
        await self.db.commit()

        logger.info(f"API key revoked: {key_id}")
        return True

class AuthAuditRepository(BaseRepository[AuthAuditModel]):
    """Repository for authentication audit logging."""

    def __init__(self, db_session: AsyncSession, tenant_id: Optional[UUID] = None):
        super().__init__(db_session, AuthAuditModel, tenant_id)

    async def log_auth_event(
        self,
        event_type: str,
        success: bool,
        user_id: Optional[UUID] = None,
        username: Optional[str] = None,
        email: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        auth_provider: AuthProvider = AuthProvider.LOCAL,
        failure_reason: Optional[str] = None,
        mfa_method: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> AuthAuditModel:
        """Log authentication event."""

        audit_event = AuthAuditModel(
            user_id=user_id,
            username=username,
            email=email,
            event_type=event_type,
            success=success,
            failure_reason=failure_reason,
            session_id=session_id,
            auth_provider=auth_provider,
            client_ip=client_ip,
            user_agent=user_agent,
            mfa_method=mfa_method,
            metadata=metadata or {},
        )

        self.db.add(audit_event)
        await self.db.commit()
        await self.db.refresh(audit_event)

        return audit_event

    async def get_user_auth_history(
        self, user_id: UUID, limit: int = 50, event_types: Optional[list[str]] = None
    ) -> list[AuthAuditModel]:
        """Get authentication history for user."""
        query = select(AuthAuditModel).where(AuthAuditModel.user_id == user_id)

        if event_types:
            query = query.where(AuthAuditModel.event_type.in_(event_types))

        query = query.order_by(desc(AuthAuditModel.created_at)).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_failed_login_attempts(
        self,
        identifier: str,  # username or email
        since: Optional[datetime] = None,
        limit: int = 10,
    ) -> list[AuthAuditModel]:
        """Get recent failed login attempts for user."""
        if not since:
            since = datetime.now(timezone.utc) - timedelta(hours=24)

        query = (
            select(AuthAuditModel)
            .where(
                or_(
                    AuthAuditModel.username == identifier,
                    AuthAuditModel.email == identifier,
                )
            )
            .where(AuthAuditModel.event_type == "login")
            .where(AuthAuditModel.success is False)
            .where(AuthAuditModel.created_at >= since)
            .order_by(desc(AuthAuditModel.created_at))
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_suspicious_activity(
        self, since: Optional[datetime] = None, limit: int = 100
    ) -> list[AuthAuditModel]:
        """Get potentially suspicious authentication activity."""
        if not since:
            since = datetime.now(timezone.utc) - timedelta(hours=24)

        # Look for patterns that might indicate suspicious activity
        query = (
            select(AuthAuditModel)
            .where(AuthAuditModel.created_at >= since)
            .where(
                or_(
                    # Multiple failed attempts
                    and_(
                        AuthAuditModel.event_type == "login",
                        AuthAuditModel.success is False,
                    ),
                    # Password reset attempts
                    AuthAuditModel.event_type == "password_reset",
                    # MFA failures
                    and_(
                        AuthAuditModel.event_type == "mfa_verify",
                        AuthAuditModel.success is False,
                    ),
                )
            )
            .order_by(desc(AuthAuditModel.created_at))
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

__all__ = [
    "AuthRepository",
    "SessionRepository",
    "MFARepository",
    "ApiKeyRepository",
    "AuthAuditRepository",
]

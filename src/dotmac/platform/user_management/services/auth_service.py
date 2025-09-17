"""
Authentication service layer for user management v2 system.
Provides comprehensive authentication workflows including login, logout, MFA, and session management.
"""

# Moved to top: import base64
import base64
import os
import secrets
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import Any, Optional
from uuid import UUID

import pyotp

# Moved to top: import pyotp
import qrcode
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.core.decorators import standard_exception_handler
from dotmac.platform.observability.logging import get_logger
from dotmac.platform.observability.unified_logging import get_logger

from dotmac.platform.config.secure import get_config_manager

from ..repositories.auth_repository import (
    ApiKeyRepository,
    AuthAuditRepository,
    AuthRepository,
    MFARepository,
    SessionRepository,
)
from ..repositories.user_repository import UserRepository
from ..schemas.auth_schemas import (
    ApiKeyCreateSchema,
    ApiKeySchema,
    AuthAuditEventType,
    ChangePasswordSchema,
    LoginAttemptResult,
    MFASetupRequestSchema,
    MFASetupResponseSchema,
    SessionCreateSchema,
    SessionInfoSchema,
    SessionStatus,
)
from .base_service import BaseService

logger = get_logger(__name__)

class AuthService(BaseService):
    """Service for user authentication and authorization operations."""

    def __init__(self, db_session: AsyncSession, tenant_id: Optional[UUID] = None):
        super().__init__(db_session, tenant_id)
        self.auth_repo = AuthRepository(db_session, tenant_id)
        self.session_repo = SessionRepository(db_session, tenant_id)
        self.mfa_repo = MFARepository(db_session, tenant_id)
        self.api_key_repo = ApiKeyRepository(db_session, tenant_id)
        self.audit_repo = AuthAuditRepository(db_session, tenant_id)
        self.user_repo = UserRepository(db_session, tenant_id)

        # Security configuration
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.jwt_algorithm = "HS256"

        # Get JWT secret from secure configuration
        config_manager = get_config_manager()
        try:
            self.jwt_secret = config_manager.get_secret_sync(
                key="auth/jwt_secret",
                env_fallback="JWT_SECRET_KEY",
                required=True,
            )
        except Exception as e:
            self.jwt_secret = os.getenv("JWT_SECRET_KEY")
            if not self.jwt_secret:
                raise ValueError(
                    "JWT secret not available. Please set JWT_SECRET_KEY environment variable "
                    "or configure OpenBao with auth/jwt_secret_key"
                ) from e
        self.jwt_expiry_hours = 24
        self.session_timeout_minutes = 480
        self.max_failed_attempts = 5
        self.lockout_duration_minutes = 30

    @standard_exception_handler
    async def authenticate_user(
        self,
        username: str,
        password: str,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
    ) -> LoginAttemptResult:
        """
        Authenticate user credentials and create session.

        Args:
            username: Username or email
            password: Plain text password
            client_ip: Client IP address
            user_agent: User agent string
            device_fingerprint: Device fingerprint for security

        Returns:
            LoginAttemptResult with authentication status and tokens
        """
        logger.info(f"Authentication attempt for user: {username}")

        # Find user by username or email
        user = await self.user_repo.get_by_username_or_email(username)
        if not user:
            await self._log_auth_event(
                None,
                AuthAuditEventType.LOGIN_FAILED,
                {"reason": "user_not_found", "username": username},
                client_ip,
            )
            return LoginAttemptResult(
                success=False,
                error_code="INVALID_CREDENTIALS",
                message="Invalid username or password",
            )

        # Check account status
        if user.status != "active":
            await self._log_auth_event(
                user.id,
                AuthAuditEventType.LOGIN_FAILED,
                {"reason": "account_inactive", "status": user.status},
                client_ip,
            )
            return LoginAttemptResult(
                success=False,
                error_code="ACCOUNT_INACTIVE",
                message="Account is not active",
            )

        # Check account lockout
        if await self._is_account_locked(user.id):
            await self._log_auth_event(
                user.id,
                AuthAuditEventType.LOGIN_FAILED,
                {"reason": "account_locked"},
                client_ip,
            )
            return LoginAttemptResult(
                success=False,
                error_code="ACCOUNT_LOCKED",
                message="Account is temporarily locked due to too many failed attempts",
            )

        # Verify password
        user_password = await self.auth_repo.get_current_password(user.id)
        if not user_password or not self.pwd_context.verify(password, user_password.password_hash):
            await self._record_failed_attempt(user.id, client_ip)
            return LoginAttemptResult(
                success=False,
                error_code="INVALID_CREDENTIALS",
                message="Invalid username or password",
            )

        # Check if MFA is required
        mfa_settings = await self.mfa_repo.get_user_mfa_settings(user.id)
        if mfa_settings and mfa_settings.is_enabled:
            # Return partial success for MFA flow
            temp_token = self._generate_temp_token(user.id)
            return LoginAttemptResult(
                success=True,
                requires_mfa=True,
                temp_token=temp_token,
                user_id=user.id,
                message="MFA verification required",
            )

        # Create session and tokens
        session_data = SessionCreateSchema(
            user_id=user.id,
            client_ip=client_ip,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
        )

        session = await self.create_session(session_data)
        access_token = self._generate_access_token(user.id, session.id)
        refresh_token = self._generate_refresh_token(user.id, session.id)

        # Clear failed attempts on successful login
        await self._clear_failed_attempts(user.id)

        await self._log_auth_event(
            user.id,
            AuthAuditEventType.LOGIN_SUCCESS,
            {"session_id": str(session.id)},
            client_ip,
        )

        return LoginAttemptResult(
            success=True,
            user_id=user.id,
            session_id=session.id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=session.expires_at,
            message="Authentication successful",
        )

    @standard_exception_handler
    async def verify_mfa_and_complete_login(
        self,
        temp_token: str,
        mfa_code: str,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
    ) -> LoginAttemptResult:
        """
        Verify MFA code and complete login process.

        Args:
            temp_token: Temporary token from initial authentication
            mfa_code: MFA verification code
            client_ip: Client IP address
            user_agent: User agent string
            device_fingerprint: Device fingerprint

        Returns:
            LoginAttemptResult with final authentication status
        """
        try:
            # Verify temp token
            payload = jwt.decode(temp_token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            user_id = UUID(payload.get("user_id"))
            token_type = payload.get("type")  # noqa: S105 - token classification, not a secret

            if token_type != "temp_mfa":
                raise JWTError("Invalid token type")

        except JWTError:
            return LoginAttemptResult(
                success=False,
                error_code="INVALID_TOKEN",
                message="Invalid or expired temporary token",
            )

        # Verify MFA code
        mfa_valid = await self.verify_mfa_code(user_id, mfa_code)
        if not mfa_valid:
            await self._log_auth_event(
                user_id,
                AuthAuditEventType.MFA_FAILED,
                {"reason": "invalid_code"},
                client_ip,
            )
            return LoginAttemptResult(
                success=False, error_code="INVALID_MFA_CODE", message="Invalid MFA code"
            )

        # Create session and tokens
        session_data = SessionCreateSchema(
            user_id=user_id,
            client_ip=client_ip,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
        )

        session = await self.create_session(session_data)
        access_token = self._generate_access_token(user_id, session.id)
        refresh_token = self._generate_refresh_token(user_id, session.id)

        await self._log_auth_event(
            user_id,
            AuthAuditEventType.LOGIN_SUCCESS,
            {"session_id": str(session.id), "mfa_verified": True},
            client_ip,
        )

        return LoginAttemptResult(
            success=True,
            user_id=user_id,
            session_id=session.id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=session.expires_at,
            message="MFA verification successful",
        )

    @standard_exception_handler
    async def logout_user(self, session_id: UUID, client_ip: Optional[str] = None) -> bool:
        """
        Logout user and invalidate session.

        Args:
            session_id: Session ID to invalidate
            client_ip: Client IP address

        Returns:
            True if logout successful
        """
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            return False

        # Invalidate session
        await self.session_repo.update(
            session_id,
            status=SessionStatus.LOGGED_OUT,
            ended_at=datetime.now(timezone.utc),
        )

        await self._log_auth_event(
            session.user_id,
            AuthAuditEventType.LOGOUT,
            {"session_id": str(session_id)},
            client_ip,
        )

        logger.info(f"User {session.user_id} logged out, session {session_id} invalidated")
        return True

    @standard_exception_handler
    async def create_session(self, session_data: SessionCreateSchema) -> SessionInfoSchema:
        """
        Create new user session.

        Args:
            session_data: Session creation data

        Returns:
            Created session information
        """
        # Generate session token
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.session_timeout_minutes)

        session = await self.session_repo.create_session(
            user_id=session_data.user_id,
            session_token=session_token,
            client_ip=session_data.client_ip,
            user_agent=session_data.user_agent,
            device_fingerprint=session_data.device_fingerprint,
            expires_at=expires_at,
        )

        return SessionInfoSchema.model_validate(session)

    @standard_exception_handler
    async def refresh_token(self, refresh_token: str) -> Optional[tuple[str, str]]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            Tuple of (new_access_token, new_refresh_token) or None if invalid
        """
        try:
            payload = jwt.decode(refresh_token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            user_id = UUID(payload.get("user_id"))
            session_id = UUID(payload.get("session_id"))
            token_type = payload.get("type")  # noqa: S105 - token classification, not a secret

            if token_type != "refresh":
                raise JWTError("Invalid token type")

        except JWTError:
            return None

        # Verify session is still valid
        session = await self.session_repo.get_active_session(session_id)
        if not session or session.user_id != user_id:
            return None

        # Generate new tokens
        new_access_token = self._generate_access_token(user_id, session_id)
        new_refresh_token = self._generate_refresh_token(user_id, session_id)

        # Update session last activity
        await self.session_repo.update_last_activity(session_id)

        return (new_access_token, new_refresh_token)

    @standard_exception_handler
    async def setup_mfa(
        self, user_id: UUID, request: MFASetupRequestSchema
    ) -> MFASetupResponseSchema:
        """
        Setup MFA for user account.

        Args:
            user_id: User ID
            request: MFA setup request data

        Returns:
            MFA setup response with QR code and backup codes
        """
        # Generate TOTP secret
        secret = pyotp.random_base32()

        # Create provisioning URI for QR code
        user = await self.user_repo.get_by_id(user_id)
        provisioning_uri = pyotp.TOTP(secret).provisioning_uri(
            name=user.email, issuer_name="DotMac"
        )

        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        qr_image = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = BytesIO()
        qr_image.save(qr_buffer, format="PNG")
        qr_code_base64 = base64.b64encode(qr_buffer.getvalue()).decode()

        # Generate backup codes
        backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]

        # Store MFA settings (not enabled yet)
        mfa_settings = await self.mfa_repo.setup_mfa(
            user_id=user_id,
            mfa_type=request.mfa_type,
            secret=secret,
            backup_codes=backup_codes,
            is_enabled=False,  # Will be enabled after verification
        )

        return MFASetupResponseSchema(
            mfa_id=mfa_settings.id,
            qr_code=f"data:image/png;base64,{qr_code_base64}",
            manual_entry_key=secret,
            backup_codes=backup_codes,
            message="Please verify MFA setup by entering a code from your authenticator app",
        )

    @standard_exception_handler
    async def verify_mfa_setup(self, user_id: UUID, mfa_code: str) -> bool:
        """
        Verify MFA setup with code from authenticator app.

        Args:
            user_id: User ID
            mfa_code: MFA code to verify

        Returns:
            True if verification successful
        """
        mfa_settings = await self.mfa_repo.get_user_mfa_settings(user_id)
        if not mfa_settings:
            return False

        # Verify TOTP code
        totp = pyotp.TOTP(mfa_settings.secret)
        if not totp.verify(mfa_code, valid_window=1):
            return False

        # Enable MFA
        await self.mfa_repo.enable_mfa(user_id)

        await self._log_auth_event(user_id, AuthAuditEventType.MFA_ENABLED, {})

        return True

    @standard_exception_handler
    async def verify_mfa_code(self, user_id: UUID, mfa_code: str) -> bool:
        """
        Verify MFA code for login.

        Args:
            user_id: User ID
            mfa_code: MFA code to verify

        Returns:
            True if code is valid
        """
        mfa_settings = await self.mfa_repo.get_user_mfa_settings(user_id)
        if not mfa_settings or not mfa_settings.is_enabled:
            return False

        # Check if it's a backup code
        if mfa_code.upper() in mfa_settings.backup_codes:
            # Remove used backup code
            await self.mfa_repo.use_backup_code(user_id, mfa_code.upper())
            return True

        # Verify TOTP code
        totp = pyotp.TOTP(mfa_settings.secret)
        return totp.verify(mfa_code, valid_window=1)

    @standard_exception_handler
    async def change_password(
        self,
        user_id: UUID,
        request: ChangePasswordSchema,
        client_ip: Optional[str] = None,
    ) -> bool:
        """
        Change user password.

        Args:
            user_id: User ID
            request: Password change request
            client_ip: Client IP address

        Returns:
            True if password changed successfully
        """
        # Verify current password
        current_password = await self.auth_repo.get_current_password(user_id)
        if not current_password or not self.pwd_context.verify(
            request.current_password, current_password.password_hash
        ):
            await self._log_auth_event(
                user_id,
                AuthAuditEventType.PASSWORD_CHANGE_FAILED,
                {"reason": "invalid_current_password"},
                client_ip,
            )
            return False

        # Hash new password
        new_password_hash = self.pwd_context.hash(request.new_password)

        # Store new password
        await self.auth_repo.store_user_password(user_id, new_password_hash)

        # Invalidate all sessions except current one if provided
        if request.keep_current_session and request.current_session_id:
            await self.session_repo.invalidate_all_sessions_except(
                user_id, request.current_session_id
            )
        else:
            await self.session_repo.invalidate_all_sessions(user_id)

        await self._log_auth_event(user_id, AuthAuditEventType.PASSWORD_CHANGED, {}, client_ip)

        return True

    @standard_exception_handler
    async def create_api_key(self, user_id: UUID, request: ApiKeyCreateSchema) -> ApiKeySchema:
        """
        Create API key for user.

        Args:
            user_id: User ID
            request: API key creation request

        Returns:
            Created API key information
        """
        # Generate API key
        api_key = f"dmac_{secrets.token_urlsafe(32)}"
        key_hash = self.pwd_context.hash(api_key)

        expires_at = None
        if request.expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=request.expires_in_days)

        # Store API key
        api_key_record = await self.api_key_repo.create_api_key(
            user_id=user_id,
            name=request.name,
            key_hash=key_hash,
            expires_at=expires_at,
            permissions=request.permissions,
        )

        await self._log_auth_event(
            user_id,
            AuthAuditEventType.API_KEY_CREATED,
            {"api_key_id": str(api_key_record.id), "name": request.name},
        )

        return ApiKeySchema(
            key_id=str(api_key_record.id),
            name=api_key_record.name,
            prefix=api_key[:12],  # First 12 characters for identification
            permissions=api_key_record.permissions,
            expires_at=api_key_record.expires_at,
            created_at=api_key_record.created_at,
        )

    def _generate_access_token(self, user_id: UUID, session_id: UUID) -> str:
        """Generate JWT access token."""
        payload = {
            "user_id": str(user_id),
            "session_id": str(session_id),
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(hours=self.jwt_expiry_hours),
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    def _generate_refresh_token(self, user_id: UUID, session_id: UUID) -> str:
        """Generate JWT refresh token."""
        payload = {
            "user_id": str(user_id),
            "session_id": str(session_id),
            "type": "refresh",
            "exp": datetime.now(timezone.utc) + timedelta(days=30),
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    def _generate_temp_token(self, user_id: UUID) -> str:
        """Generate temporary token for MFA flow."""
        payload = {
            "user_id": str(user_id),
            "type": "temp_mfa",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    async def _is_account_locked(self, user_id: UUID) -> bool:
        """Check if account is locked due to failed attempts."""
        return await self.auth_repo.is_account_locked(
            user_id, self.max_failed_attempts, self.lockout_duration_minutes
        )

    async def _record_failed_attempt(self, user_id: UUID, client_ip: Optional[str] = None):
        """Record failed login attempt."""
        await self._log_auth_event(
            user_id,
            AuthAuditEventType.LOGIN_FAILED,
            {"reason": "invalid_password"},
            client_ip,
        )

    async def _clear_failed_attempts(self, user_id: UUID):
        """Clear failed login attempts after successful login."""
        await self.auth_repo.clear_failed_attempts(user_id)

    async def _log_auth_event(
        self,
        user_id: Optional[UUID],
        event_type: AuthAuditEventType,
        event_data: dict[str, Any],
        client_ip: Optional[str] = None,
    ):
        """Log authentication event for audit trail."""
        await self.audit_repo.log_event(
            user_id=user_id,
            event_type=event_type,
            event_data=event_data,
            client_ip=client_ip,
        )

"""
Production-ready service layer for user management.
Implements comprehensive business logic and workflows.
"""

from .auth_service import (
    AuthService,
    access_token,
    api_key,
    api_key_record,
    backup_codes,
    current_password,
    expires_at,
    key_hash,
    logger,
    mfa_settings,
    mfa_valid,
    new_access_token,
    new_password_hash,
    new_refresh_token,
    payload,
    provisioning_uri,
    qr,
    qr_buffer,
    qr_code_base64,
    qr_image,
    refresh_token,
    secret,
    session,
    session_data,
    session_id,
    session_token,
    temp_token,
    token_type,
    totp,
    user,
    user_id,
    user_password,
)

# TODO: Fix star import - from .user_lifecycle_service import *
from .user_service import UserManagementService, UserProfileService, UserService

__all__ = [
    # Core services
    "UserService",
    "UserProfileService",
    "UserManagementService",
    # Authentication services
    "AuthService",
    "AuthenticationService",
    "SessionService",
    "MFAService",
    # Lifecycle services
    "UserLifecycleService",
    "UserActivationService",
    "UserInvitationService",
    # Base service
    "BaseUserService",
]

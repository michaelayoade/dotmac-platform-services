"""
Production-ready SQLAlchemy models for user management.
All models follow DRY patterns and production best practices.
"""

from .auth_models import (
    AuthAuditModel,
    PasswordHistoryModel,
    UserActivationModel,
    UserApiKeyModel,
    UserInvitationModel,
    UserMFAModel,
    UserPasswordModel,
    UserSessionModel,
)
from .rbac_models import (
    PermissionModel,
    RoleModel,
    RolePermissionModel,
    UserRoleModel,
)
from .user_models import (
    UserContactInfoModel,
    UserModel,
    UserPreferencesModel,
    UserProfileModel,
)

__all__ = [
    # Core user models
    "UserModel",
    "UserProfileModel",
    "UserPreferencesModel",
    "UserContactInfoModel",
    # Authentication models
    "UserPasswordModel",
    "UserSessionModel",
    "UserMFAModel",
    "UserApiKeyModel",
    "AuthAuditModel",
    # Role and permission models
    "RoleModel",
    "PermissionModel",
    "UserRoleModel",
    "RolePermissionModel",
    # Lifecycle and audit models
    "UserInvitationModel",
    "UserActivationModel",
    "AuthAuditModel",
    "PasswordHistoryModel",
]

"""
Enhanced JWT token generation with RBAC permissions
This module extends the existing JWT functionality to include permissions
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from uuid import UUID
import logging

import jwt
from jwt.exceptions import InvalidTokenError as JWTError
from sqlalchemy.orm import Session

from dotmac.platform.auth.core import JWTService
from dotmac.platform.auth.rbac_service import RBACService
from dotmac.platform.auth.exceptions import TokenExpired, InvalidToken
from dotmac.platform.settings import Settings
from dotmac.platform.user_management.models import User
from dotmac.platform.caching import cache_manager

logger = logging.getLogger(__name__)
settings = Settings()


class RBACTokenService:
    """Enhanced JWT service with RBAC permissions"""

    def __init__(self, jwt_service: JWTService, rbac_service: RBACService):
        self.jwt_service = jwt_service
        self.rbac_service = rbac_service

    async def create_access_token(
        self,
        user: User,
        db_session: Session,
        expires_delta: Optional[timedelta] = None,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create an access token with user permissions and roles
        """
        # Get user's permissions
        permissions = await self.rbac_service.get_user_permissions(user.id)

        # Get user's roles
        roles = await self.rbac_service.get_user_roles(user.id)
        role_names = [role.name for role in roles]

        # Build token claims
        claims = {
            "sub": str(user.id),
            "email": user.email,
            "username": user.username,
            "permissions": list(permissions),  # Convert set to list
            "roles": role_names,
            "tenant_id": str(user.tenant_id) if hasattr(user, 'tenant_id') and user.tenant_id else None,
        }

        # Add any additional claims
        if additional_claims:
            claims.update(additional_claims)

        # Set expiration
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)

        claims["exp"] = expire
        claims["iat"] = datetime.now(timezone.utc)
        claims["type"] = "access"

        # Create token
        token = self.jwt_service.create_token(claims)

        # Cache the token metadata for quick validation
        cache_key = f"token:{user.id}:{token[:20]}"  # Use first 20 chars as identifier
        await cache_manager.set(
            cache_key,
            {
                "user_id": str(user.id),
                "permissions": list(permissions),
                "roles": role_names,
                "expires_at": expire.isoformat()
            },
            expire=int(expires_delta.total_seconds() if expires_delta else settings.access_token_expire_minutes * 60)
        )

        logger.info(f"Created access token for user {user.id} with {len(permissions)} permissions and {len(role_names)} roles")
        return token

    async def create_refresh_token(
        self,
        user: User,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a refresh token (doesn't include permissions for security)
        """
        claims = {
            "sub": str(user.id),
            "type": "refresh"
        }

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)

        claims["exp"] = expire
        claims["iat"] = datetime.now(timezone.utc)

        return self.jwt_service.create_token(claims)

    async def verify_token_with_permissions(
        self,
        token: str,
        required_permissions: Optional[List[str]] = None,
        required_roles: Optional[List[str]] = None,
        require_all_permissions: bool = True
    ) -> Dict[str, Any]:
        """
        Verify token and check for required permissions/roles
        """
        # Verify the token signature and expiration
        try:
            payload = self.jwt_service.verify_token(token)
        except JWTError as e:
            logger.error(f"Token verification failed: {e}")
            raise InvalidToken("Invalid or expired token")

        # Check if it's an access token
        if payload.get("type") != "access":
            raise InvalidToken("Token is not an access token")

        # Check for required permissions
        if required_permissions:
            user_permissions = set(payload.get("permissions", []))

            if require_all_permissions:
                # User must have ALL required permissions
                missing = set(required_permissions) - user_permissions
                if missing:
                    logger.warning(f"User {payload.get('sub')} missing permissions: {missing}")
                    raise InvalidToken(f"Missing required permissions: {', '.join(missing)}")
            else:
                # User must have AT LEAST ONE required permission
                if not any(perm in user_permissions for perm in required_permissions):
                    raise InvalidToken(f"Requires at least one of: {', '.join(required_permissions)}")

        # Check for required roles
        if required_roles:
            user_roles = set(payload.get("roles", []))

            if not any(role in user_roles for role in required_roles):
                raise InvalidToken(f"Requires one of these roles: {', '.join(required_roles)}")

        return payload

    async def refresh_access_token(
        self,
        refresh_token: str,
        db_session: Session
    ) -> tuple[str, str]:
        """
        Use refresh token to get new access token with updated permissions
        """
        # Verify refresh token
        try:
            payload = self.jwt_service.verify_token(refresh_token)
        except JWTError:
            raise InvalidToken("Invalid refresh token")

        if payload.get("type") != "refresh":
            raise InvalidToken("Token is not a refresh token")

        # Get user
        user_id = UUID(payload["sub"])
        user = db_session.query(User).filter_by(id=user_id).first()

        if not user:
            raise InvalidToken("User not found")

        if not user.is_active:
            raise InvalidToken("User account is disabled")

        # Create new tokens with current permissions
        access_token = await self.create_access_token(user, db_session)
        new_refresh_token = await self.create_refresh_token(user)

        return access_token, new_refresh_token

    async def revoke_token(self, token: str) -> None:
        """
        Revoke a token by adding it to a blacklist
        """
        try:
            payload = self.jwt_service.verify_token(token)
            exp = payload.get("exp")

            if exp:
                # Calculate TTL for blacklist entry
                ttl = exp - datetime.now(timezone.utc).timestamp()
                if ttl > 0:
                    # Add to blacklist
                    await cache_manager.set(
                        f"blacklist:{token[:50]}",  # Use first 50 chars
                        True,
                        expire=int(ttl)
                    )
                    logger.info(f"Token revoked for user {payload.get('sub')}")
        except JWTError:
            pass  # Token is already invalid

    async def is_token_revoked(self, token: str) -> bool:
        """
        Check if token is in the blacklist
        """
        return await cache_manager.get(f"blacklist:{token[:50]}") is not None

    async def get_user_from_token(
        self,
        token: str,
        db_session: Session
    ) -> tuple[User, List[str], List[str]]:
        """
        Get user, permissions, and roles from token
        Returns: (user, permissions, roles)
        """
        payload = await self.verify_token_with_permissions(token)

        user_id = UUID(payload["sub"])
        user = db_session.query(User).filter_by(id=user_id).first()

        if not user:
            raise InvalidToken("User not found")

        permissions = payload.get("permissions", [])
        roles = payload.get("roles", [])

        return user, permissions, roles


# Factory function to create the service
def get_rbac_token_service(
    jwt_service: JWTService,
    rbac_service: RBACService
) -> RBACTokenService:
    """Factory function to create RBAC token service"""
    return RBACTokenService(jwt_service, rbac_service)
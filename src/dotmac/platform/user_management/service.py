"""
User management service.

Production-ready user service with proper database operations.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

import structlog
from passlib.context import CryptContext
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User

logger = structlog.get_logger(__name__)


class UserService:
    """Production user service with database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session
        # Configure password hashing
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def get_user_by_id(self, user_id: str | UUID) -> Optional[User]:
        """Get user by ID."""
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                return None

        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        result = await self.session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.session.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        roles: Optional[List[str]] = None,
        is_active: bool = True,
        tenant_id: Optional[str] = None,
    ) -> User:
        """Create a new user."""
        # Check if user exists
        existing = await self.get_user_by_username(username)
        if existing:
            raise ValueError(f"Username {username} already exists")

        existing = await self.get_user_by_email(email)
        if existing:
            raise ValueError(f"Email {email} already exists")

        # Hash password
        password_hash = self._hash_password(password)

        # Create user
        user = User(
            username=username,
            email=email.lower(),
            password_hash=password_hash,
            full_name=full_name,
            roles=roles or [],
            is_active=is_active,
            tenant_id=tenant_id,
        )

        self.session.add(user)

        try:
            await self.session.commit()
            await self.session.refresh(user)
            logger.info(f"Created user: {username} (ID: {user.id})")
            return user
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Failed to create user {username}: {e}")
            raise ValueError("User creation failed - username or email may already exist")

    async def update_user(
        self,
        user_id: str | UUID,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        roles: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        phone_number: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[User]:
        """Update user information."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        # Update fields if provided
        if email is not None:
            # Check if email is already taken
            existing = await self.get_user_by_email(email)
            if existing and existing.id != user.id:
                raise ValueError(f"Email {email} is already in use")
            user.email = email.lower()

        if full_name is not None:
            user.full_name = full_name
        if roles is not None:
            user.roles = roles
        if permissions is not None:
            user.permissions = permissions
        if is_active is not None:
            user.is_active = is_active
        if is_verified is not None:
            user.is_verified = is_verified
        if phone_number is not None:
            user.phone_number = phone_number
        if metadata is not None:
            user.metadata_ = metadata

        user.updated_at = datetime.now(timezone.utc)

        try:
            await self.session.commit()
            await self.session.refresh(user)
            logger.info(f"Updated user: {user.username} (ID: {user.id})")
            return user
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Failed to update user {user_id}: {e}")
            raise

    async def delete_user(self, user_id: str | UUID) -> bool:
        """Delete a user."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False

        await self.session.delete(user)
        await self.session.commit()
        logger.info(f"Deleted user: {user.username} (ID: {user.id})")
        return True

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        role: Optional[str] = None,
        tenant_id: Optional[str] = None,
        search: Optional[str] = None,
        require_tenant: bool = True,  # Default to requiring tenant for safety
    ) -> tuple[List[User], int]:
        """List users with pagination and filters."""
        # Enforce tenant isolation by default
        if require_tenant and (not tenant_id or not tenant_id.strip()):
            raise ValueError("tenant_id is required when require_tenant=True")

        query = select(User)

        # Apply filters
        conditions = []
        if is_active is not None:
            conditions.append(User.is_active == is_active)
        if role:
            conditions.append(func.jsonb_contains(User.roles, f'["{role}"]'))
        if tenant_id:
            conditions.append(User.tenant_id == tenant_id)
        if search:
            search_pattern = f"%{search}%"
            conditions.append(
                or_(
                    User.username.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.full_name.ilike(search_pattern),
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        # Get total count
        count_query = select(func.count()).select_from(User)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())

        # Execute query
        result = await self.session.execute(query)
        users = list(result.scalars().all())

        return users, total

    async def verify_password(self, user: User, password: str) -> bool:
        """Verify user password."""
        return self.pwd_context.verify(password, user.password_hash)

    async def change_password(
        self,
        user_id: str | UUID,
        current_password: str,
        new_password: str,
    ) -> bool:
        """Change user password."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False

        # Verify current password
        if not await self.verify_password(user, current_password):
            logger.warning(f"Invalid password attempt for user: {user.username}")
            return False

        # Update password
        user.password_hash = self._hash_password(new_password)
        user.updated_at = datetime.now(timezone.utc)

        await self.session.commit()
        logger.info(f"Password changed for user: {user.username}")
        return True

    async def authenticate(
        self,
        username_or_email: str,
        password: str,
    ) -> Optional[User]:
        """Authenticate user with username/email and password."""
        # Try to find user by username or email
        user = await self.get_user_by_username(username_or_email)
        if not user:
            user = await self.get_user_by_email(username_or_email)

        if not user:
            logger.debug(f"User not found: {username_or_email}")
            return None

        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            logger.warning(f"Account locked for user: {user.username}")
            return None

        # Verify password
        if not await self.verify_password(user, password):
            # Increment failed attempts
            user.failed_login_attempts += 1

            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.now(timezone.utc) + timedelta(hours=1)
                logger.warning(f"Account locked due to failed attempts: {user.username}")

            await self.session.commit()
            return None

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Inactive user login attempt: {user.username}")
            return None

        # Reset failed attempts
        user.failed_login_attempts = 0
        user.locked_until = None
        # Note: last_login is updated in the router after successful authentication

        await self.session.commit()
        logger.info(f"User authenticated: {user.username}")
        return user

    async def enable_mfa(self, user_id: str | UUID) -> str:
        """Enable MFA for user and return secret."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        # Generate MFA secret
        secret = secrets.token_hex(20)
        user.mfa_enabled = True
        user.mfa_secret = secret

        await self.session.commit()
        logger.info(f"MFA enabled for user: {user.username}")
        return secret

    async def disable_mfa(self, user_id: str | UUID) -> bool:
        """Disable MFA for user."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False

        user.mfa_enabled = False
        user.mfa_secret = None

        await self.session.commit()
        logger.info(f"MFA disabled for user: {user.username}")
        return True

    async def add_role(self, user_id: str | UUID, role: str) -> Optional[User]:
        """Add role to user."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        if role not in user.roles:
            user.roles = user.roles + [role]
            await self.session.commit()
            logger.info(f"Added role {role} to user: {user.username}")

        return user

    async def remove_role(self, user_id: str | UUID, role: str) -> Optional[User]:
        """Remove role from user."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        if role in user.roles:
            user.roles = [r for r in user.roles if r != role]
            await self.session.commit()
            logger.info(f"Removed role {role} from user: {user.username}")

        return user

    async def update_last_login(
        self,
        user_id: str | UUID,
        ip_address: Optional[str] = None
    ) -> Optional[User]:
        """Update user's last login timestamp and IP address.

        Args:
            user_id: The user ID to update
            ip_address: Optional IP address of the login

        Returns:
            Updated user object or None if user not found
        """
        from datetime import datetime, timezone

        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        # Update last login fields
        user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)
        if ip_address:
            user.last_login_ip = ip_address

        await self.session.commit()
        logger.info(f"Updated last login for user: {user.username}")

        return user

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt via passlib."""
        return self.pwd_context.hash(password)

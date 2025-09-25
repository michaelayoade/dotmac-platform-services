"""
Authentication router for FastAPI.

Provides login, register, token refresh endpoints.
"""

from datetime import datetime, timedelta
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.core import (
    UserInfo,
    hash_password,
    verify_password,
    jwt_service,
    session_manager,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    DEFAULT_USER_ROLE,
)
from dotmac.platform.auth.email_service import get_auth_email_service
from dotmac.platform.db import get_session_dependency
from dotmac.platform.rate_limiting import rate_limit
from dotmac.platform.user_management.models import User
from dotmac.platform.user_management.service import UserService

logger = structlog.get_logger(__name__)

# ========================================
# Local dependency wrappers
# ========================================


async def get_auth_session():
    """Adapter to reuse the shared session dependency helper."""
    async for session in get_session_dependency():
        yield session


# Backwards compatibility: some tests patch this symbol directly
async def get_async_session():  # pragma: no cover - compatibility wrapper
    async for session in get_session_dependency():
        yield session


# Create router
auth_router = APIRouter()
security = HTTPBearer()


# Request/Response Models
class LoginRequest(BaseModel):
    """Login request model."""

    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class RegisterRequest(BaseModel):
    """Registration request model."""

    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password")
    full_name: Optional[str] = Field(None, description="Full name")


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str = Field(..., description="Access token")
    refresh_token: str = Field(..., description="Refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""

    refresh_token: str = Field(..., description="Refresh token")


class PasswordResetRequest(BaseModel):
    """Password reset request model."""

    email: EmailStr = Field(..., description="Email address")


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model."""

    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=8, description="New password")


@auth_router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_auth_session),
) -> TokenResponse:
    """
    Authenticate user and return JWT tokens.

    The username field accepts either username or email.
    """
    user_service = UserService(session)

    # Try to find user by username or email
    user = await user_service.get_user_by_username(request.username)
    if not user:
        user = await user_service.get_user_by_email(request.username)

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    # Update last login (skip for now as the service doesn't support it yet)
    # TODO: Implement last_login update in UserService

    # Create tokens
    access_token = jwt_service.create_access_token(
        subject=str(user.id),
        additional_claims={
            "username": user.username,
            "email": user.email,
            "roles": user.roles or [],
            "tenant_id": user.tenant_id,
        }
    )

    refresh_token = jwt_service.create_refresh_token(
        subject=str(user.id)
    )

    # Create session
    await session_manager.create_session(
        user_id=str(user.id),
        data={
            "username": user.username,
            "email": user.email,
            "roles": user.roles or [],
            "access_token": access_token,
        }
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@auth_router.post("/register", response_model=TokenResponse)
async def register(
    request: RegisterRequest,
    session: AsyncSession = Depends(get_auth_session),
) -> TokenResponse:
    """
    Register a new user and return JWT tokens.
    """
    user_service = UserService(session)

    # Check if user already exists - use generic error message to prevent enumeration
    existing_user_by_username = await user_service.get_user_by_username(request.username)
    existing_user_by_email = await user_service.get_user_by_email(request.email)

    if existing_user_by_username or existing_user_by_email:
        # Generic error message to prevent user enumeration
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed. Please check your input and try again.",
        )

    # Create new user with configurable default role
    try:
        new_user = await user_service.create_user(
            username=request.username,
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            roles=[DEFAULT_USER_ROLE],  # Use configurable default role
            is_active=True,
        )
    except Exception as e:
        logger.error("Failed to create user", exc_info=True)  # Use exc_info for safer logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )

    # Create tokens
    access_token = jwt_service.create_access_token(
        subject=str(new_user.id),
        additional_claims={
            "username": new_user.username,
            "email": new_user.email,
            "roles": new_user.roles or [],
            "tenant_id": new_user.tenant_id,
        }
    )

    refresh_token = jwt_service.create_refresh_token(
        subject=str(new_user.id)
    )

    # Create session
    await session_manager.create_session(
        user_id=str(new_user.id),
        data={
            "username": new_user.username,
            "email": new_user.email,
            "roles": new_user.roles or [],
            "access_token": access_token,
        }
    )

    # Send welcome email
    try:
        email_service = get_auth_email_service()
        email_service.send_welcome_email(
            email=new_user.email,
            user_name=new_user.full_name or new_user.username
        )
    except Exception as e:
        logger.warning("Failed to send welcome email", exc_info=True)
        # Don't fail registration if email fails

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    session: AsyncSession = Depends(get_auth_session),
) -> TokenResponse:
    """
    Refresh access token using refresh token.
    """
    try:
        # Verify refresh token
        payload = jwt_service.verify_token(request.refresh_token)

        # Check if it's actually a refresh token
        token_type = payload.get("type")
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type - refresh token required",
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        # Get user
        user_service = UserService(session)
        user = await user_service.get_user_by_id(user_id)

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or disabled",
            )

        # Revoke old refresh token
        try:
            await jwt_service.revoke_token(request.refresh_token)
        except Exception as e:
            logger.warning("Failed to revoke old refresh token", exc_info=True)

        # Create new tokens
        access_token = jwt_service.create_access_token(
            subject=str(user.id),
            additional_claims={
                "username": user.username,
                "email": user.email,
                "roles": user.roles or [],
                "tenant_id": user.tenant_id,
            }
        )

        new_refresh_token = jwt_service.create_refresh_token(
            subject=str(user.id)
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except Exception as e:
        logger.error("Token refresh failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )


@auth_router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Logout user and invalidate session and tokens.
    """
    token = credentials.credentials

    try:
        # Get user info from token
        payload = jwt_service.verify_token(token)
        user_id = payload.get("sub")

        if user_id:
            # Revoke the access token
            await jwt_service.revoke_token(token)

            # Delete all user sessions (which should include refresh tokens)
            deleted_sessions = await session_manager.delete_user_sessions(user_id)

            # Also explicitly revoke all refresh tokens for this user
            # This ensures refresh tokens can't be used after logout
            try:
                # Get all active sessions to find refresh tokens
                await jwt_service.revoke_user_tokens(user_id)
            except Exception as e:
                logger.warning("Failed to revoke user refresh tokens", exc_info=True)

            logger.info("User logged out successfully", user_id=user_id, sessions_deleted=deleted_sessions)
            return {
                "message": "Logged out successfully",
                "sessions_deleted": deleted_sessions
            }
        else:
            return {"message": "Logout completed"}
    except Exception as e:
        logger.error("Logout failed", exc_info=True)
        # Still try to revoke the token even if we can't parse it
        try:
            await jwt_service.revoke_token(token)
        except Exception:
            pass
        return {"message": "Logout completed"}


@auth_router.get("/verify")
async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Verify if the current token is valid.
    """
    token = credentials.credentials

    try:
        payload = jwt_service.verify_token(token)
        return {
            "valid": True,
            "user_id": payload.get("sub"),
            "username": payload.get("username"),
            "roles": payload.get("roles", []),
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


@auth_router.post("/password-reset")
async def request_password_reset(
    request: PasswordResetRequest,
    session: AsyncSession = Depends(get_auth_session),
) -> dict:
    """
    Request a password reset token to be sent via email.
    """
    user_service = UserService(session)

    # Find user by email
    user = await user_service.get_user_by_email(request.email)

    # Always return success to prevent email enumeration
    if user and user.is_active:
        try:
            email_service = get_auth_email_service()
            response, reset_token = email_service.send_password_reset_email(
                email=user.email,
                user_name=user.full_name or user.username
            )
            logger.info("Password reset requested", user_id=str(user.id))
        except Exception as e:
            logger.error("Failed to send password reset email", exc_info=True)

    return {"message": "If the email exists, a password reset link has been sent."}


@auth_router.post("/password-reset/confirm")
async def confirm_password_reset(
    request: PasswordResetConfirm,
    session: AsyncSession = Depends(get_auth_session),
) -> dict:
    """
    Confirm password reset with token and set new password.
    """
    email_service = get_auth_email_service()

    # Verify the reset token
    email = email_service.verify_reset_token(request.token)

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Find user and update password
    user_service = UserService(session)
    user = await user_service.get_user_by_email(email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    # Update password
    try:
        user.password_hash = hash_password(request.new_password)
        await session.commit()

        # Send confirmation email
        email_service.send_password_reset_success_email(
            email=user.email,
            user_name=user.full_name or user.username
        )

        logger.info("Password reset completed", user_id=str(user.id))
        return {"message": "Password has been reset successfully."}
    except Exception as e:
        logger.error("Failed to reset password", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password",
        )


@auth_router.get("/me")
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_auth_session),
) -> dict:
    """
    Get current user information from token.
    """
    token = credentials.credentials

    try:
        payload = jwt_service.verify_token(token)
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        user_service = UserService(session)
        user = await user_service.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "roles": user.roles or [],
            "is_active": user.is_active,
            "tenant_id": user.tenant_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get current user", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


# Export router
__all__ = ["auth_router"]

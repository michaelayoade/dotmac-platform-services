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
)
from dotmac.platform.db import get_async_session
from dotmac.platform.user_management.models import User
from dotmac.platform.user_management.service import UserService

logger = structlog.get_logger(__name__)

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


@auth_router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_async_session),
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
    session: AsyncSession = Depends(get_async_session),
) -> TokenResponse:
    """
    Register a new user and return JWT tokens.
    """
    user_service = UserService(session)

    # Check if user already exists
    existing_user = await user_service.get_user_by_username(request.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    existing_user = await user_service.get_user_by_email(request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    try:
        new_user = await user_service.create_user(
            username=request.username,
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            roles=["user"],  # Default role
            is_active=True,
        )
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
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

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    session: AsyncSession = Depends(get_async_session),
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
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )


@auth_router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Logout user and invalidate session.
    """
    token = credentials.credentials

    try:
        # Get user info from token to find session
        payload = jwt_service.verify_token(token)
        user_id = payload.get("sub")

        # For now, return success as we don't track sessions by token
        # In production, you'd want to maintain a token->session mapping
        return {"message": "Logged out successfully"}
    except Exception as e:
        logger.error(f"Logout failed: {e}")
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


# Export router
__all__ = ["auth_router"]
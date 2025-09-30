"""
Authentication router for FastAPI.

Provides login, register, token refresh endpoints.
"""

from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.core import (
    UserInfo,
    hash_password,
    verify_password,
    jwt_service,
    session_manager,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    DEFAULT_USER_ROLE,
)
from dotmac.platform.auth.email_service import get_auth_email_service
from dotmac.platform.db import get_session_dependency
from dotmac.platform.settings import settings
from dotmac.platform.user_management.service import UserService
from ..audit import log_user_activity, log_api_activity, ActivityType, ActivitySeverity

logger = structlog.get_logger(__name__)

# ========================================
# Cookie management helpers
# ========================================

def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """
    Set HttpOnly authentication cookies on the response.

    Args:
        response: FastAPI Response object
        access_token: JWT access token
        refresh_token: JWT refresh token
    """
    # Cookie settings - secure only in production (requires HTTPS)
    secure = settings.environment == "production"
    # Use 'lax' for development to allow cross-origin requests, 'strict' for production
    samesite = "strict" if settings.environment == "production" else "lax"

    # Set access token cookie (15 minutes)
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # 15 minutes in seconds
        httponly=True,
        secure=secure,
        samesite=samesite,
        path="/",
    )

    # Set refresh token cookie (7 days)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=7 * 24 * 60 * 60,  # 7 days in seconds
        httponly=True,
        secure=secure,
        samesite=samesite,
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    """
    Clear authentication cookies from the response.

    Args:
        response: FastAPI Response object
    """
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")


def get_token_from_cookie(request: Request, cookie_name: str) -> Optional[str]:
    """
    Extract token from HttpOnly cookie.

    Args:
        request: FastAPI Request object
        cookie_name: Name of the cookie (access_token or refresh_token)

    Returns:
        Token value or None if not found
    """
    return request.cookies.get(cookie_name)

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
security = HTTPBearer(auto_error=False)


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


class LoginSuccessResponse(BaseModel):
    """Cookie-based login success response."""

    success: bool = Field(default=True, description="Login successful")
    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    roles: list[str] = Field(default_factory=list, description="User roles")
    message: str = Field(default="Login successful", description="Success message")


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


async def _authenticate_and_issue_tokens(
    *,
    username: str,
    password: str,
    request: Request,
    response: Response,
    session: AsyncSession,
) -> TokenResponse:
    """Shared login flow used by both JSON and OAuth2 password endpoints."""
    user_service = UserService(session)

    # Try to find user by username or email
    user = await user_service.get_user_by_username(username)
    if not user:
        user = await user_service.get_user_by_email(username)

    if not user or not verify_password(password, user.password_hash):
        # Log failed login attempt
        await log_api_activity(
            request=request,
            action="login_failed",
            description=f"Failed login attempt for username: {username}",
            severity=ActivitySeverity.HIGH,
            details={"username": username, "reason": "invalid_credentials"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.is_active:
        # Log disabled account login attempt
        await log_user_activity(
            user_id=str(user.id),
            activity_type=ActivityType.USER_LOGIN,
            action="login_disabled_account",
            description=f"Login attempt on disabled account: {user.username}",
            severity=ActivitySeverity.HIGH,
            details={"username": user.username, "reason": "account_disabled"}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    # Update last login
    client_ip = request.client.host if request.client else None
    await user_service.update_last_login(user.id, ip_address=client_ip)

    # Create tokens
    access_token = jwt_service.create_access_token(
        subject=str(user.id),
        additional_claims={
            "username": user.username,
            "email": user.email,
            "roles": user.roles or [],
            "permissions": user.permissions or [],
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

    # Log successful login
    await log_user_activity(
        user_id=str(user.id),
        activity_type=ActivityType.USER_LOGIN,
        action="login_success",
        description=f"User {user.username} logged in successfully",
        severity=ActivitySeverity.LOW,
        details={
            "username": user.username,
            "email": user.email,
            "roles": user.roles or []
        },
        # Extract context from request
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        tenant_id=user.tenant_id
    )

    # Set HttpOnly authentication cookies
    set_auth_cookies(response, access_token, refresh_token)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@auth_router.post("/login", response_model=TokenResponse)
async def login(
    login_request: LoginRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_auth_session),
) -> TokenResponse:
    """
    Authenticate user and return JWT tokens.

    The username field accepts either username or email.
    """

    return await _authenticate_and_issue_tokens(
        username=login_request.username,
        password=login_request.password,
        request=request,
        response=response,
        session=session,
    )


@auth_router.post("/login/cookie", response_model=LoginSuccessResponse)
async def login_cookie_only(
    login_request: LoginRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_auth_session),
) -> LoginSuccessResponse:
    """
    Cookie-only authentication endpoint.

    Sets HttpOnly cookies for authentication without returning tokens in response body.
    This is more secure as tokens are not exposed to JavaScript.

    The username field accepts either username or email.
    """
    # Authenticate user
    user_service = UserService(session)
    user = await user_service.authenticate(
        username_or_email=login_request.username,
        password=login_request.password,
    )

    if not user:
        # Log failed attempt
        await log_user_activity(
            user_id="unknown",
            activity_type=ActivityType.USER_LOGIN,
            action="login_failed",
            description=f"Failed login attempt for: {login_request.username}",
            severity=ActivitySeverity.MEDIUM,
            details={"username": login_request.username, "reason": "invalid_credentials"},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    # Update last login
    client_ip = request.client.host if request.client else None
    await user_service.update_last_login(user.id, ip_address=client_ip)

    # Create tokens
    access_token = jwt_service.create_access_token(
        subject=str(user.id),
        additional_claims={
            "username": user.username,
            "email": user.email,
            "roles": user.roles or [],
            "permissions": user.permissions or [],
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
        }
    )

    # Set HttpOnly authentication cookies
    set_auth_cookies(response, access_token, refresh_token)

    # Log successful login
    await log_user_activity(
        user_id=str(user.id),
        activity_type=ActivityType.USER_LOGIN,
        action="login_success",
        description=f"User {user.username} logged in successfully (cookie-auth)",
        severity=ActivitySeverity.LOW,
        details={
            "username": user.username,
            "email": user.email,
            "roles": user.roles or [],
            "auth_method": "cookie"
        },
        ip_address=client_ip,
        user_agent=request.headers.get("user-agent"),
        tenant_id=user.tenant_id
    )

    # Return success response without tokens
    return LoginSuccessResponse(
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        roles=user.roles or []
    )


@auth_router.post("/token", response_model=TokenResponse)
async def issue_token(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_auth_session),
) -> TokenResponse:
    """OAuth2 password flow endpoint compatible with FastAPI's security utilities."""

    return await _authenticate_and_issue_tokens(
        username=form_data.username,
        password=form_data.password,
        request=request,
        response=response,
        session=session,
    )


@auth_router.post("/register", response_model=TokenResponse)
async def register(
    register_request: RegisterRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_auth_session),
) -> TokenResponse:
    """
    Register a new user and return JWT tokens.
    """
    user_service = UserService(session)

    # Check if user already exists - use generic error message to prevent enumeration
    existing_user_by_username = await user_service.get_user_by_username(register_request.username)
    existing_user_by_email = await user_service.get_user_by_email(register_request.email)

    if existing_user_by_username or existing_user_by_email:
        # Log registration attempt with existing user
        await log_api_activity(
            request=request,
            action="registration_failed",
            description=f"Registration attempt with existing credentials",
            severity=ActivitySeverity.MEDIUM,
            details={
                "username": register_request.username,
                "email": register_request.email,
                "reason": "user_already_exists"
            }
        )
        # Generic error message to prevent user enumeration
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed. Please check your input and try again.",
        )

    # Create new user with configurable default role
    try:
        new_user = await user_service.create_user(
            username=register_request.username,
            email=register_request.email,
            password=register_request.password,
            full_name=register_request.full_name,
            roles=[DEFAULT_USER_ROLE],  # Use configurable default role
            is_active=True,
        )
    except Exception as e:
        logger.error("Failed to create user", exc_info=True)  # Use exc_info for safer logging
        await log_api_activity(
            request=request,
            action="registration_failed",
            description=f"Registration failed during user creation",
            severity=ActivitySeverity.HIGH,
            details={
                "username": register_request.username,
                "email": register_request.email,
                "reason": "user_creation_error",
                "error": str(e)
            }
        )
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
            "permissions": new_user.permissions or [],
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

    # Log successful registration
    await log_user_activity(
        user_id=str(new_user.id),
        activity_type=ActivityType.USER_CREATED,
        action="registration_success",
        description=f"New user {new_user.username} registered successfully",
        severity=ActivitySeverity.MEDIUM,
        details={
            "username": new_user.username,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "roles": new_user.roles or []
        },
        # Extract context from request
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        tenant_id=new_user.tenant_id
    )

    # Send welcome email
    try:
        email_service = get_auth_email_service()
        await email_service.send_welcome_email(
            email=new_user.email,
            user_name=new_user.full_name or new_user.username,
        )
    except Exception:
        logger.warning("Failed to send welcome email", exc_info=True)
        # Don't fail registration if email fails

    # Set HttpOnly authentication cookies
    set_auth_cookies(response, access_token, refresh_token)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    refresh_request: Optional[RefreshTokenRequest] = None,
    session: AsyncSession = Depends(get_auth_session),
) -> TokenResponse:
    """
    Refresh access token using refresh token.
    Can accept refresh token from request body or HttpOnly cookie.
    """
    try:
        # Get refresh token from cookie or request body
        refresh_token_value = get_token_from_cookie(request, "refresh_token")
        if not refresh_token_value and refresh_request:
            refresh_token_value = refresh_request.refresh_token

        if not refresh_token_value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not provided",
            )

        # Verify refresh token
        payload = jwt_service.verify_token(refresh_token_value)

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
            await jwt_service.revoke_token(refresh_token_value)
        except Exception:
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

        # Set new HttpOnly authentication cookies
        set_auth_cookies(response, access_token, new_refresh_token)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except Exception:
        logger.error("Token refresh failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )


@auth_router.post("/logout")
async def logout(
    request: Request,
    response: Response,
) -> dict:
    """
    Logout user and invalidate session and tokens.
    """
    try:
        # Get token from Authorization header or cookie
        token = None
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
        else:
            # Fall back to cookie
            token = get_token_from_cookie(request, "access_token")

        if token:
            # Get user info from token
            try:
                payload = jwt_service.verify_token(token)
                user_id = payload.get("sub")
            except Exception:
                # Invalid token, still clear cookies
                clear_auth_cookies(response)
                return {"message": "Logout completed"}
        else:
            # No token found, just clear cookies
            clear_auth_cookies(response)
            return {"message": "Logout completed"}

        if user_id:

            # Revoke the access token
            if token:
                await jwt_service.revoke_token(token)

            # Delete all user sessions (which should include refresh tokens)
            deleted_sessions = await session_manager.delete_user_sessions(user_id)

            # Also explicitly revoke all refresh tokens for this user
            # This ensures refresh tokens can't be used after logout
            try:
                # Get all active sessions to find refresh tokens
                await jwt_service.revoke_user_tokens(user_id)
            except Exception:
                logger.warning("Failed to revoke user refresh tokens", exc_info=True)

            logger.info("User logged out successfully", user_id=user_id, sessions_deleted=deleted_sessions)

            # Clear authentication cookies
            clear_auth_cookies(response)

            return {
                "message": "Logged out successfully",
                "sessions_deleted": deleted_sessions
            }
        else:
            # Clear authentication cookies even if no user found
            clear_auth_cookies(response)
            return {"message": "Logout completed"}
    except Exception:
        logger.error("Logout failed", exc_info=True)
        # Still try to revoke the token even if we can't parse it
        try:
            if token:
                await jwt_service.revoke_token(token)
        except Exception:
            pass

        # Always clear cookies on logout
        clear_auth_cookies(response)
        return {"message": "Logout completed"}


@auth_router.get("/verify")
async def verify_token(
    user_info: UserInfo = Depends(get_current_user),
) -> dict:
    """
    Verify if the current token is valid from Bearer token or HttpOnly cookie.
    """
    return {
        "valid": True,
        "user_id": user_info.user_id,
        "username": user_info.username,
        "roles": user_info.roles,
        "permissions": user_info.permissions,
    }


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
            response, reset_token = await email_service.send_password_reset_email(
                email=user.email,
                user_name=user.full_name or user.username,
            )
            logger.info("Password reset requested", user_id=str(user.id))
        except Exception:
            logger.error("Failed to send password reset email", exc_info=True)

    return {"message": "If the email exists, a password reset link has been sent."}


@auth_router.post("/password-reset/confirm")
async def confirm_password_reset(
    request: PasswordResetConfirm,
    response: Response,
    session: AsyncSession = Depends(get_auth_session),
) -> dict:
    """
    Confirm password reset with token and set new password.
    """
    # Verify the reset token
    email_service = get_auth_email_service()
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
        await email_service.send_password_reset_success_email(
            email=user.email,
            user_name=user.full_name or user.username,
        )

        logger.info("Password reset completed", user_id=str(user.id))
        return {"message": "Password has been reset successfully."}
    except Exception:
        logger.error("Failed to reset password", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password",
        )


@auth_router.get("/me")
async def get_current_user_endpoint(
    user_info: UserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_auth_session),
) -> dict:
    """
    Get current user information from Bearer token or HttpOnly cookie.
    """
    try:
        user_service = UserService(session)
        user = await user_service.get_user_by_id(user_info.user_id)

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
    except Exception:
        logger.error("Failed to get current user", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information",
        )


# Export router
__all__ = ["auth_router"]

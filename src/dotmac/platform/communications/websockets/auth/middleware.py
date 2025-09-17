"""
Authentication middleware for WebSocket connections.
"""


from collections.abc import Awaitable, Callable
from typing import Any, Optional

from .manager import AuthManager
from .types import AuthResult

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

class AuthMiddleware:
    """WebSocket authentication middleware."""

    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager

        # Hooks
        self._auth_success_handlers: list[Callable[[AuthResult], Awaitable[None]]] = []
        self._auth_failure_handlers: list[Callable[[AuthResult], Awaitable[None]]] = []

    def add_auth_success_handler(self, handler: Callable[[AuthResult], Awaitable[None]]):
        """Add handler for successful authentication."""
        self._auth_success_handlers.append(handler)

    def add_auth_failure_handler(self, handler: Callable[[AuthResult], Awaitable[None]]):
        """Add handler for failed authentication."""
        self._auth_failure_handlers.append(handler)

    async def authenticate_connection(self, websocket, path: str) -> AuthResult:
        """Authenticate WebSocket connection during handshake."""
        try:
            auth_result = await self.auth_manager.validate_websocket_auth(websocket, path)

            # Call appropriate handlers
            if auth_result.success:
                for handler in self._auth_success_handlers:
                    try:
                        await handler(auth_result)
                    except Exception as e:
                        logger.error(f"Auth success handler error: {e}")
            else:
                for handler in self._auth_failure_handlers:
                    try:
                        await handler(auth_result)
                    except Exception as e:
                        logger.error(f"Auth failure handler error: {e}")

            return auth_result

        except Exception as e:
            logger.error(f"Authentication middleware error: {e}")
            return AuthResult.failure_result("Authentication middleware error")

    async def check_message_permission(
        self, session, message_type: str, required_permission: Optional[str] = None
    ) -> bool:
        """Check if session has permission to send a message type."""
        if not self.auth_manager.config.enabled:
            return True

        if not session.is_authenticated:
            # Check if message type allows anonymous access
            anonymous_allowed = ["ping", "pong", "auth", "authenticate"]
            return message_type in anonymous_allowed

        # Check specific permission if required
        if required_permission:
            user_info = session.metadata.custom_data.get("user_info")
            if user_info and hasattr(user_info, "has_permission"):
                return user_info.has_permission(required_permission)
            return False

        return True

    async def check_channel_access(
        self,
        session,
        channel_name: str,
        action: str = "subscribe",  # subscribe, unsubscribe, send
    ) -> bool:
        """Check if session can access a channel."""
        if not self.auth_manager.config.enabled:
            return True

        # Anonymous users
        if not session.is_authenticated:
            # Only allow public channels
            if channel_name.startswith("public:"):
                return True
            return False

        user_info = session.metadata.custom_data.get("user_info")
        if not user_info:
            return False

        # User-specific channels
        if channel_name.startswith(f"user:{user_info.user_id}:"):
            return True

        # Tenant channels
        if hasattr(user_info, "tenant_id") and user_info.tenant_id:
            if channel_name.startswith(f"tenant:{user_info.tenant_id}:"):
                return True

        # Role-based channels
        if hasattr(user_info, "roles"):
            for role in user_info.roles:
                if channel_name.startswith(f"role:{role}:"):
                    return True

        # Permission-based channels
        if hasattr(user_info, "permissions"):
            channel_permission = f"channel:{channel_name}:{action}"
            if user_info.has_permission(channel_permission):
                return True

            # Check wildcard permissions
            wildcard_permission = f"channel:*:{action}"
            if user_info.has_permission(wildcard_permission):
                return True

        # Admin users have access to everything
        if hasattr(user_info, "has_role") and user_info.has_role("admin"):
            return True

        return False

    def create_auth_required_decorator(self, required_permission: Optional[str] = None):
        """Create decorator for message handlers that require authentication."""

        def decorator(handler: Callable):
            async def wrapper(session, data):
                if not await self.check_message_permission(
                    session, handler.__name__, required_permission
                ):
                    await session.send_message(
                        "permission_denied",
                        {
                            "message": "Insufficient permissions",
                            "required_permission": required_permission,
                        },
                    )
                    return

                return await handler(session, data)

            return wrapper

        return decorator

    def create_permission_required_decorator(self, permission: str):
        """Create decorator for handlers that require specific permission."""
        return self.create_auth_required_decorator(permission)

    def create_role_required_decorator(self, roles: list[str]):
        """Create decorator for handlers that require specific roles."""

        def decorator(handler: Callable):
            async def wrapper(session, data):
                if not session.is_authenticated:
                    await session.send_message(
                        "auth_required", {"message": "Authentication required"}
                    )
                    return

                user_info = session.metadata.custom_data.get("user_info")
                if (
                    not user_info
                    or not hasattr(user_info, "has_any_role")
                    or not user_info.has_any_role(roles)
                ):
                    await session.send_message(
                        "permission_denied", {"message": f"Requires one of roles: {roles}"}
                    )
                    return

                return await handler(session, data)

            return wrapper

        return decorator

    async def enforce_connection_limits(self, websocket, auth_result: AuthResult) -> bool:
        """Enforce connection limits based on authentication."""
        if not auth_result.success:
            return True  # Let connection proceed to be rejected later

        user_info = auth_result.user_info
        if not user_info:
            return True

        # This would typically check against current connection counts
        # For now, just return True
        return True

    def get_stats(self) -> dict[str, Any]:
        """Get middleware statistics."""
        return {
            "auth_success_handlers": len(self._auth_success_handlers),
            "auth_failure_handlers": len(self._auth_failure_handlers),
            "auth_manager_stats": self.auth_manager.get_stats(),
        }

"""
RADIUS authentication handler.
"""

import logging
from typing import Optional

from .types import (
    RADIUSClient,
    RADIUSPacket,
    RADIUSResponse,
    RADIUSUser,
)

logger = logging.getLogger(__name__)


class RADIUSAuthenticator:
    """
    RADIUS authentication processor.

    Handles user authentication for RADIUS access requests.
    """

    def __init__(self):
        self._users: dict[str, RADIUSUser] = {}
        self._auth_methods = ["pap", "chap"]

    async def authenticate(
        self, packet: RADIUSPacket, username: str, client: RADIUSClient
    ) -> RADIUSResponse:
        """
        Authenticate RADIUS access request.

        Args:
            packet: RADIUS request packet
            username: Username to authenticate
            client: RADIUS client making request

        Returns:
            RADIUSResponse with authentication result
        """
        try:
            user = self._users.get(username)
            if not user:
                return RADIUSResponse.error_response(
                    f"User {username} not found", "USER_NOT_FOUND"
                )

            if not user.is_active:
                return RADIUSResponse.error_response(
                    f"User {username} is disabled", "USER_DISABLED"
                )

            # Perform password authentication (simplified)
            if await self._verify_password(packet, user):
                return RADIUSResponse.success_response(
                    f"User {username} authenticated successfully"
                )
            else:
                return RADIUSResponse.error_response(
                    "Invalid credentials", "INVALID_CREDENTIALS"
                )

        except Exception as e:
            logger.error(f"Authentication error for {username}: {e}")
            return RADIUSResponse.error_response("Authentication failed", "AUTH_ERROR")

    async def _verify_password(self, packet: RADIUSPacket, user: RADIUSUser) -> bool:
        """Verify user password from RADIUS packet."""
        # This would implement proper RADIUS password verification
        # For now, return True as placeholder
        return True

    def add_user(self, user: RADIUSUser):
        """Add user for authentication."""
        self._users[user.username] = user

    def remove_user(self, username: str):
        """Remove user."""
        if username in self._users:
            del self._users[username]

    def get_user(self, username: str) -> Optional[RADIUSUser]:
        """Get user by username."""
        return self._users.get(username)

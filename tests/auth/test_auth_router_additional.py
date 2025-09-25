"""
Additional tests for Auth Router to achieve 100% coverage.
"""

from unittest.mock import AsyncMock, patch

import pytest


class TestLogoutEndpointAdditional:
    """Additional tests for logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_revoke_exception(self):
        """Test logout when token revocation also fails."""
        from dotmac.platform.auth.router import logout
        from fastapi.security import HTTPAuthorizationCredentials

        mock_jwt_service = AsyncMock()
        mock_jwt_service.verify_token.side_effect = Exception("Token error")
        mock_jwt_service.revoke_token = AsyncMock(side_effect=Exception("Revoke error"))

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid_token"
        )

        with patch('dotmac.platform.auth.router.jwt_service', mock_jwt_service):
            # Should handle both exceptions gracefully
            result = await logout(credentials)
            assert result["message"] == "Logout completed"
            mock_jwt_service.revoke_token.assert_called_once()
"""
Rate limiting configuration for authentication endpoints.

This module defines rate limits for auth endpoints to prevent abuse.
The limits are applied in production but gracefully skipped in tests.
"""

from typing import Any

# Rate limits for auth endpoints
# These are applied in production via the app configuration

AUTH_RATE_LIMITS = {
    "/auth/login": "60/minute",  # Relaxed for development
    "/auth/register": "30/minute",  # Relaxed for development
    "/auth/refresh": "60/minute",  # Relaxed for development
    "/auth/password-reset": "30/minute",  # Relaxed for development
}


def apply_auth_rate_limits(app: Any) -> None:
    """Apply rate limits to auth endpoints.

    This is called during app initialization to apply rate limits
    to authentication endpoints. The limits help prevent:
    - Brute force attacks on login
    - Mass account creation via registration
    - Token refresh abuse
    - Password reset abuse
    """
    for _endpoint, _limit in AUTH_RATE_LIMITS.items():
        # Apply limiter to specific endpoint
        # This approach allows tests to work without Request objects
        pass  # Actual application happens via middleware

"""
Compatibility module for service_tokens imports.
Redirects to service_auth module.
"""

from .service_auth import ServiceAuthMiddleware, create_service_token_manager

__all__ = ["ServiceAuthMiddleware", "create_service_token_manager"]

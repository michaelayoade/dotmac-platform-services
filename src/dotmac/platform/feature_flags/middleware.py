"""
Feature flag middleware for web frameworks
"""

import asyncio
import time
from collections.abc import Callable
from typing import Any, Optional

try:
    from fastapi import Request, Response
    from fastapi.middleware.base import BaseHTTPMiddleware

    FASTAPI_AVAILABLE = True
except ImportError:
    # FastAPI not available, create dummy base class
    FASTAPI_AVAILABLE = False

    class BaseHTTPMiddleware:
        def __init__(self, app, **kwargs):
            pass

    class Request:
        pass

    class Response:
        pass


from dotmac_shared.core.logging import get_logger

from .manager import FeatureFlagManager

logger = get_logger(__name__)


class FeatureFlagMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for feature flag context injection and performance tracking
    """

    def __init__(
        self,
        app,
        manager: FeatureFlagManager,
        context_extractor: Optional[Callable[[Request], dict[str, Any]]] = None,
        track_performance: bool = True,
    ):
        super().__init__(app)
        self.manager = manager
        self.context_extractor = context_extractor or self._default_context_extractor
        self.track_performance = track_performance

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and inject feature flag context"""
        start_time = time.time() if self.track_performance else None

        try:
            # Extract context from request
            context = self.context_extractor(request)

            # Store context in request state for use in handlers
            request.state.feature_flag_context = context
            request.state.feature_flag_manager = self.manager

            # Add convenience methods to request state
            request.state.is_feature_enabled = lambda flag_key: self._check_feature_enabled(flag_key, context)
            request.state.get_feature_variant = lambda flag_key: self._get_feature_variant(flag_key, context)
            request.state.get_feature_payload = lambda flag_key: self._get_feature_payload(flag_key, context)

            # Process request
            response = await call_next(request)

            # Add feature flag headers if enabled
            if self.track_performance:
                end_time = time.time()
                response.headers["X-Feature-Flags-Processed"] = "true"
                response.headers["X-Feature-Flags-Time"] = f"{(end_time - start_time) * 1000:.2f}ms"

            return response

        except Exception as e:
            logger.error(f"Error in FeatureFlagMiddleware: {e}")
            # Continue with request even if feature flag processing fails
            return await call_next(request)

    def _default_context_extractor(self, request: Request) -> dict[str, Any]:
        """Default context extraction from FastAPI request"""
        context = {
            "user_agent": request.headers.get("user-agent", ""),
            "ip_address": request.client.host if request.client else "",
            "path": request.url.path,
            "method": request.method,
        }

        # Extract from headers
        if "x-user-id" in request.headers:
            context["user_id"] = request.headers["x-user-id"]

        if "x-tenant-id" in request.headers:
            context["tenant_id"] = request.headers["x-tenant-id"]

        # Extract from path parameters
        context.update(request.path_params)

        # Extract from request state (if set by auth middleware)
        if hasattr(request.state, "user_id"):
            context["user_id"] = request.state.user_id

        if hasattr(request.state, "tenant_id"):
            context["tenant_id"] = request.state.tenant_id

        if hasattr(request.state, "user_tier"):
            context["user_tier"] = request.state.user_tier

        return context

    async def _check_feature_enabled(self, flag_key: str, context: dict[str, Any]) -> bool:
        """Check if feature is enabled for context"""
        try:
            return await self.manager.is_enabled(flag_key, context)
        except Exception as e:
            logger.error(f"Error checking feature {flag_key}: {e}")
            return False

    async def _get_feature_variant(self, flag_key: str, context: dict[str, Any]) -> Optional[str]:
        """Get feature variant for context"""
        try:
            return await self.manager.get_variant(flag_key, context)
        except Exception as e:
            logger.error(f"Error getting variant for {flag_key}: {e}")
            return None

    async def _get_feature_payload(self, flag_key: str, context: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Get feature payload for context"""
        try:
            return await self.manager.get_payload(flag_key, context)
        except Exception as e:
            logger.error(f"Error getting payload for {flag_key}: {e}")
            return None


class DjangoFeatureFlagMiddleware:
    """
    Django middleware for feature flag context injection
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.manager: Optional[FeatureFlagManager] = None

    def __call__(self, request):
        if not self.manager:
            from .decorators import _get_global_manager

            self.manager = _get_global_manager()

        if self.manager:
            # Extract context
            context = self._extract_context(request)

            # Add to request
            request.feature_flag_context = context
            request.feature_flag_manager = self.manager

            # Add convenience methods
            request.is_feature_enabled = lambda flag_key: self._check_feature_enabled_sync(flag_key, context)
            request.get_feature_variant = lambda flag_key: self._get_feature_variant_sync(flag_key, context)

        response = self.get_response(request)
        return response

    def _extract_context(self, request) -> dict[str, Any]:
        """Extract context from Django request"""
        context = {
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "ip_address": request.META.get("REMOTE_ADDR", ""),
            "path": request.path,
            "method": request.method,
        }

        # Extract user info
        if hasattr(request, "user") and request.user.is_authenticated:
            context["user_id"] = str(request.user.id)
            context["email"] = request.user.email

        return context

    def _check_feature_enabled_sync(self, flag_key: str, context: dict[str, Any]) -> bool:
        """Synchronous wrapper for checking feature flags"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.manager.is_enabled(flag_key, context))
        except Exception as e:
            logger.error(f"Error checking feature {flag_key}: {e}")
            return False
        finally:
            loop.close()

    def _get_feature_variant_sync(self, flag_key: str, context: dict[str, Any]) -> Optional[str]:
        """Synchronous wrapper for getting feature variants"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.manager.get_variant(flag_key, context))
        except Exception as e:
            logger.error(f"Error getting variant for {flag_key}: {e}")
            return None
        finally:
            loop.close()


class FlaskFeatureFlagExtension:
    """
    Flask extension for feature flags
    """

    def __init__(self, app=None, manager: Optional[FeatureFlagManager] = None):
        self.manager = manager
        if app is not None:
            self.init_app(app)

    def init_app(self, app, manager: Optional[FeatureFlagManager] = None):
        """Initialize extension with Flask app"""
        if manager:
            self.manager = manager

        if not self.manager:
            from .decorators import _get_global_manager

            self.manager = _get_global_manager()

        if not self.manager:
            raise ValueError("FeatureFlagManager must be provided or set globally")

        # Register before request handler
        app.before_request(self._before_request)

        # Register template globals
        app.jinja_env.globals["is_feature_enabled"] = self._template_is_feature_enabled

    def _before_request(self):
        """Extract context and add to Flask g"""
        flask_mod = __import__("flask")
        request = flask_mod.request
        g = flask_mod.g

        context = {
            "user_agent": request.headers.get("User-Agent", ""),
            "ip_address": request.remote_addr or "",
            "path": request.path,
            "method": request.method,
        }

        # Extract user info (assumes some auth system sets g.user)
        if hasattr(g, "user") and g.user:
            context["user_id"] = str(g.user.id)
            context["email"] = g.user.email

        g.feature_flag_context = context
        g.feature_flag_manager = self.manager

        # Add convenience functions
        g.is_feature_enabled = lambda flag_key: self._check_feature_enabled_sync(flag_key, context)
        g.get_feature_variant = lambda flag_key: self._get_feature_variant_sync(flag_key, context)

    def _template_is_feature_enabled(self, flag_key: str) -> bool:
        """Template function to check feature flags"""
        g = __import__("flask").g
        if hasattr(g, "is_feature_enabled"):
            return g.is_feature_enabled(flag_key)
        return False

    def _check_feature_enabled_sync(self, flag_key: str, context: dict[str, Any]) -> bool:
        """Synchronous wrapper for checking feature flags"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.manager.is_enabled(flag_key, context))
        except Exception as e:
            logger.error(f"Error checking feature {flag_key}: {e}")
            return False
        finally:
            loop.close()

    def _get_feature_variant_sync(self, flag_key: str, context: dict[str, Any]) -> Optional[str]:
        """Synchronous wrapper for getting feature variants"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.manager.get_variant(flag_key, context))
        except Exception as e:
            logger.error(f"Error getting variant for {flag_key}: {e}")
            return None
        finally:
            loop.close()

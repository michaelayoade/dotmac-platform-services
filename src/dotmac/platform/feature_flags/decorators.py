"""
Feature flag decorators for easy integration
"""

import asyncio
import functools
from collections.abc import Callable
from typing import Optional

try:
    from fastapi import HTTPException, Request

    FASTAPI_AVAILABLE = True
except ImportError:
    # FastAPI not available, create dummy classes
    FASTAPI_AVAILABLE = False

    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail
            super().__init__(detail)

    class Request:
        pass


from dotmac_shared.core.logging import get_logger

from .manager import FeatureFlagManager

logger = get_logger(__name__)


def feature_flag(
    flag_key: str,
    manager: Optional[FeatureFlagManager] = None,
    fallback_enabled: bool = False,
    context_extractor: Optional[Callable] = None,
    on_disabled: Optional[Callable] = None,
):
    """
    Decorator to enable/disable functions based on feature flags

    Args:
        flag_key: Feature flag key to check
        manager: FeatureFlagManager instance (if None, uses global instance)
        fallback_enabled: Default behavior if flag evaluation fails
        context_extractor: Function to extract context from function args
        on_disabled: Function to call when feature is disabled
    """

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get context for flag evaluation
            context = {}
            if context_extractor:
                try:
                    context = context_extractor(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Context extraction failed for {flag_key}: {e}")

            # Get manager instance
            flag_manager = manager or _get_global_manager()
            if not flag_manager:
                logger.warning(f"No FeatureFlagManager available for {flag_key}")
                if fallback_enabled:
                    return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                else:
                    if on_disabled:
                        return (
                            await on_disabled(*args, **kwargs)
                            if asyncio.iscoroutinefunction(on_disabled)
                            else on_disabled(*args, **kwargs)
                        )
                    return None

            # Check if feature is enabled
            try:
                is_enabled = await flag_manager.is_enabled(flag_key, context)
                if is_enabled:
                    return await func(*args, **kwargs)
                else:
                    logger.debug(f"Feature {flag_key} is disabled for context: {context}")
                    if on_disabled:
                        return (
                            await on_disabled(*args, **kwargs)
                            if asyncio.iscoroutinefunction(on_disabled)
                            else on_disabled(*args, **kwargs)
                        )
                    return None
            except Exception as e:
                logger.error(f"Error evaluating feature flag {flag_key}: {e}")
                if fallback_enabled:
                    return await func(*args, **kwargs)
                else:
                    if on_disabled:
                        return (
                            await on_disabled(*args, **kwargs)
                            if asyncio.iscoroutinefunction(on_disabled)
                            else on_disabled(*args, **kwargs)
                        )
                    return None

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For synchronous functions, we need to run the async flag check
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            return loop.run_until_complete(async_wrapper(*args, **kwargs))

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def requires_feature(
    flag_key: str,
    manager: Optional[FeatureFlagManager] = None,
    error_message: str = "Feature not available",
    error_code: int = 404,
    context_extractor: Optional[Callable] = None,
):
    """
    Decorator that raises an HTTP exception if feature is disabled
    Useful for API endpoints that should return 404 when disabled
    """

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get context
            context = {}
            if context_extractor:
                try:
                    context = context_extractor(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Context extraction failed for {flag_key}: {e}")

            # Get manager
            flag_manager = manager or _get_global_manager()
            if not flag_manager:
                logger.warning(f"No FeatureFlagManager available for {flag_key}")
                raise HTTPException(status_code=503, detail="Feature flag service unavailable")

            # Check feature
            try:
                is_enabled = await flag_manager.is_enabled(flag_key, context)
                if not is_enabled:
                    raise HTTPException(status_code=error_code, detail=error_message)

                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error checking feature flag {flag_key}: {e}")
                raise HTTPException(status_code=503, detail="Feature flag evaluation failed") from e

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            return loop.run_until_complete(async_wrapper(*args, **kwargs))

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def ab_test(
    flag_key: str,
    variants: dict[str, Callable],
    manager: Optional[FeatureFlagManager] = None,
    default_variant: str = "control",
    context_extractor: Optional[Callable] = None,
):
    """
    Decorator for A/B testing with different function implementations per variant

    Args:
        flag_key: Feature flag key for the A/B test
        variants: Dictionary mapping variant names to functions
        manager: FeatureFlagManager instance
        default_variant: Default variant if flag is disabled or error occurs
        context_extractor: Function to extract context from function args
    """

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get context
            context = {}
            if context_extractor:
                try:
                    context = context_extractor(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Context extraction failed for {flag_key}: {e}")

            # Get manager
            flag_manager = manager or _get_global_manager()
            if not flag_manager:
                logger.warning(f"No FeatureFlagManager available for {flag_key}")
                # Use default variant
                variant_func = variants.get(default_variant, func)
                return (
                    await variant_func(*args, **kwargs)
                    if asyncio.iscoroutinefunction(variant_func)
                    else variant_func(*args, **kwargs)
                )

            try:
                # Check if test is enabled
                is_enabled = await flag_manager.is_enabled(flag_key, context)
                if not is_enabled:
                    variant_func = variants.get(default_variant, func)
                    return (
                        await variant_func(*args, **kwargs)
                        if asyncio.iscoroutinefunction(variant_func)
                        else variant_func(*args, **kwargs)
                    )

                # Get variant for user
                variant_name = await flag_manager.get_variant(flag_key, context)
                if not variant_name:
                    variant_name = default_variant

                # Execute variant function
                variant_func = variants.get(variant_name, variants.get(default_variant, func))
                logger.debug(f"A/B test {flag_key}: using variant {variant_name} for context {context}")

                return (
                    await variant_func(*args, **kwargs)
                    if asyncio.iscoroutinefunction(variant_func)
                    else variant_func(*args, **kwargs)
                )

            except Exception as e:
                logger.error(f"Error in A/B test {flag_key}: {e}")
                # Fallback to default
                variant_func = variants.get(default_variant, func)
                return (
                    await variant_func(*args, **kwargs)
                    if asyncio.iscoroutinefunction(variant_func)
                    else variant_func(*args, **kwargs)
                )

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            return loop.run_until_complete(async_wrapper(*args, **kwargs))

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def feature_variant(
    flag_key: str,
    variant_name: str,
    manager: Optional[FeatureFlagManager] = None,
    context_extractor: Optional[Callable] = None,
):
    """
    Decorator to execute function only for a specific A/B test variant
    """

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get context
            context = {}
            if context_extractor:
                try:
                    context = context_extractor(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Context extraction failed for {flag_key}: {e}")

            # Get manager
            flag_manager = manager or _get_global_manager()
            if not flag_manager:
                return None

            try:
                # Get user's variant
                user_variant = await flag_manager.get_variant(flag_key, context)
                if user_variant == variant_name:
                    return await func(*args, **kwargs)
                else:
                    return None
            except Exception as e:
                logger.error(f"Error checking variant {variant_name} for flag {flag_key}: {e}")
                return None

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            return loop.run_until_complete(async_wrapper(*args, **kwargs))

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Context extractors for common patterns
def fastapi_context_extractor(*args, **kwargs):
    """Extract context from FastAPI request"""
    request = None

    # Look for Request object in args or kwargs
    for arg in args:
        if hasattr(arg, "headers") and hasattr(arg, "path_params"):
            request = arg
            break

    if "request" in kwargs:
        request = kwargs["request"]

    if not request:
        return {}

    context = {}

    # Extract user ID from headers or JWT
    if hasattr(request.state, "user_id"):
        context["user_id"] = request.state.user_id

    if hasattr(request.state, "tenant_id"):
        context["tenant_id"] = request.state.tenant_id

    # Extract from headers
    context["user_agent"] = request.headers.get("user-agent", "")
    context["ip_address"] = request.client.host if request.client else ""

    # Extract from path parameters
    context.update(request.path_params)

    return context


def django_context_extractor(*args, **kwargs):
    """Extract context from Django request"""
    request = args[0] if args else None

    if not hasattr(request, "META"):
        return {}

    context = {}

    # Extract user info
    if hasattr(request, "user") and request.user.is_authenticated:
        context["user_id"] = str(request.user.id)
        context["email"] = request.user.email

    # Extract from META
    context["user_agent"] = request.META.get("HTTP_USER_AGENT", "")
    context["ip_address"] = request.META.get("REMOTE_ADDR", "")

    return context


# Global manager instance (set by application)
_global_manager: Optional[FeatureFlagManager] = None


def set_global_manager(manager: FeatureFlagManager):
    """Set the global feature flag manager instance"""
    global _global_manager
    _global_manager = manager


def _get_global_manager() -> Optional[FeatureFlagManager]:
    """Get the global feature flag manager instance"""
    return _global_manager

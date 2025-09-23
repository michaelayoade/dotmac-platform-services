"""
Simple feature flags using Redis + cache - no bloat.

Provides a lightweight feature flag system with Redis backend and in-memory cache.
Supports simple on/off flags, context-based evaluation, and A/B testing.
"""

import json
import time
from typing import Any, Callable, Dict, Optional, TypeVar

import redis.asyncio as redis
import structlog
from cachetools import TTLCache  # type: ignore[import-untyped]

from dotmac.platform.settings import settings

logger = structlog.get_logger(__name__)

# In-memory cache for fast lookups
_flag_cache = TTLCache(maxsize=1000, ttl=60)  # 1 minute TTL
_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    """Get Redis client for flags."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis.url)
    return _redis_client


async def set_flag(name: str, enabled: bool, context: Optional[Dict[str, Any]] = None) -> None:
    """Set feature flag value."""
    client = await get_redis_client()

    flag_data = {"enabled": enabled, "context": context or {}, "updated_at": int(time.time())}

    await client.hset("feature_flags", name, json.dumps(flag_data))  # type: ignore[misc]

    # Update cache
    _flag_cache[name] = flag_data
    logger.info("Feature flag updated", flag=name, enabled=enabled)


async def is_enabled(name: str, context: Optional[Dict[str, Any]] = None) -> bool:
    """Check if feature flag is enabled."""
    # Check cache first
    if name in _flag_cache:
        flag_data = _flag_cache[name]
    else:
        # Get from Redis
        client = await get_redis_client()
        flag_json = await client.hget("feature_flags", name)  # type: ignore[misc]

        if not flag_json:
            logger.debug("Feature flag not found, defaulting to False", flag=name)
            return False

        flag_data = json.loads(flag_json)
        _flag_cache[name] = flag_data

    enabled: bool = flag_data.get("enabled", False)

    # Simple context matching (can be extended)
    flag_context = flag_data.get("context", {})
    if context and flag_context:
        # Check if all flag context conditions match
        for key, value in flag_context.items():
            if context.get(key) != value:
                enabled = False
                break

    logger.debug("Feature flag checked", flag=name, enabled=enabled, context=context)
    return enabled


async def get_variant(name: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Get A/B test variant. Returns 'control' if flag disabled."""
    if not await is_enabled(name, context):
        return "control"

    # Simple A/B test based on user_id hash
    if context and "user_id" in context:
        user_hash = hash(f"{name}:{context['user_id']}") % 100
        return "variant_a" if user_hash < 50 else "variant_b"

    return "control"


async def list_flags() -> Dict[str, Dict[str, Any]]:
    """List all feature flags."""
    client = await get_redis_client()
    flags = await client.hgetall("feature_flags")  # type: ignore[misc]

    result = {}
    for name, flag_json in flags.items():
        if isinstance(name, bytes):
            name = name.decode()
        if isinstance(flag_json, bytes):
            flag_json = flag_json.decode()

        try:
            result[name] = json.loads(flag_json)
        except json.JSONDecodeError:
            logger.warning("Invalid flag data", flag=name)

    return result


async def delete_flag(name: str) -> bool:
    """Delete feature flag."""
    client = await get_redis_client()
    deleted = await client.hdel("feature_flags", name)  # type: ignore[misc]

    if name in _flag_cache:
        del _flag_cache[name]

    if deleted:
        logger.info("Feature flag deleted", flag=name)

    return bool(deleted)


# Convenience decorators
F = TypeVar("F", bound=Callable[..., Any])


def feature_flag(flag_name: str, default: bool = False) -> Callable[[F], F]:
    """Decorator to enable/disable function based on feature flag."""
    import asyncio

    def decorator(func: F) -> F:
        if asyncio.iscoroutinefunction(func):
            # Handle async functions
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                # Extract context from kwargs if available
                context = kwargs.pop("_feature_context", None)

                if await is_enabled(flag_name, context):
                    return await func(*args, **kwargs)
                elif default:
                    return await func(*args, **kwargs)
                else:
                    logger.debug("Function skipped due to feature flag", flag=flag_name)
                    return None

            return async_wrapper  # type: ignore[return-value]
        else:
            # Handle sync functions
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                # Extract context from kwargs if available
                context = kwargs.pop("_feature_context", None)

                # Run async check in sync context
                loop = asyncio.get_event_loop()
                enabled = loop.run_until_complete(is_enabled(flag_name, context))

                if enabled or default:
                    return func(*args, **kwargs)
                else:
                    logger.debug("Function skipped due to feature flag", flag=flag_name)
                    return None

            return sync_wrapper  # type: ignore[return-value]

    return decorator


# Usage examples:
#
# # Set flags
# await set_flag("new_ui", True)
# await set_flag("beta_features", True, {"user_type": "premium"})
#
# # Check flags
# if await is_enabled("new_ui"):
#     return render_new_ui()
#
# # A/B testing
# variant = await get_variant("checkout_flow", {"user_id": "123"})
# if variant == "variant_a":
#     return new_checkout()
#
# # Decorator usage
# @feature_flag("experimental_feature")
# async def experimental_function():
#     return "This only runs if flag is enabled"
#
# # For even simpler cases, use Redis directly:
# import redis.asyncio as redis
# client = redis.from_url("redis://localhost")
# await client.hset("flags", "my_flag", "true")
# enabled = await client.hget("flags", "my_flag") == b"true"

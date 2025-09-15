"""
Feature flag manager for centralized flag management
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Optional

from dotmac_shared.core.logging import get_logger

from .models import FeatureFlag, FeatureFlagStatus, RolloutStrategy
from .storage import FeatureFlagStorage, RedisStorage

logger = get_logger(__name__)


class FeatureFlagManager:
    """
    Centralized feature flag manager with caching and real-time updates
    """

    def __init__(
        self,
        storage: Optional[FeatureFlagStorage] = None,
        cache_ttl: int = 300,  # 5 minutes
        environment: str = "development",
        service_name: Optional[str] = None,
    ):
        self.storage = storage or RedisStorage()
        self.cache_ttl = cache_ttl
        self.environment = environment
        self.service_name = service_name

        # In-memory cache
        self._cache: dict[str, FeatureFlag] = {}
        self._cache_timestamps: dict[str, datetime] = {}

        # Subscriptions for real-time updates
        self._subscribers: set[callable] = set()
        self._update_task: Optional[asyncio.Task] = None

        logger.info(f"FeatureFlagManager initialized for {environment} environment")

    async def initialize(self):
        """Initialize the manager and start background tasks"""
        await self.storage.initialize()
        await self._load_all_flags()

        # Start background update task
        self._update_task = asyncio.create_task(self._background_update_task())

        logger.info("FeatureFlagManager initialized successfully")

    async def shutdown(self):
        """Clean shutdown of manager"""
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

        await self.storage.close()
        logger.info("FeatureFlagManager shut down")

    async def _background_update_task(self):
        """Background task to refresh cache and handle updates"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._refresh_expired_cache()
                await self._cleanup_expired_flags()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background update task: {e}")

    async def _load_all_flags(self):
        """Load all feature flags into cache"""
        flags = await self.storage.get_all_flags()
        now = datetime.utcnow()

        for flag in flags:
            if self.environment in flag.environments:
                self._cache[flag.key] = flag
                self._cache_timestamps[flag.key] = now

        logger.info(f"Loaded {len(self._cache)} feature flags into cache")

    async def _refresh_expired_cache(self):
        """Refresh expired cache entries"""
        now = datetime.utcnow()
        expired_keys = []

        for key, timestamp in self._cache_timestamps.items():
            if (now - timestamp).total_seconds() > self.cache_ttl:
                expired_keys.append(key)

        if expired_keys:
            logger.debug(f"Refreshing {len(expired_keys)} expired cache entries")
            for key in expired_keys:
                await self._refresh_flag(key)

    async def _refresh_flag(self, flag_key: str):
        """Refresh a specific flag in cache"""
        try:
            flag = await self.storage.get_flag(flag_key)
            if flag and self.environment in flag.environments:
                self._cache[flag_key] = flag
                self._cache_timestamps[flag_key] = datetime.utcnow()
            elif flag_key in self._cache:
                # Flag no longer valid for this environment
                del self._cache[flag_key]
                del self._cache_timestamps[flag_key]
        except Exception as e:
            logger.error(f"Error refreshing flag {flag_key}: {e}")

    async def _cleanup_expired_flags(self):
        """Clean up expired flags from cache"""
        now = datetime.utcnow()
        expired_keys = []

        for key, flag in self._cache.items():
            if flag.expires_at and now > flag.expires_at:
                expired_keys.append(key)

        for key in expired_keys:
            logger.info(f"Removing expired flag: {key}")
            del self._cache[key]
            del self._cache_timestamps[key]

    async def is_enabled(self, flag_key: str, context: dict[str, Any]) -> bool:
        """
        Check if a feature flag is enabled for the given context

        Args:
            flag_key: Feature flag key
            context: Context for evaluation (user_id, tenant_id, etc.)

        Returns:
            True if flag is enabled, False otherwise
        """
        flag = await self._get_flag(flag_key)
        if not flag:
            logger.debug(f"Flag not found: {flag_key}")
            return False

        # Add service context
        evaluation_context = {
            **context,
            "service_name": self.service_name,
            "environment": self.environment,
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            enabled = flag.is_enabled_for_context(evaluation_context)
            logger.debug(f"Flag {flag_key} evaluation: {enabled} for context: {context}")
            return enabled
        except Exception as e:
            logger.error(f"Error evaluating flag {flag_key}: {e}")
            return False

    async def get_variant(self, flag_key: str, context: dict[str, Any]) -> Optional[str]:
        """Get A/B test variant for flag and context"""
        flag = await self._get_flag(flag_key)
        if not flag:
            return None

        evaluation_context = {
            **context,
            "service_name": self.service_name,
            "environment": self.environment,
        }

        try:
            return flag.get_variant_for_context(evaluation_context)
        except Exception as e:
            logger.error(f"Error getting variant for flag {flag_key}: {e}")
            return None

    async def get_payload(self, flag_key: str, context: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Get feature payload for flag and context"""
        flag = await self._get_flag(flag_key)
        if not flag:
            return None

        evaluation_context = {
            **context,
            "service_name": self.service_name,
            "environment": self.environment,
        }

        try:
            return flag.get_payload_for_context(evaluation_context)
        except Exception as e:
            logger.error(f"Error getting payload for flag {flag_key}: {e}")
            return None

    async def _get_flag(self, flag_key: str) -> Optional[FeatureFlag]:
        """Get flag from cache or storage"""
        # Check cache first
        if flag_key in self._cache:
            timestamp = self._cache_timestamps.get(flag_key)
            if timestamp and (datetime.utcnow() - timestamp).total_seconds() < self.cache_ttl:
                return self._cache[flag_key]

        # Load from storage
        await self._refresh_flag(flag_key)
        return self._cache.get(flag_key)

    # Admin methods
    async def create_flag(self, flag: FeatureFlag) -> bool:
        """Create a new feature flag"""
        try:
            success = await self.storage.save_flag(flag)
            if success:
                # Update cache
                self._cache[flag.key] = flag
                self._cache_timestamps[flag.key] = datetime.utcnow()
                await self._notify_subscribers("flag_created", flag)
                logger.info(f"Created feature flag: {flag.key}")
            return success
        except Exception as e:
            logger.error(f"Error creating flag {flag.key}: {e}")
            return False

    async def update_flag(self, flag: FeatureFlag) -> bool:
        """Update an existing feature flag"""
        try:
            flag.updated_at = datetime.utcnow()
            success = await self.storage.save_flag(flag)
            if success:
                # Update cache
                self._cache[flag.key] = flag
                self._cache_timestamps[flag.key] = datetime.utcnow()
                await self._notify_subscribers("flag_updated", flag)
                logger.info(f"Updated feature flag: {flag.key}")
            return success
        except Exception as e:
            logger.error(f"Error updating flag {flag.key}: {e}")
            return False

    async def delete_flag(self, flag_key: str) -> bool:
        """Delete a feature flag"""
        try:
            success = await self.storage.delete_flag(flag_key)
            if success:
                # Remove from cache
                if flag_key in self._cache:
                    del self._cache[flag_key]
                    del self._cache_timestamps[flag_key]
                await self._notify_subscribers("flag_deleted", {"key": flag_key})
                logger.info(f"Deleted feature flag: {flag_key}")
            return success
        except Exception as e:
            logger.error(f"Error deleting flag {flag_key}: {e}")
            return False

    async def list_flags(self, tags: Optional[list[str]] = None) -> list[FeatureFlag]:
        """List all feature flags, optionally filtered by tags"""
        flags = list(self._cache.values())

        if tags:
            flags = [flag for flag in flags if any(tag in flag.tags for tag in tags)]

        return sorted(flags, key=lambda f: f.created_at, reverse=True)

    async def get_flag_details(self, flag_key: str) -> Optional[FeatureFlag]:
        """Get detailed information about a flag"""
        return await self._get_flag(flag_key)

    # Gradual rollout management
    async def start_gradual_rollout(
        self,
        flag_key: str,
        start_percentage: float = 0.0,
        end_percentage: float = 100.0,
        duration_hours: int = 24,
        increment_hours: int = 4,
    ) -> bool:
        """Start a gradual rollout for a feature flag"""
        flag = await self._get_flag(flag_key)
        if not flag:
            return False

        from .models import GradualRolloutConfig

        start_date = datetime.utcnow()
        end_date = start_date + timedelta(hours=duration_hours)

        flag.strategy = RolloutStrategy.GRADUAL
        flag.gradual_rollout = GradualRolloutConfig(
            start_percentage=start_percentage,
            end_percentage=end_percentage,
            start_date=start_date,
            end_date=end_date,
            increment_percentage=(end_percentage - start_percentage) / (duration_hours // increment_hours),
            increment_interval_hours=increment_hours,
        )

        return await self.update_flag(flag)

    async def stop_gradual_rollout(self, flag_key: str, final_percentage: Optional[float] = None) -> bool:
        """Stop gradual rollout and set final percentage"""
        flag = await self._get_flag(flag_key)
        if not flag or flag.strategy != RolloutStrategy.GRADUAL:
            return False

        if final_percentage is not None:
            flag.strategy = RolloutStrategy.PERCENTAGE
            flag.percentage = final_percentage
        else:
            flag.strategy = RolloutStrategy.ALL_OFF

        flag.gradual_rollout = None
        return await self.update_flag(flag)

    # Subscription management for real-time updates
    def subscribe(self, callback: callable):
        """Subscribe to flag update notifications"""
        self._subscribers.add(callback)

    def unsubscribe(self, callback: callable):
        """Unsubscribe from flag update notifications"""
        self._subscribers.discard(callback)

    async def _notify_subscribers(self, event_type: str, data: Any):
        """Notify all subscribers of an event"""
        for callback in self._subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type, data)
                else:
                    callback(event_type, data)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")

    # Context managers for temporary flag overrides (testing)
    @asynccontextmanager
    async def override_flag(self, flag_key: str, enabled: bool):
        """Temporarily override a flag for testing"""
        original_flag = self._cache.get(flag_key)

        # Create override
        if original_flag:
            override_flag = original_flag.copy(deep=True)
        else:
            from .models import FeatureFlag

            override_flag = FeatureFlag(key=flag_key, name=f"Override {flag_key}")

        override_flag.strategy = RolloutStrategy.ALL_ON if enabled else RolloutStrategy.ALL_OFF
        override_flag.status = FeatureFlagStatus.ACTIVE

        # Apply override
        self._cache[flag_key] = override_flag
        self._cache_timestamps[flag_key] = datetime.utcnow()

        try:
            yield
        finally:
            # Restore original
            if original_flag:
                self._cache[flag_key] = original_flag
                self._cache_timestamps[flag_key] = datetime.utcnow()
            else:
                self._cache.pop(flag_key, None)
                self._cache_timestamps.pop(flag_key, None)

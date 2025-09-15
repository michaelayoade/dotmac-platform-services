"""
Feature flag client for easy integration with applications
"""

import os
from datetime import datetime, timedelta
from typing import Any, Optional, Union

from dotmac_shared.core.logging import get_logger

from .manager import FeatureFlagManager
from .models import (
    ABTestConfig,
    ABTestVariant,
    FeatureFlag,
    FeatureFlagStatus,
    GradualRolloutConfig,
    RolloutStrategy,
    TargetingRule,
)
from .storage import DatabaseStorage, InMemoryStorage, RedisStorage

logger = get_logger(__name__)


class FeatureFlagClient:
    """
    High-level client for feature flag operations
    Provides convenient methods for common use cases
    """

    def __init__(
        self,
        storage_type: str = "redis",
        storage_config: Optional[dict[str, Any]] = None,
        environment: str = "development",
        service_name: Optional[str] = None,
        cache_ttl: int = 300,
    ):
        """
        Initialize feature flag client

        Args:
            storage_type: Type of storage ("redis", "database", "memory")
            storage_config: Storage configuration parameters
            environment: Environment name (development, staging, production)
            service_name: Service name for context
            cache_ttl: Cache TTL in seconds
        """
        self.environment = environment
        self.service_name = service_name

        # Initialize storage
        if storage_type == "redis":
            self.storage = RedisStorage(**(storage_config or {}))
        elif storage_type == "database":
            self.storage = DatabaseStorage(**(storage_config or {}))
        elif storage_type == "memory":
            self.storage = InMemoryStorage()
        else:
            raise ValueError(f"Unknown storage type: {storage_type}")

        # Initialize manager
        self.manager = FeatureFlagManager(
            storage=self.storage,
            cache_ttl=cache_ttl,
            environment=environment,
            service_name=service_name,
        )

        self._initialized = False

    async def initialize(self):
        """Initialize the client"""
        if not self._initialized:
            await self.manager.initialize()
            self._initialized = True
            logger.info(f"FeatureFlagClient initialized for {self.environment} environment")

    async def shutdown(self):
        """Shutdown the client"""
        if self._initialized:
            await self.manager.shutdown()
            self._initialized = False

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.shutdown()

    # Feature flag evaluation methods
    async def is_enabled(self, flag_key: str, context: Optional[dict[str, Any]] = None) -> bool:
        """Check if a feature flag is enabled"""
        if not self._initialized:
            await self.initialize()

        return await self.manager.is_enabled(flag_key, context or {})

    async def get_variant(self, flag_key: str, context: Optional[dict[str, Any]] = None) -> Optional[str]:
        """Get A/B test variant for a feature flag"""
        if not self._initialized:
            await self.initialize()

        return await self.manager.get_variant(flag_key, context or {})

    async def get_payload(self, flag_key: str, context: Optional[dict[str, Any]] = None) -> Optional[dict[str, Any]]:
        """Get feature payload for a feature flag"""
        if not self._initialized:
            await self.initialize()

        return await self.manager.get_payload(flag_key, context or {})

    # Feature flag management methods
    async def create_simple_flag(
        self,
        key: str,
        name: str,
        description: str = "",
        enabled: bool = False,
        tags: Optional[list[str]] = None,
    ) -> bool:
        """Create a simple on/off feature flag"""
        flag = FeatureFlag(
            key=key,
            name=name,
            description=description,
            status=FeatureFlagStatus.ACTIVE,
            strategy=RolloutStrategy.ALL_ON if enabled else RolloutStrategy.ALL_OFF,
            tags=tags or [],
            environments=[self.environment],
        )

        return await self.manager.create_flag(flag)

    async def create_percentage_flag(
        self,
        key: str,
        name: str,
        percentage: float,
        description: str = "",
        tags: Optional[list[str]] = None,
    ) -> bool:
        """Create a percentage-based rollout flag"""
        flag = FeatureFlag(
            key=key,
            name=name,
            description=description,
            status=FeatureFlagStatus.ACTIVE,
            strategy=RolloutStrategy.PERCENTAGE,
            percentage=percentage,
            tags=tags or [],
            environments=[self.environment],
        )

        return await self.manager.create_flag(flag)

    async def create_user_list_flag(
        self,
        key: str,
        name: str,
        user_list: list[str],
        description: str = "",
        tags: Optional[list[str]] = None,
    ) -> bool:
        """Create a user list based flag"""
        flag = FeatureFlag(
            key=key,
            name=name,
            description=description,
            status=FeatureFlagStatus.ACTIVE,
            strategy=RolloutStrategy.USER_LIST,
            user_list=user_list,
            tags=tags or [],
            environments=[self.environment],
        )

        return await self.manager.create_flag(flag)

    async def create_ab_test_flag(
        self,
        key: str,
        name: str,
        variants: list[dict[str, Any]],
        description: str = "",
        tags: Optional[list[str]] = None,
    ) -> bool:
        """
        Create an A/B test flag

        Args:
            variants: List of variants with 'name', 'percentage', and optional 'payload'
        """
        ab_variants = []
        for variant in variants:
            ab_variants.append(
                ABTestVariant(
                    name=variant["name"],
                    percentage=variant["percentage"],
                    payload=variant.get("payload"),
                    description=variant.get("description"),
                )
            )

        flag = FeatureFlag(
            key=key,
            name=name,
            description=description,
            status=FeatureFlagStatus.ACTIVE,
            strategy=RolloutStrategy.AB_TEST,
            ab_test=ABTestConfig(variants=ab_variants),
            tags=tags or [],
            environments=[self.environment],
        )

        return await self.manager.create_flag(flag)

    async def create_gradual_rollout_flag(
        self,
        key: str,
        name: str,
        duration_hours: int = 24,
        start_percentage: float = 0.0,
        end_percentage: float = 100.0,
        description: str = "",
        tags: Optional[list[str]] = None,
    ) -> bool:
        """Create a gradual rollout flag"""
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(hours=duration_hours)

        flag = FeatureFlag(
            key=key,
            name=name,
            description=description,
            status=FeatureFlagStatus.ACTIVE,
            strategy=RolloutStrategy.GRADUAL,
            gradual_rollout=GradualRolloutConfig(
                start_percentage=start_percentage,
                end_percentage=end_percentage,
                start_date=start_date,
                end_date=end_date,
                increment_percentage=10.0,
                increment_interval_hours=2,
            ),
            tags=tags or [],
            environments=[self.environment],
        )

        return await self.manager.create_flag(flag)

    async def update_flag_percentage(self, key: str, percentage: float) -> bool:
        """Update the percentage for a percentage-based flag"""
        flag = await self.manager.get_flag_details(key)
        if not flag:
            return False

        if flag.strategy != RolloutStrategy.PERCENTAGE:
            flag.strategy = RolloutStrategy.PERCENTAGE

        flag.percentage = percentage
        return await self.manager.update_flag(flag)

    async def enable_flag(self, key: str) -> bool:
        """Enable a feature flag (set to ALL_ON)"""
        flag = await self.manager.get_flag_details(key)
        if not flag:
            return False

        flag.strategy = RolloutStrategy.ALL_ON
        flag.status = FeatureFlagStatus.ACTIVE
        return await self.manager.update_flag(flag)

    async def disable_flag(self, key: str) -> bool:
        """Disable a feature flag (set to ALL_OFF)"""
        flag = await self.manager.get_flag_details(key)
        if not flag:
            return False

        flag.strategy = RolloutStrategy.ALL_OFF
        return await self.manager.update_flag(flag)

    async def add_targeting_rule(
        self,
        key: str,
        attribute: str,
        operator: str,
        value: Union[str, int, float, list[str], bool],
        description: str = "",
    ) -> bool:
        """Add a targeting rule to a flag"""
        flag = await self.manager.get_flag_details(key)
        if not flag:
            return False

        from .models import ComparisonOperator, TargetingAttribute

        rule = TargetingRule(
            attribute=TargetingAttribute(attribute),
            operator=ComparisonOperator(operator),
            value=value,
            description=description,
        )

        flag.targeting_rules.append(rule)
        return await self.manager.update_flag(flag)

    async def set_flag_expiry(self, key: str, expires_at: datetime) -> bool:
        """Set expiry date for a flag"""
        flag = await self.manager.get_flag_details(key)
        if not flag:
            return False

        flag.expires_at = expires_at
        return await self.manager.update_flag(flag)

    # Gradual rollout management
    async def start_gradual_rollout(
        self,
        key: str,
        duration_hours: int = 24,
        start_percentage: float = 0.0,
        end_percentage: float = 100.0,
    ) -> bool:
        """Start a gradual rollout for an existing flag"""
        return await self.manager.start_gradual_rollout(key, start_percentage, end_percentage, duration_hours)

    async def stop_gradual_rollout(self, key: str, final_percentage: Optional[float] = None) -> bool:
        """Stop a gradual rollout"""
        return await self.manager.stop_gradual_rollout(key, final_percentage)

    # Flag information and management
    async def list_flags(self, tags: Optional[list[str]] = None) -> list[dict[str, Any]]:
        """List all flags with their current status"""
        flags = await self.manager.list_flags(tags)

        result = []
        for flag in flags:
            flag_info = {
                "key": flag.key,
                "name": flag.name,
                "description": flag.description,
                "status": flag.status.value if hasattr(flag.status, "value") else flag.status,
                "strategy": flag.strategy.value if hasattr(flag.strategy, "value") else flag.strategy,
                "created_at": flag.created_at.isoformat(),
                "updated_at": flag.updated_at.isoformat(),
                "tags": flag.tags,
            }

            # Add strategy-specific info
            if flag.strategy == RolloutStrategy.PERCENTAGE:
                flag_info["percentage"] = flag.percentage
            elif flag.strategy == RolloutStrategy.USER_LIST:
                flag_info["user_count"] = len(flag.user_list)
            elif flag.strategy == RolloutStrategy.GRADUAL and flag.gradual_rollout:
                flag_info["current_percentage"] = flag.gradual_rollout.get_current_percentage()
            elif flag.strategy == RolloutStrategy.AB_TEST and flag.ab_test:
                flag_info["variants"] = [v.name for v in flag.ab_test.variants]

            result.append(flag_info)

        return result

    async def get_flag_info(self, key: str) -> Optional[dict[str, Any]]:
        """Get detailed information about a flag"""
        flag = await self.manager.get_flag_details(key)
        if not flag:
            return None

        return flag.model_dump()

    async def delete_flag(self, key: str) -> bool:
        """Delete a feature flag"""
        return await self.manager.delete_flag(key)

    # Bulk operations
    async def create_flags_from_config(self, config: dict[str, Any]) -> dict[str, bool]:
        """Create multiple flags from configuration"""
        results = {}

        for flag_key, flag_config in config.items():
            try:
                flag = FeatureFlag(key=flag_key, environments=[self.environment], **flag_config)
                results[flag_key] = await self.manager.create_flag(flag)
            except Exception as e:
                logger.error(f"Error creating flag {flag_key}: {e}")
                results[flag_key] = False

        return results

    async def export_flags(self, tags: Optional[list[str]] = None) -> dict[str, Any]:
        """Export flag configurations"""
        flags = await self.manager.list_flags(tags)

        config = {}
        for flag in flags:
            config[flag.key] = flag.model_dump(exclude={"created_at", "updated_at"})

        return {
            "environment": self.environment,
            "exported_at": datetime.utcnow().isoformat(),
            "flags": config,
        }

    # Testing utilities
    async def override_flag_for_testing(self, key: str, enabled: bool):
        """Context manager for temporarily overriding a flag in tests"""
        return self.manager.override_flag(key, enabled)


# Convenience functions for common patterns
async def create_client_from_env() -> FeatureFlagClient:
    """Create a client from environment variables"""
    storage_type = os.getenv("FEATURE_FLAGS_STORAGE", "redis")
    environment = os.getenv("ENVIRONMENT", "development")
    service_name = os.getenv("SERVICE_NAME")

    storage_config = {}
    if storage_type == "redis":
        storage_config["redis_url"] = os.getenv("REDIS_URL")
    elif storage_type == "database":
        storage_config["database_url"] = os.getenv("DATABASE_URL")

    client = FeatureFlagClient(
        storage_type=storage_type,
        storage_config=storage_config,
        environment=environment,
        service_name=service_name,
        cache_ttl=int(os.getenv("FEATURE_FLAGS_CACHE_TTL", "300")),
    )

    await client.initialize()
    return client

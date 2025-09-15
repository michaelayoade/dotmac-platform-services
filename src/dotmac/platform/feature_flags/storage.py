"""
Storage backends for feature flags
"""

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from dotmac_shared.core.logging import get_logger

from .models import FeatureFlag

logger = get_logger(__name__)


class FeatureFlagStorage(ABC):
    """Abstract base class for feature flag storage"""

    @abstractmethod
    async def initialize(self):
        """Initialize storage connection"""
        pass

    @abstractmethod
    async def close(self):
        """Close storage connection"""
        pass

    @abstractmethod
    async def get_flag(self, flag_key: str) -> Optional[FeatureFlag]:
        """Get a single feature flag"""
        pass

    @abstractmethod
    async def get_all_flags(self) -> list[FeatureFlag]:
        """Get all feature flags"""
        pass

    @abstractmethod
    async def save_flag(self, flag: FeatureFlag) -> bool:
        """Save a feature flag"""
        pass

    @abstractmethod
    async def delete_flag(self, flag_key: str) -> bool:
        """Delete a feature flag"""
        pass


class RedisStorage(FeatureFlagStorage):
    """Redis-based storage for feature flags"""

    def __init__(self, redis_url: Optional[str] = None, key_prefix: str = "feature_flags:"):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.key_prefix = key_prefix
        self.redis = None

    async def initialize(self):
        """Initialize Redis connection"""
        try:
            import redis.asyncio as redis

            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("Redis feature flag storage initialized")
        except ImportError:
            logger.warning("Redis not available, falling back to in-memory storage")
            self.redis = None
        except Exception as e:
            logger.error(f"Failed to initialize Redis storage: {e}")
            self.redis = None

    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()

    async def get_flag(self, flag_key: str) -> Optional[FeatureFlag]:
        """Get flag from Redis"""
        if not self.redis:
            return None

        try:
            data = await self.redis.get(f"{self.key_prefix}{flag_key}")
            if data:
                flag_data = json.loads(data)
                return FeatureFlag(**flag_data)
        except Exception as e:
            logger.error(f"Error getting flag {flag_key} from Redis: {e}")

        return None

    async def get_all_flags(self) -> list[FeatureFlag]:
        """Get all flags from Redis"""
        if not self.redis:
            return []

        try:
            pattern = f"{self.key_prefix}*"
            keys = await self.redis.keys(pattern)

            if not keys:
                return []

            values = await self.redis.mget(keys)
            flags = []

            for value in values:
                if value:
                    try:
                        flag_data = json.loads(value)
                        flags.append(FeatureFlag(**flag_data))
                    except Exception as e:
                        logger.error(f"Error parsing flag data: {e}")

            return flags
        except Exception as e:
            logger.error(f"Error getting all flags from Redis: {e}")
            return []

    async def save_flag(self, flag: FeatureFlag) -> bool:
        """Save flag to Redis"""
        if not self.redis:
            return False

        try:
            flag_data = flag.model_dump()
            # Convert datetime objects to ISO strings for JSON serialization
            for key, value in flag_data.items():
                if isinstance(value, datetime):
                    flag_data[key] = value.isoformat()
                elif isinstance(value, dict):
                    # Handle nested datetime objects
                    flag_data[key] = self._serialize_datetimes(value)

            await self.redis.set(
                f"{self.key_prefix}{flag.key}",
                json.dumps(flag_data, default=str),
                ex=86400 * 30,  # Expire after 30 days as backup
            )
            return True
        except Exception as e:
            logger.error(f"Error saving flag {flag.key} to Redis: {e}")
            return False

    async def delete_flag(self, flag_key: str) -> bool:
        """Delete flag from Redis"""
        if not self.redis:
            return False

        try:
            result = await self.redis.delete(f"{self.key_prefix}{flag_key}")
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting flag {flag_key} from Redis: {e}")
            return False

    def _serialize_datetimes(self, obj):
        """Recursively serialize datetime objects in nested structures"""
        if isinstance(obj, dict):
            return {k: self._serialize_datetimes(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetimes(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return obj


class DatabaseStorage(FeatureFlagStorage):
    """Database-based storage for feature flags"""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        self.engine = None
        self.session_factory = None

    async def initialize(self):
        """Initialize database connection"""
        try:
            from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

            self.engine = create_async_engine(self.database_url)
            self.session_factory = async_sessionmaker(self.engine)

            # Create tables if they don't exist
            async with self.engine.begin() as conn:
                from dotmac.database.base import Base

                await conn.run_sync(Base.metadata.create_all)

            logger.info("Database feature flag storage initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database storage: {e}")
            raise

    async def close(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()

    async def get_flag(self, flag_key: str) -> Optional[FeatureFlag]:
        """Get flag from database"""
        try:
            from sqlalchemy import select

            from .db_models import FeatureFlagModel

            async with self.session_factory() as session:
                result = await session.execute(select(FeatureFlagModel).where(FeatureFlagModel.key == flag_key))
                db_flag = result.scalar_one_or_none()

                if db_flag:
                    return db_flag.to_pydantic()
        except Exception as e:
            logger.error(f"Error getting flag {flag_key} from database: {e}")

        return None

    async def get_all_flags(self) -> list[FeatureFlag]:
        """Get all flags from database"""
        try:
            from sqlalchemy import select

            from .db_models import FeatureFlagModel

            async with self.session_factory() as session:
                result = await session.execute(select(FeatureFlagModel))
                db_flags = result.scalars().all()

                return [db_flag.to_pydantic() for db_flag in db_flags]
        except Exception as e:
            logger.error(f"Error getting all flags from database: {e}")
            return []

    async def save_flag(self, flag: FeatureFlag) -> bool:
        """Save flag to database"""
        try:
            from sqlalchemy import select

            from .db_models import FeatureFlagModel

            async with self.session_factory() as session:
                # Check if flag exists
                result = await session.execute(select(FeatureFlagModel).where(FeatureFlagModel.key == flag.key))
                db_flag = result.scalar_one_or_none()

                if db_flag:
                    # Update existing
                    db_flag.from_pydantic(flag)
                else:
                    # Create new
                    db_flag = FeatureFlagModel.from_pydantic(flag)
                    session.add(db_flag)

                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving flag {flag.key} to database: {e}")
            return False

    async def delete_flag(self, flag_key: str) -> bool:
        """Delete flag from database"""
        try:
            from sqlalchemy import delete

            from .db_models import FeatureFlagModel

            async with self.session_factory() as session:
                result = await session.execute(delete(FeatureFlagModel).where(FeatureFlagModel.key == flag_key))
                await session.commit()
                return result.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting flag {flag_key} from database: {e}")
            return False


class InMemoryStorage(FeatureFlagStorage):
    """In-memory storage for testing and development"""

    def __init__(self):
        self.flags: dict[str, FeatureFlag] = {}

    async def initialize(self):
        """Initialize in-memory storage"""
        logger.info("In-memory feature flag storage initialized")

    async def close(self):
        """Close in-memory storage"""
        self.flags.clear()

    async def get_flag(self, flag_key: str) -> Optional[FeatureFlag]:
        """Get flag from memory"""
        return self.flags.get(flag_key)

    async def get_all_flags(self) -> list[FeatureFlag]:
        """Get all flags from memory"""
        return list(self.flags.values())

    async def save_flag(self, flag: FeatureFlag) -> bool:
        """Save flag to memory"""
        self.flags[flag.key] = flag
        return True

    async def delete_flag(self, flag_key: str) -> bool:
        """Delete flag from memory"""
        return self.flags.pop(flag_key, None) is not None

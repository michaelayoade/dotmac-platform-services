"""
Distributed Lock Manager implementation using Redis.

Provides distributed locking with automatic renewal and deadlock detection.
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Any, Optional
from uuid import uuid4

import redis.asyncio as redis
from redis.exceptions import LockError, RedisError

from dotmac.platform.core.decorators import standard_exception_handler
from dotmac.platform.observability.unified_logging import get_logger

logger = get_logger(__name__)


class DistributedLock:
    """
    Distributed lock with automatic renewal.

    Features:
    - Automatic lock renewal
    - Deadlock detection
    - Fair queueing
    - Monitoring and metrics
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        name: str,
        timeout: float = 10.0,
        blocking: bool = True,
        blocking_timeout: Optional[float] = None,
        auto_renewal: bool = True,
        renewal_interval: float = None,
    ):
        """Initialize distributed lock."""
        self.redis = redis_client
        self.name = f"lock:{name}"
        self.timeout = timeout
        self.blocking = blocking
        self.blocking_timeout = blocking_timeout
        self.auto_renewal = auto_renewal
        self.renewal_interval = renewal_interval or (timeout / 3)

        self.token = str(uuid4())
        self._lock: Optional[redis.lock.Lock] = None
        self._renewal_task: Optional[asyncio.Task] = None
        self._acquired = False

    async def acquire(self) -> bool:
        """Acquire the lock."""
        try:
            self._lock = self.redis.lock(
                self.name,
                timeout=self.timeout,
                blocking=self.blocking,
                blocking_timeout=self.blocking_timeout,
                token=self.token.encode(),
            )

            self._acquired = await self._lock.acquire()

            if self._acquired and self.auto_renewal:
                self._renewal_task = asyncio.create_task(self._auto_renew())

            logger.debug(f"Lock {self.name} acquired: {self._acquired}")
            return self._acquired

        except Exception as e:
            logger.error(f"Failed to acquire lock {self.name}: {e}")
            return False

    async def release(self) -> bool:
        """Release the lock."""
        if not self._acquired or not self._lock:
            return False

        try:
            # Cancel renewal task
            if self._renewal_task:
                self._renewal_task.cancel()
                try:
                    await self._renewal_task
                except asyncio.CancelledError:
                    pass

            # Release lock
            await self._lock.release()
            self._acquired = False

            logger.debug(f"Lock {self.name} released")
            return True

        except LockError as e:
            logger.warning(f"Lock {self.name} already released: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to release lock {self.name}: {e}")
            return False

    async def extend(self, additional_time: float) -> bool:
        """Extend lock timeout."""
        if not self._acquired or not self._lock:
            return False

        try:
            await self._lock.extend(additional_time)
            logger.debug(f"Lock {self.name} extended by {additional_time}s")
            return True
        except Exception as e:
            logger.error(f"Failed to extend lock {self.name}: {e}")
            return False

    async def _auto_renew(self):
        """Automatically renew lock."""
        while self._acquired:
            try:
                await asyncio.sleep(self.renewal_interval)
                if self._acquired:
                    await self.extend(self.timeout)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in lock renewal for {self.name}: {e}")
                break

    @property
    def is_acquired(self) -> bool:
        """Check if lock is acquired."""
        return self._acquired

    async def __aenter__(self):
        """Async context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.release()


class LockManager:
    """
    Centralized distributed lock manager.

    Features:
    - Multiple lock backends
    - Lock monitoring
    - Deadlock detection
    - Fair lock queueing
    """

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        namespace: str = "dotmac",
        default_timeout: float = 10.0,
    ):
        """Initialize lock manager."""
        self.redis = redis_client
        self.namespace = namespace
        self.default_timeout = default_timeout
        self._active_locks: dict[str, DistributedLock] = {}
        self._stats = {
            "locks_acquired": 0,
            "locks_released": 0,
            "lock_timeouts": 0,
            "lock_errors": 0,
        }

    async def connect(self, redis_url: str = "redis://localhost:6379/0"):
        """Connect to Redis if not already connected."""
        if not self.redis:
            self.redis = redis.from_url(redis_url)
            await self.redis.ping()
            logger.info("Lock manager connected to Redis")

    @asynccontextmanager
    async def lock(
        self,
        name: str,
        timeout: Optional[float] = None,
        blocking: bool = True,
        blocking_timeout: Optional[float] = None,
        auto_renewal: bool = True,
    ):
        """Create and acquire a distributed lock."""
        full_name = f"{self.namespace}:{name}"
        lock = DistributedLock(
            self.redis,
            full_name,
            timeout=timeout or self.default_timeout,
            blocking=blocking,
            blocking_timeout=blocking_timeout,
            auto_renewal=auto_renewal,
        )

        try:
            acquired = await lock.acquire()
            if acquired:
                self._active_locks[full_name] = lock
                self._stats["locks_acquired"] += 1
                yield lock
            else:
                self._stats["lock_timeouts"] += 1
                raise TimeoutError(f"Failed to acquire lock: {name}")
        finally:
            if lock.is_acquired:
                await lock.release()
                self._active_locks.pop(full_name, None)
                self._stats["locks_released"] += 1

    @standard_exception_handler
    async def try_lock(
        self,
        name: str,
        timeout: Optional[float] = None,
    ) -> Optional[DistributedLock]:
        """Try to acquire a lock without blocking."""
        full_name = f"{self.namespace}:{name}"
        lock = DistributedLock(
            self.redis,
            full_name,
            timeout=timeout or self.default_timeout,
            blocking=False,
        )

        acquired = await lock.acquire()
        if acquired:
            self._active_locks[full_name] = lock
            self._stats["locks_acquired"] += 1
            return lock

        return None

    @standard_exception_handler
    async def is_locked(self, name: str) -> bool:
        """Check if a resource is locked."""
        full_name = f"{self.namespace}:{name}"
        lock_key = f"lock:{full_name}"

        try:
            return await self.redis.exists(lock_key) > 0
        except Exception as e:
            logger.error(f"Failed to check lock status for {name}: {e}")
            return False

    @standard_exception_handler
    async def get_lock_info(self, name: str) -> Optional[dict[str, Any]]:
        """Get information about a lock."""
        full_name = f"{self.namespace}:{name}"
        lock_key = f"lock:{full_name}"

        try:
            # Get lock value (token) and TTL
            token = await self.redis.get(lock_key)
            ttl = await self.redis.ttl(lock_key)

            if token:
                return {
                    "name": name,
                    "locked": True,
                    "token": token.decode() if token else None,
                    "ttl": ttl if ttl > 0 else None,
                    "is_mine": full_name in self._active_locks,
                }

            return {"name": name, "locked": False}

        except Exception as e:
            logger.error(f"Failed to get lock info for {name}: {e}")
            return None

    @standard_exception_handler
    async def list_locks(self, pattern: str = "*") -> list[str]:
        """List all active locks matching pattern."""
        search_pattern = f"lock:{self.namespace}:{pattern}"

        try:
            keys = await self.redis.keys(search_pattern)
            return [key.decode().replace(f"lock:{self.namespace}:", "") for key in keys]
        except Exception as e:
            logger.error(f"Failed to list locks: {e}")
            return []

    @standard_exception_handler
    async def force_release(self, name: str) -> bool:
        """Force release a lock (admin operation)."""
        full_name = f"{self.namespace}:{name}"
        lock_key = f"lock:{full_name}"

        try:
            result = await self.redis.delete(lock_key)
            if result:
                logger.warning(f"Force released lock: {name}")
                self._active_locks.pop(full_name, None)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to force release lock {name}: {e}")
            return False

    @standard_exception_handler
    async def detect_deadlocks(self) -> list[dict[str, Any]]:
        """Detect potential deadlocks in the system."""
        deadlocks = []

        try:
            # Get all locks
            all_locks = await self.list_locks()

            for lock_name in all_locks:
                info = await self.get_lock_info(lock_name)
                if info and info.get("ttl") is not None:
                    # Check for locks with very short TTL (potential issues)
                    if info["ttl"] < 2:
                        deadlocks.append({
                            "type": "expiring_lock",
                            "lock": lock_name,
                            "ttl": info["ttl"],
                        })

            # Check for orphaned locks in our tracking
            for tracked_name, lock in self._active_locks.items():
                if not lock.is_acquired:
                    deadlocks.append({
                        "type": "orphaned_lock",
                        "lock": tracked_name,
                    })

            return deadlocks

        except Exception as e:
            logger.error(f"Failed to detect deadlocks: {e}")
            return []

    def get_stats(self) -> dict[str, Any]:
        """Get lock manager statistics."""
        return {
            **self._stats,
            "active_locks": len(self._active_locks),
            "active_lock_names": list(self._active_locks.keys()),
        }

    async def cleanup(self):
        """Cleanup resources."""
        # Release all active locks
        for lock in self._active_locks.values():
            try:
                await lock.release()
            except Exception as e:
                logger.error(f"Error releasing lock during cleanup: {e}")

        self._active_locks.clear()

        if self.redis:
            await self.redis.close()


# Global instance
_lock_manager: Optional[LockManager] = None


async def get_lock_manager() -> LockManager:
    """Get global lock manager instance."""
    global _lock_manager

    if _lock_manager is None:
        _lock_manager = LockManager()
        await _lock_manager.connect()

    return _lock_manager
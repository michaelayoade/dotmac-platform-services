"""
Distributed Lock Manager for coordinating access across services.

Provides distributed locking, leader election, and semaphores.
"""

from .lock_manager import LockManager, DistributedLock, get_lock_manager

__all__ = [
    "LockManager",
    "DistributedLock",
    "get_lock_manager",
]

# Note: LeaderElection and DistributedSemaphore not yet implemented
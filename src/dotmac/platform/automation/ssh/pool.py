"""
SSH connection pooling for efficient connection reuse.
"""

import asyncio
import logging
import time
from collections import defaultdict
from typing import Optional

from .automation import SSHAutomation
from .types import (
    ConnectionStatus,
    DeviceCredentials,
    DeviceType,
    SSHConnection,
    SSHConnectionConfig,
    SSHPoolConfig,
)

logger = logging.getLogger(__name__)


class SSHConnectionPool:
    """
    SSH connection pool for efficient connection management.

    Provides connection pooling, reuse, and automatic cleanup for SSH connections.
    """

    def __init__(self, config: SSHPoolConfig = None):
        self.config = config or SSHPoolConfig()
        self.ssh_automation = SSHAutomation()

        # Connection pools by host
        self._pools: dict[str, list[SSHConnection]] = defaultdict(list)
        self._active_connections: dict[str, SSHConnection] = {}
        self._connection_usage: dict[str, int] = defaultdict(int)

        # Pool management
        self._pool_lock = asyncio.Lock()
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start connection pool."""
        if self._running:
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("SSH connection pool started")

    async def stop(self):
        """Stop connection pool and close all connections."""
        if not self._running:
            return

        self._running = False

        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Close all connections
        async with self._pool_lock:
            for pool in self._pools.values():
                for conn in pool:
                    await self.ssh_automation.disconnect(conn.connection_id)

            for conn in self._active_connections.values():
                await self.ssh_automation.disconnect(conn.connection_id)

            self._pools.clear()
            self._active_connections.clear()
            self._connection_usage.clear()

        logger.info("SSH connection pool stopped")

    async def get_connection(
        self,
        host: str,
        credentials: DeviceCredentials,
        config: Optional[SSHConnectionConfig] = None,
        device_type: DeviceType = DeviceType.UNKNOWN,
    ) -> SSHConnection:
        """
        Get SSH connection from pool or create new one.

        Args:
            host: Target hostname or IP
            credentials: Authentication credentials
            config: Connection configuration
            device_type: Device type

        Returns:
            SSH connection ready for use
        """
        pool_key = f"{host}:{credentials.username}"

        async with self._pool_lock:
            # Try to get connection from pool
            pool = self._pools[pool_key]
            if pool:
                connection = pool.pop(0)

                # Verify connection is still active
                if connection.status == ConnectionStatus.CONNECTED:
                    self._active_connections[connection.connection_id] = connection
                    self._connection_usage[connection.connection_id] += 1
                    connection.update_last_used()

                    logger.debug(f"Reusing pooled connection to {host}")
                    return connection
                else:
                    # Connection is stale, remove it
                    await self.ssh_automation.disconnect(connection.connection_id)

            # Check if we've exceeded max connections
            total_connections = len(self._active_connections) + sum(
                len(p) for p in self._pools.values()
            )
            if total_connections >= self.config.max_connections:
                # Try to find and close an idle connection
                oldest_conn = await self._find_oldest_idle_connection()
                if oldest_conn:
                    await self._close_connection(oldest_conn)
                else:
                    raise Exception(
                        f"Connection pool exhausted (max: {self.config.max_connections})"
                    )

            # Create new connection
            connection = await self.ssh_automation.connect(
                host=host,
                credentials=credentials,
                config=config or SSHConnectionConfig(host=host),
                device_type=device_type,
            )

            self._active_connections[connection.connection_id] = connection
            self._connection_usage[connection.connection_id] = 1

            logger.info(f"Created new pooled connection to {host}")
            return connection

    async def return_connection(self, connection: SSHConnection):
        """
        Return connection to pool for reuse.

        Args:
            connection: SSH connection to return
        """
        async with self._pool_lock:
            if connection.connection_id not in self._active_connections:
                logger.warning(
                    f"Attempted to return unknown connection {connection.connection_id}"
                )
                return

            # Remove from active connections
            del self._active_connections[connection.connection_id]

            # Check if connection is still healthy
            if connection.status != ConnectionStatus.CONNECTED:
                await self.ssh_automation.disconnect(connection.connection_id)
                return

            # Check connection age
            age = time.time() - connection.created_at.timestamp()
            if age > self.config.max_connection_age:
                logger.debug(f"Connection {connection.connection_id} too old, closing")
                await self.ssh_automation.disconnect(connection.connection_id)
                return

            # Return to pool
            pool_key = f"{connection.host}:{connection.username}"
            pool = self._pools[pool_key]

            # Limit pool size per host
            max_pool_size = max(1, self.config.max_connections // 4)
            if len(pool) < max_pool_size:
                pool.append(connection)
                logger.debug(f"Returned connection to pool: {connection.connection_id}")
            else:
                # Pool is full, close connection
                await self.ssh_automation.disconnect(connection.connection_id)

    async def _cleanup_loop(self):
        """Background cleanup task for idle connections."""
        while self._running:
            try:
                await self._cleanup_idle_connections()
                await asyncio.sleep(self.config.cleanup_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in connection pool cleanup: {e}")
                await asyncio.sleep(10)

    async def _cleanup_idle_connections(self):
        """Clean up idle connections from pools."""
        current_time = time.time()

        async with self._pool_lock:
            for pool_key, pool in list(self._pools.items()):
                # Remove idle connections
                remaining = []
                for conn in pool:
                    idle_time = current_time - conn.last_used.timestamp()
                    age = current_time - conn.created_at.timestamp()

                    if (
                        idle_time > self.config.idle_timeout
                        or age > self.config.max_connection_age
                        or conn.status != ConnectionStatus.CONNECTED
                    ):
                        await self.ssh_automation.disconnect(conn.connection_id)
                        logger.debug(f"Cleaned up idle connection {conn.connection_id}")
                    else:
                        remaining.append(conn)

                if remaining:
                    self._pools[pool_key] = remaining
                else:
                    del self._pools[pool_key]

    async def _find_oldest_idle_connection(self) -> Optional[SSHConnection]:
        """Find oldest idle connection to close."""
        oldest_conn = None
        oldest_time = float("inf")

        for pool in self._pools.values():
            for conn in pool:
                if conn.last_used.timestamp() < oldest_time:
                    oldest_time = conn.last_used.timestamp()
                    oldest_conn = conn

        return oldest_conn

    async def _close_connection(self, connection: SSHConnection):
        """Close and remove connection from pool."""
        # Remove from pools
        for _pool_key, pool in self._pools.items():
            if connection in pool:
                pool.remove(connection)
                break

        # Remove from active if present
        if connection.connection_id in self._active_connections:
            del self._active_connections[connection.connection_id]

        # Close connection
        await self.ssh_automation.disconnect(connection.connection_id)

    def get_pool_stats(self) -> dict[str, any]:
        """Get connection pool statistics."""
        return {
            "active_connections": len(self._active_connections),
            "pooled_connections": sum(len(p) for p in self._pools.values()),
            "total_pools": len(self._pools),
            "max_connections": self.config.max_connections,
            "pool_utilization": (
                len(self._active_connections) / self.config.max_connections
            )
            * 100,
        }

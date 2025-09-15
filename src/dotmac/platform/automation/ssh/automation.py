"""
SSH automation for device management and provisioning.

Provides direct SSH connection and command execution capabilities
using asyncssh with proper error handling and connection management.
"""

import asyncio
import logging
from typing import Optional
from uuid import uuid4

import asyncssh

from .types import (
    ConnectionStatus,
    DeviceCredentials,
    DeviceType,
    SSHAuthenticationError,
    SSHCommandError,
    SSHConnection,
    SSHConnectionConfig,
    SSHConnectionError,
    SSHResponse,
    SSHTimeoutError,
)

logger = logging.getLogger(__name__)


class SSHAutomation:
    """
    SSH automation engine for device management.

    Provides direct SSH connection and command execution capabilities
    with proper error handling and connection lifecycle management.
    """

    def __init__(self):
        self._connections: dict[str, asyncssh.SSHClientConnection] = {}
        self._connection_metadata: dict[str, SSHConnection] = {}

    async def connect(
        self,
        host: str,
        credentials: DeviceCredentials,
        config: SSHConnectionConfig,
        device_type: DeviceType,
    ) -> SSHConnection:
        """
        Establish SSH connection to a device.

        Args:
            host: Target hostname or IP address
            credentials: SSH credentials (username, password, key)
            config: SSH connection configuration
            device_type: Type of device being connected to

        Returns:
            SSHConnection object with connection details

        Raises:
            SSHConnectionError: If connection fails
            SSHAuthenticationError: If authentication fails
            SSHTimeoutError: If connection times out
        """
        connection_id = str(uuid4())

        try:
            logger.info(f"Connecting to {host}:{config.port} (connection: {connection_id})")

            # Prepare connection options
            connect_options = {
                "host": host,
                "port": config.port,
                "username": credentials.username,
                "connect_timeout": config.timeout,
                "keepalive_interval": 30,
            }

            # Add authentication method
            if credentials.ssh_key:
                # Use SSH key authentication
                connect_options["client_keys"] = [credentials.ssh_key]
            elif credentials.password:
                # Use password authentication
                connect_options["password"] = credentials.password
            else:
                raise SSHAuthenticationError("No authentication method provided")

            # Establish connection
            conn = await asyncio.wait_for(
                asyncssh.connect(**connect_options),
                timeout=config.timeout
            )

            # Create connection metadata
            ssh_connection = SSHConnection(
                connection_id=connection_id,
                host=host,
                port=config.port,
                device_type=device_type,
                status=ConnectionStatus.CONNECTED,
                credentials=credentials,
                config=config,
            )

            # Store connections
            self._connections[connection_id] = conn
            self._connection_metadata[connection_id] = ssh_connection

            logger.info(f"✅ Connected to {host} (connection: {connection_id})")
            return ssh_connection

        except asyncio.TimeoutError as e:
            error_msg = f"Connection timeout to {host}:{config.port}"
            logger.error(f"❌ {error_msg}")
            raise SSHTimeoutError(error_msg) from e

        except asyncssh.PermissionDenied as e:
            error_msg = f"Authentication failed for {credentials.username}@{host}"
            logger.error(f"❌ {error_msg}")
            raise SSHAuthenticationError(error_msg) from e

        except (asyncssh.Error, OSError) as e:
            error_msg = f"Failed to connect to {host}:{config.port}: {e}"
            logger.error(f"❌ {error_msg}")
            raise SSHConnectionError(error_msg) from e

    async def execute_command(
        self,
        connection_id: str,
        command: str,
        timeout: Optional[float] = None,
    ) -> SSHResponse:
        """
        Execute command on SSH connection.

        Args:
            connection_id: ID of established SSH connection
            command: Command to execute
            timeout: Command execution timeout (optional)

        Returns:
            SSHResponse with command results

        Raises:
            SSHConnectionError: If connection not found or invalid
            SSHCommandError: If command execution fails
            SSHTimeoutError: If command times out
        """
        if connection_id not in self._connections:
            raise SSHConnectionError(f"Connection {connection_id} not found")

        conn = self._connections[connection_id]
        metadata = self._connection_metadata[connection_id]

        try:
            logger.debug(f"Executing command on {metadata.host}: {command}")

            # Execute command with timeout
            execution_timeout = timeout or metadata.config.timeout
            result = await asyncio.wait_for(
                conn.run(command),
                timeout=execution_timeout
            )

            # Create response
            response = SSHResponse(
                command=command,
                exit_code=result.exit_status,
                output=result.stdout,
                error=result.stderr,
                success=result.exit_status == 0,
                execution_time=0.0,  # asyncssh doesn't provide timing
            )

            if response.success:
                logger.debug(f"✅ Command executed successfully: {command}")
            else:
                logger.warning(f"⚠️  Command failed (exit {result.exit_status}): {command}")

            return response

        except asyncio.TimeoutError as e:
            error_msg = f"Command timeout: {command}"
            logger.error(f"❌ {error_msg}")
            raise SSHTimeoutError(error_msg) from e

        except asyncssh.Error as e:
            error_msg = f"Command execution failed: {command} - {e}"
            logger.error(f"❌ {error_msg}")
            raise SSHCommandError(error_msg) from e

    async def disconnect(self, connection_id: str) -> None:
        """
        Disconnect specific SSH connection.

        Args:
            connection_id: ID of connection to disconnect
        """
        if connection_id not in self._connections:
            logger.warning(f"Connection {connection_id} not found for disconnection")
            return

        conn = self._connections[connection_id]
        metadata = self._connection_metadata[connection_id]

        try:
            logger.info(f"Disconnecting from {metadata.host} (connection: {connection_id})")
            conn.close()
            await conn.wait_closed()

            # Update metadata status
            metadata.status = ConnectionStatus.DISCONNECTED

            logger.info(f"✅ Disconnected from {metadata.host}")

        except Exception as e:
            logger.error(f"❌ Error during disconnection: {e}")

        finally:
            # Clean up connection references
            self._connections.pop(connection_id, None)
            self._connection_metadata.pop(connection_id, None)

    async def disconnect_all(self) -> None:
        """
        Disconnect all active SSH connections.
        """
        if not self._connections:
            logger.info("No active connections to disconnect")
            return

        logger.info(f"Disconnecting {len(self._connections)} active connections")

        # Disconnect all connections concurrently
        disconnect_tasks = [
            self.disconnect(connection_id)
            for connection_id in list(self._connections.keys())
        ]

        await asyncio.gather(*disconnect_tasks, return_exceptions=True)

        logger.info("✅ All connections disconnected")

    def get_connection_info(self, connection_id: str) -> Optional[SSHConnection]:
        """
        Get connection metadata by ID.

        Args:
            connection_id: Connection ID

        Returns:
            SSHConnection metadata or None if not found
        """
        return self._connection_metadata.get(connection_id)

    def list_active_connections(self) -> list[SSHConnection]:
        """
        List all active SSH connections.

        Returns:
            List of active SSH connection metadata
        """
        return list(self._connection_metadata.values())

    async def is_connection_alive(self, connection_id: str) -> bool:
        """
        Check if SSH connection is still alive.

        Args:
            connection_id: Connection ID to check

        Returns:
            True if connection is alive, False otherwise
        """
        if connection_id not in self._connections:
            return False

        conn = self._connections[connection_id]

        try:
            # Try a simple echo command to test connectivity
            await asyncio.wait_for(conn.run("echo test"), timeout=5.0)
            return True
        except Exception:
            # Connection is dead, clean it up
            await self.disconnect(connection_id)
            return False

"""
RADIUS server management and orchestration.
"""

import asyncio
import hashlib
import logging
import socket
import struct
from contextlib import asynccontextmanager
from typing import Any, Optional

from .accounting import RADIUSAccounting
from .auth import RADIUSAuthenticator
from .coa import CoAManager
from .session import RADIUSSessionManager
from .types import (
    RADIUSAttribute,
    RADIUSAttributeType,
    RADIUSClient,
    RADIUSPacket,
    RADIUSPacketType,
    RADIUSResponse,
    RADIUSServerConfig,
    RADIUSSession,
    RADIUSSessionStatus,
    RADIUSUser,
)

logger = logging.getLogger(__name__)


class RADIUSManager:
    """
    Main RADIUS server manager orchestrating all RADIUS operations.

    Provides centralized management for:
    - Authentication and authorization
    - Session management and tracking
    - Accounting and usage monitoring
    - Change of Authorization (CoA)
    - Client management and configuration
    """

    def __init__(self, config: RADIUSServerConfig):
        self.config = config
        self._running = False
        self._auth_socket: Optional[socket.socket] = None
        self._acct_socket: Optional[socket.socket] = None
        self._coa_socket: Optional[socket.socket] = None

        # Core components
        self.authenticator = RADIUSAuthenticator()
        self.session_manager = RADIUSSessionManager()
        self.accounting = RADIUSAccounting()
        self.coa_manager = CoAManager()

        # Storage
        self._clients: dict[str, RADIUSClient] = {}
        self._users: dict[str, RADIUSUser] = {}
        self._active_sessions: dict[str, RADIUSSession] = {}

        # Packet handling
        self._packet_handlers = {
            RADIUSPacketType.ACCESS_REQUEST: self._handle_access_request,
            RADIUSPacketType.ACCOUNTING_REQUEST: self._handle_accounting_request,
        }

    async def start(self):
        """Start the RADIUS server."""
        if self._running:
            logger.warning("RADIUS server is already running")
            return

        try:
            # Create and bind sockets
            await self._create_sockets()

            # Start component managers
            await self.session_manager.start()
            await self.accounting.start()
            await self.coa_manager.start()

            self._running = True
            logger.info(f"RADIUS server started on {self.config.bind_address}")

            # Start packet processing tasks
            tasks = []
            if self._auth_socket:
                tasks.append(asyncio.create_task(self._process_auth_packets()))
            if self._acct_socket and self.config.enable_accounting:
                tasks.append(asyncio.create_task(self._process_acct_packets()))
            if self._coa_socket and self.config.enable_coa:
                tasks.append(asyncio.create_task(self._process_coa_packets()))

            # Wait for all tasks
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"Failed to start RADIUS server: {e}")
            await self.stop()
            raise

    async def stop(self):
        """Stop the RADIUS server."""
        if not self._running:
            return

        self._running = False

        # Close sockets
        for sock in [self._auth_socket, self._acct_socket, self._coa_socket]:
            if sock:
                sock.close()

        # Stop components
        await self.session_manager.stop()
        await self.accounting.stop()
        await self.coa_manager.stop()

        logger.info("RADIUS server stopped")

    async def _create_sockets(self):
        """Create and configure server sockets."""
        # Authentication socket
        self._auth_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._auth_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._auth_socket.bind((self.config.bind_address, self.config.auth_port))
        self._auth_socket.setblocking(False)

        # Accounting socket
        if self.config.enable_accounting:
            self._acct_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._acct_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._acct_socket.bind((self.config.bind_address, self.config.acct_port))
            self._acct_socket.setblocking(False)

        # CoA socket
        if self.config.enable_coa:
            self._coa_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._coa_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._coa_socket.bind((self.config.bind_address, self.config.coa_port))
            self._coa_socket.setblocking(False)

    async def _process_auth_packets(self):
        """Process authentication packets."""
        while self._running:
            try:
                loop = asyncio.get_event_loop()
                data, addr = await loop.sock_recvfrom(
                    self._auth_socket, self.config.max_packet_size
                )

                # Process packet in background
                asyncio.create_task(self._handle_packet(data, addr, self._auth_socket))

            except Exception as e:
                if self._running:
                    logger.error(f"Error processing auth packet: {e}")
                await asyncio.sleep(0.01)

    async def _process_acct_packets(self):
        """Process accounting packets."""
        while self._running and self._acct_socket:
            try:
                loop = asyncio.get_event_loop()
                data, addr = await loop.sock_recvfrom(
                    self._acct_socket, self.config.max_packet_size
                )

                # Process packet in background
                asyncio.create_task(self._handle_packet(data, addr, self._acct_socket))

            except Exception as e:
                if self._running:
                    logger.error(f"Error processing acct packet: {e}")
                await asyncio.sleep(0.01)

    async def _process_coa_packets(self):
        """Process CoA packets."""
        while self._running and self._coa_socket:
            try:
                loop = asyncio.get_event_loop()
                data, addr = await loop.sock_recvfrom(
                    self._coa_socket, self.config.max_packet_size
                )

                # Process packet in background
                asyncio.create_task(self._handle_packet(data, addr, self._coa_socket))

            except Exception as e:
                if self._running:
                    logger.error(f"Error processing CoA packet: {e}")
                await asyncio.sleep(0.01)

    async def _handle_packet(self, data: bytes, addr: tuple, sock: socket.socket):
        """Handle incoming RADIUS packet."""
        try:
            client_ip = addr[0]

            # Validate client
            client = self._get_client(client_ip)
            if not client:
                logger.warning(f"Unknown client {client_ip}")
                return

            # Parse packet
            packet = self._parse_packet(data, client.shared_secret)
            if not packet:
                logger.warning(f"Invalid packet from {client_ip}")
                return

            # Handle packet by type
            handler = self._packet_handlers.get(packet.packet_type)
            if handler:
                response = await handler(packet, client)
                if response:
                    response_data = self._build_response_packet(
                        response, client.shared_secret
                    )
                    loop = asyncio.get_event_loop()
                    await loop.sock_sendto(sock, response_data, addr)
            else:
                logger.warning(f"Unhandled packet type: {packet.packet_type}")

        except Exception as e:
            logger.error(f"Error handling packet from {addr}: {e}")

    def _parse_packet(self, data: bytes, shared_secret: str) -> Optional[RADIUSPacket]:
        """Parse raw RADIUS packet data."""
        if len(data) < 20:
            return None

        try:
            # Parse header
            packet_type, packet_id, length = struct.unpack("!BBH", data[:4])
            authenticator = data[4:20]

            # Verify length
            if len(data) != length:
                return None

            # Parse attributes
            attributes = []
            offset = 20
            while offset < len(data):
                if offset + 2 > len(data):
                    break

                attr_type, attr_length = struct.unpack("!BB", data[offset : offset + 2])
                if attr_length < 2 or offset + attr_length > len(data):
                    break

                attr_value = data[offset + 2 : offset + attr_length]
                attributes.append(RADIUSAttribute(attr_type, attr_value))
                offset += attr_length

            return RADIUSPacket(
                packet_type=RADIUSPacketType(packet_type),
                packet_id=packet_id,
                authenticator=authenticator,
                attributes=attributes,
            )

        except (struct.error, ValueError) as e:
            logger.error(f"Packet parsing error: {e}")
            return None

    def _build_response_packet(
        self, response: RADIUSResponse, shared_secret: str
    ) -> bytes:
        """Build RADIUS response packet."""
        if not response.packet:
            return b""

        packet = response.packet

        # Build attributes data
        attrs_data = b""
        for attr in packet.attributes:
            if isinstance(attr.value, str):
                value = attr.value.encode("utf-8")
            elif isinstance(attr.value, int):
                value = struct.pack("!I", attr.value)
            else:
                value = attr.value

            attr_data = struct.pack("!BB", attr.type, len(value) + 2) + value
            attrs_data += attr_data

        # Build packet
        length = 20 + len(attrs_data)
        header = struct.pack("!BBH", packet.packet_type, packet.packet_id, length)

        # Calculate response authenticator
        # MD5 is required by RADIUS protocol RFC 2865 - not used for security
        auth_data = (
            header + packet.authenticator + attrs_data + shared_secret.encode("utf-8")
        )
        response_auth = hashlib.md5(auth_data, usedforsecurity=False).digest()  # nosec B324

        return header + response_auth + attrs_data

    async def _handle_access_request(
        self, packet: RADIUSPacket, client: RADIUSClient
    ) -> Optional[RADIUSResponse]:
        """Handle ACCESS-REQUEST packet."""
        try:
            # Extract authentication info
            username_attr = packet.get_attribute(RADIUSAttributeType.USER_NAME)
            if not username_attr:
                return self._create_access_reject(packet.packet_id, "Missing username")

            username = (
                username_attr.value.decode("utf-8")
                if isinstance(username_attr.value, bytes)
                else str(username_attr.value)
            )

            # Authenticate user
            auth_result = await self.authenticator.authenticate(
                packet, username, client
            )

            if auth_result.success:
                # Create session
                session = await self._create_session(packet, username, client)

                # Create ACCESS-ACCEPT
                response_packet = RADIUSPacket(
                    packet_type=RADIUSPacketType.ACCESS_ACCEPT,
                    packet_id=packet.packet_id,
                    authenticator=packet.authenticator,
                )

                # Add session attributes
                if session.framed_ip:
                    response_packet.add_attribute(
                        RADIUSAttributeType.FRAMED_IP_ADDRESS,
                        socket.inet_aton(session.framed_ip),
                    )

                return RADIUSResponse.success_response(
                    message="Access granted",
                    packet=response_packet,
                    session_id=session.session_id,
                )
            else:
                return self._create_access_reject(packet.packet_id, auth_result.message)

        except Exception as e:
            logger.error(f"Error handling access request: {e}")
            return self._create_access_reject(packet.packet_id, "Internal server error")

    async def _handle_accounting_request(
        self, packet: RADIUSPacket, client: RADIUSClient
    ) -> Optional[RADIUSResponse]:
        """Handle ACCOUNTING-REQUEST packet."""
        try:
            await self.accounting.process_accounting_request(packet, client)

            # Create ACCOUNTING-RESPONSE
            response_packet = RADIUSPacket(
                packet_type=RADIUSPacketType.ACCOUNTING_RESPONSE,
                packet_id=packet.packet_id,
                authenticator=packet.authenticator,
            )

            return RADIUSResponse.success_response(
                message="Accounting processed", packet=response_packet
            )

        except Exception as e:
            logger.error(f"Error handling accounting request: {e}")
            return None

    def _create_access_reject(self, packet_id: int, reason: str) -> RADIUSResponse:
        """Create ACCESS-REJECT response."""
        response_packet = RADIUSPacket(
            packet_type=RADIUSPacketType.ACCESS_REJECT,
            packet_id=packet_id,
            authenticator=b"\x00" * 16,
        )

        if reason:
            response_packet.add_attribute(RADIUSAttributeType.REPLY_MESSAGE, reason)

        return RADIUSResponse.error_response(
            message=reason, error_code="ACCESS_REJECTED", packet=response_packet
        )

    async def _create_session(
        self, packet: RADIUSPacket, username: str, client: RADIUSClient
    ) -> RADIUSSession:
        """Create new RADIUS session from access request."""
        # Extract session info from packet
        packet.get_attribute(RADIUSAttributeType.NAS_IP_ADDRESS)
        nas_port_attr = packet.get_attribute(RADIUSAttributeType.NAS_PORT)
        calling_station_attr = packet.get_attribute(
            RADIUSAttributeType.CALLING_STATION_ID
        )
        called_station_attr = packet.get_attribute(
            RADIUSAttributeType.CALLED_STATION_ID
        )

        session = RADIUSSession(
            username=username,
            nas_ip=client.ip_address,
            nas_port=(
                struct.unpack("!I", nas_port_attr.value)[0] if nas_port_attr else None
            ),
            calling_station_id=(
                calling_station_attr.value.decode("utf-8")
                if calling_station_attr
                else ""
            ),
            called_station_id=(
                called_station_attr.value.decode("utf-8") if called_station_attr else ""
            ),
            status=RADIUSSessionStatus.ACTIVE,
        )

        # Store session
        await self.session_manager.create_session(session)
        self._active_sessions[session.session_id] = session

        return session

    def _get_client(self, ip_address: str) -> Optional[RADIUSClient]:
        """Get RADIUS client by IP address."""
        return self._clients.get(ip_address)

    # Client Management
    def add_client(self, client: RADIUSClient):
        """Add RADIUS client."""
        self._clients[client.ip_address] = client
        logger.info(f"Added RADIUS client: {client.name} ({client.ip_address})")

    def remove_client(self, ip_address: str):
        """Remove RADIUS client."""
        if ip_address in self._clients:
            del self._clients[ip_address]
            logger.info(f"Removed RADIUS client: {ip_address}")

    def get_clients(self) -> list[RADIUSClient]:
        """Get all RADIUS clients."""
        return list(self._clients.values())

    # User Management
    def add_user(self, user: RADIUSUser):
        """Add RADIUS user."""
        self._users[user.username] = user
        logger.info(f"Added RADIUS user: {user.username}")

    def remove_user(self, username: str):
        """Remove RADIUS user."""
        if username in self._users:
            del self._users[username]
            logger.info(f"Removed RADIUS user: {username}")

    def get_user(self, username: str) -> Optional[RADIUSUser]:
        """Get RADIUS user by username."""
        return self._users.get(username)

    def get_users(self) -> list[RADIUSUser]:
        """Get all RADIUS users."""
        return list(self._users.values())

    # Session Management
    def get_active_sessions(self) -> list[RADIUSSession]:
        """Get all active sessions."""
        return list(self._active_sessions.values())

    def get_session(self, session_id: str) -> Optional[RADIUSSession]:
        """Get session by ID."""
        return self._active_sessions.get(session_id)

    async def disconnect_session(
        self, session_id: str, reason: str = "Administrative disconnect"
    ) -> bool:
        """Disconnect active session."""
        session = self._active_sessions.get(session_id)
        if not session:
            return False

        try:
            # Send CoA disconnect
            await self.coa_manager.disconnect_session(session, reason)

            # Update session status
            session.status = RADIUSSessionStatus.TERMINATED
            await self.session_manager.update_session(session)

            # Remove from active sessions
            del self._active_sessions[session_id]

            return True

        except Exception as e:
            logger.error(f"Error disconnecting session {session_id}: {e}")
            return False

    # Statistics and Monitoring
    def get_server_stats(self) -> dict[str, Any]:
        """Get server statistics."""
        return {
            "running": self._running,
            "active_sessions": len(self._active_sessions),
            "registered_clients": len(self._clients),
            "registered_users": len(self._users),
            "auth_port": self.config.auth_port,
            "acct_port": self.config.acct_port,
            "coa_port": self.config.coa_port,
            "accounting_enabled": self.config.enable_accounting,
            "coa_enabled": self.config.enable_coa,
        }

    @asynccontextmanager
    async def server_context(self):
        """Context manager for RADIUS server lifecycle."""
        try:
            await self.start()
            yield self
        finally:
            await self.stop()

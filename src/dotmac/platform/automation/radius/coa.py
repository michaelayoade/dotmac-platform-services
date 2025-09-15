"""
RADIUS Change of Authorization (CoA) manager.
"""

import asyncio
import logging
import socket
import struct
from typing import Optional

from .types import (
    RADIUSAttributeType,
    RADIUSPacket,
    RADIUSPacketType,
    RADIUSSession,
)

logger = logging.getLogger(__name__)


class CoAManager:
    """
    RADIUS Change of Authorization manager.

    Implements RFC 3576 for dynamic session management:
    - Disconnect sessions
    - Change session attributes
    - Send policy updates
    """

    def __init__(self):
        self._coa_socket: Optional[socket.socket] = None
        self._running = False
        self._coa_requests: dict[int, asyncio.Future] = {}
        self._packet_id_counter = 1

    async def start(self):
        """Start CoA manager."""
        if self._running:
            return

        self._running = True
        logger.info("RADIUS CoA manager started")

    async def stop(self):
        """Stop CoA manager."""
        if not self._running:
            return

        self._running = False

        if self._coa_socket:
            self._coa_socket.close()
            self._coa_socket = None

        # Cancel pending requests
        for future in self._coa_requests.values():
            if not future.done():
                future.cancel()

        self._coa_requests.clear()
        logger.info("RADIUS CoA manager stopped")

    async def disconnect_session(
        self, session: RADIUSSession, reason: str = "Administrative disconnect"
    ) -> bool:
        """
        Send CoA disconnect request for session.

        Args:
            session: RADIUS session to disconnect
            reason: Disconnect reason

        Returns:
            True if disconnect successful
        """
        try:
            # Create disconnect request packet
            packet = RADIUSPacket(
                packet_type=RADIUSPacketType.DISCONNECT_REQUEST,
                packet_id=self._get_next_packet_id(),
                authenticator=b"\x00" * 16,  # Will be calculated properly
            )

            # Add session identification attributes
            if session.username:
                packet.add_attribute(RADIUSAttributeType.USER_NAME, session.username)

            if session.session_id:
                packet.add_attribute(
                    RADIUSAttributeType.ACCT_SESSION_ID, session.session_id
                )

            if session.nas_ip:
                packet.add_attribute(
                    RADIUSAttributeType.NAS_IP_ADDRESS, socket.inet_aton(session.nas_ip)
                )

            if session.nas_port is not None:
                packet.add_attribute(
                    RADIUSAttributeType.NAS_PORT, struct.pack("!I", session.nas_port)
                )

            if session.framed_ip:
                packet.add_attribute(
                    RADIUSAttributeType.FRAMED_IP_ADDRESS,
                    socket.inet_aton(session.framed_ip),
                )

            # Add disconnect reason
            packet.add_attribute(RADIUSAttributeType.REPLY_MESSAGE, reason)

            # Send disconnect request
            response = await self._send_coa_request(session.nas_ip, packet)

            if response and response.packet_type == RADIUSPacketType.DISCONNECT_ACK:
                logger.info(f"Session {session.session_id} disconnected successfully")
                return True
            else:
                logger.warning(f"Session {session.session_id} disconnect failed")
                return False

        except Exception as e:
            logger.error(f"Error disconnecting session {session.session_id}: {e}")
            return False

    async def change_session_attributes(
        self, session: RADIUSSession, attributes: dict[int, bytes]
    ) -> bool:
        """
        Send CoA request to change session attributes.

        Args:
            session: RADIUS session to modify
            attributes: Dictionary of attribute type -> value

        Returns:
            True if change successful
        """
        try:
            # Create CoA request packet
            packet = RADIUSPacket(
                packet_type=RADIUSPacketType.COA_REQUEST,
                packet_id=self._get_next_packet_id(),
                authenticator=b"\x00" * 16,  # Will be calculated properly
            )

            # Add session identification attributes
            if session.username:
                packet.add_attribute(RADIUSAttributeType.USER_NAME, session.username)

            if session.session_id:
                packet.add_attribute(
                    RADIUSAttributeType.ACCT_SESSION_ID, session.session_id
                )

            # Add new attributes to apply
            for attr_type, attr_value in attributes.items():
                packet.add_attribute(attr_type, attr_value)

            # Send CoA request
            response = await self._send_coa_request(session.nas_ip, packet)

            if response and response.packet_type == RADIUSPacketType.COA_ACK:
                logger.info(
                    f"Session {session.session_id} attributes changed successfully"
                )
                return True
            else:
                logger.warning(f"Session {session.session_id} attribute change failed")
                return False

        except Exception as e:
            logger.error(f"Error changing session {session.session_id} attributes: {e}")
            return False

    async def _send_coa_request(
        self, nas_ip: str, packet: RADIUSPacket
    ) -> Optional[RADIUSPacket]:
        """
        Send CoA request to NAS.

        Args:
            nas_ip: NAS IP address
            packet: CoA request packet

        Returns:
            Response packet or None
        """
        try:
            # Create socket if needed
            if not self._coa_socket:
                self._coa_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self._coa_socket.settimeout(5.0)

            # Build packet data (simplified)
            packet_data = self._build_coa_packet(packet)

            # Send packet
            self._coa_socket.sendto(packet_data, (nas_ip, 3799))  # CoA port

            # Wait for response
            response_data, addr = self._coa_socket.recvfrom(4096)

            # Parse response (simplified)
            response = self._parse_coa_response(response_data)

            return response

        except socket.timeout:
            logger.error(f"CoA request to {nas_ip} timed out")
            return None
        except Exception as e:
            logger.error(f"Error sending CoA request to {nas_ip}: {e}")
            return None

    def _build_coa_packet(self, packet: RADIUSPacket) -> bytes:
        """Build CoA packet data (simplified implementation)."""
        # This would implement proper RADIUS packet building
        # For now, return minimal packet
        header = struct.pack("!BBH", packet.packet_type.value, packet.packet_id, 20)
        authenticator = b"\x00" * 16
        return header + authenticator

    def _parse_coa_response(self, data: bytes) -> Optional[RADIUSPacket]:
        """Parse CoA response packet (simplified implementation)."""
        if len(data) < 20:
            return None

        try:
            packet_type, packet_id, length = struct.unpack("!BBH", data[:4])
            authenticator = data[4:20]

            return RADIUSPacket(
                packet_type=RADIUSPacketType(packet_type),
                packet_id=packet_id,
                authenticator=authenticator,
            )

        except (struct.error, ValueError):
            return None

    def _get_next_packet_id(self) -> int:
        """Get next packet ID."""
        packet_id = self._packet_id_counter
        self._packet_id_counter = (self._packet_id_counter + 1) % 256
        return packet_id

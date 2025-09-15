"""
RADIUS accounting processor.
"""

import logging
import socket
from datetime import UTC

from .types import (
    AcctStatusType,
    RADIUSAttributeType,
    RADIUSClient,
    RADIUSPacket,
    RADIUSResponse,
)

logger = logging.getLogger(__name__)


class RADIUSAccounting:
    """
    RADIUS accounting processor.

    Handles RADIUS accounting requests for session tracking and usage monitoring.
    """

    def __init__(self):
        self._accounting_records: list[dict] = []
        self._running = False

    async def start(self):
        """Start accounting processor."""
        self._running = True
        logger.info("RADIUS accounting processor started")

    async def stop(self):
        """Stop accounting processor."""
        self._running = False
        logger.info("RADIUS accounting processor stopped")

    async def process_accounting_request(
        self, packet: RADIUSPacket, client: RADIUSClient
    ) -> RADIUSResponse:
        """
        Process RADIUS accounting request.

        Args:
            packet: RADIUS accounting request packet
            client: RADIUS client making request

        Returns:
            RADIUSResponse with processing result
        """
        try:
            # Extract accounting information
            acct_status_attr = packet.get_attribute(
                RADIUSAttributeType.ACCT_STATUS_TYPE
            )
            if not acct_status_attr:
                return RADIUSResponse.error_response(
                    "Missing Acct-Status-Type", "MISSING_ACCT_STATUS"
                )

            acct_status = AcctStatusType(int.from_bytes(acct_status_attr.value, "big"))

            # Process based on accounting status type
            if acct_status == AcctStatusType.START:
                return await self._process_accounting_start(packet, client)
            elif acct_status == AcctStatusType.STOP:
                return await self._process_accounting_stop(packet, client)
            elif acct_status == AcctStatusType.INTERIM_UPDATE:
                return await self._process_accounting_update(packet, client)
            elif acct_status == AcctStatusType.ACCOUNTING_ON:
                return await self._process_accounting_on(packet, client)
            elif acct_status == AcctStatusType.ACCOUNTING_OFF:
                return await self._process_accounting_off(packet, client)
            else:
                return RADIUSResponse.error_response(
                    f"Unsupported accounting status: {acct_status}",
                    "UNSUPPORTED_ACCT_STATUS",
                )

        except Exception as e:
            logger.error(f"Error processing accounting request: {e}")
            return RADIUSResponse.error_response(
                "Accounting processing failed", "ACCT_PROCESSING_ERROR"
            )

    async def _process_accounting_start(
        self, packet: RADIUSPacket, client: RADIUSClient
    ) -> RADIUSResponse:
        """Process accounting start request."""
        try:
            # Extract session information
            session_info = self._extract_session_info(packet)

            # Create accounting record
            record = {
                "type": "start",
                "client_ip": client.ip_address,
                "username": session_info.get("username"),
                "session_id": session_info.get("session_id"),
                "nas_ip": session_info.get("nas_ip"),
                "nas_port": session_info.get("nas_port"),
                "calling_station_id": session_info.get("calling_station_id"),
                "called_station_id": session_info.get("called_station_id"),
                "timestamp": session_info.get("timestamp"),
            }

            self._accounting_records.append(record)
            logger.info(
                f"Accounting START: {record['username']} session {record['session_id']}"
            )

            return RADIUSResponse.success_response("Accounting start processed")

        except Exception as e:
            logger.error(f"Error processing accounting start: {e}")
            return RADIUSResponse.error_response(
                "Accounting start processing failed", "ACCT_START_ERROR"
            )

    async def _process_accounting_stop(
        self, packet: RADIUSPacket, client: RADIUSClient
    ) -> RADIUSResponse:
        """Process accounting stop request."""
        try:
            # Extract session information
            session_info = self._extract_session_info(packet)

            # Create accounting record
            record = {
                "type": "stop",
                "client_ip": client.ip_address,
                "username": session_info.get("username"),
                "session_id": session_info.get("session_id"),
                "session_time": session_info.get("session_time"),
                "input_octets": session_info.get("input_octets"),
                "output_octets": session_info.get("output_octets"),
                "input_packets": session_info.get("input_packets"),
                "output_packets": session_info.get("output_packets"),
                "terminate_cause": session_info.get("terminate_cause"),
                "timestamp": session_info.get("timestamp"),
            }

            self._accounting_records.append(record)
            logger.info(
                f"Accounting STOP: {record['username']} session {record['session_id']} - Duration: {record['session_time']}s"
            )

            return RADIUSResponse.success_response("Accounting stop processed")

        except Exception as e:
            logger.error(f"Error processing accounting stop: {e}")
            return RADIUSResponse.error_response(
                "Accounting stop processing failed", "ACCT_STOP_ERROR"
            )

    async def _process_accounting_update(
        self, packet: RADIUSPacket, client: RADIUSClient
    ) -> RADIUSResponse:
        """Process accounting interim update request."""
        try:
            # Extract session information
            session_info = self._extract_session_info(packet)

            # Create accounting record
            record = {
                "type": "update",
                "client_ip": client.ip_address,
                "username": session_info.get("username"),
                "session_id": session_info.get("session_id"),
                "session_time": session_info.get("session_time"),
                "input_octets": session_info.get("input_octets"),
                "output_octets": session_info.get("output_octets"),
                "input_packets": session_info.get("input_packets"),
                "output_packets": session_info.get("output_packets"),
                "timestamp": session_info.get("timestamp"),
            }

            self._accounting_records.append(record)
            logger.debug(
                f"Accounting UPDATE: {record['username']} session {record['session_id']}"
            )

            return RADIUSResponse.success_response("Accounting update processed")

        except Exception as e:
            logger.error(f"Error processing accounting update: {e}")
            return RADIUSResponse.error_response(
                "Accounting update processing failed", "ACCT_UPDATE_ERROR"
            )

    async def _process_accounting_on(
        self, packet: RADIUSPacket, client: RADIUSClient
    ) -> RADIUSResponse:
        """Process accounting on request."""
        logger.info(f"Accounting ON from NAS {client.ip_address}")
        return RADIUSResponse.success_response("Accounting on processed")

    async def _process_accounting_off(
        self, packet: RADIUSPacket, client: RADIUSClient
    ) -> RADIUSResponse:
        """Process accounting off request."""
        logger.info(f"Accounting OFF from NAS {client.ip_address}")
        return RADIUSResponse.success_response("Accounting off processed")

    def _extract_session_info(self, packet: RADIUSPacket) -> dict:
        """Extract session information from accounting packet."""
        import struct
        from datetime import datetime

        info = {"timestamp": datetime.now(UTC)}

        # Extract username
        username_attr = packet.get_attribute(RADIUSAttributeType.USER_NAME)
        if username_attr:
            info["username"] = (
                username_attr.value.decode("utf-8")
                if isinstance(username_attr.value, bytes)
                else str(username_attr.value)
            )

        # Extract session ID
        session_id_attr = packet.get_attribute(RADIUSAttributeType.ACCT_SESSION_ID)
        if session_id_attr:
            info["session_id"] = (
                session_id_attr.value.decode("utf-8")
                if isinstance(session_id_attr.value, bytes)
                else str(session_id_attr.value)
            )

        # Extract NAS information
        nas_ip_attr = packet.get_attribute(RADIUSAttributeType.NAS_IP_ADDRESS)
        if nas_ip_attr:
            info["nas_ip"] = socket.inet_ntoa(nas_ip_attr.value)

        nas_port_attr = packet.get_attribute(RADIUSAttributeType.NAS_PORT)
        if nas_port_attr:
            info["nas_port"] = struct.unpack("!I", nas_port_attr.value)[0]

        # Extract calling/called station IDs
        calling_station_attr = packet.get_attribute(
            RADIUSAttributeType.CALLING_STATION_ID
        )
        if calling_station_attr:
            info["calling_station_id"] = calling_station_attr.value.decode("utf-8")

        called_station_attr = packet.get_attribute(
            RADIUSAttributeType.CALLED_STATION_ID
        )
        if called_station_attr:
            info["called_station_id"] = called_station_attr.value.decode("utf-8")

        # Extract usage statistics
        session_time_attr = packet.get_attribute(RADIUSAttributeType.ACCT_SESSION_TIME)
        if session_time_attr:
            info["session_time"] = struct.unpack("!I", session_time_attr.value)[0]

        input_octets_attr = packet.get_attribute(RADIUSAttributeType.ACCT_INPUT_OCTETS)
        if input_octets_attr:
            info["input_octets"] = struct.unpack("!I", input_octets_attr.value)[0]

        output_octets_attr = packet.get_attribute(
            RADIUSAttributeType.ACCT_OUTPUT_OCTETS
        )
        if output_octets_attr:
            info["output_octets"] = struct.unpack("!I", output_octets_attr.value)[0]

        input_packets_attr = packet.get_attribute(
            RADIUSAttributeType.ACCT_INPUT_PACKETS
        )
        if input_packets_attr:
            info["input_packets"] = struct.unpack("!I", input_packets_attr.value)[0]

        output_packets_attr = packet.get_attribute(
            RADIUSAttributeType.ACCT_OUTPUT_PACKETS
        )
        if output_packets_attr:
            info["output_packets"] = struct.unpack("!I", output_packets_attr.value)[0]

        terminate_cause_attr = packet.get_attribute(
            RADIUSAttributeType.ACCT_TERMINATE_CAUSE
        )
        if terminate_cause_attr:
            info["terminate_cause"] = struct.unpack("!I", terminate_cause_attr.value)[0]

        return info

    def get_accounting_records(self) -> list[dict]:
        """Get all accounting records."""
        return self._accounting_records.copy()

    def get_user_accounting(self, username: str) -> list[dict]:
        """Get accounting records for specific user."""
        return [r for r in self._accounting_records if r.get("username") == username]

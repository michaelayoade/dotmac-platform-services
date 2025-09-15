"""
OLT (Optical Line Terminal) management.
"""

import logging
from typing import Any

from .types import OLTDevice, VOLTHAResponse

logger = logging.getLogger(__name__)


class OLTManager:
    """
    OLT device management and operations.
    """

    def __init__(self, voltha_manager):
        self.voltha_manager = voltha_manager
        self._initialized = False

    async def initialize(self):
        """Initialize OLT manager."""
        self._initialized = True
        logger.info("OLT manager initialized")

    async def shutdown(self):
        """Shutdown OLT manager."""
        self._initialized = False
        logger.info("OLT manager shutdown")

    async def create_olt(self, config: dict[str, Any]) -> VOLTHAResponse:
        """
        Create and provision OLT device.

        Args:
            config: OLT configuration dictionary

        Returns:
            VOLTHAResponse with creation result
        """
        try:
            # Create OLT device object
            olt = OLTDevice(
                type=config.get("type", "openolt"),
                host_and_port=config.get("host_and_port", ""),
                vendor=config.get("vendor", ""),
                model=config.get("model", ""),
                serial_number=config.get("serial_number", ""),
            )

            # Register with VOLTHA manager
            self.voltha_manager._register_device(olt)

            logger.info(f"Created OLT device {olt.id}")

            return VOLTHAResponse.success_response(
                "OLT created successfully", olt, olt.id
            )

        except Exception as e:
            logger.error(f"Error creating OLT: {e}")
            return VOLTHAResponse.error_response(
                f"Failed to create OLT: {e}", "OLT_CREATE_FAILED"
            )

    async def provision_olt(self, olt_id: str) -> VOLTHAResponse:
        """Provision OLT device."""
        try:
            olt = self.voltha_manager.get_olt(olt_id)
            if not olt:
                return VOLTHAResponse.error_response(
                    f"OLT {olt_id} not found", "OLT_NOT_FOUND", olt_id
                )

            # Perform OLT provisioning
            # This would involve actual VOLTHA gRPC calls
            logger.info(f"Provisioned OLT {olt_id}")

            return VOLTHAResponse.success_response(
                f"OLT {olt_id} provisioned", olt, olt_id
            )

        except Exception as e:
            logger.error(f"Error provisioning OLT {olt_id}: {e}")
            return VOLTHAResponse.error_response(
                f"Failed to provision OLT: {e}", "OLT_PROVISION_FAILED", olt_id
            )

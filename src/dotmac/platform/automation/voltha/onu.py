"""
ONU (Optical Network Unit) management.
"""

import logging
from typing import Any

from .types import ONUDevice, VOLTHAResponse

logger = logging.getLogger(__name__)


class ONUManager:
    """
    ONU device management and operations.
    """

    def __init__(self, voltha_manager):
        self.voltha_manager = voltha_manager
        self._initialized = False

    async def initialize(self):
        """Initialize ONU manager."""
        self._initialized = True
        logger.info("ONU manager initialized")

    async def shutdown(self):
        """Shutdown ONU manager."""
        self._initialized = False
        logger.info("ONU manager shutdown")

    async def create_onu(self, config: dict[str, Any]) -> VOLTHAResponse:
        """
        Create and provision ONU device.

        Args:
            config: ONU configuration dictionary

        Returns:
            VOLTHAResponse with creation result
        """
        try:
            # Create ONU device object
            onu = ONUDevice(
                serial_number=config.get("serial_number", ""),
                olt_device_id=config.get("olt_device_id", ""),
                pon_port_no=config.get("pon_port_no", 0),
                onu_id=config.get("onu_id", 0),
                vendor=config.get("vendor", ""),
                model=config.get("model", ""),
            )

            # Register with VOLTHA manager
            self.voltha_manager._register_device(onu)

            logger.info(f"Created ONU device {onu.id}")

            return VOLTHAResponse.success_response(
                "ONU created successfully", onu, onu.id
            )

        except Exception as e:
            logger.error(f"Error creating ONU: {e}")
            return VOLTHAResponse.error_response(
                f"Failed to create ONU: {e}", "ONU_CREATE_FAILED"
            )

    async def provision_onu(self, onu_id: str) -> VOLTHAResponse:
        """Provision ONU device."""
        try:
            onu = self.voltha_manager.get_onu(onu_id)
            if not onu:
                return VOLTHAResponse.error_response(
                    f"ONU {onu_id} not found", "ONU_NOT_FOUND", onu_id
                )

            # Perform ONU provisioning
            # This would involve actual VOLTHA gRPC calls
            logger.info(f"Provisioned ONU {onu_id}")

            return VOLTHAResponse.success_response(
                f"ONU {onu_id} provisioned", onu, onu_id
            )

        except Exception as e:
            logger.error(f"Error provisioning ONU {onu_id}: {e}")
            return VOLTHAResponse.error_response(
                f"Failed to provision ONU: {e}", "ONU_PROVISION_FAILED", onu_id
            )

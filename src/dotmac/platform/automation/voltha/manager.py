"""
VOLTHA manager for fiber network management and coordination.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Optional

import grpc

from .olt import OLTManager
from .onu import ONUManager
from .types import (
    AdminState,
    ConnectStatus,
    OLTDevice,
    ONUDevice,
    OperStatus,
    VOLTHAConfig,
    VOLTHAConnectionError,
    VOLTHADevice,
    VOLTHADeviceError,
    VOLTHAException,
    VOLTHAFlow,
    VOLTHAResponse,
)

logger = logging.getLogger(__name__)


class VOLTHAManager:
    """
    Main VOLTHA manager for fiber network operations.

    Coordinates OLT and ONU management, device provisioning,
    flow configuration, and network topology management.
    """

    def __init__(self, config: VOLTHAConfig):
        self.config = config
        self._connected = False
        self._channel: Optional[grpc.Channel] = None

        # Component managers
        self.olt_manager = OLTManager(self)
        self.onu_manager = ONUManager(self)

        # Device storage
        self._devices: dict[str, VOLTHADevice] = {}
        self._olt_devices: dict[str, OLTDevice] = {}
        self._onu_devices: dict[str, ONUDevice] = {}

        # Flow management
        self._flows: dict[str, VOLTHAFlow] = {}

        # Event handlers
        self._event_handlers: dict[str, list[callable]] = {}

    async def connect(self) -> bool:
        """Connect to VOLTHA core."""
        if self._connected:
            return True

        try:
            # Create gRPC channel
            if self.config.enable_tls:
                credentials = grpc.ssl_channel_credentials(
                    root_certificates=(
                        self._load_cert(self.config.ca_cert_file)
                        if self.config.ca_cert_file
                        else None
                    ),
                    private_key=(
                        self._load_cert(self.config.key_file)
                        if self.config.key_file
                        else None
                    ),
                    certificate_chain=(
                        self._load_cert(self.config.cert_file)
                        if self.config.cert_file
                        else None
                    ),
                )
                self._channel = grpc.aio.secure_channel(
                    self.config.core_endpoint, credentials
                )
            else:
                self._channel = grpc.aio.insecure_channel(self.config.core_endpoint)

            # Test connection
            await self._test_connection()

            self._connected = True
            logger.info(f"Connected to VOLTHA core at {self.config.core_endpoint}")

            # Initialize managers
            await self.olt_manager.initialize()
            await self.onu_manager.initialize()

            return True

        except Exception as e:
            logger.error(f"Failed to connect to VOLTHA: {e}")
            if self._channel:
                await self._channel.close()
                self._channel = None
            raise VOLTHAConnectionError(f"Connection failed: {e}") from e

    async def disconnect(self):
        """Disconnect from VOLTHA core."""
        if not self._connected:
            return

        try:
            # Stop managers
            await self.olt_manager.shutdown()
            await self.onu_manager.shutdown()

            # Close channel
            if self._channel:
                await self._channel.close()
                self._channel = None

            self._connected = False
            logger.info("Disconnected from VOLTHA core")

        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

    def _load_cert(self, cert_path: str) -> bytes:
        """Load certificate file."""
        try:
            with open(cert_path, "rb") as f:
                return f.read()
        except Exception as e:
            raise VOLTHAException(f"Failed to load certificate {cert_path}: {e}") from e

    async def _test_connection(self):
        """Test VOLTHA connection."""
        # This would implement a basic health check or version request
        # For now, just ensure channel is created
        if not self._channel:
            raise VOLTHAConnectionError("No gRPC channel available")

    @property
    def channel(self) -> Optional[grpc.Channel]:
        """Get gRPC channel."""
        return self._channel

    @property
    def connected(self) -> bool:
        """Check if connected to VOLTHA."""
        return self._connected

    # Device Management
    async def get_devices(
        self, device_type: Optional[str] = None
    ) -> list[VOLTHADevice]:
        """Get all devices, optionally filtered by type."""
        if not self._connected:
            raise VOLTHAConnectionError("Not connected to VOLTHA")

        try:
            # This would make actual gRPC call to get devices
            devices = list(self._devices.values())

            if device_type:
                devices = [
                    d
                    for d in devices
                    if getattr(d, "device_type", d.type) == device_type
                ]

            return devices

        except Exception as e:
            logger.error(f"Error getting devices: {e}")
            raise VOLTHADeviceError("", f"Failed to get devices: {e}") from e

    async def get_device(self, device_id: str) -> Optional[VOLTHADevice]:
        """Get device by ID."""
        if not self._connected:
            raise VOLTHAConnectionError("Not connected to VOLTHA")

        return self._devices.get(device_id)

    async def enable_device(self, device_id: str) -> VOLTHAResponse:
        """Enable VOLTHA device."""
        if not self._connected:
            raise VOLTHAConnectionError("Not connected to VOLTHA")

        try:
            device = self._devices.get(device_id)
            if not device:
                return VOLTHAResponse.error_response(
                    f"Device {device_id} not found", "DEVICE_NOT_FOUND", device_id
                )

            # Update device state
            device.admin_state = AdminState.ENABLED
            device.oper_status = OperStatus.ACTIVE
            device.connect_status = ConnectStatus.REACHABLE

            logger.info(f"Enabled device {device_id}")

            return VOLTHAResponse.success_response(
                f"Device {device_id} enabled", device, device_id
            )

        except Exception as e:
            logger.error(f"Error enabling device {device_id}: {e}")
            return VOLTHAResponse.error_response(
                f"Failed to enable device: {e}", "ENABLE_FAILED", device_id
            )

    async def disable_device(self, device_id: str) -> VOLTHAResponse:
        """Disable VOLTHA device."""
        if not self._connected:
            raise VOLTHAConnectionError("Not connected to VOLTHA")

        try:
            device = self._devices.get(device_id)
            if not device:
                return VOLTHAResponse.error_response(
                    f"Device {device_id} not found", "DEVICE_NOT_FOUND", device_id
                )

            # Update device state
            device.admin_state = AdminState.DISABLED
            device.oper_status = OperStatus.UNKNOWN
            device.connect_status = ConnectStatus.UNREACHABLE

            logger.info(f"Disabled device {device_id}")

            return VOLTHAResponse.success_response(
                f"Device {device_id} disabled", device, device_id
            )

        except Exception as e:
            logger.error(f"Error disabling device {device_id}: {e}")
            return VOLTHAResponse.error_response(
                f"Failed to disable device: {e}", "DISABLE_FAILED", device_id
            )

    async def delete_device(self, device_id: str) -> VOLTHAResponse:
        """Delete VOLTHA device."""
        if not self._connected:
            raise VOLTHAConnectionError("Not connected to VOLTHA")

        try:
            device = self._devices.get(device_id)
            if not device:
                return VOLTHAResponse.error_response(
                    f"Device {device_id} not found", "DEVICE_NOT_FOUND", device_id
                )

            # Remove from all collections
            del self._devices[device_id]
            if device_id in self._olt_devices:
                del self._olt_devices[device_id]
            if device_id in self._onu_devices:
                del self._onu_devices[device_id]

            logger.info(f"Deleted device {device_id}")

            return VOLTHAResponse.success_response(
                f"Device {device_id} deleted", None, device_id
            )

        except Exception as e:
            logger.error(f"Error deleting device {device_id}: {e}")
            return VOLTHAResponse.error_response(
                f"Failed to delete device: {e}", "DELETE_FAILED", device_id
            )

    # OLT Management
    async def create_olt(self, olt_config: dict[str, Any]) -> VOLTHAResponse:
        """Create and provision OLT device."""
        return await self.olt_manager.create_olt(olt_config)

    async def get_olts(self) -> list[OLTDevice]:
        """Get all OLT devices."""
        return list(self._olt_devices.values())

    async def get_olt(self, olt_id: str) -> Optional[OLTDevice]:
        """Get OLT device by ID."""
        return self._olt_devices.get(olt_id)

    # ONU Management
    async def create_onu(self, onu_config: dict[str, Any]) -> VOLTHAResponse:
        """Create and provision ONU device."""
        return await self.onu_manager.create_onu(onu_config)

    async def get_onus(self, olt_id: Optional[str] = None) -> list[ONUDevice]:
        """Get ONU devices, optionally filtered by OLT."""
        onus = list(self._onu_devices.values())
        if olt_id:
            onus = [onu for onu in onus if onu.olt_device_id == olt_id]
        return onus

    async def get_onu(self, onu_id: str) -> Optional[ONUDevice]:
        """Get ONU device by ID."""
        return self._onu_devices.get(onu_id)

    # Flow Management
    async def create_flow(
        self, device_id: str, flow_config: dict[str, Any]
    ) -> VOLTHAResponse:
        """Create flow on device."""
        if not self._connected:
            raise VOLTHAConnectionError("Not connected to VOLTHA")

        try:
            device = self._devices.get(device_id)
            if not device:
                return VOLTHAResponse.error_response(
                    f"Device {device_id} not found", "DEVICE_NOT_FOUND", device_id
                )

            # Create flow object
            flow = VOLTHAFlow(device_id=device_id, **flow_config)

            # Store flow
            self._flows[flow.id] = flow
            device.flows.append(flow)

            logger.info(f"Created flow {flow.id} on device {device_id}")

            return VOLTHAResponse.success_response(
                f"Flow created on device {device_id}", flow, device_id
            )

        except Exception as e:
            logger.error(f"Error creating flow on device {device_id}: {e}")
            return VOLTHAResponse.error_response(
                f"Failed to create flow: {e}", "FLOW_CREATE_FAILED", device_id
            )

    async def delete_flow(self, device_id: str, flow_id: str) -> VOLTHAResponse:
        """Delete flow from device."""
        if not self._connected:
            raise VOLTHAConnectionError("Not connected to VOLTHA")

        try:
            flow = self._flows.get(flow_id)
            if not flow:
                return VOLTHAResponse.error_response(
                    f"Flow {flow_id} not found", "FLOW_NOT_FOUND", device_id
                )

            # Remove from device
            device = self._devices.get(device_id)
            if device:
                device.flows = [f for f in device.flows if f.id != flow_id]

            # Remove from global flows
            del self._flows[flow_id]

            logger.info(f"Deleted flow {flow_id} from device {device_id}")

            return VOLTHAResponse.success_response(
                f"Flow {flow_id} deleted from device {device_id}", None, device_id
            )

        except Exception as e:
            logger.error(f"Error deleting flow {flow_id} from device {device_id}: {e}")
            return VOLTHAResponse.error_response(
                f"Failed to delete flow: {e}", "FLOW_DELETE_FAILED", device_id
            )

    async def get_flows(self, device_id: Optional[str] = None) -> list[VOLTHAFlow]:
        """Get flows, optionally filtered by device."""
        flows = list(self._flows.values())
        if device_id:
            flows = [f for f in flows if f.device_id == device_id]
        return flows

    # Event Management
    def add_event_handler(self, event_type: str, handler: callable):
        """Add event handler for specific event type."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    def remove_event_handler(self, event_type: str, handler: callable):
        """Remove event handler."""
        if event_type in self._event_handlers:
            try:
                self._event_handlers[event_type].remove(handler)
            except ValueError:
                pass

    async def _emit_event(self, event_type: str, event_data: dict[str, Any]):
        """Emit event to registered handlers."""
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_data)
                else:
                    handler(event_data)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")

    # Device Registration (Internal)
    def _register_device(self, device: VOLTHADevice):
        """Register device in manager."""
        self._devices[device.id] = device

        if isinstance(device, OLTDevice):
            self._olt_devices[device.id] = device
        elif isinstance(device, ONUDevice):
            self._onu_devices[device.id] = device

    def _unregister_device(self, device_id: str):
        """Unregister device from manager."""
        if device_id in self._devices:
            del self._devices[device_id]
        if device_id in self._olt_devices:
            del self._olt_devices[device_id]
        if device_id in self._onu_devices:
            del self._onu_devices[device_id]

    # Statistics
    def get_network_stats(self) -> dict[str, Any]:
        """Get network statistics."""
        return {
            "connected": self._connected,
            "total_devices": len(self._devices),
            "olt_devices": len(self._olt_devices),
            "onu_devices": len(self._onu_devices),
            "total_flows": len(self._flows),
            "core_endpoint": self.config.core_endpoint,
        }

    @asynccontextmanager
    async def connection_context(self):
        """Context manager for VOLTHA connection lifecycle."""
        try:
            await self.connect()
            yield self
        finally:
            await self.disconnect()

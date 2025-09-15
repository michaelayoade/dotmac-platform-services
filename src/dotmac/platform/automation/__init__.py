"""
DotMac Network Automation Toolkit

Comprehensive network automation package providing:
- RADIUS server management and AAA operations
- VOLTHA integration for fiber network management
- SSH automation and device provisioning
- Network monitoring and health checks
- Device configuration management
"""

from .config import DeviceConfiguration, NetworkConfigManager
from .monitoring import DeviceHealthChecker, NetworkMonitor, SNMPCollector
from .radius import RADIUSAuthenticator, RADIUSManager, RADIUSSession
from .ssh import DeviceProvisioner, SSHAutomation, SSHConnectionPool
from .voltha import OLTManager, ONUManager, VOLTHAManager

__version__ = "0.1.0"

__all__ = [
    # RADIUS Management
    "RADIUSManager",
    "RADIUSSession",
    "RADIUSAuthenticator",
    # VOLTHA Integration
    "VOLTHAManager",
    "OLTManager",
    "ONUManager",
    # SSH Automation
    "SSHAutomation",
    "DeviceProvisioner",
    "SSHConnectionPool",
    # Monitoring
    "NetworkMonitor",
    "DeviceHealthChecker",
    "SNMPCollector",
    # Configuration
    "NetworkConfigManager",
    "DeviceConfiguration",
]

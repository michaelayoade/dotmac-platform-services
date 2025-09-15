"""
Convenience imports for RADIUS components.

This module re-exports the automation.radius API under a simpler path and
provides a couple of compatibility aliases to match documentation examples.
"""

from ..automation.radius import (
    CoAManager,
    RADIUSAccounting,
    RADIUSAttribute,
    RADIUSAuthenticator,
    RADIUSClient,
    RADIUSManager,
    RADIUSPacket,
    RADIUSResponse,
    RADIUSServerConfig,
    RADIUSSession,
    RADIUSSessionManager,
    RADIUSUser,
)

# Compatibility aliases used in docs/examples
RADIUSServer = RADIUSManager
AuthManager = RADIUSAuthenticator

__all__ = [
    "RADIUSManager",
    "RADIUSSession",
    "RADIUSSessionManager",
    "RADIUSAuthenticator",
    "RADIUSClient",
    "RADIUSAccounting",
    "CoAManager",
    "RADIUSAttribute",
    "RADIUSPacket",
    "RADIUSResponse",
    "RADIUSServerConfig",
    "RADIUSUser",
    # Aliases
    "RADIUSServer",
    "AuthManager",
]

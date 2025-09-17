"""
Frontend Integration Module

This module provides utilities for integrating the backend platform services
with the frontend packages in the frontend/ directory.
"""

from .config_bridge import (
    FrontendConfigBridge,
    get_frontend_config,
    generate_frontend_config_files,
)

__all__ = [
    "FrontendConfigBridge",
    "get_frontend_config",
    "generate_frontend_config_files",
]
"""
Device configuration management.
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DeviceConfiguration:
    """
    Device configuration container.
    """

    device_id: str
    config_data: dict[str, Any]
    version: str = "1.0"

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get configuration setting."""
        return self.config_data.get(key, default)

    def set_setting(self, key: str, value: Any):
        """Set configuration setting."""
        self.config_data[key] = value

from dotmac.platform.logging import get_logger

"""
Simple access control decorator.
For complex use cases, use AccessControlManager directly.
"""

import functools
from typing import Any, Optional

from dotmac.platform.logging import get_logger
from .manager import AccessControlManager
from .models import AccessRequest, ActionType, ResourceType

logger = get_logger(__name__)

# For access control, use AccessControlManager directly:
#
# manager = AccessControlManager()
# access_request = AccessRequest(
#     subject_type="user",
#     subject_id="user123",
#     resource_type=ResourceType.DOCUMENT,
#     action=ActionType.READ
# )
# decision = await manager.check_permission(access_request)
# if decision.decision != "allow":
#     raise HTTPException(403, "Access denied")

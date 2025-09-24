"""
Customer Management Module for DotMac Platform Services.

This module provides comprehensive customer relationship management capabilities including:
- Customer profile management with rich metadata
- Customer segmentation and categorization
- Activity tracking and timeline
- Communication preferences
- Customer lifecycle management
- Integration with auth and billing systems
"""

from dotmac.platform.customer_management.models import (
    Customer,
    CustomerSegment,
    CustomerActivity,
    CustomerNote,
    CustomerTag,
)
from dotmac.platform.customer_management.service import CustomerService
from dotmac.platform.customer_management.router import router as customer_router

__all__ = [
    "Customer",
    "CustomerSegment",
    "CustomerActivity",
    "CustomerNote",
    "CustomerTag",
    "CustomerService",
    "customer_router",
]
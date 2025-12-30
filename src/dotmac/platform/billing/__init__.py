"""
Billing system module.

Provides billing capabilities including:
- Product catalog management
- Subscription lifecycle
- Usage-based billing
- Pricing rules and discounts
- Invoice and payment processing
- PDF invoice generation

Integrated with DotMac platform services.
"""

from __future__ import annotations

import os
from typing import Final

from dotmac.platform.billing.exceptions import (
    BillingConfigurationError,
    BillingError,
    CategoryNotFoundError,
    InvalidPricingRuleError,
    PlanNotFoundError,
    PricingError,
    ProductError,
    ProductNotFoundError,
    SubscriptionError,
    SubscriptionNotFoundError,
    UsageTrackingError,
)


def _is_truthy_env(value: str | None) -> bool:
    return (value or "").lower() in {"1", "true", "yes", "on"}


_SKIP_BILLING_MODELS: Final[bool] = _is_truthy_env(
    os.getenv("DOTMAC_SKIP_BILLING_MODELS") or os.getenv("DOTMAC_SKIP_PLATFORM_MODELS")
)


__all__ = [
    # Exceptions (always available)
    "BillingError",
    "ProductError",
    "ProductNotFoundError",
    "CategoryNotFoundError",
    "SubscriptionError",
    "SubscriptionNotFoundError",
    "PlanNotFoundError",
    "PricingError",
    "InvalidPricingRuleError",
    "UsageTrackingError",
    "BillingConfigurationError",
]

if not _SKIP_BILLING_MODELS:
    from dotmac.platform.billing.catalog.models import (
        Product,
        ProductCategory,
        ProductCategoryCreateRequest,
        ProductCategoryResponse,
        ProductCreateRequest,
        ProductFilters,
        ProductResponse,
        ProductType,
        ProductUpdateRequest,
        TaxClass,
        UsageType,
    )
    from dotmac.platform.billing.catalog.service import ProductService
    from dotmac.platform.billing.core.models import (
        Customer,
        Invoice,
        InvoiceItem,
        InvoiceLineItem,
        Payment,
        Price,
        Subscription,
    )
    from dotmac.platform.billing.models import (
        BillingBaseModel,
        BillingPricingRuleTable,
        BillingProductCategoryTable,
        BillingProductTable,
        BillingRuleUsageTable,
        BillingSettingsTable,
        BillingSQLModel,
        BillingSubscriptionEventTable,
        BillingSubscriptionPlanTable,
        BillingSubscriptionTable,
    )
    from dotmac.platform.billing.money_utils import create_money, format_money, money_handler
    from dotmac.platform.billing.pdf_generator_reportlab import ReportLabInvoiceGenerator

    __all__ += [
        # Product catalog
        "Product",
        "ProductCategory",
        "ProductType",
        "UsageType",
        "TaxClass",
        "ProductCreateRequest",
        "ProductUpdateRequest",
        "ProductCategoryCreateRequest",
        "ProductFilters",
        "ProductResponse",
        "ProductCategoryResponse",
        "ProductService",
        # Core billing models
        "Invoice",
        "InvoiceLineItem",
        "InvoiceItem",
        "Payment",
        "Customer",
        "Subscription",
        "Price",
        # Database models
        "BillingBaseModel",
        "BillingSQLModel",
        "BillingProductTable",
        "BillingProductCategoryTable",
        "BillingSubscriptionPlanTable",
        "BillingSubscriptionTable",
        "BillingSubscriptionEventTable",
        "BillingPricingRuleTable",
        "BillingRuleUsageTable",
        "BillingSettingsTable",
        # Money utilities
        "money_handler",
        "create_money",
        "format_money",
        "ReportLabInvoiceGenerator",
    ]

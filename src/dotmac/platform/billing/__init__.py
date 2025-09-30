"""
Billing system module.

Provides billing capabilities including:
- Product catalog management
- Subscription lifecycle
- Usage-based billing
- Pricing rules and discounts
- Invoice and payment processing
- Money-aware models with accurate currency handling
- PDF invoice generation

Integrated with DotMac platform services.
"""

from dotmac.platform.billing.catalog.models import (
    Product,
    ProductCategory,
    ProductType,
    UsageType,
    TaxClass,
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductCategoryCreateRequest,
    ProductFilters,
    ProductResponse,
    ProductCategoryResponse,
)

from dotmac.platform.billing.catalog.service import ProductService

from dotmac.platform.billing.exceptions import (
    BillingError,
    ProductError,
    ProductNotFoundError,
    CategoryNotFoundError,
    SubscriptionError,
    SubscriptionNotFoundError,
    PlanNotFoundError,
    PricingError,
    InvalidPricingRuleError,
    UsageTrackingError,
    BillingConfigurationError,
)

from dotmac.platform.billing.models import (
    BillingBaseModel,
    BillingSQLModel,
    BillingProductTable,
    BillingProductCategoryTable,
    BillingSubscriptionPlanTable,
    BillingSubscriptionTable,
    BillingSubscriptionEventTable,
    BillingPricingRuleTable,
    BillingRuleUsageTable,
)

# Import core models for tests
from dotmac.platform.billing.core.models import (
    Invoice,
    InvoiceLineItem,
    Payment,
    Customer,
    Subscription,
    Product,
    Price,
    InvoiceItem,
)

__all__ = [
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

    # Exceptions
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

    # Money-aware models and utilities
    "MoneyInvoice",
    "MoneyInvoiceLineItem",
    "MoneyField",
    "money_handler",
    "create_money",
    "format_money",
    "InvoiceMigrationAdapter",
    "BatchMigrationService",
    "MoneyInvoiceService",
    "ReportLabInvoiceGenerator",
]

# Import Money modules for convenience
from dotmac.platform.billing.money_models import MoneyInvoice, MoneyInvoiceLineItem, MoneyField
from dotmac.platform.billing.money_utils import money_handler, create_money, format_money
from dotmac.platform.billing.money_migration import InvoiceMigrationAdapter, BatchMigrationService
from dotmac.platform.billing.invoicing.money_service import MoneyInvoiceService
from dotmac.platform.billing.pdf_generator_reportlab import ReportLabInvoiceGenerator
"""
Billing module configuration
"""

import os
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class StripeConfig(BaseModel):
    """Stripe configuration"""

    api_key: str = Field(..., description="Stripe API key")
    webhook_secret: Optional[str] = Field(None, description="Stripe webhook secret")
    publishable_key: Optional[str] = Field(None, description="Stripe publishable key")


class PayPalConfig(BaseModel):
    """PayPal configuration"""

    client_id: str = Field(..., description="PayPal client ID")
    client_secret: str = Field(..., description="PayPal client secret")
    webhook_id: Optional[str] = Field(None, description="PayPal webhook ID")
    environment: str = Field("sandbox", description="PayPal environment (sandbox/live)")


class TaxConfig(BaseModel):
    """Tax configuration"""

    provider: Optional[str] = Field(None, description="Tax provider (avalara, taxjar)")
    avalara_api_key: Optional[str] = Field(None, description="Avalara API key")
    avalara_company_code: Optional[str] = Field(None, description="Avalara company code")
    taxjar_api_token: Optional[str] = Field(None, description="TaxJar API token")
    default_tax_rate: float = Field(0.0, description="Default tax rate percentage")


class CurrencyConfig(BaseModel):
    """Currency configuration - Single currency support"""

    default_currency: str = Field("USD", description="Default currency code")
    currency_symbol: str = Field("$", description="Currency symbol")
    currency_decimal_places: int = Field(2, description="Number of decimal places")
    currency_format: str = Field("{symbol}{amount}", description="Currency display format")
    use_minor_units: bool = Field(
        True,
        description="Store amounts in minor units (cents)"
    )


class InvoiceConfig(BaseModel):
    """Invoice configuration"""

    number_format: str = Field(
        "INV-{year}-{sequence:06d}",
        description="Invoice number format template",
    )
    due_days_default: int = Field(30, description="Default payment terms in days")
    auto_finalize: bool = Field(False, description="Auto-finalize draft invoices")
    overdue_check_hours: int = Field(24, description="How often to check for overdue invoices")
    send_reminders: bool = Field(True, description="Send payment reminder emails")
    reminder_days: list[int] = Field(
        default=[7, 3, 1],
        description="Days before due date to send reminders",
    )


class PaymentConfig(BaseModel):
    """Payment configuration"""

    default_provider: str = Field("stripe", description="Default payment provider")
    auto_retry_failed: bool = Field(True, description="Auto-retry failed payments")
    max_retry_attempts: int = Field(3, description="Maximum payment retry attempts")
    retry_backoff_hours: list[int] = Field(
        default=[2, 24, 72],
        description="Hours to wait between retry attempts",
    )
    require_verification: bool = Field(
        True,
        description="Require payment method verification",
    )


class WebhookConfig(BaseModel):
    """Webhook configuration"""

    endpoint_base_url: str = Field(
        "https://api.example.com",
        description="Base URL for webhook endpoints",
    )
    signing_secret: str = Field(..., description="Secret for webhook signature verification")
    retry_attempts: int = Field(3, description="Webhook delivery retry attempts")
    timeout_seconds: int = Field(30, description="Webhook request timeout")


class BillingConfig(BaseModel):
    """Main billing configuration"""

    # Provider configurations
    stripe: Optional[StripeConfig] = None
    paypal: Optional[PayPalConfig] = None

    # Module configurations
    tax: TaxConfig = Field(default_factory=TaxConfig)
    currency: CurrencyConfig = Field(default_factory=CurrencyConfig)
    invoice: InvoiceConfig = Field(default_factory=InvoiceConfig)
    payment: PaymentConfig = Field(default_factory=PaymentConfig)
    webhook: Optional[WebhookConfig] = None

    # Feature flags
    enable_subscriptions: bool = Field(True, description="Enable subscription billing")
    enable_credit_notes: bool = Field(True, description="Enable credit note management")
    enable_tax_calculation: bool = Field(True, description="Enable automatic tax calculation")
    enable_multi_currency: bool = Field(True, description="Enable multi-currency support")
    enable_webhooks: bool = Field(False, description="Enable webhook notifications")

    # Audit and compliance
    audit_log_enabled: bool = Field(True, description="Enable billing audit logging")
    pci_compliance_mode: bool = Field(False, description="Enable PCI compliance mode")
    data_retention_days: int = Field(2555, description="Data retention period in days (7 years)")

    @classmethod
    def from_env(cls) -> "BillingConfig":
        """Create configuration from environment variables"""

        config_dict: Dict[str, Any] = {}

        # Stripe configuration
        if os.getenv("STRIPE_API_KEY"):
            config_dict["stripe"] = StripeConfig(
                api_key=os.getenv("STRIPE_API_KEY", ""),
                webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET"),
                publishable_key=os.getenv("STRIPE_PUBLISHABLE_KEY"),
            )

        # PayPal configuration
        if os.getenv("PAYPAL_CLIENT_ID"):
            config_dict["paypal"] = PayPalConfig(
                client_id=os.getenv("PAYPAL_CLIENT_ID", ""),
                client_secret=os.getenv("PAYPAL_CLIENT_SECRET", ""),
                webhook_id=os.getenv("PAYPAL_WEBHOOK_ID"),
                environment=os.getenv("PAYPAL_ENVIRONMENT", "sandbox"),
            )

        # Tax configuration
        tax_config = TaxConfig(
            provider=os.getenv("TAX_PROVIDER"),
            avalara_api_key=os.getenv("AVALARA_API_KEY"),
            avalara_company_code=os.getenv("AVALARA_COMPANY_CODE"),
            taxjar_api_token=os.getenv("TAXJAR_API_TOKEN"),
            default_tax_rate=float(os.getenv("DEFAULT_TAX_RATE", "0.0")),
        )
        config_dict["tax"] = tax_config

        # Currency configuration
        currency_config = CurrencyConfig(
            default_currency=os.getenv("DEFAULT_CURRENCY", "USD"),
            currency_symbol=os.getenv("CURRENCY_SYMBOL", "$"),
            currency_decimal_places=int(os.getenv("CURRENCY_DECIMAL_PLACES", "2")),
            currency_format=os.getenv("CURRENCY_FORMAT", "{symbol}{amount}"),
            use_minor_units=os.getenv("USE_MINOR_UNITS", "true").lower() == "true",
        )
        config_dict["currency"] = currency_config

        # Invoice configuration
        invoice_config = InvoiceConfig(
            number_format=os.getenv("INVOICE_NUMBER_FORMAT", "INV-{year}-{sequence:06d}"),
            due_days_default=int(os.getenv("INVOICE_DUE_DAYS", "30")),
            auto_finalize=os.getenv("INVOICE_AUTO_FINALIZE", "false").lower() == "true",
            overdue_check_hours=int(os.getenv("OVERDUE_CHECK_HOURS", "24")),
            send_reminders=os.getenv("SEND_PAYMENT_REMINDERS", "true").lower() == "true",
        )
        config_dict["invoice"] = invoice_config

        # Payment configuration
        payment_config = PaymentConfig(
            default_provider=os.getenv("DEFAULT_PAYMENT_PROVIDER", "stripe"),
            auto_retry_failed=os.getenv("AUTO_RETRY_FAILED_PAYMENTS", "true").lower() == "true",
            max_retry_attempts=int(os.getenv("MAX_PAYMENT_RETRY_ATTEMPTS", "3")),
            require_verification=os.getenv("REQUIRE_PAYMENT_VERIFICATION", "true").lower() == "true",
        )
        config_dict["payment"] = payment_config

        # Webhook configuration
        if os.getenv("WEBHOOK_ENDPOINT_URL") and os.getenv("WEBHOOK_SIGNING_SECRET"):
            config_dict["webhook"] = WebhookConfig(
                endpoint_base_url=os.getenv("WEBHOOK_ENDPOINT_URL", ""),
                signing_secret=os.getenv("WEBHOOK_SIGNING_SECRET", ""),
                retry_attempts=int(os.getenv("WEBHOOK_RETRY_ATTEMPTS", "3")),
                timeout_seconds=int(os.getenv("WEBHOOK_TIMEOUT_SECONDS", "30")),
            )

        # Feature flags
        config_dict["enable_subscriptions"] = os.getenv("ENABLE_SUBSCRIPTIONS", "true").lower() == "true"
        config_dict["enable_credit_notes"] = os.getenv("ENABLE_CREDIT_NOTES", "true").lower() == "true"
        config_dict["enable_tax_calculation"] = os.getenv("ENABLE_TAX_CALCULATION", "true").lower() == "true"
        config_dict["enable_multi_currency"] = os.getenv("ENABLE_MULTI_CURRENCY", "true").lower() == "true"
        config_dict["enable_webhooks"] = os.getenv("ENABLE_WEBHOOKS", "false").lower() == "true"

        # Audit and compliance
        config_dict["audit_log_enabled"] = os.getenv("BILLING_AUDIT_LOG", "true").lower() == "true"
        config_dict["pci_compliance_mode"] = os.getenv("PCI_COMPLIANCE_MODE", "false").lower() == "true"
        config_dict["data_retention_days"] = int(os.getenv("BILLING_DATA_RETENTION_DAYS", "2555"))

        return cls(**config_dict)


# Global configuration instance
_billing_config: Optional[BillingConfig] = None


def get_billing_config() -> BillingConfig:
    """Get the global billing configuration instance"""
    global _billing_config
    if _billing_config is None:
        _billing_config = BillingConfig.from_env()
    return _billing_config


def set_billing_config(config: BillingConfig) -> None:
    """Set the global billing configuration instance"""
    global _billing_config
    _billing_config = config
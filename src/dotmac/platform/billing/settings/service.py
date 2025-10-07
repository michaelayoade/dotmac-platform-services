"""
Billing settings service
"""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.billing.metrics import get_billing_metrics

from .models import (
    BillingSettings,
    CompanyInfo,
    InvoiceSettings,
    NotificationSettings,
    PaymentSettings,
    TaxSettings,
)

logger = logging.getLogger(__name__)


class BillingSettingsService:
    """Service for managing billing settings"""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db = db_session
        self.metrics = get_billing_metrics()

    async def get_settings(self, tenant_id: str) -> BillingSettings:
        """Get billing settings for tenant"""

        # In a real implementation, this would query a settings table
        # For now, return default settings
        default_settings = self._get_default_settings(tenant_id)

        logger.info(f"Retrieved billing settings for tenant {tenant_id}")
        return default_settings

    async def update_settings(self, tenant_id: str, settings: BillingSettings) -> BillingSettings:
        """Update billing settings for tenant"""

        # Validate settings
        await self._validate_settings(settings)

        # In a real implementation, this would save to database
        # For now, just return the settings with updated tenant_id
        settings.tenant_id = tenant_id

        logger.info(f"Updated billing settings for tenant {tenant_id}")
        return settings

    async def update_company_info(
        self, tenant_id: str, company_info: CompanyInfo
    ) -> BillingSettings:
        """Update company information"""

        settings = await self.get_settings(tenant_id)
        settings.company_info = company_info
        return await self.update_settings(tenant_id, settings)

    async def update_tax_settings(
        self, tenant_id: str, tax_settings: TaxSettings
    ) -> BillingSettings:
        """Update tax settings"""

        settings = await self.get_settings(tenant_id)
        settings.tax_settings = tax_settings
        return await self.update_settings(tenant_id, settings)

    async def update_payment_settings(
        self, tenant_id: str, payment_settings: PaymentSettings
    ) -> BillingSettings:
        """Update payment settings"""

        settings = await self.get_settings(tenant_id)
        settings.payment_settings = payment_settings
        return await self.update_settings(tenant_id, settings)

    async def update_invoice_settings(
        self, tenant_id: str, invoice_settings: InvoiceSettings
    ) -> BillingSettings:
        """Update invoice settings"""

        settings = await self.get_settings(tenant_id)
        settings.invoice_settings = invoice_settings
        return await self.update_settings(tenant_id, settings)

    async def update_notification_settings(
        self, tenant_id: str, notification_settings: NotificationSettings
    ) -> BillingSettings:
        """Update notification settings"""

        settings = await self.get_settings(tenant_id)
        settings.notification_settings = notification_settings
        return await self.update_settings(tenant_id, settings)

    async def update_feature_flags(
        self, tenant_id: str, features: dict[str, bool]
    ) -> BillingSettings:
        """Update feature flags"""

        settings = await self.get_settings(tenant_id)
        settings.features_enabled.update(features)
        return await self.update_settings(tenant_id, settings)

    async def get_feature_flag(self, tenant_id: str, feature_name: str) -> bool:
        """Get specific feature flag value"""

        settings = await self.get_settings(tenant_id)
        return settings.features_enabled.get(feature_name, False)

    async def update_custom_setting(self, tenant_id: str, key: str, value: Any) -> BillingSettings:
        """Update custom setting"""

        settings = await self.get_settings(tenant_id)
        settings.custom_settings[key] = value
        return await self.update_settings(tenant_id, settings)

    async def get_custom_setting(self, tenant_id: str, key: str, default: Any | None = None) -> Any:
        """Get custom setting value"""

        settings = await self.get_settings(tenant_id)
        return settings.custom_settings.get(key, default)

    async def reset_to_defaults(self, tenant_id: str) -> BillingSettings:
        """Reset settings to defaults"""

        default_settings = self._get_default_settings(tenant_id)
        return await self.update_settings(tenant_id, default_settings)

    async def validate_settings_for_tenant(self, tenant_id: str) -> dict[str, Any]:
        """Validate current settings and return validation report"""

        settings = await self.get_settings(tenant_id)
        validation_report = {
            "valid": True,
            "warnings": [],
            "errors": [],
        }

        # Validate company info
        if not settings.company_info.name:
            validation_report["errors"].append("Company name is required")
            validation_report["valid"] = False

        if not settings.company_info.address_line1:
            validation_report["errors"].append("Company address is required")
            validation_report["valid"] = False

        # Validate tax settings
        if settings.tax_settings.calculate_tax and not settings.tax_settings.tax_registrations:
            validation_report["warnings"].append(
                "Tax calculation enabled but no tax registrations configured"
            )

        # Validate payment settings
        if not settings.payment_settings.enabled_payment_methods:
            validation_report["errors"].append("At least one payment method must be enabled")
            validation_report["valid"] = False

        # Validate invoice settings
        if (
            settings.invoice_settings.send_payment_reminders
            and not settings.invoice_settings.reminder_schedule_days
        ):
            validation_report["warnings"].append(
                "Payment reminders enabled but no reminder schedule configured"
            )

        logger.info(
            f"Settings validation for tenant {tenant_id}: {'valid' if validation_report['valid'] else 'invalid'}"
        )
        return validation_report

    # ============================================================================
    # Private helper methods
    # ============================================================================

    def _get_default_settings(self, tenant_id: str) -> BillingSettings:
        """Get default billing settings"""

        return BillingSettings(
            tenant_id=tenant_id,
            company_info=CompanyInfo(
                name="Your Company",
                address_line1="123 Business Street",
                city="San Francisco",
                state="CA",
                postal_code="94105",
                country="US",
                email="billing@yourcompany.com",
            ),
            tax_settings=TaxSettings(),
            payment_settings=PaymentSettings(),
            invoice_settings=InvoiceSettings(),
            notification_settings=NotificationSettings(),
        )

    async def _validate_settings(self, settings: BillingSettings) -> None:
        """Validate settings before saving"""

        # Basic validation is handled by Pydantic models
        # Add any business logic validation here

        # Validate currency codes
        if (
            settings.payment_settings.default_currency
            not in settings.payment_settings.supported_currencies
        ):
            raise ValueError("Default currency must be in supported currencies list")

        # Validate tax registrations format
        for reg in settings.tax_settings.tax_registrations:
            if "jurisdiction" not in reg or "registration_number" not in reg:
                raise ValueError("Tax registrations must have jurisdiction and registration_number")

        # Validate webhook URL format if provided
        if settings.notification_settings.webhook_url:
            if not settings.notification_settings.webhook_url.startswith(("http://", "https://")):
                raise ValueError("Webhook URL must be a valid HTTP/HTTPS URL")

        logger.debug("Settings validation completed successfully")

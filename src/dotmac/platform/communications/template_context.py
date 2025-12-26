"""
Template context builders for email templates.

Provides centralized context building with branding support for all email templates.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from .template_service import BrandingConfig, TenantAwareTemplateService

if TYPE_CHECKING:
    from dotmac.platform.billing.models import Invoice, Payment, Subscription
    from dotmac.platform.tenant.schemas import TenantBrandingConfig


def _format_currency(amount: int, currency: str) -> str:
    return TenantAwareTemplateService._format_currency(amount, currency)


def branding_from_tenant(tenant_branding: TenantBrandingConfig | None) -> BrandingConfig:
    """
    Convert tenant branding config to template BrandingConfig.

    Args:
        tenant_branding: Tenant-specific branding configuration

    Returns:
        BrandingConfig for template rendering
    """
    if not tenant_branding:
        return BrandingConfig()

    return BrandingConfig(
        product_name=getattr(tenant_branding, "product_name", None) or "DotMac Platform",
        company_name=getattr(tenant_branding, "company_name", None),
        support_email=getattr(tenant_branding, "support_email", None),
        primary_color=getattr(tenant_branding, "primary_color", None) or "#0070f3",
        secondary_color=getattr(tenant_branding, "secondary_color", None) or "#6b7280",
        accent_color=getattr(tenant_branding, "accent_color", None) or "#10b981",
        logo_url=getattr(tenant_branding, "logo_light_url", None),
        logo_dark_url=getattr(tenant_branding, "logo_dark_url", None),
        docs_url=getattr(tenant_branding, "docs_url", None),
        support_portal_url=getattr(tenant_branding, "support_portal_url", None),
    )


class TemplateContextBuilder:
    """Build context dictionaries for email templates."""

    @staticmethod
    def base_context() -> dict[str, Any]:
        """
        Base context available to all templates.

        Returns:
            Dictionary with common template variables
        """
        return {
            "current_year": datetime.now(UTC).year,
        }

    # =========================================================================
    # Auth Templates
    # =========================================================================

    @staticmethod
    def welcome(
        user_name: str,
        email: str,
        login_url: str | None = None,
        app_name: str = "DotMac Platform",
    ) -> dict[str, Any]:
        """
        Build context for welcome email.

        Args:
            user_name: User's display name
            email: User's email address
            login_url: Optional login page URL
            app_name: Application name
        """
        context = TemplateContextBuilder.base_context()
        context.update({
            "user_name": user_name,
            "email": email,
            "login_url": login_url,
            "app_name": app_name,
        })
        return context

    @staticmethod
    def password_reset(
        user_name: str,
        reset_link: str,
        expiry_hours: int = 1,
        app_name: str = "DotMac Platform",
    ) -> dict[str, Any]:
        """
        Build context for password reset email.

        Args:
            user_name: User's display name
            reset_link: Password reset URL with token
            expiry_hours: Hours until the reset link expires
            app_name: Application name
        """
        context = TemplateContextBuilder.base_context()
        context.update({
            "user_name": user_name,
            "reset_link": reset_link,
            "expiry_hours": expiry_hours,
            "app_name": app_name,
        })
        return context

    @staticmethod
    def verification(
        user_name: str,
        verification_url: str,
        expiry_hours: int = 24,
        app_name: str = "DotMac Platform",
    ) -> dict[str, Any]:
        """
        Build context for email verification.

        Args:
            user_name: User's display name
            verification_url: Email verification URL
            expiry_hours: Hours until the verification link expires
            app_name: Application name
        """
        context = TemplateContextBuilder.base_context()
        context.update({
            "user_name": user_name,
            "verification_url": verification_url,
            "expiry_hours": expiry_hours,
            "app_name": app_name,
        })
        return context

    @staticmethod
    def password_reset_success(
        user_name: str,
        app_name: str = "DotMac Platform",
    ) -> dict[str, Any]:
        """
        Build context for password reset success email.

        Args:
            user_name: User's display name
            app_name: Application name
        """
        context = TemplateContextBuilder.base_context()
        context.update({
            "user_name": user_name,
            "app_name": app_name,
        })
        return context

    # =========================================================================
    # Billing Templates
    # =========================================================================

    @staticmethod
    def subscription_created(
        plan_name: str,
        price_amount: int,
        billing_cycle: str,
        start_date: datetime,
        next_billing_date: datetime,
        dashboard_url: str,
        trial_end: datetime | None = None,
        currency: str = "USD",
    ) -> dict[str, Any]:
        """
        Build context for subscription created email.

        Args:
            plan_name: Name of the subscription plan
            price_amount: Price in cents
            billing_cycle: Billing frequency (monthly, yearly)
            start_date: Subscription start date
            next_billing_date: Next billing date
            dashboard_url: Customer billing dashboard URL
            trial_end: Trial period end date (if applicable)
            currency: Currency code
        """
        context = TemplateContextBuilder.base_context()
        context.update({
            "plan_name": plan_name,
            "price_amount": price_amount,
            "price_formatted": _format_currency(price_amount, currency),
            "billing_cycle": billing_cycle,
            "start_date": start_date,
            "next_billing_date": next_billing_date,
            "dashboard_url": dashboard_url,
            "trial_end": trial_end,
            "has_trial": trial_end is not None,
            "currency": currency,
        })
        return context

    @staticmethod
    def subscription_upgraded(
        old_plan_name: str,
        new_plan_name: str,
        prorated_credit: int,
        prorated_charge: int,
        total_charged: int,
        new_price: int,
        billing_cycle: str,
        next_billing_date: datetime,
        currency: str = "USD",
    ) -> dict[str, Any]:
        """
        Build context for subscription upgrade email.

        Args:
            old_plan_name: Previous plan name
            new_plan_name: New plan name
            prorated_credit: Credit for unused old plan (cents)
            prorated_charge: Charge for new plan (cents)
            total_charged: Total amount charged (cents)
            new_price: New recurring price (cents)
            billing_cycle: Billing frequency
            next_billing_date: Next billing date
            currency: Currency code
        """
        context = TemplateContextBuilder.base_context()
        context.update({
            "old_plan_name": old_plan_name,
            "new_plan_name": new_plan_name,
            "prorated_credit": prorated_credit,
            "prorated_credit_formatted": _format_currency(prorated_credit, currency),
            "prorated_charge": prorated_charge,
            "prorated_charge_formatted": _format_currency(prorated_charge, currency),
            "total_charged": total_charged,
            "total_charged_formatted": _format_currency(total_charged, currency),
            "new_price": new_price,
            "new_price_formatted": _format_currency(new_price, currency),
            "billing_cycle": billing_cycle,
            "next_billing_date": next_billing_date,
            "currency": currency,
        })
        return context

    @staticmethod
    def subscription_canceled(
        plan_name: str,
        access_until_date: datetime,
        refund_amount: int = 0,
        feedback_reason: str = "",
        reactivate_url: str = "",
        currency: str = "USD",
    ) -> dict[str, Any]:
        """
        Build context for subscription cancellation email.

        Args:
            plan_name: Canceled plan name
            access_until_date: Date until which access remains
            refund_amount: Refund amount in cents
            feedback_reason: Cancellation reason provided
            reactivate_url: URL to reactivate subscription
            currency: Currency code
        """
        context = TemplateContextBuilder.base_context()
        context.update({
            "plan_name": plan_name,
            "access_until_date": access_until_date,
            "refund_amount": refund_amount,
            "refund_formatted": _format_currency(refund_amount, currency),
            "feedback_reason": feedback_reason or "No reason provided",
            "reactivate_url": reactivate_url,
            "currency": currency,
        })
        return context

    @staticmethod
    def payment_succeeded(
        amount: int,
        payment_date: datetime,
        payment_method: str,
        invoice_number: str,
        invoice_url: str,
        currency: str = "USD",
    ) -> dict[str, Any]:
        """
        Build context for payment success email.

        Args:
            amount: Payment amount in cents
            payment_date: Date of payment
            payment_method: Payment method description
            invoice_number: Invoice reference number
            invoice_url: URL to download invoice
            currency: Currency code
        """
        context = TemplateContextBuilder.base_context()
        context.update({
            "amount": amount,
            "amount_formatted": _format_currency(amount, currency),
            "payment_date": payment_date,
            "payment_method": payment_method,
            "invoice_number": invoice_number,
            "invoice_url": invoice_url,
            "currency": currency,
        })
        return context

    @staticmethod
    def payment_failed(
        amount: int,
        payment_method: str,
        failure_reason: str,
        retry_date: str,
        update_payment_url: str,
        currency: str = "USD",
    ) -> dict[str, Any]:
        """
        Build context for payment failure email.

        Args:
            amount: Failed payment amount in cents
            payment_method: Payment method that failed
            failure_reason: Reason for failure
            retry_date: When the payment will be retried
            update_payment_url: URL to update payment method
            currency: Currency code
        """
        context = TemplateContextBuilder.base_context()
        context.update({
            "amount": amount,
            "amount_formatted": _format_currency(amount, currency),
            "payment_method": payment_method,
            "failure_reason": failure_reason,
            "retry_date": retry_date,
            "update_payment_url": update_payment_url,
            "currency": currency,
        })
        return context

    @staticmethod
    def invoice_generated(
        invoice_number: str,
        issue_date: datetime,
        due_date: datetime | None,
        amount: int,
        payment_method: str,
        invoice_url: str,
        notes: str | None = None,
        currency: str = "USD",
    ) -> dict[str, Any]:
        """
        Build context for invoice generated email.

        Args:
            invoice_number: Invoice reference number
            issue_date: Invoice issue date
            due_date: Payment due date
            amount: Invoice amount in cents
            payment_method: Payment method on file
            invoice_url: URL to view/download invoice
            currency: Currency code
        """
        context = TemplateContextBuilder.base_context()
        context.update({
            "invoice_number": invoice_number,
            "issue_date": issue_date,
            "due_date": due_date,
            "amount": amount,
            "amount_formatted": _format_currency(amount, currency),
            "payment_method": payment_method,
            "invoice_url": invoice_url,
            "currency": currency,
            "notes": notes,
            "has_notes": bool(notes),
        })
        return context

    @staticmethod
    def payment_reminder(
        invoice_number: str,
        due_date: datetime | None,
        amount_due: int,
        invoice_url: str,
        status: str,
        custom_message: str | None = None,
        currency: str = "USD",
    ) -> dict[str, Any]:
        """
        Build context for payment reminder email.

        Args:
            invoice_number: Invoice reference number
            due_date: Payment due date
            amount_due: Amount due in cents
            invoice_url: URL to view/download invoice
            status: Invoice status
            custom_message: Optional custom message
            currency: Currency code
        """
        context = TemplateContextBuilder.base_context()
        context.update({
            "invoice_number": invoice_number,
            "due_date": due_date,
            "amount_due": amount_due,
            "amount_due_formatted": _format_currency(amount_due, currency),
            "invoice_url": invoice_url,
            "status": status,
            "custom_message": custom_message,
            "has_custom_message": bool(custom_message),
            "currency": currency,
        })
        return context

    @staticmethod
    def addon_purchased(
        addon_name: str,
        price: int,
        billing_cycle: str,
        quantity: int,
        total: int,
        next_billing_date: datetime,
        addon_url: str,
        currency: str = "USD",
    ) -> dict[str, Any]:
        """
        Build context for add-on purchase email.

        Args:
            addon_name: Name of the add-on
            price: Unit price in cents
            billing_cycle: Billing frequency
            quantity: Number of units purchased
            total: Total amount in cents
            next_billing_date: Next billing date
            addon_url: URL to manage add-ons
            currency: Currency code
        """
        context = TemplateContextBuilder.base_context()
        context.update({
            "addon_name": addon_name,
            "price": price,
            "price_formatted": _format_currency(price, currency),
            "billing_cycle": billing_cycle,
            "quantity": quantity,
            "total": total,
            "total_formatted": _format_currency(total, currency),
            "next_billing_date": next_billing_date,
            "addon_url": addon_url,
            "currency": currency,
        })
        return context

    @staticmethod
    def usage_limit_warning(
        metric_name: str,
        current_usage: int,
        limit: int,
        percentage: int,
        period_start: datetime,
        period_end: datetime,
        remaining: int,
        unit: str,
        upgrade_url: str,
    ) -> dict[str, Any]:
        """
        Build context for usage limit warning email.

        Args:
            metric_name: Name of the usage metric
            current_usage: Current usage amount
            limit: Usage limit
            percentage: Percentage of limit used
            period_start: Billing period start
            period_end: Billing period end
            remaining: Remaining usage
            unit: Unit of measurement
            upgrade_url: URL to upgrade plan
        """
        context = TemplateContextBuilder.base_context()
        context.update({
            "metric_name": metric_name,
            "current_usage": current_usage,
            "limit": limit,
            "percentage": percentage,
            "period_start": period_start,
            "period_end": period_end,
            "remaining": remaining,
            "unit": unit,
            "upgrade_url": upgrade_url,
        })
        return context

    # =========================================================================
    # Helper methods for building context from models
    # =========================================================================

    @staticmethod
    def from_subscription(
        subscription: Subscription,
        dashboard_url: str,
    ) -> dict[str, Any]:
        """
        Build subscription_created context from a Subscription model.

        Args:
            subscription: Subscription model instance
            dashboard_url: Customer billing dashboard URL
        """
        raw_plan_name = (
            getattr(subscription, "plan_name", None)
            or getattr(subscription, "plan_id", None)
            or "Subscription"
        )
        plan_name = str(raw_plan_name)

        raw_price = getattr(subscription, "price_amount", None)
        if raw_price is None:
            raw_price = getattr(subscription, "price", None)
        try:
            price_amount = int(raw_price) if raw_price is not None else 0
        except (TypeError, ValueError):
            price_amount = 0

        billing_cycle = str(getattr(subscription, "billing_cycle", None) or "monthly")

        start_date = (
            getattr(subscription, "started_at", None)
            or getattr(subscription, "current_period_start", None)
            or getattr(subscription, "created_at", None)
            or datetime.now(UTC)
        )
        next_billing_date = (
            getattr(subscription, "current_period_end", None)
            or getattr(subscription, "next_billing_date", None)
            or datetime.now(UTC)
        )
        trial_end = getattr(subscription, "trial_end", None)

        return TemplateContextBuilder.subscription_created(
            plan_name=plan_name,
            price_amount=price_amount,
            billing_cycle=billing_cycle,
            start_date=start_date,
            next_billing_date=next_billing_date,
            dashboard_url=dashboard_url,
            trial_end=trial_end,
        )

    @staticmethod
    def from_payment(
        payment: Payment,
        invoice_url: str,
    ) -> dict[str, Any]:
        """
        Build payment_succeeded context from a Payment model.

        Args:
            payment: Payment model instance
            invoice_url: URL to download invoice
        """
        return TemplateContextBuilder.payment_succeeded(
            amount=payment.amount,
            payment_date=payment.created_at,
            payment_method=f"****{payment.payment_method_last4}" if hasattr(payment, "payment_method_last4") else "Card",
            invoice_number=payment.invoice_number if hasattr(payment, "invoice_number") else "",
            invoice_url=invoice_url,
        )

    @staticmethod
    def from_invoice(
        invoice: Invoice,
        invoice_url: str,
    ) -> dict[str, Any]:
        """
        Build invoice_generated context from an Invoice model.

        Args:
            invoice: Invoice model instance
            invoice_url: URL to view/download invoice
        """
        raw_number = (
            getattr(invoice, "number", None)
            or getattr(invoice, "invoice_number", None)
            or getattr(invoice, "invoice_id", None)
            or getattr(invoice, "id", None)
            or "unknown"
        )
        invoice_number = str(raw_number)

        issue_date = (
            getattr(invoice, "issue_date", None)
            or getattr(invoice, "created_at", None)
            or datetime.now(UTC)
        )
        due_date = getattr(invoice, "due_date", None) or issue_date

        raw_amount = (
            getattr(invoice, "total", None)
            or getattr(invoice, "total_amount", None)
            or getattr(invoice, "subtotal", None)
            or 0
        )
        try:
            amount = int(raw_amount)
        except (TypeError, ValueError):
            amount = 0

        return TemplateContextBuilder.invoice_generated(
            invoice_number=invoice_number,
            issue_date=issue_date,
            due_date=due_date,
            amount=amount,
            payment_method="Card on file",
            invoice_url=invoice_url,
        )

"""
Tests for TenantAwareTemplateService with file-based templates and tenant overrides.
"""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from dotmac.platform.communications.template_context import TemplateContextBuilder
from dotmac.platform.communications.template_service import (
    BrandingConfig,
    RenderedEmail,
    TenantAwareTemplateService,
    TemplateBundle,
    get_tenant_template_service,
)


# Path to the templates directory
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "src" / "dotmac" / "platform" / "templates"


@pytest.mark.unit
class TestTenantAwareTemplateServiceInit:
    """Test TenantAwareTemplateService initialization."""

    def test_init_with_default_template_dir(self):
        """Test initialization with default template directory."""
        service = TenantAwareTemplateService()

        assert service.template_dir is not None
        assert service.env is not None
        assert service.string_env is not None

    def test_init_with_custom_template_dir(self):
        """Test initialization with custom template directory."""
        if TEMPLATES_DIR.exists():
            service = TenantAwareTemplateService(template_dir=TEMPLATES_DIR)
            assert service.template_dir == TEMPLATES_DIR
            assert service.env is not None

    def test_template_globals_added(self):
        """Test that template globals are added."""
        service = TenantAwareTemplateService()

        assert "len" in service.env.globals
        assert "str" in service.env.globals
        assert "now" in service.env.globals
        assert "today" in service.env.globals

    def test_custom_filters_added(self):
        """Test that custom filters are added."""
        service = TenantAwareTemplateService()

        assert "format_currency" in service.env.filters
        assert "format_date" in service.env.filters
        assert "format_datetime" in service.env.filters


@pytest.mark.unit
class TestCustomFilters:
    """Test custom Jinja2 filters."""

    def test_format_currency_usd(self):
        """Test USD currency formatting."""
        result = TenantAwareTemplateService._format_currency(1000, "USD")
        assert result == "$10.00"

    def test_format_currency_cents(self):
        """Test currency formatting with cents."""
        result = TenantAwareTemplateService._format_currency(9999, "USD")
        assert result == "$99.99"

    def test_format_currency_eur(self):
        """Test EUR currency formatting."""
        result = TenantAwareTemplateService._format_currency(5000, "EUR")
        assert result == "€50.00"

    def test_format_date(self):
        """Test date formatting."""
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
        result = TenantAwareTemplateService._format_date(dt)
        assert result == "January 15, 2024"

    def test_format_date_custom_format(self):
        """Test date formatting with custom format."""
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
        result = TenantAwareTemplateService._format_date(dt, "%Y-%m-%d")
        assert result == "2024-01-15"

    def test_format_date_none(self):
        """Test date formatting with None."""
        result = TenantAwareTemplateService._format_date(None)
        assert result == ""

    def test_format_datetime(self):
        """Test datetime formatting."""
        dt = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)
        result = TenantAwareTemplateService._format_datetime(dt)
        assert "January 15, 2024" in result
        assert "02:30 PM" in result


@pytest.mark.unit
class TestTemplateKeyConversion:
    """Test template key to path conversion."""

    def test_email_auth_template(self):
        """Test email auth template key conversion."""
        service = TenantAwareTemplateService()
        path = service._template_key_to_path("email.auth.welcome", "html")
        assert path == "email/auth/welcome.html.j2"

    def test_email_billing_template(self):
        """Test email billing template key conversion."""
        service = TenantAwareTemplateService()
        path = service._template_key_to_path("email.billing.payment_succeeded", "txt")
        assert path == "email/billing/payment_succeeded.txt.j2"

    def test_subject_template(self):
        """Test subject template key conversion."""
        service = TenantAwareTemplateService()
        path = service._template_key_to_path("email.auth.password_reset", "subject")
        assert path == "email/auth/password_reset.subject.j2"


@pytest.mark.unit
class TestBrandingConfig:
    """Test BrandingConfig dataclass."""

    def test_default_values(self):
        """Test default branding values."""
        branding = BrandingConfig()

        assert branding.product_name == "DotMac Platform"
        assert branding.primary_color == "#0070f3"
        assert branding.secondary_color == "#6b7280"
        assert branding.accent_color == "#10b981"

    def test_custom_values(self):
        """Test custom branding values."""
        branding = BrandingConfig(
            product_name="My App",
            company_name="My Company",
            primary_color="#ff0000",
            support_email="support@myapp.com",
        )

        assert branding.product_name == "My App"
        assert branding.company_name == "My Company"
        assert branding.primary_color == "#ff0000"
        assert branding.support_email == "support@myapp.com"


@pytest.mark.unit
class TestContextBuilding:
    """Test context building methods."""

    def test_build_full_context_with_branding(self):
        """Test full context building with branding."""
        service = TenantAwareTemplateService()
        branding = BrandingConfig(
            product_name="Test App",
            support_email="support@test.com",
        )

        context = service._build_full_context(
            {"user_name": "John"},
            branding=branding,
        )

        assert context["user_name"] == "John"
        assert context["branding"]["product_name"] == "Test App"
        assert context["branding"]["support_email"] == "support@test.com"
        assert "current_year" in context

    def test_build_full_context_without_branding(self):
        """Test full context building without branding."""
        service = TenantAwareTemplateService()

        context = service._build_full_context({"user_name": "Jane"})

        assert context["user_name"] == "Jane"
        assert context["branding"]["product_name"] == "DotMac Platform"
        assert "current_year" in context


@pytest.mark.unit
class TestTemplateContextBuilder:
    """Test TemplateContextBuilder static methods."""

    def test_welcome_context(self):
        """Test welcome email context building."""
        context = TemplateContextBuilder.welcome(
            user_name="John Doe",
            email="john@example.com",
            login_url="https://app.example.com/login",
        )

        assert context["user_name"] == "John Doe"
        assert context["email"] == "john@example.com"
        assert context["login_url"] == "https://app.example.com/login"
        assert "current_year" in context

    def test_password_reset_context(self):
        """Test password reset email context building."""
        context = TemplateContextBuilder.password_reset(
            user_name="Jane Doe",
            reset_link="https://app.example.com/reset?token=abc123",
            expiry_hours=1,
        )

        assert context["user_name"] == "Jane Doe"
        assert context["reset_link"] == "https://app.example.com/reset?token=abc123"
        assert context["expiry_hours"] == 1

    def test_subscription_created_context(self):
        """Test subscription created email context building."""
        now = datetime.now(UTC)
        context = TemplateContextBuilder.subscription_created(
            plan_name="Pro",
            price_amount=2999,
            billing_cycle="monthly",
            start_date=now,
            next_billing_date=now,
            dashboard_url="https://app.example.com/billing",
        )

        assert context["plan_name"] == "Pro"
        assert context["price_formatted"] == "$29.99"
        assert context["billing_cycle"] == "monthly"
        assert context["has_trial"] is False

    def test_subscription_created_context_with_trial(self):
        """Test subscription created context with trial."""
        now = datetime.now(UTC)
        trial_end = datetime(2024, 2, 15, tzinfo=UTC)

        context = TemplateContextBuilder.subscription_created(
            plan_name="Pro",
            price_amount=2999,
            billing_cycle="monthly",
            start_date=now,
            next_billing_date=now,
            dashboard_url="https://app.example.com/billing",
            trial_end=trial_end,
        )

        assert context["has_trial"] is True
        assert context["trial_end"] == trial_end

    def test_payment_succeeded_context(self):
        """Test payment succeeded email context building."""
        payment_date = datetime.now(UTC)
        context = TemplateContextBuilder.payment_succeeded(
            amount=4999,
            payment_date=payment_date,
            payment_method="****1234",
            invoice_number="INV-001",
            invoice_url="https://app.example.com/invoices/001",
        )

        assert context["amount_formatted"] == "$49.99"
        assert context["payment_method"] == "****1234"
        assert context["invoice_number"] == "INV-001"

    def test_payment_failed_context(self):
        """Test payment failed email context building."""
        context = TemplateContextBuilder.payment_failed(
            amount=2999,
            payment_method="****4321",
            failure_reason="Insufficient funds",
            retry_date="in 3 days",
            update_payment_url="https://app.example.com/billing/payment",
        )

        assert context["amount_formatted"] == "$29.99"
        assert context["failure_reason"] == "Insufficient funds"
        assert context["retry_date"] == "in 3 days"


@pytest.mark.unit
class TestTemplateValidation:
    """Test template validation methods."""

    def test_validate_valid_template(self):
        """Test validating a valid template."""
        service = TenantAwareTemplateService()
        is_valid, error = service.validate_template("Hello {{ name }}!")

        assert is_valid is True
        assert error is None

    def test_validate_invalid_template(self):
        """Test validating an invalid template."""
        service = TenantAwareTemplateService()
        is_valid, error = service.validate_template("Hello {{ name }")

        assert is_valid is False
        assert error is not None
        assert "Syntax error" in error

    def test_extract_variables(self):
        """Test extracting variables from template."""
        service = TenantAwareTemplateService()
        variables = service.extract_variables(
            "Hello {{ user_name }}, your order {{ order_id }} is ready."
        )

        assert "user_name" in variables
        assert "order_id" in variables
        assert len(variables) == 2


@pytest.mark.unit
class TestStringRendering:
    """Test string template rendering."""

    def test_render_simple_string(self):
        """Test rendering a simple string template."""
        service = TenantAwareTemplateService()
        result = service._render_string(
            "Hello {{ name }}!",
            {"name": "World"},
            autoescape=False,
        )

        assert result == "Hello World!"

    def test_render_with_filters(self):
        """Test rendering with custom filters."""
        service = TenantAwareTemplateService()
        dt = datetime(2024, 1, 15, tzinfo=UTC)
        result = service._render_string(
            "Date: {{ date | format_date }}",
            {"date": dt},
            autoescape=False,
        )

        assert result == "Date: January 15, 2024"


@pytest.mark.unit
class TestGlobalServiceInstance:
    """Test global service instance."""

    def test_get_tenant_template_service(self):
        """Test getting global tenant template service."""
        service1 = get_tenant_template_service()
        service2 = get_tenant_template_service()

        # Should return the same instance
        assert service1 is service2


@pytest.mark.skipif(
    not TEMPLATES_DIR.exists(),
    reason="Templates directory not found",
)
@pytest.mark.unit
class TestFileTemplateLoading:
    """Test loading templates from files."""

    @pytest.fixture
    def service(self):
        """Create service with templates directory."""
        return TenantAwareTemplateService(template_dir=TEMPLATES_DIR)

    def test_load_auth_welcome_template(self, service):
        """Test loading auth welcome template."""
        bundle = service._get_file_template("email.auth.welcome")

        assert bundle.source == "file"
        assert bundle.template_key == "email.auth.welcome"
        assert bundle.html_template is not None or bundle.text_template is not None

    def test_load_billing_payment_succeeded_template(self, service):
        """Test loading billing payment succeeded template."""
        bundle = service._get_file_template("email.billing.payment_succeeded")

        assert bundle.source == "file"
        assert bundle.template_key == "email.billing.payment_succeeded"

    def test_load_nonexistent_template_raises(self, service):
        """Test loading nonexistent template raises error."""
        with pytest.raises(ValueError) as exc_info:
            service._get_file_template("email.nonexistent.template")

        assert "No template files found" in str(exc_info.value)


@pytest.mark.skipif(
    not TEMPLATES_DIR.exists(),
    reason="Templates directory not found",
)
@pytest.mark.asyncio
@pytest.mark.unit
class TestEmailRendering:
    """Test email template rendering."""

    @pytest.fixture
    def service(self):
        """Create service with templates directory."""
        return TenantAwareTemplateService(template_dir=TEMPLATES_DIR)

    async def test_render_welcome_email(self, service):
        """Test rendering welcome email."""
        context = TemplateContextBuilder.welcome(
            user_name="John Doe",
            email="john@example.com",
        )

        result = await service.render_email(
            template_key="email.auth.welcome",
            context=context,
        )

        assert isinstance(result, RenderedEmail)
        assert result.template_key == "email.auth.welcome"
        assert result.html_body is not None or result.text_body is not None
        if result.html_body:
            assert "John Doe" in result.html_body

    async def test_render_payment_succeeded_email(self, service):
        """Test rendering payment succeeded email."""
        payment_date = datetime.now(UTC)
        context = TemplateContextBuilder.payment_succeeded(
            amount=4999,
            payment_date=payment_date,
            payment_method="****1234",
            invoice_number="INV-001",
            invoice_url="https://example.com/invoices/001",
        )

        result = await service.render_email(
            template_key="email.billing.payment_succeeded",
            context=context,
        )

        assert isinstance(result, RenderedEmail)
        if result.html_body:
            assert "$49.99" in result.html_body

    async def test_render_with_branding(self, service):
        """Test rendering with custom branding."""
        branding = BrandingConfig(
            product_name="My Custom App",
            primary_color="#ff5500",
            support_email="help@myapp.com",
        )

        context = TemplateContextBuilder.welcome(
            user_name="Jane Doe",
            email="jane@example.com",
        )

        result = await service.render_email(
            template_key="email.auth.welcome",
            context=context,
            branding=branding,
        )

        # The branding should be applied to the template
        assert result is not None
        assert result.html_body is not None or result.text_body is not None

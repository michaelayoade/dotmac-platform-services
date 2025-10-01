"""
Tests for billing settings API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from dotmac.platform.main import app
from dotmac.platform.billing.settings.models import (
    BillingSettings,
    CompanyInfo,
    TaxSettings,
    PaymentSettings,
    InvoiceSettings,
    NotificationSettings,
)


client = TestClient(app)


@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def mock_current_user():
    """Mock current user dependency"""
    return {"user_id": "test-user", "tenant_id": "test-tenant"}


@pytest.fixture
def sample_company_info():
    """Sample company info for testing"""
    return CompanyInfo(
        name="Test Company",
        address_line1="123 Test St",
        city="San Francisco",
        state="CA",
        postal_code="94105",
        country="US"
    )


@pytest.fixture
def sample_invoice_settings():
    """Sample invoice settings for testing"""
    return InvoiceSettings(
        invoice_number_prefix="TEST",
        invoice_number_format="{prefix}-{year}-{sequence:04d}",
        default_due_days=15
    )


class TestBillingSettingsAPI:
    """Test billing settings API endpoints"""

    @pytest.mark.asyncio
    async def test_get_billing_settings(self, auth_headers, mock_current_user):
        """Test retrieving billing settings"""
        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
            with patch('dotmac.platform.billing.settings.service.BillingSettingsService.get_settings') as mock_get:
                # Mock the service response
                mock_settings = BillingSettings(
                    tenant_id="test-tenant",
                    company_info=CompanyInfo(
                        name="Test Company",
                        address_line1="123 Test St",
                        city="SF",
                        postal_code="94105",
                        country="US"
                    )
                )
                mock_get.return_value = mock_settings

                response = client.get(
                    "/api/v1/billing/settings",
                    headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert data["tenant_id"] == "test-tenant"
                assert data["company_info"]["name"] == "Test Company"

    @pytest.mark.asyncio
    async def test_update_company_info(self, auth_headers, mock_current_user, sample_company_info):
        """Test updating company information"""
        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
            with patch('dotmac.platform.billing.settings.service.BillingSettingsService.update_company_info') as mock_update:
                # Mock the service response
                mock_settings = BillingSettings(
                    tenant_id="test-tenant",
                    company_info=sample_company_info
                )
                mock_update.return_value = mock_settings

                response = client.put(
                    "/api/v1/billing/settings/company",
                    json=sample_company_info.dict(),
                    headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert data["company_info"]["name"] == "Test Company"

    @pytest.mark.asyncio
    async def test_update_invoice_settings(self, auth_headers, mock_current_user, sample_invoice_settings):
        """Test updating invoice settings including numbering format"""
        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
            with patch('dotmac.platform.billing.settings.service.BillingSettingsService.update_invoice_settings') as mock_update:
                # Mock the service response
                mock_settings = BillingSettings(
                    tenant_id="test-tenant",
                    company_info=CompanyInfo(
                        name="Test",
                        address_line1="123 St",
                        city="SF",
                        postal_code="94105",
                        country="US"
                    ),
                    invoice_settings=sample_invoice_settings
                )
                mock_update.return_value = mock_settings

                response = client.put(
                    "/api/v1/billing/settings/invoice",
                    json=sample_invoice_settings.dict(),
                    headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert data["invoice_settings"]["invoice_number_prefix"] == "TEST"
                assert data["invoice_settings"]["invoice_number_format"] == "{prefix}-{year}-{sequence:04d}"
                assert data["invoice_settings"]["default_due_days"] == 15

    @pytest.mark.asyncio
    async def test_update_tax_settings(self, auth_headers, mock_current_user):
        """Test updating tax settings"""
        tax_settings = TaxSettings(
            calculate_tax=True,
            tax_inclusive_pricing=False,
            default_tax_rate=8.25,
            tax_registrations=[
                {"jurisdiction": "US-CA", "registration_number": "123-456"}
            ]
        )

        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
            with patch('dotmac.platform.billing.settings.service.BillingSettingsService.update_tax_settings') as mock_update:
                mock_settings = BillingSettings(
                    tenant_id="test-tenant",
                    company_info=CompanyInfo(
                        name="Test",
                        address_line1="123 St",
                        city="SF",
                        postal_code="94105",
                        country="US"
                    ),
                    tax_settings=tax_settings
                )
                mock_update.return_value = mock_settings

                response = client.put(
                    "/api/v1/billing/settings/tax",
                    json=tax_settings.dict(),
                    headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert data["tax_settings"]["default_tax_rate"] == 8.25
                assert len(data["tax_settings"]["tax_registrations"]) == 1

    @pytest.mark.asyncio
    async def test_update_payment_settings(self, auth_headers, mock_current_user):
        """Test updating payment settings"""
        payment_settings = PaymentSettings(
            enabled_payment_methods=["card", "bank_account", "digital_wallet"],
            default_currency="EUR",
            default_payment_terms=45,
            retry_failed_payments=True,
            max_retry_attempts=5
        )

        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
            with patch('dotmac.platform.billing.settings.service.BillingSettingsService.update_payment_settings') as mock_update:
                mock_settings = BillingSettings(
                    tenant_id="test-tenant",
                    company_info=CompanyInfo(
                        name="Test",
                        address_line1="123 St",
                        city="SF",
                        postal_code="94105",
                        country="US"
                    ),
                    payment_settings=payment_settings
                )
                mock_update.return_value = mock_settings

                response = client.put(
                    "/api/v1/billing/settings/payment",
                    json=payment_settings.dict(),
                    headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert data["payment_settings"]["default_currency"] == "EUR"
                assert data["payment_settings"]["default_payment_terms"] == 45
                assert "digital_wallet" in data["payment_settings"]["enabled_payment_methods"]

    @pytest.mark.asyncio
    async def test_update_notification_settings(self, auth_headers, mock_current_user):
        """Test updating notification settings"""
        notification_settings = NotificationSettings(
            send_invoice_notifications=True,
            send_payment_confirmations=True,
            webhook_url="https://api.example.com/webhooks",
            webhook_events=["invoice.created", "payment.succeeded"]
        )

        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
            with patch('dotmac.platform.billing.settings.service.BillingSettingsService.update_notification_settings') as mock_update:
                mock_settings = BillingSettings(
                    tenant_id="test-tenant",
                    company_info=CompanyInfo(
                        name="Test",
                        address_line1="123 St",
                        city="SF",
                        postal_code="94105",
                        country="US"
                    ),
                    notification_settings=notification_settings
                )
                mock_update.return_value = mock_settings

                response = client.put(
                    "/api/v1/billing/settings/notifications",
                    json=notification_settings.dict(),
                    headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert data["notification_settings"]["webhook_url"] == "https://api.example.com/webhooks"
                assert "invoice.created" in data["notification_settings"]["webhook_events"]

    @pytest.mark.asyncio
    async def test_update_feature_flags(self, auth_headers, mock_current_user):
        """Test updating feature flags"""
        features = {
            "invoicing": True,
            "payments": False,
            "credit_notes": True,
            "tax_calculation": False
        }

        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
            with patch('dotmac.platform.billing.settings.service.BillingSettingsService.update_feature_flags') as mock_update:
                mock_settings = BillingSettings(
                    tenant_id="test-tenant",
                    company_info=CompanyInfo(
                        name="Test",
                        address_line1="123 St",
                        city="SF",
                        postal_code="94105",
                        country="US"
                    ),
                    features_enabled=features
                )
                mock_update.return_value = mock_settings

                response = client.put(
                    "/api/v1/billing/settings/features",
                    json=features,
                    headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert data["features_enabled"]["invoicing"] is True
                assert data["features_enabled"]["payments"] is False

    @pytest.mark.asyncio
    async def test_reset_to_defaults(self, auth_headers, mock_current_user):
        """Test resetting settings to defaults"""
        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
            with patch('dotmac.platform.billing.settings.service.BillingSettingsService.reset_to_defaults') as mock_reset:
                mock_settings = BillingSettings(
                    tenant_id="test-tenant",
                    company_info=CompanyInfo(
                        name="Your Company",
                        address_line1="123 Business Street",
                        city="San Francisco",
                        state="CA",
                        postal_code="94105",
                        country="US"
                    ),
                    invoice_settings=InvoiceSettings()
                )
                mock_reset.return_value = mock_settings

                response = client.post(
                    "/api/v1/billing/settings/reset",
                    headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert data["company_info"]["name"] == "Your Company"
                assert data["invoice_settings"]["invoice_number_prefix"] == "INV"

    @pytest.mark.asyncio
    async def test_validate_settings(self, auth_headers, mock_current_user):
        """Test validating current settings"""
        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
            with patch('dotmac.platform.billing.settings.service.BillingSettingsService.validate_settings_for_tenant') as mock_validate:
                mock_validate.return_value = {
                    "valid": True,
                    "warnings": ["Tax calculation enabled but no tax registrations configured"],
                    "errors": []
                }

                response = client.get(
                    "/api/v1/billing/settings/validate",
                    headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert data["valid"] is True
                assert len(data["warnings"]) == 1

    @pytest.mark.asyncio
    async def test_invoice_numbering_formats(self, auth_headers, mock_current_user):
        """Test different invoice numbering format configurations"""
        test_formats = [
            ("{prefix}-{year}-{sequence:06d}", "INV-2024-000001"),
            ("{prefix}/{year}/{sequence:04d}", "INV/2024/0001"),
            ("{prefix}-{sequence:08d}", "INV-00000001"),
            ("{year}{month:02d}-{sequence:04d}", "202401-0001"),
            ("{prefix}_{year}_{month:02d}_{sequence:04d}", "INV_2024_01_0001")
        ]

        for format_template, expected_example in test_formats:
            invoice_settings = InvoiceSettings(
                invoice_number_prefix="INV",
                invoice_number_format=format_template
            )

            with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
                with patch('dotmac.platform.billing.settings.service.BillingSettingsService.update_invoice_settings') as mock_update:
                    mock_settings = BillingSettings(
                        tenant_id="test-tenant",
                        company_info=CompanyInfo(
                            name="Test",
                            address_line1="123 St",
                            city="SF",
                            postal_code="94105",
                            country="US"
                        ),
                        invoice_settings=invoice_settings
                    )
                    mock_update.return_value = mock_settings

                    response = client.put(
                        "/api/v1/billing/settings/invoice",
                        json=invoice_settings.dict(),
                        headers=auth_headers
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["invoice_settings"]["invoice_number_format"] == format_template

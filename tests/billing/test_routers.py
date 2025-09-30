"""
Comprehensive router endpoint tests for maximum coverage.

Tests all FastAPI endpoints with proper request/response mocking.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from typing import Dict, Any

# Create test app
app = FastAPI()


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_current_user():
    """Mock authenticated user."""
    from dotmac.platform.auth.models import UserClaims
    return UserClaims(
        user_id="user_123",
        tenant_id="tenant_123",
        scopes=["billing:read", "billing:write", "billing:admin"],
        metadata={}
    )


class TestCatalogRouter:
    """Test catalog router endpoints."""

    @pytest.mark.asyncio
    async def test_create_product_endpoint(self, client, mock_current_user):
        """Test POST /products endpoint."""
        from dotmac.platform.billing.catalog.router import router as catalog_router
        app.include_router(catalog_router, prefix="/api/billing")

        request_data = {
            "sku": "TEST-SKU-001",
            "name": "Test Product",
            "description": "Test Description",
            "product_type": "subscription",
            "category": "software",
            "base_price": "99.99",
            "currency": "USD",
            "tax_class": "standard",
            "metadata": {"test": True}
        }

        mock_product = MagicMock()
        mock_product.product_id = "prod_123"
        mock_product.sku = request_data["sku"]
        mock_product.name = request_data["name"]
        mock_product.base_price = Decimal(request_data["base_price"])

        with patch('dotmac.platform.billing.catalog.router.ProductService') as mock_service:
            mock_service.return_value.create_product = AsyncMock(return_value=mock_product)
            with patch('dotmac.platform.billing.catalog.router.get_current_user', return_value=mock_current_user):
                response = client.post("/api/billing/products", json=request_data)

        assert response.status_code == 201
        assert response.json()["sku"] == request_data["sku"]

    @pytest.mark.asyncio
    async def test_get_product_endpoint(self, client, mock_current_user):
        """Test GET /products/{product_id} endpoint."""
        from dotmac.platform.billing.catalog.router import router as catalog_router
        app.include_router(catalog_router, prefix="/api/billing")

        mock_product = MagicMock()
        mock_product.product_id = "prod_123"
        mock_product.sku = "TEST-SKU"
        mock_product.name = "Test Product"
        mock_product.base_price = Decimal("99.99")
        mock_product.is_active = True

        with patch('dotmac.platform.billing.catalog.router.ProductService') as mock_service:
            mock_service.return_value.get_product = AsyncMock(return_value=mock_product)
            with patch('dotmac.platform.billing.catalog.router.get_current_user', return_value=mock_current_user):
                response = client.get("/api/billing/products/prod_123")

        assert response.status_code == 200
        assert response.json()["product_id"] == "prod_123"

    @pytest.mark.asyncio
    async def test_update_product_endpoint(self, client, mock_current_user):
        """Test PATCH /products/{product_id} endpoint."""
        from dotmac.platform.billing.catalog.router import router as catalog_router
        app.include_router(catalog_router, prefix="/api/billing")

        update_data = {
            "name": "Updated Product",
            "base_price": "149.99",
            "is_active": False
        }

        mock_product = MagicMock()
        mock_product.product_id = "prod_123"
        mock_product.name = update_data["name"]
        mock_product.base_price = Decimal(update_data["base_price"])
        mock_product.is_active = update_data["is_active"]

        with patch('dotmac.platform.billing.catalog.router.ProductService') as mock_service:
            mock_service.return_value.update_product = AsyncMock(return_value=mock_product)
            with patch('dotmac.platform.billing.catalog.router.get_current_user', return_value=mock_current_user):
                response = client.patch("/api/billing/products/prod_123", json=update_data)

        assert response.status_code == 200
        assert response.json()["name"] == update_data["name"]

    @pytest.mark.asyncio
    async def test_delete_product_endpoint(self, client, mock_current_user):
        """Test DELETE /products/{product_id} endpoint."""
        from dotmac.platform.billing.catalog.router import router as catalog_router
        app.include_router(catalog_router, prefix="/api/billing")

        with patch('dotmac.platform.billing.catalog.router.ProductService') as mock_service:
            mock_service.return_value.delete_product = AsyncMock()
            with patch('dotmac.platform.billing.catalog.router.get_current_user', return_value=mock_current_user):
                response = client.delete("/api/billing/products/prod_123")

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_list_products_endpoint(self, client, mock_current_user):
        """Test GET /products endpoint with filters."""
        from dotmac.platform.billing.catalog.router import router as catalog_router
        app.include_router(catalog_router, prefix="/api/billing")

        mock_products = [
            MagicMock(product_id=f"prod_{i}", sku=f"SKU-{i:03d}", name=f"Product {i}")
            for i in range(5)
        ]

        with patch('dotmac.platform.billing.catalog.router.ProductService') as mock_service:
            mock_service.return_value.list_products = AsyncMock(return_value=mock_products)
            with patch('dotmac.platform.billing.catalog.router.get_current_user', return_value=mock_current_user):
                response = client.get("/api/billing/products?category=software&is_active=true&limit=10")

        assert response.status_code == 200
        assert len(response.json()) == 5


class TestSubscriptionRouter:
    """Test subscription router endpoints."""

    @pytest.mark.asyncio
    async def test_create_subscription_endpoint(self, client, mock_current_user):
        """Test POST /subscriptions endpoint."""
        from dotmac.platform.billing.subscriptions.router import router as sub_router
        app.include_router(sub_router, prefix="/api/billing")

        request_data = {
            "customer_id": "cust_123",
            "plan_id": "plan_123",
            "metadata": {"source": "api"}
        }

        mock_subscription = MagicMock()
        mock_subscription.subscription_id = "sub_123"
        mock_subscription.customer_id = request_data["customer_id"]
        mock_subscription.plan_id = request_data["plan_id"]
        mock_subscription.status = "active"

        with patch('dotmac.platform.billing.subscriptions.router.SubscriptionService') as mock_service:
            mock_service.return_value.create_subscription = AsyncMock(return_value=mock_subscription)
            with patch('dotmac.platform.billing.subscriptions.router.get_current_user', return_value=mock_current_user):
                response = client.post("/api/billing/subscriptions", json=request_data)

        assert response.status_code == 201
        assert response.json()["subscription_id"] == "sub_123"

    @pytest.mark.asyncio
    async def test_cancel_subscription_endpoint(self, client, mock_current_user):
        """Test POST /subscriptions/{subscription_id}/cancel endpoint."""
        from dotmac.platform.billing.subscriptions.router import router as sub_router
        app.include_router(sub_router, prefix="/api/billing")

        mock_subscription = MagicMock()
        mock_subscription.subscription_id = "sub_123"
        mock_subscription.status = "canceled"
        mock_subscription.cancel_at_period_end = True

        with patch('dotmac.platform.billing.subscriptions.router.SubscriptionService') as mock_service:
            mock_service.return_value.cancel_subscription = AsyncMock(return_value=mock_subscription)
            with patch('dotmac.platform.billing.subscriptions.router.get_current_user', return_value=mock_current_user):
                response = client.post("/api/billing/subscriptions/sub_123/cancel", json={"at_period_end": True})

        assert response.status_code == 200
        assert response.json()["status"] == "canceled"

    @pytest.mark.asyncio
    async def test_change_plan_endpoint(self, client, mock_current_user):
        """Test POST /subscriptions/{subscription_id}/change-plan endpoint."""
        from dotmac.platform.billing.subscriptions.router import router as sub_router
        app.include_router(sub_router, prefix="/api/billing")

        request_data = {
            "new_plan_id": "plan_456",
            "immediate": True
        }

        mock_subscription = MagicMock()
        mock_subscription.subscription_id = "sub_123"
        mock_subscription.plan_id = request_data["new_plan_id"]

        with patch('dotmac.platform.billing.subscriptions.router.SubscriptionService') as mock_service:
            mock_service.return_value.change_plan = AsyncMock(return_value=mock_subscription)
            with patch('dotmac.platform.billing.subscriptions.router.get_current_user', return_value=mock_current_user):
                response = client.post("/api/billing/subscriptions/sub_123/change-plan", json=request_data)

        assert response.status_code == 200
        assert response.json()["plan_id"] == "plan_456"

    @pytest.mark.asyncio
    async def test_get_subscription_usage_endpoint(self, client, mock_current_user):
        """Test GET /subscriptions/{subscription_id}/usage endpoint."""
        from dotmac.platform.billing.subscriptions.router import router as sub_router
        app.include_router(sub_router, prefix="/api/billing")

        mock_usage = {
            "api_calls": {"used": 5000, "included": 10000, "overage": 0},
            "storage_gb": {"used": 75, "included": 100, "overage": 0}
        }

        with patch('dotmac.platform.billing.subscriptions.router.SubscriptionService') as mock_service:
            mock_service.return_value.get_usage = AsyncMock(return_value=mock_usage)
            with patch('dotmac.platform.billing.subscriptions.router.get_current_user', return_value=mock_current_user):
                response = client.get("/api/billing/subscriptions/sub_123/usage")

        assert response.status_code == 200
        assert response.json()["api_calls"]["used"] == 5000


class TestPricingRouter:
    """Test pricing router endpoints."""

    @pytest.mark.asyncio
    async def test_calculate_price_endpoint(self, client, mock_current_user):
        """Test POST /pricing/calculate endpoint."""
        from dotmac.platform.billing.pricing.router import router as pricing_router
        app.include_router(pricing_router, prefix="/api/billing")

        request_data = {
            "product_id": "prod_123",
            "quantity": 2,
            "customer_id": "cust_123",
            "customer_segments": ["premium"]
        }

        mock_result = MagicMock()
        mock_result.original_price = Decimal("200.00")
        mock_result.final_price = Decimal("180.00")
        mock_result.adjustments = [
            {"rule_id": "rule_123", "discount_amount": Decimal("20.00")}
        ]

        with patch('dotmac.platform.billing.pricing.router.PricingEngine') as mock_service:
            mock_service.return_value.calculate_price = AsyncMock(return_value=mock_result)
            with patch('dotmac.platform.billing.pricing.router.get_current_user', return_value=mock_current_user):
                response = client.post("/api/billing/pricing/calculate", json=request_data)

        assert response.status_code == 200
        assert response.json()["final_price"] == "180.00"

    @pytest.mark.asyncio
    async def test_create_pricing_rule_endpoint(self, client, mock_current_user):
        """Test POST /pricing/rules endpoint."""
        from dotmac.platform.billing.pricing.router import router as pricing_router
        app.include_router(pricing_router, prefix="/api/billing")

        request_data = {
            "name": "Volume Discount",
            "description": "10% off bulk orders",
            "discount_type": "percentage",
            "discount_value": "10.0",
            "min_quantity": 10,
            "applies_to_product_ids": ["prod_123"],
            "priority": 100
        }

        mock_rule = MagicMock()
        mock_rule.rule_id = "rule_123"
        mock_rule.name = request_data["name"]
        mock_rule.discount_type = request_data["discount_type"]
        mock_rule.discount_value = Decimal(request_data["discount_value"])

        with patch('dotmac.platform.billing.pricing.router.PricingEngine') as mock_service:
            mock_service.return_value.create_rule = AsyncMock(return_value=mock_rule)
            with patch('dotmac.platform.billing.pricing.router.get_current_user', return_value=mock_current_user):
                response = client.post("/api/billing/pricing/rules", json=request_data)

        assert response.status_code == 201
        assert response.json()["rule_id"] == "rule_123"


class TestWebhookRouter:
    """Test webhook router endpoints."""

    @pytest.mark.asyncio
    async def test_stripe_webhook_endpoint(self, client):
        """Test POST /webhooks/stripe endpoint."""
        from dotmac.platform.billing.webhooks.router import router as webhook_router
        app.include_router(webhook_router, prefix="/api/billing")

        webhook_data = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_123",
                    "amount": 9999,
                    "currency": "usd",
                    "metadata": {
                        "subscription_id": "sub_123",
                        "tenant_id": "tenant_123"
                    }
                }
            }
        }

        with patch('dotmac.platform.billing.webhooks.router.verify_stripe_signature', return_value=True):
            with patch('dotmac.platform.billing.webhooks.router.WebhookHandler') as mock_handler:
                mock_handler.return_value.handle_stripe_event = AsyncMock(return_value={"processed": True})

                response = client.post(
                    "/api/billing/webhooks/stripe",
                    json=webhook_data,
                    headers={"Stripe-Signature": "test_signature"}
                )

        assert response.status_code == 200
        assert response.json()["status"] == "success"


class TestReportsRouter:
    """Test reports router endpoints."""

    @pytest.mark.asyncio
    async def test_generate_invoice_report_endpoint(self, client, mock_current_user):
        """Test GET /reports/invoices endpoint."""
        from dotmac.platform.billing.reports.router import router as reports_router
        app.include_router(reports_router, prefix="/api/billing")

        mock_report = {
            "period": "2024-01",
            "total_invoices": 150,
            "total_revenue": "15000.00",
            "average_invoice": "100.00",
            "top_customers": [
                {"customer_id": "cust_1", "total": "1500.00"},
                {"customer_id": "cust_2", "total": "1200.00"}
            ]
        }

        with patch('dotmac.platform.billing.reports.router.ReportsService') as mock_service:
            mock_service.return_value.generate_invoice_report = AsyncMock(return_value=mock_report)
            with patch('dotmac.platform.billing.reports.router.get_current_user', return_value=mock_current_user):
                response = client.get("/api/billing/reports/invoices?start_date=2024-01-01&end_date=2024-01-31")

        assert response.status_code == 200
        assert response.json()["total_invoices"] == 150

    @pytest.mark.asyncio
    async def test_generate_revenue_report_endpoint(self, client, mock_current_user):
        """Test GET /reports/revenue endpoint."""
        from dotmac.platform.billing.reports.router import router as reports_router
        app.include_router(reports_router, prefix="/api/billing")

        mock_report = {
            "period": "2024-Q1",
            "total_revenue": "45000.00",
            "recurring_revenue": "35000.00",
            "one_time_revenue": "10000.00",
            "growth_rate": "15.5%"
        }

        with patch('dotmac.platform.billing.reports.router.ReportsService') as mock_service:
            mock_service.return_value.generate_revenue_report = AsyncMock(return_value=mock_report)
            with patch('dotmac.platform.billing.reports.router.get_current_user', return_value=mock_current_user):
                response = client.get("/api/billing/reports/revenue?period=quarterly")

        assert response.status_code == 200
        assert response.json()["total_revenue"] == "45000.00"


class TestErrorHandling:
    """Test error handling in routers."""

    @pytest.mark.asyncio
    async def test_handle_not_found_error(self, client, mock_current_user):
        """Test 404 error handling."""
        from dotmac.platform.billing.catalog.router import router as catalog_router
        from dotmac.platform.billing.exceptions import ProductNotFoundError

        app.include_router(catalog_router, prefix="/api/billing")

        with patch('dotmac.platform.billing.catalog.router.ProductService') as mock_service:
            mock_service.return_value.get_product = AsyncMock(side_effect=ProductNotFoundError("Product not found"))
            with patch('dotmac.platform.billing.catalog.router.get_current_user', return_value=mock_current_user):
                response = client.get("/api/billing/products/nonexistent")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_handle_validation_error(self, client, mock_current_user):
        """Test 422 validation error handling."""
        from dotmac.platform.billing.catalog.router import router as catalog_router

        app.include_router(catalog_router, prefix="/api/billing")

        invalid_data = {
            "sku": "",  # Invalid empty SKU
            "name": "Test",
            "base_price": "-10.00"  # Invalid negative price
        }

        response = client.post("/api/billing/products", json=invalid_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_handle_unauthorized_error(self, client):
        """Test 401 unauthorized error."""
        from dotmac.platform.billing.catalog.router import router as catalog_router

        app.include_router(catalog_router, prefix="/api/billing")

        with patch('dotmac.platform.billing.catalog.router.get_current_user', side_effect=HTTPException(status_code=401)):
            response = client.get("/api/billing/products/prod_123")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_handle_forbidden_error(self, client, mock_current_user):
        """Test 403 forbidden error."""
        from dotmac.platform.billing.catalog.router import router as catalog_router

        app.include_router(catalog_router, prefix="/api/billing")

        # Mock user without admin scope
        limited_user = MagicMock()
        limited_user.scopes = ["billing:read"]  # No write permission

        with patch('dotmac.platform.billing.catalog.router.get_current_user', return_value=limited_user):
            with patch('dotmac.platform.billing.catalog.router.require_scope', side_effect=HTTPException(status_code=403)):
                response = client.delete("/api/billing/products/prod_123")

        assert response.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
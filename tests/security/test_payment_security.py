"""
Security tests for payment data handling.
Ensures PCI compliance and secure payment processing.
"""

import pytest
import json
import re
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from dotmac.platform.main import app
from dotmac.platform.billing.models import Customer, Invoice, PaymentMethod


client = TestClient(app)


class TestPaymentDataSecurity:
    """Test payment data is handled securely and PCI compliant."""

    @pytest.mark.security
    def test_credit_card_data_not_stored(self, db):
        """Test that credit card data is never stored in database."""
        # Check database schema doesn't contain sensitive fields
        import sqlalchemy as sa
        from dotmac.platform.database import engine

        inspector = sa.inspect(engine)

        # Check all tables for sensitive field names
        sensitive_patterns = [
            r'card_number', r'cvv', r'cvc', r'security_code',
            r'card_exp', r'expiry', r'card_data'
        ]

        for table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            for column in columns:
                col_name = column['name'].lower()
                for pattern in sensitive_patterns:
                    assert not re.search(pattern, col_name), \
                        f"Sensitive field '{col_name}' found in table '{table_name}'"

    @pytest.mark.security
    def test_payment_method_tokenization(self, client, auth_headers):
        """Test payment methods are properly tokenized."""
        # Attempt to add payment method
        response = client.post(
            "/api/v1/billing/payment-methods",
            json={
                "payment_method_id": "pm_test_token_123456",  # Stripe token only
                "set_as_default": True
            },
            headers=auth_headers
        )

        assert response.status_code in [200, 201]

        # Verify raw card data is not accepted
        response = client.post(
            "/api/v1/billing/payment-methods",
            json={
                "card_number": "4242424242424242",  # Raw card number
                "exp_month": 12,
                "exp_year": 2025,
                "cvc": "123"
            },
            headers=auth_headers
        )

        # Should reject raw card data
        assert response.status_code == 400
        assert "raw card data not accepted" in response.json()["detail"].lower()

    @pytest.mark.security
    def test_pii_data_masking_in_logs(self, client, auth_headers, caplog):
        """Test that PII data is masked in application logs."""
        import logging
        caplog.set_level(logging.INFO)

        # Make request with potentially sensitive data
        client.post(
            "/api/v1/customers",
            json={
                "email": "security.test@example.com",
                "name": "Security Test User",
                "phone": "+1234567890",
                "billing_address": {
                    "line1": "123 Secret Street",
                    "city": "Private City"
                }
            },
            headers=auth_headers
        )

        # Check logs don't contain full sensitive data
        log_output = caplog.text.lower()

        # Email should be masked (show first char + domain)
        assert "security.test@example.com" not in log_output
        if "s***@example.com" in log_output or "security****@example.com" in log_output:
            pass  # Properly masked
        else:
            # Full email shouldn't appear at all
            assert "security" not in log_output or "example.com" not in log_output

        # Phone numbers should be masked
        assert "+1234567890" not in log_output

    @pytest.mark.security
    def test_webhook_signature_validation(self, client):
        """Test Stripe webhook signature validation prevents tampering."""
        webhook_payload = {
            "id": "evt_security_test",
            "type": "invoice.payment_succeeded",
            "data": {"object": {"amount": 999999}}  # Malicious amount
        }

        # Test 1: No signature - should reject
        response = client.post(
            "/api/v1/billing/webhooks/stripe",
            json=webhook_payload
        )
        assert response.status_code == 400

        # Test 2: Invalid signature - should reject
        response = client.post(
            "/api/v1/billing/webhooks/stripe",
            json=webhook_payload,
            headers={"Stripe-Signature": "invalid_signature"}
        )
        assert response.status_code == 400

        # Test 3: Tampered payload with valid signature for different payload - should reject
        original_payload = {"id": "evt_original", "type": "customer.created", "data": {}}
        tampered_payload = {"id": "evt_tampered", "type": "invoice.payment_succeeded", "data": {}}

        # Generate signature for original payload
        import hmac
        import hashlib
        secret = "whsec_test_secret"
        timestamp = str(int(datetime.now().timestamp()))
        signature = hmac.new(
            secret.encode(),
            f"{timestamp}.{json.dumps(original_payload)}".encode(),
            hashlib.sha256
        ).hexdigest()

        # Send tampered payload with original signature
        response = client.post(
            "/api/v1/billing/webhooks/stripe",
            json=tampered_payload,  # Different payload
            headers={"Stripe-Signature": f"t={timestamp},v1={signature}"}
        )
        assert response.status_code == 400

    @pytest.mark.security
    def test_sql_injection_prevention(self, client, auth_headers):
        """Test SQL injection attacks are prevented."""
        # Test various SQL injection patterns
        injection_patterns = [
            "'; DROP TABLE customers; --",
            "' OR 1=1 --",
            "' UNION SELECT * FROM secrets --",
            "'; INSERT INTO invoices (amount_total) VALUES (999999); --"
        ]

        for pattern in injection_patterns:
            # Try injection in search parameter
            response = client.get(
                f"/api/v1/customers?search={pattern}",
                headers=auth_headers
            )

            # Should not crash and should return safe results
            assert response.status_code == 200
            data = response.json()

            # Results should be empty or normal, not show signs of injection
            if "customers" in data:
                assert isinstance(data["customers"], list)
                # No customer should have the injection pattern as name
                for customer in data["customers"]:
                    assert pattern not in customer.get("name", "")

    @pytest.mark.security
    def test_authorization_on_sensitive_endpoints(self, client):
        """Test sensitive billing endpoints require proper authorization."""
        sensitive_endpoints = [
            "GET /api/v1/billing/subscription",
            "POST /api/v1/billing/payment-methods",
            "GET /api/v1/billing/invoices",
            "POST /api/v1/billing/subscription/cancel",
            "GET /api/v1/customers",
            "POST /api/v1/customers"
        ]

        for endpoint in sensitive_endpoints:
            method, path = endpoint.split(" ", 1)

            if method == "GET":
                response = client.get(path)
            elif method == "POST":
                response = client.post(path, json={})
            elif method == "PUT":
                response = client.put(path, json={})
            elif method == "DELETE":
                response = client.delete(path)

            # Should require authentication
            assert response.status_code in [401, 403], \
                f"Endpoint {endpoint} should require authentication"

    @pytest.mark.security
    def test_tenant_isolation_in_billing(self, client, db):
        """Test users can only access their own billing data."""
        from dotmac.platform.auth.jwt_service import JWTService
        from dotmac.platform.tenant.models import Tenant

        jwt_service = JWTService()

        # Create two tenants
        tenant1 = Tenant(name="Tenant 1", slug="tenant1")
        tenant2 = Tenant(name="Tenant 2", slug="tenant2")
        db.add_all([tenant1, tenant2])
        await db.commit()

        # Create customers for each tenant
        customer1 = Customer(
            user_id="user1",
            stripe_customer_id="cus_tenant1",
            tenant_id=tenant1.id,
            email="user1@tenant1.com"
        )
        customer2 = Customer(
            user_id="user2",
            stripe_customer_id="cus_tenant2",
            tenant_id=tenant2.id,
            email="user2@tenant2.com"
        )
        db.add_all([customer1, customer2])
        await db.commit()

        # Create tokens for each tenant
        token1 = jwt_service.create_access_token(
            subject="user1",
            tenant_id=tenant1.id
        )
        token2 = jwt_service.create_access_token(
            subject="user2",
            tenant_id=tenant2.id
        )

        # Test tenant 1 user cannot access tenant 2 data
        response = client.get(
            f"/api/v1/customers/{customer2.id}",
            headers={"Authorization": f"Bearer {token1}"}
        )
        assert response.status_code == 404  # Should not find other tenant's data

        # Test tenant 2 user cannot access tenant 1 data
        response = client.get(
            f"/api/v1/customers/{customer1.id}",
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert response.status_code == 404

    @pytest.mark.security
    def test_rate_limiting_on_payment_endpoints(self, client, auth_headers):
        """Test rate limiting prevents abuse of payment endpoints."""
        # Rapidly attempt payment method additions
        responses = []
        for i in range(20):  # Try to exceed rate limit
            response = client.post(
                "/api/v1/billing/payment-methods",
                json={"payment_method_id": f"pm_test_{i}"},
                headers=auth_headers
            )
            responses.append(response.status_code)

        # Should start getting rate limited
        rate_limited_count = sum(1 for code in responses if code == 429)
        assert rate_limited_count > 0, "Rate limiting not working on payment endpoints"

    @pytest.mark.security
    def test_webhook_replay_attack_prevention(self, client):
        """Test webhook replay attacks are prevented."""
        import hmac
        import hashlib

        webhook_payload = {
            "id": "evt_replay_test",
            "type": "invoice.payment_succeeded",
            "data": {"object": {"id": "in_replay"}}
        }

        secret = "whsec_test_secret"
        timestamp = str(int(datetime.now().timestamp()))
        signature = hmac.new(
            secret.encode(),
            f"{timestamp}.{json.dumps(webhook_payload)}".encode(),
            hashlib.sha256
        ).hexdigest()

        headers = {"Stripe-Signature": f"t={timestamp},v1={signature}"}

        # First request should succeed
        response1 = client.post(
            "/api/v1/billing/webhooks/stripe",
            json=webhook_payload,
            headers=headers
        )
        assert response1.status_code == 200

        # Replay same webhook - should be rejected or handled as duplicate
        response2 = client.post(
            "/api/v1/billing/webhooks/stripe",
            json=webhook_payload,
            headers=headers
        )
        # Should either reject (400/409) or acknowledge as duplicate (200 with message)
        assert response2.status_code in [200, 400, 409]
        if response2.status_code == 200:
            assert "already processed" in response2.json().get("message", "").lower()

    @pytest.mark.security
    def test_timestamp_validation_in_webhooks(self, client):
        """Test webhook timestamp validation prevents old replay attacks."""
        import hmac
        import hashlib

        webhook_payload = {
            "id": "evt_old_timestamp",
            "type": "invoice.created",
            "data": {"object": {}}
        }

        secret = "whsec_test_secret"
        # Use old timestamp (more than 5 minutes ago)
        old_timestamp = str(int((datetime.now() - timedelta(minutes=10)).timestamp()))
        signature = hmac.new(
            secret.encode(),
            f"{old_timestamp}.{json.dumps(webhook_payload)}".encode(),
            hashlib.sha256
        ).hexdigest()

        response = client.post(
            "/api/v1/billing/webhooks/stripe",
            json=webhook_payload,
            headers={"Stripe-Signature": f"t={old_timestamp},v1={signature}"}
        )

        # Should reject old timestamps
        assert response.status_code == 400
        assert "timestamp" in response.json()["detail"].lower()

    @pytest.mark.security
    def test_sensitive_data_in_error_messages(self, client, auth_headers):
        """Test error messages don't leak sensitive information."""
        # Try to access non-existent customer
        response = client.get(
            "/api/v1/customers/99999",
            headers=auth_headers
        )

        error_message = response.json().get("detail", "").lower()

        # Error shouldn't contain database structure info
        sensitive_terms = [
            "table", "column", "select", "from", "where",
            "database", "sql", "query", "constraint"
        ]

        for term in sensitive_terms:
            assert term not in error_message, \
                f"Error message contains sensitive term: {term}"

    @pytest.mark.security
    def test_invoice_access_control(self, client, db):
        """Test users can only access their own invoices."""
        from dotmac.platform.auth.jwt_service import JWTService

        jwt_service = JWTService()

        # Create customers for different users
        customer1 = Customer(user_id="user1", stripe_customer_id="cus_1")
        customer2 = Customer(user_id="user2", stripe_customer_id="cus_2")
        db.add_all([customer1, customer2])
        await db.commit()

        # Create invoices
        invoice1 = Invoice(
            customer_id=customer1.id,
            stripe_invoice_id="in_user1",
            amount_total=2999
        )
        invoice2 = Invoice(
            customer_id=customer2.id,
            stripe_invoice_id="in_user2",
            amount_total=4999
        )
        db.add_all([invoice1, invoice2])
        await db.commit()

        # Create tokens
        token1 = jwt_service.create_access_token(subject="user1")
        token2 = jwt_service.create_access_token(subject="user2")

        # User 1 tries to access user 2's invoice
        response = client.get(
            f"/api/v1/billing/invoices/{invoice2.id}",
            headers={"Authorization": f"Bearer {token1}"}
        )
        assert response.status_code == 404

        # User 2 tries to access user 1's invoice
        response = client.get(
            f"/api/v1/billing/invoices/{invoice1.id}",
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert response.status_code == 404

        # Users can access their own invoices
        response = client.get(
            f"/api/v1/billing/invoices/{invoice1.id}",
            headers={"Authorization": f"Bearer {token1}"}
        )
        assert response.status_code == 200

    @pytest.mark.security
    def test_payment_amount_validation(self, client, auth_headers):
        """Test payment amounts are properly validated."""
        # Test negative amounts
        response = client.post(
            "/api/v1/billing/invoices/1/pay",
            json={
                "amount": -100,  # Negative amount
                "payment_method_id": "pm_test"
            },
            headers=auth_headers
        )
        assert response.status_code == 400

        # Test zero amounts
        response = client.post(
            "/api/v1/billing/invoices/1/pay",
            json={
                "amount": 0,  # Zero amount
                "payment_method_id": "pm_test"
            },
            headers=auth_headers
        )
        assert response.status_code == 400

        # Test extremely large amounts
        response = client.post(
            "/api/v1/billing/invoices/1/pay",
            json={
                "amount": 999999999,  # Unrealistic amount
                "payment_method_id": "pm_test"
            },
            headers=auth_headers
        )
        assert response.status_code == 400

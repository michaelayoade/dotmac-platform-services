"""
Comprehensive tests for bank account management
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.main import app
from dotmac.platform.billing.bank_accounts.models import (
    CompanyBankAccountCreate,
    CompanyBankAccountUpdate,
    CompanyBankAccountResponse,
    BankAccountStatus,
    AccountType,
)
from dotmac.platform.billing.bank_accounts.service import BankAccountService
from dotmac.platform.billing.bank_accounts.entities import CompanyBankAccount

client = TestClient(app)


@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def mock_current_user():
    """Mock current user dependency"""
    return {
        "user_id": "test-user-123",
        "tenant_id": "test-tenant",
        "email": "test@example.com"
    }


@pytest.fixture
def sample_bank_account_data():
    """Sample bank account data for testing"""
    return CompanyBankAccountCreate(
        account_name="Test Company LLC",
        account_nickname="Main Operating Account",
        bank_name="Chase Bank",
        bank_address="123 Bank St, New York, NY",
        bank_country="US",
        account_number="1234567890",
        account_type=AccountType.BUSINESS,
        currency="USD",
        routing_number="021000021",
        swift_code="CHASUS33",
        iban=None,
        is_primary=True,
        accepts_deposits=True,
        notes="Primary operating account for the company"
    )


class TestBankAccountCRUD:
    """Test CRUD operations for bank accounts"""

    @pytest.mark.asyncio
    async def test_create_bank_account(self, auth_headers, mock_current_user, sample_bank_account_data):
        """Test creating a new bank account"""
        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
            with patch('dotmac.platform.billing.bank_accounts.service.BankAccountService.create_bank_account') as mock_create:
                # Mock the service response
                mock_response = CompanyBankAccountResponse(
                    id=1,
                    tenant_id="test-tenant",
                    account_name=sample_bank_account_data.account_name,
                    account_nickname=sample_bank_account_data.account_nickname,
                    bank_name=sample_bank_account_data.bank_name,
                    bank_address=sample_bank_account_data.bank_address,
                    bank_country=sample_bank_account_data.bank_country,
                    account_number_last_four="7890",
                    account_type=sample_bank_account_data.account_type,
                    currency=sample_bank_account_data.currency,
                    routing_number=sample_bank_account_data.routing_number,
                    swift_code=sample_bank_account_data.swift_code,
                    iban=sample_bank_account_data.iban,
                    status=BankAccountStatus.PENDING,
                    is_primary=sample_bank_account_data.is_primary,
                    is_active=True,
                    accepts_deposits=sample_bank_account_data.accepts_deposits,
                    verified_at=None,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    notes=sample_bank_account_data.notes
                )
                mock_create.return_value = mock_response

                response = client.post(
                    "/api/v1/billing/bank-accounts",
                    json=sample_bank_account_data.dict(),
                    headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert data["account_name"] == "Test Company LLC"
                assert data["account_number_last_four"] == "7890"
                assert data["status"] == "pending"
                assert data["is_primary"] is True

    @pytest.mark.asyncio
    async def test_account_number_encryption(self, sample_bank_account_data):
        """Test that account numbers are properly encrypted"""
        from dotmac.platform.billing.bank_accounts.service import BankAccountService

        service = BankAccountService(MagicMock())
        encrypted = service._encrypt_account_number("1234567890")

        # Should not be plain text
        assert encrypted != "1234567890"
        assert "$" in encrypted  # Our encryption format includes a separator

    @pytest.mark.asyncio
    async def test_list_bank_accounts(self, auth_headers, mock_current_user):
        """Test listing all bank accounts for a tenant"""
        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
            with patch('dotmac.platform.billing.bank_accounts.service.BankAccountService.get_bank_accounts') as mock_get:
                mock_accounts = [
                    CompanyBankAccountResponse(
                        id=1,
                        tenant_id="test-tenant",
                        account_name="Account 1",
                        bank_name="Bank 1",
                        bank_country="US",
                        account_number_last_four="1234",
                        account_type=AccountType.BUSINESS,
                        currency="USD",
                        status=BankAccountStatus.VERIFIED,
                        is_primary=True,
                        is_active=True,
                        accepts_deposits=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    ),
                    CompanyBankAccountResponse(
                        id=2,
                        tenant_id="test-tenant",
                        account_name="Account 2",
                        bank_name="Bank 2",
                        bank_country="US",
                        account_number_last_four="5678",
                        account_type=AccountType.CHECKING,
                        currency="USD",
                        status=BankAccountStatus.PENDING,
                        is_primary=False,
                        is_active=True,
                        accepts_deposits=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                ]
                mock_get.return_value = mock_accounts

                response = client.get(
                    "/api/v1/billing/bank-accounts",
                    headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert len(data) == 2
                assert data[0]["is_primary"] is True
                assert data[1]["is_primary"] is False

    @pytest.mark.asyncio
    async def test_update_bank_account(self, auth_headers, mock_current_user):
        """Test updating a bank account"""
        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
            with patch('dotmac.platform.billing.bank_accounts.service.BankAccountService.update_bank_account') as mock_update:
                update_data = CompanyBankAccountUpdate(
                    account_nickname="Updated Nickname",
                    is_primary=True,
                    notes="Updated notes"
                )

                mock_response = CompanyBankAccountResponse(
                    id=1,
                    tenant_id="test-tenant",
                    account_name="Test Account",
                    account_nickname="Updated Nickname",
                    bank_name="Test Bank",
                    bank_country="US",
                    account_number_last_four="1234",
                    account_type=AccountType.BUSINESS,
                    currency="USD",
                    status=BankAccountStatus.VERIFIED,
                    is_primary=True,
                    is_active=True,
                    accepts_deposits=True,
                    notes="Updated notes",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                mock_update.return_value = mock_response

                response = client.put(
                    "/api/v1/billing/bank-accounts/1",
                    json=update_data.dict(),
                    headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert data["account_nickname"] == "Updated Nickname"
                assert data["is_primary"] is True

    @pytest.mark.asyncio
    async def test_verify_bank_account(self, auth_headers, mock_current_user):
        """Test verifying a bank account"""
        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
            with patch('dotmac.platform.billing.bank_accounts.service.BankAccountService.verify_bank_account') as mock_verify:
                mock_response = CompanyBankAccountResponse(
                    id=1,
                    tenant_id="test-tenant",
                    account_name="Test Account",
                    bank_name="Test Bank",
                    bank_country="US",
                    account_number_last_four="1234",
                    account_type=AccountType.BUSINESS,
                    currency="USD",
                    status=BankAccountStatus.VERIFIED,
                    is_primary=True,
                    is_active=True,
                    accepts_deposits=True,
                    verified_at=datetime.utcnow(),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                mock_verify.return_value = mock_response

                response = client.post(
                    "/api/v1/billing/bank-accounts/1/verify",
                    json={"notes": "Verified via test deposits"},
                    headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "verified"
                assert data["verified_at"] is not None

    @pytest.mark.asyncio
    async def test_deactivate_bank_account(self, auth_headers, mock_current_user):
        """Test deactivating a bank account"""
        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
            with patch('dotmac.platform.billing.bank_accounts.service.BankAccountService.deactivate_bank_account') as mock_deactivate:
                mock_response = CompanyBankAccountResponse(
                    id=1,
                    tenant_id="test-tenant",
                    account_name="Test Account",
                    bank_name="Test Bank",
                    bank_country="US",
                    account_number_last_four="1234",
                    account_type=AccountType.BUSINESS,
                    currency="USD",
                    status=BankAccountStatus.VERIFIED,
                    is_primary=False,
                    is_active=False,  # Now inactive
                    accepts_deposits=False,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                mock_deactivate.return_value = mock_response

                response = client.delete(
                    "/api/v1/billing/bank-accounts/1",
                    headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_cannot_deactivate_primary_account(self):
        """Test that primary accounts cannot be deactivated"""
        from dotmac.platform.billing.bank_accounts.service import BankAccountService
        from dotmac.platform.billing.core.exceptions import BillingError

        mock_db = MagicMock()
        mock_account = MagicMock()
        mock_account.is_primary = True

        # Mock the database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_account
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = BankAccountService(mock_db)

        with pytest.raises(BillingError, match="Cannot deactivate primary bank account"):
            await service.deactivate_bank_account("test-tenant", 1, "user123")

    @pytest.mark.asyncio
    async def test_get_bank_account_summary(self, auth_headers, mock_current_user):
        """Test getting bank account with summary statistics"""
        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
            with patch('dotmac.platform.billing.bank_accounts.service.BankAccountService.get_bank_account_summary') as mock_summary:
                from dotmac.platform.billing.bank_accounts.models import BankAccountSummary

                mock_response = BankAccountSummary(
                    account=CompanyBankAccountResponse(
                        id=1,
                        tenant_id="test-tenant",
                        account_name="Test Account",
                        bank_name="Test Bank",
                        bank_country="US",
                        account_number_last_four="1234",
                        account_type=AccountType.BUSINESS,
                        currency="USD",
                        status=BankAccountStatus.VERIFIED,
                        is_primary=True,
                        is_active=True,
                        accepts_deposits=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    ),
                    total_deposits_mtd=15000.00,
                    total_deposits_ytd=125000.00,
                    pending_payments=5,
                    last_reconciliation=datetime.utcnow() - timedelta(days=3)
                )
                mock_summary.return_value = mock_response

                response = client.get(
                    "/api/v1/billing/bank-accounts/1/summary",
                    headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert data["total_deposits_mtd"] == 15000.00
                assert data["total_deposits_ytd"] == 125000.00
                assert data["pending_payments"] == 5


class TestBankAccountValidation:
    """Test validation rules for bank accounts"""

    def test_invalid_account_number(self):
        """Test validation of invalid account numbers"""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CompanyBankAccountCreate(
                account_name="Test",
                bank_name="Test Bank",
                bank_country="US",
                account_number="ABC123",  # Should be numeric
                account_type=AccountType.BUSINESS,
                currency="USD"
            )

    def test_invalid_country_code(self):
        """Test validation of country codes"""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CompanyBankAccountCreate(
                account_name="Test",
                bank_name="Test Bank",
                bank_country="USA",  # Should be 2-letter code
                account_number="1234567890",
                account_type=AccountType.BUSINESS,
                currency="USD"
            )

    def test_invalid_currency_code(self):
        """Test validation of currency codes"""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CompanyBankAccountCreate(
                account_name="Test",
                bank_name="Test Bank",
                bank_country="US",
                account_number="1234567890",
                account_type=AccountType.BUSINESS,
                currency="DOLLAR"  # Should be 3-letter code
            )

    def test_swift_code_length(self):
        """Test SWIFT code validation"""
        account = CompanyBankAccountCreate(
            account_name="Test",
            bank_name="Test Bank",
            bank_country="US",
            account_number="1234567890",
            account_type=AccountType.BUSINESS,
            currency="USD",
            swift_code="CHASUS33XXX"  # Valid 11-char SWIFT
        )
        assert len(account.swift_code) == 11

    def test_iban_format(self):
        """Test IBAN format validation"""
        account = CompanyBankAccountCreate(
            account_name="Test",
            bank_name="Test Bank",
            bank_country="GB",
            account_number="1234567890",
            account_type=AccountType.BUSINESS,
            currency="GBP",
            iban="GB82WEST12345698765432"  # Valid GB IBAN format
        )
        assert account.iban.startswith("GB")


class TestBankAccountSecurity:
    """Test security aspects of bank account management"""

    @pytest.mark.asyncio
    async def test_tenant_isolation(self, auth_headers):
        """Test that users can only access their tenant's bank accounts"""
        user1 = {"user_id": "user1", "tenant_id": "tenant1"}
        user2 = {"user_id": "user2", "tenant_id": "tenant2"}

        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=user1):
            with patch('dotmac.platform.billing.bank_accounts.service.BankAccountService.get_bank_accounts') as mock_get:
                mock_get.return_value = []

                response = client.get("/api/v1/billing/bank-accounts", headers=auth_headers)

                # Verify the service was called with correct tenant_id
                mock_get.assert_called_once()
                call_args = mock_get.call_args
                assert call_args[0][0] == "tenant1"  # First positional arg should be tenant_id

    @pytest.mark.asyncio
    async def test_account_number_not_exposed_in_logs(self, caplog):
        """Test that full account numbers are never logged"""
        import logging
        from dotmac.platform.billing.bank_accounts.service import BankAccountService

        caplog.set_level(logging.DEBUG)

        service = BankAccountService(MagicMock())

        # Create account with sensitive data
        account_data = CompanyBankAccountCreate(
            account_name="Test",
            bank_name="Test Bank",
            bank_country="US",
            account_number="1234567890",
            account_type=AccountType.BUSINESS,
            currency="USD"
        )

        # The service should never log the full account number
        encrypted = service._encrypt_account_number(account_data.account_number)

        # Check logs don't contain the full account number
        assert "1234567890" not in caplog.text

    @pytest.mark.asyncio
    async def test_authorization_required(self):
        """Test that all endpoints require authentication"""
        # Test without auth headers
        endpoints = [
            ("GET", "/api/v1/billing/bank-accounts"),
            ("POST", "/api/v1/billing/bank-accounts"),
            ("GET", "/api/v1/billing/bank-accounts/1"),
            ("PUT", "/api/v1/billing/bank-accounts/1"),
            ("POST", "/api/v1/billing/bank-accounts/1/verify"),
            ("DELETE", "/api/v1/billing/bank-accounts/1"),
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
            elif method == "PUT":
                response = client.put(endpoint, json={})
            elif method == "DELETE":
                response = client.delete(endpoint)

            # Should return 401 or 403 without auth
            assert response.status_code in [401, 403], f"Endpoint {endpoint} not protected"


class TestPrimaryAccountLogic:
    """Test primary account designation logic"""

    @pytest.mark.asyncio
    async def test_only_one_primary_account(self):
        """Test that only one account can be primary at a time"""
        from dotmac.platform.billing.bank_accounts.service import BankAccountService

        mock_db = MagicMock()
        mock_accounts = [
            MagicMock(id=1, is_primary=True),
            MagicMock(id=2, is_primary=True),  # Both marked as primary
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_accounts
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = BankAccountService(mock_db)

        # When setting a new primary, others should be unset
        await service._unset_primary_accounts("test-tenant", exclude_id=3)

        # Verify both existing primary accounts were unset
        assert mock_accounts[0].is_primary is False
        assert mock_accounts[1].is_primary is False

    @pytest.mark.asyncio
    async def test_set_primary_during_creation(self, sample_bank_account_data):
        """Test setting account as primary during creation"""
        from dotmac.platform.billing.bank_accounts.service import BankAccountService

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))))

        service = BankAccountService(mock_db)

        sample_bank_account_data.is_primary = True

        result = await service.create_bank_account(
            "test-tenant",
            sample_bank_account_data,
            "user123"
        )

        # Verify the account was added to the session
        mock_db.add.assert_called_once()
        added_account = mock_db.add.call_args[0][0]
        assert added_account.is_primary is True
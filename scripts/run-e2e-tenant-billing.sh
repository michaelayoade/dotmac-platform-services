#!/usr/bin/env bash
set -euo pipefail

# E2E Test Runner for Tenant Billing Portal
# This script:
# 1. Seeds E2E billing fixtures into the test database
# 2. Starts the backend server
# 3. Starts the frontend dev server
# 4. Runs Playwright E2E tests
# 5. Cleans up processes on exit

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# PID tracking for cleanup
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo -e "\n${YELLOW}Cleaning up processes...${NC}"
    if [ -n "$BACKEND_PID" ]; then
        echo "Stopping backend (PID: $BACKEND_PID)"
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ]; then
        echo "Stopping frontend (PID: $FRONTEND_PID)"
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
}

trap cleanup EXIT INT TERM

echo -e "${GREEN}=== E2E Tenant Billing Portal Test Runner ===${NC}\n"

# Step 1: Check infrastructure
echo -e "${YELLOW}[1/6] Checking infrastructure...${NC}"
if ! docker ps --format "{{.Names}}" | grep -q "dotmac-postgres"; then
    echo -e "${RED}Error: PostgreSQL container not running${NC}"
    echo "Run: make infra-up"
    exit 1
fi
echo -e "${GREEN}✓ Infrastructure running${NC}\n"

# Step 2: Seed test fixtures
echo -e "${YELLOW}[2/6] Seeding E2E billing fixtures...${NC}"
cd "$PROJECT_ROOT"

# Create a test script to seed fixtures
cat > /tmp/seed_e2e_fixtures.py << 'EOF'
"""Seed E2E billing fixtures into test database."""
import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from dotmac.platform.billing.core.entities import (
    InvoiceEntity,
    PaymentEntity,
    PaymentInvoiceEntity,
)
from dotmac.platform.billing.core.enums import InvoiceStatus, PaymentMethodType, PaymentStatus
from dotmac.platform.tenant.models import Base, BillingCycle, Tenant, TenantPlanType, TenantStatus
from dotmac.platform.user_management.models import User


async def seed_fixtures():
    """Seed E2E test fixtures."""
    # Use test database
    DATABASE_URL = "postgresql+asyncpg://dotmac_user:change-me-in-production@localhost:5432/dotmac_test"
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        tenant_id = "e2e-tenant-portal"
        customer_id = "e2e-customer-portal"

        # Clean up existing data for idempotent runs
        await session.execute(
            delete(PaymentInvoiceEntity).where(
                PaymentInvoiceEntity.payment_id.in_(
                    select(PaymentEntity.payment_id).where(PaymentEntity.tenant_id == tenant_id)
                )
            )
        )
        await session.execute(delete(PaymentEntity).where(PaymentEntity.tenant_id == tenant_id))
        await session.execute(delete(InvoiceEntity).where(InvoiceEntity.tenant_id == tenant_id))
        await session.execute(delete(Tenant).where(Tenant.id == tenant_id))
        await session.commit()

        # Create tenant
        tenant = Tenant(
            id=tenant_id,
            name="E2E Test Corporation",
            slug="e2e-test-corp",
            email="billing@e2e-test.com",
            status=TenantStatus.ACTIVE,
            plan_type=TenantPlanType.PROFESSIONAL,
            billing_cycle=BillingCycle.MONTHLY,
            billing_email="billing@e2e-test.com",
            max_users=25,
            max_api_calls_per_month=500000,
            max_storage_gb=100,
            current_users=15,
            current_api_calls=125000,
            current_storage_gb=45.5,
            created_at=datetime.now(UTC) - timedelta(days=365),
        )
        session.add(tenant)

        # Create 10 invoices with variety
        invoices = []

        # 2 overdue invoices
        for i in range(2):
            invoice = InvoiceEntity(
                invoice_id=str(uuid4()),
                tenant_id=tenant_id,
                invoice_number=f"INV-2025-{1001 + i}",
                customer_id=customer_id,
                billing_email="billing@e2e-test.com",
                billing_address={
                    "name": "E2E Test Corporation",
                    "street": "123 Test Street",
                    "city": "San Francisco",
                    "state": "CA",
                    "zip": "94105",
                    "country": "US",
                },
                issue_date=datetime.now(UTC) - timedelta(days=45 + i * 10),
                due_date=datetime.now(UTC) - timedelta(days=15 + i * 5),
                currency="USD",
                subtotal=299900,
                tax_amount=24999,
                discount_amount=0,
                total_amount=324899,
                remaining_balance=324899,
                total_credits_applied=0,
                credit_applications=[],
                status=InvoiceStatus.OPEN,
                payment_status=PaymentStatus.FAILED,
                created_at=datetime.now(UTC) - timedelta(days=46 + i * 10),
            )
            invoices.append(invoice)
            session.add(invoice)

        # 3 open invoices due soon
        for i in range(3):
            invoice = InvoiceEntity(
                invoice_id=str(uuid4()),
                tenant_id=tenant_id,
                invoice_number=f"INV-2025-{1003 + i}",
                customer_id=customer_id,
                billing_email="billing@e2e-test.com",
                billing_address={
                    "name": "E2E Test Corporation",
                    "street": "123 Test Street",
                    "city": "San Francisco",
                    "state": "CA",
                    "zip": "94105",
                    "country": "US",
                },
                issue_date=datetime.now(UTC) - timedelta(days=5 + i * 2),
                due_date=datetime.now(UTC) + timedelta(days=15 + i * 5),
                currency="USD",
                subtotal=299900,
                tax_amount=24999,
                discount_amount=0,
                total_amount=324899,
                remaining_balance=324899,
                total_credits_applied=0,
                credit_applications=[],
                status=InvoiceStatus.OPEN,
                payment_status=PaymentStatus.PENDING,
                created_at=datetime.now(UTC) - timedelta(days=6 + i * 2),
            )
            invoices.append(invoice)
            session.add(invoice)

        # 4 paid invoices
        for i in range(4):
            invoice = InvoiceEntity(
                invoice_id=str(uuid4()),
                tenant_id=tenant_id,
                invoice_number=f"INV-2025-{1006 + i}",
                customer_id=customer_id,
                billing_email="billing@e2e-test.com",
                billing_address={
                    "name": "E2E Test Corporation",
                    "street": "123 Test Street",
                    "city": "San Francisco",
                    "state": "CA",
                    "zip": "94105",
                    "country": "US",
                },
                issue_date=datetime.now(UTC) - timedelta(days=60 + i * 30),
                due_date=datetime.now(UTC) - timedelta(days=30 + i * 30),
                currency="USD",
                subtotal=299900,
                tax_amount=24999,
                discount_amount=0,
                total_amount=324899,
                remaining_balance=0,
                total_credits_applied=0,
                credit_applications=[],
                status=InvoiceStatus.PAID,
                payment_status=PaymentStatus.SUCCEEDED,
                paid_at=datetime.now(UTC) - timedelta(days=35 + i * 30),
                created_at=datetime.now(UTC) - timedelta(days=61 + i * 30),
            )
            invoices.append(invoice)
            session.add(invoice)

        # 1 draft invoice
        draft_invoice = InvoiceEntity(
            invoice_id=str(uuid4()),
            tenant_id=tenant_id,
            invoice_number="INV-2025-1010",
            customer_id=customer_id,
            billing_email="billing@e2e-test.com",
            billing_address={
                "name": "E2E Test Corporation",
                "street": "123 Test Street",
                "city": "San Francisco",
                "state": "CA",
                "zip": "94105",
                "country": "US",
            },
            issue_date=datetime.now(UTC),
            due_date=datetime.now(UTC) + timedelta(days=30),
            currency="USD",
            subtotal=299900,
            tax_amount=24999,
            discount_amount=0,
            total_amount=324899,
            remaining_balance=324899,
            total_credits_applied=0,
            credit_applications=[],
            status=InvoiceStatus.DRAFT,
            payment_status=PaymentStatus.PENDING,
            created_at=datetime.now(UTC),
        )
        invoices.append(draft_invoice)
        session.add(draft_invoice)

        # Create 15 payments
        payments = []

        # 4 successful payments for paid invoices
        paid_invoices = [inv for inv in invoices if inv.status == InvoiceStatus.PAID]
        for i, invoice in enumerate(paid_invoices):
            payment = PaymentEntity(
                payment_id=str(uuid4()),
                tenant_id=tenant_id,
                customer_id=customer_id,
                amount=324899,
                currency="USD",
                status=PaymentStatus.SUCCEEDED,
                payment_method_type=PaymentMethodType.CARD,
                payment_method_details={
                    "last_four": "4242",
                    "brand": "visa",
                    "exp_month": 12,
                    "exp_year": 2026,
                },
                provider="stripe",
                provider_payment_id=f"pi_test_success_{uuid4().hex[:8]}",
                provider_fee=972,
                created_at=datetime.now(UTC) - timedelta(days=35 + i * 30),
            )
            payments.append(payment)
            session.add(payment)
            session.add(
                PaymentInvoiceEntity(
                    payment_id=payment.payment_id,
                    invoice_id=invoice.invoice_id,
                    amount_applied=payment.amount,
                )
            )

        # 4 failed payments
        for i in range(4):
            target_invoice = invoices[0] if i < 2 else invoices[1]
            payment = PaymentEntity(
                payment_id=str(uuid4()),
                tenant_id=tenant_id,
                customer_id=customer_id,
                amount=324899,
                currency="USD",
                status=PaymentStatus.FAILED,
                payment_method_type=PaymentMethodType.CARD,
                payment_method_details={
                    "last_four": "0002",
                    "brand": "visa",
                    "exp_month": 12,
                    "exp_year": 2026,
                },
                provider="stripe",
                provider_payment_id=None,
                provider_fee=0,
                failure_reason="Your card was declined. Please use a different payment method.",
                retry_count=i + 1,
                created_at=datetime.now(UTC) - timedelta(days=10 + i * 3),
            )
            payments.append(payment)
            session.add(payment)
            session.add(
                PaymentInvoiceEntity(
                    payment_id=payment.payment_id,
                    invoice_id=target_invoice.invoice_id,
                    amount_applied=payment.amount,
                )
            )

        # 3 pending/processing payments
        for i in range(3):
            status = PaymentStatus.PENDING if i % 2 == 0 else PaymentStatus.PROCESSING
            target_invoice = invoices[2 + i]
            payment = PaymentEntity(
                payment_id=str(uuid4()),
                tenant_id=tenant_id,
                customer_id=customer_id,
                amount=324899,
                currency="USD",
                status=status,
                payment_method_type=PaymentMethodType.BANK_ACCOUNT,
                payment_method_details={
                    "account_last_four": "6789",
                    "bank_name": "Test Bank",
                },
                provider="stripe",
                provider_payment_id=f"pi_test_{status.value.lower()}_{uuid4().hex[:8]}",
                provider_fee=0,
                retry_count=0,
                created_at=datetime.now(UTC) - timedelta(days=2 + i),
            )
            payments.append(payment)
            session.add(payment)
            session.add(
                PaymentInvoiceEntity(
                    payment_id=payment.payment_id,
                    invoice_id=target_invoice.invoice_id,
                    amount_applied=payment.amount,
                )
            )

        # 4 recent successful payments
        for i in range(4):
            payment = PaymentEntity(
                payment_id=str(uuid4()),
                tenant_id=tenant_id,
                customer_id=customer_id,
                amount=99900,
                currency="USD",
                status=PaymentStatus.SUCCEEDED,
                payment_method_type=PaymentMethodType.CARD,
                payment_method_details={
                    "last_four": "4242",
                    "brand": "visa",
                    "exp_month": 12,
                    "exp_year": 2026,
                },
                provider="stripe",
                provider_payment_id=f"pi_test_addon_{uuid4().hex[:8]}",
                provider_fee=320,
                retry_count=0,
                created_at=datetime.now(UTC) - timedelta(days=i * 7),
            )
            payments.append(payment)
            session.add(payment)

        # Create E2E tenant user (scoped to e2e-tenant-portal)
        e2e_user_email = "e2e-tenant-user@test.com"
        e2e_password_hash = "$2b$12$M2xgcCnzJ6NgFkH49z43N.vexiW.LhPo9CYGDHalblOFSzN0KmAi6"  # bcrypt hash for admin123

        result = await session.execute(select(User).where(User.email == e2e_user_email))
        e2e_user = result.scalar_one_or_none()

        if e2e_user is None:
            e2e_user = User(
                id=uuid4(),
                username="e2e-tenant-user",
                email=e2e_user_email,
                password_hash=e2e_password_hash,
                full_name="E2E Tenant User",
                tenant_id=tenant_id,  # Important: assign to test tenant
                is_active=True,
                is_verified=True,
                is_superuser=False,
                is_platform_admin=False,
                roles=["admin"],
                permissions=["billing:read", "billing:write"],
            )
            session.add(e2e_user)
            print(f"✓ Created E2E tenant user: {e2e_user_email}")
        else:
            e2e_user.password_hash = e2e_password_hash
            e2e_user.tenant_id = tenant_id
            e2e_user.is_active = True
            e2e_user.is_verified = True
            e2e_user.roles = ["admin"]
            e2e_user.permissions = ["billing:read", "billing:write"]
            print(f"✓ Updated E2E tenant user: {e2e_user_email}")

        await session.commit()

        print(f"✓ Seeded tenant: {tenant_id}")
        print(f"✓ Created {len(invoices)} invoices")
        print(f"✓ Created {len(payments)} payments")
        print("\nInvoice breakdown:")
        print(f"  - {len([i for i in invoices if i.status == InvoiceStatus.OPEN and i.due_date < datetime.now(UTC)])} overdue")
        print(f"  - {len([i for i in invoices if i.status == InvoiceStatus.OPEN])} open")
        print(f"  - {len([i for i in invoices if i.status == InvoiceStatus.PAID])} paid")
        print(f"  - {len([i for i in invoices if i.status == InvoiceStatus.DRAFT])} draft")
        print("\nPayment breakdown:")
        print(f"  - {len([p for p in payments if p.status == PaymentStatus.SUCCEEDED])} successful")
        print(f"  - {len([p for p in payments if p.status == PaymentStatus.FAILED])} failed")
        print(f"  - {len([p for p in payments if p.status in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]])} pending/processing")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_fixtures())
EOF

# Run the seeding script
PYTHONPATH="$PROJECT_ROOT/src" .venv/bin/python /tmp/seed_e2e_fixtures.py
echo -e "${GREEN}✓ Fixtures seeded${NC}\n"

# Step 3: Start backend
echo -e "${YELLOW}[3/6] Starting backend server...${NC}"
cd "$PROJECT_ROOT"
export DATABASE_URL="postgresql+asyncpg://dotmac_user:change-me-in-production@localhost:5432/dotmac_test"
export DOTMAC_DATABASE_URL_ASYNC="$DATABASE_URL"

# Ensure backend port is available
if lsof -ti :8000 >/dev/null 2>&1; then
    echo "Port 8000 is in use, attempting to free it..."
    lsof -ti :8000 | xargs kill -15 2>/dev/null || true
    sleep 1
fi

.venv/bin/uvicorn dotmac.platform.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend-e2e.log 2>&1 &
BACKEND_PID=$!

echo "Backend started (PID: $BACKEND_PID)"
echo "Waiting for backend to be ready..."

# Wait for backend health check
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend ready${NC}\n"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "${RED}Error: Backend failed to start${NC}"
        echo "Check logs: tail -f /tmp/backend-e2e.log"
        exit 1
    fi
done

# Step 4: Start frontend
echo -e "${YELLOW}[4/6] Starting frontend dev server...${NC}"
cd "$PROJECT_ROOT/frontend/apps/base-app"

# Ensure default Playwright port is free
if lsof -ti :3000 >/dev/null 2>&1; then
    echo "Port 3000 is in use, attempting to free it..."
    lsof -ti :3000 | xargs kill -15 2>/dev/null || true
    sleep 1
fi

# Explicitly set frontend port to 3000 to avoid conflict with backend
PORT=3000 pnpm dev > /tmp/frontend-e2e.log 2>&1 &
FRONTEND_PID=$!

echo "Frontend started (PID: $FRONTEND_PID)"
echo "Waiting for frontend to be ready..."

# Wait for frontend
for i in {1..60}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend ready${NC}\n"
        break
    fi
    sleep 1
    if [ $i -eq 60 ]; then
        echo -e "${RED}Error: Frontend failed to start${NC}"
        echo "Check logs: tail -f /tmp/frontend-e2e.log"
        exit 1
    fi
done

# Step 5: Install Playwright if needed
echo -e "${YELLOW}[5/6] Ensuring Playwright browsers installed...${NC}"
cd "$PROJECT_ROOT/frontend/apps/base-app"
if ! pnpm exec playwright --version > /dev/null 2>&1; then
    echo "Installing Playwright browsers..."
    pnpm exec playwright install
fi
echo -e "${GREEN}✓ Playwright ready${NC}\n"

# Step 6: Run E2E tests
echo -e "${YELLOW}[6/6] Running E2E tests...${NC}"
cd "$PROJECT_ROOT/frontend/apps/base-app"

echo -e "\n${GREEN}=== Running tenant-portal.spec.ts ===${NC}\n"
# Run Playwright tests and capture exit code
pnpm exec playwright test e2e/tenant-portal.spec.ts --reporter=line
TEST_EXIT_CODE=$?

echo -e "\n${GREEN}=== Test Results ===${NC}"
echo "Exit code: $TEST_EXIT_CODE"

# Check if any tests actually failed (exit code 1 means test failures)
# Exit code 0 means all tests passed (skipped tests don't cause failures)
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All E2E tests passed!${NC}\n"
    echo "View HTML report: cd frontend/apps/base-app && pnpm exec playwright show-report"
    exit 0
else
    echo -e "${RED}✗ E2E tests failed${NC}\n"
    echo "View HTML report: cd frontend/apps/base-app && pnpm exec playwright show-report"
    exit 1
fi

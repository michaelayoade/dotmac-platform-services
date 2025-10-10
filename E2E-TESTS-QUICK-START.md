# E2E Tests - Quick Start 🚀

## Run All E2E Tests (One Command)

```bash
./scripts/run-e2e-tenant-billing.sh
```

This automatically:
- ✅ Checks infrastructure
- ✅ Seeds test data (10 invoices, 15 payments)
- ✅ Starts backend & frontend
- ✅ Runs 23 Playwright tests
- ✅ Cleans up on exit

---

## Test Credentials

**Username**: `superadmin`
**Password**: `admin123`

---

## Run Specific Tests

```bash
cd frontend/apps/base-app

# One test suite
pnpm exec playwright test tenant-portal.spec.ts -g "Layout & Navigation"

# One specific test
pnpm exec playwright test tenant-portal.spec.ts -g "shows main page structure"

# Debug mode (interactive)
pnpm exec playwright test tenant-portal.spec.ts --ui

# Headed mode (see browser)
pnpm exec playwright test tenant-portal.spec.ts --headed
```

---

## Manual Setup

```bash
# 1. Start infrastructure
make infra-up

# 2. Start backend
export DATABASE_URL="postgresql+asyncpg://dotmac_user:change-me-in-production@localhost:5432/dotmac_test"
.venv/bin/uvicorn dotmac.platform.main:app --port 8000 --reload &

# 3. Start frontend
cd frontend/apps/base-app && pnpm dev &

# 4. Run tests
pnpm test:e2e tenant-portal.spec.ts
```

---

## What Gets Tested (23 Tests)

### ✅ Layout & Navigation (3)
- Page structure, summary cards, action buttons

### ✅ Metrics & Data (6)
- Plan display, spend amounts, invoice counts, overdue detection

### ✅ Invoice List (7)
- Table rendering, search/filter, currency formatting, status badges, selection

### ✅ Payment Table (7)
- Amount formatting (cents→dollars), status badges, references, methods, dates

---

## Test Data Created

- **Tenant**: E2E Test Corporation (Professional plan)
- **Invoices**: 10 (2 overdue, 3 due soon, 4 paid, 1 draft)
- **Payments**: 15 (8 successful, 4 failed, 3 pending)
- **Amounts**: Realistic ($3,248.99 invoices, $999 add-ons)

---

## Troubleshooting

**Tests timeout?**
- Increase timeout in playwright.config.ts
- Use only Desktop Chrome (comment out mobile browsers)

**Login fails?**
- Verify superadmin password: `docker exec dotmac-postgres psql -U dotmac_user -d dotmac_test -c "SELECT username FROM users WHERE username='superadmin';"`
- Re-run password update script from docs/e2e-test-setup-complete.md

**Infrastructure not running?**
```bash
make infra-status
make infra-up
```

---

## Documentation

- **Complete Guide**: `docs/e2e-testing-guide.md`
- **Setup Details**: `docs/e2e-test-setup-complete.md`
- **Partner Portal Plan**: `docs/partner-portal-revenue-share-plan.md`

---

**Quick command**: `./scripts/run-e2e-tenant-billing.sh` ⚡

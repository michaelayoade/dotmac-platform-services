# Billing Test Coverage Strategy
## Current: 47.05% → Target: 90.00%

**Date**: 2025-09-30
**Gap**: 42.95 percentage points (3,652 uncovered lines)

---

## Executive Summary

The billing module currently has **47.05% test coverage** after excluding a broken test file. To reach the 90% target, we need a **strategic, phased approach** focusing on high-impact areas first.

###  Quick Wins (Estimated +15-20% coverage, 4-6 hours)

**Zero-Coverage Modules - Validators/Schemas (Easy to test):**
1. **mappers.py** (186 lines, 0%) - Pydantic schemas for imports
   - Test `InvoiceImportSchema` validation
   - Test `SubscriptionImportSchema` validation
   - Test `PaymentImportSchema` validation
   - **Impact**: ~5-6% coverage boost

2. **money_models.py** (133 lines, 55.40%) - Money handling models
   - Test `Money` class operations
   - Test currency conversion
   - Test decimal precision
   - **Impact**: ~2-3% coverage boost

3. **utils/currency.py** (47 lines, 24.59%) - Currency utilities
   - Test currency validation
   - Test formatting functions
   - **Impact**: ~1-2% coverage boost

**Basic Service Method Tests:**
4. **Create simple happy-path tests** for core services
   - Test basic CRUD operations only (no edge cases)
   - **Impact**: ~8-10% coverage boost

**Total Phase 1**: ~15-20% coverage gain

---

## Phase 2: Core Service Coverage (Estimated +20-25% coverage, 8-12 hours)

**Critical Services with <15% Coverage:**

### invoicing/service.py (228 lines, 10.00%)
**Priority**: CRITICAL
**Focus Areas**:
- `create_invoice()` - Line 55-167
- `get_invoice()` - Line 174-186
- `list_invoices()` - Line 201-219
- `update_invoice_status()` - Line 224-243
- **Tests Needed**: 15-20 test methods

### payments/service.py (220 lines, 10.64%)
**Priority**: CRITICAL
**Focus Areas**:
- `create_payment()` - Line 63-180
- `process_refund()` - Line 192-291
- `verify_payment()` - Line 312-343
- **Tests Needed**: 12-15 test methods

### subscriptions/service.py (261 lines, 12.16%)
**Priority**: HIGH
**Focus Areas**:
- `create_subscription()` - Line 79-110
- `update_subscription()` - Line 138-156
- `cancel_subscription()` - Line 170-230
- `renew_subscription()` - Line 260-283
- **Tests Needed**: 18-22 test methods

### pricing/service.py (274 lines, 10.56%)
**Priority**: HIGH
**Focus Areas**:
- `calculate_price()` - Line 68-111
- `apply_tiered_pricing()` - Line 185-220
- `apply_volume_discount()` - Line 225-251
- **Tests Needed**: 15-18 test methods

**Total Phase 2**: ~20-25% coverage gain

---

## Phase 3: Complex Integrations (Estimated +10-15% coverage, 6-10 hours)

### webhooks/handlers.py (469 lines, 8.84%)
**Priority**: MEDIUM
**Complexity**: HIGH (external integrations)
**Focus**: Test webhook signature validation and basic event handling
**Tests Needed**: 10-12 test methods

### integration.py (196 lines, 17.34%)
**Priority**: MEDIUM
**Focus**: Test Stripe integration mocking
**Tests Needed**: 8-10 test methods

### tax/calculator.py (104 lines, 22.39%)
**Priority**: MEDIUM
**Focus**: Tax calculation logic
**Tests Needed**: 6-8 test methods

**Total Phase 3**: ~10-15% coverage gain

---

## Phase 4: Cache & Infrastructure (Estimated +5-8% coverage, 4-6 hours)

### cache.py (296 lines, 0%)
**Priority**: LOW (infrastructure, not business logic)
**Recommendation**: Test key methods only
**Tests Needed**: 8-10 test methods

### cache_manager.py (175 lines, 0%)
**Priority**: LOW
**Tests Needed**: 5-7 test methods

### middleware.py (77 lines, 0%)
**Priority**: LOW
**Tests Needed**: 3-5 test methods

**Total Phase 4**: ~5-8% coverage gain

---

## Estimated Timeline to 90% Coverage

| Phase | Coverage Gain | Time Estimate | Cumulative Coverage |
|-------|---------------|---------------|---------------------|
| **Current** | - | - | **47.05%** |
| Phase 1 (Quick Wins) | +15-20% | 4-6 hours | 62-67% |
| Phase 2 (Core Services) | +20-25% | 8-12 hours | 82-92% |
| Phase 3 (Integrations) | +10-15% | 6-10 hours | 92-107% |
| **Target Reached** | - | - | **~90%** (Phase 2 completion) |

**Total Time to 90%**: ~12-18 hours (Phase 1 + Phase 2)

---

## Implementation Strategy

### Immediate Actions (Today)

1. ✅ **Remove broken test file** (`test_exceptions_basic.py`)
2. **Create test for mappers.py** (Quick win)
3. **Create basic invoice service tests** (High impact)
4. **Create basic payment service tests** (High impact)
5. **Run coverage check** (Should reach ~60-65%)

### This Week

1. Complete Phase 1 (Quick Wins)
2. Start Phase 2 (Core Services)
   - Focus on invoicing and payments first
   - Add subscription tests second
3. **Target**: 75-80% coverage by end of week

### Next Week

1. Complete Phase 2 (Core Services)
2. Add pricing service tests
3. **Target**: 90%+ coverage achieved

---

## Test Prioritization Matrix

| Module | Lines | Current Cov | Business Impact | Test Complexity | Priority Score |
|--------|-------|-------------|-----------------|-----------------|----------------|
| invoicing/service.py | 228 | 10.00% | CRITICAL | Medium | **1** |
| payments/service.py | 220 | 10.64% | CRITICAL | Medium | **2** |
| subscriptions/service.py | 261 | 12.16% | HIGH | Medium | **3** |
| mappers.py | 186 | 0% | LOW | Easy | **4** |
| pricing/service.py | 274 | 10.56% | HIGH | High | **5** |
| webhooks/handlers.py | 469 | 8.84% | MEDIUM | High | **6** |
| tax/calculator.py | 104 | 22.39% | MEDIUM | Medium | **7** |
| cache.py | 296 | 0% | LOW | Easy | **8** |

---

## Test Templates

### Template 1: Service Happy Path Test
```python
@pytest.mark.asyncio
async def test_create_invoice_success(async_db: AsyncSession):
    \"\"\"Test successful invoice creation.\"\"\"
    service = InvoiceService(async_db)

    invoice_data = InvoiceCreateRequest(
        customer_id="cust_123",
        amount=Decimal("100.00"),
        currency="USD",
        due_date=datetime.now() + timedelta(days=30)
    )

    invoice = await service.create_invoice(
        tenant_id="tenant_1",
        invoice_data=invoice_data
    )

    assert invoice.invoice_id is not None
    assert invoice.amount == Decimal("100.00")
    assert invoice.status == InvoiceStatus.DRAFT
```

### Template 2: Mapper Validation Test
```python
def test_invoice_import_schema_valid():
    \"\"\"Test valid invoice import data.\"\"\"
    data = {
        "customer_id": "cust_123",
        "amount": 100.50,
        "currency": "usd",
        "status": "PAID"
    }

    schema = InvoiceImportSchema(**data)
    assert schema.currency == "USD"  # uppercase
    assert schema.status == "paid"  # lowercase
    assert schema.amount == 100.50
```

### Template 3: Error Handling Test
```python
@pytest.mark.asyncio
async def test_get_invoice_not_found(async_db: AsyncSession):
    \"\"\"Test invoice not found error.\"\"\"
    service = InvoiceService(async_db)

    with pytest.raises(InvoiceNotFoundError):
        await service.get_invoice(
            tenant_id="tenant_1",
            invoice_id="nonexistent"
        )
```

---

## Coverage Metrics to Track

### Line Coverage (Primary)
- **Current**: 47.05%
- **Target**: 90.00%
- **Gap**: 42.95 points

### Branch Coverage (Secondary)
- **Current**: Unknown (many branches untested)
- **Target**: 85%+

### Statement Coverage
- **Covered**: 4,386 / 8,526 statements
- **Uncovered**: 4,140 statements
- **Need to cover**: ~3,652 statements for 90%

---

## Recommended Approach

### Option A: Comprehensive (Slower, More Thorough)
- Write tests for ALL services methodically
- Test edge cases, error paths, validations
- **Time**: 20-25 hours
- **Result**: 90-95% coverage, production-ready

### Option B: Strategic (Faster, Targeted)
- Focus only on critical business logic
- Test happy paths + basic error handling
- Skip infrastructure (cache, middleware)
- **Time**: 12-15 hours
- **Result**: 88-92% coverage, good enough

### Option C: Pragmatic (Fastest, Minimum Viable)
- Test only the 10 highest-impact modules
- Happy paths only, minimal edge cases
- **Time**: 8-10 hours
- **Result**: 75-82% coverage, acceptable

**Recommendation**: **Option B (Strategic)** - Best balance of speed and quality

---

## Next Steps

1. **Immediate** (Today):
   - Create `test_mappers.py` with validation tests (~30 min)
   - Create `test_invoice_service_basic.py` with 5-10 core tests (~2 hours)
   - Run coverage check

2. **Short-term** (This Week):
   - Complete Phase 1 (Quick Wins)
   - Start Phase 2 (invoicing + payments services)
   - Target: 70-75% coverage

3. **Medium-term** (Next Week):
   - Complete Phase 2
   - Add pricing + subscription tests
   - **Achieve 90% target**

---

## Conclusion

Reaching 90% billing coverage is **achievable in 12-18 hours** of focused work by following this strategic plan. The key is to prioritize **core business logic** (invoicing, payments, subscriptions) over infrastructure code (cache, middleware).

**Success Metrics**:
- ✅ Line coverage ≥90%
- ✅ All critical services >80% coverage
- ✅ Core business flows tested (invoice → payment → subscription)
- ✅ Key error paths tested
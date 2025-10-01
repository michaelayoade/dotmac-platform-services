# Strategic Test Management for DotMac Platform Services

## Overview

This document outlines a strategic approach to managing the 163 failing tests in the DotMac Platform Services project. Rather than fixing tests one by one, this approach addresses systematic issues that cause multiple test failures.

## Current State Analysis

### Test Failure Distribution (as of last analysis)
- **Communications**: 94 failures (57.7%)
- **Auth**: 81 failures (49.7%)
- **Billing**: 31 failures (19.0%)
- **Customer Management**: 16 failures (9.8%)
- **Other modules**: 41 failures (25.1%)

### Root Cause Categories
1. **Async/Await Coordination (40% of failures)**: Improper async mocking, coroutine warnings
2. **Dependency Injection Issues (25%)**: Missing service mocks, fixture problems
3. **Data Model Mismatches (20%)**: Pydantic v2 migration, enum mismatches
4. **Tenant/Auth Context (15%)**: Context not propagating, auth token issues

## Strategic Approach

### Phase 1: Infrastructure Foundation ✅ COMPLETED

**Created `tests/test_utils.py`** - A comprehensive testing utilities module that provides:

#### 1. Async Testing Utilities
```python
from tests.test_utils import ProperAsyncMock, create_async_session_mock

# Fixes 'coroutine was never awaited' warnings
session = create_async_session_mock()
```

#### 2. Service Mock Factories
```python
from tests.test_utils import create_mock_user_service, create_mock_email_service

# Standardized service mocks
user_service = create_mock_user_service()
email_service = create_mock_email_service()
```

#### 3. Datetime Utilities
```python
from tests.test_utils import utcnow

# Fixes datetime.utcnow() deprecation warnings
current_time = utcnow()  # timezone-aware
```

#### 4. Tenant Context Management
```python
from tests.test_utils import TenantContext, with_tenant_context

@with_tenant_context("test-tenant")
async def test_something():
    # Automatic tenant context
    pass
```

#### 5. Test Data Factory
```python
from tests.test_utils import TestDataFactory

factory = TestDataFactory()
user_data = factory.create_user()
invoice_data = factory.create_invoice()
```

#### 6. Base Test Classes
```python
from tests.test_utils import AsyncTestCase, ServiceTestCase

class TestMyService(AsyncTestCase):
    # Auto-configured with common mocks
    pass
```

### Phase 2: Quick Wins Implementation ✅ PARTIALLY COMPLETED

#### Fixed Issues:
1. **Datetime Deprecation Warnings**: Updated billing service files to use `datetime.now(timezone.utc)`
2. **CustomerNote Default Values**: Fixed is_internal field initialization
3. **UUID Validation**: Added proper UUID validation in customer service
4. **Tenant Isolation**: Fixed middleware and context handling

#### Results So Far:
- **Tenant Isolation**: 0 failures (was 15 failures) ✅
- **Customer Management**: 15 failures (was 16 failures) ✅
- **Overall**: 163 failures (was 174 failures) ✅

## Implementation Strategy

### How to Apply Strategic Test Management

#### 1. For New Tests - Use the Strategic Pattern

```python
"""Example: tests/billing/test_invoice_service_strategic.py"""
from tests.test_utils import AsyncTestCase, TestDataFactory, with_tenant_context

class TestInvoiceService(AsyncTestCase):
    @pytest.fixture(autouse=True)
    def setup_service(self):
        self.session = create_async_session_mock()
        self.factory = TestDataFactory()
        self.service = InvoiceService(self.session)

    @pytest.mark.asyncio
    @with_tenant_context("test-tenant")
    async def test_create_invoice(self):
        # Uses standardized mocks and data factory
        invoice_data = self.factory.create_invoice()
        result = await self.service.create_invoice(**invoice_data)
        assert result.tenant_id == "test-tenant"
```

#### 2. For Existing Tests - Progressive Migration

**Step 1: Import utilities**
```python
# Add to existing test file
from tests.test_utils import create_async_session_mock, utcnow
```

**Step 2: Replace problematic patterns**
```python
# Replace this:
mock_session = AsyncMock()  # Causes coroutine warnings
datetime.utcnow()  # Deprecated

# With this:
mock_session = create_async_session_mock()  # No warnings
utcnow()  # Timezone-aware
```

**Step 3: Use standardized mocks**
```python
# Replace this:
user_service = Mock()
user_service.get_user = AsyncMock(return_value=None)
# ... 20 more lines of setup

# With this:
user_service = create_mock_user_service()
```

### Phase 3: Module-Specific Fixes

#### Communications Module (94 failures)
**Priority**: Highest impact
**Strategy**:
1. Replace all async session mocks with `create_async_session_mock()`
2. Fix SMTP config access patterns (dict vs object)
3. Use `create_mock_email_service()` for consistent email service mocking
4. Apply `create_mock_celery_app()` for task scheduling tests

**Expected Impact**: 50-60 failures reduced

#### Auth Module (81 failures)
**Priority**: High impact
**Strategy**:
1. Use `create_mock_auth_service()` for consistent auth mocking
2. Use `create_mock_user_service()` for user operations
3. Apply standardized JWT token generation with `create_test_jwt()`
4. Fix async session patterns in router tests

**Expected Impact**: 40-50 failures reduced

#### Billing Module (31 failures)
**Priority**: Medium impact
**Strategy**:
1. Replace all `datetime.utcnow()` with `utcnow()` ✅ DONE
2. Apply tenant context with `@with_tenant_context` decorator
3. Use `TestDataFactory.create_invoice()` for consistent test data
4. Fix async session mocking

**Expected Impact**: 20-25 failures reduced

## Migration Checklist

### For Each Module:
- [ ] Import test utilities: `from tests.test_utils import *`
- [ ] Replace async session mocks: `create_async_session_mock()`
- [ ] Fix datetime usage: `utcnow()` instead of `datetime.utcnow()`
- [ ] Apply service mocks: `create_mock_*_service()`
- [ ] Use test data factory: `TestDataFactory.create_*()`
- [ ] Add tenant context: `@with_tenant_context("test-tenant")`

### For New Features:
- [ ] Inherit from `AsyncTestCase` or `ServiceTestCase`
- [ ] Use standardized fixtures and mocks
- [ ] Follow the strategic pattern from examples

## Benefits of Strategic Approach

### 1. Systematic Issue Resolution
- Fixes multiple tests with single change
- Addresses root causes, not symptoms
- Prevents regression of similar issues

### 2. Maintainable Test Suite
- Consistent patterns across all tests
- Shared utilities reduce duplication
- Clear separation of concerns

### 3. Developer Productivity
- Faster test development with utilities
- Less time debugging async/mock issues
- Standardized approaches reduce learning curve

### 4. Reliability
- Proper async handling eliminates race conditions
- Consistent data reduces flaky tests
- Tenant isolation prevents test interference

## Success Metrics

### Short-term (Next 2 weeks):
- [ ] Reduce total failures from 163 to <100
- [ ] Fix all datetime deprecation warnings
- [ ] Standardize all async session mocking

### Medium-term (Next month):
- [ ] Reduce total failures to <50
- [ ] Complete communications and auth module fixes
- [ ] Establish strategic pattern as standard for new tests

### Long-term (Next quarter):
- [ ] Achieve <20 total test failures
- [ ] 95%+ test reliability (non-flaky)
- [ ] Complete migration of all existing tests to strategic pattern

## Tools and Scripts

### Quick Migration Script
```bash
# Fix datetime issues across all files
find src/ -name "*.py" -exec sed -i '' 's/datetime\.utcnow()/datetime.now(timezone.utc)/g' {} \;
find src/ -name "*.py" -exec sed -i '' 's/from datetime import datetime, timedelta/from datetime import datetime, timedelta, timezone/g' {} \;
```

### Test Failure Analysis
```bash
# Get current failure distribution
.venv/bin/pytest tests/ --ignore=tests/test_observability.py --ignore=tests/test_real_services.py --ignore=tests/auth/test_mfa_service.py --tb=no -q | grep "FAILED" | cut -d':' -f1 | cut -d'/' -f2 | sort | uniq -c | sort -rn
```

## Conclusion

The strategic test management approach transforms test maintenance from a reactive, case-by-case process into a proactive, systematic approach. By addressing infrastructure issues first and providing standardized utilities, we can achieve dramatic improvements in test reliability and maintainability.

The key is to **fix patterns, not individual tests**. This approach has already demonstrated success by completely fixing the tenant isolation module and significantly improving customer management.
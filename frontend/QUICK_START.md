# Frontend Real API Integration - Quick Start Guide

**Last Updated**: 2025-09-30
**Current Status**: 8/13 pages connected (62%)

---

## 🎯 What You Need to Know in 60 Seconds

1. **Good News**: Most pages (8/13) are already using real APIs!
2. **3 Billing pages** need migration (but the hook is ready)
3. **Follow this guide** to complete the work in 6-9 hours

---

## 📋 Current State

### ✅ Already Connected (8 pages)
- Health, Feature Flags (Infrastructure)
- Roles, Permissions, Users, Secrets (Security)
- Customers (Operations)
- Analytics (overview)

### ❌ Still Mock Data (5 pages)
- **Plans** (hook ready → `useBillingPlans.ts`)
- **Payments** (need to create hook)
- **Subscriptions** (need to create hook)
- Logs (no backend API)
- Observability (no backend API)

---

## 🚀 Step-by-Step: Complete Billing Integration

### Step 1: Plans Page (2-3 hours)

**Files**:
- Hook: `hooks/useBillingPlans.ts` ✅ Already created
- Page: `app/dashboard/billing-revenue/plans/page.tsx` ❌ Still mock data
- Guide: `BILLING_INTEGRATION_GUIDE.md` 📖 Read this!

**What to do**:
```typescript
// 1. Import the hook at top of plans/page.tsx
import { useBillingPlans } from '@/hooks/useBillingPlans';

// 2. Replace useState + fetchPlans with:
const {
  plans: backendPlans,
  products,
  loading,
  error,
  createPlan,
  updatePlan,
  deletePlan
} = useBillingPlans();

// 3. Map backend data to display format
const plans = backendPlans.map(plan => ({
  id: plan.plan_id,
  name: plan.name,
  // ... see BILLING_INTEGRATION_GUIDE.md for full mapping
}));

// 4. Update handlers to use hook methods
const handleCreatePlan = async () => {
  await createPlan(newPlanData);
};

// 5. Test everything!
```

**Read**: `BILLING_INTEGRATION_GUIDE.md` for detailed instructions

---

### Step 2: Payments Page (2-3 hours)

**Backend Endpoints**:
- `POST /api/v1/billing/bank_accounts/payments/search` - Search payments
- `POST /api/v1/billing/bank_accounts/payments/cash` - Cash payment
- `POST /api/v1/billing/bank_accounts/payments/check` - Check payment
- `POST /api/v1/billing/bank_accounts/payments/bank-transfer` - Bank transfer
- `POST /api/v1/billing/bank_accounts/payments/{id}/verify` - Verify payment

**What to do**:
1. Create `hooks/usePayments.ts` (copy pattern from `useBillingPlans.ts`)
2. Implement search, create, verify functions
3. Update `app/dashboard/billing-revenue/payments/page.tsx`
4. Remove mock data
5. Test

---

### Step 3: Subscriptions Page (2-3 hours)

**Backend Endpoints**:
- `GET /api/v1/billing/subscriptions` - List subscriptions
- `POST /api/v1/billing/subscriptions` - Create subscription
- `PATCH /api/v1/billing/subscriptions/{id}` - Update subscription
- `DELETE /api/v1/billing/subscriptions/{id}` - Cancel subscription
- `POST /api/v1/billing/subscriptions/{id}/change-plan` - Change plan

**What to do**:
1. Create `hooks/useSubscriptions.ts` (copy pattern from `useBillingPlans.ts`)
2. Implement CRUD + plan change functions
3. Update `app/dashboard/billing-revenue/subscriptions/page.tsx`
4. Remove mock data
5. Test

---

## ⚡ Quick Wins (Optional but Recommended)

### Migrate 3 Pages from fetch() to apiClient (1 hour)

**Files to update**:
1. `app/dashboard/security-access/users/page.tsx`
2. `app/dashboard/security-access/secrets/page.tsx`
3. `app/dashboard/operations/customers/page.tsx`

**Find and replace**:
```typescript
// BEFORE
const response = await fetch(`${platformConfig.apiBaseUrl}/api/v1/users`, {
  credentials: 'include',
  headers: { 'Content-Type': 'application/json' }
});
const data = await response.json();

// AFTER
const response = await apiClient.get<User[]>('/api/v1/users');
if (response.success && response.data) {
  setUsers(response.data);
}
```

**Why**: Consistency, better error handling, TypeScript types

---

## 🛠️ Development Commands

```bash
# Start development server
cd frontend/apps/base-app
pnpm dev

# Build (check for errors)
pnpm build

# Type check
pnpm type-check

# Run tests
pnpm test

# Format code
pnpm format
```

---

## 📁 Key Files Reference

### Hooks (Data Fetching)
- `hooks/useBillingPlans.ts` - ✅ Ready for Plans page
- `hooks/useHealth.ts` - ✅ Example pattern
- `hooks/useFeatureFlags.ts` - ✅ Example pattern
- `contexts/RBACContext.tsx` - ⭐ Gold standard (React Query)

### Pages Needing Work
- `app/dashboard/billing-revenue/plans/page.tsx` - Use useBillingPlans
- `app/dashboard/billing-revenue/payments/page.tsx` - Create usePayments
- `app/dashboard/billing-revenue/subscriptions/page.tsx` - Create useSubscriptions

### Documentation
- `BILLING_INTEGRATION_GUIDE.md` - **Read this first!**
- `SESSION_SUMMARY.md` - Complete context
- `PROGRESS_UPDATE.md` - Current status
- `FIXES_COMPLETED.md` - Previous fixes

### Backend Reference
- `src/dotmac/platform/billing/subscriptions/router.py` - Plans & subscriptions endpoints
- `src/dotmac/platform/billing/catalog/router.py` - Products catalog
- `src/dotmac/platform/billing/bank_accounts/router.py` - Payments endpoints

---

## 🎓 Learning from Existing Code

### Best Example: RBACContext
**File**: `contexts/RBACContext.tsx`

**Why it's great**:
- Uses React Query for caching
- Centralized permission logic
- Clean TypeScript types
- Mutation callbacks with cache invalidation
- Proper error handling

**Pattern to copy**:
```typescript
const { data, isLoading, error } = useQuery({
  queryKey: ['resource-name'],
  queryFn: apiClient.get,
  staleTime: 5 * 60 * 1000,
});

const mutation = useMutation({
  mutationFn: apiClient.post,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['resource-name'] });
    toast.success('Success!');
  },
});
```

### Good Example: useHealth Hook
**File**: `hooks/useHealth.ts`

**Why it's good**:
- Simple, focused responsibility
- Uses apiClient
- Proper TypeScript interfaces
- Loading/error states
- Auto-refresh logic

---

## ⚠️ Common Pitfalls

### 1. Price Conversion
Backend stores prices in **minor units (cents)**:
```typescript
// WRONG
display_price = backend_price; // Shows 2999 instead of $29.99

// CORRECT
display_price = backend_price / 100; // Shows $29.99
```

### 2. Billing Intervals
Backend: `monthly`, `quarterly`, `annual`
Frontend Plans page: Only shows `monthly` vs `annual`

**Fix**: Filter or update UI to show all three.

### 3. Features Field
Backend: `Record<string, any>` (JSON)
Frontend: `PlanFeature[]` (structured array)

**Fix**: Need transformation function:
```typescript
function parseFeatures(backendFeatures: Record<string, any>): PlanFeature[] {
  return Object.entries(backendFeatures).map(([key, value]) => ({
    id: key,
    name: value.name,
    included: value.included,
    limit: value.limit,
  }));
}
```

---

## ✅ Definition of Done

A page is "done" when:
1. ✅ No mock data - all data from backend API
2. ✅ Uses `apiClient` or React Query (not raw `fetch()`)
3. ✅ Has loading state
4. ✅ Has error state with retry button
5. ✅ TypeScript types defined
6. ✅ Toast notifications for actions
7. ✅ Works with real backend

---

## 🎯 Time Estimates

| Task | Time | Priority |
|------|------|----------|
| Plans page | 2-3 hours | 🔥 High |
| Payments page | 2-3 hours | 🔥 High |
| Subscriptions page | 2-3 hours | 🔥 High |
| Migrate fetch() → apiClient | 1 hour | ⚡ Medium |
| Form validation | 4-5 hours | 💡 Low |
| TypeScript `any` fixes | 6-8 hours | 💡 Low |

**Total for billing**: 6-9 hours

---

## 🚨 If You Get Stuck

### Check These First:
1. **Build failing?** → Run `pnpm install` then `pnpm build`
2. **Type errors?** → Check TypeScript version, types may be in hook
3. **API errors?** → Check backend is running, check Network tab
4. **Hook not working?** → Check `apiClient` is imported correctly

### Reference Files:
- `BILLING_INTEGRATION_GUIDE.md` - Detailed migration steps
- `hooks/useHealth.ts` - Working example
- `contexts/RBACContext.tsx` - Advanced example

### Backend Verification:
```bash
# Check if backend is running
curl http://localhost:8000/health/ready

# Check billing endpoints exist
curl http://localhost:8000/api/v1/billing/subscriptions/plans \
  -H "Cookie: access_token=YOUR_TOKEN"
```

---

## 🎉 Success!

Once billing pages are done:
- **9/13 pages** connected (69%)
- **All critical revenue features** working
- **Clear path** to 100% (just 2 non-critical pages remain)

**Celebrate** the wins! 🎊

---

**Last updated**: 2025-09-30 by Claude Code
**Next update**: After billing pages are migrated

**Questions?** Read `SESSION_SUMMARY.md` for full context.
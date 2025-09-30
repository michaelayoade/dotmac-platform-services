# Billing Pages API Integration Guide

## Status: Hooks Created, Pages Need Migration

**Date**: 2025-09-30
**Current Status**: Hooks ready, pages still using mock data

---

## ✅ Completed: useBillingPlans Hook

**File**: `hooks/useBillingPlans.ts`

### Backend API Endpoints Mapped:
- `GET /api/v1/billing/subscriptions/plans` - List plans
- `POST /api/v1/billing/subscriptions/plans` - Create plan
- `PATCH /api/v1/billing/subscriptions/plans/{plan_id}` - Update plan
- `DELETE /api/v1/billing/subscriptions/plans/{plan_id}` - Delete plan
- `GET /api/v1/billing/catalog/products` - List products (for plan creation)

### Hook Features:
- ✅ Fetches subscription plans from real API
- ✅ Fetches product catalog for plan creation
- ✅ Full CRUD operations (create, update, delete)
- ✅ Loading and error states
- ✅ Auto-refresh on mount
- ✅ TypeScript interfaces aligned with backend

### Usage Example:
```typescript
import { useBillingPlans } from '@/hooks/useBillingPlans';

function MyComponent() {
  const {
    plans,           // BillingPlan[]
    products,        // ProductCatalogItem[]
    loading,         // boolean
    error,           // string | null
    createPlan,      // (data: PlanCreateRequest) => Promise<any>
    updatePlan,      // (planId: string, updates: PlanUpdateRequest) => Promise<boolean>
    deletePlan,      // (planId: string) => Promise<boolean>
    refreshPlans,    // () => Promise<void>
  } = useBillingPlans();

  // Plans are automatically fetched on mount
  // Use the data in your component
}
```

---

## 📋 Migration Steps for Plans Page

**File to Update**: `app/dashboard/billing-revenue/plans/page.tsx`

### Step 1: Import the Hook
```typescript
import { useBillingPlans, type BillingPlan } from '@/hooks/useBillingPlans';
```

### Step 2: Replace State Management
**Before (lines 100-118):**
```typescript
const [plans, setPlans] = useState<Plan[]>([]);
const [loading, setLoading] = useState(false);

useEffect(() => {
  fetchPlans();
}, []);

const fetchPlans = async () => {
  setLoading(true);
  // ... 200+ lines of mock data
  setPlans(mockPlans);
  setLoading(false);
};
```

**After:**
```typescript
const {
  plans: backendPlans,
  products,
  loading,
  error,
  createPlan,
  updatePlan,
  deletePlan
} = useBillingPlans();

// Map backend plans to display format
const plans = backendPlans.map(plan => ({
  id: plan.plan_id,
  name: plan.name,
  description: plan.description || '',
  price_monthly: plan.billing_interval === 'monthly' ? plan.price_amount / 100 : 0,
  price_annual: plan.billing_interval === 'annual' ? plan.price_amount / 100 : 0,
  currency: plan.currency,
  status: plan.is_active ? 'active' : 'inactive',
  tier: determineTier(plan.price_amount),
  features: parseFeatures(plan.features),
  popular: plan.metadata?.popular || false,
  trial_days: plan.trial_days,
  created_at: plan.created_at,
  updated_at: plan.updated_at,
  subscriber_count: 0, // Need to fetch separately
  mrr: 0, // Need to calculate separately
}));
```

### Step 3: Update CRUD Handlers
**Create Plan:**
```typescript
const handleCreatePlan = async () => {
  if (!newPlanData.product_id) {
    toast.error('Please select a product');
    return;
  }

  try {
    await createPlan(newPlanData);
    toast.success('Plan created successfully');
    setShowNewPlanDialog(false);
  } catch (error) {
    toast.error('Failed to create plan');
  }
};
```

**Update Plan:**
```typescript
const handleUpdatePlan = async () => {
  if (!selectedBackendPlan) return;

  try {
    await updatePlan(selectedBackendPlan.plan_id, {
      display_name: selectedBackendPlan.display_name,
      description: selectedBackendPlan.description,
      trial_days: selectedBackendPlan.trial_days,
      is_active: selectedBackendPlan.is_active,
    });
    toast.success('Plan updated successfully');
    setShowEditDialog(false);
  } catch (error) {
    toast.error('Failed to update plan');
  }
};
```

**Delete Plan:**
```typescript
const handleDeletePlan = async (planId: string) => {
  try {
    await deletePlan(planId);
    toast.success('Plan deleted successfully');
  } catch (error) {
    toast.error('Failed to delete plan');
  }
};
```

### Step 4: Add Loading State
```typescript
if (loading) {
  return (
    <div className="flex items-center justify-center h-96">
      <Loader2 className="h-12 w-12 animate-spin" />
      <p className="ml-4">Loading plans...</p>
    </div>
  );
}
```

### Step 5: Add Error State
```typescript
if (error) {
  return (
    <div className="p-6">
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <p className="text-red-800">{error}</p>
        <Button onClick={() => refreshPlans()} className="mt-2">
          Retry
        </Button>
      </div>
    </div>
  );
}
```

---

## ❌ TODO: Payments Page Hook

**Backend Endpoints Available**:
- `/api/v1/billing/bank_accounts/payments/*` - Manual payments
- Need to find main payments router

**Hook to Create**: `hooks/usePayments.ts`

**Required Features**:
- List payments with filters (status, date range, customer)
- Get payment details
- Create manual payments (cash, check, bank transfer)
- Verify/reconcile payments
- Search payments
- Export payments

---

## ❌ TODO: Subscriptions Page Hook

**Backend Endpoints Available**:
- `GET /api/v1/billing/subscriptions` - List subscriptions
- `POST /api/v1/billing/subscriptions` - Create subscription
- `PATCH /api/v1/billing/subscriptions/{subscription_id}` - Update subscription
- `DELETE /api/v1/billing/subscriptions/{subscription_id}` - Cancel subscription
- `POST /api/v1/billing/subscriptions/{subscription_id}/change-plan` - Change plan
- `POST /api/v1/billing/subscriptions/{subscription_id}/usage` - Record usage

**Hook to Create**: `hooks/useSubscriptions.ts`

**Required Features**:
- List customer subscriptions
- Get subscription details
- Create subscription
- Update subscription
- Cancel subscription
- Change plan with proration
- Record usage for usage-based billing
- Pause/resume subscription

---

## 📊 Backend Data Models

### SubscriptionPlanResponse
```typescript
{
  plan_id: string;
  product_id: string;
  name: string;
  display_name?: string;
  description: string;
  billing_interval: 'monthly' | 'quarterly' | 'annual';
  interval_count: number;
  price_amount: number;      // In minor units (cents)
  currency: string;
  trial_days: number;
  is_active: boolean;
  features?: Record<string, any>;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}
```

### ProductResponse
```typescript
{
  product_id: string;
  tenant_id: string;
  sku: string;
  name: string;
  description?: string;
  category?: string;
  product_type: 'standard' | 'usage_based' | 'hybrid';
  base_price: number;        // In minor units (cents)
  currency: string;
  tax_class?: string;
  usage_type?: string;
  usage_unit_name?: string;
  is_active: boolean;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}
```

---

## 🎯 Estimated Time to Complete

| Task | Time | Status |
|------|------|--------|
| useBillingPlans hook | ✅ Done | Completed |
| Migrate Plans page | 2-3 hours | **Needs work** |
| Create usePayments hook | 1 hour | Not started |
| Migrate Payments page | 1-2 hours | Not started |
| Create useSubscriptions hook | 1 hour | Not started |
| Migrate Subscriptions page | 1-2 hours | Not started |
| **Total** | **6-9 hours** | **1/6 complete** |

---

## 🚨 Important Notes

1. **Price Conversion**: Backend stores prices in minor units (cents). Frontend displays in major units (dollars).
   - Backend: `2999` = Frontend: `29.99`
   - Always divide by 100 when displaying
   - Always multiply by 100 when sending to backend

2. **Billing Intervals**: Backend supports `monthly`, `quarterly`, `annual`. Frontend Plans page only shows `monthly` vs `annual` toggle. Need to update UI or filter plans.

3. **Features Field**: Backend stores as JSON `Record<string, any>`. Frontend expects structured `PlanFeature[]`. Need transformation layer.

4. **Subscriber Count & MRR**: Not included in plan response. May need separate API calls or backend aggregation.

5. **Product Selection**: When creating plans, must first select a product from catalog. Products define base pricing and features.

---

## ✅ Next Steps (Priority Order)

1. **Migrate Plans Page** (2-3 hours)
   - Follow migration steps above
   - Test CRUD operations
   - Handle edge cases (empty state, errors)

2. **Create usePayments Hook** (1 hour)
   - Map payment endpoints
   - Implement search/filter logic
   - Handle different payment types

3. **Migrate Payments Page** (1-2 hours)
   - Replace mock data
   - Update payment handlers
   - Test payment flow

4. **Create useSubscriptions Hook** (1 hour)
   - Map subscription endpoints
   - Implement plan change logic
   - Handle usage tracking

5. **Migrate Subscriptions Page** (1-2 hours)
   - Replace mock data
   - Update subscription handlers
   - Test lifecycle (create, pause, cancel)

---

## 🔗 Related Files

- **Hook**: `frontend/apps/base-app/hooks/useBillingPlans.ts`
- **Page**: `frontend/apps/base-app/app/dashboard/billing-revenue/plans/page.tsx`
- **Backend Router**: `src/dotmac/platform/billing/subscriptions/router.py`
- **Backend Service**: `src/dotmac/platform/billing/subscriptions/service.py`
- **Catalog Router**: `src/dotmac/platform/billing/catalog/router.py`
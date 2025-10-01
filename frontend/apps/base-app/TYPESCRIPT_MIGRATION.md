# TypeScript Migration Guide

## Overview
We've implemented a centralized TypeScript type system in `/types` to improve type safety, code maintainability, and developer experience.

## Migration Completed ✅

### 1. Centralized Type Definitions
All types are now in `/types` directory:
- `api.ts` - API response/request types
- `common.ts` - Shared base types
- `customer.ts` - Customer domain types
- `billing.ts` - Billing/invoice types
- `auth.ts` - Authentication types
- `utils.ts` - TypeScript utilities

### 2. Import Path Updates
```typescript
// Before:
import { Customer, CustomerMetrics } from '@/hooks/useCustomers';

// After:
import { Customer, CustomerMetrics } from '@/types';
```

### 3. Components Updated
- ✅ CustomersList
- ✅ CustomersMetrics
- ✅ CustomerViewModal
- ✅ CustomerEditModal
- ✅ CreateCustomerModal
- ✅ useCustomers hook

## How to Use the New Types

### Basic Import
```typescript
import {
  Customer,
  CustomerCreateInput,
  ApiResponse,
  isApiError
} from '@/types';
```

### Using TypeScript Utilities
```typescript
import { PartialBy, RequiredBy, DeepPartial } from '@/types';

// Make specific fields optional
type DraftCustomer = PartialBy<Customer, 'id' | 'created_at'>;

// Make specific fields required
type ValidatedCustomer = RequiredBy<Customer, 'email' | 'first_name'>;

// Deep partial for nested updates
type CustomerPatch = DeepPartial<Customer>;
```

### Type-Safe API Calls
```typescript
import { ApiResponse, Customer, isApiError } from '@/types';

async function fetchCustomer(id: string): Promise<Customer | null> {
  const response: ApiResponse<Customer> = await api.get(`/customers/${id}`);

  if (response.success && response.data) {
    return response.data;
  }

  if (response.error && isApiError(response.error)) {
    console.error(`API Error: ${response.error.message}`);
  }

  return null;
}
```

### Using Type Guards
```typescript
import { Customer, isBusinessCustomer, isPremiumCustomer } from '@/types';

function calculateDiscount(customer: Customer): number {
  if (isPremiumCustomer(customer)) {
    return 0.2; // 20% discount for premium
  }
  if (isBusinessCustomer(customer)) {
    return 0.1; // 10% discount for business
  }
  return 0; // No discount
}
```

### Form Validation with Types
```typescript
import { CustomerCreateInput, isValidEmail, isNonEmptyString } from '@/types';

function validateCustomerForm(data: Partial<CustomerCreateInput>): string[] {
  const errors: string[] = [];

  if (!data.email || !isValidEmail(data.email)) {
    errors.push('Valid email is required');
  }

  if (!data.first_name || !isNonEmptyString(data.first_name)) {
    errors.push('First name is required');
  }

  return errors;
}
```

### Using Const Assertions
```typescript
import { CustomerStatuses, CustomerTiers } from '@/types';

// Type-safe status checking
if (customer.status === CustomerStatuses.ACTIVE) {
  // TypeScript knows this is exactly 'active'
}

// Type-safe tier comparison
const premiumTiers = [CustomerTiers.PREMIUM, CustomerTiers.ENTERPRISE];
const isPremium = premiumTiers.includes(customer.tier);
```

### Component Props with Types
```typescript
import { Customer, CustomerMetrics, Result } from '@/types';

interface DashboardProps {
  customer: Customer;
  metrics: CustomerMetrics;
  onUpdate: (customer: Customer) => Promise<Result<Customer>>;
}

export function Dashboard({ customer, metrics, onUpdate }: DashboardProps) {
  // Full type safety and IntelliSense
}
```

## Benefits

### 1. **Better IntelliSense**
- Auto-completion for all properties
- Inline documentation
- Jump to definition

### 2. **Compile-Time Safety**
```typescript
// TypeScript catches these errors:
customer.firstNam = 'John';  // ❌ Property doesn't exist
customer.status = 'invalid'; // ❌ Not a valid status
customer.email = 123;         // ❌ Wrong type
```

### 3. **Easier Refactoring**
- Change a type definition, TypeScript shows all affected code
- Rename properties safely across the codebase
- Add required fields and see where they're missing

### 4. **Self-Documenting Code**
```typescript
// The type itself documents what's expected
function processCustomer(
  customer: Customer,
  options?: PartialBy<ProcessingOptions, 'timeout'>
): Promise<Result<ProcessedCustomer>> {
  // Implementation
}
```

## Migration Checklist for New Components

When creating new components or migrating existing ones:

1. ✅ Import types from `@/types` instead of scattered locations
2. ✅ Use utility types instead of manually creating variations
3. ✅ Use type guards for runtime validation
4. ✅ Use const assertions for enums
5. ✅ Leverage TypeScript strict mode for new files
6. ✅ Add proper return types to functions
7. ✅ Use generic types for reusable components

## Gradual Strict Mode Adoption

For new features, you can opt into strict TypeScript:

```typescript
// In your component file
/// <reference path="../../tsconfig.strict.json" />

// This file now uses strict TypeScript settings
```

## Common Patterns

### API Response Handling
```typescript
const { data, error } = await apiClient.get<Customer>('/customer/123');
if (error) {
  // Handle error with full type information
  return;
}
// Use data with full type safety
```

### State Management
```typescript
const [customer, setCustomer] = useState<Customer | null>(null);
const [loading, setLoading] = useState(false); // TypeScript infers boolean
const [errors, setErrors] = useState<Record<keyof Customer, string>>({});
```

### Event Handlers
```typescript
const handleSubmit = async (data: CustomerCreateInput) => {
  const result: Result<Customer> = await createCustomer(data);
  if (result.success) {
    navigate(`/customers/${result.data.id}`);
  }
};
```

## Next Steps

1. Continue migrating remaining components to use centralized types
2. Enable strict mode for new features
3. Add runtime validation with zod for API boundaries
4. Generate types from OpenAPI schema when available
5. Create more domain-specific utility types as needed

## Questions?

The type system is designed to be:
- **Gradual** - Migrate at your own pace
- **Compatible** - Works with existing code
- **Extensible** - Easy to add new types
- **Maintainable** - Single source of truth

For questions or suggestions, please update this guide with your learnings!
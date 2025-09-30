# Form Validation Implementation Guide

## ✅ Completed

### Validation Schemas Created

All validation schemas are in `frontend/apps/base-app/lib/validations/`:

1. **`auth.ts`** - Authentication forms
   - Login validation
   - Register validation (with password strength & confirmation)
   - Password reset validation
   - Change password validation

2. **`customer.ts`** - Customer management forms
   - Customer creation/update (with email, phone, address validation)
   - Customer filtering
   - Customer notes

3. **`webhook.ts`** - Webhook configuration forms
   - Webhook subscription (HTTPS URLs only, event selection)
   - Webhook testing
   - Webhook updates

4. **`apiKey.ts`** - API key management forms
   - API key creation (with scopes, rate limits, IP whitelist)
   - API key updates
   - API key rotation

### Forms with Validation Implemented

✅ **Login Page** (`app/login/page.tsx`) - COMPLETE
- Email validation (format check)
- Password validation (minimum 8 characters)
- Real-time error messages
- Form-level error display

## 📋 Validation Features

### What's Included in Each Schema:

**Common Validations:**
- Required fields
- Min/max length constraints
- Email format validation
- URL format validation
- Regex patterns (phone, country codes, etc.)
- Custom validation rules

**Advanced Features:**
- Password strength requirements
- Password confirmation matching
- Future date validation (for expiration)
- IP address/CIDR validation
- Array length constraints
- Nested object validation

### Example Usage Pattern

```typescript
// 1. Import validation schema and react-hook-form
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { loginSchema, type LoginFormData } from '@/lib/validations/auth';

// 2. Setup form with validation
const {
  register,
  handleSubmit,
  formState: { errors },
} = useForm<LoginFormData>({
  resolver: zodResolver(loginSchema),
});

// 3. Handle form submission
const onSubmit = async (data: LoginFormData) => {
  // Data is already validated!
  console.log(data);
};

// 4. Render form with error messages
<form onSubmit={handleSubmit(onSubmit)}>
  <input
    {...register('email')}
    className={errors.email ? 'border-red-500' : 'border-gray-300'}
  />
  {errors.email && (
    <p className="text-red-500">{errors.email.message}</p>
  )}

  <button type="submit">Submit</button>
</form>
```

## 🚀 Quick Implementation Guide for Other Forms

### Register Page Example

```typescript
// app/register/page.tsx
'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { registerSchema, type RegisterFormData } from '@/lib/validations/auth';

export default function RegisterPage() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterFormData) => {
    // Call API with validated data
    await apiClient.register(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('email')} />
      {errors.email && <span>{errors.email.message}</span>}

      <input {...register('password')} type="password" />
      {errors.password && <span>{errors.password.message}</span>}

      <input {...register('confirmPassword')} type="password" />
      {errors.confirmPassword && <span>{errors.confirmPassword.message}</span>}

      <button type="submit">Register</button>
    </form>
  );
}
```

### Customer Form Example

```typescript
// components/customers/CreateCustomerModal.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { customerSchema, type CustomerFormData } from '@/lib/validations/customer';

export default function CreateCustomerModal() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CustomerFormData>({
    resolver: zodResolver(customerSchema),
  });

  const onSubmit = async (data: CustomerFormData) => {
    await createCustomer(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('name')} placeholder="Customer Name" />
      {errors.name && <span>{errors.name.message}</span>}

      <input {...register('email')} placeholder="Email" />
      {errors.email && <span>{errors.email.message}</span>}

      <input {...register('phone')} placeholder="+1234567890" />
      {errors.phone && <span>{errors.phone.message}</span>}

      <button type="submit">Create Customer</button>
    </form>
  );
}
```

### Webhook Form Example

```typescript
// components/webhooks/WebhookForm.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { webhookSchema, type WebhookFormData } from '@/lib/validations/webhook';

export default function WebhookForm() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<WebhookFormData>({
    resolver: zodResolver(webhookSchema),
    defaultValues: {
      active: true,
      events: [],
    },
  });

  const onSubmit = async (data: WebhookFormData) => {
    await createWebhook(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input
        {...register('url')}
        placeholder="https://your-domain.com/webhook"
      />
      {errors.url && <span>{errors.url.message}</span>}

      <select {...register('events')} multiple>
        <option value="user.created">User Created</option>
        <option value="payment.succeeded">Payment Succeeded</option>
      </select>
      {errors.events && <span>{errors.events.message}</span>}

      <button type="submit">Create Webhook</button>
    </form>
  );
}
```

### API Key Form Example

```typescript
// components/api-keys/CreateApiKeyModal.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { apiKeySchema, type ApiKeyFormData } from '@/lib/validations/apiKey';

export default function CreateApiKeyModal() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ApiKeyFormData>({
    resolver: zodResolver(apiKeySchema),
  });

  const onSubmit = async (data: ApiKeyFormData) => {
    await createApiKey(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('name')} placeholder="API Key Name" />
      {errors.name && <span>{errors.name.message}</span>}

      <select {...register('scopes')} multiple>
        <option value="read:users">Read Users</option>
        <option value="write:users">Write Users</option>
      </select>
      {errors.scopes && <span>{errors.scopes.message}</span>}

      <input {...register('rate_limit')} type="number" placeholder="1000" />
      {errors.rate_limit && <span>{errors.rate_limit.message}</span>}

      <button type="submit">Create API Key</button>
    </form>
  );
}
```

## 📊 Forms Still Needing Validation

Based on the codebase scan, these forms should be updated next (in priority order):

### Priority 1 - Authentication Forms
- ✅ Login page - DONE
- ⏳ Register page (`app/register/page.tsx`)
- ⏳ Password reset pages

### Priority 2 - Customer Management
- ⏳ Create customer modal (`components/customers/CreateCustomerModal.tsx`)
- ⏳ Customer edit forms
- ⏳ Customer notes form

### Priority 3 - Webhooks
- ⏳ Webhook creation form
- ⏳ Webhook edit form

### Priority 4 - API Keys
- ⏳ API key creation modal (`components/api-keys/CreateApiKeyModal.tsx`)
- ⏳ API key edit form

## 🎯 Benefits of This Implementation

1. **Type Safety**: TypeScript types generated from Zod schemas
2. **Reusable**: Schemas can be used in multiple places
3. **Consistent**: Same validation rules across frontend
4. **User Friendly**: Clear error messages
5. **Secure**: Client-side validation + server-side validation
6. **Maintainable**: Centralized validation logic

## 📝 Validation Rules Summary

### Auth Forms
- Email: Required, valid email format
- Password: 8+ chars, uppercase, lowercase, number
- Password confirmation: Must match password

### Customer Forms
- Name: 2-200 characters
- Email: Valid email format
- Phone: International format with regex
- Country: ISO 3166-1 alpha-2 codes
- Website: Valid URL format

### Webhook Forms
- URL: HTTPS required for security
- Events: At least 1 selected, max 50
- Secret: 16+ characters for security

### API Key Forms
- Name: 3-100 characters, alphanumeric only
- Scopes: At least 1 selected
- Rate limit: 1-10,000 requests
- IP whitelist: Valid IP/CIDR notation

## 🔧 Testing Validation

```typescript
// Test in browser console or Jest
import { loginSchema } from '@/lib/validations/auth';

// Valid data
loginSchema.parse({
  email: 'test@example.com',
  password: 'Password123',
}); // ✅ Success

// Invalid data
loginSchema.parse({
  email: 'invalid-email',
  password: 'short',
}); // ❌ Throws ZodError with details
```

## 📚 Next Steps

1. Apply validation to register page (5-10 minutes)
2. Update customer forms (10-15 minutes)
3. Update webhook forms (10-15 minutes)
4. Update API key forms (10-15 minutes)

**Total estimated time: ~1-2 hours** for all remaining forms.

The infrastructure is complete - just copy the pattern from the login page!
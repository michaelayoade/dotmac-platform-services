# Frontend Production Readmap - DotMac Platform Services

## Overview
This document outlines all the frontend fixes and implementations required to make the dashboard production-ready. Each item is prioritized and includes implementation details.

## 🔴 Critical Issues (P0)

### 1. Navigation Coverage - Missing Routes
**Status**: ✅ Partially Fixed
**Files to Create**:

#### Operations Section
- [x] `/dashboard/operations/files` - Created with full file management UI

#### Billing & Revenue Section
- [ ] `/dashboard/billing-revenue/subscriptions/page.tsx`
- [ ] `/dashboard/billing-revenue/payments/page.tsx`
- [ ] `/dashboard/billing-revenue/plans/page.tsx`

#### Security & Access Section
- [ ] `/dashboard/security-access/roles/page.tsx`

#### Infrastructure Section
- [ ] `/dashboard/infrastructure/health/page.tsx`
- [ ] `/dashboard/infrastructure/logs/page.tsx`
- [ ] `/dashboard/infrastructure/observability/page.tsx`
- [ ] `/dashboard/infrastructure/feature-flags/page.tsx`

#### Settings Section
- [ ] `/dashboard/settings/profile/page.tsx`
- [ ] `/dashboard/settings/organization/page.tsx`
- [ ] `/dashboard/settings/notifications/page.tsx`
- [ ] `/dashboard/settings/integrations/page.tsx`

### 2. Operations → Customers Modal Refactor
**Location**: `apps/base-app/app/dashboard/operations/customers/page.tsx`
**Issues**:
- Hand-rolled state management (lines 62-71)
- Using browser `confirm()/alert()` instead of proper dialogs
- Ad-hoc validation without schema

**Fix Required**:
```typescript
// Replace with:
- react-hook-form for form management
- zod for schema validation
- Shared toast system for notifications
- TanStack Query for mutations and cache invalidation
```

### 3. Operations → Communications Actions
**Location**: `apps/base-app/components/communications/CommunicationsDashboard.tsx`
**Issues**:
- "Send Message" button has no handler (lines 69-73)
- Missing compose/send flows
- No empty states
- Missing error handling

**Fix Required**:
- Implement message composition modal
- Add send functionality with API integration
- Create empty state components
- Add proper error toasts

## 🟡 Important Issues (P1)

### 4. Billing & Revenue Features
**Location**: `apps/base-app/app/dashboard/billing-revenue/`
**Issues**:
- Export button is placeholder (invoices/page.tsx:29)
- Missing pagination
- No invoice detail overlays
- Missing subscriptions/payments/plans pages

**Fix Required**:
- Implement real export functionality (CSV/PDF)
- Add pagination with page size controls
- Create invoice detail modal/drawer
- Build complete subscription management
- Implement payment tracking UI
- Create pricing plans editor

### 5. Security & Access Live Data
**Location**: `apps/base-app/app/dashboard/security-access/page.tsx`
**Issues**:
- Hardcoded values (totalRoles: 12, lines 214-223)
- Missing roles page
- Limited audit data display

**Fix Required**:
- Connect to real RBAC endpoints
- Implement roles management page
- Enhance audit log display with filtering
- Add permission matrix view

### 6. Infrastructure Sub-sections
**Location**: `apps/base-app/app/dashboard/infrastructure/`
**Issues**:
- Missing health monitoring dashboard
- No log viewer implementation
- Observability page absent
- Feature flags management missing

**Fix Required**:
- Create health dashboard with service status
- Implement log streaming/viewing
- Build metrics/traces visualization
- Add feature flag toggle interface

## 🟢 Nice to Have (P2)

### 7. Plugin Management Enhancements
**Location**: `apps/base-app/app/dashboard/settings/plugins/`
**Issues**:
- No per-instance detail route
- Missing RBAC integration
- No global alert integration

**Fix Required**:
- Add `/dashboard/settings/plugins/[id]` route
- Implement role-based access controls
- Surface plugin alerts in global banner
- Add audit logging for plugin operations

### 8. Settings Hub Implementation
**Location**: `apps/base-app/app/dashboard/settings/`
**Pages to Build**:
- Profile settings (user preferences, avatar, 2FA)
- Organization settings (company info, branding)
- Notification preferences (email, in-app, webhooks)
- Integration settings (OAuth apps, API configs)

## 🔧 General Polish Tasks

### Code Quality
- [ ] Replace all `console.log` with proper logging
- [ ] Remove all `alert()` calls
- [ ] Standardize error handling
- [ ] Implement consistent loading states

### Data Fetching
- [ ] Migrate all API calls to TanStack Query
- [ ] Implement proper caching strategies
- [ ] Add optimistic updates where appropriate
- [ ] Standardize error/empty/loading states

### Backend Integration
- [ ] Verify all endpoints in `lib/services/metrics-service.ts`
- [ ] Ensure authentication headers are included
- [ ] Handle rate limiting gracefully
- [ ] Implement retry logic for failed requests

### Testing
- [ ] Add Playwright E2E tests for critical paths
- [ ] Create Jest unit tests for components
- [ ] Test error scenarios
- [ ] Verify accessibility compliance

## Implementation Priority

### Phase 1: Critical Path (Week 1)
1. Create all missing route pages (even if placeholder)
2. Fix Operations → Customers modals
3. Complete Communications actions

### Phase 2: Core Features (Week 2)
1. Implement Billing & Revenue pages
2. Add Security & Access live data
3. Build Infrastructure monitoring

### Phase 3: Polish (Week 3)
1. Plugin detail pages
2. Settings hub completion
3. General polish and testing

## Quick Implementation Templates

### Basic Page Template
```typescript
'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function PageName() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Page Title</h1>
        <p className="text-gray-500">Page description</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Section Title</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Content here */}
        </CardContent>
      </Card>
    </div>
  );
}
```

### TanStack Query Integration
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Query hook
const { data, isLoading, error } = useQuery({
  queryKey: ['resource-name'],
  queryFn: fetchResource,
});

// Mutation hook
const mutation = useMutation({
  mutationFn: updateResource,
  onSuccess: () => {
    queryClient.invalidateQueries(['resource-name']);
    toast({ title: 'Success', description: 'Resource updated' });
  },
});
```

### Form with Validation
```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';

const schema = z.object({
  field: z.string().min(1, 'Required'),
});

const form = useForm({
  resolver: zodResolver(schema),
  defaultValues: { field: '' },
});

const onSubmit = (data) => {
  // Handle submission
};
```

## Success Metrics

- [ ] All navigation links lead to valid pages
- [ ] No browser alerts or console.logs in production
- [ ] All forms use proper validation
- [ ] Data fetching uses TanStack Query
- [ ] Loading/error/empty states are consistent
- [ ] Test coverage > 80%
- [ ] Lighthouse score > 90

## Next Steps

1. Start with Phase 1 critical issues
2. Set up TanStack Query provider if not present
3. Create shared empty/error state components
4. Implement one page fully as reference
5. Replicate pattern across remaining pages

This roadmap ensures the dashboard becomes production-ready with proper architecture, error handling, and user experience.
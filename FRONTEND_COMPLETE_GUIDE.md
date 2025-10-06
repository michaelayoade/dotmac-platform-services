# DotMac Platform - Frontend Complete Guide

## Overview

The DotMac Platform frontend is a **production-ready Next.js 14 application** with TypeScript, providing a complete SaaS dashboard with authentication, billing, customer management, analytics, and administrative interfaces.

## Technology Stack

| Technology | Version | Purpose |
|-----------|---------|---------|
| **Next.js** | 14.2+ | React framework with App Router |
| **TypeScript** | 5.4+ | Type-safe JavaScript |
| **React** | 18.3 | UI library |
| **TailwindCSS** | 3.4+ | Utility-first CSS |
| **shadcn/ui** | Latest | Component library |
| **TanStack Query** | 5.59+ | Data fetching & caching |
| **React Hook Form** | 7.51+ | Form management |
| **Zod** | 3.22+ | Schema validation |
| **next-themes** | 0.3+ | Dark/light mode |
| **Playwright** | 1.49+ | E2E testing |
| **Jest** | 29.7+ | Unit testing |
| **MSW** | 2.11+ | API mocking |
| **Storybook** | 8.6+ | Component development |

## Project Structure

```
frontend/
├── apps/
│   └── base-app/                    # Main Next.js application
│       ├── app/                     # Next.js App Router
│       │   ├── (auth)/             # Auth-related pages
│       │   │   ├── login/
│       │   │   ├── register/
│       │   │   └── forgot-password/
│       │   ├── dashboard/          # Main dashboard (protected)
│       │   │   ├── analytics/      # Business analytics
│       │   │   ├── billing-revenue/ # Billing & revenue
│       │   │   │   ├── invoices/
│       │   │   │   ├── payments/
│       │   │   │   ├── subscriptions/
│       │   │   │   └── plans/
│       │   │   ├── infrastructure/ # Platform infrastructure
│       │   │   │   ├── health/
│       │   │   │   ├── logs/
│       │   │   │   ├── observability/
│       │   │   │   └── feature-flags/
│       │   │   ├── operations/     # Daily operations
│       │   │   │   ├── customers/
│       │   │   │   ├── communications/
│       │   │   │   └── files/
│       │   │   ├── partners/       # Partner management
│       │   │   ├── security-access/ # Security & access control
│       │   │   │   ├── api-keys/
│       │   │   │   ├── permissions/
│       │   │   │   ├── roles/
│       │   │   │   ├── secrets/
│       │   │   │   └── users/
│       │   │   ├── settings/       # App settings
│       │   │   │   ├── billing/
│       │   │   │   ├── integrations/
│       │   │   │   ├── notifications/
│       │   │   │   ├── organization/
│       │   │   │   ├── plugins/
│       │   │   │   └── profile/
│       │   │   └── webhooks/       # Webhook management
│       │   ├── portal/             # Partner portal
│       │   │   ├── dashboard/
│       │   │   ├── customers/
│       │   │   ├── referrals/
│       │   │   ├── commissions/
│       │   │   └── settings/
│       │   ├── layout.tsx          # Root layout
│       │   ├── page.tsx            # Landing page
│       │   └── globals.css         # Global styles
│       ├── components/              # React components
│       │   ├── ui/                 # shadcn/ui components
│       │   │   ├── button.tsx
│       │   │   ├── card.tsx
│       │   │   ├── dialog.tsx
│       │   │   ├── input.tsx
│       │   │   ├── table.tsx
│       │   │   └── ... (40+ components)
│       │   ├── alerts/
│       │   ├── billing/
│       │   ├── charts/
│       │   ├── communications/
│       │   ├── customers/
│       │   └── partners/
│       ├── lib/                     # Utilities & API client
│       │   ├── api/                # API client layer
│       │   │   ├── generated/      # Auto-generated from OpenAPI
│       │   │   └── httponly-auth.ts # HTTP-only cookie auth
│       │   ├── auth.ts             # Auth utilities
│       │   ├── utils.ts            # Helper functions
│       │   └── platformConfig.ts   # Platform configuration
│       ├── hooks/                   # Custom React hooks
│       │   ├── useAuth.ts
│       │   ├── useCustomers.ts
│       │   ├── useHealth.ts
│       │   ├── useLogs.ts
│       │   ├── useObservability.ts
│       │   ├── usePartners.ts
│       │   └── ... (20+ hooks)
│       ├── __tests__/              # Test suites
│       │   ├── a11y/               # Accessibility tests
│       │   ├── components/         # Component tests
│       │   ├── pages/              # Page tests
│       │   └── mocks/              # MSW mock handlers
│       ├── e2e/                    # Playwright E2E tests
│       │   ├── auth.spec.ts
│       │   ├── billing.spec.ts
│       │   ├── customer.spec.ts
│       │   ├── plugins.spec.ts
│       │   └── visual.spec.ts
│       ├── stories/                 # Storybook stories
│       ├── public/                  # Static assets
│       ├── middleware.ts            # Next.js middleware
│       ├── next.config.mjs         # Next.js configuration
│       ├── tailwind.config.ts      # Tailwind configuration
│       ├── jest.config.mjs         # Jest configuration
│       ├── jest.setup.js           # Jest setup
│       ├── playwright.config.ts    # Playwright configuration
│       └── package.json            # Dependencies & scripts
└── shared/
    └── packages/                    # Shared workspace packages
        ├── @dotmac/ui              # Shared UI components
        ├── @dotmac/auth            # Auth utilities
        ├── @dotmac/http-client     # HTTP client
        ├── @dotmac/hooks           # Shared hooks
        ├── @dotmac/analytics       # Analytics utilities
        ├── @dotmac/graphql-client  # GraphQL client
        └── ...                      # 10+ shared packages
```

## Quick Start

### Prerequisites
- Node.js 18+
- pnpm 8+
- Backend running on http://localhost:8000

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
pnpm install

# Build shared packages
pnpm build

# Start development server
pnpm dev:base-app
```

The app will be available at http://localhost:3000

### Environment Variables

Create `.env.local` in `frontend/apps/base-app/`:

```bash
# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Authentication
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-nextauth-secret-change-in-production

# Optional: Enable mock API for development
NEXT_PUBLIC_MOCK_API=false

# Optional: Enable debug logging
NEXT_PUBLIC_DEBUG=false
```

## Development Workflow

### Running the App

```bash
# Development mode (hot reload)
pnpm dev:base-app

# Development with mock API (no backend needed)
pnpm dev:mock

# Production build
pnpm build

# Start production server
pnpm start

# Clean build artifacts
pnpm clean
```

### Code Quality

```bash
# Linting
pnpm lint

# Type checking
pnpm type-check

# Auto-formatting
pnpm format
```

### Testing

#### Unit Tests (Jest + React Testing Library)

```bash
# Run all tests
pnpm test

# Watch mode
pnpm test:watch

# Coverage report
pnpm test:coverage

# Test specific component
pnpm test PluginCard

# Test specific pattern
pnpm test --testPathPattern=components
```

**Current Status**: 277 tests, 93.9% pass rate (260 passing, 17 failing/skipped)

#### E2E Tests (Playwright)

```bash
# Run all E2E tests
pnpm test:e2e

# Run with UI mode (interactive)
pnpm test:e2e:ui

# Run specific test suite
pnpm test:e2e:billing
pnpm test:e2e:auth
pnpm test:e2e:critical

# Visual regression tests
pnpm test:visual

# Update visual snapshots
pnpm test:visual:update

# Visual test UI mode
pnpm test:visual:ui
```

### Storybook

```bash
# Start Storybook dev server
pnpm storybook

# Build Storybook for production
pnpm storybook:build
```

## API Integration

### Auto-Generated API Client

The frontend uses auto-generated TypeScript types from the backend OpenAPI schema.

```bash
# Generate API types from running backend
pnpm generate:api

# Generate from production API
pnpm generate:api:prod
```

This creates `lib/api/generated/types.ts` with full type safety.

### HTTP-Only Cookie Authentication

```typescript
// lib/api/httponly-auth.ts
import { platformConfig } from '../platformConfig';

export async function login(credentials: LoginCredentials) {
  const response = await fetch(
    `${platformConfig.apiBaseUrl}/api/v1/auth/login/cookie`,
    {
      method: 'POST',
      credentials: 'include', // Include HTTP-only cookies
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    }
  );
  return response.json();
}

export async function getCurrentUser() {
  const response = await fetch(
    `${platformConfig.apiBaseUrl}/api/v1/auth/me`,
    {
      credentials: 'include', // Send cookies with request
    }
  );
  return response.json();
}
```

### Custom Hooks for API Integration

```typescript
// hooks/useCustomers.ts
import { useQuery, useMutation } from '@tanstack/react-query';

export function useCustomers(tenantId?: string) {
  return useQuery({
    queryKey: ['customers', tenantId],
    queryFn: async () => {
      const response = await fetch(
        `/api/v1/customers${tenantId ? `?tenant_id=${tenantId}` : ''}`,
        { credentials: 'include' }
      );
      return response.json();
    },
  });
}

export function useCreateCustomer() {
  return useMutation({
    mutationFn: async (data: CustomerCreateRequest) => {
      const response = await fetch('/api/v1/customers', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      return response.json();
    },
  });
}
```

## UI Components

### shadcn/ui Component Library

The app uses 40+ pre-built, customizable components from shadcn/ui:

- **Forms**: Button, Input, Textarea, Select, Checkbox, Switch, RadioGroup
- **Data Display**: Table, Card, Badge, Separator, Progress
- **Feedback**: Alert, Dialog, Toast, Skeleton
- **Navigation**: Tabs, Breadcrumb, Dropdown Menu
- **Layout**: Sheet, ScrollArea

### Custom Components

#### Plugin Management
```typescript
// components/plugins/PluginCard.tsx
<PluginCard
  plugin={whatsappPlugin}
  onConfigure={handleConfigure}
  onTestConnection={handleTest}
/>
```

#### Customer Management
```typescript
// components/customers/CustomersMetrics.tsx
<CustomersMetrics
  totalCustomers={1250}
  activeCustomers={980}
  churnRate={2.5}
  growthRate={15.3}
/>
```

#### Billing
```typescript
// components/billing/InvoiceList.tsx
<InvoiceList
  invoices={invoices}
  onDownload={handleDownload}
  onView={handleView}
/>
```

## Routing & Pages

### App Router Structure

```typescript
// app/dashboard/layout.tsx - Protected dashboard layout
export default function DashboardLayout({ children }: { children: React.Node }) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1">
        {children}
      </main>
    </div>
  );
}

// app/dashboard/billing-revenue/invoices/page.tsx
export default async function InvoicesPage() {
  return (
    <div>
      <PageHeader title="Invoices" />
      <InvoiceList />
    </div>
  );
}
```

### Middleware for Auth Protection

```typescript
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Check if user is authenticated
  const isAuthenticated = request.cookies.has('session_token');

  if (!isAuthenticated && request.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*', '/portal/:path*'],
};
```

## Theme System

### Dark/Light Mode

```typescript
// Uses next-themes for theme management
import { ThemeProvider } from 'next-themes';

// app/layout.tsx
<ThemeProvider attribute="class" defaultTheme="system" enableSystem>
  {children}
</ThemeProvider>

// components/theme-toggle.tsx
import { useTheme } from 'next-themes';

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <button onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
      Toggle Theme
    </button>
  );
}
```

### Custom Theming

```css
/* app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%;
    --secondary: 210 40% 96.1%;
    /* ... more custom properties */
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --primary: 217.2 91.2% 59.8%;
    --secondary: 217.2 32.6% 17.5%;
    /* ... dark theme overrides */
  }
}
```

## Testing Strategies

### Unit Testing Best Practices

```typescript
// __tests__/components/PluginCard.test.tsx
import { render, screen, userEvent } from '@testing-library/react';
import { PluginCard } from '@/components/plugins/PluginCard';

describe('PluginCard', () => {
  it('displays plugin information', () => {
    render(<PluginCard plugin={mockPlugin} />);

    expect(screen.getByText('WhatsApp Integration')).toBeInTheDocument();
    expect(screen.getByText('healthy')).toBeInTheDocument();
  });

  it('handles configure action', async () => {
    const onConfigure = jest.fn();
    const user = userEvent.setup();

    render(<PluginCard plugin={mockPlugin} onConfigure={onConfigure} />);

    await user.click(screen.getByRole('button', { name: /configure/i }));

    expect(onConfigure).toHaveBeenCalledWith(mockPlugin.id);
  });
});
```

### E2E Testing with Playwright

```typescript
// e2e/billing.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Billing Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
  });

  test('can view invoices', async ({ page }) => {
    await page.goto('/dashboard/billing-revenue/invoices');

    // Wait for invoices to load
    await page.waitForSelector('[data-testid="invoice-list"]');

    // Check invoice is displayed
    await expect(page.getByText('INV-2024-001')).toBeVisible();
  });

  test('can create subscription', async ({ page }) => {
    await page.goto('/dashboard/billing-revenue/subscriptions');

    await page.click('button:has-text("New Subscription")');

    await page.selectOption('[name="plan"]', 'professional');
    await page.fill('[name="quantity"]', '5');

    await page.click('button:has-text("Create")');

    await expect(page.getByText('Subscription created')).toBeVisible();
  });
});
```

### MSW for API Mocking

```typescript
// __tests__/mocks/handlers.ts
import { rest } from 'msw';

export const handlers = [
  rest.get('/api/v1/customers', (req, res, ctx) => {
    return res(
      ctx.json({
        customers: [
          { id: '1', name: 'Acme Corp', status: 'active' },
          { id: '2', name: 'Tech Startup', status: 'trial' },
        ],
      })
    );
  }),

  rest.post('/api/v1/customers', async (req, res, ctx) => {
    const data = await req.json();
    return res(
      ctx.status(201),
      ctx.json({ id: '3', ...data })
    );
  }),
];
```

## CI/CD Integration

### Frontend Test Workflows

1. **frontend-tests.yml**
   - Lint & type check all packages
   - Unit tests for shared packages (with coverage)
   - Unit tests for base app (with coverage)
   - E2E tests with backend integration
   - Production build validation
   - Security audit (pnpm audit)

2. **e2e-tests.yml**
   - Matrix testing (Chromium, Firefox, WebKit)
   - Sharded execution (2-4 shards)
   - Visual regression tests
   - Performance tests (main branch only)
   - Nightly runs (full matrix)
   - PR comments with results

3. **type-safety-validation.yml**
   - Backend Pydantic validation
   - OpenAPI schema generation
   - TypeScript type generation
   - Frontend type check
   - Build validation
   - PR comments with type safety report

### GitHub Actions Configuration

```yaml
# .github/workflows/frontend-tests.yml
name: Frontend Tests
on:
  push:
    branches: [main, dev/*]
    paths: ['frontend/**']
  pull_request:
    branches: [main]
    paths: ['frontend/**']

jobs:
  unit-tests-base-app:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      - uses: pnpm/action-setup@v2
        with:
          version: 8
      - run: pnpm install --frozen-lockfile
        working-directory: ./frontend
      - run: pnpm build
        working-directory: ./frontend
      - run: pnpm --filter "@dotmac/base-app" test --coverage
        working-directory: ./frontend
```

## Performance Optimization

### Code Splitting

```typescript
// Dynamic imports for large components
import dynamic from 'next/dynamic';

const AnalyticsDashboard = dynamic(
  () => import('@/components/analytics/AnalyticsDashboard'),
  {
    loading: () => <Skeleton className="h-96" />,
    ssr: false, // Disable SSR for client-only components
  }
);
```

### Image Optimization

```typescript
import Image from 'next/image';

<Image
  src="/logo.png"
  alt="Company Logo"
  width={200}
  height={50}
  priority // Above the fold images
/>
```

### Font Optimization

```typescript
// app/layout.tsx
import { Inter } from 'next/font/google';

const inter = Inter({ subsets: ['latin'] });

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={inter.className}>
      <body>{children}</body>
    </html>
  );
}
```

## Accessibility

### ARIA Labels & Roles

```typescript
<button
  aria-label="Close dialog"
  onClick={onClose}
>
  <X className="h-4 w-4" />
</button>

<div role="alert" aria-live="polite">
  {errorMessage}
</div>
```

### Keyboard Navigation

```typescript
// All interactive elements support keyboard navigation
<Card
  tabIndex={0}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      onClick();
    }
  }}
  className="cursor-pointer"
>
  {content}
</Card>
```

### Accessibility Testing

```typescript
// __tests__/a11y/button-accessibility.test.tsx
import { axe } from 'jest-axe';

test('Button has no accessibility violations', async () => {
  const { container } = render(<Button>Click me</Button>);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

## Best Practices

### Component Structure

```typescript
// components/customers/CustomerCard.tsx
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface CustomerCardProps {
  customer: Customer;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
}

export function CustomerCard({ customer, onEdit, onDelete }: CustomerCardProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">{customer.name}</h3>
          <Badge variant={customer.status === 'active' ? 'success' : 'secondary'}>
            {customer.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{customer.email}</p>
        <div className="mt-4 flex gap-2">
          {onEdit && (
            <button onClick={() => onEdit(customer.id)}>Edit</button>
          )}
          {onDelete && (
            <button onClick={() => onDelete(customer.id)}>Delete</button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
```

### Error Handling

```typescript
import { useQuery } from '@tanstack/react-query';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';

export function CustomerList() {
  const { data, error, isLoading } = useCustomers();

  if (isLoading) return <Skeleton count={5} />;

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Error loading customers</AlertTitle>
        <AlertDescription>{error.message}</AlertDescription>
      </Alert>
    );
  }

  return <div>{/* Render customers */}</div>;
}
```

### Type Safety

```typescript
// Always use TypeScript interfaces for props
interface InvoiceListProps {
  invoices: Invoice[];
  onDownload: (invoiceId: string) => Promise<void>;
  loading?: boolean;
}

// Use discriminated unions for component variants
type ButtonVariant =
  | { variant: 'primary'; onClick: () => void }
  | { variant: 'link'; href: string };

// Leverage inferred types from API client
import type { components } from '@/lib/api/generated/types';
type Customer = components['schemas']['CustomerResponse'];
```

## Troubleshooting

### Common Issues

**Issue**: "Module not found" errors
```bash
# Clear Next.js cache
rm -rf .next

# Reinstall dependencies
pnpm install
```

**Issue**: Type errors after API changes
```bash
# Regenerate API types
pnpm generate:api

# Clear TypeScript cache
pnpm type-check --force
```

**Issue**: Tests failing in CI but passing locally
```bash
# Run tests with CI environment
CI=true pnpm test

# Check for hardcoded URLs or environment-specific logic
```

**Issue**: Playwright tests timeout
```bash
# Increase timeout in playwright.config.ts
timeout: 60000 // 60 seconds
```

## Resources

- **Next.js Documentation**: https://nextjs.org/docs
- **shadcn/ui Components**: https://ui.shadcn.com
- **TanStack Query**: https://tanstack.com/query/latest
- **Playwright**: https://playwright.dev
- **Testing Library**: https://testing-library.com/react

---

**Last Updated**: 2025-10-06
**Frontend Version**: 0.1.0
**Status**: ✅ Production Ready

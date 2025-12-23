# DotMac Platform Dashboard - Implementation Plan

## Overview

This document outlines the complete frontend implementation plan for the DotMac Platform Services admin dashboard. The frontend is built with Next.js 14+ App Router and leverages the centralized `@dotmac/component-library` for consistent UI.

---

## Design System: "Precision Control Room"

### Aesthetic Direction
- **Dark theme** with strategic accent colors (electric cyan, amber highlights)
- **Information-dense** but elegantly organized layouts
- **Command-center** feel with real-time status indicators
- **Sharp typography** that feels authoritative yet modern
- **Micro-animations** for feedback and delight

### Color Palette
| Token | Value | Usage |
|-------|-------|-------|
| `surface` | `hsl(220 20% 6%)` | Base background |
| `surface-elevated` | `hsl(220 18% 9%)` | Cards, modals |
| `accent` | `hsl(185 85% 50%)` | Primary actions, links |
| `highlight` | `hsl(45 95% 55%)` | Secondary accents |
| `status-success` | `hsl(145 72% 45%)` | Positive states |
| `status-warning` | `hsl(38 95% 55%)` | Warning states |
| `status-error` | `hsl(0 75% 55%)` | Error states |

---

## Component Library Integration

### Packages Used

| Package | Components | Usage |
|---------|------------|-------|
| `@dotmac/design-tokens` | ThemeProvider, colors, spacing | Theme system, CSS variables |
| `@dotmac/core` | Button, Card, Input, Modal, Select, Toast | UI primitives |
| `@dotmac/forms` | Form, FormField, FormSubmitButton | Form handling with Zod validation |
| `@dotmac/data-table` | DataTable | User/tenant/invoice tables |
| `@dotmac/charts` | LineChart, BarChart, AreaChart, PieChart | Analytics visualizations |
| `@dotmac/dashboards` | DashboardLayout, KPITile, FilterBar, ChartGrid | Dashboard layouts |

---

## Application Structure

```
frontend/
├── app/
│   ├── (auth)/                 # Auth routes (unauthenticated)
│   │   ├── login/
│   │   ├── forgot-password/
│   │   └── layout.tsx
│   ├── (dashboard)/            # Protected dashboard routes
│   │   ├── layout.tsx          # Dashboard shell
│   │   ├── page.tsx            # Overview dashboard
│   │   ├── users/              # User management
│   │   ├── tenants/            # Tenant management
│   │   ├── billing/            # Billing & invoices
│   │   ├── analytics/          # Analytics dashboards
│   │   ├── customers/          # CRM
│   │   ├── deployments/        # Deployment management
│   │   └── settings/           # Configuration
│   ├── api/                    # API routes
│   └── layout.tsx              # Root layout
├── components/
│   ├── layout/                 # Shell, Sidebar, Header
│   ├── features/               # Feature-specific components
│   └── shared/                 # Reusable composed components
├── lib/
│   ├── api/                    # API client & data fetching
│   ├── auth/                   # NextAuth configuration
│   ├── hooks/                  # Custom React hooks
│   ├── providers/              # Context providers
│   └── utils.ts                # Utility functions
└── types/                      # TypeScript definitions
```

---

## Key Features Implementation

### 1. Dashboard Overview (`/`)
- **KPI Grid**: Users, Tenants, Revenue, Deployments
- **Revenue Chart**: 12-month trend with AreaChart
- **User Growth**: Weekly registrations with BarChart
- **Recent Activity**: Real-time activity feed
- **System Health**: Service status monitoring
- **Quick Actions**: Fast access to common tasks

### 2. User Management (`/users`)
- **DataTable**: Full-featured with pagination, sorting, filtering
- **Bulk Actions**: Email, Activate, Suspend, Delete
- **Quick Filters**: Active, Admins, Pending Invite
- **Role Management**: Admin, Owner, Member, Viewer
- **User CRUD**: Create, edit, view user details

### 3. Tenant Management (`/tenants`)
- **Tenant List**: Organizations with subscription status
- **Onboarding Flow**: New tenant setup wizard
- **Configuration**: Tenant-specific settings
- **Usage Analytics**: Per-tenant metrics

### 4. Billing Dashboard (`/billing`)
- **Revenue KPIs**: MRR, ARR, Outstanding, Collection Rate
- **Invoice Management**: Create, send, void invoices
- **Subscription Tracking**: Active, churned, upgrades
- **Payment Analytics**: Methods, trends, forecasting

### 5. Analytics (`/analytics`)
- **Usage Metrics**: API calls, active users, storage
- **Revenue Analytics**: Cohort analysis, churn prediction
- **Performance**: Response times, error rates
- **Custom Reports**: Exportable data views

### 6. Deployment Management (`/deployments`)
- **Deployment List**: Status, health, resources
- **Provisioning**: New instance creation
- **Monitoring**: Real-time metrics and logs
- **Scaling**: Resource management

### 7. Settings (`/settings`)
- **Profile**: User preferences
- **Security**: MFA, sessions, API keys
- **Notifications**: Email preferences
- **Team**: Role management
- **Billing**: Payment methods, invoices

---

## API Integration

### Backend Endpoints
- **REST API**: `/api/v1/*` for CRUD operations
- **GraphQL**: `/api/v1/graphql` for analytics
- **Health**: `/health` for system status
- **Auth**: `/api/v1/auth/*` for authentication

### Client Architecture
```typescript
// API client with automatic auth
const api = {
  get: <T>(endpoint, options?) => request<T>(endpoint, { method: "GET", ...options }),
  post: <T>(endpoint, data?, options?) => request<T>(endpoint, { method: "POST", body: data, ...options }),
  // ...
};

// TanStack Query for caching
const { data, isLoading } = useQuery({
  queryKey: ["users", { page, search }],
  queryFn: () => getUsers({ page, search }),
});
```

---

## Authentication Flow

1. **Login**: Email/password via NextAuth CredentialsProvider
2. **JWT Storage**: Access token in session, refresh token in HTTP-only cookie
3. **Session Sync**: Automatic token refresh every 5 minutes
4. **RBAC**: Permission checks via `usePermission` hook
5. **Multi-Tenancy**: Tenant context from auth token

---

## State Management

| State Type | Solution | Use Case |
|------------|----------|----------|
| Server State | TanStack Query | API data, caching, mutations |
| Client State | Zustand | UI state, preferences |
| URL State | Next.js searchParams | Pagination, filters |
| Form State | React Hook Form | Form inputs, validation |

---

## Performance Optimizations

1. **Server Components**: Default for all pages
2. **Streaming**: Suspense boundaries for progressive loading
3. **Data Caching**: TanStack Query with 30s stale time
4. **Code Splitting**: Automatic with App Router
5. **Image Optimization**: Next.js Image component
6. **Bundle Analysis**: Regular audits

---

## Next Steps

### Phase 1: Core Infrastructure
- [x] Project setup with Next.js 14
- [x] Tailwind configuration with design tokens
- [x] Authentication with NextAuth
- [x] Dashboard shell with navigation
- [x] API client setup

### Phase 2: Primary Features
- [x] Dashboard overview page
- [x] Users management
- [x] Billing dashboard
- [ ] Tenant management
- [ ] Analytics dashboards

### Phase 3: Secondary Features
- [ ] Customer CRM
- [ ] Deployment management
- [ ] Settings pages
- [ ] Notifications

### Phase 4: Polish
- [ ] Error boundaries and loading states
- [ ] Accessibility audit
- [ ] Performance optimization
- [ ] E2E testing with Playwright
- [ ] Documentation

---

## Development Commands

```bash
# Install dependencies
pnpm install

# Start development server
pnpm dev

# Build for production
pnpm build

# Type checking
pnpm type-check

# Linting
pnpm lint
```

---

## Environment Variables

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
API_URL=http://localhost:8000

# Authentication
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-key

# Optional: SSO Providers
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
AZURE_AD_CLIENT_ID=
AZURE_AD_CLIENT_SECRET=
AZURE_AD_TENANT_ID=
```

---

This implementation provides a production-ready admin dashboard that:
- Integrates seamlessly with the DotMac Platform Services backend
- Uses the centralized component library for consistent UI
- Follows Next.js 14 best practices
- Implements proper authentication and authorization
- Provides a distinctive, memorable user experience

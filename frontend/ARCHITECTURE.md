# DotMac Platform Dashboard - Architecture

## Tech Stack

- **Framework**: Next.js 14+ (App Router)
- **Styling**: Tailwind CSS + @dotmac/design-tokens
- **Components**: @dotmac/component-library (core, forms, data-table, charts, dashboards)
- **State**: TanStack Query (server state) + Zustand (client state)
- **Auth**: NextAuth.js (App Router handler at `/app/api/auth/[...nextauth]`) with JWT from backend
- **API**: REST (/api/v1/*)

## Directory Structure

```
frontend/
├── app/                          # Next.js App Router
│   ├── (auth)/                   # Auth routes (login, signup, verify-email)
│   │   ├── login/
│   │   ├── forgot-password/
│   │   ├── signup/
│   │   ├── verify-email/
│   │   └── layout.tsx
│   ├── (partner)/                # Partner portal routes
│   │   ├── page.tsx              # Partner dashboard
│   │   ├── referrals/
│   │   ├── customers/
│   │   ├── commissions/
│   │   ├── statements/
│   │   └── settings/
│   ├── (tenant)/                 # Tenant portal routes
│   │   ├── page.tsx              # Tenant dashboard
│   │   ├── team/
│   │   ├── billing/
│   │   ├── usage/
│   │   └── settings/
│   ├── (dashboard)/              # Protected dashboard routes
│   │   ├── layout.tsx            # Dashboard shell with sidebar
│   │   ├── page.tsx              # Home/Overview dashboard
│   │   ├── users/                # User management
│   │   ├── tenants/              # Tenant/org management
│   │   ├── billing/              # Billing dashboard
│   │   ├── analytics/            # Analytics & reports
│   │   ├── customers/            # CRM
│   │   ├── deployments/          # Deployment management
│   │   └── settings/             # Configuration
│   ├── api/                      # API routes (BFF pattern)
│   │   └── auth/                 # NextAuth route handler
│   │       └── [...nextauth]/    # NextAuth App Router endpoint
│   ├── layout.tsx                # Root layout
│   └── globals.css
├── components/
│   ├── layout/                   # Shell, Sidebar, Header, etc.
│   ├── features/                 # Feature-specific components
│   └── shared/                   # Reusable composed components
├── lib/
│   ├── api/                      # API client & hooks
│   ├── auth/                     # Auth utilities
│   ├── stores/                   # Zustand stores
│   └── utils/                    # Helpers
├── types/                        # TypeScript definitions
└── config/                       # App configuration
```

## Design System Integration

The frontend extends @dotmac/design-tokens with platform-specific theming:

```tsx
// Theme hierarchy
@dotmac/design-tokens (base)
  └── platform-theme (extends)
       ├── admin-portal (variant)
       ├── customer-portal (variant)
       └── partner-portal (variant)
```

## Key Patterns

### 1. Server Components by Default
- Pages default to server components
- Client components are used for interactive flows (signup wizard, partner/tenant portals)
- Streaming with Suspense for progressive loading

### 2. API Integration
- TanStack Query for data fetching/caching
- Optimistic updates for better UX
- Real-time updates via WebSockets where needed

### 3. Role-Based Access
- Route-group layouts guard authenticated access with NextAuth sessions
- API enforces role/tenant access control for portal data
- Client-side permission hooks adapt UI where available

### 4. Multi-Tenancy
- Tenant context from auth token
- API calls include tenant scope; partner portal can set `X-Active-Tenant-Id`
- UI adapts to tenant configuration

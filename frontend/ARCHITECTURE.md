# DotMac Platform Dashboard - Architecture

## Tech Stack

- **Framework**: Next.js 14+ (App Router)
- **Styling**: Tailwind CSS + @dotmac/design-tokens
- **Components**: @dotmac/component-library (core, forms, data-table, charts, dashboards)
- **State**: TanStack Query (server state) + Zustand (client state)
- **Auth**: NextAuth.js with JWT from backend
- **API**: REST (/api/v1/*) + GraphQL (/api/v1/graphql)

## Directory Structure

```
frontend/
├── app/                          # Next.js App Router
│   ├── (auth)/                   # Auth routes (login, forgot-password)
│   │   ├── login/
│   │   ├── forgot-password/
│   │   └── layout.tsx
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
- All pages are server components
- Client components only where interactivity is needed
- Streaming with Suspense for progressive loading

### 2. API Integration
- TanStack Query for data fetching/caching
- Optimistic updates for better UX
- Real-time updates via WebSockets where needed

### 3. Role-Based Access
- Middleware checks JWT & permissions
- Server components verify access before rendering
- Client-side permission hooks for UI adaptation

### 4. Multi-Tenancy
- Tenant context from auth token
- All API calls include tenant scope
- UI adapts to tenant configuration

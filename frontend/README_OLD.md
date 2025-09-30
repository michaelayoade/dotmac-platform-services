# DotMac Frontend Shared Workspace

Reusable frontend workspace that ships the cross-cutting packages and a
Next.js base application for DotMac products.

## Workspace Layout

- `shared/packages/*` – UI primitives, analytics widgets, auth providers, HTTP
  clients, and other shared libraries
- `apps/base-app` – Opinionated Next.js starter wired to the shared packages

## Install & Develop

```bash
cd frontend
pnpm install
pnpm build              # build all shared packages
pnpm generate:api-client # regenerate TypeScript types from ../openapi.json
pnpm dev:base-app        # start the base Next.js app (http://localhost:3000)
```

To work on a specific package:

```bash
pnpm --filter @dotmac/ui dev
pnpm --filter @dotmac/analytics build
```

## Included Shared Packages

### Core UI & Design
- `design-system` – Design tokens and global styling primitives
- `ui` – Shared component library with accessibility features
- `primitives` – Low-level UI primitives (buttons, inputs, modals)
- `styled-components` – Theming helpers and multi-brand support

### Data & Analytics
- `analytics` – Higher-level analytics widgets and services
- `dashboard` – Reusable charting/dashboard widgets (Recharts-based)
- `data-tables` – Universal data table components (sorting, filtering, export)

### State & Logic
- `headless` – Headless React logic (state stores, query helpers, realtime)
- `hooks` – Additional shared React hooks
- `providers` – Universal context providers; depends on `auth`/`rbac`
- `http-client` – Lightweight client helpers for API access

### Authentication & Security
- `auth` – Authentication utilities (token/session helpers)
- `rbac` – Role-based access control helpers
- `forms` – Reusable form components and validation wrappers

### Platform Integrations
- `service-registry` – Service discovery and health monitoring integration
- `audit-trail` – Audit logging and compliance monitoring integration
- `distributed-locks` – Distributed locking and optimistic updates

### Utilities & Assets
- `notifications` – Reusable notification utilities
- `assets` – Shared icons, illustrations, and asset pipeline helpers
- `utils` – General-purpose helpers

### Development Tools
- `testing` – Testing utilities/configuration
- `typescript-config` – TypeScript configuration presets
- `eslint-config` – ESLint configuration presets

Domain-specific packages (CRM, billing, etc.) remain excluded so this workspace focuses on reusable UI and service layers only.

## Base Next.js App

The starter located under `apps/base-app` demonstrates how to:

- Hydrate the shared providers (auth, notifications, React Query)
- Call the API gateway and render analytics widgets
- Provide a ready-made sign-in and dashboard experience

Update `.env.example`, tweak the theme, and extend the dashboard to build a new
DotMac product quickly.

## Syncing With Upstream

When the upstream `dotmac_framework` repository changes, copy only the relevant
packages from `frontend/shared/packages/` into this workspace and regenerate the
API client if the backend changes.

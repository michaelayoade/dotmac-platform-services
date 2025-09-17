# DotMac Base App

A production-ready Next.js starter that wires the DotMac platform frontend
packages out of the box. It includes:

- Authentication via `@dotmac/auth` and shared providers
- React Query + generated HTTP client (`@dotmac/http-client`)
- UI primitives, analytics dashboard, and notification system
- Example dashboard and sign-in flows ready to customize

## Getting Started

```bash
cd frontend/apps/base-app
pnpm install      # installs local dependencies
pnpm dev          # start Next.js on http://localhost:3000
```

Set the required environment variables (see `.env.example`) to point at your
API gateway and WebSocket endpoints. By default the app expects the platform to
be running locally on ports 8000/8001.

## Structure

```
app/
  page.tsx            # Landing page showcasing platform integrations
  dashboard/page.tsx  # Authenticated example dashboard
  (auth)/login/page.tsx
  api/platform/summary # Aggregates health & metrics from the platform gateway
providers/ClientProviders.tsx # Wraps React Query, Auth and Notifications
lib/config.ts         # Environment-aware platform configuration
```

## Customization

1. Update `globals.css` or extend the shared theme in `design-system` to match
your brand.
2. Replace the mock API route with real calls to your backend.
3. Extend dashboard widgets using `@dotmac/analytics`, `@dotmac/data-tables`,
and other shared packages.

## Scripts

- `pnpm dev` – Start the Next.js development server
- `pnpm build` – Production build
- `pnpm start` – Run the production server
- `pnpm lint` – Run Next.js linting
- `pnpm type-check` – Run TypeScript in noEmit mode

This app is intended as the baseline for new DotMac products—clone it, adjust
the theme, point to your environment, and build.

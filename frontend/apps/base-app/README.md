# DotMac Base App

A production-ready Next.js 14 starter with full DotMac Platform Services integration.

## Features

✅ **Authentication** - JWT auth with session management & MFA support
✅ **API Client** - Type-safe HTTP client with auto token refresh
✅ **Real-time** - WebSocket support for live updates
✅ **UI Components** - 26+ pre-built packages (design system, forms, notifications)
✅ **State Management** - React Query v5 with caching
✅ **Dark Mode** - Theme switching built-in
✅ **TypeScript** - Full type safety with strict mode

## Quick Start

```bash
# 1. Copy environment variables
cp .env.example .env

# 2. Install dependencies
pnpm install

# 3. Start development server
pnpm dev          # Runs on http://localhost:3000
```

**Prerequisite**: Backend API should be running at `http://localhost:8000`

## Project Structure

```
app/                    # Next.js 14 App Router
├── page.tsx           # Homepage with API health check
├── layout.tsx         # Root layout with providers
├── auth/              # Authentication pages
└── dashboard/         # Protected dashboard pages

lib/                   # Utilities and configuration
├── config.ts          # Environment configuration
└── http-client.ts     # Pre-configured API client

providers/             # React providers
└── ClientProviders.tsx # All client-side providers
```

## Available Packages

This app has access to 26+ packages from the monorepo:

- `@dotmac/auth` - Authentication with JWT & MFA
- `@dotmac/http-client` - Type-safe API client
- `@dotmac/ui` - Component library
- `@dotmac/design-system` - Design tokens & theming
- `@dotmac/notifications` - Toast notifications
- `@dotmac/analytics` - Analytics tracking
- `@dotmac/file-upload` - File upload components
- And many more...

## Scripts

```bash
pnpm dev        # Start development server
pnpm build      # Build for production
pnpm start      # Start production server
pnpm lint       # Run ESLint
pnpm type-check # Check TypeScript types
pnpm clean      # Clean build artifacts
```

## Environment Variables

```env
# Required
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
NEXT_PUBLIC_ENVIRONMENT=development

# Optional
NEXT_PUBLIC_ANALYTICS_ID=your-analytics-id
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

## Customization

1. **Theme**: Edit `tailwind.config.ts` and `app/globals.css`
2. **Auth**: Choose provider variant in `ClientProviders.tsx` (Simple/Secure/Enterprise)
3. **API**: Update endpoints in `lib/config.ts`
4. **Pages**: Add your routes in the `app/` directory

## Production Deployment

### Docker
```bash
docker build -t my-app .
docker run -p 3000:3000 my-app
```

### Vercel
```bash
vercel deploy
```

### Manual
```bash
pnpm build
pnpm start
```

## Next Steps

1. Set up your backend API at `localhost:8000`
2. Copy `.env.example` to `.env` and configure
3. Customize branding and theme
4. Add your business logic and pages
5. Deploy to production

---

Built with the DotMac Platform Services boilerplate.

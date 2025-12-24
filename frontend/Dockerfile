# DotMac Platform Services Frontend Dockerfile
# Build from the root of the monorepo
FROM node:20-alpine AS base

# Enable corepack for pnpm
RUN corepack enable

# Dependencies stage
FROM base AS deps
WORKDIR /app

# Copy workspace config and package files
COPY pnpm-workspace.yaml ./
COPY package.json ./frontend/package.json
COPY packages ./packages

# Install dependencies at monorepo root
RUN cd /app && pnpm install --filter @dotmac/platform-dashboard...

# Builder stage
FROM base AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/frontend/node_modules ./frontend/node_modules
COPY --from=deps /app/packages ./packages
COPY . ./frontend

# Build arguments for environment variables
ARG NEXT_PUBLIC_API_URL=http://localhost:8001
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8001
ARG NEXT_PUBLIC_WS_URL=ws://localhost:8001
ARG NEXTAUTH_SECRET=dev-secret
ARG NEXTAUTH_URL=http://localhost:3002

ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL
ENV NEXTAUTH_SECRET=$NEXTAUTH_SECRET
ENV NEXTAUTH_URL=$NEXTAUTH_URL

# Build the application
WORKDIR /app/frontend
RUN pnpm build

# Runner stage
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built application
COPY --from=builder /app/frontend/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/frontend/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/frontend/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]

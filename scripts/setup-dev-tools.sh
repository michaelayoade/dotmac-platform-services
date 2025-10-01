#!/bin/bash

echo "🔧 Setting up development tools..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Install Python dependencies
echo "📦 Installing Python dependencies..."
poetry install --with dev

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
pnpm install

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
cd apps/base-app
npx playwright install

# Initialize Husky
echo "🪝 Setting up git hooks..."
cd ../../..
npx husky install

# Set up MSW
echo "🎭 Setting up Mock Service Worker..."
cd frontend/apps/base-app
npx msw init public/ --save

# Create .env files if they don't exist
echo "📝 Creating environment files..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo -e "${YELLOW}Created .env from .env.example - please update with your values${NC}"
fi

if [ ! -f frontend/apps/base-app/.env.local ]; then
  cat > frontend/apps/base-app/.env.local << EOF
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Mock API (set to true to use mocked responses)
NEXT_PUBLIC_MOCK_API=false

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=false
NEXT_PUBLIC_ENABLE_MONITORING=false
EOF
  echo -e "${YELLOW}Created frontend/.env.local - please update if needed${NC}"
fi

echo ""
echo -e "${GREEN}✨ Development tools setup complete!${NC}"
echo ""
echo "📚 Quick Start Guide:"
echo "  1. Start backend:     make run-dev"
echo "  2. Start frontend:    cd frontend/apps/base-app && pnpm dev"
echo "  3. With mocks:        cd frontend/apps/base-app && pnpm dev:mock"
echo "  4. Run E2E tests:     cd frontend/apps/base-app && pnpm test:e2e"
echo "  5. Open Storybook:    cd frontend/apps/base-app && pnpm storybook"
echo "  6. Seed database:     make seed-db"
echo ""
echo "🎯 Pre-commit hooks are now active!"
echo "  - Python: formatting, linting, fast tests"
echo "  - Frontend: ESLint, Prettier, TypeScript"
echo "  - Commit messages: Conventional Commits format"
echo ""
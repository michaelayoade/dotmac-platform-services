#!/bin/bash

echo "🔧 Configurable Frontend Test Script"
echo "====================================="
echo

# Load configuration from .env.test or use defaults
if [ -f ".env.test" ]; then
  source .env.test
  echo "✅ Loaded configuration from .env.test"
else
  # Default configuration
  FRONTEND_PORT=${FRONTEND_PORT:-3000}
  BACKEND_PORT=${BACKEND_PORT:-8001}
  echo "ℹ️  Using default ports (Frontend: $FRONTEND_PORT, Backend: $BACKEND_PORT)"
  echo "   Create .env.test to customize ports"
fi

echo

# Function to check if a port is open
check_port() {
  local port=$1
  local service=$2
  nc -z localhost $port 2>/dev/null
  if [ $? -eq 0 ]; then
    echo "✅ $service is running on port $port"
    return 0
  else
    echo "❌ $service is not running on port $port"
    return 1
  fi
}

# Check services
check_port $FRONTEND_PORT "Frontend" || {
  echo "   Please start the frontend with: npm run dev"
  echo "   Or update FRONTEND_PORT in .env.test"
}

check_port $BACKEND_PORT "Backend" || {
  echo "   Please start the backend with: uvicorn dotmac.platform.main:app --port $BACKEND_PORT"
  echo "   Or update BACKEND_PORT in .env.test"
}

echo
echo "Running Tests..."
echo "----------------"

# Test 1: Backend Health
echo
echo "1. Backend Health Check"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:${BACKEND_PORT}/health)
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
BODY=$(echo "$HEALTH_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ Backend healthy (HTTP $HTTP_CODE)"
  if echo "$BODY" | jq -e '.status' > /dev/null 2>&1; then
    STATUS=$(echo "$BODY" | jq -r '.status')
    echo "   Status: $STATUS"
  fi
else
  echo "❌ Backend health check failed (HTTP $HTTP_CODE)"
fi

# Test 2: Frontend to Backend Proxy
echo
echo "2. Frontend Proxy Test"
PROXY_RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:${FRONTEND_PORT}/api/v1/health)
PROXY_CODE=$(echo "$PROXY_RESPONSE" | tail -n1)

if [ "$PROXY_CODE" = "200" ]; then
  echo "✅ Frontend proxy working (HTTP $PROXY_CODE)"
else
  echo "⚠️  Frontend proxy returned HTTP $PROXY_CODE"
  echo "   Check next.config.mjs rewrites configuration"
fi

# Test 3: Authentication Flow
echo
echo "3. Authentication Test"
# Login and save cookies
LOGIN_RESP=$(curl -s -X POST http://localhost:${BACKEND_PORT}/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' \
  -c /tmp/test-cookies.txt)

if echo "$LOGIN_RESP" | jq -e '.access_token' > /dev/null 2>&1; then
  echo "✅ Login successful"

  # Test authenticated endpoint
  ME_RESP=$(curl -s http://localhost:${BACKEND_PORT}/api/v1/auth/me \
    -b /tmp/test-cookies.txt)

  if echo "$ME_RESP" | jq -e '.user_id' > /dev/null 2>&1; then
    USER_ID=$(echo "$ME_RESP" | jq -r '.user_id')
    echo "✅ Auth verification successful (User: $USER_ID)"
  else
    echo "❌ Auth verification failed"
  fi
else
  echo "❌ Login failed"
fi

# Test 4: Frontend Pages
echo
echo "4. Frontend Pages Test"
PAGES=(
  "/:Home"
  "/login:Login"
  "/register:Register"
  "/dashboard:Dashboard"
)

for page_info in "${PAGES[@]}"; do
  IFS=':' read -r path name <<< "$page_info"
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${FRONTEND_PORT}${path})

  if [ "$STATUS" = "200" ]; then
    echo "✅ $name page accessible (HTTP $STATUS)"
  elif [ "$STATUS" = "500" ]; then
    echo "⚠️  $name page has server error (HTTP $STATUS)"
  elif [ "$STATUS" = "404" ]; then
    echo "❌ $name page not found (HTTP $STATUS)"
  else
    echo "❌ $name page error (HTTP $STATUS)"
  fi
done

# Test 5: Frontend Auth Implementation
echo
echo "5. Frontend Implementation Checks"

# Check if landing page uses auth API
HOME_PAGE=$(curl -s http://localhost:${FRONTEND_PORT}/ 2>/dev/null)
if echo "$HOME_PAGE" | grep -q "/api/v1/auth/me"; then
  echo "✅ Landing page has auth detection"
else
  echo "⚠️  Landing page missing auth detection"
fi

# Check for test IDs (if login page renders)
LOGIN_PAGE=$(curl -s http://localhost:${FRONTEND_PORT}/login 2>/dev/null)
if echo "$LOGIN_PAGE" | grep -q "500"; then
  echo "⚠️  Login page has rendering error"
else
  TEST_IDS=("login-form" "email-input" "password-input" "login-button")
  FOUND=0
  for id in "${TEST_IDS[@]}"; do
    if echo "$LOGIN_PAGE" | grep -q "data-testid=\"$id\""; then
      ((FOUND++))
    fi
  done

  if [ $FOUND -eq ${#TEST_IDS[@]} ]; then
    echo "✅ All E2E test IDs present ($FOUND/${#TEST_IDS[@]})"
  else
    echo "⚠️  Missing E2E test IDs ($FOUND/${#TEST_IDS[@]} found)"
  fi
fi

echo
echo "====================================="
echo "Test Summary"
echo "====================================="
echo "Configuration:"
echo "  Frontend: http://localhost:$FRONTEND_PORT"
echo "  Backend:  http://localhost:$BACKEND_PORT"
echo
echo "Frontend Architecture Fixes Applied:"
echo "  1. Landing page auth detection via API"
echo "  2. Login form E2E test selectors"
echo "  3. Removed legacy http-client imports"
echo "  4. Consistent cookie-based authentication"
echo
echo "To customize ports, edit .env.test"
echo "====================================="
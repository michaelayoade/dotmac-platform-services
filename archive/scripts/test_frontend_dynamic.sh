#!/bin/bash

echo "🔧 Dynamic Frontend Test Script"
echo "==============================="
echo

# Detect ports dynamically
FRONTEND_PORT=$(lsof -i :3000,3001 -P -n | grep LISTEN | head -1 | awk '{print $9}' | cut -d: -f2)
BACKEND_PORT=$(lsof -i :8000,8001,8002 -P -n | grep LISTEN | grep -iE "uvicorn|python" | head -1 | awk '{print $9}' | cut -d: -f2)

if [ -z "$FRONTEND_PORT" ]; then
  echo "❌ No frontend server detected on ports 3000-3001"
  echo "   Please start the frontend with: npm run dev"
  exit 1
fi

if [ -z "$BACKEND_PORT" ]; then
  echo "❌ No backend server detected on ports 8000-8002"
  echo "   Please start the backend with: uvicorn dotmac.platform.main:app"
  exit 1
fi

echo "✅ Frontend detected on port: $FRONTEND_PORT"
echo "✅ Backend detected on port: $BACKEND_PORT"
echo

# Test 1: Backend health check
echo "1. Testing Backend Health..."
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${BACKEND_PORT}/health)
if [ "$BACKEND_HEALTH" = "200" ]; then
  echo "✅ Backend is healthy (HTTP $BACKEND_HEALTH)"
else
  echo "❌ Backend health check failed (HTTP $BACKEND_HEALTH)"
fi

# Test 2: Frontend proxy to backend
echo
echo "2. Testing Frontend Proxy to Backend..."
# Frontend proxies /api/v1/* to backend
PROXY_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${FRONTEND_PORT}/api/v1/health)
if [ "$PROXY_TEST" = "200" ]; then
  echo "✅ Frontend proxy working (HTTP $PROXY_TEST)"
else
  echo "⚠️  Frontend proxy may not be configured (HTTP $PROXY_TEST)"
fi

# Test 3: Authentication flow
echo
echo "3. Testing Authentication Flow..."
# Login directly to backend
LOGIN_RESPONSE=$(curl -X POST http://localhost:${BACKEND_PORT}/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' \
  -c /tmp/dynamic-test-cookies.txt \
  -s)

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
  echo "✅ Login successful via backend"

  # Test authenticated request
  USER_INFO=$(curl -s http://localhost:${BACKEND_PORT}/api/v1/auth/me \
    -b /tmp/dynamic-test-cookies.txt)

  if echo "$USER_INFO" | grep -q "user_id"; then
    echo "✅ Authenticated request successful"
  else
    echo "❌ Authenticated request failed"
  fi
else
  echo "❌ Login failed"
fi

# Test 4: Frontend pages
echo
echo "4. Testing Frontend Pages..."
# Use detected frontend port
PAGES=("/" "/login" "/register")
for page in "${PAGES[@]}"; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${FRONTEND_PORT}${page})
  if [ "$STATUS" = "200" ]; then
    echo "✅ Page $page accessible (HTTP $STATUS)"
  else
    echo "❌ Page $page error (HTTP $STATUS)"
  fi
done

# Test 5: Landing page auth detection
echo
echo "5. Testing Landing Page Auth Detection..."
LANDING_PAGE=$(curl -s http://localhost:${FRONTEND_PORT}/)

# Check if the landing page has the auth check code
if echo "$LANDING_PAGE" | grep -q "/api/v1/auth/me"; then
  echo "✅ Landing page includes auth detection code"
else
  echo "⚠️  Landing page may not have auth detection"
fi

# Test 6: Login form test IDs
echo
echo "6. Testing Login Form Test IDs..."
LOGIN_PAGE=$(curl -s http://localhost:${FRONTEND_PORT}/login 2>/dev/null || echo "")

if [ -z "$LOGIN_PAGE" ] || echo "$LOGIN_PAGE" | grep -q "Error"; then
  echo "⚠️  Login page not rendering correctly"
else
  test_ids=("login-form" "email-input" "password-input" "login-button")
  found_count=0

  for id in "${test_ids[@]}"; do
    if echo "$LOGIN_PAGE" | grep -q "data-testid=\"$id\""; then
      ((found_count++))
    fi
  done

  if [ $found_count -eq ${#test_ids[@]} ]; then
    echo "✅ All test IDs present ($found_count/${#test_ids[@]})"
  else
    echo "⚠️  Only $found_count/${#test_ids[@]} test IDs found"
  fi
fi

echo
echo "==============================="
echo "Summary:"
echo "- Frontend on port: $FRONTEND_PORT"
echo "- Backend on port: $BACKEND_PORT"
echo "- Proxy configuration: Check next.config.js rewrites"
echo
echo "Frontend fixes applied:"
echo "1. Landing page uses /api/v1/auth/me for auth detection"
echo "2. Login form has data-testid attributes for E2E tests"
echo "3. Removed legacy http-client.ts imports"
echo "4. API client uses consistent cookie-based auth"
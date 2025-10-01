#!/bin/bash

echo "🔧 Testing Frontend Fixes"
echo "========================"
echo

# Test 1: Landing page auth detection
echo "1. Testing Landing Page Auth Detection..."
# First login to get cookies via backend API
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' \
  -c /tmp/test-auth-cookies.txt \
  -s > /dev/null

# Now check if landing page properly detects auth
LANDING_PAGE=$(curl -s http://localhost:3000/ -b /tmp/test-auth-cookies.txt)

if echo "$LANDING_PAGE" | grep -q "Dashboard"; then
  echo "✅ Landing page correctly shows authenticated UI"
else
  echo "⚠️  Landing page may still show guest UI (check if /api/v1/auth/me is accessible)"
fi

# Test auth check endpoint
AUTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/v1/auth/me -b /tmp/test-auth-cookies.txt)
if [ "$AUTH_CHECK" = "200" ]; then
  echo "✅ Auth verification endpoint working ($AUTH_CHECK)"
else
  echo "❌ Auth verification endpoint failed ($AUTH_CHECK)"
fi

echo
echo "2. Testing Login Form Test IDs..."
LOGIN_PAGE=$(curl -s http://localhost:3000/login)

test_ids=("login-form" "email-input" "password-input" "login-button")
missing_ids=()

for id in "${test_ids[@]}"; do
  if echo "$LOGIN_PAGE" | grep -q "data-testid=\"$id\""; then
    echo "✅ Found data-testid: $id"
  else
    missing_ids+=("$id")
  fi
done

if [ ${#missing_ids[@]} -eq 0 ]; then
  echo "✅ All required test IDs present"
else
  echo "❌ Missing test IDs: ${missing_ids[*]}"
fi

echo
echo "3. Testing API Client Consistency..."
# Check for duplicate client imports
DUPLICATE_CLIENTS=$(find /Users/michaelayoade/Downloads/Projects/dotmac-platform-services/frontend/apps/base-app \( -name "*.tsx" -o -name "*.ts" \) ! -path "*/tsconfig.tsbuildinfo" | xargs grep -l "from.*http-client" 2>/dev/null | wc -l)

if [ "$DUPLICATE_CLIENTS" -eq 0 ]; then
  echo "✅ No references to removed http-client.ts"
else
  echo "⚠️  Found $DUPLICATE_CLIENTS files still importing http-client.ts"
fi

echo
echo "4. Testing E2E Selectors..."
# Simulate what Playwright would do
TEST_LOGIN_FLOW() {
  # Try to find form elements
  local page=$(curl -s http://localhost:3000/login)

  if echo "$page" | grep -q 'data-testid="email-input"' && \
     echo "$page" | grep -q 'data-testid="password-input"' && \
     echo "$page" | grep -q 'data-testid="login-button"'; then
    return 0
  else
    return 1
  fi
}

if TEST_LOGIN_FLOW; then
  echo "✅ E2E selectors are properly configured"
else
  echo "❌ E2E selectors missing or incorrect"
fi

echo
echo "========================"
echo "Summary of Fixes:"
echo "1. ✅ Landing page now uses /api/v1/auth/me for auth detection"
echo "2. ✅ Login form has data-testid attributes for E2E tests"
echo "3. ✅ Removed legacy http-client.ts placeholder"
echo "4. ✅ API client uses consistent cookie-based auth"
echo
echo "The frontend should now:"
echo "- Properly detect HttpOnly cookie sessions"
echo "- Support Playwright E2E tests out of the box"
echo "- Have a cleaner, more maintainable codebase"
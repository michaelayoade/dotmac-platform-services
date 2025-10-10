#!/bin/bash
# CORS Cookie Authentication Testing Script
# Tests all aspects of cookie-based authentication

set -e

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_ORIGIN="${FRONTEND_ORIGIN:-http://localhost:3000}"
TEST_USER="${TEST_USER:-test@example.com}"
TEST_PASS="${TEST_PASS:-password}"

echo "====================================="
echo "CORS Cookie Authentication Test"
echo "====================================="
echo "Backend URL: $BACKEND_URL"
echo "Frontend Origin: $FRONTEND_ORIGIN"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
test_step() {
    local step_name="$1"
    local step_number="$2"
    echo ""
    echo "-----------------------------------"
    echo "Test $step_number: $step_name"
    echo "-----------------------------------"
}

pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
}

fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
}

warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
}

# Test 1: Backend Health Check
test_step "Backend Health Check" "1"
if curl -s "$BACKEND_URL/health" > /dev/null 2>&1; then
    pass "Backend is running"
    HEALTH_RESPONSE=$(curl -s "$BACKEND_URL/health")
    echo "Response: $HEALTH_RESPONSE"
else
    fail "Backend is not running at $BACKEND_URL"
    echo "Start the backend with: make dev-backend"
    exit 1
fi

# Test 2: CORS Preflight
test_step "CORS Preflight (OPTIONS)" "2"
CORS_RESPONSE=$(curl -s -I -X OPTIONS "$BACKEND_URL/api/v1/auth/login/cookie" \
    -H "Origin: $FRONTEND_ORIGIN" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: Content-Type")

if echo "$CORS_RESPONSE" | grep -q "Access-Control-Allow-Origin"; then
    ALLOW_ORIGIN=$(echo "$CORS_RESPONSE" | grep -i "Access-Control-Allow-Origin" | tr -d '\r')
    pass "CORS Allow-Origin present"
    echo "  $ALLOW_ORIGIN"

    if echo "$ALLOW_ORIGIN" | grep -q "$FRONTEND_ORIGIN"; then
        pass "Origin matches frontend ($FRONTEND_ORIGIN)"
    else
        warn "Origin doesn't match frontend. Got: $ALLOW_ORIGIN"
        echo "Add $FRONTEND_ORIGIN to CORS__ORIGINS in .env"
    fi
else
    fail "Access-Control-Allow-Origin header missing"
    echo "Check CORS configuration in .env:"
    echo "  CORS__ENABLED=true"
    echo "  CORS__ORIGINS='[\"$FRONTEND_ORIGIN\",\"http://localhost:8000\"]'"
fi

if echo "$CORS_RESPONSE" | grep -q "Access-Control-Allow-Credentials: true"; then
    pass "CORS Allow-Credentials enabled"
else
    fail "Access-Control-Allow-Credentials not set to true"
    echo "Set CORS__CREDENTIALS=true in .env"
fi

# Test 3: Login Endpoint (Test Credentials)
test_step "Login Endpoint" "3"
echo "Testing login with credentials: $TEST_USER / $TEST_PASS"
echo "Note: This may fail if user doesn't exist - that's okay for this test"

LOGIN_RESPONSE=$(curl -s -i -X POST "$BACKEND_URL/api/v1/auth/login/cookie" \
    -H "Origin: $FRONTEND_ORIGIN" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$TEST_USER\",\"password\":\"$TEST_PASS\"}" 2>&1)

# Check for Set-Cookie headers
if echo "$LOGIN_RESPONSE" | grep -iq "Set-Cookie:.*access_token"; then
    pass "Access token cookie is set"
    echo "$LOGIN_RESPONSE" | grep -i "Set-Cookie:.*access_token" | head -1
else
    warn "Access token cookie not found in response"
    if echo "$LOGIN_RESPONSE" | grep -q "401"; then
        echo "  Reason: Invalid credentials (401)"
        echo "  Create test user with: make seed-db"
    elif echo "$LOGIN_RESPONSE" | grep -q "404"; then
        echo "  Reason: Endpoint not found (404)"
        echo "  Check backend routing"
    else
        echo "  Check login endpoint implementation"
    fi
fi

if echo "$LOGIN_RESPONSE" | grep -iq "Set-Cookie:.*refresh_token"; then
    pass "Refresh token cookie is set"
else
    warn "Refresh token cookie not found"
fi

# Check CORS headers in login response
if echo "$LOGIN_RESPONSE" | grep -iq "Access-Control-Allow-Origin"; then
    pass "CORS headers present in login response"
    echo "$LOGIN_RESPONSE" | grep -i "Access-Control-Allow-Origin" | head -1
else
    fail "CORS headers missing from login response"
fi

if echo "$LOGIN_RESPONSE" | grep -iq "Access-Control-Allow-Credentials: true"; then
    pass "Credentials allowed in login response"
else
    fail "Access-Control-Allow-Credentials missing or not true"
fi

# Test 4: Cookie Attributes
test_step "Cookie Security Attributes" "4"
COOKIE_LINE=$(echo "$LOGIN_RESPONSE" | grep -i "Set-Cookie:.*access_token" | head -1)

if echo "$COOKIE_LINE" | grep -q "HttpOnly"; then
    pass "HttpOnly flag set (prevents XSS)"
else
    warn "HttpOnly flag not set"
fi

if echo "$COOKIE_LINE" | grep -q "SameSite"; then
    SAMESITE_VALUE=$(echo "$COOKIE_LINE" | grep -oP "SameSite=\K[^;]+")
    pass "SameSite attribute set: $SAMESITE_VALUE"
else
    warn "SameSite attribute not set"
fi

if echo "$COOKIE_LINE" | grep -q "Path=/"; then
    pass "Path set to / (available for all routes)"
else
    warn "Path not set correctly"
fi

# Test 5: Environment Configuration
test_step "Environment Configuration" "5"
if [ -f ".env" ]; then
    pass ".env file exists"

    if grep -q "CORS__ENABLED=true" .env; then
        pass "CORS enabled in .env"
    else
        fail "CORS not enabled in .env"
        echo "Add: CORS__ENABLED=true"
    fi

    if grep -q "CORS__CREDENTIALS=true" .env; then
        pass "CORS credentials enabled in .env"
    else
        fail "CORS credentials not enabled"
        echo "Add: CORS__CREDENTIALS=true"
    fi

    if grep -q "CORS__ORIGINS" .env; then
        ORIGINS_LINE=$(grep "CORS__ORIGINS" .env)
        pass "CORS origins configured"
        echo "  $ORIGINS_LINE"

        if echo "$ORIGINS_LINE" | grep -q "$FRONTEND_ORIGIN"; then
            pass "Frontend origin ($FRONTEND_ORIGIN) in whitelist"
        else
            warn "Frontend origin not in whitelist"
            echo "Update CORS__ORIGINS to include: $FRONTEND_ORIGIN"
        fi
    else
        fail "CORS origins not configured"
        echo "Add: CORS__ORIGINS='[\"$FRONTEND_ORIGIN\",\"http://localhost:8000\"]'"
    fi
else
    fail ".env file not found"
    echo "Copy .env.example to .env and configure"
fi

# Summary
echo ""
echo "====================================="
echo "Test Summary"
echo "====================================="
echo ""
echo "Backend URL: $BACKEND_URL"
echo "Frontend Origin: $FRONTEND_ORIGIN"
echo ""
echo "Next Steps:"
echo "1. If tests failed, check the error messages above"
echo "2. Update .env file with correct CORS configuration"
echo "3. Restart backend: make dev-backend"
echo "4. Run this script again to verify"
echo ""
echo "Frontend Requirements:"
echo "  • Use credentials: 'include' in all fetch() calls"
echo "  • Check browser console for CORS errors"
echo "  • Check Network tab for Set-Cookie headers"
echo "  • Check Application > Cookies for stored cookies"
echo ""
echo "Documentation: docs/CORS_COOKIE_AUTH_GUIDE.md"
echo "====================================="

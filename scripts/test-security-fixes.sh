#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000"
API_BASE="${BASE_URL}/api/v1"

echo -e "${YELLOW}=== Security Fixes Validation ===${NC}"
echo "Testing partner portal, audit, and file storage tenant enforcement"
echo ""

# Function to make API call and check response
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local headers="$4"
    local expected_status="$5"
    local data="$6"

    echo -e "${YELLOW}Testing: $name${NC}"

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" -X GET "$endpoint" $headers)
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$endpoint" $headers -H "Content-Type: application/json" -d "$data")
    elif [ "$method" = "DELETE" ]; then
        response=$(curl -s -w "\n%{http_code}" -X DELETE "$endpoint" $headers)
    fi

    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} - Status: $http_code"
        echo "Response: $body" | head -c 200
        echo ""
    else
        echo -e "${RED}✗ FAIL${NC} - Expected: $expected_status, Got: $http_code"
        echo "Response: $body"
        echo ""
        return 1
    fi
}

echo -e "${YELLOW}=== 1. Partner Portal Security Tests ===${NC}"
echo ""

# Test 1: Partner portal without auth should fail with 401
test_endpoint \
    "Partner dashboard without authentication" \
    "GET" \
    "${API_BASE}/partners/portal/dashboard" \
    "" \
    "401" \
    ""

# Test 2: Partner portal without partner_id header (platform admin) should fail with 400
# First, we need to get a JWT token for platform admin
echo -e "${YELLOW}Getting platform admin token...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "${API_BASE}/auth/login/cookie" \
    -H "Content-Type: application/json" \
    -d '{"username":"admin@test.com","password":"Test123!@#"}')

# Extract cookies from response headers
COOKIES=$(echo "$LOGIN_RESPONSE" | grep -i "set-cookie" || echo "")

if [ -z "$COOKIES" ]; then
    echo -e "${RED}Could not get admin token - login may have failed${NC}"
    echo "Login response: $LOGIN_RESPONSE"
else
    echo -e "${GREEN}✓ Got admin token${NC}"
fi

# Test 3: Platform admin without X-Partner-ID should get 400
test_endpoint \
    "Partner portal as platform admin without X-Partner-ID" \
    "GET" \
    "${API_BASE}/partners/portal/dashboard" \
    "-H 'Cookie: $COOKIES'" \
    "400"

echo ""
echo -e "${YELLOW}=== 2. Audit Log Security Tests ===${NC}"
echo ""

# Test 4: Audit logs without authentication should fail with 401
test_endpoint \
    "Audit activities without authentication" \
    "GET" \
    "${API_BASE}/audit/activities" \
    "" \
    "401"

# Test 5: Audit logs with auth but without tenant context should require tenant_id
test_endpoint \
    "Audit activities with auth but no tenant context" \
    "GET" \
    "${API_BASE}/audit/activities" \
    "-H 'Cookie: $COOKIES'" \
    "400"

# Test 6: Recent activities without auth should fail
test_endpoint \
    "Recent activities without authentication" \
    "GET" \
    "${API_BASE}/audit/activities/recent" \
    "" \
    "401"

echo ""
echo -e "${YELLOW}=== 3. File Storage Security Tests ===${NC}"
echo ""

# Test 7: File upload without authentication should fail with 401
test_endpoint \
    "File upload without authentication" \
    "POST" \
    "${API_BASE}/files/storage/upload" \
    "" \
    "401"

# Test 8: File download without authentication should fail with 401
test_endpoint \
    "File download without authentication" \
    "GET" \
    "${API_BASE}/files/storage/test-file-id/download" \
    "" \
    "401"

# Test 9: File deletion without authentication should fail with 401
test_endpoint \
    "File deletion without authentication" \
    "DELETE" \
    "${API_BASE}/files/storage/test-file-id" \
    "" \
    "401"

# Test 10: File list without authentication should fail with 401
test_endpoint \
    "File list without authentication" \
    "GET" \
    "${API_BASE}/files/storage" \
    "" \
    "401"

# Test 11: Path traversal attempt (with auth)
echo -e "${YELLOW}Testing path traversal protection...${NC}"
test_endpoint \
    "Path traversal attempt with ../" \
    "GET" \
    "${API_BASE}/files/storage?path=../../etc/passwd" \
    "-H 'Cookie: $COOKIES'" \
    "400"

echo ""
echo -e "${GREEN}=== Security Tests Complete ===${NC}"
echo ""
echo "Summary:"
echo "- Partner portal: Requires authentication ✓"
echo "- Partner portal: Requires X-Partner-ID for platform admins ✓"
echo "- Audit logs: Requires authentication ✓"
echo "- Audit logs: Requires tenant context ✓"
echo "- File storage: Requires authentication ✓"
echo "- File storage: Blocks path traversal ✓"
echo ""

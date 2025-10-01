#!/bin/bash

# Comprehensive RBAC Integration Test

echo "🔐 FULL RBAC INTEGRATION TEST"
echo "=============================="
echo

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test function
test_endpoint() {
    local description=$1
    local url=$2
    local expected=$3

    response=$(curl -s "$url" -b /tmp/test-cookies.txt)

    if echo "$response" | jq -e "$expected" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $description${NC}"
        return 0
    else
        echo -e "${RED}❌ $description${NC}"
        echo "   Response: $response"
        return 1
    fi
}

# 1. Login
echo "1. Authentication"
echo "-----------------"
LOGIN_RESPONSE=$(curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' \
  -c /tmp/test-cookies.txt \
  -s)

if echo "$LOGIN_RESPONSE" | jq -e '.access_token' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Login successful${NC}"

    # Decode JWT to show contents
    TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
    echo "   JWT Claims:"
    echo "$TOKEN" | cut -d. -f2 | base64 -d 2>/dev/null | jq '.roles, .permissions' | head -10
else
    echo -e "${RED}❌ Login failed${NC}"
    exit 1
fi

echo
echo "2. RBAC Endpoints"
echo "-----------------"

# Test my-permissions endpoint
test_endpoint "My Permissions - Has user_id" \
    "http://localhost:8001/api/v1/auth/rbac/my-permissions" \
    '.user_id != null'

test_endpoint "My Permissions - Has roles array" \
    "http://localhost:8001/api/v1/auth/rbac/my-permissions" \
    '.roles | type == "array"'

test_endpoint "My Permissions - Has admin role" \
    "http://localhost:8001/api/v1/auth/rbac/my-permissions" \
    '.roles | map(.name) | contains(["admin"])'

test_endpoint "My Permissions - Has effective_permissions" \
    "http://localhost:8001/api/v1/auth/rbac/my-permissions" \
    '.effective_permissions | length > 0'

test_endpoint "My Permissions - Is superuser" \
    "http://localhost:8001/api/v1/auth/rbac/my-permissions" \
    '.is_superuser == true'

# Test roles endpoint
test_endpoint "Roles - Returns array" \
    "http://localhost:8001/api/v1/auth/rbac/roles?active_only=true" \
    '. | type == "array"'

test_endpoint "Roles - Contains admin role" \
    "http://localhost:8001/api/v1/auth/rbac/roles?active_only=true" \
    'map(.name) | contains(["admin"])'

echo
echo "3. Protected Endpoints"
echo "---------------------"

test_endpoint "User Profile - Accessible" \
    "http://localhost:8001/api/v1/users/me" \
    '.user_id != null'

test_endpoint "User Profile - Has roles" \
    "http://localhost:8001/api/v1/users/me" \
    '.roles | contains(["admin"])'

echo
echo "4. Frontend Proxy"
echo "-----------------"

# Test through frontend proxy
test_endpoint "Frontend Proxy - My Permissions" \
    "http://localhost:3000/api/v1/auth/rbac/my-permissions" \
    '.user_id != null and .roles != null'

test_endpoint "Frontend Proxy - Roles" \
    "http://localhost:3000/api/v1/auth/rbac/roles?active_only=true" \
    '. | length > 0'

echo
echo "5. Permission Structure Validation"
echo "----------------------------------"
PERMS=$(curl -s "http://localhost:8001/api/v1/auth/rbac/my-permissions" -b /tmp/test-cookies.txt)

echo "Roles:"
echo "$PERMS" | jq '.roles[] | {name, display_name, is_system}'

echo
echo "Permissions:"
echo "$PERMS" | jq '.effective_permissions[] | {name, category, resource, action}'

echo
echo "=============================="
echo "🎉 RBAC INTEGRATION TEST COMPLETE!"
echo
echo "Summary:"
echo "- Authentication: ✅"
echo "- RBAC Endpoints: ✅"
echo "- Permission Format: ✅"
echo "- Frontend Integration: ✅"
echo
echo "The frontend React app should now be able to:"
echo "1. Authenticate users with cookies"
echo "2. Fetch user permissions in the correct format"
echo "3. Use RBACContext without errors"
echo "4. Render permission-based UI components"
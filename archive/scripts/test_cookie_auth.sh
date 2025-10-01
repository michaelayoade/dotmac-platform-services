#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

API_BASE="http://localhost:8000/api/v1"
COOKIE_FILE="test_cookies.txt"

echo -e "${BLUE}=== Cookie Authentication Test Suite ===${NC}\n"

# Clean up old cookies
rm -f $COOKIE_FILE

echo -e "${BLUE}1. Testing Cookie-Only Login${NC}"
echo "   Endpoint: POST /api/v1/auth/login/cookie"
response=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE/auth/login/cookie" \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:3000" \
  -d '{"username":"testuser1","password":"TestPassword123!"}' \
  -c $COOKIE_FILE)

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    echo -e "   Status: ${GREEN}✓ Success (HTTP $http_code)${NC}"
    echo "   Response:"
    echo "$body" | jq '.' 2>/dev/null || echo "$body"
    echo "   Cookies saved to: $COOKIE_FILE"
else
    echo -e "   Status: ${RED}✗ Failed (HTTP $http_code)${NC}"
    echo "   Response: $body"
fi

echo -e "\n${BLUE}2. Checking Cookies Set${NC}"
echo "   Cookie file contents:"
cat $COOKIE_FILE | grep -E "access_token|refresh_token" | sed 's/^/   /'

echo -e "\n${BLUE}3. Testing /me Endpoint with Cookies${NC}"
echo "   Endpoint: GET /api/v1/auth/me"
response=$(curl -s -w "\n%{http_code}" -X GET "$API_BASE/auth/me" \
  -H "Origin: http://localhost:3000" \
  -b $COOKIE_FILE)

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    echo -e "   Status: ${GREEN}✓ Success (HTTP $http_code)${NC}"
    echo "   User info from cookie:"
    echo "$body" | jq '.' 2>/dev/null || echo "$body"
else
    echo -e "   Status: ${RED}✗ Failed (HTTP $http_code)${NC}"
    echo "   Response: $body"
fi

echo -e "\n${BLUE}4. Testing Regular Login (with token response)${NC}"
echo "   Endpoint: POST /api/v1/auth/login"
response=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE/auth/login" \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:3000" \
  -d '{"username":"testuser1","password":"TestPassword123!"}' \
  -c regular_cookies.txt)

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    echo -e "   Status: ${GREEN}✓ Success (HTTP $http_code)${NC}"
    echo "   Token in response body: $(echo "$body" | jq -r '.access_token' | head -c 50)..."
    echo "   Cookies also set: $(grep -c 'access_token' regular_cookies.txt) cookie(s)"
else
    echo -e "   Status: ${RED}✗ Failed (HTTP $http_code)${NC}"
    echo "   Response: $body"
fi

echo -e "\n${BLUE}5. Testing Logout with Cookies${NC}"
echo "   Endpoint: POST /api/v1/auth/logout"
response=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE/auth/logout" \
  -H "Origin: http://localhost:3000" \
  -b $COOKIE_FILE \
  -c logout_cookies.txt)

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    echo -e "   Status: ${GREEN}✓ Success (HTTP $http_code)${NC}"
    echo "   Response:"
    echo "$body" | jq '.' 2>/dev/null || echo "$body"
else
    echo -e "   Status: ${RED}✗ Failed (HTTP $http_code)${NC}"
    echo "   Response: $body"
fi

echo -e "\n${BLUE}6. Verifying Logout (should fail)${NC}"
echo "   Endpoint: GET /api/v1/auth/me (after logout)"
response=$(curl -s -w "\n%{http_code}" -X GET "$API_BASE/auth/me" \
  -H "Origin: http://localhost:3000" \
  -b logout_cookies.txt)

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "401" ]; then
    echo -e "   Status: ${GREEN}✓ Correctly rejected (HTTP $http_code)${NC}"
    echo "   Cookies were properly cleared"
else
    echo -e "   Status: ${RED}✗ Unexpected status (HTTP $http_code)${NC}"
    echo "   Response: $body"
fi

echo -e "\n${BLUE}=== Test Complete ===${NC}"

# Cleanup
rm -f $COOKIE_FILE regular_cookies.txt logout_cookies.txt
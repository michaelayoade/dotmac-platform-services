#!/bin/bash

# Test RBAC endpoints through frontend proxy

echo "🔐 Testing RBAC endpoints through frontend proxy..."
echo

# Login
echo "1. Logging in..."
LOGIN_RESPONSE=$(curl -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' \
  -c /tmp/test-cookies.txt \
  -s)

if echo "$LOGIN_RESPONSE" | jq -e '.access_token' > /dev/null; then
  echo "✅ Login successful"
else
  echo "❌ Login failed"
  echo "$LOGIN_RESPONSE" | jq
  exit 1
fi

echo
echo "2. Fetching permissions..."
PERMISSIONS=$(curl "http://localhost:3000/api/v1/auth/rbac/my-permissions" \
  -b /tmp/test-cookies.txt \
  -s)

echo "Permissions: $PERMISSIONS"

echo
echo "3. Fetching roles..."
ROLES=$(curl "http://localhost:3000/api/v1/auth/rbac/roles?active_only=true" \
  -b /tmp/test-cookies.txt \
  -s)

echo "Roles:"
echo "$ROLES" | jq

echo
echo "4. Testing protected endpoints..."
curl "http://localhost:3000/api/v1/users/me" \
  -b /tmp/test-cookies.txt \
  -i | head -10

echo
echo "✅ All tests completed!"
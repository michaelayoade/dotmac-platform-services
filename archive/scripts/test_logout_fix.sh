#!/bin/bash

# Test logout fix
echo "=== Testing Logout Fix ==="

# Step 1: Login to get fresh cookies
echo "1. Logging in to get fresh cookies..."
curl -X POST "http://localhost:8000/api/v1/auth/login/cookie" \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:3000" \
  -d '{"username":"testuser1","password":"TestPassword123!"}' \
  -c fresh_cookies.txt \
  -s > /dev/null

echo "2. Checking if we got cookies..."
cat fresh_cookies.txt | grep -E "access_token|refresh_token" | wc -l

echo "3. Testing /me endpoint with fresh cookies..."
response=$(curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Origin: http://localhost:3000" \
  -b fresh_cookies.txt \
  -w "%{http_code}" \
  -s)
echo "Response: ${response: -3}"

echo "4. Testing logout with fresh cookies..."
curl -X POST "http://localhost:8000/api/v1/auth/logout" \
  -H "Origin: http://localhost:3000" \
  -b fresh_cookies.txt \
  -c after_logout.txt \
  -w "\nHTTP Status: %{http_code}\n" \
  2>/dev/null

echo "5. Testing /me after logout (should fail)..."
response=$(curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Origin: http://localhost:3000" \
  -b after_logout.txt \
  -w "%{http_code}" \
  -s)
echo "Response: ${response: -3}"

# Cleanup
rm -f fresh_cookies.txt after_logout.txt
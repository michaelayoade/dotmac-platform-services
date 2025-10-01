#!/bin/bash

# Base URL
BASE_URL="http://localhost:8000"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print headers
print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

# Function to print test
print_test() {
    echo -e "\n${GREEN}$1${NC}"
}

# Test Health Endpoints
print_header "Health Check Endpoints"

print_test "1. Main health endpoint:"
curl -s $BASE_URL/health | jq .

print_test "2. Liveness check:"
curl -s $BASE_URL/health/live | jq .

print_test "3. Readiness check:"
curl -s $BASE_URL/health/ready | jq .

# Test Authentication Endpoints
print_header "Authentication Endpoints"

print_test "1. Register a new user:"
REGISTER_RESPONSE=$(curl -s -X POST $BASE_URL/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser1",
    "email": "test1@example.com",
    "password": "TestPassword123!",
    "full_name": "Test User"
  }')
echo "$REGISTER_RESPONSE" | jq .

# Extract token if registration was successful
ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | jq -r '.access_token // empty')

print_test "2. Login with the registered user:"
LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser1",
    "password": "TestPassword123!"
  }')
echo "$LOGIN_RESPONSE" | jq .

# Extract token from login if not from registration
if [ -z "$ACCESS_TOKEN" ]; then
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token // empty')
fi

if [ -n "$ACCESS_TOKEN" ]; then
    print_test "3. Verify token:"
    curl -s $BASE_URL/api/v1/auth/verify \
      -H "Authorization: Bearer $ACCESS_TOKEN" | jq .

    print_test "4. Get current user info:"
    curl -s $BASE_URL/api/v1/auth/me \
      -H "Authorization: Bearer $ACCESS_TOKEN" | jq .
fi

# Test Customer Management Endpoints
print_header "Customer Management Endpoints"

if [ -n "$ACCESS_TOKEN" ]; then
    print_test "1. Create a customer:"
    CUSTOMER_RESPONSE=$(curl -s -X POST $BASE_URL/api/v1/customers \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "email": "customer1@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "+1234567890",
        "company": "Test Corp"
      }')
    echo "$CUSTOMER_RESPONSE" | jq .

    CUSTOMER_ID=$(echo "$CUSTOMER_RESPONSE" | jq -r '.id // empty')

    if [ -n "$CUSTOMER_ID" ]; then
        print_test "2. Get customer by ID:"
        curl -s $BASE_URL/api/v1/customers/$CUSTOMER_ID \
          -H "Authorization: Bearer $ACCESS_TOKEN" | jq .

        print_test "3. Update customer:"
        curl -s -X PUT $BASE_URL/api/v1/customers/$CUSTOMER_ID \
          -H "Authorization: Bearer $ACCESS_TOKEN" \
          -H "Content-Type: application/json" \
          -d '{
            "company": "Updated Corp",
            "status": "active"
          }' | jq .

        print_test "4. Search customers:"
        curl -s "$BASE_URL/api/v1/customers/search?query=John" \
          -H "Authorization: Bearer $ACCESS_TOKEN" | jq .

        print_test "5. Add customer activity:"
        curl -s -X POST $BASE_URL/api/v1/customers/$CUSTOMER_ID/activities \
          -H "Authorization: Bearer $ACCESS_TOKEN" \
          -H "Content-Type: application/json" \
          -d '{
            "title": "Test Activity",
            "description": "Testing customer activity tracking"
          }' | jq .

        print_test "6. Get customer activities:"
        curl -s $BASE_URL/api/v1/customers/$CUSTOMER_ID/activities \
          -H "Authorization: Bearer $ACCESS_TOKEN" | jq .
    fi
fi

# Test API Documentation
print_header "API Documentation"

print_test "1. OpenAPI schema:"
curl -s $BASE_URL/openapi.json | jq '.info'

print_test "2. Check if Swagger UI is available:"
SWAGGER_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/docs)
echo "Swagger UI status: $SWAGGER_STATUS (200 = available)"

print_test "3. Check if ReDoc is available:"
REDOC_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/redoc)
echo "ReDoc status: $REDOC_STATUS (200 = available)"

# Test Other Core Endpoints
print_header "Other Core Endpoints"

if [ -n "$ACCESS_TOKEN" ]; then
    print_test "1. User Management - List users:"
    curl -s $BASE_URL/api/v1/users \
      -H "Authorization: Bearer $ACCESS_TOKEN" | jq .

    print_test "2. Secrets Management - List secrets (if authorized):"
    curl -s $BASE_URL/api/v1/secrets \
      -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.message // .detail // .'

    print_test "3. Analytics - Get metrics:"
    curl -s $BASE_URL/api/v1/analytics/metrics \
      -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.message // .detail // .'
fi

# Test Metrics Endpoint
print_header "Monitoring Endpoints"

print_test "1. Prometheus metrics (sample):"
curl -s $BASE_URL/metrics/ | head -20

print_test "2. Application info:"
curl -s $BASE_URL/api/v1/info 2>/dev/null | jq . || echo "Info endpoint not available"

print_header "Test Summary"
echo "All API endpoint tests completed!"
echo "Server is running at: $BASE_URL"
if [ -n "$ACCESS_TOKEN" ]; then
    echo "Authentication successful - token obtained"
else
    echo "Authentication may have issues - no token obtained"
fi
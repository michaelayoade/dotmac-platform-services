#!/bin/bash

# Test all API endpoints
# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000"
TOKEN=""
TEST_USER_ID=""
TEST_CUSTOMER_ID=""
TEST_CONTACT_ID=""

# Function to print test results
print_result() {
    local endpoint=$1
    local method=$2
    local status=$3
    local expected=$4

    if [ "$status" -eq "$expected" ]; then
        echo -e "${GREEN}✓${NC} ${method} ${endpoint} - Status: ${status}"
    else
        echo -e "${RED}✗${NC} ${method} ${endpoint} - Status: ${status} (Expected: ${expected})"
    fi
}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Testing DotMac Platform API Endpoints${NC}"
echo -e "${BLUE}========================================${NC}\n"

# 1. Health Check Endpoints (No Auth Required)
echo -e "${YELLOW}Testing Health Endpoints...${NC}"

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/health)
print_result "/health" "GET" "$status" 200

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/ready)
print_result "/ready" "GET" "$status" 200

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/metrics)
print_result "/metrics" "GET" "$status" 200

echo ""

# 2. Authentication Endpoints
echo -e "${YELLOW}Testing Authentication Endpoints...${NC}"

# Register a test user
REGISTER_DATA='{
  "email": "testuser@example.com",
  "password": "TestPassword123!",
  "username": "testuser"
}'

status=$(curl -s -o /tmp/register_response.json -w "%{http_code}" \
  -X POST ${BASE_URL}/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d "$REGISTER_DATA")
print_result "/api/v1/auth/register" "POST" "$status" 201

# Login
LOGIN_DATA='{
  "email": "testuser@example.com",
  "password": "TestPassword123!"
}'

response=$(curl -s -X POST ${BASE_URL}/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "$LOGIN_DATA")

status=$?
if [ $status -eq 0 ]; then
    TOKEN=$(echo $response | jq -r '.access_token // empty')
    if [ -n "$TOKEN" ]; then
        echo -e "${GREEN}✓${NC} POST /api/v1/auth/login - Token obtained"
    else
        echo -e "${YELLOW}⚠${NC} POST /api/v1/auth/login - Response received but no token"
    fi
else
    echo -e "${RED}✗${NC} POST /api/v1/auth/login - Failed"
fi

# Try with admin user if test user fails
if [ -z "$TOKEN" ]; then
    echo "Trying admin credentials..."
    ADMIN_LOGIN='{
      "email": "admin@example.com",
      "password": "admin123"
    }'

    response=$(curl -s -X POST ${BASE_URL}/api/v1/auth/login \
      -H "Content-Type: application/json" \
      -d "$ADMIN_LOGIN")

    TOKEN=$(echo $response | jq -r '.access_token // empty')
fi

# Test other auth endpoints
status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/auth/logout \
  -H "Authorization: Bearer ${TOKEN}")
print_result "/api/v1/auth/logout" "POST" "$status" 200

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/auth/me \
  -H "Authorization: Bearer ${TOKEN}")
print_result "/api/v1/auth/me" "GET" "$status" 200

echo ""

# 3. RBAC Endpoints
echo -e "${YELLOW}Testing RBAC Endpoints...${NC}"

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/auth/rbac/my-permissions \
  -H "Authorization: Bearer ${TOKEN}")
print_result "/api/v1/auth/rbac/my-permissions" "GET" "$status" 200

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/auth/rbac/roles \
  -H "Authorization: Bearer ${TOKEN}")
print_result "/api/v1/auth/rbac/roles" "GET" "$status" 200

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/auth/rbac/my-roles \
  -H "Authorization: Bearer ${TOKEN}")
print_result "/api/v1/auth/rbac/my-roles" "GET" "$status" 200

echo ""

# 4. API Keys
echo -e "${YELLOW}Testing API Key Endpoints...${NC}"

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/auth/api-keys \
  -H "Authorization: Bearer ${TOKEN}")
print_result "/api/v1/auth/api-keys" "GET" "$status" 200

echo ""

# 5. Users Management
echo -e "${YELLOW}Testing User Management Endpoints...${NC}"

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/users \
  -H "Authorization: Bearer ${TOKEN}")
print_result "/api/v1/users" "GET" "$status" 200

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/users/profile \
  -H "Authorization: Bearer ${TOKEN}")
print_result "/api/v1/users/profile" "GET" "$status" 200

echo ""

# 6. Customers
echo -e "${YELLOW}Testing Customer Endpoints...${NC}"

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/customers \
  -H "Authorization: Bearer ${TOKEN}")
print_result "/api/v1/customers" "GET" "$status" 200

# Create a test customer
CUSTOMER_DATA='{
  "name": "Test Customer",
  "email": "customer@example.com",
  "phone": "+1234567890",
  "company": "Test Company"
}'

response=$(curl -s -X POST ${BASE_URL}/api/v1/customers \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$CUSTOMER_DATA")

status=$?
if [ $status -eq 0 ]; then
    TEST_CUSTOMER_ID=$(echo $response | jq -r '.id // empty')
    if [ -n "$TEST_CUSTOMER_ID" ]; then
        echo -e "${GREEN}✓${NC} POST /api/v1/customers - Customer created"
    else
        echo -e "${YELLOW}⚠${NC} POST /api/v1/customers - Response received"
    fi
fi

echo ""

# 7. Contacts
echo -e "${YELLOW}Testing Contact Endpoints...${NC}"

# Search contacts
SEARCH_DATA='{
  "query": "",
  "page": 1,
  "page_size": 20
}'

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/contacts/search \
  -X POST \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$SEARCH_DATA")
print_result "/api/v1/contacts/search" "POST" "$status" 200

# Create a contact
CONTACT_DATA='{
  "first_name": "John",
  "last_name": "Doe",
  "company": "ACME Corp",
  "job_title": "CEO"
}'

response=$(curl -s -X POST ${BASE_URL}/api/v1/contacts/ \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$CONTACT_DATA")

status=$?
if [ $status -eq 0 ]; then
    TEST_CONTACT_ID=$(echo $response | jq -r '.id // empty')
    if [ -n "$TEST_CONTACT_ID" ]; then
        echo -e "${GREEN}✓${NC} POST /api/v1/contacts - Contact created"
    else
        echo -e "${YELLOW}⚠${NC} POST /api/v1/contacts - Response received"
    fi
fi

echo ""

# 8. Analytics
echo -e "${YELLOW}Testing Analytics Endpoints...${NC}"

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/analytics/events \
  -H "Authorization: Bearer ${TOKEN}")
print_result "/api/v1/analytics/events" "GET" "$status" 200

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/analytics/metrics \
  -H "Authorization: Bearer ${TOKEN}")
print_result "/api/v1/analytics/metrics" "GET" "$status" 200

echo ""

# 9. File Storage
echo -e "${YELLOW}Testing File Storage Endpoints...${NC}"

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/files/storage \
  -H "Authorization: Bearer ${TOKEN}")
print_result "/api/v1/files/storage" "GET" "$status" 200

echo ""

# 10. Communications
echo -e "${YELLOW}Testing Communications Endpoints...${NC}"

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/communications/templates \
  -H "Authorization: Bearer ${TOKEN}")
print_result "/api/v1/communications/templates" "GET" "$status" 200

echo ""

# 11. Search
echo -e "${YELLOW}Testing Search Endpoints...${NC}"

SEARCH_QUERY='{
  "query": "test",
  "limit": 10
}'

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/search \
  -X POST \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$SEARCH_QUERY")
print_result "/api/v1/search" "POST" "$status" 200

echo ""

# 12. Data Transfer
echo -e "${YELLOW}Testing Data Transfer Endpoints...${NC}"

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/data-transfer/exports \
  -H "Authorization: Bearer ${TOKEN}")
print_result "/api/v1/data-transfer/exports" "GET" "$status" 200

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/data-transfer/imports \
  -H "Authorization: Bearer ${TOKEN}")
print_result "/api/v1/data-transfer/imports" "GET" "$status" 200

echo ""

# 13. Feature Flags
echo -e "${YELLOW}Testing Feature Flags Endpoints...${NC}"

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/feature-flags \
  -H "Authorization: Bearer ${TOKEN}")
print_result "/api/v1/feature-flags" "GET" "$status" 200

echo ""

# 14. Secrets Management
echo -e "${YELLOW}Testing Secrets Endpoints...${NC}"

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/secrets \
  -H "Authorization: Bearer ${TOKEN}")
print_result "/api/v1/secrets" "GET" "$status" 200

echo ""

# 15. Billing
echo -e "${YELLOW}Testing Billing Endpoints...${NC}"

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/billing/invoices \
  -H "Authorization: Bearer ${TOKEN}")
print_result "/api/v1/billing/invoices" "GET" "$status" 200

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/billing/payments \
  -H "Authorization: Bearer ${TOKEN}")
print_result "/api/v1/billing/payments" "GET" "$status" 200

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/billing/catalog/products \
  -H "Authorization: Bearer ${TOKEN}")
print_result "/api/v1/billing/catalog/products" "GET" "$status" 200

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/billing/subscriptions \
  -H "Authorization: Bearer ${TOKEN}")
print_result "/api/v1/billing/subscriptions" "GET" "$status" 200

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/billing/pricing/rules \
  -H "Authorization: Bearer ${TOKEN}")
print_result "/api/v1/billing/pricing/rules" "GET" "$status" 200

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/billing/bank-accounts \
  -H "Authorization: Bearer ${TOKEN}")
print_result "/api/v1/billing/bank-accounts" "GET" "$status" 200

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/billing/settings \
  -H "Authorization: Bearer ${TOKEN}")
print_result "/api/v1/billing/settings" "GET" "$status" 200

echo ""

# 16. Audit
echo -e "${YELLOW}Testing Audit Endpoints...${NC}"

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/audit/logs \
  -H "Authorization: Bearer ${TOKEN}")
print_result "/api/v1/audit/logs" "GET" "$status" 200

echo ""

# 17. Admin Settings
echo -e "${YELLOW}Testing Admin Settings Endpoints...${NC}"

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/admin/settings \
  -H "Authorization: Bearer ${TOKEN}")
print_result "/api/v1/admin/settings" "GET" "$status" 200

echo ""

# 18. Plugin Management
echo -e "${YELLOW}Testing Plugin Endpoints...${NC}"

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/plugins \
  -H "Authorization: Bearer ${TOKEN}")
print_result "/api/v1/plugins" "GET" "$status" 200

echo ""

# 19. OpenAPI Documentation (No Auth Required)
echo -e "${YELLOW}Testing Documentation Endpoints...${NC}"

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/docs)
print_result "/docs" "GET" "$status" 200

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/redoc)
print_result "/redoc" "GET" "$status" 200

status=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/openapi.json)
print_result "/openapi.json" "GET" "$status" 200

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Testing Complete${NC}"
echo -e "${BLUE}========================================${NC}"
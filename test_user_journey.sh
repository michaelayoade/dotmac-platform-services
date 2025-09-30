#!/bin/bash

# Complete User Journey Test Script
# Tests Customer Management and Billing endpoints

# Base URL
BASE_URL="http://localhost:8000"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print headers
print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}   $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
}

# Function to print test
print_test() {
    echo -e "\n${GREEN}▶ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print info
print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Generate unique email for this test run
TIMESTAMP=$(date +%s)
TEST_EMAIL="journey_${TIMESTAMP}@test.com"
TEST_USERNAME="journey_${TIMESTAMP}"

print_header "COMPLETE USER JOURNEY TEST"
print_info "Test Email: $TEST_EMAIL"
print_info "Test Username: $TEST_USERNAME"

# ============================================
# PHASE 1: USER REGISTRATION AND AUTHENTICATION
# ============================================
print_header "PHASE 1: USER REGISTRATION & AUTHENTICATION"

print_test "1.1 Register a new user"
REGISTER_RESPONSE=$(curl -s -X POST $BASE_URL/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"$TEST_USERNAME\",
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"SecurePass123!\",
    \"full_name\": \"Journey Test User\"
  }")

echo "$REGISTER_RESPONSE" | jq '.' 2>/dev/null || echo "$REGISTER_RESPONSE"

# Extract token
ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | jq -r '.access_token // empty')

if [ -n "$ACCESS_TOKEN" ]; then
    print_success "Registration successful - Token obtained"
else
    print_info "Registration may have failed, trying login..."

    # Try to login if registration failed
    print_test "1.2 Login with credentials"
    LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL/api/v1/auth/login \
      -H "Content-Type: application/json" \
      -d "{
        \"username\": \"testuser1\",
        \"password\": \"TestPassword123!\"
      }")

    echo "$LOGIN_RESPONSE" | jq '.' 2>/dev/null || echo "$LOGIN_RESPONSE"
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token // empty')

    if [ -n "$ACCESS_TOKEN" ]; then
        print_success "Login successful - Token obtained"
    else
        print_error "Failed to obtain authentication token"
        exit 1
    fi
fi

print_test "1.3 Verify authentication token"
curl -s $BASE_URL/api/v1/auth/verify \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'

print_test "1.4 Get current user profile"
USER_INFO=$(curl -s $BASE_URL/api/v1/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN")
echo "$USER_INFO" | jq '.'
USER_ID=$(echo "$USER_INFO" | jq -r '.id // empty')

# ============================================
# PHASE 2: CUSTOMER MANAGEMENT
# ============================================
print_header "PHASE 2: CUSTOMER MANAGEMENT"

print_test "2.1 Create a new customer"
CUSTOMER_RESPONSE=$(curl -s -X POST $BASE_URL/api/v1/customers \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "customer_'$TIMESTAMP'@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890",
    "company": "Tech Corp",
    "address_line1": "123 Main St",
    "city": "San Francisco",
    "state": "CA",
    "country": "USA",
    "postal_code": "94105",
    "status": "active",
    "tier": "premium"
  }')

echo "$CUSTOMER_RESPONSE" | jq '.' 2>/dev/null || echo "$CUSTOMER_RESPONSE"
CUSTOMER_ID=$(echo "$CUSTOMER_RESPONSE" | jq -r '.id // empty')

if [ -n "$CUSTOMER_ID" ]; then
    print_success "Customer created with ID: $CUSTOMER_ID"

    print_test "2.2 Get customer details"
    curl -s $BASE_URL/api/v1/customers/$CUSTOMER_ID \
      -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'

    print_test "2.3 Update customer information"
    UPDATE_RESPONSE=$(curl -s -X PUT $BASE_URL/api/v1/customers/$CUSTOMER_ID \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "company": "Tech Corp International",
        "tier": "enterprise",
        "metadata": {
          "source": "api_test",
          "segment": "large_business"
        }
      }')
    echo "$UPDATE_RESPONSE" | jq '.' 2>/dev/null || echo "$UPDATE_RESPONSE"

    print_test "2.4 Add customer activity"
    curl -s -X POST $BASE_URL/api/v1/customers/$CUSTOMER_ID/activities \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "title": "Account Upgraded",
        "description": "Customer upgraded to enterprise tier",
        "activity_type": "account_update"
      }' | jq '.' 2>/dev/null || echo "Activity endpoint not available"

    print_test "2.5 Add customer note"
    curl -s -X POST $BASE_URL/api/v1/customers/$CUSTOMER_ID/notes \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "content": "High-value customer with growth potential",
        "is_internal": true
      }' | jq '.' 2>/dev/null || echo "Notes endpoint not available"

    print_test "2.6 Record a purchase"
    curl -s -X POST $BASE_URL/api/v1/customers/$CUSTOMER_ID/purchases \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "amount": 1999.99,
        "currency": "USD",
        "description": "Enterprise subscription"
      }' | jq '.' 2>/dev/null || echo "Purchase endpoint not available"

    print_test "2.7 Get customer metrics"
    curl -s $BASE_URL/api/v1/customers/$CUSTOMER_ID/metrics \
      -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.' 2>/dev/null || echo "Metrics endpoint not available"
else
    print_info "Customer endpoints may not be available or require different authentication"
fi

print_test "2.8 Search customers"
curl -s "$BASE_URL/api/v1/customers/search?query=John&limit=10" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.' 2>/dev/null || echo "Search endpoint not available"

# ============================================
# PHASE 3: BILLING - PRODUCTS & PRICING
# ============================================
print_header "PHASE 3: BILLING - PRODUCTS & PRICING"

print_test "3.1 Get product catalog"
CATALOG_RESPONSE=$(curl -s $BASE_URL/api/v1/billing/catalog/products \
  -H "Authorization: Bearer $ACCESS_TOKEN")
echo "$CATALOG_RESPONSE" | jq '.' 2>/dev/null || echo "$CATALOG_RESPONSE"

print_test "3.2 Create a new product"
PRODUCT_RESPONSE=$(curl -s -X POST $BASE_URL/api/v1/billing/catalog/products \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Enterprise Plan",
    "description": "Full-featured enterprise subscription",
    "sku": "ENT-'$TIMESTAMP'",
    "type": "subscription",
    "billing_period": "monthly",
    "price": 1999.99,
    "currency": "USD",
    "features": ["unlimited_users", "priority_support", "custom_integrations"]
  }')

echo "$PRODUCT_RESPONSE" | jq '.' 2>/dev/null || echo "$PRODUCT_RESPONSE"
PRODUCT_ID=$(echo "$PRODUCT_RESPONSE" | jq -r '.id // empty')

if [ -n "$PRODUCT_ID" ]; then
    print_success "Product created with ID: $PRODUCT_ID"
fi

print_test "3.3 Get pricing rules"
curl -s $BASE_URL/api/v1/billing/pricing/rules \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.' 2>/dev/null || echo "Pricing rules endpoint not available"

print_test "3.4 Calculate price with discounts"
curl -s -X POST $BASE_URL/api/v1/billing/pricing/calculate \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "'$PRODUCT_ID'",
    "quantity": 1,
    "discount_code": "WELCOME20"
  }' | jq '.' 2>/dev/null || echo "Price calculation endpoint not available"

# ============================================
# PHASE 4: BILLING - SUBSCRIPTIONS
# ============================================
print_header "PHASE 4: BILLING - SUBSCRIPTIONS"

print_test "4.1 Create a subscription"
SUBSCRIPTION_RESPONSE=$(curl -s -X POST $BASE_URL/api/v1/billing/subscriptions \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "'$CUSTOMER_ID'",
    "product_id": "'$PRODUCT_ID'",
    "plan_name": "Enterprise Monthly",
    "billing_cycle": "monthly",
    "start_date": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "auto_renew": true,
    "payment_method": "credit_card"
  }')

echo "$SUBSCRIPTION_RESPONSE" | jq '.' 2>/dev/null || echo "$SUBSCRIPTION_RESPONSE"
SUBSCRIPTION_ID=$(echo "$SUBSCRIPTION_RESPONSE" | jq -r '.id // empty')

if [ -n "$SUBSCRIPTION_ID" ]; then
    print_success "Subscription created with ID: $SUBSCRIPTION_ID"

    print_test "4.2 Get subscription details"
    curl -s $BASE_URL/api/v1/billing/subscriptions/$SUBSCRIPTION_ID \
      -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'

    print_test "4.3 Update subscription"
    curl -s -X PUT $BASE_URL/api/v1/billing/subscriptions/$SUBSCRIPTION_ID \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "auto_renew": false,
        "notes": "Customer requested manual renewal"
      }' | jq '.' 2>/dev/null || echo "Update failed"
fi

print_test "4.4 List active subscriptions"
curl -s "$BASE_URL/api/v1/billing/subscriptions?status=active" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.' 2>/dev/null || echo "List subscriptions endpoint not available"

# ============================================
# PHASE 5: BILLING - INVOICES & PAYMENTS
# ============================================
print_header "PHASE 5: BILLING - INVOICES & PAYMENTS"

print_test "5.1 Create an invoice"
INVOICE_RESPONSE=$(curl -s -X POST $BASE_URL/api/v1/billing/invoices \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "'$CUSTOMER_ID'",
    "subscription_id": "'$SUBSCRIPTION_ID'",
    "items": [
      {
        "description": "Enterprise Plan - Monthly",
        "quantity": 1,
        "unit_price": 1999.99,
        "tax_rate": 0.0875
      }
    ],
    "due_date": "'$(date -u -d "+30 days" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")'"
  }')

echo "$INVOICE_RESPONSE" | jq '.' 2>/dev/null || echo "$INVOICE_RESPONSE"
INVOICE_ID=$(echo "$INVOICE_RESPONSE" | jq -r '.id // empty')

if [ -n "$INVOICE_ID" ]; then
    print_success "Invoice created with ID: $INVOICE_ID"

    print_test "5.2 Get invoice details"
    curl -s $BASE_URL/api/v1/billing/invoices/$INVOICE_ID \
      -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'

    print_test "5.3 Record payment for invoice"
    PAYMENT_RESPONSE=$(curl -s -X POST $BASE_URL/api/v1/billing/payments \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "invoice_id": "'$INVOICE_ID'",
        "amount": 2174.89,
        "payment_method": "credit_card",
        "payment_details": {
          "last_four": "4242",
          "card_brand": "visa"
        }
      }')

    echo "$PAYMENT_RESPONSE" | jq '.' 2>/dev/null || echo "$PAYMENT_RESPONSE"
    PAYMENT_ID=$(echo "$PAYMENT_RESPONSE" | jq -r '.id // empty')

    if [ -n "$PAYMENT_ID" ]; then
        print_success "Payment recorded with ID: $PAYMENT_ID"
    fi
fi

print_test "5.4 List customer invoices"
curl -s "$BASE_URL/api/v1/billing/invoices?customer_id=$CUSTOMER_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.' 2>/dev/null || echo "List invoices endpoint not available"

print_test "5.5 Get payment history"
curl -s "$BASE_URL/api/v1/billing/payments?customer_id=$CUSTOMER_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.' 2>/dev/null || echo "Payment history endpoint not available"

# ============================================
# PHASE 6: BILLING - BANK ACCOUNTS
# ============================================
print_header "PHASE 6: BILLING - BANK ACCOUNTS"

print_test "6.1 Add bank account"
BANK_RESPONSE=$(curl -s -X POST $BASE_URL/api/v1/billing/bank-accounts \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "'$CUSTOMER_ID'",
    "account_holder_name": "John Doe",
    "account_number": "****1234",
    "routing_number": "****5678",
    "account_type": "checking",
    "bank_name": "Test Bank",
    "is_primary": true
  }')

echo "$BANK_RESPONSE" | jq '.' 2>/dev/null || echo "$BANK_RESPONSE"

print_test "6.2 List customer bank accounts"
curl -s "$BASE_URL/api/v1/billing/bank-accounts?customer_id=$CUSTOMER_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.' 2>/dev/null || echo "Bank accounts endpoint not available"

# ============================================
# PHASE 7: BILLING - REPORTS & ANALYTICS
# ============================================
print_header "PHASE 7: BILLING - REPORTS & ANALYTICS"

print_test "7.1 Get billing summary"
curl -s $BASE_URL/api/v1/billing/summary \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.' 2>/dev/null || echo "Billing summary endpoint not available"

print_test "7.2 Get revenue report"
curl -s "$BASE_URL/api/v1/billing/reports/revenue?period=monthly" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.' 2>/dev/null || echo "Revenue report endpoint not available"

print_test "7.3 Get customer billing metrics"
curl -s $BASE_URL/api/v1/billing/customers/$CUSTOMER_ID/metrics \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.' 2>/dev/null || echo "Customer billing metrics endpoint not available"

# ============================================
# PHASE 8: ADDITIONAL ENDPOINTS
# ============================================
print_header "PHASE 8: ADDITIONAL ENDPOINTS"

print_test "8.1 Get billing settings"
curl -s $BASE_URL/api/v1/billing/settings \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.' 2>/dev/null || echo "Billing settings endpoint not available"

print_test "8.2 Get tax rates"
curl -s $BASE_URL/api/v1/billing/tax-rates \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.' 2>/dev/null || echo "Tax rates endpoint not available"

print_test "8.3 Test webhook endpoint"
curl -s -X POST $BASE_URL/api/v1/billing/webhooks/stripe \
  -H "Content-Type: application/json" \
  -H "stripe-signature: test_signature" \
  -d '{
    "type": "payment_intent.succeeded",
    "data": {
      "object": {
        "id": "pi_test_'$TIMESTAMP'",
        "amount": 199999,
        "currency": "usd"
      }
    }
  }' | jq '.' 2>/dev/null || echo "Webhook endpoint not available"

# ============================================
# SUMMARY
# ============================================
print_header "TEST SUMMARY"
print_info "Test completed at: $(date)"

if [ -n "$ACCESS_TOKEN" ]; then
    print_success "Authentication: SUCCESS"
else
    print_error "Authentication: FAILED"
fi

if [ -n "$CUSTOMER_ID" ]; then
    print_success "Customer Management: Customer created successfully"
else
    print_info "Customer Management: Limited or no access"
fi

if [ -n "$SUBSCRIPTION_ID" ]; then
    print_success "Billing - Subscriptions: Subscription created successfully"
else
    print_info "Billing - Subscriptions: Limited or no access"
fi

if [ -n "$INVOICE_ID" ]; then
    print_success "Billing - Invoices: Invoice created successfully"
else
    print_info "Billing - Invoices: Limited or no access"
fi

print_header "END OF USER JOURNEY TEST"
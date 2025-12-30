#!/bin/bash
# ============================================================================
# Admin & Platform Settings Endpoint Tester
# ============================================================================
# Usage: ./test-admin-endpoints.sh [options]
# Options:
#   -h, --host       API host (default: http://localhost:8000)
#   -u, --username   Admin username/email
#   -p, --password   Admin password
#   -t, --token      Use existing JWT token (skip login)
#   -o, --output     Output directory (default: ./test-results)
#   -v, --verbose    Show full response bodies
#   --dry-run        Show commands without executing
# ============================================================================

# Don't exit on errors - we want to test all endpoints
set +e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default configuration
API_HOST="${API_HOST:-http://localhost:8000}"
OUTPUT_DIR="./test-results"
VERBOSE=false
DRY_RUN=false
TOKEN=""
USERNAME=""
PASSWORD=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--host)
            API_HOST="$2"
            shift 2
            ;;
        -u|--username)
            USERNAME="$2"
            shift 2
            ;;
        -p|--password)
            PASSWORD="$2"
            shift 2
            ;;
        -t|--token)
            TOKEN="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            head -20 "$0" | tail -15
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Create output directory
mkdir -p "$OUTPUT_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="$OUTPUT_DIR/$TIMESTAMP"
mkdir -p "$RESULTS_DIR"

# Results tracking
declare -A RESULTS
PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_skip() {
    echo -e "${CYAN}[SKIP]${NC} $1"
}

# Authenticate and get JWT token
authenticate() {
    if [[ -n "$TOKEN" ]]; then
        log_info "Using provided token"
        return 0
    fi

    if [[ -z "$USERNAME" ]] || [[ -z "$PASSWORD" ]]; then
        log_error "Username and password required for authentication"
        log_info "Use -u/--username and -p/--password, or provide -t/--token"
        exit 1
    fi

    log_info "Authenticating as $USERNAME..."

    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X POST "$API_HOST/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\": \"$USERNAME\", \"password\": \"$PASSWORD\"}")

    HTTP_CODE=$(echo "$RESPONSE" | tail -1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    if [[ "$HTTP_CODE" == "200" ]]; then
        TOKEN=$(echo "$BODY" | jq -r '.access_token // .data.access_token // empty')
        if [[ -n "$TOKEN" ]]; then
            log_success "Authentication successful"
            echo "$BODY" > "$RESULTS_DIR/auth_response.json"
        else
            log_error "Could not extract token from response"
            echo "$BODY"
            exit 1
        fi
    else
        log_error "Authentication failed (HTTP $HTTP_CODE)"
        echo "$BODY"
        exit 1
    fi
}

# Test a single endpoint
test_endpoint() {
    local METHOD="$1"
    local ENDPOINT="$2"
    local DESCRIPTION="$3"
    local DATA="$4"
    local EXPECTED_CODES="${5:-200,201}"

    local SAFE_NAME=$(echo "$ENDPOINT" | sed 's/[\/:]/_/g' | sed 's/^_//')
    local RESULT_FILE="$RESULTS_DIR/${METHOD}_${SAFE_NAME}.json"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] $METHOD $ENDPOINT - $DESCRIPTION"
        return 0
    fi

    # Build curl command
    local CURL_CMD="curl -s -w '\n%{http_code}\n%{time_total}' -X $METHOD"
    CURL_CMD="$CURL_CMD -H 'Authorization: Bearer $TOKEN'"
    CURL_CMD="$CURL_CMD -H 'Content-Type: application/json'"

    if [[ -n "$DATA" ]]; then
        CURL_CMD="$CURL_CMD -d '$DATA'"
    fi

    CURL_CMD="$CURL_CMD '$API_HOST$ENDPOINT'"

    # Execute request
    local START_TIME=$(date +%s.%N)
    local RESPONSE=$(eval $CURL_CMD 2>&1)
    local END_TIME=$(date +%s.%N)

    # Parse response
    local TIME_TOTAL=$(echo "$RESPONSE" | tail -1)
    local HTTP_CODE=$(echo "$RESPONSE" | tail -2 | head -1)
    local BODY=$(echo "$RESPONSE" | sed '$d' | sed '$d')

    # Check if response code is expected
    local IS_EXPECTED=false
    IFS=',' read -ra CODES <<< "$EXPECTED_CODES"
    for code in "${CODES[@]}"; do
        if [[ "$HTTP_CODE" == "$code" ]]; then
            IS_EXPECTED=true
            break
        fi
    done

    # Save result
    local RESULT_JSON=$(cat <<EOF
{
    "endpoint": "$ENDPOINT",
    "method": "$METHOD",
    "description": "$DESCRIPTION",
    "http_code": $HTTP_CODE,
    "expected_codes": "$EXPECTED_CODES",
    "is_expected": $IS_EXPECTED,
    "time_seconds": $TIME_TOTAL,
    "timestamp": "$(date -Iseconds)",
    "response": $BODY
}
EOF
)
    echo "$RESULT_JSON" > "$RESULT_FILE" 2>/dev/null || echo "{\"error\": \"Failed to save\", \"body\": \"$BODY\"}" > "$RESULT_FILE"

    # Log result
    if [[ "$IS_EXPECTED" == "true" ]]; then
        log_success "$METHOD $ENDPOINT → HTTP $HTTP_CODE (${TIME_TOTAL}s)"
        ((PASS_COUNT++))
        RESULTS["$METHOD $ENDPOINT"]="PASS:$HTTP_CODE"
    else
        log_error "$METHOD $ENDPOINT → HTTP $HTTP_CODE (expected: $EXPECTED_CODES)"
        ((FAIL_COUNT++))
        RESULTS["$METHOD $ENDPOINT"]="FAIL:$HTTP_CODE"
        if [[ "$VERBOSE" == "true" ]]; then
            echo "$BODY" | jq . 2>/dev/null || echo "$BODY"
        fi
    fi
}

# ============================================================================
# Test Categories
# ============================================================================

test_admin_settings() {
    log_info ""
    log_info "=========================================="
    log_info "Testing Admin Settings Endpoints"
    log_info "=========================================="

    # Settings Categories
    test_endpoint "GET" "/api/v1/admin/settings/categories" "List all settings categories"
    test_endpoint "GET" "/api/v1/admin/settings/health" "Settings health check"

    # Individual categories
    local CATEGORIES=("database" "jwt" "redis" "storage" "email" "tenant" "cors" "rate_limit" "observability" "features" "billing")
    for cat in "${CATEGORIES[@]}"; do
        test_endpoint "GET" "/api/v1/admin/settings/category/$cat" "Get $cat settings"
    done

    # Audit logs
    test_endpoint "GET" "/api/v1/admin/settings/audit-logs" "Get settings audit logs"
    test_endpoint "GET" "/api/v1/admin/settings/audit-logs?limit=10" "Get settings audit logs (limited)"
}

test_platform_admin_billing() {
    log_info ""
    log_info "=========================================="
    log_info "Testing Platform Admin Billing Endpoints"
    log_info "=========================================="

    test_endpoint "GET" "/api/v1/billing/invoices" "List all invoices"
    test_endpoint "GET" "/api/v1/billing/invoices?limit=10" "List invoices (limited)"
    test_endpoint "GET" "/api/v1/billing/payments" "List all payments"
    test_endpoint "GET" "/api/v1/billing/metrics" "Get billing metrics"
}

test_platform_admin_analytics() {
    log_info ""
    log_info "=========================================="
    log_info "Testing Platform Admin Analytics Endpoints"
    log_info "=========================================="

    test_endpoint "GET" "/api/v1/analytics/dashboard" "Get analytics dashboard"
    test_endpoint "GET" "/api/v1/analytics/activity" "Get activity analytics"
    test_endpoint "GET" "/api/v1/analytics/metrics" "Get analytics metrics"
    test_endpoint "GET" "/api/v1/analytics/events" "Get analytics events"
    test_endpoint "POST" "/api/v1/analytics/query" "Query analytics" '{"query_type":"events","filters":{}}'
    test_endpoint "GET" "/api/v1/analytics/billing/metrics" "Billing metrics"
    test_endpoint "GET" "/api/v1/analytics/security/metrics" "Security metrics"
    test_endpoint "GET" "/api/v1/analytics/operations/metrics" "Operations metrics"
    test_endpoint "GET" "/api/v1/analytics/infrastructure/health" "Infrastructure health"
}

test_platform_admin_audit() {
    log_info ""
    log_info "=========================================="
    log_info "Testing Platform Admin Audit Endpoints"
    log_info "=========================================="

    test_endpoint "GET" "/api/v1/audit/activities" "List audit activities"
    test_endpoint "GET" "/api/v1/audit/activities?limit=10" "List audit activities (limited)"
    test_endpoint "GET" "/api/v1/audit/activities/recent" "Recent audit activities"
    test_endpoint "GET" "/api/v1/audit/activities/summary" "Audit summary"
    test_endpoint "GET" "/api/v1/audit/activities/platform" "Platform audit activities"
    test_endpoint "GET" "/api/v1/audit/compliance?from_date=2024-01-01&to_date=2024-12-31" "Audit compliance"
    test_endpoint "POST" "/api/v1/audit/export" "Export audit logs" '{"format":"csv"}'
}

test_platform_admin_core() {
    log_info ""
    log_info "=========================================="
    log_info "Testing Platform Admin Core Endpoints"
    log_info "=========================================="

    test_endpoint "GET" "/api/v1/admin/platform/health" "Platform admin health"
    test_endpoint "GET" "/api/v1/admin/platform/tenants" "List all tenants"
    test_endpoint "GET" "/api/v1/admin/platform/tenants?limit=10" "List tenants (limited)"
    test_endpoint "GET" "/api/v1/admin/platform/stats" "Get platform stats"
    test_endpoint "GET" "/api/v1/admin/platform/permissions" "List permissions"
    test_endpoint "GET" "/api/v1/admin/platform/system/config" "Get system config"

    # Search endpoint
    test_endpoint "GET" "/api/v1/admin/platform/search?query=test" "Cross-tenant search (GET)"
    test_endpoint "POST" "/api/v1/admin/platform/search" "Cross-tenant search (POST)" '{"query": "test", "limit": 10}'

    # Recent audit
    test_endpoint "GET" "/api/v1/admin/platform/audit/recent" "Recent admin actions"
}

test_rbac_admin() {
    log_info ""
    log_info "=========================================="
    log_info "Testing RBAC Admin Endpoints"
    log_info "=========================================="

    test_endpoint "GET" "/api/v1/auth/rbac/admin/roles" "List all roles" "" "200,404"
    test_endpoint "GET" "/api/v1/auth/rbac/admin/permissions" "List all permissions" "" "200,404"
}

test_additional_admin() {
    log_info ""
    log_info "=========================================="
    log_info "Testing Additional Admin Endpoints"
    log_info "=========================================="

    # Tenant management
    test_endpoint "GET" "/api/v1/tenants" "List tenants" "" "200,403"

    # User management
    test_endpoint "GET" "/api/v1/users" "List users" "" "200,403"

    # API Keys
    test_endpoint "GET" "/api/v1/auth/api-keys" "List API keys" "" "200,403"

    # Webhooks
    test_endpoint "GET" "/api/v1/webhooks" "List webhooks" "" "200,403"

    # Workflows
    test_endpoint "GET" "/api/v1/workflows/" "List workflows" "" "200,403"
}

# ============================================================================
# Report Generation
# ============================================================================

generate_report() {
    log_info ""
    log_info "=========================================="
    log_info "Generating Test Report"
    log_info "=========================================="

    local REPORT_FILE="$RESULTS_DIR/report.md"
    local SUMMARY_FILE="$RESULTS_DIR/summary.json"

    # Calculate totals
    local TOTAL=$((PASS_COUNT + FAIL_COUNT + SKIP_COUNT))
    local PASS_PERCENT=0
    if [[ $TOTAL -gt 0 ]]; then
        PASS_PERCENT=$(echo "scale=1; $PASS_COUNT * 100 / $TOTAL" | bc)
    fi

    # Generate Markdown report
    cat > "$REPORT_FILE" << EOF
# Admin & Platform Endpoint Test Report

**Date:** $(date)
**API Host:** $API_HOST
**Authenticated User:** ${USERNAME:-"Using provided token"}

## Summary

| Metric | Count |
|--------|-------|
| ✅ Passed | $PASS_COUNT |
| ❌ Failed | $FAIL_COUNT |
| ⏭️ Skipped | $SKIP_COUNT |
| **Total** | $TOTAL |
| **Pass Rate** | ${PASS_PERCENT}% |

## Results by Endpoint

| Status | Method | Endpoint | HTTP Code |
|--------|--------|----------|-----------|
EOF

    # Sort and add results
    for key in "${!RESULTS[@]}"; do
        local STATUS=$(echo "${RESULTS[$key]}" | cut -d: -f1)
        local CODE=$(echo "${RESULTS[$key]}" | cut -d: -f2)
        local METHOD=$(echo "$key" | cut -d' ' -f1)
        local ENDPOINT=$(echo "$key" | cut -d' ' -f2-)

        if [[ "$STATUS" == "PASS" ]]; then
            echo "| ✅ | $METHOD | \`$ENDPOINT\` | $CODE |" >> "$REPORT_FILE"
        else
            echo "| ❌ | $METHOD | \`$ENDPOINT\` | $CODE |" >> "$REPORT_FILE"
        fi
    done

    # Add interpretation section
    cat >> "$REPORT_FILE" << 'EOF'

## Interpreting Results

### Expected HTTP Codes

- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Missing or invalid token
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Endpoint or resource doesn't exist
- **422 Unprocessable Entity**: Validation error
- **500 Internal Server Error**: Server-side error

### Common Issues

1. **401 errors**: Token expired or invalid - try re-authenticating
2. **403 errors**: User lacks required permissions (e.g., `platform.admin`, `settings.read`)
3. **404 errors**: Endpoint may not be registered or resource doesn't exist
4. **500 errors**: Check server logs for stack traces

### Files Generated

- `report.md` - This summary report
- `summary.json` - Machine-readable summary
- `*.json` - Individual endpoint response files
EOF

    # Generate JSON summary
    cat > "$SUMMARY_FILE" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "api_host": "$API_HOST",
    "total_tests": $TOTAL,
    "passed": $PASS_COUNT,
    "failed": $FAIL_COUNT,
    "skipped": $SKIP_COUNT,
    "pass_rate": $PASS_PERCENT,
    "results_directory": "$RESULTS_DIR"
}
EOF

    log_info "Report saved to: $REPORT_FILE"
    log_info "Summary saved to: $SUMMARY_FILE"
}

print_summary() {
    echo ""
    echo "=========================================="
    echo "           TEST SUMMARY"
    echo "=========================================="
    echo ""
    echo -e "  ${GREEN}✅ Passed:${NC}  $PASS_COUNT"
    echo -e "  ${RED}❌ Failed:${NC}  $FAIL_COUNT"
    echo -e "  ${CYAN}⏭️  Skipped:${NC} $SKIP_COUNT"
    echo ""
    echo "  Results saved to: $RESULTS_DIR"
    echo ""

    if [[ $FAIL_COUNT -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  Some tests failed. Check the report for details.${NC}"
        echo ""
    fi
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    echo ""
    echo "=========================================="
    echo "  Admin & Platform Endpoint Tester"
    echo "=========================================="
    echo ""
    log_info "API Host: $API_HOST"
    log_info "Output: $RESULTS_DIR"
    echo ""

    # Authenticate
    authenticate

    # Run all test categories
    test_admin_settings
    test_platform_admin_billing
    test_platform_admin_analytics
    test_platform_admin_audit
    test_platform_admin_core
    test_rbac_admin
    test_additional_admin

    # Generate reports
    generate_report
    print_summary
}

# Run main
main "$@"

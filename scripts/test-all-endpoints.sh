#!/bin/bash
# ============================================================================
# Comprehensive API Endpoint Tester - Auto-Discovery from OpenAPI
# ============================================================================
# Usage: ./test-all-endpoints.sh [options]
# Options:
#   -h, --host       API host (default: http://localhost:8000)
#   -u, --username   Platform admin username/email
#   -p, --password   Platform admin password
#   -t, --token      Platform admin JWT token (skip login)
#   --tenant-user    Tenant admin username/email
#   --tenant-pass    Tenant admin password
#   --tenant-token   Tenant admin JWT token (skip login)
#   --tenant-id      Tenant ID for tenant-scoped endpoints (X-Tenant-ID)
#   --partner-user   Partner portal username/email
#   --partner-pass   Partner portal password
#   --partner-token  Partner portal JWT token (skip login)
#   --partner-id     Partner ID for partner portal endpoints (X-Partner-ID)
#   -o, --output     Output directory (default: ./test-results)
#   -m, --methods    Methods to test (default: GET)
#   -f, --filter     Filter endpoints by pattern (e.g. "billing")
#   --skip-auth      Skip endpoints requiring path params like {id}
#   --include-write  Include POST/PUT/DELETE (dangerous!)
#   -v, --verbose    Show full response bodies
#   --dry-run        Show commands without executing
#   --no-auto-tenant Disable automatic test tenant creation
#   --cleanup-tenant Delete test tenant after tests complete
#
# Tenant Context:
#   By default, the script creates a test tenant (api-test-tenant) for testing
#   tenant-scoped endpoints. Use --tenant-id to specify an existing tenant,
#   or --no-auto-tenant to disable automatic tenant creation.
# ============================================================================

set +e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Default configuration
API_HOST="${API_HOST:-http://localhost:8000}"
OUTPUT_DIR="./test-results"
VERBOSE=false
DRY_RUN=false
TOKEN=""
USERNAME=""
PASSWORD=""
TENANT_USERNAME=""
TENANT_PASSWORD=""
TENANT_TOKEN=""
TENANT_ID=""
PARTNER_USERNAME=""
PARTNER_PASSWORD=""
PARTNER_TOKEN=""
PARTNER_ID=""
METHODS="GET"
FILTER=""
SKIP_PARAMS=true
INCLUDE_WRITE=false
AUTO_CREATE_TENANT=true
CLEANUP_TENANT=false
TEST_TENANT_SLUG="api-test-tenant"
CREATED_TENANT_ID=""
VAULT_ENABLED=true

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--host) API_HOST="$2"; shift 2 ;;
        -u|--username) USERNAME="$2"; shift 2 ;;
        -p|--password) PASSWORD="$2"; shift 2 ;;
        -t|--token) TOKEN="$2"; shift 2 ;;
        --tenant-user) TENANT_USERNAME="$2"; shift 2 ;;
        --tenant-pass) TENANT_PASSWORD="$2"; shift 2 ;;
        --tenant-token) TENANT_TOKEN="$2"; shift 2 ;;
        --tenant-id) TENANT_ID="$2"; shift 2 ;;
        --partner-user) PARTNER_USERNAME="$2"; shift 2 ;;
        --partner-pass) PARTNER_PASSWORD="$2"; shift 2 ;;
        --partner-token) PARTNER_TOKEN="$2"; shift 2 ;;
        --partner-id) PARTNER_ID="$2"; shift 2 ;;
        -o|--output) OUTPUT_DIR="$2"; shift 2 ;;
        -m|--methods) METHODS="$2"; shift 2 ;;
        -f|--filter) FILTER="$2"; shift 2 ;;
        --skip-auth) SKIP_PARAMS=true; shift ;;
        --include-write) INCLUDE_WRITE=true; shift ;;
        -v|--verbose) VERBOSE=true; shift ;;
        --dry-run) DRY_RUN=true; shift ;;
        --no-auto-tenant) AUTO_CREATE_TENANT=false; shift ;;
        --cleanup-tenant) CLEANUP_TENANT=true; shift ;;
        --help) head -25 "$0" | tail -20; exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Setup output directory
mkdir -p "$OUTPUT_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="$OUTPUT_DIR/full_$TIMESTAMP"
mkdir -p "$RESULTS_DIR"

# Counters
PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0
declare -A RESULTS
declare -A CATEGORY_STATS

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[PASS]${NC} $1"; }
log_error() { echo -e "${RED}[FAIL]${NC} $1"; }
log_skip() { echo -e "${CYAN}[SKIP]${NC} $1"; }
log_category() { echo -e "${MAGENTA}[====]${NC} $1"; }

login() {
    local LOGIN_USER="$1"
    local LOGIN_PASS="$2"

    # Try with username first, then email
    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X POST "$API_HOST/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"username\": \"$LOGIN_USER\", \"password\": \"$LOGIN_PASS\"}")

    HTTP_CODE=$(echo "$RESPONSE" | tail -1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    if [[ "$HTTP_CODE" == "200" ]]; then
        echo "$BODY" | jq -r '.access_token // empty'
        return 0
    fi

    # Fallback to email field
    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X POST "$API_HOST/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\": \"$LOGIN_USER\", \"password\": \"$LOGIN_PASS\"}")

    HTTP_CODE=$(echo "$RESPONSE" | tail -1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    if [[ "$HTTP_CODE" == "200" ]]; then
        echo "$BODY" | jq -r '.access_token // empty'
        return 0
    fi

    return 1
}

authenticate_contexts() {
    if [[ -n "$TOKEN" ]]; then
        log_info "Using provided platform token"
    elif [[ -n "$USERNAME" ]] && [[ -n "$PASSWORD" ]]; then
        log_info "Authenticating platform admin as $USERNAME..."
        TOKEN=$(login "$USERNAME" "$PASSWORD")
        if [[ -n "$TOKEN" ]]; then
            log_success "Platform admin authentication successful"
        else
            log_error "Platform admin authentication failed"
            exit 1
        fi
    fi

    if [[ -n "$TENANT_TOKEN" ]]; then
        log_info "Using provided tenant token"
    elif [[ -n "$TENANT_USERNAME" ]] && [[ -n "$TENANT_PASSWORD" ]]; then
        log_info "Authenticating tenant admin as $TENANT_USERNAME..."
        TENANT_TOKEN=$(login "$TENANT_USERNAME" "$TENANT_PASSWORD")
        if [[ -n "$TENANT_TOKEN" ]]; then
            log_success "Tenant admin authentication successful"
        else
            log_error "Tenant admin authentication failed"
            exit 1
        fi
    else
        # Fallback: use platform admin token for tenant endpoints
        log_info "No tenant credentials provided, using platform admin for tenant endpoints"
        TENANT_TOKEN="$TOKEN"
    fi

    if [[ -n "$PARTNER_TOKEN" ]]; then
        log_info "Using provided partner token"
    elif [[ -n "$PARTNER_USERNAME" ]] && [[ -n "$PARTNER_PASSWORD" ]]; then
        log_info "Authenticating partner user as $PARTNER_USERNAME..."
        PARTNER_TOKEN=$(login "$PARTNER_USERNAME" "$PARTNER_PASSWORD")
        if [[ -n "$PARTNER_TOKEN" ]]; then
            log_success "Partner authentication successful"
        else
            log_error "Partner authentication failed"
            exit 1
        fi
    fi
}

fetch_json_field() {
    local CONTEXT_TOKEN="$1"
    local ENDPOINT="$2"
    local FILTER="$3"

    if [[ -z "$CONTEXT_TOKEN" ]]; then
        return 1
    fi

    local RESPONSE
    RESPONSE=$(curl -s -H "Authorization: Bearer $CONTEXT_TOKEN" "$API_HOST$ENDPOINT")
    if [[ -z "$RESPONSE" ]]; then
        return 1
    fi

    local VALUE
    VALUE=$(echo "$RESPONSE" | jq -r "$FILTER // empty")
    if [[ -n "$VALUE" ]] && [[ "$VALUE" != "null" ]]; then
        echo "$VALUE"
        return 0
    fi

    return 1
}

detect_context_ids() {
    if [[ -z "$TENANT_ID" ]] && [[ -n "$TENANT_TOKEN" ]]; then
        log_info "Detecting tenant ID from /api/v1/tenants/current..."
        TENANT_ID=$(fetch_json_field "$TENANT_TOKEN" "/api/v1/tenants/current" ".id")
        if [[ -n "$TENANT_ID" ]]; then
            log_success "Detected tenant ID: $TENANT_ID"
        else
            log_info "Tenant ID not detected; set --tenant-id if required"
        fi
    fi

    if [[ -z "$PARTNER_ID" ]] && [[ -n "$PARTNER_TOKEN" ]]; then
        log_info "Detecting partner ID from /api/v1/partners/portal/profile..."
        PARTNER_ID=$(fetch_json_field "$PARTNER_TOKEN" "/api/v1/partners/portal/profile" ".id")
        if [[ -n "$PARTNER_ID" ]]; then
            log_success "Detected partner ID: $PARTNER_ID"
        else
            log_info "Partner ID not detected; set --partner-id if required"
        fi
    fi

    if [[ -z "$PARTNER_ID" ]] && [[ -n "$TOKEN" ]]; then
        log_info "Detecting partner ID from /api/v1/partners (platform admin)..."
        PARTNER_ID=$(fetch_json_field "$TOKEN" "/api/v1/partners" ".partners[0].id")
        if [[ -n "$PARTNER_ID" ]]; then
            log_success "Detected partner ID: $PARTNER_ID"
        else
            log_info "Partner ID not detected via platform admin; set --partner-id if required"
        fi
    fi
}

detect_vault_status() {
    if [[ -z "$TOKEN" ]]; then
        return 0
    fi

    local RESPONSE
    RESPONSE=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $TOKEN" \
        "$API_HOST/api/v1/secrets/health")

    local HTTP_CODE=$(echo "$RESPONSE" | tail -1)
    local BODY=$(echo "$RESPONSE" | sed '$d')

    if [[ "$HTTP_CODE" =~ ^2 ]]; then
        local ENABLED
        ENABLED=$(echo "$BODY" | jq -r '.enabled // empty')
        if [[ "$ENABLED" == "false" ]]; then
            VAULT_ENABLED=false
            log_info "Vault disabled: skipping secret operation endpoints"
        fi
    fi
}
# Create or get test tenant for tenant-scoped endpoint testing
setup_test_tenant() {
    if [[ "$AUTO_CREATE_TENANT" != "true" ]]; then
        return 0
    fi

    if [[ -n "$TENANT_ID" ]]; then
        log_info "Using provided tenant ID: $TENANT_ID"
        return 0
    fi

    if [[ -z "$TOKEN" ]]; then
        log_info "No platform token available, skipping tenant creation"
        return 0
    fi

    log_info "Checking for existing test tenant '$TEST_TENANT_SLUG'..."

    # Try to find existing test tenant
    local EXISTING_TENANT
    EXISTING_TENANT=$(curl -s -H "Authorization: Bearer $TOKEN" \
        "$API_HOST/api/v1/tenants?slug=$TEST_TENANT_SLUG" | jq -r '.tenants[0].id // empty')

    if [[ -n "$EXISTING_TENANT" ]] && [[ "$EXISTING_TENANT" != "null" ]]; then
        TENANT_ID="$EXISTING_TENANT"
        log_success "Found existing test tenant: $TENANT_ID"
        return 0
    fi

    log_info "Creating test tenant '$TEST_TENANT_SLUG'..."

    local CREATE_RESPONSE
    CREATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        "$API_HOST/api/v1/tenants" \
        -d "{
            \"name\": \"API Test Tenant\",
            \"slug\": \"$TEST_TENANT_SLUG\",
            \"email\": \"test@api-test.local\",
            \"plan_type\": \"free\",
            \"max_users\": 10,
            \"max_api_calls_per_month\": 100000,
            \"max_storage_gb\": 10
        }")

    local HTTP_CODE=$(echo "$CREATE_RESPONSE" | tail -1)
    local BODY=$(echo "$CREATE_RESPONSE" | sed '$d')

    if [[ "$HTTP_CODE" == "201" ]] || [[ "$HTTP_CODE" == "200" ]]; then
        TENANT_ID=$(echo "$BODY" | jq -r '.id // empty')
        if [[ -n "$TENANT_ID" ]] && [[ "$TENANT_ID" != "null" ]]; then
            CREATED_TENANT_ID="$TENANT_ID"
            log_success "Created test tenant: $TENANT_ID"
            return 0
        fi
    fi

    # Check if it's a duplicate error (tenant already exists)
    if [[ "$HTTP_CODE" == "409" ]] || [[ "$BODY" == *"already exists"* ]]; then
        # Try to fetch by slug again
        TENANT_ID=$(curl -s -H "Authorization: Bearer $TOKEN" \
            "$API_HOST/api/v1/tenants?slug=$TEST_TENANT_SLUG" | jq -r '.tenants[0].id // empty')
        if [[ -n "$TENANT_ID" ]] && [[ "$TENANT_ID" != "null" ]]; then
            log_success "Found existing test tenant: $TENANT_ID"
            return 0
        fi
    fi

    log_error "Failed to create/find test tenant (HTTP $HTTP_CODE)"
    if [[ "$VERBOSE" == "true" ]]; then
        echo "$BODY" | jq -r '.detail // .message // .' 2>/dev/null | head -3
    fi
    log_info "Tenant-scoped endpoints will fail without a tenant context"
}

# Cleanup test tenant if requested
cleanup_test_tenant() {
    if [[ "$CLEANUP_TENANT" != "true" ]]; then
        return 0
    fi

    if [[ -z "$CREATED_TENANT_ID" ]]; then
        return 0
    fi

    if [[ -z "$TOKEN" ]]; then
        return 0
    fi

    log_info "Cleaning up test tenant: $CREATED_TENANT_ID"

    local DELETE_RESPONSE
    DELETE_RESPONSE=$(curl -s -w "\n%{http_code}" -X DELETE \
        -H "Authorization: Bearer $TOKEN" \
        "$API_HOST/api/v1/tenants/$CREATED_TENANT_ID")

    local HTTP_CODE=$(echo "$DELETE_RESPONSE" | tail -1)

    if [[ "$HTTP_CODE" == "204" ]] || [[ "$HTTP_CODE" == "200" ]]; then
        log_success "Cleaned up test tenant"
    else
        log_info "Could not delete test tenant (HTTP $HTTP_CODE) - may need manual cleanup"
    fi
}

normalize_endpoint() {
    local ENDPOINT="$1"
    ENDPOINT="${ENDPOINT//\/billing\/dunning\/billing\/dunning/\/billing\/dunning}"
    ENDPOINT="${ENDPOINT//\/rate-limits\/rate-limits/\/rate-limits}"
    ENDPOINT="${ENDPOINT//\/billing\/subscriptions\/subscriptions/\/billing\/subscriptions}"
    echo "$ENDPOINT"
}

ensure_query_param() {
    local ENDPOINT="$1"
    local KEY="$2"
    local VALUE="$3"

    if [[ "$ENDPOINT" == *"$KEY="* ]]; then
        echo "$ENDPOINT"
        return 0
    fi

    if [[ "$ENDPOINT" == *"?"* ]]; then
        echo "${ENDPOINT}&${KEY}=${VALUE}"
    else
        echo "${ENDPOINT}?${KEY}=${VALUE}"
    fi
}

apply_required_params() {
    local METHOD="$1"
    local ENDPOINT="$2"
    local DATA="$3"

    if [[ "$METHOD" == "GET" ]]; then
        case "$ENDPOINT" in
            "/api/v1/admin/platform/search"*)
                ENDPOINT=$(ensure_query_param "$ENDPOINT" "query" "test")
                ;;
            "/api/v1/search"*)
                ENDPOINT=$(ensure_query_param "$ENDPOINT" "q" "test")
                ;;
            "/api/v1/audit/compliance"*)
                ENDPOINT=$(ensure_query_param "$ENDPOINT" "from_date" "2024-01-01")
                ENDPOINT=$(ensure_query_param "$ENDPOINT" "to_date" "2024-12-31")
                ;;
            "/api/v1/platform/analytics/metrics/aggregate"*)
                ENDPOINT=$(ensure_query_param "$ENDPOINT" "metric_name" "user_count")
                ;;
            "/api/v1/rate-limits/status"*)
                ENDPOINT=$(ensure_query_param "$ENDPOINT" "endpoint" "/api/v1/health")
                ;;
        esac
    fi

    echo "$ENDPOINT|$DATA"
}

get_context() {
    local ENDPOINT="$1"

    if [[ "$ENDPOINT" =~ ^/api/v1/admin/ ]]; then
        echo "platform"
        return 0
    fi

    if [[ "$ENDPOINT" =~ ^/api/v1/platform/ ]]; then
        echo "platform"
        return 0
    fi

    if [[ "$ENDPOINT" =~ ^/api/v1/secrets ]]; then
        echo "platform"
        return 0
    fi

    if [[ "$ENDPOINT" =~ ^/api/v1/partners/ ]] || [[ "$ENDPOINT" =~ ^/api/v1/partner/ ]]; then
        echo "partner"
        return 0
    fi

    echo "tenant"
}

# Test single endpoint
test_endpoint() {
    local METHOD="$1"
    local ENDPOINT="$2"
    local CATEGORY="$3"
    local DATA="$4"
    local CONTEXT="$5"

    local SAFE_NAME=$(echo "${METHOD}_${ENDPOINT}" | sed 's/[\/:]/_/g' | sed 's/^_//' | sed 's/{[^}]*}/_id_/g')
    local RESULT_FILE="$RESULTS_DIR/${SAFE_NAME}.json"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] $METHOD $ENDPOINT"
        return 0
    fi

    # Build curl command
    local CURL_OPTS="-s -w '\n%{http_code}\n%{time_total}' -X $METHOD"

    case "$CONTEXT" in
        platform)
            if [[ -z "$TOKEN" ]]; then
                log_skip "$METHOD $ENDPOINT → missing platform token"
                ((SKIP_COUNT++))
                return 0
            fi
            CURL_OPTS="$CURL_OPTS -H 'Authorization: Bearer $TOKEN'"
            ;;
        tenant)
            if [[ -z "$TENANT_TOKEN" ]]; then
                log_skip "$METHOD $ENDPOINT → missing tenant token"
                ((SKIP_COUNT++))
                return 0
            fi
            CURL_OPTS="$CURL_OPTS -H 'Authorization: Bearer $TENANT_TOKEN'"
            if [[ -n "$TENANT_ID" ]]; then
                CURL_OPTS="$CURL_OPTS -H 'X-Tenant-ID: $TENANT_ID'"
            fi
            ;;
        partner)
            if [[ -n "$PARTNER_TOKEN" ]]; then
                CURL_OPTS="$CURL_OPTS -H 'Authorization: Bearer $PARTNER_TOKEN'"
            elif [[ -n "$TOKEN" ]] && [[ -n "$PARTNER_ID" ]]; then
                CURL_OPTS="$CURL_OPTS -H 'Authorization: Bearer $TOKEN'"
                CURL_OPTS="$CURL_OPTS -H 'X-Partner-ID: $PARTNER_ID'"
            else
                log_skip "$METHOD $ENDPOINT → missing partner credentials"
                ((SKIP_COUNT++))
                return 0
            fi
            if [[ -n "$TENANT_ID" ]]; then
                CURL_OPTS="$CURL_OPTS -H 'X-Tenant-ID: $TENANT_ID'"
            fi
            ;;
    esac

    CURL_OPTS="$CURL_OPTS -H 'Content-Type: application/json'"

    if [[ -n "$DATA" ]]; then
        CURL_OPTS="$CURL_OPTS -d '$DATA'"
    fi

    RESPONSE=$(eval "curl $CURL_OPTS '$API_HOST$ENDPOINT'" 2>&1)

    local TIME_TOTAL=$(echo "$RESPONSE" | tail -1)
    local HTTP_CODE=$(echo "$RESPONSE" | tail -2 | head -1)
    local BODY=$(echo "$RESPONSE" | sed '$d' | sed '$d')

    # Determine success (2xx codes)
    local IS_SUCCESS=false
    if [[ "$HTTP_CODE" =~ ^2[0-9][0-9]$ ]]; then
        IS_SUCCESS=true
    fi

    # Save result
    cat > "$RESULT_FILE" << EOF
{
    "endpoint": "$ENDPOINT",
    "method": "$METHOD",
    "category": "$CATEGORY",
    "http_code": $HTTP_CODE,
    "success": $IS_SUCCESS,
    "time_seconds": $TIME_TOTAL,
    "context": "$CONTEXT",
    "timestamp": "$(date -Iseconds)"
}
EOF

    # Update stats
    if [[ "$IS_SUCCESS" == "true" ]]; then
        log_success "$METHOD $ENDPOINT → $HTTP_CODE (${TIME_TOTAL}s)"
        ((PASS_COUNT++))
        RESULTS["$METHOD $ENDPOINT"]="PASS:$HTTP_CODE"
        ((CATEGORY_STATS["${CATEGORY}_pass"]++))
    else
        log_error "$METHOD $ENDPOINT → $HTTP_CODE"
        ((FAIL_COUNT++))
        RESULTS["$METHOD $ENDPOINT"]="FAIL:$HTTP_CODE"
        ((CATEGORY_STATS["${CATEGORY}_fail"]++))
        if [[ "$VERBOSE" == "true" ]]; then
            echo "$BODY" | jq -r '.detail // .message // .' 2>/dev/null | head -3
        fi
    fi
}

# Extract category from endpoint
get_category() {
    local ENDPOINT="$1"
    echo "$ENDPOINT" | sed 's|^/api/v1/||' | cut -d'/' -f1-2 | tr '/' '-'
}

# Discover and test endpoints from OpenAPI
discover_and_test() {
    log_info "Fetching OpenAPI specification..."

    local OPENAPI=$(curl -s "$API_HOST/openapi.json")
    if [[ -z "$OPENAPI" ]]; then
        log_error "Failed to fetch OpenAPI spec"
        exit 1
    fi

    # Save OpenAPI spec
    echo "$OPENAPI" > "$RESULTS_DIR/openapi.json"

    # Extract endpoints
    local ENDPOINTS=$(echo "$OPENAPI" | jq -r '
        .paths | to_entries[] |
        .key as $path |
        .value | to_entries[] |
        select(.key != "options") |
        "\(.key | ascii_upcase) \($path)"
    ')

    local TOTAL=$(echo "$ENDPOINTS" | wc -l)
    log_info "Found $TOTAL endpoints"

    local CURRENT_CATEGORY=""
    local COUNT=0

    while IFS= read -r line; do
        [[ -z "$line" ]] && continue

        local METHOD=$(echo "$line" | awk '{print $1}')
        local ENDPOINT=$(echo "$line" | awk '{print $2}')
        ENDPOINT=$(normalize_endpoint "$ENDPOINT")

        # Apply filter
        if [[ -n "$FILTER" ]] && [[ ! "$ENDPOINT" =~ $FILTER ]]; then
            continue
        fi

        if [[ "$VAULT_ENABLED" != "true" ]]; then
            if [[ "$ENDPOINT" =~ ^/api/v1/secrets/ ]] && [[ "$ENDPOINT" != "/api/v1/secrets/health" ]] && [[ "$ENDPOINT" != "/api/v1/secrets" ]]; then
                ((SKIP_COUNT++))
                continue
            fi
        fi

        # Skip path params unless we have test data
        if [[ "$SKIP_PARAMS" == "true" ]] && [[ "$ENDPOINT" =~ \{.*\} ]]; then
            ((SKIP_COUNT++))
            continue
        fi

        # Skip write methods unless explicitly enabled
        if [[ "$INCLUDE_WRITE" != "true" ]] && [[ "$METHOD" != "GET" ]]; then
            ((SKIP_COUNT++))
            continue
        fi

        # Apply required query params
        local PARAM_RESULT
        PARAM_RESULT=$(apply_required_params "$METHOD" "$ENDPOINT" "")
        ENDPOINT=$(echo "$PARAM_RESULT" | cut -d'|' -f1)

        # Get category and context
        local CATEGORY=$(get_category "$ENDPOINT")
        local CONTEXT=$(get_context "$ENDPOINT")

        # Print category header
        if [[ "$CATEGORY" != "$CURRENT_CATEGORY" ]]; then
            echo ""
            log_category "Testing: $CATEGORY"
            CURRENT_CATEGORY="$CATEGORY"
        fi

        ((COUNT++))
        test_endpoint "$METHOD" "$ENDPOINT" "$CATEGORY" "" "$CONTEXT"

    done <<< "$ENDPOINTS"

    log_info ""
    log_info "Tested $COUNT endpoints (skipped $SKIP_COUNT)"
}

# Generate report
generate_report() {
    local REPORT_FILE="$RESULTS_DIR/report.md"
    local TOTAL=$((PASS_COUNT + FAIL_COUNT))
    local PASS_PERCENT=0
    [[ $TOTAL -gt 0 ]] && PASS_PERCENT=$(echo "scale=1; $PASS_COUNT * 100 / $TOTAL" | bc)

    cat > "$REPORT_FILE" << EOF
# Full API Endpoint Test Report

**Date:** $(date)
**API Host:** $API_HOST
**Filter:** ${FILTER:-"None"}

## Summary

| Metric | Count |
|--------|-------|
| ✅ Passed | $PASS_COUNT |
| ❌ Failed | $FAIL_COUNT |
| ⏭️ Skipped | $SKIP_COUNT |
| **Total Tested** | $TOTAL |
| **Pass Rate** | ${PASS_PERCENT}% |

## Results by Category

| Category | Passed | Failed | Rate |
|----------|--------|--------|------|
EOF

    # Calculate per-category stats
    for key in "${!CATEGORY_STATS[@]}"; do
        if [[ "$key" =~ _pass$ ]]; then
            local CAT=$(echo "$key" | sed 's/_pass$//')
            local PASS=${CATEGORY_STATS["${CAT}_pass"]:-0}
            local FAIL=${CATEGORY_STATS["${CAT}_fail"]:-0}
            local CAT_TOTAL=$((PASS + FAIL))
            local CAT_RATE=0
            [[ $CAT_TOTAL -gt 0 ]] && CAT_RATE=$(echo "scale=0; $PASS * 100 / $CAT_TOTAL" | bc)
            echo "| $CAT | $PASS | $FAIL | ${CAT_RATE}% |" >> "$REPORT_FILE"
        fi
    done

    cat >> "$REPORT_FILE" << EOF

## Failed Endpoints

| Method | Endpoint | HTTP Code |
|--------|----------|-----------|
EOF

    for key in "${!RESULTS[@]}"; do
        if [[ "${RESULTS[$key]}" =~ ^FAIL ]]; then
            local CODE=$(echo "${RESULTS[$key]}" | cut -d: -f2)
            local METHOD=$(echo "$key" | cut -d' ' -f1)
            local ENDPOINT=$(echo "$key" | cut -d' ' -f2-)
            echo "| $METHOD | \`$ENDPOINT\` | $CODE |" >> "$REPORT_FILE"
        fi
    done

    # JSON summary
    cat > "$RESULTS_DIR/summary.json" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "api_host": "$API_HOST",
    "filter": "$FILTER",
    "total_tested": $TOTAL,
    "passed": $PASS_COUNT,
    "failed": $FAIL_COUNT,
    "skipped": $SKIP_COUNT,
    "pass_rate": $PASS_PERCENT
}
EOF

    log_info "Report: $REPORT_FILE"
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
    echo "  Results: $RESULTS_DIR"
    echo ""
}

# Main
main() {
    echo ""
    echo "=========================================="
    echo "  Comprehensive API Endpoint Tester"
    echo "=========================================="
    echo ""
    log_info "API Host: $API_HOST"
    log_info "Output: $RESULTS_DIR"
    [[ -n "$FILTER" ]] && log_info "Filter: $FILTER"
    echo ""

    authenticate_contexts
    detect_context_ids
    detect_vault_status
    setup_test_tenant
    discover_and_test
    generate_report
    print_summary
    cleanup_test_tenant
}

main "$@"

#!/bin/bash

echo "🧪 Running comprehensive billing test suite..."

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test categories
FAILED_TESTS=""
TOTAL_TESTS=0
PASSED_TESTS=0

# Function to run test category
run_test_category() {
    local category="$1"
    local test_path="$2"
    local description="$3"

    echo ""
    echo -e "${BLUE}📋 Running $description...${NC}"
    echo "=================================="

    if .venv/bin/pytest "$test_path" -v --tb=short; then
        echo -e "${GREEN}✅ $category tests passed${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}❌ $category tests failed${NC}"
        FAILED_TESTS="$FAILED_TESTS\n  - $category"
    fi

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

# Function to run performance tests
run_performance_tests() {
    echo ""
    echo -e "${BLUE}⚡ Running Performance Tests...${NC}"
    echo "================================="

    if command -v locust &> /dev/null; then
        echo "Starting Locust load tests (background)..."
        locust -f tests/performance/test_billing_load.py --host=http://localhost:8000 --headless -u 10 -r 2 -t 60s &
        LOCUST_PID=$!

        # Wait for tests to complete
        sleep 65
        kill $LOCUST_PID 2>/dev/null || true

        echo -e "${GREEN}✅ Load tests completed${NC}"
    else
        echo -e "${YELLOW}⚠️  Locust not installed - skipping load tests${NC}"
    fi

    # Run performance pytest markers
    if .venv/bin/pytest tests/ -m performance -v --tb=short; then
        echo -e "${GREEN}✅ Performance tests passed${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}❌ Performance tests failed${NC}"
        FAILED_TESTS="$FAILED_TESTS\n  - Performance"
    fi

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

# Function to run E2E tests
run_e2e_tests() {
    echo ""
    echo -e "${BLUE}🌐 Running E2E Tests...${NC}"
    echo "========================"

    cd frontend/apps/base-app

    # Start mock API
    NEXT_PUBLIC_MOCK_API=true pnpm dev &
    DEV_PID=$!

    # Wait for server to start
    sleep 10

    # Run billing E2E tests
    if pnpm test:e2e:billing; then
        echo -e "${GREEN}✅ E2E tests passed${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}❌ E2E tests failed${NC}"
        FAILED_TESTS="$FAILED_TESTS\n  - E2E Billing"
    fi

    # Stop dev server
    kill $DEV_PID 2>/dev/null || true

    cd ../../..
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

# Main test execution
echo "🚀 Starting DotMac Billing Test Suite"
echo "====================================="
echo "Test Categories:"
echo "  1. Unit Tests"
echo "  2. Security Tests"
echo "  3. Load/Performance Tests"
echo "  4. Resilience Tests"
echo "  5. E2E Tests"
echo "  6. Integration Tests"
echo ""

# Ensure we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ Please run this script from the project root directory${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Run 'poetry install' first.${NC}"
    exit 1
fi

# 1. Unit Tests
run_test_category "Unit" \
    "tests/billing/test_*.py" \
    "Unit Tests (Models, Services, Business Logic)"

# 2. Security Tests
run_test_category "Security" \
    "tests/security/test_payment_security.py" \
    "Security Tests (PCI Compliance, Data Protection)"

# 3. Performance Tests
run_performance_tests

# 4. Resilience Tests
run_test_category "Resilience" \
    "tests/billing/test_billing_resilience.py" \
    "Resilience Tests (Error Recovery, Failure Handling)"

# 5. Integration Tests
run_test_category "Integration" \
    "tests/billing/test_stripe_webhooks_e2e.py" \
    "Integration Tests (Stripe Webhooks, External APIs)"

# 6. Invoice Generation Tests
run_test_category "Invoice Generation" \
    "tests/billing/test_automated_invoice_generation.py" \
    "Automated Invoice Generation Tests"

# 7. E2E Tests (only if frontend exists and ENABLE_E2E is set)
if [ "$ENABLE_E2E" = "true" ] && [ -d "frontend" ]; then
    run_e2e_tests
else
    echo ""
    echo -e "${YELLOW}⚠️  Skipping E2E tests (set ENABLE_E2E=true to include)${NC}"
fi

# Coverage Report
echo ""
echo -e "${BLUE}📊 Generating Coverage Report...${NC}"
echo "================================="

.venv/bin/pytest tests/billing/ tests/security/ \
    --cov=src/dotmac/platform/billing \
    --cov-report=term-missing \
    --cov-report=html:htmlcov/billing \
    --cov-fail-under=85 \
    -q

# Summary
echo ""
echo "🏆 TEST EXECUTION SUMMARY"
echo "========================="
echo -e "Total Test Categories: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$((TOTAL_TESTS - PASSED_TESTS))${NC}"

if [ -n "$FAILED_TESTS" ]; then
    echo ""
    echo -e "${RED}❌ Failed Test Categories:${NC}"
    echo -e "$FAILED_TESTS"
    echo ""
    echo -e "${RED}Please fix the failing tests before deploying billing features.${NC}"
    exit 1
else
    echo ""
    echo -e "${GREEN}🎉 All billing tests passed!${NC}"
    echo ""
    echo "✅ Unit Tests: Models, services, business logic"
    echo "✅ Security Tests: PCI compliance, data protection"
    echo "✅ Performance Tests: Load handling, response times"
    echo "✅ Resilience Tests: Error recovery, failure handling"
    echo "✅ Integration Tests: Stripe webhooks, external APIs"
    echo "✅ Invoice Tests: Generation, PDF creation, delivery"
    if [ "$ENABLE_E2E" = "true" ]; then
        echo "✅ E2E Tests: Complete user workflows"
    fi
    echo ""
    echo -e "${GREEN}🚀 Billing system is ready for production!${NC}"

    # Generate test report
    echo "📋 Test Report Generated:"
    echo "  - Coverage: htmlcov/billing/index.html"
    echo "  - Locust Report: Available in Locust web UI"

    exit 0
fi
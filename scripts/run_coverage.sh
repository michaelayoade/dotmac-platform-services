#!/bin/bash
# Run coverage module by module to avoid timeout
# This combines multiple coverage runs into a single report

set -e

echo "🔍 Running modular coverage measurement..."
echo "This avoids timeouts by measuring one module at a time."
echo ""

# Remove old coverage data
rm -f .coverage .coverage.* coverage.xml 2>/dev/null || true

# List of main modules to test
MODULES=(
    "auth"
    "billing"
    "customer_management"
    "partner_management"
    "user_management"
    "tenant"
    "webhooks"
    "secrets"
    "audit"
    "core"
)

TOTAL=${#MODULES[@]}
CURRENT=0

for module in "${MODULES[@]}"; do
    CURRENT=$((CURRENT + 1))
    echo "[$CURRENT/$TOTAL] Testing $module module..."

    # Check if test directory exists
    if [ ! -d "tests/$module" ]; then
        echo "  ⏭️  Skipping (no tests found)"
        continue
    fi

    # Run tests for this module with coverage
    poetry run pytest "tests/$module/" \
        --cov="src/dotmac/platform/$module" \
        --cov-append \
        --cov-branch \
        -q \
        2>&1 | grep -E "(passed|failed|ERROR)" | head -1 || true

    echo "  ✅ Done"
done

echo ""
echo "📊 Generating combined coverage report..."

# Generate reports
poetry run coverage report --skip-covered
poetry run coverage xml
poetry run coverage html

echo ""
echo "✅ Coverage measurement complete!"
echo ""
echo "📄 Reports generated:"
echo "  - coverage.xml (for CI and scripts)"
echo "  - htmlcov/index.html (detailed HTML report)"
echo ""
echo "🔍 Check module-specific thresholds:"
echo "  poetry run python scripts/check_coverage.py coverage.xml"

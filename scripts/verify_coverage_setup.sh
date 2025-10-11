#!/bin/bash
# Verify coverage setup installation

set -e

echo "🔍 Verifying Coverage Setup"
echo "========================================"
echo ""

# Check diff-cover
echo "✓ Checking diff-cover..."
if poetry run diff-cover --version > /dev/null 2>&1; then
    VERSION=$(poetry run diff-cover --version)
    echo "  ✅ diff-cover installed: $VERSION"
else
    echo "  ❌ diff-cover not found"
    exit 1
fi

# Check coverage validation script
echo ""
echo "✓ Checking scripts/check_coverage.py..."
if poetry run python scripts/check_coverage.py --help > /dev/null 2>&1; then
    echo "  ✅ Module coverage checker working"
else
    echo "  ❌ scripts/check_coverage.py not working"
    exit 1
fi

# Check .coveragerc exists
echo ""
echo "✓ Checking .coveragerc..."
if [ -f .coveragerc ]; then
    TARGETS=$(grep -c "^\[coverage:path\." .coveragerc || true)
    echo "  ✅ .coveragerc found with $TARGETS module targets"
else
    echo "  ❌ .coveragerc not found"
    exit 1
fi

# Check Makefile commands
echo ""
echo "✓ Checking Makefile commands..."
if grep -q "test-diff:" Makefile && grep -q "test-critical:" Makefile; then
    echo "  ✅ New Makefile commands present"
else
    echo "  ❌ Makefile not updated"
    exit 1
fi

# Check documentation
echo ""
echo "✓ Checking documentation..."
DOCS_COUNT=0
[ -f docs/TESTING_STRATEGY.md ] && ((DOCS_COUNT++))
[ -f docs/COVERAGE_QUICK_START.md ] && ((DOCS_COUNT++))
[ -f docs/COVERAGE_MIGRATION_GUIDE.md ] && ((DOCS_COUNT++))
[ -f docs/COVERAGE_SUMMARY.md ] && ((DOCS_COUNT++))

if [ $DOCS_COUNT -eq 4 ]; then
    echo "  ✅ All documentation files present ($DOCS_COUNT/4)"
else
    echo "  ⚠️  Some documentation missing ($DOCS_COUNT/4)"
fi

echo ""
echo "========================================"
echo "✅ Coverage setup verification complete!"
echo ""
echo "📚 Next steps:"
echo "  1. Read: docs/COVERAGE_QUICK_START.md"
echo "  2. Try: make test-fast"
echo "  3. Test diff coverage: make test-diff"
echo ""
echo "🎯 New coverage thresholds:"
echo "  • Base: 75% (repo-wide)"
echo "  • Diff: 80% (on PR changes)"
echo "  • Critical modules: 90% (auth, secrets, tenant, webhooks)"
echo "  • Core modules: 80% (billing, CRM, audit, etc.)"
echo "  • Adapters: 70% (communications, storage, search)"
echo ""

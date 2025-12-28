#!/bin/bash
# ============================================================================
# Compare Test Results Between Runs
# ============================================================================
# Usage: ./compare-test-results.sh <baseline_dir> <current_dir>
# Example: ./compare-test-results.sh ./test-results/20241226_100000 ./test-results/20241226_110000
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <baseline_dir> <current_dir>"
    echo ""
    echo "Example: $0 ./test-results/20241226_100000 ./test-results/20241226_110000"
    exit 1
fi

BASELINE_DIR="$1"
CURRENT_DIR="$2"

if [[ ! -d "$BASELINE_DIR" ]]; then
    echo -e "${RED}Error: Baseline directory not found: $BASELINE_DIR${NC}"
    exit 1
fi

if [[ ! -d "$CURRENT_DIR" ]]; then
    echo -e "${RED}Error: Current directory not found: $CURRENT_DIR${NC}"
    exit 1
fi

echo ""
echo "=========================================="
echo "  Comparing Test Results"
echo "=========================================="
echo ""
echo -e "${BLUE}Baseline:${NC} $BASELINE_DIR"
echo -e "${BLUE}Current:${NC}  $CURRENT_DIR"
echo ""

# Track changes
NEW_PASS=0
NEW_FAIL=0
REGRESSIONS=0
FIXES=0
UNCHANGED=0

# Comparison report
REPORT_FILE="$CURRENT_DIR/comparison_report.md"

cat > "$REPORT_FILE" << EOF
# Test Results Comparison Report

**Date:** $(date)
**Baseline:** $BASELINE_DIR
**Current:** $CURRENT_DIR

## Changes Summary

EOF

echo "| Change | Endpoint | Baseline | Current |" >> "$REPORT_FILE"
echo "|--------|----------|----------|---------|" >> "$REPORT_FILE"

# Compare each result file
for file in "$CURRENT_DIR"/*.json; do
    [[ "$file" == *"summary.json" ]] && continue
    [[ "$file" == *"auth_response.json" ]] && continue
    [[ ! -f "$file" ]] && continue

    filename=$(basename "$file")
    baseline_file="$BASELINE_DIR/$filename"

    if [[ ! -f "$baseline_file" ]]; then
        # New test
        current_code=$(jq -r '.http_code // "N/A"' "$file" 2>/dev/null || echo "N/A")
        current_expected=$(jq -r '.is_expected // false' "$file" 2>/dev/null || echo "false")
        endpoint=$(jq -r '.endpoint // "unknown"' "$file" 2>/dev/null || echo "unknown")

        if [[ "$current_expected" == "true" ]]; then
            echo -e "${CYAN}[NEW PASS]${NC} $endpoint → HTTP $current_code"
            echo "| 🆕 Pass | \`$endpoint\` | N/A | $current_code |" >> "$REPORT_FILE"
            ((NEW_PASS++))
        else
            echo -e "${YELLOW}[NEW FAIL]${NC} $endpoint → HTTP $current_code"
            echo "| 🆕 Fail | \`$endpoint\` | N/A | $current_code |" >> "$REPORT_FILE"
            ((NEW_FAIL++))
        fi
        continue
    fi

    # Compare existing tests
    baseline_code=$(jq -r '.http_code // "N/A"' "$baseline_file" 2>/dev/null || echo "N/A")
    baseline_expected=$(jq -r '.is_expected // false' "$baseline_file" 2>/dev/null || echo "false")
    current_code=$(jq -r '.http_code // "N/A"' "$file" 2>/dev/null || echo "N/A")
    current_expected=$(jq -r '.is_expected // false' "$file" 2>/dev/null || echo "false")
    endpoint=$(jq -r '.endpoint // "unknown"' "$file" 2>/dev/null || echo "unknown")

    if [[ "$baseline_expected" == "true" ]] && [[ "$current_expected" == "false" ]]; then
        # Regression
        echo -e "${RED}[REGRESSION]${NC} $endpoint: HTTP $baseline_code → $current_code"
        echo "| ⬇️ Regression | \`$endpoint\` | $baseline_code ✅ | $current_code ❌ |" >> "$REPORT_FILE"
        ((REGRESSIONS++))
    elif [[ "$baseline_expected" == "false" ]] && [[ "$current_expected" == "true" ]]; then
        # Fix
        echo -e "${GREEN}[FIXED]${NC} $endpoint: HTTP $baseline_code → $current_code"
        echo "| ⬆️ Fixed | \`$endpoint\` | $baseline_code ❌ | $current_code ✅ |" >> "$REPORT_FILE"
        ((FIXES++))
    elif [[ "$baseline_code" != "$current_code" ]]; then
        # Code changed but status same
        echo -e "${YELLOW}[CHANGED]${NC} $endpoint: HTTP $baseline_code → $current_code"
        if [[ "$current_expected" == "true" ]]; then
            echo "| 🔄 Changed | \`$endpoint\` | $baseline_code | $current_code ✅ |" >> "$REPORT_FILE"
        else
            echo "| 🔄 Changed | \`$endpoint\` | $baseline_code | $current_code ❌ |" >> "$REPORT_FILE"
        fi
    else
        ((UNCHANGED++))
    fi
done

# Check for removed tests
for file in "$BASELINE_DIR"/*.json; do
    [[ "$file" == *"summary.json" ]] && continue
    [[ "$file" == *"auth_response.json" ]] && continue
    [[ ! -f "$file" ]] && continue

    filename=$(basename "$file")
    current_file="$CURRENT_DIR/$filename"

    if [[ ! -f "$current_file" ]]; then
        endpoint=$(jq -r '.endpoint // "unknown"' "$file" 2>/dev/null || echo "unknown")
        echo -e "${YELLOW}[REMOVED]${NC} $endpoint (test no longer exists)"
        echo "| ❌ Removed | \`$endpoint\` | Existed | Missing |" >> "$REPORT_FILE"
    fi
done

# Summary
cat >> "$REPORT_FILE" << EOF

## Summary

| Category | Count |
|----------|-------|
| 🔴 Regressions | $REGRESSIONS |
| 🟢 Fixes | $FIXES |
| 🆕 New Passes | $NEW_PASS |
| 🆕 New Fails | $NEW_FAIL |
| ⚪ Unchanged | $UNCHANGED |

EOF

echo ""
echo "=========================================="
echo "           COMPARISON SUMMARY"
echo "=========================================="
echo ""
echo -e "  ${RED}🔴 Regressions:${NC} $REGRESSIONS"
echo -e "  ${GREEN}🟢 Fixes:${NC}       $FIXES"
echo -e "  ${CYAN}🆕 New Passes:${NC}  $NEW_PASS"
echo -e "  ${YELLOW}🆕 New Fails:${NC}   $NEW_FAIL"
echo -e "  ⚪ Unchanged:    $UNCHANGED"
echo ""
echo "  Report saved to: $REPORT_FILE"
echo ""

if [[ $REGRESSIONS -gt 0 ]]; then
    echo -e "${RED}⚠️  REGRESSIONS DETECTED! Review the report for details.${NC}"
    exit 1
fi

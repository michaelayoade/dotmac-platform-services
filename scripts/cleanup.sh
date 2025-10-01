#!/bin/bash
# DotMac Platform Services - Code Cleanup Script
# This script organizes misplaced files and cleans up the codebase

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "========================================="
echo "DotMac Platform Services - Code Cleanup"
echo "========================================="
echo ""

# Create necessary directories if they don't exist
echo "1. Creating organized directory structure..."
mkdir -p "$PROJECT_ROOT/scripts"
mkdir -p "$PROJECT_ROOT/scripts/demos"
mkdir -p "$PROJECT_ROOT/scripts/tests"
mkdir -p "$PROJECT_ROOT/docs/api"
mkdir -p "$PROJECT_ROOT/docs/architecture"

# Move misplaced test scripts to proper location
echo ""
echo "2. Moving test scripts to scripts/tests/..."
if [ -f "$PROJECT_ROOT/test_api.py" ]; then
    mv "$PROJECT_ROOT/test_api.py" "$PROJECT_ROOT/scripts/tests/"
    echo "   ✓ Moved test_api.py"
fi

if [ -f "$PROJECT_ROOT/test_api_detailed.py" ]; then
    mv "$PROJECT_ROOT/test_api_detailed.py" "$PROJECT_ROOT/scripts/tests/"
    echo "   ✓ Moved test_api_detailed.py"
fi

# Move demo scripts
echo ""
echo "3. Moving demo scripts to scripts/demos/..."
if [ -f "$PROJECT_ROOT/demo_file_storage.py" ]; then
    mv "$PROJECT_ROOT/demo_file_storage.py" "$PROJECT_ROOT/scripts/demos/"
    echo "   ✓ Moved demo_file_storage.py"
fi

# Move test file from src to tests
echo ""
echo "4. Moving test files from src to tests directory..."
if [ -f "$PROJECT_ROOT/src/dotmac/platform/secrets/test_vault.py" ]; then
    mkdir -p "$PROJECT_ROOT/tests/secrets"
    mv "$PROJECT_ROOT/src/dotmac/platform/secrets/test_vault.py" "$PROJECT_ROOT/tests/secrets/test_vault_integration.py"
    echo "   ✓ Moved test_vault.py to tests/secrets/test_vault_integration.py"
fi

# Remove temporary TypeScript config
echo ""
echo "5. Removing temporary/alternative configs..."
if [ -f "$PROJECT_ROOT/frontend/shared/packages/rbac/tsconfig.alternative.json" ]; then
    rm "$PROJECT_ROOT/frontend/shared/packages/rbac/tsconfig.alternative.json"
    echo "   ✓ Removed tsconfig.alternative.json"
fi

# Clean Python cache files
echo ""
echo "6. Cleaning Python cache files..."
find "$PROJECT_ROOT" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$PROJECT_ROOT" -type f -name "*.pyc" -delete 2>/dev/null || true
find "$PROJECT_ROOT" -type f -name "*.pyo" -delete 2>/dev/null || true
echo "   ✓ Removed __pycache__ directories and .pyc/.pyo files"

# Clean coverage files
echo ""
echo "7. Cleaning coverage files..."
if [ -f "$PROJECT_ROOT/.coverage" ]; then
    rm "$PROJECT_ROOT/.coverage"
    echo "   ✓ Removed .coverage file"
fi

# Clean OS-specific files
echo ""
echo "8. Cleaning OS-specific files..."
find "$PROJECT_ROOT" -name ".DS_Store" -delete 2>/dev/null || true
find "$PROJECT_ROOT" -name "Thumbs.db" -delete 2>/dev/null || true
echo "   ✓ Removed .DS_Store and Thumbs.db files"

# Create .gitignore if missing entries
echo ""
echo "9. Updating .gitignore..."
if ! grep -q "__pycache__" "$PROJECT_ROOT/.gitignore" 2>/dev/null; then
    echo "__pycache__/" >> "$PROJECT_ROOT/.gitignore"
    echo "   ✓ Added __pycache__ to .gitignore"
fi

if ! grep -q ".coverage" "$PROJECT_ROOT/.gitignore" 2>/dev/null; then
    echo ".coverage" >> "$PROJECT_ROOT/.gitignore"
    echo "   ✓ Added .coverage to .gitignore"
fi

# Organize documentation
echo ""
echo "10. Organizing documentation..."
# Move architecture docs
for doc in INTEGRATION_ARCHITECTURE.md RUNTIME_EXECUTION_PATH.md INFRASTRUCTURE.md; do
    if [ -f "$PROJECT_ROOT/$doc" ]; then
        mv "$PROJECT_ROOT/$doc" "$PROJECT_ROOT/docs/architecture/"
        echo "   ✓ Moved $doc to docs/architecture/"
    fi
done

# Move API docs
for doc in FRONTEND_BACKEND_INTEGRATION.md MOCK_SERVICES_DOCUMENTATION.md; do
    if [ -f "$PROJECT_ROOT/$doc" ]; then
        mv "$PROJECT_ROOT/$doc" "$PROJECT_ROOT/docs/api/"
        echo "   ✓ Moved $doc to docs/api/"
    fi
done

echo ""
echo "========================================="
echo "Cleanup completed successfully!"
echo "========================================="
echo ""
echo "Summary of changes:"
echo "  • Test scripts moved to scripts/tests/"
echo "  • Demo scripts moved to scripts/demos/"
echo "  • Test file moved from src/ to tests/"
echo "  • Python cache files cleaned"
echo "  • Documentation organized into docs/"
echo ""
echo "Recommended next steps:"
echo "  1. Review moved files in their new locations"
echo "  2. Update any import paths if necessary"
echo "  3. Commit the changes: git add -A && git commit -m 'chore: organize project structure'"
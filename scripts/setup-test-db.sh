#!/bin/bash
#
# Setup Test Database with Schema
#
# This script creates a fresh SQLite test database with all migrations applied.
# Use this when running billing tests that require database tables.
#
# Usage:
#   ./scripts/setup-test-db.sh
#
# Then run tests with:
#   DATABASE_URL=sqlite:////tmp/test_billing.db pytest tests/billing/
#

set -e

DB_PATH="${TEST_DB_PATH:-/tmp/test_billing.db}"

echo "🗄️  Setting up test database at $DB_PATH"

# Remove existing database
if [ -f "$DB_PATH" ]; then
    echo "📝 Removing existing database..."
    rm "$DB_PATH"
fi

# Run migrations
echo "🔄 Running Alembic migrations..."
DATABASE_URL="sqlite:///$DB_PATH" .venv/bin/alembic upgrade head

# Verify tables
echo "✅ Database created with the following billing tables:"
sqlite3 "$DB_PATH" ".tables" | tr ' ' '\n' | grep -E "(payment|invoice|billing|receipt|subscription)" | sort

echo ""
echo "✨ Test database ready!"
echo ""
echo "Run tests with:"
echo "  DATABASE_URL=sqlite:///$DB_PATH pytest tests/billing/"
echo ""
echo "Or export the variable:"
echo "  export DATABASE_URL=sqlite:///$DB_PATH"
echo "  pytest tests/billing/"

#!/bin/bash
set -e  # Exit on any error

echo "🚀 Starting Expense Manager Web App..."

# Force production environment and unset any dev environment variables
export ENV=production
unset ENVIRONMENT
unset NODE_ENV

echo "🔧 Environment variables set:"
echo "  ENV=$ENV"
echo "  DATABASE_URL=$DATABASE_URL"

# Wait for database to be ready (with timeout)
echo "⏳ Waiting for database connection..."
timeout 30 bash -c 'until alembic current > /dev/null 2>&1; do sleep 2; done' || {
    echo "❌ Database connection timeout after 30 seconds"
    echo "🔄 Proceeding with application startup anyway..."
}

# Fix database schema if needed
echo "🔧 Checking and fixing database schema..."
if python fix_production_schema.py; then
    echo "✅ Database schema fix completed"
else
    echo "⚠️  Database schema fix failed, trying SQL approach..."
    # Try running the SQL fix directly
    if command -v psql >/dev/null 2>&1; then
        echo "🔧 Running SQL schema fix..."
        psql $DATABASE_URL -f fix_schema.sql || echo "⚠️  SQL schema fix failed"
    else
        echo "⚠️  psql not available, skipping SQL schema fix"
    fi
fi

# Stamp the database with the latest migration version
# This updates the alembic_version table without running migrations
echo "📝 Stamping database with latest migration version..."
if python stamp_migrations.py; then
    echo "✅ Database stamped successfully"
else
    echo "⚠️  Database stamp failed, migrations may run and fail"
fi

# Start the application
echo "🌐 Starting application server..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT
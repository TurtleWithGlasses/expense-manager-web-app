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
# Using a simple Python script to test connection instead of alembic
echo "⏳ Waiting for database connection..."
timeout 30 bash -c 'until python -c "
import os
import sys
try:
    from sqlalchemy import create_engine, text
    engine = create_engine(
        os.getenv(\"DATABASE_URL\"),
        connect_args={\"connect_timeout\": 5},
        pool_pre_ping=True
    )
    with engine.connect() as conn:
        conn.execute(text(\"SELECT 1\"))
    sys.exit(0)
except Exception as e:
    print(f\"Connection failed: {e}\", file=sys.stderr)
    sys.exit(1)
" 2>&1; do sleep 2; done' || {
    echo "❌ Database connection timeout after 30 seconds"
    echo "🔄 Proceeding with application startup anyway..."
}

# Fix database schema if needed (with timeout to prevent hanging)
echo "🔧 Checking and fixing database schema..."
if timeout 60 python fix_production_schema.py; then
    echo "✅ Database schema fix completed"

    # Stamp the database with the latest migration version
    # This updates the alembic_version table without running migrations
    echo "📝 Stamping database with latest migration version..."
    if timeout 30 python stamp_migrations.py; then
        echo "✅ Database stamped successfully"
    else
        echo "⚠️  Database stamp failed, migrations may run and fail"
    fi
else
    echo "⚠️  Database schema fix failed or timed out"
    echo "⚠️  The application will attempt to run migrations on startup"
fi

# Start the application
echo "🌐 Starting application server..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT
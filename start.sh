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
    echo "⚠️  Database schema fix failed, but continuing with startup..."
fi

# Run migrations with error handling
echo "📊 Running database migrations..."
if alembic upgrade head; then
    echo "✅ Database migrations completed successfully"
else
    echo "⚠️  Database migration failed, but continuing with startup..."
fi

# Start the application
echo "🌐 Starting application server..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT
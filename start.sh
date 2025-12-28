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

# Note: Database connection checks are skipped during container startup
# because Railway's database might not be immediately accessible.
# The application will handle the connection when it starts.
echo "ℹ️  Skipping pre-startup database checks"
echo "ℹ️  Database connection will be established when the app starts"

# Run database migrations
echo "📊 Running database migrations..."
alembic upgrade head
echo "✅ Migrations completed successfully"

# Seed gamification data (achievements and badges)
echo "🎮 Seeding gamification data..."
python -m app.seeds.gamification_seeds
echo "✅ Gamification data seeded successfully"

# Start the application
echo "🌐 Starting application server..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT
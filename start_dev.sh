#!/bin/bash

echo "Starting Expense Manager Web App..."
echo ""

# Activate virtual environment if it exists
if [ -f .venv/Scripts/activate ]; then
    source .venv/Scripts/activate
elif [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
fi

# Set environment variables
export DATABASE_URL="sqlite:///./app.db"
export ENV="dev"

# Run the application
python run_local.py

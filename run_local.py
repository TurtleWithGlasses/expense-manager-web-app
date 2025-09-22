#!/usr/bin/env python3
"""
Local development runner for the expense manager app.
This ensures SQLite is used instead of PostgreSQL.
"""

import os
import sys
import uvicorn

# Force SQLite for local development
os.environ["DATABASE_URL"] = "sqlite:///./app.db"
os.environ["ENV"] = "dev"

if __name__ == "__main__":
    print("🚀 Starting Expense Manager Web App locally...")
    print("📊 Using SQLite database: app.db")
    print("🌐 Server will be available at: http://127.0.0.1:8000")
    print("=" * 50)
    
    try:
        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)
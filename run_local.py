#!/usr/bin/env python3
"""
Local development runner for the Expense Manager app.
This script sets up the environment for local development with SQLite.
"""

import os
import subprocess
import sys

def main():
    # Set environment variables for local development
    os.environ["DATABASE_URL"] = "sqlite:///./app.db"
    os.environ["SECRET_KEY"] = "mysecretkey"
    os.environ["SESSION_COOKIE_NAME"] = "em_session"
    os.environ["SESSION_MAX_AGE_SECONDS"] = "2592000"
    os.environ["ENV"] = "dev"
    
    print("🚀 Starting Expense Manager in local development mode...")
    print("📊 Using SQLite database: app.db")
    print("🌐 Server will be available at: http://localhost:8000")
    print("🔄 Auto-reload enabled")
    print("-" * 50)
    
    try:
        # Run the application
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

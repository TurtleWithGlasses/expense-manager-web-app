#!/usr/bin/env python3
"""
Reset the database for local development.
This will delete the existing SQLite database and recreate it.
"""

import os
import sys

# Force SQLite for local development
os.environ["DATABASE_URL"] = "sqlite:///./app.db"

def reset_database():
    """Reset the database by deleting the SQLite file and recreating tables"""
    try:
        # Import after setting environment variable
        from app.db.engine import engine
        from app.db.base import Base
        
        # Delete existing database file if it exists
        db_file = "app.db"
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"🗑️  Deleted existing database: {db_file}")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
        print("🎉 Database reset complete!")
        print("You can now run the app with: python run_local.py")
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🔄 Resetting database for local development...")
    reset_database()

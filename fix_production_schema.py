#!/usr/bin/env python3
"""
Script to fix production database schema by adding missing email verification columns.
This can be run directly in production to add the missing columns.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

def fix_production_schema():
    """Add missing email verification columns to the users table."""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not found")
        return False
    
    print(f"🔧 Connecting to database: {database_url[:50]}...")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            print("✅ Connected to database successfully")
            
            # List of columns to add
            columns_to_add = [
                {
                    'name': 'is_verified',
                    'definition': 'BOOLEAN NOT NULL DEFAULT false',
                    'check_query': "SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'is_verified'"
                },
                {
                    'name': 'verification_token',
                    'definition': 'VARCHAR(255)',
                    'check_query': "SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'verification_token'"
                },
                {
                    'name': 'verification_token_expires',
                    'definition': 'TIMESTAMP',
                    'check_query': "SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'verification_token_expires'"
                },
                {
                    'name': 'password_reset_token',
                    'definition': 'VARCHAR(255)',
                    'check_query': "SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'password_reset_token'"
                },
                {
                    'name': 'password_reset_expires',
                    'definition': 'TIMESTAMP',
                    'check_query': "SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'password_reset_expires'"
                },
                {
                    'name': 'created_at',
                    'definition': 'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP',
                    'check_query': "SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'created_at'"
                }
            ]
            
            # Add each column if it doesn't exist
            for column in columns_to_add:
                try:
                    # Check if column exists
                    result = connection.execute(text(column['check_query']))
                    if result.fetchone():
                        print(f"ℹ️  Column '{column['name']}' already exists")
                    else:
                        # Add the column
                        alter_query = f"ALTER TABLE users ADD COLUMN {column['name']} {column['definition']}"
                        connection.execute(text(alter_query))
                        connection.commit()
                        print(f"✅ Added column '{column['name']}'")
                        
                except Exception as e:
                    print(f"⚠️  Error adding column '{column['name']}': {e}")
            
            print("🎉 Database schema fix completed!")
            return True
            
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Fixing production database schema...")
    success = fix_production_schema()
    if success:
        print("✅ Schema fix completed successfully!")
        sys.exit(0)
    else:
        print("❌ Schema fix failed!")
        sys.exit(1)

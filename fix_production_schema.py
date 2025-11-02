#!/usr/bin/env python3
"""
Script to fix production database schema by adding missing columns.
This can be run directly in production to add the missing columns including:
- Email verification columns to users table
- Avatar URL column to users table
- AI-related columns to entries table
- Theme column to user_preferences table
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

def fix_production_schema():
    """Add missing columns to the database tables (email verification, avatar URL, AI columns, and theme column)."""
    
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
            
            # List of columns to add to users table
            users_columns_to_add = [
                {
                    'table': 'users',
                    'name': 'is_verified',
                    'definition': 'BOOLEAN NOT NULL DEFAULT false',
                    'check_query': "SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'is_verified'"
                },
                {
                    'table': 'users',
                    'name': 'verification_token',
                    'definition': 'VARCHAR(255)',
                    'check_query': "SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'verification_token'"
                },
                {
                    'table': 'users',
                    'name': 'verification_token_expires',
                    'definition': 'TIMESTAMP',
                    'check_query': "SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'verification_token_expires'"
                },
                {
                    'table': 'users',
                    'name': 'password_reset_token',
                    'definition': 'VARCHAR(255)',
                    'check_query': "SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'password_reset_token'"
                },
                {
                    'table': 'users',
                    'name': 'password_reset_expires',
                    'definition': 'TIMESTAMP',
                    'check_query': "SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'password_reset_expires'"
                },
                {
                    'table': 'users',
                    'name': 'created_at',
                    'definition': 'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP',
                    'check_query': "SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'created_at'"
                },
                {
                    'table': 'users',
                    'name': 'avatar_url',
                    'definition': 'VARCHAR(500)',
                    'check_query': "SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'avatar_url'"
                }
            ]
            
            # List of AI columns to add to entries table
            entries_ai_columns_to_add = [
                {
                    'table': 'entries',
                    'name': 'ai_suggested_category_id',
                    'definition': 'INTEGER',
                    'check_query': "SELECT column_name FROM information_schema.columns WHERE table_name = 'entries' AND column_name = 'ai_suggested_category_id'"
                },
                {
                    'table': 'entries',
                    'name': 'ai_confidence_score',
                    'definition': 'NUMERIC(3,2)',
                    'check_query': "SELECT column_name FROM information_schema.columns WHERE table_name = 'entries' AND column_name = 'ai_confidence_score'"
                },
                {
                    'table': 'entries',
                    'name': 'merchant_name',
                    'definition': 'VARCHAR(255)',
                    'check_query': "SELECT column_name FROM information_schema.columns WHERE table_name = 'entries' AND column_name = 'merchant_name'"
                },
                {
                    'table': 'entries',
                    'name': 'location_data',
                    'definition': 'TEXT',
                    'check_query': "SELECT column_name FROM information_schema.columns WHERE table_name = 'entries' AND column_name = 'location_data'"
                },
                {
                    'table': 'entries',
                    'name': 'ai_processed',
                    'definition': 'BOOLEAN NOT NULL DEFAULT false',
                    'check_query': "SELECT column_name FROM information_schema.columns WHERE table_name = 'entries' AND column_name = 'ai_processed'"
                }
            ]

            # List of columns to add to user_preferences table
            user_preferences_columns_to_add = [
                {
                    'table': 'user_preferences',
                    'name': 'theme',
                    'definition': "VARCHAR(10) DEFAULT 'dark'",
                    'check_query': "SELECT column_name FROM information_schema.columns WHERE table_name = 'user_preferences' AND column_name = 'theme'"
                }
            ]

            # Combine all columns to add
            all_columns_to_add = users_columns_to_add + entries_ai_columns_to_add + user_preferences_columns_to_add
            
            # Add each column if it doesn't exist
            for column in all_columns_to_add:
                try:
                    # Check if column exists
                    result = connection.execute(text(column['check_query']))
                    if result.fetchone():
                        print(f"ℹ️  Column '{column['name']}' in table '{column['table']}' already exists")
                    else:
                        # Add the column
                        alter_query = f"ALTER TABLE {column['table']} ADD COLUMN {column['name']} {column['definition']}"
                        connection.execute(text(alter_query))
                        connection.commit()
                        print(f"✅ Added column '{column['name']}' to table '{column['table']}'")
                        
                except Exception as e:
                    print(f"⚠️  Error adding column '{column['name']}' to table '{column['table']}': {e}")
            
            # Add foreign key constraint for ai_suggested_category_id if the column was added
            try:
                # Check if the foreign key constraint already exists
                fk_check_query = """
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name = 'entries' 
                AND constraint_type = 'FOREIGN KEY' 
                AND constraint_name LIKE '%ai_suggested_category_id%'
                """
                result = connection.execute(text(fk_check_query))
                if not result.fetchone():
                    # Check if the column exists before adding the constraint
                    column_check = connection.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'entries' AND column_name = 'ai_suggested_category_id'"))
                    if column_check.fetchone():
                        # Add the foreign key constraint
                        fk_query = "ALTER TABLE entries ADD CONSTRAINT fk_entries_ai_suggested_category_id FOREIGN KEY (ai_suggested_category_id) REFERENCES categories(id) ON DELETE SET NULL"
                        connection.execute(text(fk_query))
                        connection.commit()
                        print("✅ Added foreign key constraint for ai_suggested_category_id")
                    else:
                        print("ℹ️  ai_suggested_category_id column not found, skipping foreign key constraint")
                else:
                    print("ℹ️  Foreign key constraint for ai_suggested_category_id already exists")
            except Exception as e:
                print(f"⚠️  Error adding foreign key constraint: {e}")
            
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

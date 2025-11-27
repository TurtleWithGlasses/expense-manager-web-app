#!/usr/bin/env python
"""
Script to fix multiple Alembic migration heads in the PRODUCTION database (Railway).

This script connects to the production PostgreSQL database and fixes the multiple heads issue.
"""
import os
import sys
sys.path.insert(0, os.getcwd())

from sqlalchemy import create_engine, text, inspect

def fix_production_heads():
    """Fix multiple heads in production database"""
    print("=" * 70)
    print("Production Database Multiple Heads Fix")
    print("=" * 70)
    
    # Get database URL directly from environment (bypass app config)
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("\n❌ DATABASE_URL environment variable not set!")
        print("   Please set it to your production database URL:")
        print("   export DATABASE_URL='postgresql://user:pass@host:port/dbname'")
        return False
    
    print(f"\n📊 Database URL: {database_url[:50]}...")
    
    # Detect database type
    is_postgresql = 'postgresql' in database_url.lower() or 'postgres' in database_url.lower()
    is_sqlite = 'sqlite' in database_url.lower()
    
    if not is_postgresql and not is_sqlite:
        print("\n⚠️  WARNING: Unknown database type!")
        response = input("\n   Continue anyway? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("   ❌ Cancelled.")
            return False
    
    # Create engine
    try:
        engine = create_engine(database_url)
        print("\n✓ Connected to database")
    except Exception as e:
        print(f"\n❌ Failed to connect to database: {e}")
        return False
    
    # Check current state
    print("\n" + "=" * 70)
    print("Checking current state...")
    print("=" * 70)
    
    try:
        with engine.connect() as connection:
            # Check if alembic_version table exists (database-agnostic)
            inspector = inspect(engine)
            table_exists = 'alembic_version' in inspector.get_table_names()
            
            if not table_exists:
                print("\n❌ alembic_version table does not exist!")
                print("   This is unexpected. The database may not have migrations initialized.")
                return False
            
            # Get all version records
            result = connection.execute(text("SELECT version_num FROM alembic_version"))
            versions = [row[0] for row in result.fetchall()]
            
            print(f"\n📊 Current versions in database: {versions}")
            print(f"📊 Number of heads: {len(versions)}")
            
            if len(versions) == 1 and versions[0] == 'a1b2c3d4e5f6':
                print("\n✅ Database is already at the merge migration!")
                print("   No fix needed.")
                return True
            
            if len(versions) > 1:
                print("\n⚠️  WARNING: Multiple heads detected!")
                print("   This needs to be fixed by merging to: a1b2c3d4e5f6")
            else:
                print(f"\n⚠️  Current version: {versions[0] if versions else 'None'}")
                print("   Needs to be updated to: a1b2c3d4e5f6")
            
            # Ask for confirmation
            print("\n" + "=" * 70)
            print("FIX OPERATION:")
            print("=" * 70)
            print("\nThis will:")
            print("  1. Delete all current version records")
            print("  2. Insert the merge migration: a1b2c3d4e5f6")
            print("\n⚠️  WARNING: This modifies the production database!")
            print("   Make sure your database schema is already up-to-date.")
            print("   This only fixes version tracking, not the schema.")
            
            response = input("\nDo you want to proceed? (yes/no): ").strip().lower()
            
            if response not in ['yes', 'y']:
                print("\n❌ Fix cancelled by user.")
                return False
            
            # Perform the fix
            print("\n" + "=" * 70)
            print("Applying fix...")
            print("=" * 70)
            
            # Use a transaction
            with connection.begin():
                # Delete all current version records
                connection.execute(text("DELETE FROM alembic_version"))
                print("   ✓ Cleared existing version records")
                
                # Insert the merge migration
                connection.execute(text("""
                    INSERT INTO alembic_version (version_num) 
                    VALUES ('a1b2c3d4e5f6')
                """))
                print("   ✓ Stamped database to merge migration: a1b2c3d4e5f6")
            
            # Verify the fix
            print("\n" + "=" * 70)
            print("Verifying fix...")
            print("=" * 70)
            
            result = connection.execute(text("SELECT version_num FROM alembic_version"))
            new_versions = [row[0] for row in result.fetchall()]
            
            print(f"\n📊 New versions in database: {new_versions}")
            
            if len(new_versions) == 1 and new_versions[0] == 'a1b2c3d4e5f6':
                print("\n✅ SUCCESS! Multiple heads fixed in production database.")
                print("   The database is now at the merge migration.")
                print("   The warning should be gone on the next deployment restart.")
                return True
            else:
                print("\n❌ Fix verification failed")
                print("   Expected: ['a1b2c3d4e5f6']")
                print(f"   Got: {new_versions}")
                return False
                
    except Exception as e:
        print(f"\n❌ Error during fix: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("⚠️  PRODUCTION DATABASE FIX SCRIPT")
    print("=" * 70)
    print("\nThis script will fix multiple Alembic heads in the PRODUCTION database.")
    print("\n📋 USAGE:")
    print("  1. Set DATABASE_URL environment variable to your production database:")
    print("     export DATABASE_URL='postgresql://user:pass@host:port/dbname'")
    print("  2. Run this script: python fix_production_heads.py")
    print("\n⚠️  IMPORTANT:")
    print("  1. Verify that your database schema is up-to-date")
    print("  2. Have a backup of your production database")
    print("  3. This only fixes version tracking, not the schema")
    
    response = input("\nAre you ready to proceed? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        success = fix_production_heads()
        if success:
            print("\n✅ Done! Production database is fixed.")
            print("   The next deployment should start without the warning.")
        else:
            print("\n❌ Fix failed. Please check the error messages above.")
    else:
        print("\n❌ Cancelled by user.")


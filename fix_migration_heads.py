#!/usr/bin/env python
"""
Manual script to fix multiple Alembic migration heads in the database.

This script will:
1. Check the current state of the alembic_version table
2. Show what needs to be fixed
3. Optionally fix it by stamping to the correct merge migration
"""
import os
import sys
sys.path.insert(0, os.getcwd())

from sqlalchemy import create_engine, text
from alembic import command
from alembic.config import Config
from app.core.config import settings
from app.db.engine import engine

def check_current_state():
    """Check what's currently in the alembic_version table"""
    print("=" * 60)
    print("Checking current database state...")
    print("=" * 60)
    
    with engine.connect() as connection:
        # Check if alembic_version table exists
        result = connection.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='alembic_version'
        """))
        table_exists = result.fetchone() is not None
        
        if not table_exists:
            print("❌ alembic_version table does not exist!")
            return None
        
        # Get all version records
        result = connection.execute(text("SELECT version_num FROM alembic_version"))
        versions = [row[0] for row in result.fetchall()]
        
        print(f"\n📊 Current versions in database: {versions}")
        print(f"📊 Number of heads: {len(versions)}")
        
        if len(versions) > 1:
            print("\n⚠️  WARNING: Multiple heads detected!")
            print("   This needs to be fixed by merging to: a1b2c3d4e5f6")
        elif len(versions) == 1:
            print(f"\n✓ Single head: {versions[0]}")
            if versions[0] == 'a1b2c3d4e5f6':
                print("   ✓ Already at the merge migration - no fix needed!")
            else:
                print("   ⚠️  Not at the merge migration yet")
        else:
            print("\n⚠️  No version recorded - database may need initial stamping")
        
        return versions

def fix_multiple_heads():
    """Fix multiple heads by stamping to the merge migration"""
    print("\n" + "=" * 60)
    print("Fixing multiple heads...")
    print("=" * 60)
    
    # Get Alembic config
    project_root = os.path.dirname(os.path.abspath(__file__))
    alembic_ini_path = os.path.join(project_root, "alembic.ini")
    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("script_location", os.path.join(project_root, "alembic"))
    
    # Check current state first
    versions = check_current_state()
    
    if versions is None:
        print("\n❌ Cannot proceed - alembic_version table doesn't exist")
        return False
    
    if len(versions) == 1 and versions[0] == 'a1b2c3d4e5f6':
        print("\n✓ Already fixed - no action needed!")
        return True
    
    print("\n🔧 Attempting to fix...")
    print("   Strategy: Delete all current heads and stamp to merge migration")
    
    try:
        with engine.connect() as connection:
            # Delete all current version records
            connection.execute(text("DELETE FROM alembic_version"))
            connection.commit()
            print("   ✓ Cleared existing version records")
            
            # Insert the merge migration as the single head
            connection.execute(text("""
                INSERT INTO alembic_version (version_num) 
                VALUES ('a1b2c3d4e5f6')
            """))
            connection.commit()
            print("   ✓ Stamped database to merge migration: a1b2c3d4e5f6")
        
        # Verify the fix
        print("\n" + "=" * 60)
        print("Verifying fix...")
        print("=" * 60)
        new_versions = check_current_state()
        
        if new_versions and len(new_versions) == 1 and new_versions[0] == 'a1b2c3d4e5f6':
            print("\n✅ SUCCESS! Multiple heads fixed.")
            print("   The database is now at the merge migration.")
            print("   You can restart the server - the warning should be gone.")
            return True
        else:
            print("\n❌ Fix verification failed")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during fix: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("Alembic Multiple Heads Fix Script")
    print("=" * 60)
    
    # Check current state
    versions = check_current_state()
    
    if versions is None:
        print("\n⚠️  Cannot proceed - database issue")
        return
    
    if len(versions) == 1 and versions[0] == 'a1b2c3d4e5f6':
        print("\n✓ Database is already at the correct state!")
        return
    
    # Ask for confirmation
    print("\n" + "=" * 60)
    print("FIX OPTIONS:")
    print("=" * 60)
    print("\nThis script can fix the multiple heads by:")
    print("  1. Clearing all version records")
    print("  2. Stamping to the merge migration: a1b2c3d4e5f6")
    print("\n⚠️  WARNING: This will modify the alembic_version table!")
    print("   Make sure your database schema is already up-to-date.")
    print("   This only fixes the version tracking, not the schema itself.")
    
    response = input("\nDo you want to proceed with the fix? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        success = fix_multiple_heads()
        if success:
            print("\n✅ Done! You can now restart your server.")
        else:
            print("\n❌ Fix failed. Please check the error messages above.")
    else:
        print("\n❌ Fix cancelled by user.")

if __name__ == "__main__":
    main()


#!/usr/bin/env python
"""
Simple script to fix multiple Alembic heads - validates URL first.
"""
import os
import sys
sys.path.insert(0, os.getcwd())

from sqlalchemy import create_engine, text, inspect

def main():
    print("=" * 70)
    print("Simple Production Database Fix")
    print("=" * 70)
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("\n❌ DATABASE_URL not set!")
        print("\nPlease set it using:")
        print("  PowerShell: $env:DATABASE_URL = 'postgresql://...'")
        print("  Bash: export DATABASE_URL='postgresql://...'")
        return
    
    # Validate URL
    print(f"\n📊 Database URL: {database_url[:60]}...")
    
    if 'railway.internal' in database_url:
        print("\n❌ ERROR: You're using the INTERNAL Railway URL!")
        print("   Internal URLs (with 'railway.internal') don't work from your local machine.")
        print("\n✅ SOLUTION:")
        print("   1. Go to Railway Dashboard → PostgreSQL → Connect")
        print("   2. Click 'Public Network' tab (NOT Private Network)")
        print("   3. Click 'show' next to 'Connection URL'")
        print("   4. Copy the URL that has 'maglev.proxy.rlwy.net' in it")
        print("   5. Use that URL (not the internal one)")
        print("\n   Example of CORRECT public URL:")
        print("   postgresql://postgres:password@maglev.proxy.rlwy.net:29009/railway")
        return
    
    if 'maglev.proxy.rlwy.net' not in database_url and 'postgresql' in database_url:
        print("\n⚠️  WARNING: This doesn't look like Railway's public URL.")
        print("   Make sure you're using the PUBLIC network URL from Railway.")
        response = input("\nContinue anyway? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            return
    
    # Try to connect and fix
    print("\n✓ URL looks correct (public network)")
    print("\nConnecting to database...")
    
    try:
        engine = create_engine(database_url)
        
        # First, check current state (read-only)
        with engine.connect() as connection:
            # Check if table exists
            inspector = inspect(engine)
            if 'alembic_version' not in inspector.get_table_names():
                print("\n❌ alembic_version table doesn't exist!")
                return
            
            # Get current versions
            result = connection.execute(text("SELECT version_num FROM alembic_version"))
            versions = [row[0] for row in result.fetchall()]
            
            print(f"\n📊 Current versions: {versions}")
            
            if len(versions) == 1 and versions[0] == 'a1b2c3d4e5f6':
                print("\n✅ Already fixed! Database is at merge migration.")
                return
            
            if len(versions) > 1:
                print(f"\n⚠️  Multiple heads detected: {versions}")
            else:
                print(f"\n⚠️  Current version: {versions[0] if versions else 'None'}")
            
            print("\nThis will fix the multiple heads by setting to: a1b2c3d4e5f6")
            response = input("\nProceed? (yes/no): ").strip().lower()
            
            if response not in ['yes', 'y']:
                print("Cancelled.")
                return
        
        # Now do the fix in a transaction
        print("\n🔧 Fixing...")
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM alembic_version"))
            connection.execute(text("INSERT INTO alembic_version (version_num) VALUES ('a1b2c3d4e5f6')"))
        
        # Verify the fix
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version_num FROM alembic_version"))
            new_versions = [row[0] for row in result.fetchall()]
            
            if len(new_versions) == 1 and new_versions[0] == 'a1b2c3d4e5f6':
                print("\n✅ SUCCESS! Multiple heads fixed.")
                print("   Database is now at: a1b2c3d4e5f6")
                print("   The warning should be gone on next deployment.")
            else:
                print(f"\n❌ Fix failed. Got: {new_versions}")
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if 'could not translate host name' in str(e).lower():
            print("\n💡 This usually means you're using the INTERNAL URL.")
            print("   Use the PUBLIC URL from Railway's 'Public Network' tab!")

if __name__ == "__main__":
    main()


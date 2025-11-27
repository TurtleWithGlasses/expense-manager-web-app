#!/usr/bin/env python
"""
Quick script to check the current Alembic migration status.
This helps determine if the automatic upgrade has finished.
"""
import os
import sys
sys.path.insert(0, os.getcwd())

from sqlalchemy import create_engine, text
from alembic.script import ScriptDirectory
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from app.core.config import settings
from app.db.engine import engine

def check_status():
    """Check the current migration status"""
    print("=" * 70)
    print("Alembic Migration Status Check")
    print("=" * 70)
    
    # Get Alembic config
    project_root = os.path.dirname(os.path.abspath(__file__))
    alembic_ini_path = os.path.join(project_root, "alembic.ini")
    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("script_location", os.path.join(project_root, "alembic"))
    
    script = ScriptDirectory.from_config(alembic_cfg)
    
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        
        # Check database version(s)
        print("\n📊 DATABASE STATE:")
        print("-" * 70)
        try:
            current_rev = context.get_current_revision()
            print(f"   Current revision: {current_rev}")
            multiple_heads = False
        except Exception as e:
            if "more than one head" in str(e).lower():
                multiple_heads = True
                current_heads = context.get_current_heads()
                print(f"   ⚠️  Multiple heads detected: {current_heads}")
                print(f"   Number of heads: {len(current_heads)}")
            else:
                print(f"   ❌ Error getting current revision: {e}")
                return
        
        # Check script heads
        print("\n📋 MIGRATION SCRIPT STATE:")
        print("-" * 70)
        script_heads = list(script.get_heads())
        print(f"   Script heads: {script_heads}")
        print(f"   Number of script heads: {len(script_heads)}")
        
        if len(script_heads) == 1:
            target_head = script_heads[0]
            print(f"   Target head: {target_head}")
        else:
            print(f"   ⚠️  Multiple script heads - merge needed")
            target_head = None
        
        # Determine status
        print("\n🎯 STATUS:")
        print("-" * 70)
        
        if multiple_heads:
            print("   ❌ NOT FINISHED - Database still has multiple heads")
            print("   ⚠️  The automatic upgrade may still be running or failed")
            print("\n   💡 RECOMMENDATION:")
            print("      - Wait a bit longer if the server is still running")
            print("      - Or use the manual fix script: python fix_migration_heads.py")
        elif len(script_heads) > 1:
            print("   ⚠️  Script has multiple heads (this is expected)")
            print("   ✓ Database has single head")
            if target_head:
                try:
                    current_rev = context.get_current_revision()
                    if current_rev == target_head:
                        print(f"   ✅ Database is at target head: {target_head}")
                    else:
                        print(f"   ⚠️  Database at {current_rev}, target is {target_head}")
                except:
                    pass
        else:
            try:
                current_rev = context.get_current_revision()
                if target_head and current_rev == target_head:
                    print(f"   ✅ FINISHED - Database is at target head: {target_head}")
                    print("   ✓ No further action needed")
                    print("   ✓ You can restart the server - warning should be gone")
                elif target_head:
                    print(f"   ⚠️  Database at {current_rev}, target is {target_head}")
                    print("   ⚠️  Upgrade may still be in progress")
                else:
                    print(f"   ⚠️  Database at {current_rev}")
            except Exception as e:
                print(f"   ❌ Error checking status: {e}")
        
        # Check if we're at the merge migration
        print("\n🔍 DETAILED CHECK:")
        print("-" * 70)
        try:
            current_rev = context.get_current_revision()
            if current_rev == 'a1b2c3d4e5f6':
                print("   ✅ Database is at the merge migration (a1b2c3d4e5f6)")
                print("   ✅ Multiple heads issue is RESOLVED!")
            else:
                print(f"   Current: {current_rev}")
                print(f"   Target merge: a1b2c3d4e5f6")
                if current_rev != 'a1b2c3d4e5f6':
                    print("   ⚠️  Not at merge migration yet")
        except:
            if multiple_heads:
                print("   ⚠️  Still has multiple heads - not at merge migration")
        
        # Show what's in the version table
        print("\n📝 VERSION TABLE CONTENTS:")
        print("-" * 70)
        try:
            result = connection.execute(text("SELECT version_num FROM alembic_version"))
            versions = [row[0] for row in result.fetchall()]
            if versions:
                for v in versions:
                    print(f"   - {v}")
            else:
                print("   (empty)")
        except Exception as e:
            print(f"   ❌ Error reading version table: {e}")

if __name__ == "__main__":
    try:
        check_status()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


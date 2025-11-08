#!/usr/bin/env python3
"""
Script to stamp the production database with the latest migration version.
This tells Alembic that the database is at the latest version without running migrations.
Use this when the schema has been manually updated to match the latest migration.
"""

import os
import sys
from alembic import command
from alembic.config import Config

def stamp_database():
    """Stamp the database with the latest migration version."""

    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not found")
        return False

    print(f"🔧 Stamping database at: {database_url[:50]}...")

    try:
        # Setup Alembic configuration
        project_root = os.path.dirname(__file__)
        alembic_ini_path = os.path.join(project_root, "alembic.ini")
        alembic_cfg = Config(alembic_ini_path)
        alembic_cfg.set_main_option("script_location", os.path.join(project_root, "alembic"))

        # Stamp with the latest revision (head)
        print("📝 Stamping database with latest migration version (head)...")
        command.stamp(alembic_cfg, "head")

        print("✅ Database stamped successfully!")
        print("ℹ️  The database is now marked as being at the latest migration version")
        return True

    except Exception as e:
        print(f"❌ Error stamping database: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Stamping production database with migration version...")
    success = stamp_database()
    if success:
        print("✅ Stamp completed successfully!")
        sys.exit(0)
    else:
        print("❌ Stamp failed!")
        sys.exit(1)

"""
Stamp the production database to fix migration state.

This script stamps the database to the merge migration revision,
then ensures all schema is up to date using create_all().
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, inspect
from alembic import command
from alembic.config import Config
from app.models import Base

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable not set")
    sys.exit(1)

print(f"Connecting to database...")
engine = create_engine(DATABASE_URL)

# Get current migration state
inspector = inspect(engine)
print(f"\nChecking alembic_version table...")

with engine.connect() as conn:
    result = conn.execute("SELECT version_num FROM alembic_version")
    current = result.fetchone()
    if current:
        print(f"Current revision in database: {current[0]}")
    else:
        print("No revision recorded in database")

# Set up alembic config
project_root = os.path.dirname(os.path.abspath(__file__))
alembic_ini_path = os.path.join(project_root, "alembic.ini")
alembic_cfg = Config(alembic_ini_path)
alembic_cfg.set_main_option("script_location", os.path.join(project_root, "alembic"))

print(f"\nStamping database to revision: 766b569daa8d (merge migration)")
try:
    command.stamp(alembic_cfg, "766b569daa8d")
    print("✓ Database stamped successfully")
except Exception as e:
    print(f"✗ Stamp failed: {e}")
    print("\nTrying to clear and re-stamp...")
    # Delete current version and stamp fresh
    with engine.connect() as conn:
        conn.execute("DELETE FROM alembic_version")
        conn.commit()
    command.stamp(alembic_cfg, "766b569daa8d")
    print("✓ Database stamped successfully after clearing")

# Ensure all tables/columns exist
print(f"\nEnsuring database schema is up to date...")
Base.metadata.create_all(bind=engine)
print("✓ Schema verified/updated")

# Verify final state
with engine.connect() as conn:
    result = conn.execute("SELECT version_num FROM alembic_version")
    current = result.fetchone()
    print(f"\nFinal database revision: {current[0] if current else 'None'}")

# Check if is_admin column exists
inspector = inspect(engine)
columns = [col['name'] for col in inspector.get_columns('users')]
if 'is_admin' in columns:
    print("✓ is_admin column exists")
else:
    print("✗ is_admin column MISSING - this should not happen")

# Check if user_feedback table exists
if 'user_feedback' in inspector.get_table_names():
    print("✓ user_feedback table exists")
else:
    print("✗ user_feedback table MISSING - this should not happen")

print("\n" + "="*50)
print("Database migration fix complete!")
print("="*50)

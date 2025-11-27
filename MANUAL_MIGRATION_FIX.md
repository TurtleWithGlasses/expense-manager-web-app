# Manual Fix for Multiple Alembic Migration Heads

## Problem
The database's `alembic_version` table has multiple heads recorded:
- `55cc2f92ab12`
- `fix_production`

This causes the warning: "Version table 'alembic_version' has more than one head present"

## Solution Options

### Option 1: Use the Fix Script (Recommended)
```bash
python fix_migration_heads.py
```

This script will:
1. Check the current state
2. Clear the multiple heads
3. Stamp to the merge migration `a1b2c3d4e5f6`

### Option 2: Manual SQL Fix (SQLite)

**Step 1: Check current state**
```bash
sqlite3 app.db "SELECT * FROM alembic_version;"
```

**Step 2: Clear multiple heads and set to merge migration**
```bash
sqlite3 app.db <<EOF
DELETE FROM alembic_version;
INSERT INTO alembic_version (version_num) VALUES ('a1b2c3d4e5f6');
EOF
```

**Step 3: Verify**
```bash
sqlite3 app.db "SELECT * FROM alembic_version;"
```

Should show: `a1b2c3d4e5f6`

### Option 3: Use Alembic Stamp Command

**Step 1: Clear the version table manually (SQL)**
```bash
sqlite3 app.db "DELETE FROM alembic_version;"
```

**Step 2: Stamp to the merge migration**
```bash
alembic stamp a1b2c3d4e5f6
```

**Step 3: Verify**
```bash
alembic current
```

Should show: `a1b2c3d4e5f6 (head)`

### Option 4: Python Script (Direct)

```python
from sqlalchemy import create_engine, text
from app.core.config import settings
from app.db.engine import engine

# Clear and set to merge migration
with engine.connect() as connection:
    connection.execute(text("DELETE FROM alembic_version"))
    connection.execute(text("INSERT INTO alembic_version (version_num) VALUES ('a1b2c3d4e5f6')"))
    connection.commit()
    print("Fixed! Database now at: a1b2c3d4e5f6")
```

## Important Notes

⚠️ **WARNING**: These methods only fix the version tracking in the `alembic_version` table. They do NOT:
- Apply any missing migrations
- Modify your database schema
- Create or modify tables

**Before using these fixes, ensure:**
1. Your database schema is already up-to-date (all migrations have been applied)
2. You have a backup of your database
3. You understand that you're only fixing the version tracking, not the schema

## After Fixing

1. Restart your server
2. The warning should be gone
3. Future migrations will work normally from the single head

## If Schema is NOT Up-to-Date

If your database schema is missing migrations, you should:

1. **First, apply all missing migrations manually** or let Alembic upgrade
2. **Then** fix the version tracking using one of the methods above

Or use Alembic's upgrade command to let it handle everything:
```bash
alembic upgrade heads
```

This will apply all missing migrations and should resolve to the merge migration automatically.


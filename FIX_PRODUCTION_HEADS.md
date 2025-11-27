# Fix Multiple Heads in Production (Railway)

## Option 1: Use the Fix Script (Recommended)

### Method A: Run Locally with Production Database URL

⚠️ **IMPORTANT**: You need the **PUBLIC** Railway database URL, not the internal one!

The internal URL (`postgres-p241.railway.internal`) only works from within Railway's network.

1. **Get the PUBLIC database URL from Railway:**
   - Go to Railway Dashboard → Your Project → PostgreSQL Service
   - Look for "Public Network" or "Connect" section
   - Copy the **PUBLIC** connection string (usually has `maglev.proxy.rlwy.net` or similar)
   - It should look like: `postgresql://postgres:password@maglev.proxy.rlwy.net:29009/railway`

2. **Set production environment variables:**
   ```bash
   # PowerShell (Windows)
   $env:DATABASE_URL = "postgresql://postgres:password@maglev.proxy.rlwy.net:29009/railway"
   
   # Bash (Linux/Mac)
   export DATABASE_URL="postgresql://postgres:password@maglev.proxy.rlwy.net:29009/railway"
   ```

3. **Run the fix script:**
   ```bash
   python fix_production_heads.py
   ```

3. **Follow the prompts** - it will:
   - Check current state
   - Ask for confirmation
   - Fix the multiple heads
   - Verify the fix

### Method B: Run via Railway CLI

1. **Install Railway CLI** (if not already installed):
   ```bash
   npm i -g @railway/cli
   ```

2. **Login to Railway:**
   ```bash
   railway login
   ```

3. **Link to your project:**
   ```bash
   railway link
   ```

4. **Run the fix script in Railway environment:**
   ```bash
   railway run python fix_production_heads.py
   ```

## Option 2: Manual SQL Fix (Direct Database Access)

If you have direct access to your Railway PostgreSQL database:

### Via Railway Dashboard (PostgreSQL Service)

1. Go to your Railway project
2. Open the PostgreSQL service
3. Click on "Query" or "Connect" to open the database console
4. Run these SQL commands:

```sql
-- Check current state
SELECT * FROM alembic_version;

-- Fix multiple heads
DELETE FROM alembic_version;
INSERT INTO alembic_version (version_num) VALUES ('a1b2c3d4e5f6');

-- Verify fix
SELECT * FROM alembic_version;
```

Expected result after fix:
```
 version_num
-------------
 a1b2c3d4e5f6
(1 row)
```

### Via psql Command Line

If you have `psql` installed and Railway connection details:

```bash
# Connect to Railway database
psql "postgresql://postgres:password@host:port/railway"

# Then run SQL commands:
DELETE FROM alembic_version;
INSERT INTO alembic_version (version_num) VALUES ('a1b2c3d4e5f6');
SELECT * FROM alembic_version;
\q
```

## Option 3: Via Railway One-Click Deploy/Re-deploy

If the automatic migration on startup is working:

1. **Trigger a new deployment** on Railway
2. The updated `app/main.py` should automatically fix the multiple heads
3. Check the deployment logs to confirm

## Verification

After fixing, verify the fix worked:

1. **Check Railway logs** on next deployment - should see:
   ```
   Database already at latest migration (a1b2c3d4e5f6)
   ```
   Instead of:
   ```
   Database has multiple heads recorded
   ```

2. **Or run a status check** (if you have access):
   ```bash
   # With production DATABASE_URL set
   python check_migration_status.py
   ```

## Important Notes

⚠️ **WARNING**: These methods only fix the version tracking in the `alembic_version` table. They do NOT:
- Apply any missing migrations
- Modify your database schema
- Create or modify tables

**Before using these fixes, ensure:**
1. ✅ Your database schema is already up-to-date (all migrations applied)
2. ✅ You have a backup of your production database
3. ✅ You understand you're only fixing version tracking, not the schema

## Troubleshooting

### If the fix doesn't work:

1. **Check if you're connected to the right database:**
   ```bash
   # Verify DATABASE_URL
   echo $DATABASE_URL
   ```

2. **Check Railway logs** for any errors

3. **Verify the alembic_version table exists:**
   ```sql
   SELECT EXISTS (
       SELECT FROM information_schema.tables 
       WHERE table_schema = 'public' 
       AND table_name = 'alembic_version'
   );
   ```

4. **Check current state:**
   ```sql
   SELECT * FROM alembic_version;
   ```

## After Fixing

1. ✅ The warning should be gone on the next deployment
2. ✅ Future migrations will work normally
3. ✅ The database will have a single head: `a1b2c3d4e5f6`


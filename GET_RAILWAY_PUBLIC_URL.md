# How to Get Railway Public Database URL

## The Problem

Railway provides two types of database URLs:
1. **Internal URL** (`.railway.internal`) - Only accessible from within Railway's network
2. **Public URL** (`.proxy.rlwy.net` or similar) - Accessible from anywhere

You need the **PUBLIC** URL to connect from your local machine.

## How to Get the Public URL

### Method 1: Railway Dashboard

1. Go to [Railway Dashboard](https://railway.app)
2. Select your project
3. Click on your **PostgreSQL** service
4. Go to the **"Connect"** or **"Variables"** tab
5. Look for **"Public Network"** or **"Connection String"**
6. Copy the URL that contains `.proxy.rlwy.net` or similar (NOT `.railway.internal`)

### Method 2: Railway CLI

```bash
# Install Railway CLI (if not already installed)
npm i -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Get the public database URL
railway variables
```

Look for `DATABASE_URL` that has a public hostname.

### Method 3: Check Your Railway Logs

When your app starts on Railway, it logs the DATABASE_URL. Check your Railway deployment logs - you should see something like:

```
DATABASE_URL from environment: postgresql://postgres:password@maglev.proxy.rlwy.net:29009/railway
```

This is the public URL you need.

## What the URLs Look Like

**Internal URL (won't work from local machine):**
```
postgresql://postgres:password@postgres-p241.railway.internal:5432/railway
```

**Public URL (works from anywhere):**
```
postgresql://postgres:password@maglev.proxy.rlwy.net:29009/railway
```

## Quick Fix: Use Railway Database Console

If you can't get the public URL, the easiest way is to use Railway's database console:

1. Go to Railway Dashboard → PostgreSQL Service
2. Click **"Query"** or **"Connect"** to open the database console
3. Run this SQL:

```sql
DELETE FROM alembic_version;
INSERT INTO alembic_version (version_num) VALUES ('a1b2c3d4e5f6');
SELECT * FROM alembic_version;
```

This bypasses the need to connect from your local machine!


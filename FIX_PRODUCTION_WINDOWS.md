# Fix Production Database on Windows (PowerShell)

## Setting Environment Variables in PowerShell

In PowerShell, use `$env:` syntax instead of `export`:

### Option 1: Set for Current Session

```powershell
# Set the DATABASE_URL (replace with your actual Railway database URL)
$env:DATABASE_URL = "postgresql://postgres:password@host:port/railway"

# Verify it's set
echo $env:DATABASE_URL

# Run the fix script
python fix_production_heads.py
```

### Option 2: Set Inline (One Command)

```powershell
$env:DATABASE_URL = "postgresql://postgres:password@host:port/railway"; python fix_production_heads.py
```

### Option 3: Use Your Actual Railway URL

Get your Railway database URL from the Railway dashboard, then:

```powershell
# Replace with your actual Railway database URL
$env:DATABASE_URL = "postgresql://postgres:dpuNMqFDOGkUfmihuWHShgtVJHZWdmrT@postgres-p241.railway.internal:5432/railway"

# Run the fix
python fix_production_heads.py
```

## Quick Reference

| Bash/Linux | PowerShell (Windows) |
|------------|----------------------|
| `export VAR="value"` | `$env:VAR = "value"` |
| `echo $VAR` | `echo $env:VAR` |
| `unset VAR` | `Remove-Item env:VAR` |

## Notes

- Environment variables set with `$env:` only last for the current PowerShell session
- To make them permanent, you'd need to set them in System Properties or use `[System.Environment]::SetEnvironmentVariable()`
- For this one-time fix, setting it for the current session is sufficient


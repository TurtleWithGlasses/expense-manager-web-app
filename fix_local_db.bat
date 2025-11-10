@echo off
echo ========================================
echo Fix Local Database Script
echo ========================================
echo.

echo Step 1: Stopping any running Python servers...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo Step 2: Deleting old database...
if exist app.db (
    del /F app.db
    echo ✅ Old database deleted
) else (
    echo ℹ️ No database file found
)

echo Step 3: Database will be recreated on next server start
echo.
echo ========================================
echo Done! You can now start the server with:
echo   python run_local.py
echo ========================================
pause

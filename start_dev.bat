@echo off
echo Starting Expense Manager Web App...
echo.

REM Activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

REM Set environment variables
set DATABASE_URL=sqlite:///./app.db
set ENV=dev

REM Run the application
python run_local.py

"""
Startup script that runs migrations before starting the app
This ensures database schema is up to date before the app starts
"""
import os
import sys
import subprocess

def run_migration():
    """Run the avatar column migration"""
    print("=" * 60)
    print("Running database migrations...")
    print("=" * 60)

    try:
        result = subprocess.run(
            [sys.executable, "update_avatar_column.py"],
            capture_output=True,
            text=True,
            check=False
        )

        print(result.stdout)
        if result.stderr:
            print(result.stderr)

        if result.returncode != 0:
            print("[WARNING] Migration script returned non-zero exit code")
            print("[WARNING] This may be expected if migration already completed")

    except Exception as e:
        print(f"[WARNING] Migration error: {e}")
        print("[WARNING] Continuing with app startup...")

    print("=" * 60)

def start_app():
    """Start the FastAPI application"""
    print("Starting FastAPI application...")
    print("=" * 60)

    port = int(os.environ.get("PORT", 8000))

    # Use uvicorn to start the app
    os.execvp(sys.executable, [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", str(port)
    ])

if __name__ == "__main__":
    run_migration()
    start_app()

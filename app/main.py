import os
from datetime import date
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text, func
from sqlalchemy.orm import Session
from alembic import command
from alembic.config import Config
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.routes import api_router
from app.core.currency import CURRENCIES
from app.core.session import get_session
from app.core.rate_limit import limiter
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.logging_config import setup_logging, get_logger
from app.core.request_logging import RequestLoggingMiddleware
from app.db.engine import engine
from app.db.session import get_db
from app.db.base import Base
from app.templates import render
from app.models.entry import Entry
from app.services.user_preferences import user_preferences_service

# Initialize logging as early as possible
setup_logging()
logger = get_logger(__name__)

# Import all models to ensure they are registered with SQLAlchemy
from app.models.user import User
from app.models.category import Category
from app.models.user_preferences import UserPreferences
from app.models.ai_model import AIModel, AISuggestion, UserAIPreferences
from app.models.weekly_report import WeeklyReport, UserReportPreferences
from app.models.report_status import ReportStatus
from app.models.financial_goal import FinancialGoal, GoalProgressLog
from app.models.recurring_payment import RecurringPayment, PaymentReminder
from app.models.payment_history import PaymentOccurrence, PaymentLinkSuggestion  # Phase 29
from app.models.achievement import Achievement, UserAchievement, Badge, UserBadge  # Phase 1
from app.models.financial_health_score import FinancialHealthScore  # Phase 1.2

app = FastAPI(title="Expense Manager Web")

# Configure CORS for mobile/external API clients
# Import settings to get CORS configuration
from app.core.config import settings as app_settings

# Default allowed origins for development
default_origins = [
    "http://localhost:3000",  # React development
    "http://localhost:8080",  # Vue development
    "http://localhost:4200",  # Angular development
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:4200",
]

# Use environment-configured origins if provided, otherwise use defaults
cors_origins = app_settings.CORS_ALLOWED_ORIGINS
if cors_origins:
    allowed_origins = [origin.strip() for origin in cors_origins.split(",")]
else:
    allowed_origins = default_origins

# Add CORS middleware
# This should be added early in the middleware stack
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,  # Allow cookies for session-based auth
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Authorization",  # For JWT Bearer tokens
        "Content-Type",
        "Accept",
        "Origin",
        "User-Agent",
        "DNT",
        "Cache-Control",
        "X-Requested-With",
    ],
    expose_headers=["Content-Length", "X-Total-Count"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Add request logging middleware (should be after CORS for accurate timing)
app.add_middleware(RequestLoggingMiddleware)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    try:
        from app.core.config import settings

        # Try to apply migrations, but handle gracefully if they fail
        try:
            project_root = os.path.dirname(os.path.dirname(__file__))
            alembic_ini_path = os.path.join(project_root, "alembic.ini")
            alembic_cfg = Config(alembic_ini_path)
            alembic_cfg.set_main_option("script_location", os.path.join(project_root, "alembic"))

            # Check current migration version first
            from alembic.script import ScriptDirectory
            from alembic.runtime.migration import MigrationContext
            from psycopg2.errors import DuplicateColumn
            from sqlalchemy.exc import ProgrammingError

            script = ScriptDirectory.from_config(alembic_cfg)
            with engine.connect() as connection:
                context = MigrationContext.configure(connection)

                # Get current revision
                try:
                    current_rev = context.get_current_revision()
                except Exception as e:
                    logger.warning(f"Could not get current revision: {e}")
                    current_rev = None

                logger.info(f"Current database revision: {current_rev}")

                # Check if database is at a non-existent revision (orphaned migration)
                # This happens when migrations were deleted after being applied
                orphaned_revisions = ['a1b2c3d4e5f6', 'fix_production']
                if current_rev in orphaned_revisions:
                    logger.warning(f"Database is at orphaned revision '{current_rev}' which no longer exists in migration files")
                    logger.info("Fixing: Stamping database to valid merge migration revision '766b569daa8d'")
                    try:
                        # Clear the orphaned revision
                        connection.execute(text("DELETE FROM alembic_version"))
                        connection.commit()
                        logger.info("Cleared orphaned revision from alembic_version")
                        # Stamp to the valid merge migration
                        command.stamp(alembic_cfg, "766b569daa8d")
                        logger.info("Successfully stamped database to 766b569daa8d")
                        current_rev = "766b569daa8d"
                    except Exception as stamp_error:
                        logger.error(f"Failed to stamp database: {stamp_error}", exc_info=True)
                        # Fall through to schema creation

                # Ensure all tables and columns exist using SQLAlchemy models
                logger.info("Ensuring database schema is up to date...")
                try:
                    Base.metadata.create_all(bind=engine)
                    logger.info("Database schema verified/updated successfully")

                    # Verify critical columns exist
                    from sqlalchemy import inspect
                    inspector = inspect(engine)
                    users_columns = [col['name'] for col in inspector.get_columns('users')]
                    logger.info(f"Users table columns: {users_columns}")

                    # Add is_admin column if missing
                    if 'is_admin' not in users_columns:
                        logger.warning("✗ is_admin column MISSING in users table - adding it now")
                        try:
                            with engine.begin() as conn:
                                # Add the column
                                conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE"))
                                logger.info("Added is_admin column to users table")

                                # Set admin user
                                conn.execute(text("UPDATE users SET is_admin = TRUE WHERE email = 'mhmtsoylu1928@gmail.com'"))
                                logger.info("Set mhmtsoylu1928@gmail.com as admin")

                            logger.info("✓ is_admin column added and admin user set successfully")
                        except Exception as alter_error:
                            logger.error(f"Failed to add is_admin column: {alter_error}", exc_info=True)
                    else:
                        logger.info("✓ is_admin column exists in users table")

                    if 'user_feedback' in inspector.get_table_names():
                        logger.info("✓ user_feedback table exists")
                    else:
                        logger.error("✗ user_feedback table MISSING!")
                except Exception as schema_error:
                    logger.error(f"Schema creation failed: {schema_error}", exc_info=True)

        except Exception as migration_error:
            logger.warning(f"Migration check/upgrade failed: {migration_error}")
            logger.info("Attempting to create tables directly...")
            # Fallback to creating tables directly
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created/verified")

        # Start report scheduler
        # Start scheduler in production, or if explicitly enabled in development
        enable_scheduler = settings.ENV == "production" or getattr(settings, 'ENABLE_SCHEDULER', False)
        if enable_scheduler:
            from app.services.report_scheduler import report_scheduler
            report_scheduler.start()
            logger.info(f"Report scheduler started (ENV: {settings.ENV})")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        # Don't raise the exception to allow the app to start
        # The health check endpoint will catch database issues


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    from app.core.config import settings
    enable_scheduler = settings.ENV == "production" or getattr(settings, 'ENABLE_SCHEDULER', False)
    if enable_scheduler:
        try:
            from app.services.report_scheduler import report_scheduler
            report_scheduler.stop()
            logger.info("Report scheduler stopped")
        except Exception as e:
            logger.warning(f"Error stopping scheduler: {e}")

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(api_router)

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    # Check if user is authenticated
    sess = get_session(request)
    if not sess:
        return RedirectResponse(url="/login")
    
    # Get user from database
    user = db.query(User).filter(User.id == sess["id"]).first()
    if not user:
        return RedirectResponse(url="/login")

    # Refresh user to ensure latest data (including avatar)
    db.refresh(user)

    today = date.today()
    start = today.replace(day=1)
    end = today

    # calculate totals for user
    income_total = db.query(func.sum(Entry.amount))\
        .filter(Entry.user_id == user.id, Entry.type == "income").scalar() or 0
    expense_total = db.query(func.sum(Entry.amount))\
        .filter(Entry.user_id == user.id, Entry.type == "expense").scalar() or 0
    
    user_currency_code = user_preferences_service.get_user_currency(db, user.id)
    user_currency_info = CURRENCIES.get(user_currency_code, CURRENCIES['USD'])

    # Get user theme preference
    user_prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()
    user_theme = user_prefs.theme if user_prefs and user_prefs.theme else 'dark'

    # Get categories for filtering
    categories = db.query(Category).filter(Category.user_id == user.id).order_by(Category.name).all()

    return render(request, "dashboard.html", {
        "user": user,
        "user_theme": user_theme,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "income_total": income_total,
        "expense_total": expense_total,
        "user_currency": user_currency_info,
        "user_currency_code": user_currency_code,
        "categories": categories,
    })

@app.get("/healthz")
async def healthz():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        return {"ok": True}
    
    
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
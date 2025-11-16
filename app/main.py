import os
from datetime import date
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
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

app = FastAPI(title="Expense Manager Web")

# Add request logging middleware (should be first for accurate timing)
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
                current_rev = context.get_current_revision()
                head_rev = script.get_current_head()

                if current_rev == head_rev:
                    logger.info(f"Database already at latest migration ({current_rev})")
                else:
                    logger.info(f"Database migration needed - Current: {current_rev}, Target: {head_rev}")

                    # Try to upgrade
                    try:
                        command.upgrade(alembic_cfg, "head")
                        logger.info("Database migrations applied successfully")
                    except ProgrammingError as pe:
                        # Check if it's a DuplicateColumn error
                        if isinstance(pe.orig, DuplicateColumn):
                            logger.warning("Migration failed: Columns already exist (DuplicateColumn)")
                            logger.info("Schema is already up-to-date but migration version is old")
                            logger.info(f"Stamping database to latest version: {head_rev}")

                            # Stamp the database to the head revision without running migrations
                            command.stamp(alembic_cfg, "head")
                            logger.info(f"Database stamped to {head_rev}")
                        else:
                            # Re-raise if it's a different error
                            raise

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
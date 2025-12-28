from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# --- App imports
from app.core.config import settings
from app.db.base import Base
# Import models so Alembic "sees" them
from app.models.user import User
from app.models.category import Category
from app.models.entry import Entry
from app.models.user_preferences import UserPreferences
from app.models.financial_goal import FinancialGoal
from app.models.recurring_payment import RecurringPayment, PaymentReminder
from app.models.payment_history import PaymentOccurrence, PaymentLinkSuggestion
from app.models.forecast import Forecast
from app.models.scenario import Scenario
from app.models.achievement import Achievement, UserAchievement, Badge, UserBadge
from app.models.challenge import Challenge, UserChallenge
from app.models.weekly_report import WeeklyReport, UserReportPreferences
from app.models.ai_model import AIModel, AISuggestion, UserAIPreferences
from app.models.historical_report import HistoricalReport
from app.models.user_feedback import UserFeedback
from app.models.report_status import ReportStatus


# this is the Alembic Config object, which provides access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for 'autogenerate'
target_metadata = Base.metadata

def get_url():
    # Always take URL from app settings (.env)
    return settings.DATABASE_URL

def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        {"sqlalchemy.url": get_url()},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

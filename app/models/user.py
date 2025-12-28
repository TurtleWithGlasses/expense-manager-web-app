from datetime import datetime, UTC
from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None]
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Email verification fields
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verification_token_expires: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Admin privileges - Phase 33
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    # Password reset fields
    password_reset_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_reset_expires: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))

    categories = relationship("Category", back_populates="owner", cascade="all, delete-orphan", passive_deletes=True)
    entries = relationship("Entry", back_populates="owner", cascade="all, delete-orphan", passive_deletes=True)
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan", passive_deletes=True)

    # AI relationships
    ai_models = relationship("AIModel", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    ai_suggestions = relationship("AISuggestion", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    ai_preferences = relationship("UserAIPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan", passive_deletes=True)
    forecasts = relationship("Forecast", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    scenarios = relationship("Scenario", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    scenario_comparisons = relationship("ScenarioComparison", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)

    # Report relationships
    weekly_reports = relationship("WeeklyReport", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    report_preferences = relationship("UserReportPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan", passive_deletes=True)
    report_statuses = relationship("ReportStatus", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)

    # Goal relationships - Phase 17
    financial_goals = relationship("FinancialGoal", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)

    # Recurring payment relationships - Phase 28
    recurring_payments = relationship("RecurringPayment", back_populates="owner", cascade="all, delete-orphan", passive_deletes=True)
    payment_reminders = relationship("PaymentReminder", back_populates="owner", cascade="all, delete-orphan", passive_deletes=True)

    # Payment history relationships - Phase 29
    payment_occurrences = relationship("PaymentOccurrence", back_populates="owner", cascade="all, delete-orphan", passive_deletes=True)
    payment_link_suggestions = relationship("PaymentLinkSuggestion", back_populates="owner", cascade="all, delete-orphan", passive_deletes=True)

    # Historical reports relationship
    historical_reports = relationship("HistoricalReport", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)

    # Gamification relationships - Phase 1
    achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    badges = relationship("UserBadge", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
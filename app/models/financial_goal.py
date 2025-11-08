"""Financial Goal Model - Phase 17"""
from datetime import datetime
from sqlalchemy import String, DateTime, Numeric, Enum as SQLEnum, Integer, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
import enum

from app.db.base import Base


class GoalType(str, enum.Enum):
    """Types of financial goals"""
    SAVINGS = "savings"  # Save a specific amount
    SPENDING_LIMIT = "spending_limit"  # Limit spending in a category
    DEBT_PAYOFF = "debt_payoff"  # Pay off a debt
    EMERGENCY_FUND = "emergency_fund"  # Build emergency fund
    CUSTOM = "custom"  # Custom goal


class GoalStatus(str, enum.Enum):
    """Goal completion status"""
    ACTIVE = "active"  # Currently working on
    COMPLETED = "completed"  # Goal achieved
    CANCELLED = "cancelled"  # User cancelled
    FAILED = "failed"  # Deadline passed without completion


class FinancialGoal(Base):
    """Financial goals for users to track their financial objectives"""
    __tablename__ = "financial_goals"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    # Goal details
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    goal_type: Mapped[str] = mapped_column(SQLEnum(GoalType), default=GoalType.SAVINGS)

    # Financial targets
    target_amount: Mapped[float] = mapped_column(Numeric(precision=12, scale=2))
    current_amount: Mapped[float] = mapped_column(Numeric(precision=12, scale=2), default=0)
    currency_code: Mapped[str] = mapped_column(String(3), default="USD")

    # Category association (for spending limit goals)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)

    # Timeline
    start_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    target_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Status and progress
    status: Mapped[str] = mapped_column(SQLEnum(GoalStatus), default=GoalStatus.ACTIVE)
    progress_percentage: Mapped[float] = mapped_column(Numeric(precision=5, scale=2), default=0)

    # Notifications
    notify_on_milestone: Mapped[bool] = mapped_column(Boolean, default=True)
    milestone_percentage: Mapped[int] = mapped_column(Integer, default=25)  # Notify every 25%

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="financial_goals")
    category = relationship("Category")
    progress_logs = relationship("GoalProgressLog", back_populates="goal", cascade="all, delete-orphan")


class GoalProgressLog(Base):
    """Track progress updates for financial goals"""
    __tablename__ = "goal_progress_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("financial_goals.id", ondelete="CASCADE"), index=True)

    # Progress details
    previous_amount: Mapped[float] = mapped_column(Numeric(precision=12, scale=2))
    new_amount: Mapped[float] = mapped_column(Numeric(precision=12, scale=2))
    change_amount: Mapped[float] = mapped_column(Numeric(precision=12, scale=2))

    # Context
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False)  # Manual vs automatic update

    # Timestamp
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    goal = relationship("FinancialGoal", back_populates="progress_logs")

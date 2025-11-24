"""
Recurring Payment model for user-managed bills & subscriptions
"""

from datetime import datetime, date
from sqlalchemy import String, ForeignKey, Numeric, Date, Boolean, Integer, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
import enum


class RecurrenceFrequency(enum.Enum):
    """Frequency of recurring payments"""
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


class RecurringPayment(Base):
    """
    User-managed recurring bills and subscriptions

    Users manually configure their bills/subscriptions by:
    - Selecting a category (NOT auto-detected by AI)
    - Setting a due date
    - Specifying amount and frequency

    AI only provides warnings about upcoming payments based on user-defined data.
    """
    __tablename__ = "recurring_payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), index=True)

    # Payment details
    name: Mapped[str] = mapped_column(String(255))  # e.g., "Netflix Subscription", "Electric Bill"
    description: Mapped[str | None] = mapped_column(String, nullable=True)  # Optional notes
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    currency_code: Mapped[str] = mapped_column(String(3), default='USD')

    # Recurrence settings
    frequency: Mapped[RecurrenceFrequency] = mapped_column(SQLEnum(RecurrenceFrequency))
    due_day: Mapped[int] = mapped_column(Integer)  # Day of month (1-31) for monthly/quarterly/annually, or day of week (0-6) for weekly
    start_date: Mapped[date] = mapped_column(Date)  # When this payment started
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)  # Optional end date

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # User can pause/resume

    # Reminder settings
    remind_days_before: Mapped[int] = mapped_column(Integer, default=3)  # Days before due date to send reminder

    # Metadata
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="recurring_payments")
    category = relationship("Category", back_populates="recurring_payments")


class PaymentReminder(Base):
    """
    AI-generated reminders for upcoming recurring payments

    These are automatically created by the system based on user-defined
    recurring payments. AI warns users about upcoming bills.
    """
    __tablename__ = "payment_reminders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    recurring_payment_id: Mapped[int] = mapped_column(ForeignKey("recurring_payments.id", ondelete="CASCADE"), index=True)

    # Reminder details
    reminder_date: Mapped[date] = mapped_column(Date, index=True)  # When to show this reminder
    due_date: Mapped[date] = mapped_column(Date)  # Actual due date of payment
    amount: Mapped[float] = mapped_column(Numeric(12, 2))

    # Status
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)  # User can mark as paid
    paid_entry_id: Mapped[int | None] = mapped_column(ForeignKey("entries.id", ondelete="SET NULL"), nullable=True)  # Link to actual payment entry

    # Metadata
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="payment_reminders")
    recurring_payment = relationship("RecurringPayment")
    paid_entry = relationship("Entry", foreign_keys=[paid_entry_id])

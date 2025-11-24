"""
Payment History Models (Phase 29)

Tracks actual payment occurrences for recurring payments.
Supports auto-linking with expense entries and payment history visualization.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from sqlalchemy import ForeignKey, String, Numeric, Date, DateTime, Boolean, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PaymentOccurrence(Base):
    """
    Records each actual payment of a recurring bill/subscription.

    This allows users to:
    - Track when they actually paid their bills
    - View payment history over time
    - Identify missed or late payments
    - Link payments to actual expense entries
    """
    __tablename__ = "payment_occurrences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    recurring_payment_id: Mapped[int] = mapped_column(
        ForeignKey("recurring_payments.id", ondelete="CASCADE"),
        index=True
    )

    # Payment details
    scheduled_date: Mapped[date] = mapped_column(Date, index=True)  # When it was supposed to be paid
    actual_date: Mapped[date | None] = mapped_column(Date, nullable=True)  # When it was actually paid
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency_code: Mapped[str] = mapped_column(String(3))

    # Payment status
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    is_skipped: Mapped[bool] = mapped_column(Boolean, default=False)  # User intentionally skipped this payment
    is_late: Mapped[bool] = mapped_column(Boolean, default=False)

    # Linking to actual expense entry
    linked_entry_id: Mapped[int | None] = mapped_column(
        ForeignKey("entries.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Notes and metadata
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    confirmation_number: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="payment_occurrences")
    recurring_payment = relationship("RecurringPayment", back_populates="occurrences")
    linked_entry = relationship("Entry", foreign_keys=[linked_entry_id])


class PaymentLinkSuggestion(Base):
    """
    AI-generated suggestions for linking expense entries to recurring payments.

    The system analyzes expense entries and suggests which ones might be
    payments for recurring bills/subscriptions.
    """
    __tablename__ = "payment_link_suggestions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    recurring_payment_id: Mapped[int] = mapped_column(
        ForeignKey("recurring_payments.id", ondelete="CASCADE"),
        index=True
    )
    entry_id: Mapped[int] = mapped_column(
        ForeignKey("entries.id", ondelete="CASCADE"),
        index=True
    )

    # Suggestion metadata
    confidence_score: Mapped[float] = mapped_column(Numeric(5, 4))  # 0.0000 to 1.0000
    match_reason: Mapped[str] = mapped_column(Text)  # JSON string explaining why it matched

    # Suggestion status
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_accepted: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="payment_link_suggestions")
    recurring_payment = relationship("RecurringPayment")
    entry = relationship("Entry")

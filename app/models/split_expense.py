"""Split Expense Models - Phase 31: Social & Collaboration"""
from datetime import datetime, date, UTC
from decimal import Decimal
from sqlalchemy import String, DateTime, Numeric, Boolean, Text, Date, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.base import Base


class SplitStatus(str, enum.Enum):
    OPEN = "open"        # Some participants haven't settled
    SETTLED = "settled"  # All participants have settled


class SplitContact(Base):
    """A person you split expenses with — doesn't need a BudgetPulse account."""
    __tablename__ = "split_contacts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(150))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None)
    )

    owner = relationship("User", back_populates="split_contacts")
    participations = relationship(
        "SplitParticipant", back_populates="contact", cascade="all, delete-orphan"
    )


class SplitExpense(Base):
    """A shared expense split between the owner and one or more contacts."""
    __tablename__ = "split_expenses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    # Optional link to an existing expense entry
    entry_id: Mapped[int | None] = mapped_column(
        ForeignKey("entries.id", ondelete="SET NULL"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(200))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency_code: Mapped[str] = mapped_column(String(3), default="USD")
    date: Mapped[date] = mapped_column(Date, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=SplitStatus.OPEN)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None)
    )

    owner = relationship("User", back_populates="split_expenses")
    entry = relationship("Entry", foreign_keys=[entry_id])
    participants = relationship(
        "SplitParticipant", back_populates="split_expense", cascade="all, delete-orphan"
    )


class SplitParticipant(Base):
    """One person's share in a split expense."""
    __tablename__ = "split_participants"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    split_expense_id: Mapped[int] = mapped_column(
        ForeignKey("split_expenses.id", ondelete="CASCADE"), index=True
    )
    contact_id: Mapped[int | None] = mapped_column(
        ForeignKey("split_contacts.id", ondelete="SET NULL"), nullable=True
    )
    # Snapshot of name so history is preserved even if contact is renamed/deleted
    name: Mapped[str] = mapped_column(String(150))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    # True = this person actually paid the bill; False = they owe their share
    is_payer: Mapped[bool] = mapped_column(Boolean, default=False)
    is_settled: Mapped[bool] = mapped_column(Boolean, default=False)
    settled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    split_expense = relationship("SplitExpense", back_populates="participants")
    contact = relationship("SplitContact", back_populates="participations")

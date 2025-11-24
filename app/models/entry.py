from datetime import date
from sqlalchemy import String, ForeignKey, Numeric, Date, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class EntryType:
    INCOME = "income"
    EXPENSE = "expense"


class Entry(Base):
    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)  # Index for user filtering
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), index=True)  # Index for category filtering

    type: Mapped[str] = mapped_column(String(16), index=True)  # Index for income/expense filtering
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    note: Mapped[str | None] = mapped_column(String(255))
    date: Mapped[date] = mapped_column(Date, index=True)  # Index for date sorting and range queries
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    currency_code: Mapped[str] = mapped_column(String(3), default='USD')
    
    # AI-related fields (temporarily kept for database compatibility)
    ai_suggested_category_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    ai_confidence_score: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)  # 0.00 to 1.00
    merchant_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location_data: Mapped[str | None] = mapped_column(String, nullable=True)  # JSON stored as string
    ai_processed: Mapped[bool] = mapped_column(Boolean, default=False)

    owner = relationship("User", back_populates="entries")
    category = relationship("Category", back_populates="entries", foreign_keys=[category_id])

    # AI relationships
    ai_suggestions = relationship("AISuggestion", back_populates="entry", cascade="all, delete-orphan")
    ai_suggested_category = relationship("Category", foreign_keys=[ai_suggested_category_id])
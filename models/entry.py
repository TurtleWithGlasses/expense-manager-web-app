from datetime import date
from sqlalchemy import String, ForeignKey, Numeric, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class EntryType:
    INCOME = "income"
    EXPENSE = "expense"


class Entry(Base):
    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"))

    type: Mapped[str] = mapped_column(String(16)) # "income" | "expense"
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    note: Mapped[str | None] = mapped_column(String(255))
    date: Mapped[date] = mapped_column(Date)

    owner = relationship("User", back_populates="entries")
    category = relationship("Category", back_populates="entries")
"""MerchantCategoryMapping – Phase E: merchant learning from receipt corrections."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MerchantCategoryMapping(Base):
    """
    Remembers which category a user assigned to a given merchant name.
    Built up automatically each time a receipt scan entry is saved.
    Used to pre-suggest the same category on future scans of the same merchant.
    """
    __tablename__ = "merchant_category_mappings"
    __table_args__ = (
        UniqueConstraint("user_id", "merchant_key", name="uq_user_merchant_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # Normalised merchant name used for matching (lowercase, stripped)
    merchant_key: Mapped[str] = mapped_column(String(255))
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    use_count: Mapped[int] = mapped_column(Integer, default=1)
    last_used: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user     = relationship("User", back_populates="merchant_mappings")
    category = relationship("Category")

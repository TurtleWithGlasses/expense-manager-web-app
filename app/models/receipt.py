"""Receipt model – Phase A: Receipt Persistence"""
from __future__ import annotations

import json
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    entry_id: Mapped[int | None] = mapped_column(
        ForeignKey("entries.id", ondelete="SET NULL"), nullable=True, index=True
    )

    image_data: Mapped[str | None] = mapped_column(Text, nullable=True)      # base64-encoded image
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string
    confidence: Mapped[str | None] = mapped_column(String(16), nullable=True)  # high/medium/low
    merchant: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    receipt_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="receipts")
    entry = relationship("Entry", back_populates="receipt", foreign_keys=[entry_id])

    @property
    def extracted(self) -> dict:
        try:
            return json.loads(self.extracted_data) if self.extracted_data else {}
        except Exception:
            return {}

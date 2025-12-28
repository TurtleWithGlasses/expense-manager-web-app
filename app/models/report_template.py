"""Report Template Model - Phase 2.1: Advanced Custom Reports"""
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, Text, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from app.db.base import Base


class ReportTemplate(Base):
    """Saved custom report templates for reuse"""
    __tablename__ = "report_templates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    # Template metadata
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)

    # Report configuration
    report_type: Mapped[str] = mapped_column(String(50))  # 'expense', 'income', 'comprehensive'

    # Date range configuration
    date_range_type: Mapped[str] = mapped_column(String(50), default='custom')  # 'custom', 'last_7_days', 'this_month', etc.
    custom_days: Mapped[int | None] = mapped_column(Integer, nullable=True)  # For relative ranges like 'last_30_days'

    # Filters (stored as JSON for flexibility)
    # Example: {"categories": [1, 2, 3], "min_amount": 10.0, "max_amount": 500.0}
    filters: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Export format preference
    default_export_format: Mapped[str] = mapped_column(String(20), default='excel')  # 'excel', 'pdf'

    # Usage tracking
    use_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="report_templates")

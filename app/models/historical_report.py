"""
Historical Report Model

Stores generated reports for historical access.
Allows users to view past weekly, monthly, and annual reports.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from app.db.base import Base


class HistoricalReport(Base):
    """
    Stores generated financial reports for historical viewing

    Each report is saved when generated, allowing users to:
    - View past weekly/monthly/annual reports
    - Track changes over time
    - Access historical financial data
    """
    __tablename__ = "historical_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Report identification
    report_type = Column(String(20), nullable=False, index=True)  # 'weekly', 'monthly', 'annual'
    report_period = Column(String(50), nullable=False, index=True)  # '2024-W45', '2024-10', '2024', etc.

    # Report period dates
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # Report data stored as JSON
    report_data = Column(Text, nullable=False)  # Complete report data as JSON string

    # Summary metrics for quick access
    total_income = Column(Integer, default=0)  # In cents to avoid floating point issues
    total_expenses = Column(Integer, default=0)  # In cents
    net_savings = Column(Integer, default=0)  # In cents
    transaction_count = Column(Integer, default=0)

    # Metadata
    currency_code = Column(String(3), default='USD')
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="historical_reports")

    def __repr__(self):
        return f"<HistoricalReport(user_id={self.user_id}, type={self.report_type}, period={self.report_period})>"

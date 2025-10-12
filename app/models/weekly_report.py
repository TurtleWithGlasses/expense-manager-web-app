"""Weekly Report Models"""

from datetime import datetime, date
from sqlalchemy import String, ForeignKey, Integer, Boolean, DateTime, Date, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
import enum


class ReportFrequency(str, enum.Enum):
    """Report frequency options"""
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    DISABLED = "disabled"


class WeeklyReport(Base):
    """Stored weekly financial reports"""
    __tablename__ = "weekly_reports"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    
    # Report period
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    week_end: Mapped[date] = mapped_column(Date, nullable=False)
    week_number: Mapped[int] = mapped_column(Integer)
    year: Mapped[int] = mapped_column(Integer)
    
    # Report data (stored as JSON)
    report_data: Mapped[str] = mapped_column(Text)  # JSON string
    
    # Summary metrics
    total_expenses: Mapped[float] = mapped_column(nullable=False)
    total_income: Mapped[float] = mapped_column(nullable=False)
    net_savings: Mapped[float] = mapped_column(nullable=False)
    transaction_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status
    is_viewed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_sent_via_email: Mapped[bool] = mapped_column(Boolean, default=False)
    email_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="weekly_reports")


class UserReportPreferences(Base):
    """User preferences for automated reports"""
    __tablename__ = "user_report_preferences"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    
    # Report settings
    frequency: Mapped[str] = mapped_column(String(20), default="weekly")  # weekly, biweekly, monthly, disabled
    send_email: Mapped[bool] = mapped_column(Boolean, default=True)
    show_on_dashboard: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Email delivery settings
    email_day_of_week: Mapped[int] = mapped_column(Integer, default=0)  # 0=Monday, 6=Sunday
    email_hour: Mapped[int] = mapped_column(Integer, default=9)  # 9 AM
    
    # Content preferences
    include_achievements: Mapped[bool] = mapped_column(Boolean, default=True)
    include_recommendations: Mapped[bool] = mapped_column(Boolean, default=True)
    include_anomalies: Mapped[bool] = mapped_column(Boolean, default=True)
    include_category_breakdown: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Notification preferences
    notify_on_high_spending: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_on_anomalies: Mapped[bool] = mapped_column(Boolean, default=True)
    high_spending_threshold: Mapped[float] = mapped_column(default=500.0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="report_preferences")


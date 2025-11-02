from datetime import datetime
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None]
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Email verification fields
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verification_token_expires: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Password reset fields
    password_reset_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_reset_expires: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    categories = relationship("Category", back_populates="owner", cascade="all, delete-orphan")
    entries = relationship("Entry", back_populates="owner", cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False)
    
    # AI relationships
    ai_models = relationship("AIModel", back_populates="user", cascade="all, delete-orphan")
    ai_suggestions = relationship("AISuggestion", back_populates="user", cascade="all, delete-orphan")
    ai_preferences = relationship("UserAIPreferences", back_populates="user", uselist=False)
    
    # Report relationships
    weekly_reports = relationship("WeeklyReport", back_populates="user", cascade="all, delete-orphan")
    report_preferences = relationship("UserReportPreferences", back_populates="user", uselist=False)
    report_statuses = relationship("ReportStatus", back_populates="user", cascade="all, delete-orphan")
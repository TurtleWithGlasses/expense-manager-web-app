from datetime import datetime
from sqlalchemy import String, ForeignKey, Integer, Boolean, DateTime, Numeric, Text, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class AIModel(Base):
    """AI model configuration and training metadata"""
    __tablename__ = "ai_models"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    model_name: Mapped[str] = mapped_column(String(100))  # e.g., "categorization_v1"
    model_type: Mapped[str] = mapped_column(String(50))  # e.g., "classification", "regression"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    accuracy_score: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)  # 0.0000 to 1.0000
    training_data_count: Mapped[int] = mapped_column(Integer, default=0)
    last_trained: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    model_parameters: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON stored as string
    model_blob: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)  # Serialized ML model (joblib)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="ai_models")


class AISuggestion(Base):
    """AI-generated suggestions for entries"""
    __tablename__ = "ai_suggestions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    entry_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("entries.id", ondelete="CASCADE"), nullable=True)
    suggested_category_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    suggestion_type: Mapped[str] = mapped_column(String(50))  # e.g., "category", "amount", "pattern"
    confidence_score: Mapped[float] = mapped_column(Numeric(3, 2))  # 0.00 to 1.00
    suggestion_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON stored as string
    is_accepted: Mapped[bool | None] = mapped_column(Boolean, nullable=True)  # True/False/None (pending)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    feedback_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user = relationship("User", back_populates="ai_suggestions")
    entry = relationship("Entry", back_populates="ai_suggestions")
    suggested_category = relationship("Category", foreign_keys=[suggested_category_id])


class UserAIPreferences(Base):
    """User preferences for AI features"""
    __tablename__ = "user_ai_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    
    # Feature toggles
    auto_categorization_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    smart_suggestions_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    spending_insights_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    budget_predictions_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Confidence thresholds
    min_confidence_threshold: Mapped[float] = mapped_column(Numeric(3, 2), default=0.7)  # 0.00 to 1.00
    auto_accept_threshold: Mapped[float] = mapped_column(Numeric(3, 2), default=0.9)  # 0.00 to 1.00
    
    # Learning preferences
    learn_from_feedback: Mapped[bool] = mapped_column(Boolean, default=True)
    retrain_frequency_days: Mapped[int] = mapped_column(Integer, default=7)
    
    # Privacy settings
    share_anonymized_data: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="ai_preferences")

"""
Forecast Model for storing Prophet forecasting results
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base


class Forecast(Base):
    """
    Store Prophet forecast results for caching and historical tracking

    This avoids recomputing forecasts and allows tracking prediction accuracy
    """
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Forecast metadata
    forecast_type = Column(String(50), nullable=False)  # 'total_spending', 'category', 'seasonal'
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)

    # Forecast parameters
    forecast_horizon_days = Column(Integer, nullable=False)  # How many days ahead
    training_data_start = Column(DateTime, nullable=False)
    training_data_end = Column(DateTime, nullable=False)
    training_data_points = Column(Integer, nullable=False)

    # Forecast results (stored as JSON)
    forecast_data = Column(JSON, nullable=False)  # Array of {date, predicted, lower, upper, trend}
    summary = Column(JSON, nullable=True)  # Summary statistics
    insights = Column(JSON, nullable=True)  # Generated insights

    # Model information
    model_type = Column(String(50), default="prophet")
    model_params = Column(JSON, nullable=True)  # Model configuration
    confidence_level = Column(Float, default=0.95)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True)  # When to recompute
    is_active = Column(Boolean, default=True)

    # Performance tracking
    actual_vs_predicted = Column(JSON, nullable=True)  # For accuracy assessment
    accuracy_score = Column(Float, nullable=True)  # MAPE or similar

    # Relationships
    user = relationship("User", back_populates="forecasts")
    category = relationship("Category", foreign_keys=[category_id])

    def __repr__(self):
        return f"<Forecast(id={self.id}, type={self.forecast_type}, user_id={self.user_id})>"

    def to_dict(self):
        """Convert forecast to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'forecast_type': self.forecast_type,
            'category_id': self.category_id,
            'forecast_horizon_days': self.forecast_horizon_days,
            'forecast_data': self.forecast_data,
            'summary': self.summary,
            'insights': self.insights,
            'model_type': self.model_type,
            'confidence_level': self.confidence_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'accuracy_score': self.accuracy_score
        }

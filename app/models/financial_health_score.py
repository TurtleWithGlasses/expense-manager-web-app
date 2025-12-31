"""
Financial Health Score Model - Phase 1.2

Stores historical financial health scores for users.
Enables tracking score trends over time.
"""

from sqlalchemy import Integer, Date, DateTime, ForeignKey, UniqueConstraint, Index, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from datetime import datetime, date
from typing import Optional, Dict, Any

from app.db.base import Base


class FinancialHealthScore(Base):
    """
    Financial Health Score

    Stores calculated financial health scores with component breakdowns
    """
    __tablename__ = "financial_health_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    score_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Component scores (0-100 each)
    savings_rate_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expense_consistency_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    budget_adherence_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    debt_management_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    goal_progress_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    emergency_fund_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Supporting data (raw calculation details)
    # Example: {
    #   'income': 5000,
    #   'expenses': 3500,
    #   'savings_rate': 30,
    #   'goal_count': 3,
    #   'completed_goals': 1
    # }
    calculation_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"),
        nullable=True
    )

    # Recommendations for improvement
    # Example: [
    #   'Increase savings rate by 5% to reach Excellent grade',
    #   'Reduce spending variance in Transportation category'
    # ]
    recommendations: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="health_scores")

    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'score_date', name='uq_user_score_date'),
        Index('idx_health_scores_user_date', 'user_id', 'score_date'),
        CheckConstraint('score >= 0 AND score <= 100', name='check_score_range'),
    )

    def __repr__(self):
        return f"<FinancialHealthScore user_id={self.user_id} score={self.score} date={self.score_date}>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'score': self.score,
            'score_date': self.score_date.isoformat() if self.score_date else None,
            'grade': self.get_grade(),
            'components': {
                'savings_rate': self.savings_rate_score,
                'expense_consistency': self.expense_consistency_score,
                'budget_adherence': self.budget_adherence_score,
                'debt_management': self.debt_management_score,
                'goal_progress': self.goal_progress_score,
                'emergency_fund': self.emergency_fund_score
            },
            'calculation_data': self.calculation_data,
            'recommendations': self.recommendations,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def get_grade(self) -> str:
        """Get letter grade based on score"""
        if self.score >= 90:
            return 'Excellent'
        elif self.score >= 70:
            return 'Good'
        elif self.score >= 50:
            return 'Fair'
        else:
            return 'Poor'

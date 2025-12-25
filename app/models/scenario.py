"""
Scenario Models for What-If Analysis and Financial Planning

Enables users to test different financial scenarios:
- Spending reductions
- Income increases
- Goal-based planning
- Budget adjustments
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class Scenario(Base):
    """
    Financial scenario for what-if analysis

    Examples:
    - "What if I reduce dining out by 30%?"
    - "What if I get a $500/month raise?"
    - "What if I save $200/month for 12 months?"
    """
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Scenario metadata
    name = Column(String(200), nullable=False)  # e.g., "Reduce dining by 30%"
    description = Column(Text, nullable=True)
    scenario_type = Column(String(50), nullable=False)  # 'spending_reduction', 'income_increase', 'goal_based', 'category_adjustment'

    # Scenario parameters (flexible JSON structure)
    parameters = Column(JSON, nullable=False)
    """
    Example parameters:
    {
        "type": "spending_reduction",
        "category_id": 5,
        "reduction_percent": 30,
        "duration_months": 6
    }
    or
    {
        "type": "income_increase",
        "amount": 500,
        "frequency": "monthly",
        "start_date": "2025-02-01"
    }
    or
    {
        "type": "goal_based",
        "target_amount": 5000,
        "timeframe_months": 12,
        "category_adjustments": [
            {"category_id": 3, "reduction_percent": 20},
            {"category_id": 5, "reduction_percent": 40}
        ]
    }
    """

    # Projected outcome (calculated by ScenarioService)
    projected_outcome = Column(JSON, nullable=True)
    """
    {
        "monthly_savings": 150,
        "total_savings": 900,
        "end_balance": 5000,
        "goal_achievable": true,
        "timeline": [
            {"month": "2025-02", "balance": 150, "income": 3000, "expenses": 2850},
            ...
        ]
    }
    """

    # Comparison baseline (current state for comparison)
    baseline_data = Column(JSON, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_favorite = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="scenarios")

    def __repr__(self):
        return f"<Scenario(id={self.id}, name='{self.name}', type={self.scenario_type})>"

    def to_dict(self):
        """Convert scenario to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'scenario_type': self.scenario_type,
            'parameters': self.parameters,
            'projected_outcome': self.projected_outcome,
            'baseline_data': self.baseline_data,
            'is_active': self.is_active,
            'is_favorite': self.is_favorite,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ScenarioComparison(Base):
    """
    Stores comparison of multiple scenarios

    Allows users to save comparisons for later review
    """
    __tablename__ = "scenario_comparisons"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Array of scenario IDs being compared
    scenario_ids = Column(JSON, nullable=False)  # [1, 2, 3]

    # Comparison results
    comparison_data = Column(JSON, nullable=False)
    """
    {
        "scenarios": [
            {"id": 1, "name": "Reduce dining", "monthly_savings": 150, "total_savings": 900},
            {"id": 2, "name": "Increase income", "monthly_savings": 500, "total_savings": 3000}
        ],
        "winner": {
            "scenario_id": 2,
            "reason": "Highest total savings"
        },
        "insights": [
            "Scenario 2 achieves goal 5 months faster",
            "Scenario 1 requires less lifestyle change"
        ]
    }
    """

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="scenario_comparisons")

    def __repr__(self):
        return f"<ScenarioComparison(id={self.id}, name='{self.name}')>"

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'scenario_ids': self.scenario_ids,
            'comparison_data': self.comparison_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

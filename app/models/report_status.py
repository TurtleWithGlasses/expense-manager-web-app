from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class ReportStatus(Base):
    """Track the view status of reports for users"""
    __tablename__ = "report_status"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    report_type = Column(String(20), nullable=False)  # 'weekly', 'monthly', 'annual'
    report_period = Column(String(50), nullable=False)  # 'current', '2024-10', etc.
    is_new = Column(Boolean, default=True, nullable=False)
    last_viewed = Column(DateTime(timezone=True), nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship
    user = relationship("User", back_populates="report_statuses")
    
    def __repr__(self):
        return f"<ReportStatus(user_id={self.user_id}, report_type={self.report_type}, is_new={self.is_new})>"

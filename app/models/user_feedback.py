"""
User Feedback Model

Stores user feedback, feature requests, and bug reports.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base


class UserFeedback(Base):
    """
    Stores user feedback and feature requests

    Allows users to:
    - Submit feature requests
    - Report bugs
    - Provide general feedback
    - Rate the application
    """
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Feedback details
    feedback_type = Column(String(20), nullable=False, index=True)  # 'bug', 'feature', 'feedback'
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)

    # Optional rating (1-5 stars)
    rating = Column(Integer, nullable=True)

    # Admin response
    admin_response = Column(Text, nullable=True)
    is_resolved = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="feedback")

    def __repr__(self):
        return f"<UserFeedback(user_id={self.user_id}, type={self.feedback_type}, subject='{self.subject}')>"

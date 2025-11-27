"""
User Feedback Service

Manages user feedback, feature requests, and bug reports.
"""

from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy import desc, and_, or_
from sqlalchemy.orm import Session

from app.models.user_feedback import UserFeedback


class FeedbackService:
    """Service for managing user feedback"""

    def __init__(self, db: Session):
        self.db = db

    def submit_feedback(
        self,
        user_id: int,
        feedback_type: str,
        subject: str,
        message: str,
        rating: Optional[int] = None
    ) -> UserFeedback:
        """
        Submit new feedback

        Args:
            user_id: ID of user submitting feedback
            feedback_type: 'bug', 'feature', or 'feedback'
            subject: Short summary
            message: Detailed message
            rating: Optional 1-5 star rating

        Returns:
            Created feedback object
        """
        feedback = UserFeedback(
            user_id=user_id,
            feedback_type=feedback_type,
            subject=subject,
            message=message,
            rating=rating
        )

        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)

        return feedback

    def get_user_feedback(self, user_id: int) -> List[UserFeedback]:
        """Get all feedback submitted by a user"""
        return self.db.query(UserFeedback).filter(
            UserFeedback.user_id == user_id
        ).order_by(desc(UserFeedback.created_at)).all()

    def get_all_feedback(
        self,
        page: int = 1,
        per_page: int = 20,
        feedback_type: Optional[str] = None,
        is_resolved: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict:
        """
        Get all feedback with pagination and filtering (admin only)

        Args:
            page: Page number
            per_page: Items per page
            feedback_type: Filter by type
            is_resolved: Filter by resolution status
            sort_by: Sort field
            sort_order: Sort direction

        Returns:
            Dictionary with feedback list and pagination info
        """
        query = self.db.query(UserFeedback)

        # Apply filters
        if feedback_type:
            query = query.filter(UserFeedback.feedback_type == feedback_type)

        if is_resolved is not None:
            query = query.filter(UserFeedback.is_resolved == is_resolved)

        # Get total count
        total_count = query.count()

        # Apply sorting
        sort_field = getattr(UserFeedback, sort_by, UserFeedback.created_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(sort_field)

        # Apply pagination
        offset = (page - 1) * per_page
        feedback_list = query.offset(offset).limit(per_page).all()

        total_pages = (total_count + per_page - 1) // per_page

        return {
            "feedback": feedback_list,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            }
        }

    def respond_to_feedback(
        self,
        feedback_id: int,
        admin_response: str,
        mark_resolved: bool = True
    ) -> Optional[UserFeedback]:
        """
        Admin responds to feedback

        Args:
            feedback_id: ID of feedback to respond to
            admin_response: Admin's response message
            mark_resolved: Whether to mark as resolved

        Returns:
            Updated feedback object or None if not found
        """
        feedback = self.db.query(UserFeedback).filter(
            UserFeedback.id == feedback_id
        ).first()

        if not feedback:
            return None

        feedback.admin_response = admin_response
        if mark_resolved:
            feedback.is_resolved = True
            feedback.resolved_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(feedback)

        return feedback

    def get_feedback_statistics(self) -> Dict:
        """Get feedback statistics for admin dashboard"""
        from sqlalchemy import func

        total = self.db.query(func.count(UserFeedback.id)).scalar() or 0
        resolved = self.db.query(func.count(UserFeedback.id)).filter(
            UserFeedback.is_resolved == True
        ).scalar() or 0
        pending = total - resolved

        # Count by type
        bugs = self.db.query(func.count(UserFeedback.id)).filter(
            UserFeedback.feedback_type == 'bug'
        ).scalar() or 0

        features = self.db.query(func.count(UserFeedback.id)).filter(
            UserFeedback.feedback_type == 'feature'
        ).scalar() or 0

        general = self.db.query(func.count(UserFeedback.id)).filter(
            UserFeedback.feedback_type == 'feedback'
        ).scalar() or 0

        # Average rating
        avg_rating = self.db.query(func.avg(UserFeedback.rating)).filter(
            UserFeedback.rating.isnot(None)
        ).scalar() or 0

        return {
            "total": total,
            "resolved": resolved,
            "pending": pending,
            "by_type": {
                "bugs": bugs,
                "features": features,
                "general": general,
            },
            "average_rating": round(float(avg_rating), 2) if avg_rating else 0,
        }


def get_feedback_service(db: Session) -> FeedbackService:
    """Factory function to get feedback service instance"""
    return FeedbackService(db)

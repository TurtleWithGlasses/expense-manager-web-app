"""
Admin Service

Provides administrative functionality for:
- User statistics and monitoring
- System health metrics
- User management (suspend, delete, reset)
"""

from datetime import datetime, timedelta, date
from typing import Dict, List, Optional
from sqlalchemy import func, and_, or_, desc, extract
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.entry import Entry
from app.models.category import Category
from app.models.ai_model import AIModel
from app.models.weekly_report import WeeklyReport
from app.models.financial_goal import FinancialGoal
from app.models.recurring_payment import RecurringPayment
from app.core.security import hash_password


class AdminService:
    """Service for admin operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_statistics(self) -> Dict:
        """
        Get comprehensive dashboard statistics

        Returns:
        - Total users (active, inactive, verified, unverified)
        - New registrations (today, this week, this month)
        - Active users (logged in within last 7/30 days)
        - Total entries, categories, goals
        - System activity metrics
        """
        now = datetime.utcnow()
        today = date.today()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        today_start = datetime.combine(today, datetime.min.time())

        # User statistics
        total_users = self.db.query(func.count(User.id)).scalar() or 0
        verified_users = self.db.query(func.count(User.id)).filter(User.is_verified == True).scalar() or 0
        unverified_users = total_users - verified_users

        # New registrations
        registrations_today = self.db.query(func.count(User.id)).filter(
            User.created_at >= today_start
        ).scalar() or 0

        registrations_week = self.db.query(func.count(User.id)).filter(
            User.created_at >= week_ago
        ).scalar() or 0

        registrations_month = self.db.query(func.count(User.id)).filter(
            User.created_at >= month_ago
        ).scalar() or 0

        # Content statistics
        total_entries = self.db.query(func.count(Entry.id)).scalar() or 0
        total_categories = self.db.query(func.count(Category.id)).scalar() or 0
        total_goals = self.db.query(func.count(FinancialGoal.id)).scalar() or 0
        total_recurring_payments = self.db.query(func.count(RecurringPayment.id)).scalar() or 0

        # Entries created this month
        entries_this_month = self.db.query(func.count(Entry.id)).filter(
            Entry.date >= month_ago.date()
        ).scalar() or 0

        # AI model statistics (count models that have been trained)
        ai_models_trained = self.db.query(func.count(AIModel.id)).filter(
            AIModel.last_trained.isnot(None)
        ).scalar() or 0

        # Reports generated
        reports_generated = self.db.query(func.count(WeeklyReport.id)).scalar() or 0

        return {
            "users": {
                "total": total_users,
                "verified": verified_users,
                "unverified": unverified_users,
                "registrations_today": registrations_today,
                "registrations_week": registrations_week,
                "registrations_month": registrations_month,
            },
            "content": {
                "total_entries": total_entries,
                "entries_this_month": entries_this_month,
                "total_categories": total_categories,
                "total_goals": total_goals,
                "total_recurring_payments": total_recurring_payments,
            },
            "ai": {
                "models_trained": ai_models_trained,
            },
            "reports": {
                "total_generated": reports_generated,
            },
            "generated_at": now.isoformat(),
        }

    def get_user_list(
        self,
        page: int = 1,
        per_page: int = 20,
        search: Optional[str] = None,
        filter_verified: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict:
        """
        Get paginated list of users with optional filtering

        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            search: Search by email or name
            filter_verified: Filter by verification status
            sort_by: Sort field (created_at, email, full_name)
            sort_order: Sort order (asc, desc)

        Returns:
            Dictionary with users list and pagination info
        """
        query = self.db.query(User)

        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    User.email.ilike(search_term),
                    User.full_name.ilike(search_term)
                )
            )

        # Apply verification filter
        if filter_verified is not None:
            query = query.filter(User.is_verified == filter_verified)

        # Get total count
        total_count = query.count()

        # Apply sorting
        sort_field = getattr(User, sort_by, User.created_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(sort_field)

        # Apply pagination
        offset = (page - 1) * per_page
        users = query.offset(offset).limit(per_page).all()

        # Get additional stats for each user
        user_list = []
        for user in users:
            entry_count = self.db.query(func.count(Entry.id)).filter(Entry.user_id == user.id).scalar() or 0
            category_count = self.db.query(func.count(Category.id)).filter(Category.user_id == user.id).scalar() or 0
            goal_count = self.db.query(func.count(FinancialGoal.id)).filter(FinancialGoal.user_id == user.id).scalar() or 0

            # Get last entry date
            last_entry = self.db.query(Entry).filter(Entry.user_id == user.id).order_by(desc(Entry.date)).first()
            last_activity = last_entry.date if last_entry else None

            user_list.append({
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_verified": user.is_verified,
                "is_admin": user.is_admin,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "stats": {
                    "entries": entry_count,
                    "categories": category_count,
                    "goals": goal_count,
                    "last_activity": last_activity.isoformat() if last_activity else None,
                }
            })

        total_pages = (total_count + per_page - 1) // per_page

        return {
            "users": user_list,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            }
        }

    def get_user_activity_stats(self, days: int = 30) -> Dict:
        """
        Get user activity statistics for the last N days

        Returns daily user registration counts
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get daily registration counts
        daily_registrations = self.db.query(
            func.date(User.created_at).label('date'),
            func.count(User.id).label('count')
        ).filter(
            User.created_at >= start_date
        ).group_by(
            func.date(User.created_at)
        ).order_by(
            func.date(User.created_at)
        ).all()

        # Format results
        activity_data = []
        for reg in daily_registrations:
            activity_data.append({
                "date": str(reg.date) if reg.date else None,
                "registrations": reg.count
            })

        return {
            "period_days": days,
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat(),
            "daily_activity": activity_data,
        }

    def get_system_health_metrics(self) -> Dict:
        """
        Get system health metrics

        Returns:
        - Database statistics
        - Recent activity indicators
        - System status
        """
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)

        # Recent activity (last hour)
        recent_entries = self.db.query(func.count(Entry.id)).filter(
            Entry.date >= hour_ago.date()
        ).scalar() or 0

        recent_registrations = self.db.query(func.count(User.id)).filter(
            User.created_at >= hour_ago
        ).scalar() or 0

        # Get database table sizes (counts)
        table_sizes = {
            "users": self.db.query(func.count(User.id)).scalar() or 0,
            "entries": self.db.query(func.count(Entry.id)).scalar() or 0,
            "categories": self.db.query(func.count(Category.id)).scalar() or 0,
            "ai_models": self.db.query(func.count(AIModel.id)).scalar() or 0,
            "weekly_reports": self.db.query(func.count(WeeklyReport.id)).scalar() or 0,
            "financial_goals": self.db.query(func.count(FinancialGoal.id)).scalar() or 0,
            "recurring_payments": self.db.query(func.count(RecurringPayment.id)).scalar() or 0,
        }

        return {
            "status": "operational",
            "checked_at": now.isoformat(),
            "recent_activity": {
                "entries_last_hour": recent_entries,
                "registrations_last_hour": recent_registrations,
            },
            "database": {
                "table_sizes": table_sizes,
                "total_records": sum(table_sizes.values()),
            }
        }

    def get_user_details(self, user_id: int) -> Optional[Dict]:
        """Get detailed information about a specific user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        # Get comprehensive stats
        entry_count = self.db.query(func.count(Entry.id)).filter(Entry.user_id == user.id).scalar() or 0
        category_count = self.db.query(func.count(Category.id)).filter(Category.user_id == user.id).scalar() or 0
        goal_count = self.db.query(func.count(FinancialGoal.id)).filter(FinancialGoal.user_id == user.id).scalar() or 0
        recurring_payment_count = self.db.query(func.count(RecurringPayment.id)).filter(
            RecurringPayment.user_id == user.id
        ).scalar() or 0
        ai_model_count = self.db.query(func.count(AIModel.id)).filter(AIModel.user_id == user.id).scalar() or 0

        # Get last entry
        last_entry = self.db.query(Entry).filter(Entry.user_id == user.id).order_by(desc(Entry.date)).first()

        # Get first entry
        first_entry = self.db.query(Entry).filter(Entry.user_id == user.id).order_by(Entry.date).first()

        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_verified": user.is_verified,
            "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "stats": {
                "entries": entry_count,
                "categories": category_count,
                "goals": goal_count,
                "recurring_payments": recurring_payment_count,
                "ai_models": ai_model_count,
                "first_entry_date": first_entry.date.isoformat() if first_entry else None,
                "last_entry_date": last_entry.date.isoformat() if last_entry else None,
                "account_age_days": (datetime.utcnow() - user.created_at).days if user.created_at else 0,
            }
        }

    def resend_verification_email(self, user_id: int) -> bool:
        """Resend verification email to user (admin-initiated)"""
        # This would integrate with your email service
        # For now, just return True
        user = self.db.query(User).filter(User.id == user_id).first()
        return user is not None

    def admin_reset_password(self, user_id: int, new_password: str) -> bool:
        """Admin-initiated password reset"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        user.hashed_password = hash_password(new_password)
        self.db.commit()
        return True

    def delete_user_account(self, user_id: int) -> bool:
        """
        Delete user account (admin action)

        Cascading deletes will handle all related data
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # Prevent deleting admin users
        if user.is_admin:
            return False

        self.db.delete(user)
        self.db.commit()
        return True


def get_admin_service(db: Session) -> AdminService:
    """Factory function to get admin service instance"""
    return AdminService(db)

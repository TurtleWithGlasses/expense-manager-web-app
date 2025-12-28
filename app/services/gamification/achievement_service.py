"""
Achievement Service - Phase 1.1

Handles achievement checking, unlocking, and progress tracking.
Automatically checks achievements after user actions.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
import logging

from app.models.achievement import Achievement, UserAchievement
from app.models.entry import Entry
from app.models.user import User

logger = logging.getLogger(__name__)


class AchievementService:
    """Service for managing user achievements"""

    @staticmethod
    def check_and_unlock_achievements(db: Session, user_id: int) -> List[UserAchievement]:
        """
        Check all achievements for a user and unlock any newly earned ones

        Called after user actions like:
        - Adding an entry
        - Completing a goal
        - Reaching a streak

        Returns list of newly unlocked achievements
        """
        # Get all active achievements
        achievements = db.query(Achievement).filter(
            Achievement.is_active == True
        ).all()

        newly_unlocked = []

        for achievement in achievements:
            # Skip if user already has this achievement
            existing = db.query(UserAchievement).filter(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_id == achievement.id
            ).first()

            if existing:
                continue

            # Check if user meets criteria
            if AchievementService._check_criteria(db, user_id, achievement.unlock_criteria):
                # Unlock achievement!
                user_achievement = UserAchievement(
                    user_id=user_id,
                    achievement_id=achievement.id,
                    is_completed=True,
                    is_new=True,
                    earned_at=datetime.utcnow()
                )
                db.add(user_achievement)
                newly_unlocked.append(user_achievement)

                logger.info(f"User {user_id} unlocked achievement: {achievement.code}")

        if newly_unlocked:
            db.commit()

        return newly_unlocked

    @staticmethod
    def _check_criteria(db: Session, user_id: int, criteria: Dict) -> bool:
        """
        Check if user meets achievement criteria

        Criteria examples:
        {'type': 'entry_count', 'threshold': 1}
        {'type': 'daily_streak', 'days': 7}
        {'type': 'savings_rate', 'percentage': 20}
        {'type': 'no_spend_days', 'count': 3, 'period': 'month'}
        """
        criteria_type = criteria.get('type')

        if criteria_type == 'entry_count':
            return AchievementService._check_entry_count(db, user_id, criteria['threshold'])

        elif criteria_type == 'daily_streak':
            return AchievementService._check_daily_streak(db, user_id, criteria['days'])

        elif criteria_type == 'no_spend_days':
            return AchievementService._check_no_spend_days(
                db, user_id, criteria['count'], criteria.get('period', 'month')
            )

        elif criteria_type == 'savings_rate':
            return AchievementService._check_savings_rate(db, user_id, criteria['percentage'])

        elif criteria_type == 'category_budget':
            return AchievementService._check_category_budget(db, user_id, criteria)

        elif criteria_type == 'total_saved':
            return AchievementService._check_total_saved(db, user_id, criteria['amount'])

        elif criteria_type == 'expense_reduction':
            return AchievementService._check_expense_reduction(db, user_id, criteria['percentage'])

        else:
            logger.warning(f"Unknown achievement criteria type: {criteria_type}")
            return False

    @staticmethod
    def _check_entry_count(db: Session, user_id: int, threshold: int) -> bool:
        """Check if user has logged enough entries"""
        count = db.query(func.count(Entry.id)).filter(
            Entry.user_id == user_id
        ).scalar()

        return count >= threshold

    @staticmethod
    def _check_daily_streak(db: Session, user_id: int, required_days: int) -> bool:
        """
        Check if user has logged entries for consecutive days

        Returns True if user has a current streak >= required_days
        """
        # Get dates with entries, ordered by date descending
        dates = db.query(Entry.date).filter(
            Entry.user_id == user_id
        ).distinct().order_by(Entry.date.desc()).all()

        if not dates:
            return False

        dates = [d[0] for d in dates]

        # Check consecutive days starting from today or most recent entry
        today = date.today()
        current_streak = 0

        # Start from today or most recent entry
        if dates[0] >= today:
            check_date = today
        else:
            check_date = dates[0]

        # Count backwards
        for i in range(365):  # Max check 365 days
            if check_date in dates:
                current_streak += 1
                if current_streak >= required_days:
                    return True
            else:
                # Streak broken
                break

            check_date -= timedelta(days=1)

        return False

    @staticmethod
    def _check_no_spend_days(db: Session, user_id: int, required_count: int, period: str = 'month') -> bool:
        """
        Check if user has enough no-spend days in the period

        A "no-spend day" is a day with no expense entries
        """
        # Determine date range
        if period == 'month':
            start_date = date.today().replace(day=1)
            end_date = date.today()
        elif period == 'week':
            start_date = date.today() - timedelta(days=date.today().weekday())
            end_date = date.today()
        else:
            start_date = date.today() - timedelta(days=30)
            end_date = date.today()

        # Get days with expenses
        days_with_expenses = db.query(Entry.date).filter(
            Entry.user_id == user_id,
            Entry.type == 'expense',
            Entry.date >= start_date,
            Entry.date <= end_date
        ).distinct().all()

        days_with_expenses = {d[0] for d in days_with_expenses}

        # Count days in period
        total_days = (end_date - start_date).days + 1

        # Calculate no-spend days
        no_spend_days = total_days - len(days_with_expenses)

        return no_spend_days >= required_count

    @staticmethod
    def _check_savings_rate(db: Session, user_id: int, required_percentage: float) -> bool:
        """
        Check if user's savings rate meets threshold

        Savings rate = (Income - Expenses) / Income * 100
        Calculated for the current month
        """
        start_date = date.today().replace(day=1)
        end_date = date.today()

        # Get total income
        total_income = db.query(func.sum(Entry.amount)).filter(
            Entry.user_id == user_id,
            Entry.type == 'income',
            Entry.date >= start_date,
            Entry.date <= end_date
        ).scalar() or 0

        if total_income == 0:
            return False

        # Get total expenses
        total_expenses = db.query(func.sum(Entry.amount)).filter(
            Entry.user_id == user_id,
            Entry.type == 'expense',
            Entry.date >= start_date,
            Entry.date <= end_date
        ).scalar() or 0

        # Calculate savings rate
        savings = total_income - total_expenses
        savings_rate = (savings / total_income) * 100

        return savings_rate >= required_percentage

    @staticmethod
    def _check_category_budget(db: Session, user_id: int, criteria: Dict) -> bool:
        """
        Check if user stayed within category budget

        Criteria: {'type': 'category_budget', 'category_id': 5, 'budget': 500, 'period': 'month'}
        """
        category_id = criteria.get('category_id')
        budget = criteria.get('budget')
        period = criteria.get('period', 'month')

        if period == 'month':
            start_date = date.today().replace(day=1)
        else:
            start_date = date.today() - timedelta(days=30)

        # Get category spending
        total_spent = db.query(func.sum(Entry.amount)).filter(
            Entry.user_id == user_id,
            Entry.type == 'expense',
            Entry.category_id == category_id,
            Entry.date >= start_date
        ).scalar() or 0

        return total_spent <= budget

    @staticmethod
    def _check_total_saved(db: Session, user_id: int, required_amount: float) -> bool:
        """Check if user has saved a total amount over all time"""
        total_income = db.query(func.sum(Entry.amount)).filter(
            Entry.user_id == user_id,
            Entry.type == 'income'
        ).scalar() or 0

        total_expenses = db.query(func.sum(Entry.amount)).filter(
            Entry.user_id == user_id,
            Entry.type == 'expense'
        ).scalar() or 0

        total_saved = total_income - total_expenses

        return total_saved >= required_amount

    @staticmethod
    def _check_expense_reduction(db: Session, user_id: int, required_percentage: float) -> bool:
        """
        Check if user reduced expenses by percentage compared to previous month

        Compares current month vs previous month spending
        """
        # Current month
        current_month_start = date.today().replace(day=1)
        current_month_end = date.today()

        current_expenses = db.query(func.sum(Entry.amount)).filter(
            Entry.user_id == user_id,
            Entry.type == 'expense',
            Entry.date >= current_month_start,
            Entry.date <= current_month_end
        ).scalar() or 0

        # Previous month
        prev_month_end = current_month_start - timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)

        prev_expenses = db.query(func.sum(Entry.amount)).filter(
            Entry.user_id == user_id,
            Entry.type == 'expense',
            Entry.date >= prev_month_start,
            Entry.date <= prev_month_end
        ).scalar() or 0

        if prev_expenses == 0:
            return False

        # Calculate reduction
        reduction = ((prev_expenses - current_expenses) / prev_expenses) * 100

        return reduction >= required_percentage

    @staticmethod
    def get_user_achievements(db: Session, user_id: int, include_locked: bool = False) -> List[Dict]:
        """
        Get all achievements for a user with progress information

        Returns achievements with progress data and locked/unlocked status
        """
        # Get all achievements
        achievements = db.query(Achievement).filter(
            Achievement.is_active == True
        ).order_by(Achievement.sort_order, Achievement.id).all()

        # Get user's unlocked achievements
        user_achievements = db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id
        ).all()

        unlocked_ids = {ua.achievement_id for ua in user_achievements}
        user_achievement_map = {ua.achievement_id: ua for ua in user_achievements}

        result = []

        for achievement in achievements:
            # Skip secret achievements that aren't unlocked
            if achievement.is_secret and achievement.id not in unlocked_ids:
                if not include_locked:
                    continue

            achievement_data = achievement.to_dict()
            achievement_data['is_unlocked'] = achievement.id in unlocked_ids

            if achievement.id in unlocked_ids:
                # Add unlock data
                user_ach = user_achievement_map[achievement.id]
                achievement_data['earned_at'] = user_ach.earned_at.isoformat() if user_ach.earned_at else None
                achievement_data['is_new'] = user_ach.is_new
                achievement_data['progress'] = 100  # Completed
            else:
                # Calculate progress
                progress = AchievementService._calculate_progress(db, user_id, achievement.unlock_criteria)
                achievement_data['progress'] = progress

                # Hide details for secret achievements
                if achievement.is_secret:
                    achievement_data['name'] = '???'
                    achievement_data['description'] = 'Secret achievement - unlock to reveal!'
                    achievement_data['progress'] = 0

            result.append(achievement_data)

        return result

    @staticmethod
    def _calculate_progress(db: Session, user_id: int, criteria: Dict) -> int:
        """
        Calculate achievement progress percentage (0-100)
        """
        criteria_type = criteria.get('type')

        if criteria_type == 'entry_count':
            count = db.query(func.count(Entry.id)).filter(Entry.user_id == user_id).scalar()
            threshold = criteria['threshold']
            return min(100, int((count / threshold) * 100))

        elif criteria_type == 'daily_streak':
            # This is complex, return simplified version
            # In production, calculate actual current streak
            return 0  # TODO: Implement streak progress

        elif criteria_type == 'savings_rate':
            # Calculate current savings rate
            start_date = date.today().replace(day=1)
            total_income = db.query(func.sum(Entry.amount)).filter(
                Entry.user_id == user_id,
                Entry.type == 'income',
                Entry.date >= start_date
            ).scalar() or 0

            if total_income == 0:
                return 0

            total_expenses = db.query(func.sum(Entry.amount)).filter(
                Entry.user_id == user_id,
                Entry.type == 'expense',
                Entry.date >= start_date
            ).scalar() or 0

            savings_rate = ((total_income - total_expenses) / total_income) * 100
            target_rate = criteria['percentage']

            return min(100, int((savings_rate / target_rate) * 100))

        # Default: unknown progress
        return 0

    @staticmethod
    def mark_achievements_viewed(db: Session, user_id: int) -> int:
        """
        Mark all new achievements as viewed

        Returns count of achievements marked
        """
        count = db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id,
            UserAchievement.is_new == True
        ).update({
            'is_new': False,
            'viewed_at': datetime.utcnow()
        })

        db.commit()
        return count

    @staticmethod
    def get_achievement_stats(db: Session, user_id: int) -> Dict:
        """
        Get achievement statistics for a user

        Returns total points, unlocked count, etc.
        """
        # Get user's unlocked achievements with their achievement details
        user_achievements = db.query(UserAchievement).join(Achievement).filter(
            UserAchievement.user_id == user_id
        ).all()

        # Calculate total points
        total_points = sum(ua.achievement.points for ua in user_achievements)

        # Count by tier
        tier_counts = {}
        for ua in user_achievements:
            tier = ua.achievement.tier
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

        # Total available achievements
        total_achievements = db.query(func.count(Achievement.id)).filter(
            Achievement.is_active == True,
            Achievement.is_secret == False  # Don't count secret in total
        ).scalar()

        return {
            'total_points': total_points,
            'unlocked_count': len(user_achievements),
            'total_count': total_achievements,
            'completion_percentage': int((len(user_achievements) / total_achievements * 100)) if total_achievements > 0 else 0,
            'tier_counts': tier_counts,
            'recent_achievements': [ua.to_dict() for ua in user_achievements[-5:]]  # Last 5
        }

"""
Achievement Service - Phase 1.1

Manages achievement unlocking, tracking, and progress calculation.
Handles both automatic achievement checking and manual triggers.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.achievement import Achievement, UserAchievement
from app.models.entry import Entry
from app.models.financial_goal import FinancialGoal
from app.models.user import User


class AchievementService:
    """
    Manages achievement unlocking and tracking

    Evaluates user data against achievement criteria and awards
    achievements when conditions are met.
    """

    def __init__(self, db: Session):
        self.db = db

    async def check_and_unlock_achievements(self, user_id: int) -> List[UserAchievement]:
        """
        Check all achievement criteria and unlock new ones

        Args:
            user_id: The user to check achievements for

        Returns:
            List of newly unlocked achievements
        """
        # Get all active achievements
        all_achievements = self.db.query(Achievement).filter(
            Achievement.is_active == True
        ).all()

        # Get user's already earned achievements
        earned_achievement_ids = {
            ua.achievement_id for ua in
            self.db.query(UserAchievement.achievement_id).filter(
                UserAchievement.user_id == user_id
            ).all()
        }

        newly_unlocked = []

        for achievement in all_achievements:
            # Skip if already earned
            if achievement.id in earned_achievement_ids:
                continue

            # Check if criteria is met
            is_unlocked, progress_data = await self._check_achievement_criteria(
                user_id,
                achievement.unlock_criteria
            )

            if is_unlocked:
                # Award the achievement
                user_achievement = UserAchievement(
                    user_id=user_id,
                    achievement_id=achievement.id,
                    earned_at=datetime.utcnow(),
                    is_completed=True,
                    is_new=True,
                    progress_data=progress_data
                )
                self.db.add(user_achievement)
                self.db.commit()
                self.db.refresh(user_achievement)

                # Award XP to user
                user = self.db.query(User).filter(User.id == user_id).first()
                if user:
                    user.xp += achievement.points
                    self.db.commit()

                newly_unlocked.append(user_achievement)

        return newly_unlocked

    async def _check_achievement_criteria(
        self,
        user_id: int,
        criteria: Dict[str, Any]
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check if achievement criteria is met

        Args:
            user_id: The user to check
            criteria: The unlock criteria dict

        Returns:
            Tuple of (is_met, progress_data)
        """
        criteria_type = criteria.get('type')

        if criteria_type == 'entry_count':
            return await self._check_entry_count(user_id, criteria)
        elif criteria_type == 'daily_streak':
            return await self._check_daily_streak(user_id, criteria)
        elif criteria_type == 'no_spend_days':
            return await self._check_no_spend_days(user_id, criteria)
        elif criteria_type == 'savings_rate':
            return await self._check_savings_rate(user_id, criteria)
        elif criteria_type == 'goal_completion':
            return await self._check_goal_completion(user_id, criteria)
        elif criteria_type == 'budget_discipline':
            return await self._check_budget_discipline(user_id, criteria)
        elif criteria_type == 'category_usage':
            return await self._check_category_usage(user_id, criteria)
        else:
            return False, {}

    async def _check_entry_count(self, user_id: int, criteria: Dict) -> tuple[bool, Dict]:
        """Check if user has logged enough entries"""
        threshold = criteria.get('threshold', 1)

        count = self.db.query(func.count(Entry.id)).filter(
            Entry.user_id == user_id
        ).scalar()

        progress = {
            'current': count,
            'target': threshold,
            'percentage': min(100, int((count / threshold) * 100))
        }

        return count >= threshold, progress

    async def _check_daily_streak(self, user_id: int, criteria: Dict) -> tuple[bool, Dict]:
        """Check if user has logged entries for consecutive days"""
        required_days = criteria.get('days', 7)

        # Get unique entry dates for last 60 days
        sixty_days_ago = date.today() - timedelta(days=60)
        entry_dates = self.db.query(
            func.date(Entry.date).label('entry_date')
        ).filter(
            and_(
                Entry.user_id == user_id,
                Entry.date >= sixty_days_ago
            )
        ).distinct().order_by(func.date(Entry.date).desc()).all()

        if not entry_dates:
            return False, {'current': 0, 'target': required_days, 'percentage': 0}

        # Calculate current streak
        current_streak = 0
        expected_date = date.today()

        for (entry_date,) in entry_dates:
            if entry_date == expected_date or entry_date == expected_date - timedelta(days=1):
                current_streak += 1
                expected_date = entry_date - timedelta(days=1)
            else:
                break

        progress = {
            'current': current_streak,
            'target': required_days,
            'percentage': min(100, int((current_streak / required_days) * 100))
        }

        return current_streak >= required_days, progress

    async def _check_no_spend_days(self, user_id: int, criteria: Dict) -> tuple[bool, Dict]:
        """Check if user has enough no-spend days in current month"""
        threshold = criteria.get('threshold', 2)
        period = criteria.get('period', 'month')

        # Get start of current month
        today = date.today()
        month_start = date(today.year, today.month, 1)

        # Get all days in current month with expenses
        expense_dates = self.db.query(
            func.date(Entry.date).label('expense_date')
        ).filter(
            and_(
                Entry.user_id == user_id,
                Entry.type == 'expense',
                Entry.date >= month_start,
                Entry.date <= today
            )
        ).distinct().all()

        expense_date_set = {d[0] for d in expense_dates}

        # Count no-spend days
        no_spend_count = 0
        current_date = month_start
        while current_date <= today:
            if current_date not in expense_date_set:
                no_spend_count += 1
            current_date += timedelta(days=1)

        progress = {
            'current': no_spend_count,
            'target': threshold,
            'percentage': min(100, int((no_spend_count / threshold) * 100))
        }

        return no_spend_count >= threshold, progress

    async def _check_savings_rate(self, user_id: int, criteria: Dict) -> tuple[bool, Dict]:
        """Check if user has maintained savings rate"""
        target_percentage = criteria.get('percentage', 20)  # e.g., 20%

        # Calculate for last 30 days
        thirty_days_ago = date.today() - timedelta(days=30)

        income = self.db.query(func.sum(Entry.amount)).filter(
            and_(
                Entry.user_id == user_id,
                Entry.type == 'income',
                Entry.date >= thirty_days_ago
            )
        ).scalar() or 0

        expenses = self.db.query(func.sum(Entry.amount)).filter(
            and_(
                Entry.user_id == user_id,
                Entry.type == 'expense',
                Entry.date >= thirty_days_ago
            )
        ).scalar() or 0

        if income == 0:
            return False, {'current': 0, 'target': target_percentage, 'percentage': 0}

        savings_rate = ((income - expenses) / income) * 100

        progress = {
            'current': round(savings_rate, 2),
            'target': target_percentage,
            'percentage': min(100, int((savings_rate / target_percentage) * 100))
        }

        return savings_rate >= target_percentage, progress

    async def _check_goal_completion(self, user_id: int, criteria: Dict) -> tuple[bool, Dict]:
        """Check if user has completed enough goals"""
        threshold = criteria.get('threshold', 1)

        completed_count = self.db.query(func.count(FinancialGoal.id)).filter(
            and_(
                FinancialGoal.user_id == user_id,
                FinancialGoal.status == 'completed'
            )
        ).scalar()

        progress = {
            'current': completed_count,
            'target': threshold,
            'percentage': min(100, int((completed_count / threshold) * 100))
        }

        return completed_count >= threshold, progress

    async def _check_budget_discipline(self, user_id: int, criteria: Dict) -> tuple[bool, Dict]:
        """Check if user stayed under budget for required days"""
        required_days = criteria.get('days', 7)

        # This is a simplified check - in practice, you'd compare against
        # user's budget settings for each category
        # For now, just check if they had consistent spending (placeholder)

        progress = {
            'current': 0,
            'target': required_days,
            'percentage': 0
        }

        return False, progress  # Placeholder

    async def _check_category_usage(self, user_id: int, criteria: Dict) -> tuple[bool, Dict]:
        """Check if user has used enough categories"""
        threshold = criteria.get('threshold', 5)

        category_count = self.db.query(func.count(func.distinct(Entry.category_id))).filter(
            Entry.user_id == user_id
        ).scalar()

        progress = {
            'current': category_count,
            'target': threshold,
            'percentage': min(100, int((category_count / threshold) * 100))
        }

        return category_count >= threshold, progress

    async def get_user_achievements(
        self,
        user_id: int,
        include_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Get all achievements for a user with progress

        Args:
            user_id: The user ID
            include_progress: Whether to calculate progress for locked achievements

        Returns:
            Dict with earned and available achievements
        """
        # Get earned achievements
        earned = self.db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id
        ).all()

        # Get all achievements
        all_achievements = self.db.query(Achievement).filter(
            Achievement.is_active == True
        ).all()

        earned_ids = {ua.achievement_id for ua in earned}

        earned_list = []
        available_list = []

        for achievement in all_achievements:
            achievement_dict = achievement.to_dict()

            if achievement.id in earned_ids:
                # Find the user_achievement
                user_ach = next(ua for ua in earned if ua.achievement_id == achievement.id)
                earned_list.append({
                    **achievement_dict,
                    'earned_at': user_ach.earned_at.isoformat() if user_ach.earned_at else None,
                    'is_new': user_ach.is_new,
                    'progress': user_ach.progress_data
                })
            else:
                # Calculate current progress if requested
                if include_progress and not achievement.is_secret:
                    _, progress = await self._check_achievement_criteria(
                        user_id,
                        achievement.unlock_criteria
                    )
                    achievement_dict['progress'] = progress
                else:
                    achievement_dict['progress'] = None

                available_list.append(achievement_dict)

        return {
            'earned': earned_list,
            'available': available_list,
            'total_earned': len(earned_list),
            'total_available': len(all_achievements),
            'completion_percentage': round((len(earned_list) / len(all_achievements)) * 100, 2) if all_achievements else 0
        }

    async def get_achievement_progress(
        self,
        user_id: int,
        achievement_code: str
    ) -> Dict[str, Any]:
        """
        Get progress towards a specific achievement

        Args:
            user_id: The user ID
            achievement_code: The achievement code

        Returns:
            Dict with achievement details and progress
        """
        achievement = self.db.query(Achievement).filter(
            Achievement.code == achievement_code
        ).first()

        if not achievement:
            return None

        # Check if already earned
        user_ach = self.db.query(UserAchievement).filter(
            and_(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_id == achievement.id
            )
        ).first()

        if user_ach:
            return {
                **achievement.to_dict(),
                'is_earned': True,
                'earned_at': user_ach.earned_at.isoformat(),
                'progress': user_ach.progress_data
            }

        # Calculate current progress
        _, progress = await self._check_achievement_criteria(
            user_id,
            achievement.unlock_criteria
        )

        return {
            **achievement.to_dict(),
            'is_earned': False,
            'progress': progress
        }

    async def mark_achievement_seen(self, user_id: int, achievement_id: int) -> bool:
        """
        Mark an achievement as seen (remove NEW badge)

        Args:
            user_id: The user ID
            achievement_id: The achievement ID

        Returns:
            True if successful, False otherwise
        """
        user_ach = self.db.query(UserAchievement).filter(
            and_(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_id == achievement_id
            )
        ).first()

        if not user_ach:
            return False

        user_ach.is_new = False
        user_ach.viewed_at = datetime.utcnow()
        self.db.commit()

        return True

    async def seed_default_achievements(self):
        """
        Create default achievement definitions

        Seeds 20+ achievements covering various categories
        """
        default_achievements = [
            # Tracking Consistency
            {
                'code': 'first_entry',
                'name': 'First Step',
                'description': 'Log your first transaction',
                'category': 'tracking',
                'tier': 'bronze',
                'icon_name': 'trophy',
                'color_hex': '#CD7F32',
                'points': 10,
                'unlock_criteria': {'type': 'entry_count', 'threshold': 1}
            },
            {
                'code': 'streak_7',
                'name': '7-Day Streak',
                'description': 'Log entries for 7 consecutive days',
                'category': 'tracking',
                'tier': 'silver',
                'icon_name': 'fire',
                'color_hex': '#C0C0C0',
                'points': 50,
                'unlock_criteria': {'type': 'daily_streak', 'days': 7}
            },
            {
                'code': 'streak_14',
                'name': '14-Day Streak',
                'description': 'Log entries for 14 consecutive days',
                'category': 'tracking',
                'tier': 'gold',
                'icon_name': 'fire',
                'color_hex': '#FFD700',
                'points': 100,
                'unlock_criteria': {'type': 'daily_streak', 'days': 14}
            },
            {
                'code': 'streak_30',
                'name': 'Monthly Master',
                'description': 'Log entries for 30 consecutive days',
                'category': 'tracking',
                'tier': 'platinum',
                'icon_name': 'fire',
                'color_hex': '#E5E4E2',
                'points': 200,
                'unlock_criteria': {'type': 'daily_streak', 'days': 30}
            },

            # No-Spend Days
            {
                'code': 'no_spend_days_1',
                'name': 'Restraint Rookie',
                'description': 'Have at least 1 no-spend day this month',
                'category': 'saving',
                'tier': 'bronze',
                'icon_name': 'piggy-bank',
                'color_hex': '#CD7F32',
                'points': 20,
                'unlock_criteria': {'type': 'no_spend_days', 'threshold': 1, 'period': 'month'}
            },
            {
                'code': 'no_spend_days_3',
                'name': 'Spending Saver',
                'description': 'Have at least 3 no-spend days this month',
                'category': 'saving',
                'tier': 'silver',
                'icon_name': 'piggy-bank',
                'color_hex': '#C0C0C0',
                'points': 50,
                'unlock_criteria': {'type': 'no_spend_days', 'threshold': 3, 'period': 'month'}
            },
            {
                'code': 'no_spend_days_7',
                'name': 'Frugal Champion',
                'description': 'Have at least 7 no-spend days this month',
                'category': 'saving',
                'tier': 'gold',
                'icon_name': 'piggy-bank',
                'color_hex': '#FFD700',
                'points': 100,
                'unlock_criteria': {'type': 'no_spend_days', 'threshold': 7, 'period': 'month'}
            },
            {
                'code': 'no_spend_days_14',
                'name': 'Minimalist Master',
                'description': 'Have at least 14 no-spend days this month',
                'category': 'saving',
                'tier': 'platinum',
                'icon_name': 'piggy-bank',
                'color_hex': '#E5E4E2',
                'points': 200,
                'unlock_criteria': {'type': 'no_spend_days', 'threshold': 14, 'period': 'month'}
            },

            # Savings Rate
            {
                'code': 'savings_rate_10',
                'name': 'Savings Starter',
                'description': 'Maintain 10% savings rate for 30 days',
                'category': 'saving',
                'tier': 'bronze',
                'icon_name': 'chart-line',
                'color_hex': '#CD7F32',
                'points': 30,
                'unlock_criteria': {'type': 'savings_rate', 'percentage': 10}
            },
            {
                'code': 'savings_rate_20',
                'name': 'Thrifty Expert',
                'description': 'Maintain 20% savings rate for 30 days',
                'category': 'saving',
                'tier': 'silver',
                'icon_name': 'chart-line',
                'color_hex': '#C0C0C0',
                'points': 75,
                'unlock_criteria': {'type': 'savings_rate', 'percentage': 20}
            },
            {
                'code': 'savings_rate_30',
                'name': 'Savings Superstar',
                'description': 'Maintain 30% savings rate for 30 days',
                'category': 'saving',
                'tier': 'gold',
                'icon_name': 'chart-line',
                'color_hex': '#FFD700',
                'points': 150,
                'unlock_criteria': {'type': 'savings_rate', 'percentage': 30}
            },

            # Goal Completion
            {
                'code': 'goal_complete_1',
                'name': 'Goal Getter',
                'description': 'Complete your first financial goal',
                'category': 'goal',
                'tier': 'bronze',
                'icon_name': 'target',
                'color_hex': '#CD7F32',
                'points': 50,
                'unlock_criteria': {'type': 'goal_completion', 'threshold': 1}
            },
            {
                'code': 'goal_complete_3',
                'name': 'Goal Crusher',
                'description': 'Complete 3 financial goals',
                'category': 'goal',
                'tier': 'silver',
                'icon_name': 'target',
                'color_hex': '#C0C0C0',
                'points': 100,
                'unlock_criteria': {'type': 'goal_completion', 'threshold': 3}
            },
            {
                'code': 'goal_complete_5',
                'name': 'Goal Master',
                'description': 'Complete 5 financial goals',
                'category': 'goal',
                'tier': 'gold',
                'icon_name': 'target',
                'color_hex': '#FFD700',
                'points': 200,
                'unlock_criteria': {'type': 'goal_completion', 'threshold': 5}
            },
            {
                'code': 'goal_complete_10',
                'name': 'Goal Legend',
                'description': 'Complete 10 financial goals',
                'category': 'goal',
                'tier': 'platinum',
                'icon_name': 'target',
                'color_hex': '#E5E4E2',
                'points': 500,
                'unlock_criteria': {'type': 'goal_completion', 'threshold': 10}
            },

            # Category Usage
            {
                'code': 'category_usage_5',
                'name': 'Category Explorer',
                'description': 'Use at least 5 different categories',
                'category': 'tracking',
                'tier': 'bronze',
                'icon_name': 'folder',
                'color_hex': '#CD7F32',
                'points': 25,
                'unlock_criteria': {'type': 'category_usage', 'threshold': 5}
            },
            {
                'code': 'category_usage_10',
                'name': 'Category Pro',
                'description': 'Use at least 10 different categories',
                'category': 'tracking',
                'tier': 'silver',
                'icon_name': 'folder',
                'color_hex': '#C0C0C0',
                'points': 50,
                'unlock_criteria': {'type': 'category_usage', 'threshold': 10}
            },
        ]

        for ach_data in default_achievements:
            # Check if achievement already exists
            existing = self.db.query(Achievement).filter(
                Achievement.code == ach_data['code']
            ).first()

            if not existing:
                achievement = Achievement(**ach_data)
                self.db.add(achievement)

        self.db.commit()
        return len(default_achievements)

"""Level & XP Service - Phase 3: Full Gamification

Handles user experience points (XP) and leveling system.
Users earn XP through various activities and unlock new levels.
"""
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session

from app.models.user import User


class LevelService:
    """Service for managing user levels and experience points"""

    # XP required for each level (exponential curve)
    LEVEL_THRESHOLDS = {
        1: 0,
        2: 100,
        3: 250,
        4: 500,
        5: 850,
        6: 1300,
        7: 1850,
        8: 2500,
        9: 3250,
        10: 4100,
        11: 5050,
        12: 6100,
        13: 7250,
        14: 8500,
        15: 9850,
        16: 11300,
        17: 12850,
        18: 14500,
        19: 16250,
        20: 18100,
        21: 20050,
        22: 22100,
        23: 24250,
        24: 26500,
        25: 28850,
        26: 31300,
        27: 33850,
        28: 36500,
        29: 39250,
        30: 42100,
        # Levels 31-50 continue with similar pattern
        35: 54600,
        40: 70100,
        45: 88100,
        50: 108600,
    }

    # XP rewards for different activities
    XP_REWARDS = {
        'entry_logged': 5,
        'goal_created': 20,
        'goal_completed': 100,
        'achievement_unlocked': 50,
        'badge_earned': 75,
        'challenge_completed': 150,
        'weekly_report_viewed': 10,
        'forecast_created': 30,
        'scenario_created': 25,
        'budget_adhered': 40,
        'daily_streak_milestone': 30,  # Per milestone (7, 14, 30 days)
    }

    def __init__(self, db: Session):
        self.db = db

    def add_xp(self, user_id: int, xp_amount: int, reason: str = None) -> Dict:
        """
        Add XP to user and check for level up

        Returns:
            Dict with level_up status, new level, xp gained, etc.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        # Initialize if not set
        if not hasattr(user, 'xp') or user.xp is None:
            user.xp = 0
        if not hasattr(user, 'level') or user.level is None:
            user.level = 1

        old_level = user.level
        old_xp = user.xp

        # Add XP
        user.xp += xp_amount

        # Check for level up
        new_level = self._calculate_level(user.xp)
        leveled_up = new_level > old_level

        if leveled_up:
            user.level = new_level

        self.db.commit()
        self.db.refresh(user)

        return {
            'xp_gained': xp_amount,
            'total_xp': user.xp,
            'old_level': old_level,
            'new_level': user.level,
            'leveled_up': leveled_up,
            'reason': reason,
            'next_level_xp': self._get_xp_for_next_level(user.level),
            'progress_to_next_level': self._get_progress_to_next_level(user.xp, user.level)
        }

    def _calculate_level(self, total_xp: int) -> int:
        """Calculate user level based on total XP"""
        level = 1
        for lvl, xp_required in sorted(self.LEVEL_THRESHOLDS.items()):
            if total_xp >= xp_required:
                level = lvl
            else:
                break
        return level

    def _get_xp_for_next_level(self, current_level: int) -> int:
        """Get XP required for next level"""
        next_level = current_level + 1
        if next_level in self.LEVEL_THRESHOLDS:
            return self.LEVEL_THRESHOLDS[next_level]

        # If beyond defined thresholds, use formula
        # XP = 100 * level^1.5 + 50 * level
        return int(100 * (next_level ** 1.5) + 50 * next_level)

    def _get_progress_to_next_level(self, total_xp: int, current_level: int) -> float:
        """Get progress percentage to next level (0-100)"""
        current_level_xp = self.LEVEL_THRESHOLDS.get(current_level, 0)
        next_level_xp = self._get_xp_for_next_level(current_level)

        xp_in_current_level = total_xp - current_level_xp
        xp_needed_for_next = next_level_xp - current_level_xp

        if xp_needed_for_next == 0:
            return 100.0

        progress = (xp_in_current_level / xp_needed_for_next) * 100
        return min(100.0, max(0.0, progress))

    def get_user_level_info(self, user_id: int) -> Dict:
        """Get comprehensive level information for user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        # Initialize if not set
        if not hasattr(user, 'xp') or user.xp is None:
            user.xp = 0
        if not hasattr(user, 'level') or user.level is None:
            user.level = 1

        current_level_xp = self.LEVEL_THRESHOLDS.get(user.level, 0)
        next_level_xp = self._get_xp_for_next_level(user.level)
        xp_in_current_level = user.xp - current_level_xp
        xp_needed_for_next = next_level_xp - current_level_xp

        return {
            'level': user.level,
            'total_xp': user.xp,
            'current_level_xp': current_level_xp,
            'xp_in_current_level': xp_in_current_level,
            'next_level_xp': next_level_xp,
            'xp_needed_for_next_level': xp_needed_for_next,
            'progress_to_next_level': self._get_progress_to_next_level(user.xp, user.level),
            'rank': self._get_rank_name(user.level),
            'perks': self._get_level_perks(user.level)
        }

    def _get_rank_name(self, level: int) -> str:
        """Get rank name based on level"""
        if level >= 50:
            return 'Master'
        elif level >= 40:
            return 'Expert'
        elif level >= 30:
            return 'Professional'
        elif level >= 20:
            return 'Advanced'
        elif level >= 10:
            return 'Intermediate'
        elif level >= 5:
            return 'Apprentice'
        else:
            return 'Novice'

    def _get_level_perks(self, level: int) -> List[str]:
        """Get perks unlocked at this level"""
        perks = []

        if level >= 5:
            perks.append("Custom categories unlocked")
        if level >= 10:
            perks.append("Advanced reports unlocked")
        if level >= 15:
            perks.append("Forecasting unlocked")
        if level >= 20:
            perks.append("Scenario planning unlocked")
        if level >= 25:
            perks.append("Custom challenges unlocked")
        if level >= 30:
            perks.append("Export to PDF unlocked")
        if level >= 40:
            perks.append("Priority support")
        if level >= 50:
            perks.append("VIP features unlocked")

        return perks

    # ===== CONVENIENCE METHODS FOR AWARDING XP =====

    def award_entry_xp(self, user_id: int) -> Dict:
        """Award XP for logging an entry"""
        return self.add_xp(user_id, self.XP_REWARDS['entry_logged'], "Entry logged")

    def award_goal_created_xp(self, user_id: int) -> Dict:
        """Award XP for creating a goal"""
        return self.add_xp(user_id, self.XP_REWARDS['goal_created'], "Goal created")

    def award_goal_completed_xp(self, user_id: int) -> Dict:
        """Award XP for completing a goal"""
        return self.add_xp(user_id, self.XP_REWARDS['goal_completed'], "Goal completed")

    def award_achievement_xp(self, user_id: int) -> Dict:
        """Award XP for unlocking an achievement"""
        return self.add_xp(user_id, self.XP_REWARDS['achievement_unlocked'], "Achievement unlocked")

    def award_badge_xp(self, user_id: int) -> Dict:
        """Award XP for earning a badge"""
        return self.add_xp(user_id, self.XP_REWARDS['badge_earned'], "Badge earned")

    def award_challenge_completed_xp(self, user_id: int) -> Dict:
        """Award XP for completing a challenge"""
        return self.add_xp(user_id, self.XP_REWARDS['challenge_completed'], "Challenge completed")

    def award_streak_milestone_xp(self, user_id: int, days: int) -> Dict:
        """Award XP for reaching a streak milestone"""
        return self.add_xp(
            user_id,
            self.XP_REWARDS['daily_streak_milestone'],
            f"{days}-day streak milestone"
        )

    # ===== LEADERBOARD SUPPORT =====

    def get_top_users_by_xp(self, limit: int = 10) -> List[Dict]:
        """Get top users by total XP"""
        users = self.db.query(User).filter(
            User.xp.isnot(None)
        ).order_by(User.xp.desc()).limit(limit).all()

        return [
            {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'level': user.level or 1,
                'total_xp': user.xp or 0,
                'rank': self._get_rank_name(user.level or 1)
            }
            for user in users
        ]

    def get_top_users_by_level(self, limit: int = 10) -> List[Dict]:
        """Get top users by level"""
        users = self.db.query(User).filter(
            User.level.isnot(None)
        ).order_by(User.level.desc(), User.xp.desc()).limit(limit).all()

        return [
            {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'level': user.level or 1,
                'total_xp': user.xp or 0,
                'rank': self._get_rank_name(user.level or 1)
            }
            for user in users
        ]

    def get_user_rank_position(self, user_id: int) -> Dict:
        """Get user's position in global rankings"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        # Count users with higher XP
        higher_xp_count = self.db.query(User).filter(
            User.xp > (user.xp or 0)
        ).count()

        position = higher_xp_count + 1
        total_users = self.db.query(User).count()

        return {
            'position': position,
            'total_users': total_users,
            'percentile': round((1 - (position / total_users)) * 100, 1) if total_users > 0 else 0,
            'level': user.level or 1,
            'total_xp': user.xp or 0
        }

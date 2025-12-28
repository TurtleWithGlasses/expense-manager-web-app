"""
Badge Service - Phase 1.1

Handles badge awarding, checking, and management.
Badges are earned through achievements or special milestones.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import List, Dict, Optional
import logging

from app.models.achievement import Badge, UserBadge, Achievement, UserAchievement
from app.models.user import User

logger = logging.getLogger(__name__)


class BadgeService:
    """Service for managing user badges"""

    @staticmethod
    def check_and_award_badges(db: Session, user_id: int) -> List[UserBadge]:
        """
        Check all badge requirements and award newly earned badges

        Called after:
        - Achievement unlocks
        - Milestone completions
        - Special events

        Returns list of newly awarded badges
        """
        # Get all active badges
        badges = db.query(Badge).filter(
            Badge.is_active == True
        ).all()

        newly_awarded = []

        for badge in badges:
            # Skip if user already has this badge
            existing = db.query(UserBadge).filter(
                UserBadge.user_id == user_id,
                UserBadge.badge_id == badge.id
            ).first()

            if existing:
                continue

            # Check if user meets badge requirements
            if BadgeService._check_badge_requirements(db, user_id, badge.requirement_type, badge.requirement_data):
                # Award badge!
                user_badge = UserBadge(
                    user_id=user_id,
                    badge_id=badge.id,
                    is_equipped=False,
                    is_new=True,
                    earned_at=datetime.utcnow()
                )
                db.add(user_badge)
                newly_awarded.append(user_badge)

                logger.info(f"User {user_id} earned badge: {badge.code}")

        if newly_awarded:
            db.commit()

        return newly_awarded

    @staticmethod
    def _check_badge_requirements(db: Session, user_id: int, requirement_type: str, requirement_data: Dict) -> bool:
        """
        Check if user meets badge requirements

        Requirement types:
        - achievement: Unlock specific achievement(s)
        - points: Earn X achievement points
        - streak: Maintain X day streak
        - tier_collection: Unlock all achievements in a tier
        - category_collection: Unlock all achievements in a category
        - special: Special event or milestone
        """
        if requirement_type == 'achievement':
            return BadgeService._check_achievement_requirement(db, user_id, requirement_data)

        elif requirement_type == 'points':
            return BadgeService._check_points_requirement(db, user_id, requirement_data)

        elif requirement_type == 'streak':
            return BadgeService._check_streak_requirement(db, user_id, requirement_data)

        elif requirement_type == 'tier_collection':
            return BadgeService._check_tier_collection(db, user_id, requirement_data)

        elif requirement_type == 'category_collection':
            return BadgeService._check_category_collection(db, user_id, requirement_data)

        elif requirement_type == 'special':
            return BadgeService._check_special_requirement(db, user_id, requirement_data)

        else:
            logger.warning(f"Unknown badge requirement type: {requirement_type}")
            return False

    @staticmethod
    def _check_achievement_requirement(db: Session, user_id: int, requirement_data: Dict) -> bool:
        """
        Check if user has unlocked required achievement(s)

        requirement_data: {'achievement_codes': ['first_entry', '7_day_streak']}
        or: {'achievement_id': 5}
        """
        achievement_codes = requirement_data.get('achievement_codes', [])
        achievement_id = requirement_data.get('achievement_id')

        if achievement_id:
            # Check single achievement by ID
            user_achievement = db.query(UserAchievement).join(Achievement).filter(
                UserAchievement.user_id == user_id,
                Achievement.id == achievement_id
            ).first()
            return user_achievement is not None

        elif achievement_codes:
            # Check multiple achievements by code
            for code in achievement_codes:
                achievement = db.query(Achievement).filter(Achievement.code == code).first()
                if not achievement:
                    return False

                user_achievement = db.query(UserAchievement).filter(
                    UserAchievement.user_id == user_id,
                    UserAchievement.achievement_id == achievement.id
                ).first()

                if not user_achievement:
                    return False

            return True

        return False

    @staticmethod
    def _check_points_requirement(db: Session, user_id: int, requirement_data: Dict) -> bool:
        """
        Check if user has earned enough achievement points

        requirement_data: {'threshold': 1000}
        """
        threshold = requirement_data.get('threshold', 0)

        # Calculate total points
        total_points = db.query(func.sum(Achievement.points)).join(
            UserAchievement,
            Achievement.id == UserAchievement.achievement_id
        ).filter(
            UserAchievement.user_id == user_id
        ).scalar() or 0

        return total_points >= threshold

    @staticmethod
    def _check_streak_requirement(db: Session, user_id: int, requirement_data: Dict) -> bool:
        """
        Check if user has a streak-related achievement

        requirement_data: {'days': 30}
        """
        days = requirement_data.get('days', 0)

        # Check if user has unlocked the corresponding streak achievement
        # This assumes streak achievements follow the pattern: 'streak_{days}'
        achievement_code = f'streak_{days}'

        achievement = db.query(Achievement).filter(
            Achievement.code == achievement_code
        ).first()

        if not achievement:
            return False

        user_achievement = db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_id == achievement.id
        ).first()

        return user_achievement is not None

    @staticmethod
    def _check_tier_collection(db: Session, user_id: int, requirement_data: Dict) -> bool:
        """
        Check if user has unlocked all achievements in a tier

        requirement_data: {'tier': 'bronze'}
        """
        tier = requirement_data.get('tier')

        # Get all achievements in this tier
        tier_achievements = db.query(Achievement).filter(
            Achievement.tier == tier,
            Achievement.is_active == True,
            Achievement.is_secret == False  # Don't require secret achievements
        ).all()

        if not tier_achievements:
            return False

        # Check if user has unlocked all of them
        for achievement in tier_achievements:
            user_achievement = db.query(UserAchievement).filter(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_id == achievement.id
            ).first()

            if not user_achievement:
                return False

        return True

    @staticmethod
    def _check_category_collection(db: Session, user_id: int, requirement_data: Dict) -> bool:
        """
        Check if user has unlocked all achievements in a category

        requirement_data: {'category': 'tracking'}
        """
        category = requirement_data.get('category')

        # Get all achievements in this category
        category_achievements = db.query(Achievement).filter(
            Achievement.category == category,
            Achievement.is_active == True,
            Achievement.is_secret == False  # Don't require secret achievements
        ).all()

        if not category_achievements:
            return False

        # Check if user has unlocked all of them
        for achievement in category_achievements:
            user_achievement = db.query(UserAchievement).filter(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_id == achievement.id
            ).first()

            if not user_achievement:
                return False

        return True

    @staticmethod
    def _check_special_requirement(db: Session, user_id: int, requirement_data: Dict) -> bool:
        """
        Check special requirements (custom logic)

        requirement_data: {'type': 'early_adopter', 'signup_before': '2025-01-01'}
        or: {'type': 'perfect_month', 'all_goals_met': True}
        """
        special_type = requirement_data.get('type')

        if special_type == 'early_adopter':
            # Check if user signed up before a certain date
            signup_before = requirement_data.get('signup_before')
            if signup_before:
                user = db.query(User).filter(User.id == user_id).first()
                if user and user.created_at:
                    return user.created_at <= datetime.fromisoformat(signup_before)

        elif special_type == 'perfect_month':
            # Check if user met all goals this month
            # This would require integration with the goals service
            # For now, return False as placeholder
            return False

        elif special_type == 'achievement_count':
            # Check if user has unlocked X achievements
            count_threshold = requirement_data.get('count', 0)
            user_achievement_count = db.query(func.count(UserAchievement.id)).filter(
                UserAchievement.user_id == user_id
            ).scalar() or 0

            return user_achievement_count >= count_threshold

        return False

    @staticmethod
    def equip_badge(db: Session, user_id: int, badge_id: int) -> Optional[UserBadge]:
        """
        Equip a badge for display on user profile

        Only one badge can be equipped at a time
        """
        # Verify user has this badge
        user_badge = db.query(UserBadge).filter(
            UserBadge.user_id == user_id,
            UserBadge.badge_id == badge_id
        ).first()

        if not user_badge:
            return None

        # Unequip all other badges
        db.query(UserBadge).filter(
            UserBadge.user_id == user_id,
            UserBadge.is_equipped == True
        ).update({'is_equipped': False, 'equipped_at': None})

        # Equip this badge
        user_badge.is_equipped = True
        user_badge.equipped_at = datetime.utcnow()

        db.commit()

        return user_badge

    @staticmethod
    def unequip_badge(db: Session, user_id: int, badge_id: int) -> bool:
        """
        Unequip a badge
        """
        user_badge = db.query(UserBadge).filter(
            UserBadge.user_id == user_id,
            UserBadge.badge_id == badge_id
        ).first()

        if not user_badge:
            return False

        user_badge.is_equipped = False
        user_badge.equipped_at = None

        db.commit()

        return True

    @staticmethod
    def get_user_badges(db: Session, user_id: int, include_locked: bool = False) -> List[Dict]:
        """
        Get all badges for a user

        Returns badges with earned/locked status
        """
        # Get all badges
        badges = db.query(Badge).filter(
            Badge.is_active == True
        ).all()

        # Get user's earned badges
        user_badges = db.query(UserBadge).filter(
            UserBadge.user_id == user_id
        ).all()

        earned_ids = {ub.badge_id for ub in user_badges}
        user_badge_map = {ub.badge_id: ub for ub in user_badges}

        result = []

        for badge in badges:
            badge_data = badge.to_dict()
            badge_data['is_earned'] = badge.id in earned_ids

            if badge.id in earned_ids:
                # Add user badge data
                ub = user_badge_map[badge.id]
                badge_data['is_equipped'] = ub.is_equipped
                badge_data['is_new'] = ub.is_new
                badge_data['earned_at'] = ub.earned_at.isoformat() if ub.earned_at else None
            else:
                # Locked badge
                if not include_locked:
                    continue
                badge_data['is_equipped'] = False
                badge_data['is_new'] = False
                badge_data['earned_at'] = None

            result.append(badge_data)

        return result

    @staticmethod
    def get_equipped_badge(db: Session, user_id: int) -> Optional[Dict]:
        """
        Get currently equipped badge for a user
        """
        user_badge = db.query(UserBadge).filter(
            UserBadge.user_id == user_id,
            UserBadge.is_equipped == True
        ).first()

        if not user_badge:
            return None

        return user_badge.to_dict()

    @staticmethod
    def mark_badges_viewed(db: Session, user_id: int) -> int:
        """
        Mark all new badges as viewed

        Returns count of badges marked
        """
        count = db.query(UserBadge).filter(
            UserBadge.user_id == user_id,
            UserBadge.is_new == True
        ).update({'is_new': False})

        db.commit()
        return count

    @staticmethod
    def get_badge_stats(db: Session, user_id: int) -> Dict:
        """
        Get badge statistics for a user
        """
        # Get user's earned badges
        user_badges = db.query(UserBadge).join(Badge).filter(
            UserBadge.user_id == user_id
        ).all()

        # Count by rarity
        rarity_counts = {}
        for ub in user_badges:
            rarity = ub.badge.rarity
            rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1

        # Total available badges
        total_badges = db.query(func.count(Badge.id)).filter(
            Badge.is_active == True
        ).scalar()

        return {
            'earned_count': len(user_badges),
            'total_count': total_badges,
            'completion_percentage': int((len(user_badges) / total_badges * 100)) if total_badges > 0 else 0,
            'rarity_counts': rarity_counts,
            'recent_badges': [ub.to_dict() for ub in user_badges[-5:]]  # Last 5
        }

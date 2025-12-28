"""
Achievement Models - Phase 1.1

Persistent achievement and badge system for gamification.
Tracks user progress and unlocked achievements.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, DECIMAL, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class Achievement(Base):
    """
    Achievement Definition

    Represents an achievement that users can unlock.
    Examples: "First Entry", "7-Day Streak", "Budget Master"
    """
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False, index=True)  # e.g., 'first_entry'
    name = Column(String(200), nullable=False)                           # 'First Step'
    description = Column(Text)                                           # 'Log your first transaction'

    # Classification
    category = Column(String(50))                    # 'tracking', 'saving', 'spending', 'goal'
    tier = Column(String(20))                        # 'bronze', 'silver', 'gold', 'platinum'

    # Visual
    icon_name = Column(String(100))                  # Icon identifier for UI
    color_hex = Column(String(7))                    # Badge color (e.g., '#FFD700' for gold)

    # Rewards
    points = Column(Integer, default=0)              # Points awarded when unlocked

    # Unlock requirements (stored as JSON)
    # Examples:
    # {'type': 'entry_count', 'threshold': 1}
    # {'type': 'daily_streak', 'days': 7}
    # {'type': 'savings_rate', 'percentage': 20}
    unlock_criteria = Column(JSON, nullable=False)

    # Metadata
    is_active = Column(Boolean, default=True)        # Can be earned
    is_secret = Column(Boolean, default=False)       # Hidden until unlocked
    sort_order = Column(Integer, default=0)          # Display order
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user_achievements = relationship("UserAchievement", back_populates="achievement", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Achievement(code='{self.code}', name='{self.name}', tier='{self.tier}')>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'tier': self.tier,
            'icon_name': self.icon_name,
            'color_hex': self.color_hex,
            'points': self.points,
            'unlock_criteria': self.unlock_criteria,
            'is_secret': self.is_secret,
            'sort_order': self.sort_order
        }


class UserAchievement(Base):
    """
    User's Earned Achievement

    Tracks which achievements a user has unlocked and their progress.
    """
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    achievement_id = Column(Integer, ForeignKey('achievements.id', ondelete='CASCADE'), nullable=False)

    # Progress tracking (stored as JSON)
    # Examples:
    # {'current': 5, 'required': 7} - for 7-day streak
    # {'amount': 1500, 'threshold': 2000} - for savings goal
    progress_data = Column(JSON)

    # Status
    is_completed = Column(Boolean, default=True)     # True when unlocked
    is_new = Column(Boolean, default=True)           # Show "NEW" badge in UI

    # Timestamps
    earned_at = Column(DateTime, default=datetime.utcnow, index=True)
    viewed_at = Column(DateTime)                     # When user viewed the achievement

    # Relationships
    achievement = relationship("Achievement", back_populates="user_achievements")
    user = relationship("User", back_populates="achievements")

    def __repr__(self):
        return f"<UserAchievement(user_id={self.user_id}, achievement_id={self.achievement_id})>"

    def to_dict(self, include_achievement=True):
        """Convert to dictionary for API responses"""
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'achievement_id': self.achievement_id,
            'progress_data': self.progress_data,
            'is_completed': self.is_completed,
            'is_new': self.is_new,
            'earned_at': self.earned_at.isoformat() if self.earned_at else None,
            'viewed_at': self.viewed_at.isoformat() if self.viewed_at else None
        }

        if include_achievement and self.achievement:
            result['achievement'] = self.achievement.to_dict()

        return result


class Badge(Base):
    """
    Special Badge

    Visual badges that can be earned through achievements or special events.
    Displayed on user profile.
    """
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Visual
    icon_url = Column(String(500))                   # Badge image URL
    color_hex = Column(String(7))                    # Badge color
    rarity = Column(String(20))                      # 'common', 'rare', 'epic', 'legendary'

    # Requirements
    requirement_type = Column(String(50))            # 'achievement', 'points', 'streak', 'special'
    requirement_data = Column(JSON)                  # Requirements definition

    # Metadata
    is_active = Column(Boolean, default=True)
    is_displayable = Column(Boolean, default=True)   # Can be shown on profile
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user_badges = relationship("UserBadge", back_populates="badge", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Badge(code='{self.code}', name='{self.name}', rarity='{self.rarity}')>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'icon_url': self.icon_url,
            'color_hex': self.color_hex,
            'rarity': self.rarity,
            'requirement_type': self.requirement_type,
            'requirement_data': self.requirement_data,
            'is_displayable': self.is_displayable
        }


class UserBadge(Base):
    """
    User's Earned Badge

    Tracks which badges a user has earned.
    """
    __tablename__ = "user_badges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    badge_id = Column(Integer, ForeignKey('badges.id', ondelete='CASCADE'), nullable=False)

    # Status
    is_equipped = Column(Boolean, default=False)     # Currently displayed on profile
    is_new = Column(Boolean, default=True)

    # Timestamps
    earned_at = Column(DateTime, default=datetime.utcnow, index=True)
    equipped_at = Column(DateTime)

    # Relationships
    badge = relationship("Badge", back_populates="user_badges")
    user = relationship("User", back_populates="badges")

    def __repr__(self):
        return f"<UserBadge(user_id={self.user_id}, badge_id={self.badge_id})>"

    def to_dict(self, include_badge=True):
        """Convert to dictionary for API responses"""
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'badge_id': self.badge_id,
            'is_equipped': self.is_equipped,
            'is_new': self.is_new,
            'earned_at': self.earned_at.isoformat() if self.earned_at else None,
            'equipped_at': self.equipped_at.isoformat() if self.equipped_at else None
        }

        if include_badge and self.badge:
            result['badge'] = self.badge.to_dict()

        return result

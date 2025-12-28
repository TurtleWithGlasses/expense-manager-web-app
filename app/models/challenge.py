"""Challenge Model - Phase 3: Full Gamification"""
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Boolean, Text, Numeric, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
import enum

from app.db.base import Base


class ChallengeType(str, enum.Enum):
    """Types of challenges"""
    WEEKLY = "weekly"  # Resets every week
    MONTHLY = "monthly"  # Resets every month
    ONE_TIME = "one_time"  # Complete once
    SEASONAL = "seasonal"  # Special event challenges


class ChallengeStatus(str, enum.Enum):
    """Challenge status"""
    ACTIVE = "active"  # Currently available
    UPCOMING = "upcoming"  # Not yet started
    ENDED = "ended"  # Challenge period ended
    ARCHIVED = "archived"  # Hidden from users


class UserChallengeStatus(str, enum.Enum):
    """User's participation status in a challenge"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Challenge(Base):
    """Challenges for users to complete for rewards"""
    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Challenge details
    code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    challenge_type: Mapped[str] = mapped_column(String(20), default=ChallengeType.WEEKLY)

    # Completion criteria (JSON format for flexibility)
    # Example: {"type": "no_spend_days", "target": 7, "period": "week"}
    # Example: {"type": "save_amount", "target": 500}
    completion_criteria: Mapped[dict] = mapped_column(JSON)

    # Rewards
    xp_reward: Mapped[int] = mapped_column(Integer, default=0)
    points_reward: Mapped[int] = mapped_column(Integer, default=0)
    badge_reward_id: Mapped[int | None] = mapped_column(
        ForeignKey("badges.id", ondelete="SET NULL"),
        nullable=True
    )

    # Schedule
    start_date: Mapped[datetime] = mapped_column(DateTime)
    end_date: Mapped[datetime] = mapped_column(DateTime)

    # Status and metadata
    status: Mapped[str] = mapped_column(String(20), default=ChallengeStatus.ACTIVE)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    difficulty_level: Mapped[int] = mapped_column(Integer, default=1)  # 1-5
    participant_count: Mapped[int] = mapped_column(Integer, default=0)
    completion_count: Mapped[int] = mapped_column(Integer, default=0)

    # Icon and visual
    icon_name: Mapped[str] = mapped_column(String(50), default="trophy")
    color_hex: Mapped[str] = mapped_column(String(7), default="#3b82f6")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    badge_reward = relationship("Badge", foreign_keys=[badge_reward_id])
    user_challenges = relationship("UserChallenge", back_populates="challenge", cascade="all, delete-orphan")


class UserChallenge(Base):
    """Track user participation in challenges"""
    __tablename__ = "user_challenges"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenges.id", ondelete="CASCADE"), index=True)

    # Progress tracking
    status: Mapped[str] = mapped_column(String(20), default=UserChallengeStatus.NOT_STARTED)
    current_progress: Mapped[float] = mapped_column(Numeric(precision=10, scale=2), default=0)
    target_progress: Mapped[float] = mapped_column(Numeric(precision=10, scale=2))
    progress_percentage: Mapped[float] = mapped_column(Numeric(precision=5, scale=2), default=0)

    # Additional progress data (JSON for flexibility)
    # Example: {"days_completed": 5, "last_update": "2025-12-28"}
    progress_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Timestamps
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_progress_update: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Rewards claimed
    rewards_claimed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="user_challenges")
    challenge = relationship("Challenge", back_populates="user_challenges")

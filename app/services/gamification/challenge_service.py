"""Challenge Service - Phase 3: Full Gamification

Handles challenge creation, participation, progress tracking, and completion.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.challenge import Challenge, UserChallenge, ChallengeStatus, UserChallengeStatus, ChallengeType
from app.models.entry import Entry
from app.models.financial_goal import FinancialGoal, GoalStatus


class ChallengeService:
    """Service for managing challenges and user participation"""

    def __init__(self, db: Session):
        self.db = db

    # ===== CHALLENGE CRUD =====

    def get_active_challenges(self) -> List[Challenge]:
        """Get all currently active challenges"""
        now = datetime.utcnow()
        return self.db.query(Challenge).filter(
            Challenge.status == ChallengeStatus.ACTIVE,
            Challenge.start_date <= now,
            Challenge.end_date >= now
        ).order_by(Challenge.is_featured.desc(), Challenge.created_at.desc()).all()

    def get_challenge(self, challenge_id: int) -> Optional[Challenge]:
        """Get a specific challenge"""
        return self.db.query(Challenge).filter(Challenge.id == challenge_id).first()

    def get_user_challenges(
        self,
        user_id: int,
        status: Optional[UserChallengeStatus] = None,
        include_completed: bool = True
    ) -> List[UserChallenge]:
        """Get challenges user is participating in"""
        query = self.db.query(UserChallenge).filter(UserChallenge.user_id == user_id)

        if status:
            query = query.filter(UserChallenge.status == status)
        elif not include_completed:
            query = query.filter(UserChallenge.status != UserChallengeStatus.COMPLETED)

        return query.order_by(UserChallenge.joined_at.desc()).all()

    def join_challenge(self, user_id: int, challenge_id: int) -> UserChallenge:
        """Join a challenge"""
        # Check if already joined
        existing = self.db.query(UserChallenge).filter(
            UserChallenge.user_id == user_id,
            UserChallenge.challenge_id == challenge_id
        ).first()

        if existing:
            return existing

        challenge = self.get_challenge(challenge_id)
        if not challenge:
            raise ValueError("Challenge not found")

        # Extract target from completion criteria
        target = challenge.completion_criteria.get('target', 100)

        user_challenge = UserChallenge(
            user_id=user_id,
            challenge_id=challenge_id,
            status=UserChallengeStatus.IN_PROGRESS,
            current_progress=0,
            target_progress=target,
            progress_percentage=0,
            progress_data={}
        )

        self.db.add(user_challenge)

        # Update participant count
        challenge.participant_count += 1

        self.db.commit()
        self.db.refresh(user_challenge)

        return user_challenge

    def update_challenge_progress(
        self,
        user_id: int,
        challenge_id: int,
        new_progress: float
    ) -> UserChallenge:
        """Update progress on a challenge"""
        user_challenge = self.db.query(UserChallenge).filter(
            UserChallenge.user_id == user_id,
            UserChallenge.challenge_id == challenge_id
        ).first()

        if not user_challenge:
            raise ValueError("User is not participating in this challenge")

        user_challenge.current_progress = new_progress
        user_challenge.progress_percentage = min(
            (new_progress / user_challenge.target_progress * 100),
            100
        )
        user_challenge.last_progress_update = datetime.utcnow()

        # Check for completion
        if user_challenge.current_progress >= user_challenge.target_progress:
            if user_challenge.status != UserChallengeStatus.COMPLETED:
                user_challenge.status = UserChallengeStatus.COMPLETED
                user_challenge.completed_at = datetime.utcnow()

                # Update completion count
                challenge = user_challenge.challenge
                challenge.completion_count += 1

        self.db.commit()
        self.db.refresh(user_challenge)

        return user_challenge

    def claim_challenge_rewards(self, user_id: int, challenge_id: int) -> Dict:
        """Claim rewards for completing a challenge"""
        user_challenge = self.db.query(UserChallenge).filter(
            UserChallenge.user_id == user_id,
            UserChallenge.challenge_id == challenge_id,
            UserChallenge.status == UserChallengeStatus.COMPLETED
        ).first()

        if not user_challenge:
            raise ValueError("Challenge not completed or not found")

        if user_challenge.rewards_claimed:
            raise ValueError("Rewards already claimed")

        challenge = user_challenge.challenge

        # Mark as claimed
        user_challenge.rewards_claimed = True
        self.db.commit()

        return {
            'xp_reward': challenge.xp_reward,
            'points_reward': challenge.points_reward,
            'badge_reward_id': challenge.badge_reward_id
        }

    # ===== AUTOMATIC PROGRESS TRACKING =====

    def check_and_update_all_user_challenges(self, user_id: int) -> List[UserChallenge]:
        """
        Check and update progress for all of user's active challenges.
        Called after user actions (entries, goals, etc.)
        """
        active_challenges = self.get_user_challenges(
            user_id,
            status=UserChallengeStatus.IN_PROGRESS
        )

        updated = []
        for user_challenge in active_challenges:
            try:
                progress = self._calculate_challenge_progress(
                    user_id,
                    user_challenge.challenge
                )
                if progress != user_challenge.current_progress:
                    self.update_challenge_progress(
                        user_id,
                        user_challenge.challenge_id,
                        progress
                    )
                    updated.append(user_challenge)
            except Exception as e:
                print(f"Error updating challenge {user_challenge.challenge_id}: {e}")
                continue

        return updated

    def _calculate_challenge_progress(self, user_id: int, challenge: Challenge) -> float:
        """Calculate current progress for a challenge based on criteria"""
        criteria = challenge.completion_criteria
        criteria_type = criteria.get('type')

        # Define date range for the challenge
        start_date = challenge.start_date
        end_date = min(challenge.end_date, datetime.utcnow())

        if criteria_type == 'no_spend_days':
            # Count days with no expenses
            target = criteria.get('target', 7)
            return self._count_no_spend_days(user_id, start_date, end_date)

        elif criteria_type == 'save_amount':
            # Calculate total income minus expenses
            target = criteria.get('target', 500)
            return self._calculate_savings(user_id, start_date, end_date)

        elif criteria_type == 'entry_count':
            # Count total entries
            return self._count_entries(user_id, start_date, end_date)

        elif criteria_type == 'spend_under_budget':
            # Check if spending is under a certain amount
            target = criteria.get('target', 1000)
            total_spending = self._calculate_total_spending(user_id, start_date, end_date)
            return max(0, target - total_spending)  # Remaining budget

        elif criteria_type == 'goal_completion':
            # Count completed goals
            return self._count_completed_goals(user_id, start_date, end_date)

        elif criteria_type == 'daily_streak':
            # Track consecutive days with entries
            return self._calculate_current_streak(user_id, start_date, end_date)

        else:
            return 0

    # ===== HELPER METHODS =====

    def _count_no_spend_days(self, user_id: int, start_date: datetime, end_date: datetime) -> float:
        """Count days with no expense entries"""
        # Get all dates with expenses
        dates_with_expenses = set(
            row[0] for row in self.db.query(func.date(Entry.date)).filter(
                Entry.user_id == user_id,
                Entry.type == 'expense',
                Entry.date >= start_date,
                Entry.date <= end_date
            ).distinct().all()
        )

        # Count total days in range
        total_days = (end_date.date() - start_date.date()).days + 1

        # Days without expenses
        return total_days - len(dates_with_expenses)

    def _calculate_savings(self, user_id: int, start_date: datetime, end_date: datetime) -> float:
        """Calculate total savings (income - expenses)"""
        income = self.db.query(func.sum(Entry.amount)).filter(
            Entry.user_id == user_id,
            Entry.type == 'income',
            Entry.date >= start_date,
            Entry.date <= end_date
        ).scalar() or 0

        expenses = self.db.query(func.sum(Entry.amount)).filter(
            Entry.user_id == user_id,
            Entry.type == 'expense',
            Entry.date >= start_date,
            Entry.date <= end_date
        ).scalar() or 0

        return float(income) - float(expenses)

    def _count_entries(self, user_id: int, start_date: datetime, end_date: datetime) -> float:
        """Count total entries in date range"""
        count = self.db.query(func.count(Entry.id)).filter(
            Entry.user_id == user_id,
            Entry.date >= start_date,
            Entry.date <= end_date
        ).scalar() or 0

        return float(count)

    def _calculate_total_spending(self, user_id: int, start_date: datetime, end_date: datetime) -> float:
        """Calculate total spending"""
        total = self.db.query(func.sum(Entry.amount)).filter(
            Entry.user_id == user_id,
            Entry.type == 'expense',
            Entry.date >= start_date,
            Entry.date <= end_date
        ).scalar() or 0

        return float(total)

    def _count_completed_goals(self, user_id: int, start_date: datetime, end_date: datetime) -> float:
        """Count goals completed in date range"""
        count = self.db.query(func.count(FinancialGoal.id)).filter(
            FinancialGoal.user_id == user_id,
            FinancialGoal.status == GoalStatus.COMPLETED,
            FinancialGoal.completed_date >= start_date,
            FinancialGoal.completed_date <= end_date
        ).scalar() or 0

        return float(count)

    def _calculate_current_streak(self, user_id: int, start_date: datetime, end_date: datetime) -> float:
        """Calculate current consecutive day streak"""
        # Get all dates with entries in range
        dates_with_entries = [
            row[0] for row in self.db.query(func.date(Entry.date)).filter(
                Entry.user_id == user_id,
                Entry.date >= start_date,
                Entry.date <= end_date
            ).distinct().order_by(func.date(Entry.date).desc()).all()
        ]

        if not dates_with_entries:
            return 0

        # Count consecutive days from most recent
        streak = 1
        current_date = dates_with_entries[0]

        for i in range(1, len(dates_with_entries)):
            next_date = dates_with_entries[i]
            # Check if dates are consecutive
            if (current_date - next_date).days == 1:
                streak += 1
                current_date = next_date
            else:
                break

        return float(streak)

    # ===== STATISTICS =====

    def get_user_challenge_stats(self, user_id: int) -> Dict:
        """Get statistics about user's challenge participation"""
        total_joined = self.db.query(func.count(UserChallenge.id)).filter(
            UserChallenge.user_id == user_id
        ).scalar() or 0

        completed = self.db.query(func.count(UserChallenge.id)).filter(
            UserChallenge.user_id == user_id,
            UserChallenge.status == UserChallengeStatus.COMPLETED
        ).scalar() or 0

        in_progress = self.db.query(func.count(UserChallenge.id)).filter(
            UserChallenge.user_id == user_id,
            UserChallenge.status == UserChallengeStatus.IN_PROGRESS
        ).scalar() or 0

        return {
            'total_joined': total_joined,
            'completed': completed,
            'in_progress': in_progress,
            'completion_rate': (completed / total_joined * 100) if total_joined > 0 else 0
        }

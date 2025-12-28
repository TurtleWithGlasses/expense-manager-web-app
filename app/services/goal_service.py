"""Goal Service - Phase 17: Goal Setting & Tracking"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.financial_goal import FinancialGoal, GoalProgressLog, GoalType, GoalStatus
from app.models.entry import Entry
from app.models.category import Category


class GoalService:
    """Service for managing financial goals and tracking progress"""

    def __init__(self, db: Session):
        self.db = db

    def create_goal(
        self,
        user_id: int,
        name: str,
        target_amount: float,
        goal_type: str = GoalType.SAVINGS,
        description: str = None,
        category_id: int = None,
        target_date: datetime = None,
        currency_code: str = "USD",
        notify_on_milestone: bool = True,
        milestone_percentage: int = 25
    ) -> FinancialGoal:
        """Create a new financial goal"""
        goal = FinancialGoal(
            user_id=user_id,
            name=name,
            description=description,
            goal_type=goal_type,
            target_amount=target_amount,
            current_amount=0,
            currency_code=currency_code,
            category_id=category_id,
            target_date=target_date,
            notify_on_milestone=notify_on_milestone,
            milestone_percentage=milestone_percentage,
            status=GoalStatus.ACTIVE
        )

        self.db.add(goal)
        self.db.commit()
        self.db.refresh(goal)

        # Log initial creation
        self._log_progress(goal.id, 0, 0, 0, "Goal created", is_manual=False)

        return goal

    def get_user_goals(
        self,
        user_id: int,
        status: GoalStatus = None,
        include_completed: bool = True
    ) -> List[FinancialGoal]:
        """Get all goals for a user"""
        query = self.db.query(FinancialGoal).filter(FinancialGoal.user_id == user_id)

        if status:
            query = query.filter(FinancialGoal.status == status)
        elif not include_completed:
            query = query.filter(FinancialGoal.status != GoalStatus.COMPLETED)

        return query.order_by(FinancialGoal.created_at.desc()).all()

    def get_goal(self, goal_id: int, user_id: int) -> Optional[FinancialGoal]:
        """Get a specific goal"""
        return self.db.query(FinancialGoal).filter(
            FinancialGoal.id == goal_id,
            FinancialGoal.user_id == user_id
        ).first()

    def update_goal(
        self,
        goal_id: int,
        user_id: int,
        **updates
    ) -> Optional[FinancialGoal]:
        """Update a goal's details"""
        goal = self.get_goal(goal_id, user_id)
        if not goal:
            return None

        # Track if amount changed
        amount_changed = 'current_amount' in updates and updates['current_amount'] != goal.current_amount

        for key, value in updates.items():
            if hasattr(goal, key):
                setattr(goal, key, value)

        goal.updated_at = datetime.utcnow()

        # Update progress percentage
        if amount_changed or 'target_amount' in updates:
            self._update_progress_percentage(goal)

        self.db.commit()
        self.db.refresh(goal)

        # Log progress if amount changed
        if amount_changed:
            self._log_progress(
                goal.id,
                goal.current_amount - updates['current_amount'],
                updates['current_amount'],
                updates['current_amount'] - goal.current_amount,
                updates.get('note', 'Manual update'),
                is_manual=True
            )

        return goal

    def update_goal_progress(
        self,
        goal_id: int,
        user_id: int,
        new_amount: float,
        note: str = None,
        is_manual: bool = True
    ) -> Optional[FinancialGoal]:
        """Update the progress of a goal"""
        goal = self.get_goal(goal_id, user_id)
        if not goal:
            return None

        previous_amount = float(goal.current_amount)
        change_amount = new_amount - previous_amount

        goal.current_amount = new_amount
        goal.updated_at = datetime.utcnow()

        # Update progress percentage
        self._update_progress_percentage(goal)

        # Check if goal is completed
        if goal.current_amount >= goal.target_amount and goal.status == GoalStatus.ACTIVE:
            goal.status = GoalStatus.COMPLETED
            goal.completed_date = datetime.utcnow()

        self.db.commit()
        self.db.refresh(goal)

        # Log progress
        self._log_progress(goal.id, previous_amount, new_amount, change_amount, note, is_manual)

        return goal

    def delete_goal(self, goal_id: int, user_id: int) -> bool:
        """Delete a goal"""
        goal = self.get_goal(goal_id, user_id)
        if not goal:
            return False

        self.db.delete(goal)
        self.db.commit()
        return True

    def get_goal_progress_logs(
        self,
        goal_id: int,
        user_id: int,
        limit: int = 50
    ) -> List[GoalProgressLog]:
        """Get progress history for a goal"""
        goal = self.get_goal(goal_id, user_id)
        if not goal:
            return []

        return self.db.query(GoalProgressLog).filter(
            GoalProgressLog.goal_id == goal_id
        ).order_by(GoalProgressLog.recorded_at.desc()).limit(limit).all()

    def get_goal_statistics(self, user_id: int) -> Dict:
        """Get statistics about user's goals"""
        all_goals = self.get_user_goals(user_id, include_completed=True)

        active_goals = [g for g in all_goals if g.status == GoalStatus.ACTIVE]
        completed_goals = [g for g in all_goals if g.status == GoalStatus.COMPLETED]

        total_target = sum(g.target_amount for g in active_goals)
        total_current = sum(g.current_amount for g in active_goals)
        overall_progress = (total_current / total_target * 100) if total_target > 0 else 0

        # Goals by type
        goals_by_type = {}
        for goal_type in GoalType:
            goals_by_type[goal_type.value] = len([g for g in all_goals if g.goal_type == goal_type])

        # Upcoming deadlines
        now = datetime.utcnow()
        upcoming_deadlines = [
            g for g in active_goals
            if g.target_date and g.target_date > now and g.target_date <= now + timedelta(days=30)
        ]

        return {
            'total_goals': len(all_goals),
            'active_goals': len(active_goals),
            'completed_goals': len(completed_goals),
            'completion_rate': (len(completed_goals) / len(all_goals) * 100) if all_goals else 0,
            'total_target_amount': total_target,
            'total_current_amount': total_current,
            'overall_progress': overall_progress,
            'goals_by_type': goals_by_type,
            'upcoming_deadlines': len(upcoming_deadlines)
        }

    def auto_update_spending_limit_goals(self, user_id: int) -> List[FinancialGoal]:
        """Automatically update spending limit goals based on actual spending"""
        spending_goals = self.db.query(FinancialGoal).filter(
            FinancialGoal.user_id == user_id,
            FinancialGoal.goal_type == GoalType.SPENDING_LIMIT,
            FinancialGoal.status == GoalStatus.ACTIVE
        ).all()

        updated_goals = []
        now = datetime.utcnow()

        for goal in spending_goals:
            # Calculate current spending for the category
            query = self.db.query(func.sum(Entry.amount)).filter(
                Entry.user_id == user_id,
                Entry.type == "expense"
            )

            # Filter by category if specified
            if goal.category_id:
                query = query.filter(Entry.category_id == goal.category_id)

            # Filter by goal timeline
            if goal.start_date:
                query = query.filter(Entry.date >= goal.start_date)
            if goal.target_date:
                query = query.filter(Entry.date <= goal.target_date)

            current_spending = query.scalar() or 0

            # Update goal progress
            if current_spending != goal.current_amount:
                previous_amount = goal.current_amount
                goal.current_amount = current_spending
                self._update_progress_percentage(goal)

                # Check if exceeded limit
                if current_spending > goal.target_amount and goal.status == GoalStatus.ACTIVE:
                    goal.status = GoalStatus.FAILED
                    goal.completed_date = now

                goal.updated_at = now
                updated_goals.append(goal)

                # Log progress
                self._log_progress(
                    goal.id,
                    previous_amount,
                    current_spending,
                    current_spending - previous_amount,
                    "Automatic update from transactions",
                    is_manual=False
                )

        if updated_goals:
            self.db.commit()

        return updated_goals

    def _update_progress_percentage(self, goal: FinancialGoal):
        """Calculate and update progress percentage"""
        if goal.target_amount > 0:
            progress = (goal.current_amount / goal.target_amount * 100)
            goal.progress_percentage = min(progress, 100)  # Cap at 100%
        else:
            goal.progress_percentage = 0

    def _log_progress(
        self,
        goal_id: int,
        previous_amount: float,
        new_amount: float,
        change_amount: float,
        note: str = None,
        is_manual: bool = False
    ):
        """Log a progress update"""
        log = GoalProgressLog(
            goal_id=goal_id,
            previous_amount=previous_amount,
            new_amount=new_amount,
            change_amount=change_amount,
            note=note,
            is_manual=is_manual
        )
        self.db.add(log)
        # Commit happens in calling function

    def get_goals_summary_for_dashboard(self, user_id: int) -> Dict:
        """Get a summary of goals for dashboard widget"""
        active_goals = self.get_user_goals(user_id, status=GoalStatus.ACTIVE)

        if not active_goals:
            return {
                'has_goals': False,
                'total_goals': 0,
                'on_track': 0,
                'needs_attention': 0,
                'goals': []
            }

        # Categorize goals
        on_track = []
        needs_attention = []
        now = datetime.utcnow()

        for goal in active_goals:
            # Check if on track
            if goal.target_date:
                days_remaining = (goal.target_date - now).days
                total_days = (goal.target_date - goal.start_date).days
                expected_progress = ((total_days - days_remaining) / total_days * 100) if total_days > 0 else 0

                if goal.progress_percentage >= expected_progress - 10:  # 10% tolerance
                    on_track.append(goal)
                else:
                    needs_attention.append(goal)
            elif goal.progress_percentage >= 50:
                on_track.append(goal)
            else:
                needs_attention.append(goal)

        # Get top 3 goals by priority (needs attention first, then by progress)
        priority_goals = (needs_attention + on_track)[:3]

        return {
            'has_goals': True,
            'total_goals': len(active_goals),
            'on_track': len(on_track),
            'needs_attention': len(needs_attention),
            'goals': [
                {
                    'id': g.id,
                    'name': g.name,
                    'progress': float(g.progress_percentage),
                    'current_amount': float(g.current_amount),
                    'target_amount': float(g.target_amount),
                    'currency_code': g.currency_code,
                    'target_date': g.target_date.isoformat() if g.target_date else None,
                    'status': 'on_track' if g in on_track else 'needs_attention'
                }
                for g in priority_goals
            ]
        }

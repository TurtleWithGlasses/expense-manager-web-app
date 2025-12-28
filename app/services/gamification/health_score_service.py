"""Financial Health Score Service - Phase 3: Full Gamification

Calculates a comprehensive financial health score (0-100) based on multiple factors.
Provides detailed insights and recommendations for improvement.
"""
from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.entry import Entry
from app.models.financial_goal import FinancialGoal, GoalStatus
from app.models.category import Category


class HealthScoreService:
    """Service for calculating and tracking financial health scores"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_health_score(self, user_id: int) -> Dict:
        """
        Calculate comprehensive financial health score (0-100)

        Components (weighted):
        - Savings Rate (25%): Percentage of income saved
        - Budget Adherence (20%): Staying within budgets
        - Goal Progress (20%): Progress towards financial goals
        - Spending Consistency (15%): Consistent spending patterns
        - Income Stability (10%): Consistent income streams
        - Tracking Consistency (10%): Regular expense tracking
        """
        now = datetime.utcnow()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        three_months_ago = current_month_start - timedelta(days=90)

        # Calculate each component
        savings_score = self._calculate_savings_score(user_id, current_month_start, now)
        budget_score = self._calculate_budget_adherence_score(user_id, current_month_start, now)
        goal_score = self._calculate_goal_progress_score(user_id)
        consistency_score = self._calculate_spending_consistency_score(user_id, three_months_ago, now)
        income_score = self._calculate_income_stability_score(user_id, three_months_ago, now)
        tracking_score = self._calculate_tracking_consistency_score(user_id, current_month_start, now)

        # Weighted total
        total_score = (
            savings_score['score'] * 0.25 +
            budget_score['score'] * 0.20 +
            goal_score['score'] * 0.20 +
            consistency_score['score'] * 0.15 +
            income_score['score'] * 0.10 +
            tracking_score['score'] * 0.10
        )

        # Determine overall rating
        rating = self._get_rating(total_score)

        return {
            'total_score': round(total_score, 1),
            'rating': rating,
            'components': {
                'savings_rate': savings_score,
                'budget_adherence': budget_score,
                'goal_progress': goal_score,
                'spending_consistency': consistency_score,
                'income_stability': income_score,
                'tracking_consistency': tracking_score
            },
            'recommendations': self._generate_recommendations(
                savings_score, budget_score, goal_score,
                consistency_score, income_score, tracking_score
            ),
            'calculated_at': now.isoformat()
        }

    def _calculate_savings_score(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Calculate savings rate score (0-100)"""
        # Get income and expenses for the period
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

        if income == 0:
            return {'score': 0, 'savings_rate': 0, 'detail': 'No income recorded'}

        savings_rate = ((income - expenses) / income) * 100

        # Score based on savings rate
        # 0% = 0 points, 20% = 80 points, 30%+ = 100 points
        if savings_rate < 0:
            score = 0  # Spending more than earning
        elif savings_rate >= 30:
            score = 100
        else:
            score = min(100, (savings_rate / 30) * 100)

        return {
            'score': round(score, 1),
            'savings_rate': round(savings_rate, 1),
            'income': float(income),
            'expenses': float(expenses),
            'detail': f'Saving {round(savings_rate, 1)}% of income'
        }

    def _calculate_budget_adherence_score(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Calculate budget adherence score (0-100)"""
        # Get spending limit goals
        goals = self.db.query(FinancialGoal).filter(
            FinancialGoal.user_id == user_id,
            FinancialGoal.goal_type == 'spending_limit',
            FinancialGoal.status == GoalStatus.ACTIVE
        ).all()

        if not goals:
            return {'score': 75, 'detail': 'No budgets set (neutral score)'}

        within_budget = 0
        over_budget = 0

        for goal in goals:
            if goal.current_amount <= goal.target_amount:
                within_budget += 1
            else:
                over_budget += 1

        total_goals = len(goals)
        adherence_rate = (within_budget / total_goals) * 100

        # Score based on adherence rate
        score = adherence_rate

        return {
            'score': round(score, 1),
            'within_budget': within_budget,
            'over_budget': over_budget,
            'total_budgets': total_goals,
            'adherence_rate': round(adherence_rate, 1),
            'detail': f'{within_budget}/{total_goals} budgets on track'
        }

    def _calculate_goal_progress_score(self, user_id: int) -> Dict:
        """Calculate goal progress score (0-100)"""
        active_goals = self.db.query(FinancialGoal).filter(
            FinancialGoal.user_id == user_id,
            FinancialGoal.status == GoalStatus.ACTIVE
        ).all()

        if not active_goals:
            return {'score': 50, 'detail': 'No active goals (neutral score)'}

        total_progress = sum(float(goal.progress_percentage) for goal in active_goals)
        avg_progress = total_progress / len(active_goals)

        # Bonus for having goals
        score = min(100, avg_progress + 10)

        return {
            'score': round(score, 1),
            'average_progress': round(avg_progress, 1),
            'active_goals': len(active_goals),
            'detail': f'{round(avg_progress, 1)}% average progress across {len(active_goals)} goals'
        }

    def _calculate_spending_consistency_score(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Calculate spending consistency score (0-100)"""
        # Get monthly spending for last 3 months
        monthly_spending = []
        current_date = end_date

        for i in range(3):
            month_start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            spending = self.db.query(func.sum(Entry.amount)).filter(
                Entry.user_id == user_id,
                Entry.type == 'expense',
                Entry.date >= month_start,
                Entry.date <= min(month_end, current_date)
            ).scalar() or 0

            monthly_spending.append(float(spending))
            current_date = month_start - timedelta(days=1)

        if not any(monthly_spending):
            return {'score': 50, 'detail': 'Insufficient data'}

        # Calculate coefficient of variation (lower is better)
        avg_spending = sum(monthly_spending) / len(monthly_spending)
        if avg_spending == 0:
            return {'score': 100, 'detail': 'No spending recorded'}

        variance = sum((x - avg_spending) ** 2 for x in monthly_spending) / len(monthly_spending)
        std_dev = variance ** 0.5
        cv = (std_dev / avg_spending) * 100

        # Score based on CV (lower variation = higher score)
        # CV < 20% = 100 points, CV > 50% = 0 points
        if cv <= 20:
            score = 100
        elif cv >= 50:
            score = 0
        else:
            score = 100 - ((cv - 20) / 30 * 100)

        return {
            'score': round(score, 1),
            'coefficient_of_variation': round(cv, 1),
            'average_spending': round(avg_spending, 2),
            'detail': f'Spending variation: {round(cv, 1)}%'
        }

    def _calculate_income_stability_score(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Calculate income stability score (0-100)"""
        # Get monthly income for last 3 months
        monthly_income = []
        current_date = end_date

        for i in range(3):
            month_start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            income = self.db.query(func.sum(Entry.amount)).filter(
                Entry.user_id == user_id,
                Entry.type == 'income',
                Entry.date >= month_start,
                Entry.date <= min(month_end, current_date)
            ).scalar() or 0

            monthly_income.append(float(income))
            current_date = month_start - timedelta(days=1)

        if not any(monthly_income):
            return {'score': 50, 'detail': 'No income recorded'}

        # Calculate coefficient of variation
        avg_income = sum(monthly_income) / len(monthly_income)
        if avg_income == 0:
            return {'score': 50, 'detail': 'No income data'}

        variance = sum((x - avg_income) ** 2 for x in monthly_income) / len(monthly_income)
        std_dev = variance ** 0.5
        cv = (std_dev / avg_income) * 100

        # Score based on CV (lower variation = higher score)
        if cv <= 10:
            score = 100
        elif cv >= 40:
            score = 0
        else:
            score = 100 - ((cv - 10) / 30 * 100)

        return {
            'score': round(score, 1),
            'coefficient_of_variation': round(cv, 1),
            'average_income': round(avg_income, 2),
            'detail': f'Income variation: {round(cv, 1)}%'
        }

    def _calculate_tracking_consistency_score(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Calculate tracking consistency score (0-100)"""
        # Count days with entries
        dates_with_entries = self.db.query(func.count(func.distinct(func.date(Entry.date)))).filter(
            Entry.user_id == user_id,
            Entry.date >= start_date,
            Entry.date <= end_date
        ).scalar() or 0

        total_days = (end_date.date() - start_date.date()).days + 1
        tracking_rate = (dates_with_entries / total_days) * 100

        # Score based on tracking rate
        # 80%+ = 100 points, 50% = 50 points, <30% = 0 points
        if tracking_rate >= 80:
            score = 100
        elif tracking_rate <= 30:
            score = 0
        else:
            score = (tracking_rate - 30) / 50 * 100

        return {
            'score': round(score, 1),
            'days_tracked': dates_with_entries,
            'total_days': total_days,
            'tracking_rate': round(tracking_rate, 1),
            'detail': f'Tracked {dates_with_entries}/{total_days} days'
        }

    def _get_rating(self, score: float) -> str:
        """Get rating label for score"""
        if score >= 90:
            return 'Excellent'
        elif score >= 75:
            return 'Good'
        elif score >= 60:
            return 'Fair'
        elif score >= 40:
            return 'Needs Improvement'
        else:
            return 'Poor'

    def _generate_recommendations(
        self,
        savings_score: Dict,
        budget_score: Dict,
        goal_score: Dict,
        consistency_score: Dict,
        income_score: Dict,
        tracking_score: Dict
    ) -> List[str]:
        """Generate personalized recommendations based on scores"""
        recommendations = []

        # Savings recommendations
        if savings_score['score'] < 60:
            if savings_score.get('savings_rate', 0) < 10:
                recommendations.append("💰 Try to save at least 10% of your income each month")
            else:
                recommendations.append("💰 Aim to increase your savings rate to 20% or higher")

        # Budget recommendations
        if budget_score['score'] < 70:
            if budget_score.get('over_budget', 0) > 0:
                recommendations.append("📊 Review and adjust budgets that are being exceeded")

        # Goal recommendations
        if goal_score['score'] < 60:
            if goal_score.get('active_goals', 0) == 0:
                recommendations.append("🎯 Set financial goals to stay motivated and track progress")
            else:
                recommendations.append("🎯 Update your goal progress regularly to stay on track")

        # Consistency recommendations
        if consistency_score['score'] < 60:
            recommendations.append("📈 Try to maintain more consistent spending patterns each month")

        # Income recommendations
        if income_score['score'] < 60:
            recommendations.append("💵 Consider additional income streams for more stability")

        # Tracking recommendations
        if tracking_score['score'] < 70:
            recommendations.append("📝 Track your expenses daily for better financial awareness")

        # If doing well
        if not recommendations:
            recommendations.append("✨ Great job! Keep up the excellent financial habits")

        return recommendations

    def get_score_history(self, user_id: int, months: int = 6) -> List[Dict]:
        """Get historical health scores (placeholder for future implementation)"""
        # This would require storing historical scores in a database table
        # For now, return empty list
        return []

    def get_score_trends(self, user_id: int) -> Dict:
        """Get trends in health score components (placeholder)"""
        # Future implementation: track changes over time
        return {
            'trend': 'stable',
            'change_from_last_month': 0,
            'improving_areas': [],
            'declining_areas': []
        }

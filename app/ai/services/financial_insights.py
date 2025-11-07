"""Smart Financial Insights & Recommendations Service"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from collections import defaultdict

from app.models.entry import Entry
from app.models.category import Category
from app.ai.services.prediction_service import PredictionService
from app.ai.services.anomaly_detection import AnomalyDetectionService


class FinancialInsightsService:
    """Service for generating smart financial insights and personalized recommendations"""

    def __init__(self, db: Session):
        self.db = db
        self.prediction_service = PredictionService(db)
        self.anomaly_service = AnomalyDetectionService(db)

    def get_comprehensive_insights(self, user_id: int) -> Dict:
        """
        Generate comprehensive financial insights for user

        Returns:
            Dictionary with insights, recommendations, and action items
        """
        try:
            insights = {
                'spending_insights': self._analyze_spending_patterns(user_id),
                'saving_opportunities': self._identify_saving_opportunities(user_id),
                'budget_health': self._assess_budget_health(user_id),
                'category_insights': self._analyze_category_trends(user_id),
                'recommendations': self._generate_recommendations(user_id),
                'achievements': self._identify_achievements(user_id),
                'alerts': self._generate_alerts(user_id)
            }

            return {
                'success': True,
                'insights': insights,
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            print(f"Error generating insights: {e}")
            return {
                'success': False,
                'message': f"Failed to generate insights: {str(e)}",
                'error': str(e)
            }

    def _analyze_spending_patterns(self, user_id: int) -> Dict:
        """Analyze user's spending patterns and habits"""
        # Get last 3 months of data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=90)

        entries = self.db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.type == 'expense',
            Entry.date >= start_date,
            Entry.date <= end_date
        ).all()

        if not entries:
            return {'message': 'Not enough data for analysis'}

        df = pd.DataFrame([{
            'amount': float(e.amount),
            'date': e.date,
            'weekday': e.date.weekday(),
            'day_of_month': e.date.day,
            'hour': e.date.hour if hasattr(e, 'created_at') else 12,
            'category': e.category.name if e.category else 'Uncategorized'
        } for e in entries])

        # Analyze patterns
        patterns = {
            'most_active_day': self._get_weekday_name(df.groupby('weekday')['amount'].count().idxmax()),
            'highest_spending_day': self._get_weekday_name(df.groupby('weekday')['amount'].sum().idxmax()),
            'average_transaction': round(float(df['amount'].mean()), 2),
            'largest_transaction': round(float(df['amount'].max()), 2),
            'total_transactions': len(entries),
            'avg_daily_spending': round(float(df.groupby('date')['amount'].sum().mean()), 2),
            'spending_consistency': self._calculate_consistency(df)
        }

        # Month phases (beginning, middle, end)
        early_month = df[df['day_of_month'] <= 10]['amount'].sum()
        mid_month = df[(df['day_of_month'] > 10) & (df['day_of_month'] <= 20)]['amount'].sum()
        late_month = df[df['day_of_month'] > 20]['amount'].sum()

        if early_month > mid_month and early_month > late_month:
            patterns['spending_phase'] = 'front_loaded'
            patterns['spending_phase_description'] = "You spend more at the beginning of the month"
        elif late_month > early_month and late_month > mid_month:
            patterns['spending_phase'] = 'back_loaded'
            patterns['spending_phase_description'] = "You spend more at the end of the month"
        else:
            patterns['spending_phase'] = 'balanced'
            patterns['spending_phase_description'] = "Your spending is evenly distributed throughout the month"

        return patterns

    def _identify_saving_opportunities(self, user_id: int) -> List[Dict]:
        """Identify opportunities to save money"""
        opportunities = []

        # Get last 90 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=90)

        entries = self.db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.type == 'expense',
            Entry.date >= start_date,
            Entry.date <= end_date,
            Entry.category_id.isnot(None)
        ).all()

        if len(entries) < 20:
            return opportunities

        # Analyze by category
        category_spending = defaultdict(list)
        for entry in entries:
            category_spending[entry.category.name].append(float(entry.amount))

        for category, amounts in category_spending.items():
            if len(amounts) < 5:
                continue

            total = sum(amounts)
            avg = total / len(amounts)
            monthly_avg = total / 3  # 3 months of data

            # High volume category
            if monthly_avg > 200 and len(amounts) > 10:
                potential_saving = monthly_avg * 0.15  # 15% reduction
                opportunities.append({
                    'type': 'high_volume_category',
                    'category': category,
                    'current_monthly': round(monthly_avg, 2),
                    'potential_saving': round(potential_saving, 2),
                    'recommendation': f"Reduce {category} spending by 15% to save {potential_saving:.2f} per month",
                    'priority': 'high' if monthly_avg > 500 else 'medium'
                })

            # Frequent small purchases
            if len(amounts) > 15 and avg < 30:
                monthly_count = len(amounts) / 3
                if monthly_count > 8:  # More than 8 transactions per month
                    opportunities.append({
                        'type': 'frequent_small_purchases',
                        'category': category,
                        'avg_transaction': round(avg, 2),
                        'monthly_transactions': int(monthly_count),
                        'recommendation': f"Consolidate {category} purchases to reduce impulse spending",
                        'priority': 'low'
                    })

        # Sort by potential savings
        opportunities.sort(key=lambda x: x.get('potential_saving', 0), reverse=True)
        return opportunities[:5]  # Top 5 opportunities

    def _assess_budget_health(self, user_id: int) -> Dict:
        """Assess overall budget health"""
        # Get current month data
        now = datetime.now()
        month_start = now.replace(day=1).date()

        current_month_expenses = self.db.query(func.sum(Entry.amount)).filter(
            Entry.user_id == user_id,
            Entry.type == 'expense',
            Entry.date >= month_start
        ).scalar() or 0

        current_month_income = self.db.query(func.sum(Entry.amount)).filter(
            Entry.user_id == user_id,
            Entry.type == 'income',
            Entry.date >= month_start
        ).scalar() or 0

        # Get previous month data
        prev_month_start = (month_start - timedelta(days=1)).replace(day=1)
        prev_month_end = month_start - timedelta(days=1)

        prev_month_expenses = self.db.query(func.sum(Entry.amount)).filter(
            Entry.user_id == user_id,
            Entry.type == 'expense',
            Entry.date >= prev_month_start,
            Entry.date <= prev_month_end
        ).scalar() or 0

        prev_month_income = self.db.query(func.sum(Entry.amount)).filter(
            Entry.user_id == user_id,
            Entry.type == 'income',
            Entry.date >= prev_month_start,
            Entry.date <= prev_month_end
        ).scalar() or 0

        # Calculate health metrics
        current_savings_rate = ((current_month_income - current_month_expenses) / current_month_income * 100) if current_month_income > 0 else 0
        prev_savings_rate = ((prev_month_income - prev_month_expenses) / prev_month_income * 100) if prev_month_income > 0 else 0

        # Health score (0-100)
        health_score = 100

        # Deduct points for negative savings
        if current_savings_rate < 0:
            health_score -= 30
        elif current_savings_rate < 10:
            health_score -= 20
        elif current_savings_rate < 20:
            health_score -= 10

        # Deduct points for increasing expenses
        expense_change = ((current_month_expenses - prev_month_expenses) / prev_month_expenses * 100) if prev_month_expenses > 0 else 0
        if expense_change > 20:
            health_score -= 20
        elif expense_change > 10:
            health_score -= 10

        health_score = max(0, min(100, health_score))

        # Determine status
        if health_score >= 80:
            status = 'excellent'
            status_message = 'Your budget health is excellent!'
        elif health_score >= 60:
            status = 'good'
            status_message = 'Your budget health is good with room for improvement'
        elif health_score >= 40:
            status = 'fair'
            status_message = 'Your budget health needs attention'
        else:
            status = 'poor'
            status_message = 'Your budget health requires immediate action'

        return {
            'health_score': round(health_score, 1),
            'status': status,
            'status_message': status_message,
            'current_savings_rate': round(float(current_savings_rate), 2),
            'previous_savings_rate': round(float(prev_savings_rate), 2),
            'expense_change_percentage': round(float(expense_change), 2),
            'current_month_expense': round(float(current_month_expenses), 2),
            'current_month_income': round(float(current_month_income), 2)
        }

    def _analyze_category_trends(self, user_id: int) -> List[Dict]:
        """Analyze spending trends by category"""
        # Get last 6 months of data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=180)

        entries = self.db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.type == 'expense',
            Entry.date >= start_date,
            Entry.date <= end_date,
            Entry.category_id.isnot(None)
        ).all()

        if not entries:
            return []

        # Group by category and month
        df = pd.DataFrame([{
            'category': e.category.name,
            'amount': float(e.amount),
            'month': f"{e.date.year}-{e.date.month:02d}"
        } for e in entries])

        category_trends = []

        for category in df['category'].unique():
            cat_data = df[df['category'] == category]
            monthly_spending = cat_data.groupby('month')['amount'].sum()

            if len(monthly_spending) < 2:
                continue

            # Calculate trend
            months = list(range(len(monthly_spending)))
            amounts = monthly_spending.values

            # Simple linear regression
            if len(months) > 1:
                slope = np.polyfit(months, amounts, 1)[0]
                avg_monthly = amounts.mean()
                trend_percentage = (slope / avg_monthly * 100) if avg_monthly > 0 else 0

                trend = 'increasing' if trend_percentage > 5 else 'decreasing' if trend_percentage < -5 else 'stable'

                category_trends.append({
                    'category': category,
                    'trend': trend,
                    'trend_percentage': round(float(trend_percentage), 2),
                    'avg_monthly': round(float(avg_monthly), 2),
                    'latest_month': round(float(amounts[-1]), 2),
                    'change_amount': round(float(amounts[-1] - avg_monthly), 2)
                })

        # Sort by absolute trend percentage
        category_trends.sort(key=lambda x: abs(x['trend_percentage']), reverse=True)
        return category_trends[:5]  # Top 5 trending categories

    def _generate_recommendations(self, user_id: int) -> List[Dict]:
        """Generate personalized financial recommendations"""
        recommendations = []

        # Get budget health
        budget_health = self._assess_budget_health(user_id)

        # Recommendation based on budget health
        if budget_health['health_score'] < 60:
            recommendations.append({
                'type': 'budget_health',
                'priority': 'high',
                'title': 'Improve Budget Health',
                'description': f"Your budget health score is {budget_health['health_score']:.0f}/100. Focus on reducing expenses and increasing savings.",
                'action': 'Review spending in top categories and set reduction targets',
                'potential_impact': 'high'
            })

        # Recommendation based on savings rate
        if budget_health['current_savings_rate'] < 10:
            recommendations.append({
                'type': 'savings_rate',
                'priority': 'high',
                'title': 'Increase Savings Rate',
                'description': f"Your current savings rate is {budget_health['current_savings_rate']:.1f}%. Aim for at least 20%.",
                'action': 'Set a monthly savings goal and automate transfers',
                'potential_impact': 'high'
            })

        # Get saving opportunities
        opportunities = self._identify_saving_opportunities(user_id)
        if opportunities:
            total_potential = sum(opp.get('potential_saving', 0) for opp in opportunities)
            recommendations.append({
                'type': 'saving_opportunities',
                'priority': 'medium',
                'title': 'Identified Saving Opportunities',
                'description': f"Found {len(opportunities)} opportunities to save up to {total_potential:.2f} per month",
                'action': f"Focus on reducing {opportunities[0]['category']} spending first",
                'potential_impact': 'medium'
            })

        # Check for anomalies
        anomaly_insights = self.anomaly_service.get_anomaly_insights(user_id)
        if anomaly_insights.get('success') and len(anomaly_insights.get('insights', [])) > 0:
            recommendations.append({
                'type': 'anomaly_review',
                'priority': 'medium',
                'title': 'Review Unusual Transactions',
                'description': 'Detected unusual spending patterns that need review',
                'action': 'Check anomaly alerts for potential fraud or errors',
                'potential_impact': 'medium'
            })

        # Category trend recommendations
        category_trends = self._analyze_category_trends(user_id)
        increasing_trends = [t for t in category_trends if t['trend'] == 'increasing' and t['trend_percentage'] > 15]

        if increasing_trends:
            top_increasing = increasing_trends[0]
            recommendations.append({
                'type': 'category_trend',
                'priority': 'low',
                'title': f"{top_increasing['category']} Spending Increasing",
                'description': f"{top_increasing['category']} spending has increased by {top_increasing['trend_percentage']:.1f}%",
                'action': f"Monitor {top_increasing['category']} expenses and set a limit",
                'potential_impact': 'low'
            })

        return recommendations

    def _identify_achievements(self, user_id: int) -> List[Dict]:
        """Identify positive financial achievements"""
        achievements = []

        budget_health = self._assess_budget_health(user_id)

        # Good savings rate
        if budget_health['current_savings_rate'] > 20:
            achievements.append({
                'type': 'savings_rate',
                'title': 'Excellent Saver',
                'description': f"You're saving {budget_health['current_savings_rate']:.1f}% of your income!",
                'icon': 'piggy-bank'
            })

        # Improved from last month
        if budget_health['current_savings_rate'] > budget_health['previous_savings_rate']:
            improvement = budget_health['current_savings_rate'] - budget_health['previous_savings_rate']
            achievements.append({
                'type': 'improvement',
                'title': 'Savings Improved',
                'description': f"Your savings rate increased by {improvement:.1f}% from last month",
                'icon': 'graph-up'
            })

        # Good budget health
        if budget_health['health_score'] >= 80:
            achievements.append({
                'type': 'budget_health',
                'title': 'Excellent Budget Health',
                'description': f"Your budget health score is {budget_health['health_score']:.0f}/100!",
                'icon': 'award'
            })

        # Consistent tracking
        total_entries = self.db.query(Entry).filter(Entry.user_id == user_id).count()
        if total_entries > 50:
            achievements.append({
                'type': 'consistency',
                'title': 'Consistent Tracker',
                'description': f"You've recorded {total_entries} transactions. Great job!",
                'icon': 'check-circle'
            })

        return achievements

    def _generate_alerts(self, user_id: int) -> List[Dict]:
        """Generate important financial alerts"""
        alerts = []

        # Budget health alerts
        budget_health = self._assess_budget_health(user_id)

        if budget_health['health_score'] < 40:
            alerts.append({
                'type': 'warning',
                'severity': 'high',
                'title': 'Budget Health Critical',
                'message': 'Your budget health needs immediate attention',
                'action': 'Review expenses and create a spending plan'
            })

        if budget_health['current_savings_rate'] < 0:
            alerts.append({
                'type': 'warning',
                'severity': 'high',
                'title': 'Spending Exceeds Income',
                'message': 'You\'re spending more than you earn this month',
                'action': 'Reduce discretionary expenses immediately'
            })

        # Expense increase alert
        if budget_health['expense_change_percentage'] > 25:
            alerts.append({
                'type': 'info',
                'severity': 'medium',
                'title': 'Expenses Increased',
                'message': f"Your expenses increased by {budget_health['expense_change_percentage']:.1f}% from last month",
                'action': 'Review recent large purchases'
            })

        # Get prediction
        prediction = self.prediction_service.predict_budget_status(user_id)
        if prediction.get('success') and prediction.get('status') == 'over_budget':
            alerts.append({
                'type': 'warning',
                'severity': 'medium',
                'title': 'Projected to Exceed Budget',
                'message': f"You're projected to spend {prediction['predicted_month_total']:.2f} this month",
                'action': 'Reduce spending for the rest of the month'
            })

        return alerts

    def _calculate_consistency(self, df: pd.DataFrame) -> str:
        """Calculate spending consistency"""
        daily_spending = df.groupby('date')['amount'].sum()
        std_dev = daily_spending.std()
        mean = daily_spending.mean()

        cv = (std_dev / mean) if mean > 0 else 0  # Coefficient of variation

        if cv < 0.5:
            return 'very_consistent'
        elif cv < 1.0:
            return 'consistent'
        elif cv < 1.5:
            return 'moderate'
        else:
            return 'inconsistent'

    def _get_weekday_name(self, weekday: int) -> str:
        """Convert weekday number to name"""
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return days[int(weekday)]

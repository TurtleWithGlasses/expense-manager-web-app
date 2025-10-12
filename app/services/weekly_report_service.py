"""Automated Weekly Financial Report Service"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal

from app.models.entry import Entry
from app.models.category import Category
from app.models.user import User
from app.core.currency import CurrencyService


class WeeklyReportService:
    """Generate comprehensive weekly financial reports"""
    
    def __init__(self, db: Session):
        self.db = db
        self.currency_service = CurrencyService()
    
    def generate_weekly_report(self, user_id: int, week_end_date: Optional[date] = None) -> Dict:
        """
        Generate comprehensive weekly financial report
        
        Args:
            user_id: User ID
            week_end_date: End date of the week (defaults to today)
        
        Returns:
            Dictionary with comprehensive weekly insights
        """
        # Default to current week (Monday to Sunday)
        if week_end_date is None:
            week_end_date = date.today()
        
        # Calculate week boundaries (Monday to Sunday)
        week_start = week_end_date - timedelta(days=week_end_date.weekday())  # Monday
        week_end = week_start + timedelta(days=6)  # Sunday
        
        # Get previous week for comparison
        prev_week_start = week_start - timedelta(days=7)
        prev_week_end = week_start - timedelta(days=1)
        
        # Get user for currency
        user = self.db.query(User).filter(User.id == user_id).first()
        
        # Generate all report sections
        report = {
            'period': {
                'start': week_start.isoformat(),
                'end': week_end.isoformat(),
                'week_number': week_start.isocalendar()[1],
                'year': week_start.year
            },
            'summary': self._generate_summary(user_id, week_start, week_end, prev_week_start, prev_week_end),
            'category_analysis': self._analyze_categories(user_id, week_start, week_end, prev_week_start, prev_week_end),
            'daily_breakdown': self._daily_breakdown(user_id, week_start, week_end),
            'insights': self._generate_insights(user_id, week_start, week_end, prev_week_start, prev_week_end),
            'achievements': self._detect_achievements(user_id, week_start, week_end),
            'recommendations': self._generate_recommendations(user_id, week_start, week_end),
            'anomalies': self._detect_anomalies(user_id, week_start, week_end),
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return report
    
    def _generate_summary(self, user_id: int, week_start: date, week_end: date,
                         prev_week_start: date, prev_week_end: date) -> Dict:
        """Generate week summary with comparisons"""
        # Current week data
        current_week = self.db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.date >= week_start,
            Entry.date <= week_end
        ).all()
        
        # Previous week data
        previous_week = self.db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.date >= prev_week_start,
            Entry.date <= prev_week_end
        ).all()
        
        # Calculate totals
        current_expenses = sum(float(e.amount) for e in current_week if e.type == 'expense')
        current_income = sum(float(e.amount) for e in current_week if e.type == 'income')
        
        prev_expenses = sum(float(e.amount) for e in previous_week if e.type == 'expense')
        prev_income = sum(float(e.amount) for e in previous_week if e.type == 'income')
        
        # Calculate changes
        expense_change = ((current_expenses - prev_expenses) / prev_expenses * 100) if prev_expenses > 0 else 0
        income_change = ((current_income - prev_income) / prev_income * 100) if prev_income > 0 else 0
        
        # Net savings
        current_net = current_income - current_expenses
        prev_net = prev_income - prev_expenses
        net_change = current_net - prev_net
        
        return {
            'total_expenses': current_expenses,
            'total_income': current_income,
            'net_savings': current_net,
            'transaction_count': len(current_week),
            'avg_transaction': current_expenses / len([e for e in current_week if e.type == 'expense']) if any(e.type == 'expense' for e in current_week) else 0,
            'comparison': {
                'expense_change_pct': expense_change,
                'expense_change_amount': current_expenses - prev_expenses,
                'income_change_pct': income_change,
                'income_change_amount': current_income - prev_income,
                'net_change': net_change,
                'prev_week_expenses': prev_expenses,
                'prev_week_income': prev_income
            }
        }
    
    def _analyze_categories(self, user_id: int, week_start: date, week_end: date,
                           prev_week_start: date, prev_week_end: date) -> Dict:
        """Analyze spending by category with comparisons"""
        # Current week by category
        current_week = self.db.query(
            Category.name,
            func.sum(Entry.amount).label('total'),
            func.count(Entry.id).label('count')
        ).join(
            Entry, Entry.category_id == Category.id
        ).filter(
            Entry.user_id == user_id,
            Entry.type == 'expense',
            Entry.date >= week_start,
            Entry.date <= week_end
        ).group_by(Category.name).all()
        
        # Previous week by category
        previous_week = self.db.query(
            Category.name,
            func.sum(Entry.amount).label('total')
        ).join(
            Entry, Entry.category_id == Category.id
        ).filter(
            Entry.user_id == user_id,
            Entry.type == 'expense',
            Entry.date >= prev_week_start,
            Entry.date <= prev_week_end
        ).group_by(Category.name).all()
        
        # Build category map for previous week
        prev_category_map = {name: float(total) for name, total in previous_week}
        
        # Analyze each category
        categories = []
        increased = []
        decreased = []
        new_spending = []
        no_spending = []
        
        for name, total, count in current_week:
            total_float = float(total)
            prev_total = prev_category_map.get(name, 0)
            
            if prev_total > 0:
                change_pct = ((total_float - prev_total) / prev_total) * 100
                change_amount = total_float - prev_total
            else:
                change_pct = 100 if total_float > 0 else 0
                change_amount = total_float
                if total_float > 0:
                    new_spending.append({
                        'category': name,
                        'amount': total_float,
                        'count': count
                    })
            
            category_data = {
                'name': name,
                'amount': total_float,
                'count': count,
                'prev_amount': prev_total,
                'change_pct': change_pct,
                'change_amount': change_amount
            }
            
            categories.append(category_data)
            
            if change_pct > 10:
                increased.append(category_data)
            elif change_pct < -10:
                decreased.append(category_data)
        
        # Find categories with no spending this week (but had spending before)
        all_categories = self.db.query(Category.name).filter(Category.user_id == user_id).all()
        current_category_names = {name for name, _, _ in current_week}
        
        for (cat_name,) in all_categories:
            if cat_name not in current_category_names and cat_name in prev_category_map:
                no_spending.append({
                    'category': cat_name,
                    'prev_amount': prev_category_map[cat_name]
                })
        
        # Sort by amount
        categories.sort(key=lambda x: x['amount'], reverse=True)
        increased.sort(key=lambda x: x['change_pct'], reverse=True)
        decreased.sort(key=lambda x: x['change_pct'])
        
        return {
            'all_categories': categories,
            'top_category': categories[0] if categories else None,
            'increased_spending': increased,
            'decreased_spending': decreased,
            'new_spending_categories': new_spending,
            'no_spending_categories': no_spending,
            'total_categories_used': len(categories)
        }
    
    def _daily_breakdown(self, user_id: int, week_start: date, week_end: date) -> List[Dict]:
        """Daily breakdown of the week"""
        daily_data = []
        
        for i in range(7):
            day = week_start + timedelta(days=i)
            day_name = day.strftime('%A')
            
            day_entries = self.db.query(Entry).filter(
                Entry.user_id == user_id,
                Entry.date == day
            ).all()
            
            expenses = sum(float(e.amount) for e in day_entries if e.type == 'expense')
            income = sum(float(e.amount) for e in day_entries if e.type == 'income')
            
            daily_data.append({
                'date': day.isoformat(),
                'day_name': day_name,
                'expenses': expenses,
                'income': income,
                'net': income - expenses,
                'transaction_count': len(day_entries),
                'is_weekend': day.weekday() >= 5
            })
        
        return daily_data
    
    def _generate_insights(self, user_id: int, week_start: date, week_end: date,
                          prev_week_start: date, prev_week_end: date) -> List[str]:
        """Generate natural language insights"""
        insights = []
        
        summary = self._generate_summary(user_id, week_start, week_end, prev_week_start, prev_week_end)
        category_analysis = self._analyze_categories(user_id, week_start, week_end, prev_week_start, prev_week_end)
        
        # Expense trend insight
        expense_change = summary['comparison']['expense_change_pct']
        if abs(expense_change) >= 10:
            if expense_change > 0:
                insights.append(f"Your expenses increased by {abs(expense_change):.1f}% compared to last week (${summary['comparison']['expense_change_amount']:.2f} more).")
            else:
                insights.append(f"Great job! Your expenses decreased by {abs(expense_change):.1f}% compared to last week (${abs(summary['comparison']['expense_change_amount']):.2f} saved).")
        else:
            insights.append(f"Your expenses remained stable this week (only {abs(expense_change):.1f}% change).")
        
        # Category insights
        if category_analysis['increased_spending']:
            top_increase = category_analysis['increased_spending'][0]
            insights.append(f"You spent {top_increase['change_pct']:.0f}% more on {top_increase['name']} (${top_increase['change_amount']:.2f} increase).")
        
        if category_analysis['decreased_spending']:
            top_decrease = category_analysis['decreased_spending'][0]
            insights.append(f"You spent {abs(top_decrease['change_pct']):.0f}% less on {top_decrease['name']} (${abs(top_decrease['change_amount']):.2f} saved).")
        
        # Top spending category
        if category_analysis['top_category']:
            top_cat = category_analysis['top_category']
            insights.append(f"Your biggest spending category was {top_cat['name']} with ${top_cat['amount']:.2f} ({top_cat['count']} transactions).")
        
        # New categories
        if category_analysis['new_spending_categories']:
            new_cats = [c['category'] for c in category_analysis['new_spending_categories']]
            if len(new_cats) == 1:
                insights.append(f"New category this week: {new_cats[0]}.")
            else:
                insights.append(f"New categories this week: {', '.join(new_cats)}.")
        
        # No spending categories
        if category_analysis['no_spending_categories']:
            no_spend_cats = [c['category'] for c in category_analysis['no_spending_categories'][:3]]
            if len(no_spend_cats) == 1:
                insights.append(f"You didn't spend on {no_spend_cats[0]} this week.")
            elif len(no_spend_cats) <= 3:
                insights.append(f"You didn't spend on {', '.join(no_spend_cats)} this week.")
            else:
                insights.append(f"You didn't spend on {len(category_analysis['no_spending_categories'])} categories this week.")
        
        # Total spending insight
        insights.append(f"Total spending this week: ${summary['total_expenses']:.2f} across {summary['transaction_count']} transactions.")
        
        # Net savings insight
        if summary['net_savings'] > 0:
            insights.append(f"You saved ${summary['net_savings']:.2f} this week!")
        elif summary['net_savings'] < 0:
            insights.append(f"You spent ${abs(summary['net_savings']):.2f} more than you earned this week.")
        
        return insights
    
    def _detect_achievements(self, user_id: int, week_start: date, week_end: date) -> List[Dict]:
        """Detect positive achievements and milestones"""
        achievements = []
        
        # Get current week data
        current_week = self.db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.date >= week_start,
            Entry.date <= week_end
        ).all()
        
        expenses = [e for e in current_week if e.type == 'expense']
        
        # Achievement 1: Low spending streak
        daily_expenses = {}
        for e in expenses:
            day_str = e.date.isoformat()
            if day_str not in daily_expenses:
                daily_expenses[day_str] = 0
            daily_expenses[day_str] += float(e.amount)
        
        # Count days with no expenses or low expenses
        no_expense_days = sum(1 for day in self._get_week_days(week_start, week_end) 
                             if day.isoformat() not in daily_expenses)
        
        if no_expense_days >= 2:
            achievements.append({
                'type': 'no_spend_days',
                'title': f'{no_expense_days} No-Spend Days',
                'description': f'You had {no_expense_days} days without any expenses this week!',
                'points': no_expense_days * 10
            })
        
        # Achievement 2: Budget discipline
        avg_daily_expense = sum(daily_expenses.values()) / 7 if daily_expenses else 0
        
        # Get historical average
        thirty_days_ago = week_start - timedelta(days=30)
        historical = self.db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.type == 'expense',
            Entry.date >= thirty_days_ago,
            Entry.date < week_start
        ).all()
        
        if historical:
            hist_avg = sum(float(e.amount) for e in historical) / 30
            if avg_daily_expense < hist_avg * 0.8:
                savings = (hist_avg - avg_daily_expense) * 7
                achievements.append({
                    'type': 'under_budget',
                    'title': 'Under Budget!',
                    'description': f'You spent 20% less than your average this week, saving ${savings:.2f}!',
                    'points': 50
                })
        
        # Achievement 3: Consistent tracking
        if len(current_week) >= 7:
            achievements.append({
                'type': 'consistent_tracking',
                'title': 'Consistent Tracker',
                'description': 'You tracked at least one transaction every day this week!',
                'points': 25
            })
        
        # Achievement 4: Category diversity (balanced spending)
        categories_used = set(e.category_id for e in expenses if e.category_id)
        if len(categories_used) >= 5:
            achievements.append({
                'type': 'balanced_spending',
                'title': 'Balanced Spending',
                'description': f'You maintained diverse spending across {len(categories_used)} categories.',
                'points': 30
            })
        
        return achievements
    
    def _generate_recommendations(self, user_id: int, week_start: date, week_end: date) -> List[Dict]:
        """Generate actionable recommendations"""
        recommendations = []
        
        category_analysis = self._analyze_categories(user_id, week_start, week_end, 
                                                     week_start - timedelta(days=7), 
                                                     week_start - timedelta(days=1))
        
        # Recommendation 1: High spending category
        if category_analysis['top_category']:
            top_cat = category_analysis['top_category']
            if top_cat['amount'] > 200:  # Threshold
                recommendations.append({
                    'type': 'reduce_spending',
                    'priority': 'high',
                    'category': top_cat['name'],
                    'title': f"Consider reducing {top_cat['name']} spending",
                    'description': f"You spent ${top_cat['amount']:.2f} on {top_cat['name']} this week. Could you reduce by 10-20%?",
                    'potential_savings': top_cat['amount'] * 0.15  # 15% savings potential
                })
        
        # Recommendation 2: Increased spending alerts
        for cat in category_analysis['increased_spending'][:2]:  # Top 2 increases
            if cat['change_pct'] > 50:
                recommendations.append({
                    'type': 'spending_spike',
                    'priority': 'medium',
                    'category': cat['name'],
                    'title': f"{cat['name']} spending spiked {cat['change_pct']:.0f}%",
                    'description': f"You spent ${cat['change_amount']:.2f} more on {cat['name']} this week. Is this expected?",
                    'action': 'review'
                })
        
        # Recommendation 3: Savings opportunity
        summary = self._generate_summary(user_id, week_start, week_end, 
                                        week_start - timedelta(days=7), 
                                        week_start - timedelta(days=1))
        
        if summary['net_savings'] < 0:
            recommendations.append({
                'type': 'increase_savings',
                'priority': 'high',
                'title': 'Increase your savings',
                'description': f"You spent ${abs(summary['net_savings']):.2f} more than you earned. Consider setting a weekly budget.",
                'action': 'budget_plan'
            })
        
        # Recommendation 4: Positive reinforcement
        for cat in category_analysis['decreased_spending'][:1]:  # Top decrease
            if cat['change_pct'] < -20:
                recommendations.append({
                    'type': 'positive_habit',
                    'priority': 'low',
                    'category': cat['name'],
                    'title': f"Great job on {cat['name']}!",
                    'description': f"You reduced {cat['name']} spending by {abs(cat['change_pct']):.0f}%, saving ${abs(cat['change_amount']):.2f}. Keep it up!",
                    'action': 'celebrate'
                })
        
        return recommendations
    
    def _detect_anomalies(self, user_id: int, week_start: date, week_end: date) -> List[Dict]:
        """Detect unusual transactions"""
        anomalies = []
        
        # Get current week transactions
        current_week = self.db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.type == 'expense',
            Entry.date >= week_start,
            Entry.date <= week_end
        ).all()
        
        if not current_week:
            return anomalies
        
        # Get historical data for comparison (last 90 days)
        ninety_days_ago = week_start - timedelta(days=90)
        historical = self.db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.type == 'expense',
            Entry.date >= ninety_days_ago,
            Entry.date < week_start
        ).all()
        
        if not historical:
            return anomalies
        
        # Calculate statistical thresholds
        hist_amounts = [float(e.amount) for e in historical]
        mean_amount = np.mean(hist_amounts)
        std_amount = np.std(hist_amounts)
        threshold = mean_amount + (2 * std_amount)  # 2 standard deviations
        
        # Detect anomalies
        for entry in current_week:
            amount = float(entry.amount)
            
            # Anomaly 1: Unusually large transaction
            if amount > threshold and amount > mean_amount * 2:
                anomalies.append({
                    'type': 'large_transaction',
                    'entry_id': entry.id,
                    'date': entry.date.isoformat(),
                    'amount': amount,
                    'category': entry.category.name if entry.category else 'Uncategorized',
                    'note': entry.note,
                    'severity': 'high' if amount > mean_amount * 5 else 'medium',
                    'description': f"${amount:.2f} is {(amount/mean_amount):.1f}x your average transaction.",
                    'comparison': f"Your typical transaction: ${mean_amount:.2f}"
                })
            
            # Anomaly 2: Unusual category for amount
            if entry.category_id:
                category_hist = [e for e in historical if e.category_id == entry.category_id]
                if category_hist:
                    cat_amounts = [float(e.amount) for e in category_hist]
                    cat_mean = np.mean(cat_amounts)
                    
                    if amount > cat_mean * 3:
                        anomalies.append({
                            'type': 'unusual_category_amount',
                            'entry_id': entry.id,
                            'date': entry.date.isoformat(),
                            'amount': amount,
                            'category': entry.category.name,
                            'note': entry.note,
                            'severity': 'medium',
                            'description': f"${amount:.2f} is unusually high for {entry.category.name}.",
                            'comparison': f"Typical {entry.category.name}: ${cat_mean:.2f}"
                        })
        
        return anomalies
    
    def _get_week_days(self, week_start: date, week_end: date) -> List[date]:
        """Get list of all days in the week"""
        return [week_start + timedelta(days=i) for i in range(7)]
    
    def format_report_text(self, report: Dict) -> str:
        """Format report as readable text for email"""
        summary = report['summary']
        period = report['period']
        
        text = f"""
📊 YOUR WEEKLY FINANCIAL REPORT
Week of {period['start']} to {period['end']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 SUMMARY
• Total Expenses: ${summary['total_expenses']:.2f}
• Total Income: ${summary['total_income']:.2f}
• Net Savings: ${summary['net_savings']:.2f}
• Transactions: {summary['transaction_count']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 KEY INSIGHTS

"""
        
        for insight in report['insights']:
            text += f"{insight}\n"
        
        text += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Achievements
        if report['achievements']:
            text += "🏆 ACHIEVEMENTS THIS WEEK\n\n"
            for achievement in report['achievements']:
                text += f"{achievement['title']}\n{achievement['description']}\n\n"
            text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Recommendations
        if report['recommendations']:
            text += "💡 RECOMMENDATIONS\n\n"
            for rec in report['recommendations']:
                text += f"{rec['title']}\n{rec['description']}\n\n"
            text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Anomalies
        if report['anomalies']:
            text += "⚠️ UNUSUAL TRANSACTIONS\n\n"
            for anomaly in report['anomalies']:
                text += f"• ${anomaly['amount']:.2f} on {anomaly['date']} - {anomaly['category']}\n"
                text += f"  {anomaly['description']}\n\n"
        
        text += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Keep tracking your finances! 💪

View detailed report: https://www.yourbudgetpulse.online/
"""
        
        return text


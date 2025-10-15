"""Monthly Financial Report Service"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.entry import Entry
from app.models.user_preferences import UserPreferences
from app.models.category import Category
from app.core.currency import CurrencyService


class MonthlyReportService:
    """Service for generating monthly financial reports"""
    
    def __init__(self, db: Session):
        self.db = db
        self.currency_service = CurrencyService()
    
    def generate_monthly_report(self, user_id: int, month_date: Optional[date] = None) -> Dict:
        """
        Generate comprehensive monthly financial report
        
        Args:
            user_id: User ID
            month_date: Specific month to analyze (defaults to current month)
        
        Returns:
            Dict containing monthly report data
        """
        if month_date is None:
            month_date = date.today()
        
        # Calculate month boundaries
        month_start = month_date.replace(day=1)
        if month_date.month == 12:
            month_end = month_date.replace(year=month_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = month_date.replace(month=month_date.month + 1, day=1) - timedelta(days=1)
        
        # Previous month for comparison
        if month_start.month == 1:
            prev_month_start = month_start.replace(year=month_start.year - 1, month=12)
            prev_month_end = month_start - timedelta(days=1)
        else:
            prev_month_start = month_start.replace(month=month_start.month - 1)
            prev_month_end = month_start - timedelta(days=1)
        
        # Get user's currency
        user_prefs = self.db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
        user_currency = user_prefs.currency_code if user_prefs and user_prefs.currency_code else 'USD'
        
        # Generate report components (monthly reports show income)
        report = {
            'period': {
                'start': month_start.isoformat(),
                'end': month_end.isoformat(),
                'month': month_start.month,
                'year': month_start.year,
                'month_name': month_start.strftime('%B')
            },
            'currency': user_currency,
            'summary': self._generate_summary(user_id, month_start, month_end, prev_month_start, prev_month_end),
            'category_analysis': self._analyze_categories(user_id, month_start, month_end, prev_month_start, prev_month_end),
            'daily_breakdown': self._daily_breakdown(user_id, month_start, month_end),
            'insights': self._generate_insights(user_id, month_start, month_end, prev_month_start, prev_month_end),
            'achievements': self._detect_achievements(user_id, month_start, month_end),
            'recommendations': self._generate_recommendations(user_id, month_start, month_end),
            'show_income': True,  # Monthly reports always show income
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return report
    
    def _generate_summary(self, user_id: int, month_start: date, month_end: date,
                         prev_month_start: date, prev_month_end: date) -> Dict:
        """Generate month summary with comparisons"""
        # Current month data
        current_month = self.db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.date >= month_start,
            Entry.date <= month_end
        ).all()
        
        # Previous month data
        prev_month = self.db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.date >= prev_month_start,
            Entry.date <= prev_month_end
        ).all()
        
        # Calculate totals
        current_expenses = sum(float(e.amount) for e in current_month if e.type == 'expense')
        current_income = sum(float(e.amount) for e in current_month if e.type == 'income')
        
        prev_expenses = sum(float(e.amount) for e in prev_month if e.type == 'expense')
        prev_income = sum(float(e.amount) for e in prev_month if e.type == 'income')
        
        # Calculate changes
        expense_change = ((current_expenses - prev_expenses) / prev_expenses * 100) if prev_expenses > 0 else 0
        income_change = ((current_income - prev_income) / prev_income * 100) if prev_income > 0 else 0
        
        # Net savings
        current_net = current_income - current_expenses
        prev_net = prev_income - prev_expenses
        net_change = current_net - prev_net
        
        # Calculate savings rate
        savings_rate = (current_net / current_income * 100) if current_income > 0 else 0
        
        return {
            'total_expenses': current_expenses,
            'total_income': current_income,
            'net_savings': current_net,
            'savings_rate': savings_rate,
            'transaction_count': len(current_month),
            'avg_transaction': current_expenses / len([e for e in current_month if e.type == 'expense']) if any(e.type == 'expense' for e in current_month) else 0,
            'show_income': True,
            'comparison': {
                'expense_change_pct': expense_change,
                'expense_change_amount': current_expenses - prev_expenses,
                'income_change_pct': income_change,
                'income_change_amount': current_income - prev_income,
                'net_change': net_change,
                'prev_month_expenses': prev_expenses,
                'prev_month_income': prev_income
            }
        }
    
    def _analyze_categories(self, user_id: int, month_start: date, month_end: date,
                           prev_month_start: date, prev_month_end: date) -> Dict:
        """Analyze spending by category with comparisons"""
        # Current month by category
        current_categories = self.db.query(
            Category.name,
            func.sum(Entry.amount).label('total'),
            func.count(Entry.id).label('count')
        ).join(Entry, Category.id == Entry.category_id).filter(
            Entry.user_id == user_id,
            Entry.date >= month_start,
            Entry.date <= month_end,
            Entry.type == 'expense'
        ).group_by(Category.name).all()
        
        # Previous month by category
        prev_categories = self.db.query(
            Category.name,
            func.sum(Entry.amount).label('total')
        ).join(Entry, Category.id == Entry.category_id).filter(
            Entry.user_id == user_id,
            Entry.date >= prev_month_start,
            Entry.date <= prev_month_end,
            Entry.type == 'expense'
        ).group_by(Category.name).all()
        
        # Convert to dictionaries for easier comparison
        prev_dict = {cat.name: float(cat.total) for cat in prev_categories}
        
        # Analyze changes
        increased_spending = []
        decreased_spending = []
        new_spending = []
        
        for cat in current_categories:
            amount = float(cat.total)
            prev_amount = prev_dict.get(cat.name, 0)
            
            if prev_amount == 0:
                new_spending.append({
                    'category': cat.name,
                    'amount': amount,
                    'count': cat.count
                })
            else:
                change_pct = ((amount - prev_amount) / prev_amount * 100)
                change_amount = amount - prev_amount
                
                if change_pct > 10:
                    increased_spending.append({
                        'name': cat.name,
                        'amount': amount,
                        'change_pct': change_pct,
                        'change_amount': change_amount
                    })
                elif change_pct < -10:
                    decreased_spending.append({
                        'name': cat.name,
                        'amount': amount,
                        'change_pct': change_pct,
                        'change_amount': change_amount
                    })
        
        # Sort by change amount
        increased_spending.sort(key=lambda x: x['change_amount'], reverse=True)
        decreased_spending.sort(key=lambda x: x['change_amount'])
        
        # Top spending category
        top_category = None
        if current_categories:
            top_cat = max(current_categories, key=lambda x: x.total)
            top_category = {
                'name': top_cat.name,
                'amount': float(top_cat.total),
                'count': top_cat.count
            }
        
        return {
            'increased_spending': increased_spending[:3],
            'decreased_spending': decreased_spending[:3],
            'new_spending_categories': new_spending[:3],
            'top_category': top_category,
            'total_categories': len(current_categories)
        }
    
    def _daily_breakdown(self, user_id: int, month_start: date, month_end: date) -> List[Dict]:
        """Get daily breakdown for the month"""
        daily_data = []
        current_date = month_start
        
        while current_date <= month_end:
            day_entries = self.db.query(Entry).filter(
                Entry.user_id == user_id,
                Entry.date == current_date
            ).all()
            
            expenses = sum(float(e.amount) for e in day_entries if e.type == 'expense')
            income = sum(float(e.amount) for e in day_entries if e.type == 'income')
            
            daily_data.append({
                'date': current_date.isoformat(),
                'day_name': current_date.strftime('%A'),
                'expenses': expenses,
                'income': income,
                'net': income - expenses,
                'transaction_count': len(day_entries),
                'is_weekend': current_date.weekday() >= 5
            })
            
            current_date += timedelta(days=1)
        
        return daily_data
    
    def _generate_insights(self, user_id: int, month_start: date, month_end: date,
                          prev_month_start: date, prev_month_end: date) -> List[str]:
        """Generate natural language insights for monthly report"""
        insights = []
        
        summary = self._generate_summary(user_id, month_start, month_end, prev_month_start, prev_month_end)
        category_analysis = self._analyze_categories(user_id, month_start, month_end, prev_month_start, prev_month_end)
        
        # Expense trend insight
        expense_change = summary['comparison']['expense_change_pct']
        if abs(expense_change) >= 15:
            if expense_change > 0:
                insights.append(f"Your expenses increased by {abs(expense_change):.1f}% compared to last month ({summary['comparison']['expense_change_amount']:.2f} more).")
            else:
                insights.append(f"Great job! Your expenses decreased by {abs(expense_change):.1f}% compared to last month ({abs(summary['comparison']['expense_change_amount']):.2f} saved).")
        else:
            insights.append(f"Your expenses remained stable this month (only {abs(expense_change):.1f}% change).")
        
        # Income trend insight
        income_change = summary['comparison']['income_change_pct']
        if abs(income_change) >= 10:
            if income_change > 0:
                insights.append(f"Your income increased by {abs(income_change):.1f}% compared to last month ({summary['comparison']['income_change_amount']:.2f} more).")
            else:
                insights.append(f"Your income decreased by {abs(income_change):.1f}% compared to last month ({abs(summary['comparison']['income_change_amount']):.2f} less).")
        
        # Savings rate insight
        savings_rate = summary['savings_rate']
        if savings_rate > 20:
            insights.append(f"Excellent savings rate of {savings_rate:.1f}%! You're saving {summary['net_savings']:.2f} per month.")
        elif savings_rate > 10:
            insights.append(f"Good savings rate of {savings_rate:.1f}%. You saved {summary['net_savings']:.2f} this month.")
        elif savings_rate < 0:
            insights.append(f"You spent {abs(summary['net_savings']):.2f} more than you earned this month.")
        
        # Category insights
        if category_analysis['top_category']:
            top_cat = category_analysis['top_category']
            insights.append(f"Your biggest expense category was {top_cat['name']} with {top_cat['amount']:.2f} ({top_cat['count']} transactions).")
        
        if category_analysis['increased_spending']:
            top_increase = category_analysis['increased_spending'][0]
            insights.append(f"You spent {top_increase['change_pct']:.0f}% more on {top_increase['name']} this month ({top_increase['change_amount']:.2f} increase).")
        
        # Total spending insight
        insights.append(f"Total spending this month: {summary['total_expenses']:.2f} across {summary['transaction_count']} transactions.")
        
        return insights
    
    def _detect_achievements(self, user_id: int, month_start: date, month_end: date) -> List[Dict]:
        """Detect monthly achievements"""
        achievements = []
        
        summary = self._generate_summary(user_id, month_start, month_end, 
                                       month_start - timedelta(days=30), month_start - timedelta(days=1))
        
        # Savings achievement
        savings_rate = summary['savings_rate']
        if savings_rate >= 20:
            achievements.append({
                'type': 'high_savings',
                'title': 'Savings Champion!',
                'description': f'You saved {savings_rate:.1f}% of your income this month!',
                'points': 100
            })
        elif savings_rate >= 10:
            achievements.append({
                'type': 'good_savings',
                'title': 'Good Saver',
                'description': f'You saved {savings_rate:.1f}% of your income this month.',
                'points': 50
            })
        
        # Expense control achievement
        if summary['total_expenses'] < 1000:  # Low spending threshold
            achievements.append({
                'type': 'low_spending',
                'title': 'Frugal Month',
                'description': f'You kept expenses under 1000 this month!',
                'points': 75
            })
        
        return achievements
    
    def _generate_recommendations(self, user_id: int, month_start: date, month_end: date) -> List[Dict]:
        """Generate monthly recommendations"""
        recommendations = []
        
        summary = self._generate_summary(user_id, month_start, month_end, 
                                       month_start - timedelta(days=30), month_start - timedelta(days=1))
        category_analysis = self._analyze_categories(user_id, month_start, month_end,
                                                   month_start - timedelta(days=30), month_start - timedelta(days=1))
        
        # Savings recommendations
        savings_rate = summary['savings_rate']
        if savings_rate < 10:
            recommendations.append({
                'type': 'increase_savings',
                'priority': 'high',
                'title': 'Increase your savings rate',
                'description': f'Your savings rate is {savings_rate:.1f}%. Aim for at least 20%.',
                'action': 'budget_plan'
            })
        
        # Top spending category recommendation
        if category_analysis['top_category'] and summary['total_income'] > 0:
            top_cat = category_analysis['top_category']
            if top_cat['amount'] > summary['total_income'] * 0.3:  # More than 30% of income
                income_percentage = (top_cat['amount'] / summary['total_income']) * 100
                recommendations.append({
                    'type': 'reduce_spending',
                    'priority': 'high',
                    'category': top_cat['name'],
                    'title': f'Consider reducing {top_cat["name"]} spending',
                    'description': f'You spent {top_cat["amount"]:.2f} on {top_cat["name"]} this month ({income_percentage:.1f}% of income).',
                    'potential_savings': top_cat['amount'] * 0.15
                })
        elif category_analysis['top_category'] and summary['total_income'] == 0:
            # Handle case where there's no income data
            top_cat = category_analysis['top_category']
            recommendations.append({
                'type': 'track_income',
                'priority': 'high',
                'category': top_cat['name'],
                'title': 'Start tracking your income',
                'description': f'You spent {top_cat["amount"]:.2f} on {top_cat["name"]} this month. Consider adding income entries for better financial insights.',
                'action': 'add_income'
            })
        
        return recommendations

"""
Chart Configuration Service - Phase 1.3

Generates Chart.js compatible data structures for frontend charts.
Provides reusable chart configurations for various visualization types.
"""

from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import logging

from app.models.entry import Entry
from app.models.category import Category
from app.models.user import User

logger = logging.getLogger(__name__)


class ChartConfigService:
    """Generate Chart.js compatible data structures"""

    # Color palette for charts
    COLORS = [
        '#ef4444',  # Red
        '#3b82f6',  # Blue
        '#10b981',  # Green
        '#f59e0b',  # Amber
        '#8b5cf6',  # Purple
        '#ec4899',  # Pink
        '#14b8a6',  # Teal
        '#f97316',  # Orange
        '#6366f1',  # Indigo
        '#84cc16',  # Lime
    ]

    @staticmethod
    def category_pie_data(db: Session, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None, entry_type: str = 'expense') -> Dict:
        """
        Generate pie chart data grouped by category

        Args:
            db: Database session
            user_id: User ID
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            entry_type: 'expense' or 'income'

        Returns:
            Chart.js compatible pie chart data
        """
        # Build query
        query = db.query(
            Category.name,
            Category.color,
            db.func.sum(Entry.amount).label('total')
        ).join(
            Entry, Entry.category_id == Category.id
        ).filter(
            Entry.user_id == user_id,
            Entry.type == entry_type
        )

        # Apply date filters
        if start_date:
            query = query.filter(Entry.date >= start_date)
        if end_date:
            query = query.filter(Entry.date <= end_date)

        # Group and order
        results = query.group_by(Category.id, Category.name, Category.color).order_by(
            db.func.sum(Entry.amount).desc()
        ).all()

        if not results:
            return {
                'labels': [],
                'datasets': [{
                    'data': [],
                    'backgroundColor': [],
                    'borderWidth': 0
                }],
                'total': 0
            }

        labels = []
        amounts = []
        colors = []
        total = 0

        for category_name, category_color, amount in results:
            labels.append(category_name)
            amounts.append(float(amount))
            colors.append(category_color or ChartConfigService.COLORS[len(colors) % len(ChartConfigService.COLORS)])
            total += float(amount)

        return {
            'labels': labels,
            'datasets': [{
                'data': amounts,
                'backgroundColor': colors,
                'borderWidth': 0
            }],
            'total': total
        }

    @staticmethod
    def daily_trend_data(db: Session, user_id: int, start_date: date, end_date: date) -> Dict:
        """
        Generate line chart data for daily income/expense trends

        Args:
            db: Database session
            user_id: User ID
            start_date: Start date
            end_date: End date

        Returns:
            Chart.js compatible line chart data
        """
        # Get daily totals for expenses
        expense_query = db.query(
            Entry.date,
            db.func.sum(Entry.amount).label('total')
        ).filter(
            Entry.user_id == user_id,
            Entry.type == 'expense',
            Entry.date >= start_date,
            Entry.date <= end_date
        ).group_by(Entry.date).all()

        # Get daily totals for income
        income_query = db.query(
            Entry.date,
            db.func.sum(Entry.amount).label('total')
        ).filter(
            Entry.user_id == user_id,
            Entry.type == 'income',
            Entry.date >= start_date,
            Entry.date <= end_date
        ).group_by(Entry.date).all()

        # Create date-to-amount maps
        expense_map = {d: float(total) for d, total in expense_query}
        income_map = {d: float(total) for d, total in income_query}

        # Generate all dates in range
        labels = []
        expense_data = []
        income_data = []

        current_date = start_date
        while current_date <= end_date:
            labels.append(current_date.isoformat())
            expense_data.append(expense_map.get(current_date, 0))
            income_data.append(income_map.get(current_date, 0))
            current_date += timedelta(days=1)

        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Expenses',
                    'data': expense_data,
                    'borderColor': '#ef4444',
                    'backgroundColor': 'rgba(239, 68, 68, 0.1)',
                    'tension': 0.4,
                    'fill': True
                },
                {
                    'label': 'Income',
                    'data': income_data,
                    'borderColor': '#10b981',
                    'backgroundColor': 'rgba(16, 185, 129, 0.1)',
                    'tension': 0.4,
                    'fill': True
                }
            ]
        }

    @staticmethod
    def category_bar_data(db: Session, user_id: int, start_date: date, end_date: date, limit: int = 10) -> Dict:
        """
        Generate bar chart data for top categories

        Args:
            db: Database session
            user_id: User ID
            start_date: Start date
            end_date: End date
            limit: Number of top categories to show

        Returns:
            Chart.js compatible bar chart data
        """
        # Get top expense categories
        results = db.query(
            Category.name,
            db.func.sum(Entry.amount).label('total')
        ).join(
            Entry, Entry.category_id == Category.id
        ).filter(
            Entry.user_id == user_id,
            Entry.type == 'expense',
            Entry.date >= start_date,
            Entry.date <= end_date
        ).group_by(Category.id, Category.name).order_by(
            db.func.sum(Entry.amount).desc()
        ).limit(limit).all()

        if not results:
            return {
                'labels': [],
                'datasets': [{
                    'label': 'Expenses',
                    'data': [],
                    'backgroundColor': '#ef4444'
                }]
            }

        labels = [name for name, _ in results]
        amounts = [float(total) for _, total in results]

        return {
            'labels': labels,
            'datasets': [{
                'label': 'Expenses',
                'data': amounts,
                'backgroundColor': '#ef4444'
            }]
        }

    @staticmethod
    def category_comparison_data(
        db: Session,
        user_id: int,
        current_start: date,
        current_end: date,
        previous_start: date,
        previous_end: date
    ) -> Dict:
        """
        Generate comparison bar chart for two periods

        Args:
            db: Database session
            user_id: User ID
            current_start: Current period start date
            current_end: Current period end date
            previous_start: Previous period start date
            previous_end: Previous period end date

        Returns:
            Chart.js compatible grouped bar chart data
        """
        # Get current period totals by category
        current_query = db.query(
            Category.name,
            db.func.sum(Entry.amount).label('total')
        ).join(
            Entry, Entry.category_id == Category.id
        ).filter(
            Entry.user_id == user_id,
            Entry.type == 'expense',
            Entry.date >= current_start,
            Entry.date <= current_end
        ).group_by(Category.id, Category.name).all()

        # Get previous period totals by category
        previous_query = db.query(
            Category.name,
            db.func.sum(Entry.amount).label('total')
        ).join(
            Entry, Entry.category_id == Category.id
        ).filter(
            Entry.user_id == user_id,
            Entry.type == 'expense',
            Entry.date >= previous_start,
            Entry.date <= previous_end
        ).group_by(Category.id, Category.name).all()

        # Create maps
        current_map = {name: float(total) for name, total in current_query}
        previous_map = {name: float(total) for name, total in previous_query}

        # Get all unique categories
        all_categories = sorted(set(current_map.keys()) | set(previous_map.keys()))

        if not all_categories:
            return {
                'labels': [],
                'datasets': []
            }

        # Build datasets
        current_data = [current_map.get(cat, 0) for cat in all_categories]
        previous_data = [previous_map.get(cat, 0) for cat in all_categories]

        return {
            'labels': all_categories,
            'datasets': [
                {
                    'label': 'Current Period',
                    'data': current_data,
                    'backgroundColor': '#3b82f6'
                },
                {
                    'label': 'Previous Period',
                    'data': previous_data,
                    'backgroundColor': '#94a3b8'
                }
            ]
        }

    @staticmethod
    def monthly_summary_data(db: Session, user_id: int, months: int = 6) -> Dict:
        """
        Generate monthly income vs expense comparison

        Args:
            db: Database session
            user_id: User ID
            months: Number of months to show

        Returns:
            Chart.js compatible grouped bar chart data
        """
        end_date = date.today()
        start_date = end_date.replace(day=1) - timedelta(days=1)  # Last day of previous month

        # Go back N months
        for _ in range(months - 1):
            start_date = start_date.replace(day=1) - timedelta(days=1)

        start_date = start_date.replace(day=1)  # First day of oldest month

        # Get monthly totals
        results = db.query(
            db.func.date_trunc('month', Entry.date).label('month'),
            Entry.type,
            db.func.sum(Entry.amount).label('total')
        ).filter(
            Entry.user_id == user_id,
            Entry.date >= start_date,
            Entry.date <= end_date
        ).group_by(
            db.func.date_trunc('month', Entry.date),
            Entry.type
        ).order_by(
            db.func.date_trunc('month', Entry.date)
        ).all()

        # Organize data
        monthly_data = defaultdict(lambda: {'income': 0, 'expense': 0})

        for month, entry_type, total in results:
            month_key = month.strftime('%Y-%m')
            monthly_data[month_key][entry_type] = float(total)

        # Generate labels for all months
        labels = []
        income_data = []
        expense_data = []

        current = start_date
        while current <= end_date:
            month_key = current.strftime('%Y-%m')
            month_label = current.strftime('%b %Y')

            labels.append(month_label)
            income_data.append(monthly_data[month_key]['income'])
            expense_data.append(monthly_data[month_key]['expense'])

            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Income',
                    'data': income_data,
                    'backgroundColor': '#10b981'
                },
                {
                    'label': 'Expenses',
                    'data': expense_data,
                    'backgroundColor': '#ef4444'
                }
            ]
        }

    @staticmethod
    def savings_rate_trend(db: Session, user_id: int, months: int = 12) -> Dict:
        """
        Generate savings rate trend over time

        Args:
            db: Database session
            user_id: User ID
            months: Number of months to analyze

        Returns:
            Chart.js compatible line chart data
        """
        end_date = date.today()
        start_date = end_date.replace(day=1) - timedelta(days=1)

        for _ in range(months - 1):
            start_date = start_date.replace(day=1) - timedelta(days=1)

        start_date = start_date.replace(day=1)

        # Get monthly totals by type
        results = db.query(
            db.func.date_trunc('month', Entry.date).label('month'),
            Entry.type,
            db.func.sum(Entry.amount).label('total')
        ).filter(
            Entry.user_id == user_id,
            Entry.date >= start_date,
            Entry.date <= end_date
        ).group_by(
            db.func.date_trunc('month', Entry.date),
            Entry.type
        ).order_by(
            db.func.date_trunc('month', Entry.date)
        ).all()

        # Calculate savings rate per month
        monthly_data = defaultdict(lambda: {'income': 0, 'expense': 0})

        for month, entry_type, total in results:
            month_key = month.strftime('%Y-%m')
            monthly_data[month_key][entry_type] = float(total)

        labels = []
        savings_rates = []

        current = start_date
        while current <= end_date:
            month_key = current.strftime('%Y-%m')
            month_label = current.strftime('%b %Y')

            income = monthly_data[month_key]['income']
            expense = monthly_data[month_key]['expense']

            if income > 0:
                savings_rate = ((income - expense) / income) * 100
            else:
                savings_rate = 0

            labels.append(month_label)
            savings_rates.append(round(savings_rate, 2))

            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

        return {
            'labels': labels,
            'datasets': [{
                'label': 'Savings Rate (%)',
                'data': savings_rates,
                'borderColor': '#8b5cf6',
                'backgroundColor': 'rgba(139, 92, 246, 0.1)',
                'tension': 0.4,
                'fill': True
            }]
        }

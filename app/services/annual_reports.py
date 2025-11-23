"""
Annual Reports Service
Provides comprehensive annual financial analysis and insights
"""

from datetime import date, datetime
from typing import Dict, List, Optional
from sqlalchemy import func, extract
from sqlalchemy.orm import Session
from decimal import Decimal

from app.models.entry import Entry, EntryType
from app.models.category import Category
from app.models.financial_goal import FinancialGoal


def get_annual_summary(db: Session, user_id: int, year: int) -> Dict:
    """
    Get comprehensive annual financial summary with all metrics

    Args:
        db: Database session
        user_id: User ID
        year: Year to analyze

    Returns:
        Dict containing annual summary data
    """
    # Get all entries for the year
    entries = db.query(Entry).filter(
        Entry.user_id == user_id,
        extract('year', Entry.date) == year
    ).all()

    total_income = sum(float(e.amount) for e in entries if e.type == EntryType.INCOME)
    total_expense = sum(float(e.amount) for e in entries if e.type == EntryType.EXPENSE)
    balance = total_income - total_expense
    savings_rate = (balance / total_income * 100) if total_income > 0 else 0

    return {
        'year': year,
        'total_income': round(total_income, 2),
        'total_expense': round(total_expense, 2),
        'balance': round(balance, 2),
        'savings_rate': round(savings_rate, 2),
        'entry_count': len(entries),
        'income_count': sum(1 for e in entries if e.type == EntryType.INCOME),
        'expense_count': sum(1 for e in entries if e.type == EntryType.EXPENSE)
    }


def get_year_over_year_comparison(db: Session, user_id: int, year: int) -> Dict:
    """
    Compare current year with previous years

    Args:
        db: Database session
        user_id: User ID
        year: Current year to compare

    Returns:
        Dict with year-over-year comparison data
    """
    current_year = get_annual_summary(db, user_id, year)
    previous_year = get_annual_summary(db, user_id, year - 1)

    # Calculate changes
    income_change = current_year['total_income'] - previous_year['total_income']
    expense_change = current_year['total_expense'] - previous_year['total_expense']
    balance_change = current_year['balance'] - previous_year['balance']

    # Calculate percentage changes
    income_change_pct = (income_change / previous_year['total_income'] * 100) if previous_year['total_income'] > 0 else 0
    expense_change_pct = (expense_change / previous_year['total_expense'] * 100) if previous_year['total_expense'] > 0 else 0

    return {
        'current_year': current_year,
        'previous_year': previous_year,
        'changes': {
            'income': {
                'amount': round(income_change, 2),
                'percentage': round(income_change_pct, 2),
                'trend': 'up' if income_change > 0 else 'down' if income_change < 0 else 'stable'
            },
            'expense': {
                'amount': round(expense_change, 2),
                'percentage': round(expense_change_pct, 2),
                'trend': 'up' if expense_change > 0 else 'down' if expense_change < 0 else 'stable'
            },
            'balance': {
                'amount': round(balance_change, 2),
                'trend': 'up' if balance_change > 0 else 'down' if balance_change < 0 else 'stable'
            }
        }
    }


def get_monthly_breakdown(db: Session, user_id: int, year: int) -> Dict:
    """
    Get monthly breakdown of income and expenses for the year

    Args:
        db: Database session
        user_id: User ID
        year: Year to analyze

    Returns:
        Dict with monthly data
    """
    monthly_data = {}

    for month in range(1, 13):
        entries = db.query(Entry).filter(
            Entry.user_id == user_id,
            extract('year', Entry.date) == year,
            extract('month', Entry.date) == month
        ).all()

        income = sum(float(e.amount) for e in entries if e.type == EntryType.INCOME)
        expense = sum(float(e.amount) for e in entries if e.type == EntryType.EXPENSE)
        balance = income - expense

        month_name = date(year, month, 1).strftime('%B')

        monthly_data[month] = {
            'month': month,
            'month_name': month_name,
            'income': round(income, 2),
            'expense': round(expense, 2),
            'balance': round(balance, 2),
            'savings_rate': round((balance / income * 100) if income > 0 else 0, 2),
            'entry_count': len(entries)
        }

    return monthly_data


def get_seasonal_analysis(db: Session, user_id: int, year: int) -> Dict:
    """
    Analyze spending patterns by season (quarters)

    Args:
        db: Database session
        user_id: User ID
        year: Year to analyze

    Returns:
        Dict with seasonal analysis
    """
    seasons = {
        'Q1': {'months': [1, 2, 3], 'name': 'Q1 (Jan-Mar)'},
        'Q2': {'months': [4, 5, 6], 'name': 'Q2 (Apr-Jun)'},
        'Q3': {'months': [7, 8, 9], 'name': 'Q3 (Jul-Sep)'},
        'Q4': {'months': [10, 11, 12], 'name': 'Q4 (Oct-Dec)'}
    }

    seasonal_data = {}

    for quarter, info in seasons.items():
        entries = db.query(Entry).filter(
            Entry.user_id == user_id,
            extract('year', Entry.date) == year,
            extract('month', Entry.date).in_(info['months'])
        ).all()

        income = sum(float(e.amount) for e in entries if e.type == EntryType.INCOME)
        expense = sum(float(e.amount) for e in entries if e.type == EntryType.EXPENSE)

        seasonal_data[quarter] = {
            'name': info['name'],
            'income': round(income, 2),
            'expense': round(expense, 2),
            'balance': round(income - expense, 2),
            'entry_count': len(entries)
        }

    # Find highest and lowest spending quarters
    quarters_by_expense = sorted(seasonal_data.items(), key=lambda x: x[1]['expense'], reverse=True)

    return {
        'quarters': seasonal_data,
        'highest_spending_quarter': quarters_by_expense[0][0] if quarters_by_expense else None,
        'lowest_spending_quarter': quarters_by_expense[-1][0] if quarters_by_expense else None
    }


def get_category_analysis(db: Session, user_id: int, year: int) -> Dict:
    """
    Analyze spending by category for the year

    Args:
        db: Database session
        user_id: User ID
        year: Year to analyze

    Returns:
        Dict with category breakdown
    """
    # Get all expenses for the year grouped by category
    results = db.query(
        Category.name,
        func.sum(Entry.amount).label('total'),
        func.count(Entry.id).label('count')
    ).join(
        Entry, Entry.category_id == Category.id
    ).filter(
        Entry.user_id == user_id,
        Entry.type == EntryType.EXPENSE,
        extract('year', Entry.date) == year
    ).group_by(
        Category.name
    ).order_by(
        func.sum(Entry.amount).desc()
    ).all()

    total_expense = sum(float(r.total) for r in results)

    categories = []
    for result in results:
        amount = float(result.total)
        percentage = (amount / total_expense * 100) if total_expense > 0 else 0

        categories.append({
            'name': result.name,
            'amount': round(amount, 2),
            'percentage': round(percentage, 2),
            'count': result.count
        })

    # Get top 10 categories
    top_10 = categories[:10]

    return {
        'categories': categories,
        'top_10': top_10,
        'total_categories': len(categories),
        'total_expense': round(total_expense, 2)
    }


def get_annual_achievements(db: Session, user_id: int, year: int) -> Dict:
    """
    Calculate financial achievements and milestones for the year

    Args:
        db: Database session
        user_id: User ID
        year: Year to analyze

    Returns:
        Dict with achievements
    """
    monthly_data = get_monthly_breakdown(db, user_id, year)

    # Find best saving month
    months_with_data = [m for m in monthly_data.values() if m['balance'] > 0]
    best_saving_month = max(months_with_data, key=lambda x: x['balance']) if months_with_data else None

    # Find highest income month
    highest_income_month = max(monthly_data.values(), key=lambda x: x['income'])

    # Find lowest expense month (excluding months with no expenses)
    months_with_expenses = [m for m in monthly_data.values() if m['expense'] > 0]
    lowest_expense_month = min(months_with_expenses, key=lambda x: x['expense']) if months_with_expenses else None

    # Count days with entries
    entries = db.query(func.count(func.distinct(Entry.date))).filter(
        Entry.user_id == user_id,
        extract('year', Entry.date) == year
    ).scalar()

    # Get completed goals for the year
    completed_goals = db.query(FinancialGoal).filter(
        FinancialGoal.user_id == user_id,
        FinancialGoal.is_completed == True,
        extract('year', FinancialGoal.target_date) == year
    ).count()

    # Calculate consecutive saving months
    consecutive_months = 0
    max_streak = 0
    for month in range(1, 13):
        if monthly_data[month]['balance'] > 0:
            consecutive_months += 1
            max_streak = max(max_streak, consecutive_months)
        else:
            consecutive_months = 0

    return {
        'best_saving_month': best_saving_month,
        'highest_income_month': highest_income_month,
        'lowest_expense_month': lowest_expense_month,
        'days_with_entries': entries or 0,
        'completed_goals': completed_goals,
        'longest_saving_streak': max_streak,
        'months_with_positive_balance': len(months_with_data)
    }


def get_comprehensive_annual_report(db: Session, user_id: int, year: int) -> Dict:
    """
    Generate comprehensive annual report with all analyses

    Args:
        db: Database session
        user_id: User ID
        year: Year to analyze

    Returns:
        Dict with complete annual report
    """
    return {
        'summary': get_annual_summary(db, user_id, year),
        'year_over_year': get_year_over_year_comparison(db, user_id, year),
        'monthly_breakdown': get_monthly_breakdown(db, user_id, year),
        'seasonal_analysis': get_seasonal_analysis(db, user_id, year),
        'category_analysis': get_category_analysis(db, user_id, year),
        'achievements': get_annual_achievements(db, user_id, year)
    }

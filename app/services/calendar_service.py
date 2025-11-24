"""
Calendar service for aggregating financial entries by date and showing upcoming bills
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from app.models.entry import Entry, EntryType
from app.models.category import Category
from app.services.recurring_payment_service import RecurringPaymentService


def get_calendar_data(
    db: Session,
    user_id: int,
    year: int,
    month: int
) -> Dict:
    """
    Get calendar data for a specific month and year.

    Returns aggregated entry data for each day in the month:
    - Total income for each day
    - Total expenses for each day
    - Net balance for each day
    - Entry count
    - List of entries with category info

    Args:
        db: Database session
        user_id: User ID to filter entries
        year: Year (e.g., 2025)
        month: Month (1-12)

    Returns:
        Dict with year, month, and dates data
    """

    # Get first and last day of month
    first_day = date(year, month, 1)

    # Calculate last day of month
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    # Query all entries for this month
    entries = db.query(Entry).filter(
        Entry.user_id == user_id,
        Entry.date >= first_day,
        Entry.date <= last_day
    ).order_by(Entry.date.desc(), Entry.id.desc()).all()

    # Aggregate entries by date
    dates_data = {}

    for entry in entries:
        entry_date = entry.date.isoformat()

        # Initialize date if not exists
        if entry_date not in dates_data:
            dates_data[entry_date] = {
                'income_total': 0.0,
                'expense_total': 0.0,
                'net': 0.0,
                'entry_count': 0,
                'entries': []
            }

        # Get category info
        category_name = entry.category.name if entry.category else 'Uncategorized'
        # Categories don't have icons, use a generic icon based on type
        if entry.type == EntryType.INCOME:
            category_icon = '💰'
        else:
            category_icon = '💸'

        # Add to appropriate total
        amount = float(entry.amount)
        if entry.type == EntryType.INCOME:
            dates_data[entry_date]['income_total'] += amount
        else:
            dates_data[entry_date]['expense_total'] += amount

        # Update net (income - expense)
        dates_data[entry_date]['net'] = (
            dates_data[entry_date]['income_total'] -
            dates_data[entry_date]['expense_total']
        )

        # Increment count
        dates_data[entry_date]['entry_count'] += 1

        # Add entry details
        dates_data[entry_date]['entries'].append({
            'id': entry.id,
            'type': entry.type,
            'amount': amount,
            'currency_code': entry.currency_code,
            'category_name': category_name,
            'category_icon': category_icon,
            'note': entry.note,
            'description': entry.description,
        })

    # Round all monetary values to 2 decimal places
    for date_key in dates_data:
        dates_data[date_key]['income_total'] = round(dates_data[date_key]['income_total'], 2)
        dates_data[date_key]['expense_total'] = round(dates_data[date_key]['expense_total'], 2)
        dates_data[date_key]['net'] = round(dates_data[date_key]['net'], 2)

    # Add upcoming bills & subscriptions to calendar
    recurring_service = RecurringPaymentService(db)
    payments = recurring_service.get_user_recurring_payments(user_id, include_inactive=False)

    for payment in payments:
        next_due = recurring_service.calculate_next_due_date(payment, first_day)

        # If due date falls within this month, add it to the calendar
        if next_due and first_day <= next_due <= last_day:
            due_date_str = next_due.isoformat()

            # Initialize date if not exists
            if due_date_str not in dates_data:
                dates_data[due_date_str] = {
                    'income_total': 0.0,
                    'expense_total': 0.0,
                    'net': 0.0,
                    'entry_count': 0,
                    'entries': []
                }

            # Add bill/subscription as a special entry type
            dates_data[due_date_str]['entries'].append({
                'id': f'bill_{payment.id}',
                'type': 'bill',  # Special type for bills
                'amount': float(payment.amount),
                'currency_code': payment.currency_code,
                'category_name': payment.category.name if payment.category else 'Uncategorized',
                'category_icon': '📅',  # Calendar icon for bills
                'note': payment.name,
                'description': f"Due: {payment.name}",
                'is_recurring': True,
                'frequency': payment.frequency.value
            })

    return {
        'year': year,
        'month': month,
        'month_name': first_day.strftime('%B'),
        'first_day': first_day.isoformat(),
        'last_day': last_day.isoformat(),
        'dates': dates_data
    }


def get_month_summary(
    db: Session,
    user_id: int,
    year: int,
    month: int
) -> Dict:
    """
    Get summary statistics for a specific month.

    Args:
        db: Database session
        user_id: User ID
        year: Year
        month: Month (1-12)

    Returns:
        Dict with total income, expenses, and net for the month
    """

    # Get first and last day of month
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    # Get all entries for the month
    entries = db.query(Entry).filter(
        Entry.user_id == user_id,
        Entry.date >= first_day,
        Entry.date <= last_day
    ).all()

    total_income = 0.0
    total_expense = 0.0

    for entry in entries:
        amount = float(entry.amount)
        if entry.type == EntryType.INCOME:
            total_income += amount
        else:
            total_expense += amount

    return {
        'total_income': round(total_income, 2),
        'total_expense': round(total_expense, 2),
        'net': round(total_income - total_expense, 2),
        'entry_count': len(entries)
    }


def get_available_months(
    db: Session,
    user_id: int
) -> List[Dict]:
    """
    Get list of months that have entries for the user.
    Useful for month/year navigation dropdown.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        List of dicts with year and month
    """

    # Query distinct year-month combinations
    results = db.query(
        extract('year', Entry.date).label('year'),
        extract('month', Entry.date).label('month')
    ).filter(
        Entry.user_id == user_id
    ).distinct().order_by(
        extract('year', Entry.date).desc(),
        extract('month', Entry.date).desc()
    ).all()

    months = []
    for result in results:
        year = int(result.year)
        month = int(result.month)
        month_name = date(year, month, 1).strftime('%B %Y')

        months.append({
            'year': year,
            'month': month,
            'month_name': month_name,
            'display': month_name
        })

    return months


def get_date_entries(
    db: Session,
    user_id: int,
    target_date: date
) -> Dict:
    """
    Get all entries for a specific date with detailed information.
    Used when user clicks on a specific date.

    Args:
        db: Database session
        user_id: User ID
        target_date: Date to get entries for

    Returns:
        Dict with date info and entries
    """

    # Query entries for this date
    entries = db.query(Entry).filter(
        Entry.user_id == user_id,
        Entry.date == target_date
    ).order_by(Entry.id.desc()).all()

    total_income = 0.0
    total_expense = 0.0
    entry_list = []

    for entry in entries:
        amount = float(entry.amount)

        # Get category info
        category_name = entry.category.name if entry.category else 'Uncategorized'
        # Categories don't have icons, use a generic icon based on type
        if entry.type == EntryType.INCOME:
            category_icon = '💰'
        else:
            category_icon = '💸'

        # Calculate totals
        if entry.type == EntryType.INCOME:
            total_income += amount
        else:
            total_expense += amount

        # Add entry details
        entry_list.append({
            'id': entry.id,
            'type': entry.type,
            'amount': amount,
            'currency_code': entry.currency_code,
            'category_id': entry.category_id,
            'category_name': category_name,
            'category_icon': category_icon,
            'note': entry.note,
            'description': entry.description,
            'date': entry.date.isoformat()
        })

    return {
        'date': target_date.isoformat(),
        'date_display': target_date.strftime('%B %d, %Y'),
        'day_name': target_date.strftime('%A'),
        'total_income': round(total_income, 2),
        'total_expense': round(total_expense, 2),
        'net': round(total_income - total_expense, 2),
        'entry_count': len(entry_list),
        'entries': entry_list
    }

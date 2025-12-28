"""
Chart API Endpoints - Phase 1.3

Provides Chart.js-compatible data for various chart types.
Supports category breakdowns, trends, comparisons, and summaries.
"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from typing import Optional

from app.db.session import get_db
from app.deps import current_user
from app.models.user import User
from app.services.chart_config_service import ChartConfigService


router = APIRouter(prefix="/api/charts", tags=["Charts"])


@router.get("/category-pie")
async def get_category_pie_chart(
    start_date: Optional[date] = Query(None, description="Start date for filtering"),
    end_date: Optional[date] = Query(None, description="End date for filtering"),
    entry_type: str = Query('expense', description="Entry type: 'expense' or 'income'"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get category breakdown as pie chart data

    Returns Chart.js-compatible data for pie/doughnut charts showing
    spending or income distribution across categories.

    Query params:
    - start_date: Filter entries from this date (optional)
    - end_date: Filter entries to this date (optional)
    - entry_type: 'expense' or 'income' (default: 'expense')
    """
    # Default to current month if no dates provided
    if not start_date and not end_date:
        today = date.today()
        start_date = today.replace(day=1)
        end_date = today

    data = ChartConfigService.category_pie_data(
        db, user.id, start_date, end_date, entry_type
    )

    return JSONResponse({
        'success': True,
        'chart_data': data,
        'period': {
            'start': start_date.isoformat() if start_date else None,
            'end': end_date.isoformat() if end_date else None,
            'type': entry_type
        }
    })


@router.get("/daily-trend")
async def get_daily_trend_chart(
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get daily income/expense trend line chart data

    Returns Chart.js-compatible data showing daily income and expense trends.

    Query params:
    - start_date: Start date (default: 30 days ago)
    - end_date: End date (default: today)
    """
    # Default to last 30 days
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    data = ChartConfigService.daily_trend_data(db, user.id, start_date, end_date)

    return JSONResponse({
        'success': True,
        'chart_data': data,
        'period': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat(),
            'days': (end_date - start_date).days + 1
        }
    })


@router.get("/category-bar")
async def get_category_bar_chart(
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    limit: int = Query(10, ge=1, le=20, description="Number of top categories"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get top categories as bar chart data

    Returns Chart.js-compatible data showing top spending categories.

    Query params:
    - start_date: Filter entries from this date (default: current month start)
    - end_date: Filter entries to this date (default: today)
    - limit: Number of top categories to show (1-20, default: 10)
    """
    # Default to current month
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date.replace(day=1)

    data = ChartConfigService.category_bar_data(
        db, user.id, start_date, end_date, limit
    )

    return JSONResponse({
        'success': True,
        'chart_data': data,
        'period': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        }
    })


@router.get("/category-comparison")
async def get_category_comparison_chart(
    current_start: date = Query(..., description="Current period start date"),
    current_end: date = Query(..., description="Current period end date"),
    previous_start: date = Query(..., description="Previous period start date"),
    previous_end: date = Query(..., description="Previous period end date"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get category comparison between two periods

    Returns Chart.js-compatible grouped bar chart data comparing
    spending across categories for two time periods.

    Query params:
    - current_start: Current period start date (required)
    - current_end: Current period end date (required)
    - previous_start: Previous period start date (required)
    - previous_end: Previous period end date (required)
    """
    data = ChartConfigService.category_comparison_data(
        db, user.id,
        current_start, current_end,
        previous_start, previous_end
    )

    return JSONResponse({
        'success': True,
        'chart_data': data,
        'periods': {
            'current': {
                'start': current_start.isoformat(),
                'end': current_end.isoformat()
            },
            'previous': {
                'start': previous_start.isoformat(),
                'end': previous_end.isoformat()
            }
        }
    })


@router.get("/monthly-summary")
async def get_monthly_summary_chart(
    months: int = Query(6, ge=1, le=24, description="Number of months to show"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get monthly income vs expense summary

    Returns Chart.js-compatible grouped bar chart data showing
    monthly income and expense comparison.

    Query params:
    - months: Number of months to include (1-24, default: 6)
    """
    data = ChartConfigService.monthly_summary_data(db, user.id, months)

    return JSONResponse({
        'success': True,
        'chart_data': data,
        'months': months
    })


@router.get("/savings-rate-trend")
async def get_savings_rate_trend_chart(
    months: int = Query(12, ge=1, le=24, description="Number of months to show"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get savings rate trend over time

    Returns Chart.js-compatible line chart data showing
    monthly savings rate percentage.

    Query params:
    - months: Number of months to analyze (1-24, default: 12)
    """
    data = ChartConfigService.savings_rate_trend(db, user.id, months)

    return JSONResponse({
        'success': True,
        'chart_data': data,
        'months': months
    })


@router.get("/this-month-vs-last-month")
async def get_this_month_vs_last_month_chart(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Quick comparison: this month vs last month

    Convenience endpoint that returns a comparison chart
    for the current month vs the previous month.
    """
    today = date.today()

    # Current month
    current_start = today.replace(day=1)
    current_end = today

    # Previous month
    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end.replace(day=1)

    data = ChartConfigService.category_comparison_data(
        db, user.id,
        current_start, current_end,
        previous_start, previous_end
    )

    return JSONResponse({
        'success': True,
        'chart_data': data,
        'periods': {
            'current': {
                'label': 'This Month',
                'start': current_start.isoformat(),
                'end': current_end.isoformat()
            },
            'previous': {
                'label': 'Last Month',
                'start': previous_start.isoformat(),
                'end': previous_end.isoformat()
            }
        }
    })


@router.get("/spending-by-weekday")
async def get_spending_by_weekday_chart(
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get average spending by day of week

    Returns Chart.js-compatible bar chart showing which days
    of the week have highest spending.

    Query params:
    - start_date: Start date (default: 90 days ago)
    - end_date: End date (default: today)
    """
    from app.models.entry import Entry

    # Default to last 90 days
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=90)

    # Get all expense entries
    entries = db.query(Entry).filter(
        Entry.user_id == user.id,
        Entry.type == 'expense',
        Entry.date >= start_date,
        Entry.date <= end_date
    ).all()

    # Group by weekday
    weekday_totals = [0.0] * 7  # Monday to Sunday
    weekday_counts = [0] * 7

    for entry in entries:
        weekday = entry.date.weekday()  # 0 = Monday, 6 = Sunday
        weekday_totals[weekday] += float(entry.amount)
        weekday_counts[weekday] += 1

    # Calculate averages
    weekday_averages = [
        round(total / count, 2) if count > 0 else 0
        for total, count in zip(weekday_totals, weekday_counts)
    ]

    weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    data = {
        'labels': weekday_names,
        'datasets': [{
            'label': 'Average Spending',
            'data': weekday_averages,
            'backgroundColor': '#3b82f6'
        }]
    }

    return JSONResponse({
        'success': True,
        'chart_data': data,
        'period': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        }
    })

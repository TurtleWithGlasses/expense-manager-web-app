"""
Calendar view endpoints for displaying entries in calendar format
"""

from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import current_user
from app.models.user import User
from app.services import calendar_service
from app.services.user_preferences import user_preferences_service
from app.core.currency import currency_service

router = APIRouter(prefix="/calendar", tags=["calendar"])
templates = Jinja2Templates(directory="app/templates")

# Add custom Jinja2 filters for calendar
def parse_date_filter(date_str):
    """Parse ISO date string to date object"""
    if isinstance(date_str, date):
        return date_str
    return datetime.strptime(date_str, "%Y-%m-%d").date()

def add_days_filter(date_obj, days):
    """Add days to a date object"""
    return date_obj + timedelta(days=days)

templates.env.filters['parse_date'] = parse_date_filter
templates.env.filters['add_days'] = add_days_filter


def _get_currency_formatter(db: Session, user_id: int):
    """Get currency formatter for the user's currency preference."""
    currency_code = user_preferences_service.get_user_currency(db, user_id)

    def format_currency(amount: float):
        return currency_service.format_amount(amount, currency_code)

    return format_currency


@router.get("", response_class=HTMLResponse)
def calendar_view(
    request: Request,
    year: int = Query(None, description="Year to display"),
    month: int = Query(None, description="Month to display (1-12)"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Display calendar view of financial entries.

    If year/month not provided, shows current month.
    """

    # Default to current month if not specified
    today = date.today()
    display_year = year if year else today.year
    display_month = month if month else today.month

    # Validate month
    if not (1 <= display_month <= 12):
        display_month = today.month

    # Get calendar data
    calendar_data = calendar_service.get_calendar_data(
        db=db,
        user_id=user.id,
        year=display_year,
        month=display_month
    )

    # Get month summary
    month_summary = calendar_service.get_month_summary(
        db=db,
        user_id=user.id,
        year=display_year,
        month=display_month
    )

    # Get available months for navigation
    available_months = calendar_service.get_available_months(
        db=db,
        user_id=user.id
    )

    # Calculate previous and next month
    if display_month == 1:
        prev_month = 12
        prev_year = display_year - 1
    else:
        prev_month = display_month - 1
        prev_year = display_year

    if display_month == 12:
        next_month = 1
        next_year = display_year + 1
    else:
        next_month = display_month + 1
        next_year = display_year

    # Pre-calculate calendar grid data to avoid Jinja2 filter issues
    first_day = datetime.strptime(calendar_data['first_day'], "%Y-%m-%d").date()
    last_day = datetime.strptime(calendar_data['last_day'], "%Y-%m-%d").date()

    # Calculate first weekday (convert Monday=0 to Sunday=0)
    first_weekday = (first_day.weekday() + 1) % 7

    # Calculate total days in month
    total_days = (last_day - first_day).days + 1

    # Generate list of all dates in the month with metadata
    calendar_dates = []
    for day_num in range(1, total_days + 1):
        current_date = first_day + timedelta(days=day_num - 1)
        date_str = current_date.isoformat()
        date_data = calendar_data['dates'].get(date_str, {})

        calendar_dates.append({
            'day_num': day_num,
            'date': date_str,
            'date_obj': current_date,
            'date_display': current_date.strftime('%B %d, %Y'),
            'is_today': date_str == today.isoformat(),
            'has_entries': date_data.get('entry_count', 0) > 0,
            'data': date_data
        })

    # Get currency formatter
    format_currency = _get_currency_formatter(db, user.id)

    return templates.TemplateResponse(
        "calendar/index.html",
        {
            "request": request,
            "user": user,
            "calendar_data": calendar_data,
            "month_summary": month_summary,
            "available_months": available_months,
            "current_year": display_year,
            "current_month": display_month,
            "today": today.isoformat(),
            "prev_month": prev_month,
            "prev_year": prev_year,
            "next_month": next_month,
            "next_year": next_year,
            "first_weekday": first_weekday,
            "calendar_dates": calendar_dates,
            "format_currency": format_currency,
        }
    )


@router.get("/date/{date_str}", response_class=HTMLResponse)
def calendar_date_detail(
    request: Request,
    date_str: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed view of entries for a specific date.
    Returns HTML fragment for HTMX modal.

    Date format: YYYY-MM-DD
    """

    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return HTMLResponse(content="<p>Invalid date format</p>", status_code=400)

    # Get entries for this date
    date_data = calendar_service.get_date_entries(
        db=db,
        user_id=user.id,
        target_date=target_date
    )

    # Get currency formatter
    format_currency = _get_currency_formatter(db, user.id)

    return templates.TemplateResponse(
        "calendar/date_detail.html",
        {
            "request": request,
            "user": user,
            "date_data": date_data,
            "format_currency": format_currency,
        }
    )


@router.get("/api/month-data", response_class=HTMLResponse)
def get_month_data_api(
    request: Request,
    year: int = Query(..., description="Year"),
    month: int = Query(..., description="Month (1-12)"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get calendar data for a specific month via HTMX.
    Returns HTML fragment to replace calendar grid.
    """

    # Validate month
    if not (1 <= month <= 12):
        return HTMLResponse(content="<p>Invalid month</p>", status_code=400)

    # Get calendar data
    calendar_data = calendar_service.get_calendar_data(
        db=db,
        user_id=user.id,
        year=year,
        month=month
    )

    # Get month summary
    month_summary = calendar_service.get_month_summary(
        db=db,
        user_id=user.id,
        year=year,
        month=month
    )

    today = date.today()

    # Get currency formatter
    format_currency = _get_currency_formatter(db, user.id)

    return templates.TemplateResponse(
        "calendar/calendar_grid.html",
        {
            "request": request,
            "user": user,
            "calendar_data": calendar_data,
            "month_summary": month_summary,
            "current_year": year,
            "current_month": month,
            "today": today.isoformat(),
            "format_currency": format_currency,
        }
    )

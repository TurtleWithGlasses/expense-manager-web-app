from datetime import date, timedelta
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
import json

from app.deps import current_user
from app.db.session import get_db
from app.services.metrics import expenses_by_category, daily_expenses
from app.models.entry import Entry
from app.models.category import Category
from app.templates import render

router = APIRouter(prefix="/metrics", tags=["metrics"])


def _parsed_dates(start: str | None, end: str | None):
    # fallback to current month if not provided
    today = date.today()
    if not start or not end:
        month_start = today.replace(day=1)
        # naive month end
        next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        month_end = next_month - timedelta(days=1)
        return month_start, month_end
    return date.fromisoformat(start), date.fromisoformat(end)


def _ensure_date(d):
    if isinstance(d, str):
        from datetime import datetime
        return datetime.fromisoformat(d).date()
    return d


def daily_expenses_with_categories(db, user_id: int, start: date, end: date):
    """Get daily expenses with category breakdown for enhanced tooltips"""
    start = _ensure_date(start)
    end = _ensure_date(end)
    e_next = end + timedelta(days=1)
    
    # Get all expenses with categories for the date range
    q = (
        db.query(Entry.date, Entry.amount, Category.name)
        .join(Category, Category.id == Entry.category_id, isouter=True)
        .filter(
            Entry.user_id == user_id,
            func.lower(Entry.type) == "expense",
            Entry.date >= start,
            Entry.date < e_next,
        )
        .order_by(Entry.date.asc())
    )
    
    # Group by date and category
    daily_data = {}
    cur = start
    
    # Initialize all dates with empty data
    while cur <= end:
        daily_data[cur.isoformat()] = {
            'total': 0.0,
            'categories': {}
        }
        cur += timedelta(days=1)
    
    # Fill in actual data
    for entry_date, amount, category_name in q.all():
        date_key = entry_date.isoformat()
        category = category_name or "Uncategorized"
        
        if date_key in daily_data:
            daily_data[date_key]['total'] += float(amount)
            if category in daily_data[date_key]['categories']:
                daily_data[date_key]['categories'][category] += float(amount)
            else:
                daily_data[date_key]['categories'][category] = float(amount)
    
    return daily_data


@router.get("/chart/pie", response_class=HTMLResponse)
async def chart_pie(
    request: Request,
    start: str | None = Query(None),
    end: str | None = Query(None),
    user = Depends(current_user),
    db: Session = Depends(get_db)
):
    s, e = _parsed_dates(start, end)
    data = expenses_by_category(db, user_id=user["id"], start=s, end=e)
    labels = [n for n, _ in data]
    values = [v for _, v in data]
    return render(request, "dashboard/_chart_pie.html", {"labels": labels, "values": values})


@router.get("/chart/bar", response_class=HTMLResponse)
async def chart_bar(
    request: Request,
    start: str | None = Query(None),
    end: str | None = Query(None),
    user = Depends(current_user),
    db: Session = Depends(get_db),
):
    s, e = _parsed_dates(start, end)
    data = expenses_by_category(db, user_id=user["id"], start=s, end=e)
    labels = [n for n, _ in data]
    values = [v for _, v in data]
    return render(request, "dashboard/_chart_bar.html", {"labels": labels, "values": values})


@router.get("/chart/daily", response_class=HTMLResponse)
async def chart_daily(
    request: Request,
    start: str | None = Query(None),
    end: str | None = Query(None),
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    s, e = _parsed_dates(start, end)
    
    # Get enhanced data with category breakdown
    data = daily_expenses_with_categories(db, user_id=user["id"], start=s, end=e)
    
    # Prepare chart data for Chart.js with category information
    chart_data = {
        'labels': [],
        'datasets': [{
            'label': 'Daily Expenses',
            'data': [],
            'categoryData': [],
            'borderColor': 'rgb(59, 130, 246)',
            'backgroundColor': 'rgba(59, 130, 246, 0.1)',
            'borderWidth': 2,
            'pointBackgroundColor': 'rgb(59, 130, 246)',
            'pointBorderColor': '#fff',
            'pointBorderWidth': 2,
            'pointRadius': 4,
            'pointHoverRadius': 6,
            'tension': 0.4,
            'fill': True
        }]
    }
    
    for date_str in sorted(data.keys()):
        chart_data['labels'].append(date_str)
        chart_data['datasets'][0]['data'].append(data[date_str]['total'])
        chart_data['datasets'][0]['categoryData'].append(data[date_str]['categories'])
    
    # Convert to JSON for JavaScript
    chart_data_json = json.dumps(chart_data)
    
    return render(request, "dashboard/_chart_daily.html", {
        "chart_data": chart_data_json,
        "start_date": s.isoformat(),
        "end_date": e.isoformat()
    })
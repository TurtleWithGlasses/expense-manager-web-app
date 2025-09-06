from datetime import date, timedelta
from fastapi import APIRouter, Depends, Request,  Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.deps import current_user
from app.db.session import get_db
from app.services.metrics import expenses_by_category, daily_expenses
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
    series = daily_expenses(db, user_id=user["id"], start=s, end=e)
    labels = list(series.keys())
    values = list(series.values())
    return render(request, "dashboard/_chart_daily.html", {"labels": labels, "values": values})
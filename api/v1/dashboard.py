from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import current_user
from app.templates import render
from app.services.metrics import range_summary, expense_in_range, income_in_range

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

def _parse_dates(start: str | None, end: str | None):
    today = date.today()
    if not start or not end:
        month_start = today.replace(day=1)
        next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        month_end = next_month - timedelta(days=1)
        return month_start, month_end
    return date.fromisoformat(start), date.fromisoformat(end)

@router.get("/summary", response_class=HTMLResponse)
async def summary_panel(
    request: Request,
    start: str | None = Query(None),
    end: str | None = Query(None),
    user = Depends(current_user),
    db: Session = Depends(get_db),
):
    s, e = _parse_dates(start, end)
    totals = range_summary(db, user_id=user["id"], start=s, end=e)
    return render(request, "dashboard/_summary.html", {"totals": totals})

@router.get("/expenses", response_class=HTMLResponse)
async def expenses_panel(
    request: Request,
    start: str | None = Query(None),
    end: str | None = Query(None),
    user = Depends(current_user),
    db: Session = Depends(get_db)
):
    s, e = _parse_dates(start, end)
    items = expense_in_range(db, user_id=user["id"], start=s, end=e)
    return render(request, "dashboard/_expenses_list.html", {"items": items})

@router.get("/incomes", response_class=HTMLResponse)
async def incomes_panel(
    request: Request,
    start: str | None = Query(None),
    end: str | None = Query(None),
    user = Depends(current_user),
    db: Session = Depends(get_db)
):
    s, e = _parse_dates(start, end)
    items = income_in_range(db, user_id=user["id"], start=s, end=e)
    return render(request, "dashboard/_incomes_list.html", {"items": items})
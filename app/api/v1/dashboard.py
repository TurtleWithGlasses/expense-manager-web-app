# app/api/v1/dashboard.py
from datetime import date, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import current_user
from app.models.entry import Entry
from app.templates import render
from app.services.metrics import range_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _parse_dates(start: str | None, end: str | None) -> tuple[date, date]:
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
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    s, e = _parse_dates(start, end)
    totals = range_summary(db, user_id=user["id"], start=s, end=e)
    return render(request, "dashboard/_summary.html", {"totals": totals})


@router.get("/expenses", response_class=HTMLResponse)
async def expenses_panel(
    request: Request,
    start: date = Query(...),
    end: date = Query(...),
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Entry)
        .filter(
            Entry.user_id == user["id"],
            Entry.type == "expense",
            Entry.date >= start,
            Entry.date <= end,
        )
        .order_by(Entry.date.asc())
        .all()
    )
    total_expense: Decimal = (
        db.query(func.coalesce(func.sum(Entry.amount), 0))
        .filter(
            Entry.user_id == user["id"],
            Entry.type == "expense",
            Entry.date >= start,
            Entry.date <= end,
        )
        .scalar()
    )
    return render(
        request,
        "dashboard/_expenses_list.html",
        {"rows": rows, "total_expense": total_expense},
    )


@router.get("/incomes", response_class=HTMLResponse)
async def incomes_panel(
    request: Request,
    start: date = Query(...),
    end: date = Query(...),
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Entry)
        .filter(
            Entry.user_id == user["id"],
            Entry.type == "income",
            Entry.date >= start,
            Entry.date <= end,
        )
        .order_by(Entry.date.asc())
        .all()
    )
    total_income: Decimal = (
        db.query(func.coalesce(func.sum(Entry.amount), 0))
        .filter(
            Entry.user_id == user["id"],
            Entry.type == "income",
            Entry.date >= start,
            Entry.date <= end,
        )
        .scalar()
    )
    return render(
        request,
        "dashboard/_incomes_list.html",
        {"rows": rows, "total_income": total_income},
    )

from datetime import date, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.deps import current_user
from app.models.entry import Entry
from app.templates import render
from app.services.metrics import range_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _parse_dates(start: date | None, end: date | None) -> tuple[date, date]:
    """If no start/end provided, default to the current month range."""
    today = date.today()
    if not start or not end:
        month_start = today.replace(day=1)
        # last day of month
        next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        month_end = next_month - timedelta(days=1)
        return month_start, month_end
    return start, end


def _sum_amount(rows) -> Decimal:
    total = Decimal("0")
    for r in rows:
        total += Decimal(str(r.amount))
    return total


@router.get("/summary", response_class=HTMLResponse)
async def summary_panel(
    request: Request,
    start: date | None = Query(None),
    end: date | None = Query(None),
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    s, e = _parse_dates(start, end)
    totals = range_summary(db, user_id=user["id"], start=s, end=e)
    return render(request, "dashboard/_summary.html", {"totals": totals})


@router.get("/expenses", response_class=HTMLResponse)
async def expenses_panel(
    request: Request,
    start: date | None = Query(None),
    end: date | None = Query(None),
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    s, e = _parse_dates(start, end)
    e_next = e + timedelta(days=1)

    rows = (
        db.query(Entry)
        .filter(
            Entry.user_id == user["id"],
            func.lower(Entry.type) == "expense", 
            Entry.date >= s,
            Entry.date < e_next,
        )
        .order_by(Entry.date.asc())
        .all()
    )
    total_expense = _sum_amount(rows)
    return render(
        request,
        "dashboard/_expenses_list.html",
        {"rows": rows, "total_expense": float(total_expense)},
    )


@router.get("/incomes", response_class=HTMLResponse)
async def incomes_panel(
    request: Request,
    start: date | None = Query(None),
    end: date | None = Query(None),
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    s, e = _parse_dates(start, end)
    e_next = e + timedelta(days=1)

    rows = (
        db.query(Entry)
        .filter(
            Entry.user_id == user["id"],
            func.lower(Entry.type) == "income", 
            Entry.date >= s,
            Entry.date < e_next,
        )
        .order_by(Entry.date.asc())
        .all()
    )
    total_income = _sum_amount(rows)
    return render(
        request,
        "dashboard/_incomes_list.html",
        {"rows": rows, "total_income": float(total_income)},
    )

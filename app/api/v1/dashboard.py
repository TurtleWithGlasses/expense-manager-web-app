from datetime import date, datetime, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.deps import current_user
from app.models.entry import Entry
from app.templates import render
from app.services.metrics import range_summary_multi_currency
from app.services.user_preferences import user_preferences_service
from app.core.currency import currency_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

def _parse_dates(start: str | None, end: str | None) -> tuple[date, date]:
    today = date.today()
    if not start or not end:
        month_start = today.replace(day=1)
        next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        month_end = next_month - timedelta(days=1)
        return month_start, month_end
    
    s = datetime.fromisoformat(start).date() if isinstance(start, str) else start
    e = datetime.fromisoformat(end).date() if isinstance(end, str) else end
    return s, e

def _sum_amount(rows) -> Decimal:
    total = Decimal("0")
    for r in rows:
        total += Decimal(str(r.amount))
    return total

async def _convert_and_format_amounts(db: Session, user_id: int, amounts: dict) -> dict:
    """Convert amounts to user's preferred currency and format them"""
    user_currency = user_preferences_service.get_user_currency(db, user_id)
    converted_amounts = {}
    
    for key, amount in amounts.items():
        converted_amount = await currency_service.convert_amount(
            float(amount), 'USD', user_currency
        )
        # Provide both raw number and formatted string
        converted_amounts[key] = converted_amount  # Raw number for calculations
        converted_amounts[f"{key}_formatted"] = currency_service.format_amount(
            converted_amount, user_currency
        )  # Formatted string for display
    
    return converted_amounts

@router.get("/summary", response_class=HTMLResponse)
async def summary_panel(
    request: Request,
    start: date | None = Query(None),
    end: date | None = Query(None),
    category: int | None = Query(None),
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    s, e = _parse_dates(start, end)
    user_currency = user_preferences_service.get_user_currency(db, user.id)
    
    # Use multi-currency summary that properly converts each entry
    totals = await range_summary_multi_currency(db, user.id, s, e, user_currency, category)
    
    # Format the amounts
    converted_totals = {
        "income": totals["income"],
        "expense": totals["expense"],
        "balance": totals["balance"],
        "income_formatted": currency_service.format_amount(totals["income"], user_currency),
        "expense_formatted": currency_service.format_amount(totals["expense"], user_currency),
        "balance_formatted": currency_service.format_amount(totals["balance"], user_currency),
    }
    
    return render(request, "dashboard/_summary.html", {"totals": converted_totals})

@router.get("/expenses", response_class=HTMLResponse)
async def expenses_panel(
    request: Request,
    start: date | None = Query(None),
    end: date | None = Query(None),
    category: int | None = Query(None),
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    s, e = _parse_dates(start, end)
    e_next = e + timedelta(days=1)
    user_currency = user_preferences_service.get_user_currency(db, user.id)

    query = db.query(Entry).filter(
        Entry.user_id == user.id,
        func.lower(Entry.type) == "expense", 
        Entry.date >= s,
        Entry.date < e_next,
    )
    
    # Add category filter if specified
    if category:
        query = query.filter(Entry.category_id == category)
    
    rows = query.order_by(Entry.date.asc()).all()
    
    # Convert each entry amount to user's currency
    converted_rows = []
    total_expense = 0
    
    for row in rows:
        converted_amount = await currency_service.convert_amount(
            float(row.amount), row.currency_code, user_currency
        )
        
        # Create a new object with converted amount
        converted_row = {
            'id': row.id,
            'date': row.date,
            'category': row.category,
            'amount': converted_amount,
            'formatted_amount': currency_service.format_amount(converted_amount, user_currency)
        }
        converted_rows.append(converted_row)
        total_expense += converted_amount
    
    formatted_total = currency_service.format_amount(total_expense, user_currency)
    
    return render(
        request,
        "dashboard/_expenses_list.html",
        {
            "rows": converted_rows, 
            "total_expense": total_expense,
            "formatted_total": formatted_total
        },
    )

@router.get("/incomes", response_class=HTMLResponse)
async def incomes_panel(
    request: Request,
    start: date | None = Query(None),
    end: date | None = Query(None),
    category: int | None = Query(None),
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    s, e = _parse_dates(start, end)
    e_next = e + timedelta(days=1)
    user_currency = user_preferences_service.get_user_currency(db, user.id)

    query = db.query(Entry).filter(
        Entry.user_id == user.id,
        func.lower(Entry.type) == "income", 
        Entry.date >= s,
        Entry.date < e_next,
    )
    
    # Add category filter if specified
    if category:
        query = query.filter(Entry.category_id == category)
    
    rows = query.order_by(Entry.date.asc()).all()
    
    # Convert each entry amount to user's currency
    converted_rows = []
    total_income = 0
    
    for row in rows:
        converted_amount = await currency_service.convert_amount(
            float(row.amount), row.currency_code, user_currency
        )
        
        # Create a new object with converted amount
        converted_row = {
            'id': row.id,
            'date': row.date,
            'category': row.category,
            'description': row.description,
            'amount': converted_amount,
            'formatted_amount': currency_service.format_amount(converted_amount, user_currency)
        }
        converted_rows.append(converted_row)
        total_income += converted_amount
    
    formatted_total = currency_service.format_amount(total_income, user_currency)
    
    return render(
        request,
        "dashboard/_incomes_list.html",
        {
            "rows": converted_rows, 
            "total_income": total_income,
            "formatted_total": formatted_total
        },
    )
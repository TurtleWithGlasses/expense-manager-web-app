from datetime import date, datetime, timedelta
from sqlalchemy import func, case
from app.models.entry import Entry
from app.models.category import Category
from sqlalchemy.orm import Session
from app.core.currency import currency_service


def _ensure_date(d):
    if isinstance(d, str):
        return datetime.fromisoformat(d).date()
    return d

def range_summary(db, user_id: int, start, end):
    # make end exclusive for consistency
    start = _ensure_date(start)
    end = _ensure_date(end)
    e_next = end + timedelta(days=1)

    q = (
        db.query(
            func.sum(case((func.lower(Entry.type) == "income", Entry.amount), else_=0)).label("income"),
            func.sum(case((func.lower(Entry.type) == "expense", Entry.amount), else_=0)).label("expense"),
        )
        .filter(
            Entry.user_id == user_id,
            Entry.date >= start,
            Entry.date < e_next,
        )
    )
    income, expense = q.one()
    return {
        "income": float(income or 0),
        "expense": float(expense or 0),
        "balance": float((income or 0) - (expense or 0)),
    }

async def range_summary_multi_currency(db, user_id: int, start, end, target_currency: str, category_id: int = None):
    """Calculate range summary with proper multi-currency conversion"""
    start = _ensure_date(start)
    end = _ensure_date(end)
    e_next = end + timedelta(days=1)

    # Get all entries in the range
    query = db.query(Entry).filter(
        Entry.user_id == user_id,
        Entry.date >= start,
        Entry.date < e_next,
    )
    
    # Add category filter if specified
    if category_id:
        query = query.filter(Entry.category_id == category_id)
    
    entries = query.all()
    
    total_income = 0.0
    total_expense = 0.0
    
    for entry in entries:
        # Convert each entry to target currency
        converted_amount = await currency_service.convert_amount(
            float(entry.amount), entry.currency_code, target_currency
        )
        
        if entry.type.lower() == "income":
            total_income += converted_amount
        else:
            total_expense += converted_amount
    
    return {
        "income": total_income,
        "expense": total_expense,
        "balance": total_income - total_expense,
    }

def by_category(db, user_id: int, start, end):
    start = _ensure_date(start)
    end = _ensure_date(end)
    e_next = end + timedelta(days=1)
    
    q = (
        db.query(Category.name, func.sum(Entry.amount))
        .join(Category, Category.id == Entry.category_id, isouter=True)
        .filter(
            Entry.user_id == user_id, 
            func.lower(Entry.type) == "expense",
            Entry.date >= start,
            Entry.date < e_next,
        )
        .group_by(Category.name)
        .order_by(func.sum(Entry.amount).desc())
    )
    return [(name or "Uncategorized", float(total or 0)) for name, total in q.all()]

def expenses_by_category(db, user_id: int, start: date, end: date):
    start = _ensure_date(start)
    end = _ensure_date(end)
    e_next = end + timedelta(days=1)
    
    q = (
        db.query(Category.name, func.coalesce(func.sum(Entry.amount), 0))
        .join(Category, Category.id == Entry.category_id, isouter=True)
        .filter(
            Entry.user_id == user_id,
            func.lower(Entry.type) == "expense",
            Entry.date >= start,
            Entry.date < e_next,
        )
        .group_by(Category.name)
        .order_by(func.sum(Entry.amount).desc())
    )
    return [(name or "Uncategorized", float(total or 0)) for name, total in q.all()]


def daily_expenses(db, user_id: int, start: date, end: date):
    start = _ensure_date(start)
    end = _ensure_date(end)
    e_next = end + timedelta(days=1)
    
    q = (
        db.query(Entry.date, func.coalesce(func.sum(Entry.amount), 0))
        .filter(
            Entry.user_id == user_id,
            func.lower(Entry.type) == "expense",
            Entry.date >= start,
            Entry.date < e_next,
        )
        .group_by(Entry.date)
        .order_by(Entry.date.asc())
    )
    raw = {d.isoformat(): float(t or 0) for d, t in q.all()}
    # fill gaps
    cur = start
    out = {}
    while cur <= end:
        k = cur.isoformat()
        out[k] = raw.get(k, 0.0)
        cur += timedelta(days=1)
    return out

def expense_in_range(db: Session, user_id: int, start: date, end: date):
    start = _ensure_date(start)
    end = _ensure_date(end)
    # most recent first
    return (
        db.query(Entry)
        .filter(
            Entry.user_id == user_id,
            Entry.type == "expense",
            Entry.date.between(start, end),
        )
        .order_by(Entry.date.desc(), Entry.id.desc())
        .all()
    )

def income_in_range(db: Session, user_id: int, start: date, end: date):
    # most recent first
    return (
        db.query(Entry)
        .filter(
            Entry.user_id == user_id,
            Entry.type == "income",
            Entry.date.between(start, end),
        )
        .order_by(Entry.date.desc(), Entry.id.desc())
        .all()
    )
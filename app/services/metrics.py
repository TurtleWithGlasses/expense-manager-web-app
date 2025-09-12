from datetime import date, timedelta
from sqlalchemy import func, case, select
from app.models.entry import Entry
from app.models.category import Category
from sqlalchemy.orm import Session

def range_summary(db, user_id: int, start, end):
    # make end exclusive for consistency
    e_next = end + timedelta(days=1)

    q = (
        db.query(
            func.sum(case((Entry.type == "income", Entry.amount), else_=0)).label("income"),
            func.sum(case((Entry.type == "expense", Entry.amount), else_=0)).label("expense"),
        )
        .filter(
            Entry.user_id == user_id,
            Entry.date >= start,
            Entry.date < e_next,   # use exclusive bound like in dashboard.py
        )
    )
    income, expense = q.one()
    return {
        "income": float(income or 0),
        "expense": float(expense or 0),
        "balance": float((income or 0) - (expense or 0)),
    }

def by_category(db, user_id: int, start, end):
    from app.models.category import Category
    q = (
        db.query(Category.name, func.sum(Entry.amount))
        .join(Category, Category.id == Entry.category_id, isouter=True)
        .filter(Entry.user_id == user_id, Entry.type == "expense", Entry.date.between(start, end))
        .group_by(Category.name)
        .order_by(func.sum(Entry.amount).desc())
    )
    return [(name or "Uncategorized", float(total or 0)) for name, total in q.all()]

def expenses_by_category(db, user_id: int, start: date, end: date):
    # returns list[(name, total_expense)]
    q = (
        db.query(Category.name, func.coalesce(func.sum(Entry.amount), 0))
        .join(Category, Category.id == Entry.category_id, isouter=True)
        .filter(
            Entry.user_id == user_id,
            Entry.type == "expense",
            Entry.date.between(start, end),
        )
        .group_by(Category.name)
        .order_by(func.sum(Entry.amount).desc())
    )
    return [(name or "Uncategorized", float(total or 0)) for name, total in q.all()]

def daily_expenses(db, user_id: int, start: date, end: date):
    # returns dict[iso_date] -> total_expense; includes 0s for empty days
    q = (
        db.query(Entry.date, func.coalesce(func.sum(Entry.amount), 0))
        .filter(
            Entry.user_id == user_id,
            Entry.type == "expense",
            Entry.date.between(start, end),
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
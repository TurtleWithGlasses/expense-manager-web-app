from datetime import date as _date
from fastapi import APIRouter, Depends, Form, Query, Request, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.deps import current_user
from app.db.session import get_db
from app.services.entries import (
    list_entries,
    create_entry,
    delete_entry,
    update_entry_amount,
    search_entries,
    get_entries_count,
    get_search_entries_count,
)
from app.services.categories import list_categories
from app.services.user_preferences import user_preferences_service
from app.templates import render
from app.models.entry import Entry

router = APIRouter(prefix="/entries", tags=["entries"])


# ---------- Page ----------

@router.get("/", response_class=HTMLResponse)
async def page(
    request: Request,
    start: str | None = Query(None),
    end: str | None = Query(None),
    category: str | None = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("date", regex="^(date|amount|category)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    user=Depends(current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    # Parse date parameters
    start_date = None
    end_date = None
    if start:
        start_date = _date.fromisoformat(start)
    if end:
        end_date = _date.fromisoformat(end)

    # Parse category parameter - convert to int if not empty, otherwise None
    category_id = None
    if category and category.strip():
        try:
            category_id = int(category)
        except ValueError:
            category_id = None

    # Use search_entries for filtering if dates or category are provided
    if start_date and end_date:
        entries = search_entries(db, user_id=user.id, start=start_date, end=end_date,
                                category_id=category_id, limit=limit, offset=offset,
                                sort_by=sort_by, order=order)
        total_count = get_search_entries_count(db, user_id=user.id, start=start_date,
                                              end=end_date, category_id=category_id)
    elif category_id:
        entries = search_entries(db, user_id=user.id, category_id=category_id,
                                limit=limit, offset=offset, sort_by=sort_by, order=order)
        total_count = get_search_entries_count(db, user_id=user.id, category_id=category_id)
    else:
        entries = list_entries(db, user_id=user.id, limit=limit, offset=offset,
                              sort_by=sort_by, order=order)
        total_count = get_entries_count(db, user_id=user.id)

    cats = list_categories(db, user_id=user.id)
    user_currency = user_preferences_service.get_user_currency(db, user.id)

    # Calculate pagination info
    showing_from = offset + 1 if total_count > 0 else 0
    showing_to = min(offset + limit, total_count)
    has_more = showing_to < total_count

    return render(request, "entries/index.html",
                  {"entries": entries,
                   "categories": cats,
                   "today": _date.today().isoformat(),
                   "user_currency": user_currency,
                   "start_date": start,
                   "end_date": end,
                   "selected_category": str(category_id) if category_id else None,
                   "limit": limit,
                   "offset": offset,
                   "sort_by": sort_by,
                   "order": order,
                   "total_count": total_count,
                   "showing_from": showing_from,
                   "showing_to": showing_to,
                   "has_more": has_more})


# ---------- Create ----------

@router.post("/create", response_class=HTMLResponse)
async def add(
    request: Request,
    type: str = Form(...),
    amount: float = Form(...),  # This amount is already in user's currency
    category_id: int | None = Form(None),
    note: str | None = Form(None),
    date_str: str | None = Form(None),
    currency_code: str | None = Form(None),  # Accept currency from form
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    from app.services.user_preferences import user_preferences_service
    
    # Get user's preferred currency (fallback if not provided in form)
    user_currency = currency_code or user_preferences_service.get_user_currency(db, user.id)
    
    d = _date.fromisoformat(date_str) if date_str else _date.today()

    # Store the amount AS-IS in the user's currency (no conversion)
    create_entry(
        db,
        user_id=user.id,
        type=type,
        amount=float(amount),  # Raw amount in user's currency
        category_id=category_id if category_id else None,
        note=note,
        date=d,
        currency_code=user_currency
    )

    entries = list_entries(db, user_id=user.id)
    user_currency = user_preferences_service.get_user_currency(db, user.id)
    return render(request, "entries/_list.html", {"entries": entries, "user_currency": user_currency})


# ---------- Delete ----------

@router.post("/delete/{entry_id}", response_class=HTMLResponse)
async def remove(
    request: Request,
    entry_id: int,
    user=Depends(current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    delete_entry(db, user_id=user.id, entry_id=entry_id)
    entries = list_entries(db, user_id=user.id)
    user_currency = user_preferences_service.get_user_currency(db, user.id)
    return render(request, "entries/_list.html", {"entries": entries, "user_currency": user_currency})


# ---------- Inline edit: amount cell ----------

@router.get("/edit_amount/{entry_id}", response_class=HTMLResponse)
async def edit_amount_cell(
    request: Request,
    entry_id: int,
    user=Depends(current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    e = db.query(Entry).filter(
        Entry.user_id == user.id, Entry.id == entry_id
    ).first()
    if not e:
        raise HTTPException(status_code=404, detail="Entry not found")
    # returns the edit fragment for the amount cell
    return render(request, "entries/_cell_amount_edit.html", {"e": e})


@router.post("/update_amount/{entry_id}", response_class=HTMLResponse)
async def update_amount_cell(
    request: Request,
    entry_id: int,
    amount: float = Form(...),
    user=Depends(current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    e = update_entry_amount(db, user_id=user.id, entry_id=entry_id, new_amount=amount)
    if not e:
        raise HTTPException(status_code=404, detail="Entry not found")
    # return the display cell (amount) only
    return render(request, "entries/_cell_amount.html", {"e": e})


@router.get("/cell_amount/{entry_id}", response_class=HTMLResponse)
async def amount_cell_display(
    request: Request,
    entry_id: int,
    user=Depends(current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    e = db.query(Entry).filter(
        Entry.user_id == user.id, Entry.id == entry_id
    ).first()
    if not e:
        raise HTTPException(status_code=404, detail="Entry not found")
    return render(request, "entries/_cell_amount.html", {"e": e})

# === Row display (used for Cancel) ===
@router.get("/row/{entry_id}", response_class=HTMLResponse)
async def row_display(
    request: Request,
    entry_id: int,
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    e = db.query(Entry).filter(Entry.user_id == user.id, Entry.id == entry_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Entry not found")
    cats = list_categories(db, user_id=user.id)
    user_currency = user_preferences_service.get_user_currency(db, user.id)
    return render(request, "entries/_row.html", {"e": e, "categories": cats, "user_currency": user_currency, "wrap": True})

# === Row edit (GET) ===
@router.get("/edit/{entry_id}", response_class=HTMLResponse)
async def row_edit(
    request: Request,
    entry_id: int,
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    e = db.query(Entry).filter(Entry.user_id == user.id, Entry.id == entry_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Entry not found")
    cats = list_categories(db, user_id=user.id)
    return render(request, "entries/_row_edit.html", {"e": e, "categories": cats, "wrap": True})

# === Row update (POST) ===
@router.post("/update/{entry_id}", response_class=HTMLResponse)
async def update_entry(
    request: Request,
    entry_id: int,
    type: str = Form(...),
    amount: float = Form(...),
    category_id: int | None = Form(None),
    note: str | None = Form(None),
    date: str = Form(...),  # accept as string
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    e = db.query(Entry).filter(
        Entry.user_id == user.id, Entry.id == entry_id
    ).first()
    if not e:
        raise HTTPException(status_code=404, detail="Entry not found")

    # update fields (preserve currency_code)
    e.type = type
    e.amount = float(amount)
    e.category_id = category_id or None
    e.note = note
    e.date = _date.fromisoformat(date)
    # Note: currency_code is preserved from the original entry

    db.add(e)
    db.commit()
    db.refresh(e)

    cats = list_categories(db, user_id=user.id)
    user_currency = user_preferences_service.get_user_currency(db, user.id)
    return render(
        request,
        "entries/_row.html",
        {"e": e, "categories": cats, "user_currency": user_currency, "wrap": True}
    )


# ---------- API Endpoints for Bulk Operations ----------

from fastapi.responses import JSONResponse
from pydantic import BaseModel

@router.get("/uncategorized", response_class=JSONResponse)
async def get_uncategorized_entries(
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    """Get all uncategorized entries for the current user."""
    try:
        entries = db.query(Entry).filter(
            Entry.user_id == user.id,
            Entry.category_id.is_(None)
        ).order_by(Entry.date.desc()).all()

        entries_data = [
            {
                "id": e.id,
                "type": e.type,
                "amount": float(e.amount),
                "note": e.note,
                "description": e.note,  # Alias for compatibility
                "date": e.date.isoformat() if e.date else None,
                "currency_code": e.currency_code
            }
            for e in entries
        ]

        return JSONResponse({
            "success": True,
            "entries": entries_data,
            "count": len(entries_data)
        })
    except Exception as error:
        return JSONResponse({
            "success": False,
            "message": str(error)
        }, status_code=500)


class UpdateCategoryRequest(BaseModel):
    category_id: int

@router.put("/{entry_id}/category", response_class=JSONResponse)
async def update_entry_category(
    entry_id: int,
    request_data: UpdateCategoryRequest,
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    """Update category for a specific entry."""
    try:
        entry = db.query(Entry).filter(
            Entry.id == entry_id,
            Entry.user_id == user.id
        ).first()

        if not entry:
            return JSONResponse({
                "success": False,
                "message": "Entry not found"
            }, status_code=404)

        entry.category_id = request_data.category_id
        db.commit()

        return JSONResponse({
            "success": True,
            "message": "Category updated successfully"
        })
    except Exception as error:
        db.rollback()
        return JSONResponse({
            "success": False,
            "message": str(error)
        }, status_code=500)
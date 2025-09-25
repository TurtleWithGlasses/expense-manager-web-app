from datetime import date as _date
from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.deps import current_user
from app.db.session import get_db
from app.services.entries import (
    list_entries,
    create_entry,
    delete_entry,
    update_entry_amount,
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
    user=Depends(current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    entries = list_entries(db, user_id=user.id)
    cats = list_categories(db, user_id=user.id)
    user_currency = user_preferences_service.get_user_currency(db, user.id)
    return render(request, "entries/index.html",
                  {"entries": entries,
                   "categories": cats,
                   "today": _date.today().isoformat(),
                   "user_currency": user_currency})


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
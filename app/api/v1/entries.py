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
    entries = list_entries(db, user_id=user["id"])
    cats = list_categories(db, user_id=user["id"])
    return render(request, "entries/index.html", {"entries": entries, "categories": cats})


# ---------- Create ----------

@router.post("/create", response_class=HTMLResponse)
async def add(
    request: Request,
    type: str = Form(...),                       # "expense" | "income"
    amount: float = Form(...),
    category_id: int | None = Form(None),        # may be empty
    note: str | None = Form(None),
    date: _date = Form(...),                     # HTML <input type="date"> sends ISO; FastAPI parses to date
    user=Depends(current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    # Normalize optional category_id (empty string -> None)
    if category_id == "":
        category_id = None

    # Persist
    create_entry(
        db,
        user_id=user["id"],
        type=type,
        amount=float(amount),
        category_id=category_id,
        note=note,
        date=date,
    )

    # Re-render the table body
    entries = list_entries(db, user_id=user["id"])
    return render(request, "entries/_list.html", {"entries": entries})


# ---------- Delete ----------

@router.post("/delete/{entry_id}", response_class=HTMLResponse)
async def remove(
    request: Request,
    entry_id: int,
    user=Depends(current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    delete_entry(db, user_id=user["id"], entry_id=entry_id)
    entries = list_entries(db, user_id=user["id"])
    return render(request, "entries/_list.html", {"entries": entries})


# ---------- Inline edit: amount cell ----------

@router.get("/edit_amount/{entry_id}", response_class=HTMLResponse)
async def edit_amount_cell(
    request: Request,
    entry_id: int,
    user=Depends(current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    e = db.query(Entry).filter(
        Entry.user_id == user["id"], Entry.id == entry_id
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
    e = update_entry_amount(db, user_id=user["id"], entry_id=entry_id, new_amount=amount)
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
        Entry.user_id == user["id"], Entry.id == entry_id
    ).first()
    if not e:
        raise HTTPException(status_code=404, detail="Entry not found")
    return render(request, "entries/_cell_amount.html", {"e": e})

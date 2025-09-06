from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import date
from app.deps import current_user
from app.db.session import get_db
from app.services.entries import list_entries, create_entry, delete_entry, update_entry_amount
from app.services.categories import list_categories
from app.templates import render
from app.models.entry import Entry

router = APIRouter(prefix="/entries", tags=["entries"])


@router.get("/", response_class=HTMLResponse)
async def page(request=Request, user=Depends(current_user), db: Session = Depends(get_db)):
    entries = list_entries(db, user_id=user["id"])
    cats = list_categories(db, user_id=user["id"])
    return render(request, "entries/index.html", {"entries": entries, "categories": cats})


@router.post("/create", response_class=HTMLResponse)
async def add(
    type: str = Form(...),
    amount: float = Form(...),
    category_id: int | None = Form(None),
    note: str | None = Form(None),
    date_str: str = Form(...),
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    create_entry(db,
                 user_id=user["id"],
                 type=type,
                 amount=float(amount),
                 category_id=category_id if category_id else None,
                 note=note,
                 date=date.fromisoformat(date_str),
                )
    entries = list_entries(db, user_id=user["id"])
    cats = list_categories(db, user_id=user["id"])
    return render("entries/_list.html", {"entries": entries})


@router.post("/delete/{entry_id}", response_class=HTMLResponse)
async def remove(entry_id: int, user=Depends(current_user), db: Session = Depends(get_db)):
    delete_entry(db, user_id=user["id"], entry_id=entry_id)
    entries = list_entries(db, user_id=user["id"])
    return render("entries/_list.html", {"entries": entries})


@router.get("/edit_amount/{entry_id}", response_class=HTMLResponse)
async def edit_amount_cell(
    request: Request, entry_id: int, user=Depends(current_user), db: Session = Depends(get_db)
):
    e = db.query(Entry).filter(Entry.user_id == user["id"], Entry.id == entry_id).first()
    return render(request, "entries/_cell_amount_edit.html", {"e": e})

@router.post("/update_amount/{entry_id}", response_class=HTMLResponse)
async def update_amount_cell(
    request: Request,
    entry_id: int,
    amount: float = Form(...),
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    e = update_entry_amount(db, user_id=user["id"], entry_id=entry_id, new_amount=amount)
    # return the display cell (amount) only
    return render(request, "entries/_cell_amount.html", {"e": e})

@router.get("/cell_amount/{entry_id}", response_class=HTMLResponse)
async def amount_cell_display(
    request: Request, entry_id: int, user=Depends(current_user), db: Session = Depends(get_db)
):
    e = db.query(Entry).filter(Entry.user_id == user["id"], Entry.id == entry_id).first()
    return render(request, "entries/_cell_amount.html", {"e": e})

"""Split Expenses API - Phase 31: Social & Collaboration"""
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import current_user
from app.models.user import User
from app.templates import render
from app.core.currency import CURRENCIES
from app.services.user_preferences import user_preferences_service
from app.services import split_expense_service as svc

router = APIRouter(tags=["Split Expenses"])


# ── Pydantic schemas ─────────────────────────────────────────────────────────

class ContactCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    email: Optional[str] = None
    notes: Optional[str] = None


class ContactUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    email: Optional[str] = None
    notes: Optional[str] = None


class ParticipantIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    amount: float = Field(..., gt=0)
    contact_id: Optional[int] = None
    is_payer: bool = False


class SplitCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    total_amount: float = Field(..., gt=0)
    currency_code: str = Field(default="USD", min_length=3, max_length=3)
    date: date
    notes: Optional[str] = None
    entry_id: Optional[int] = None
    participants: list[ParticipantIn] = Field(..., min_length=1)


# ── Page route ───────────────────────────────────────────────────────────────

@router.get("/split", response_class=HTMLResponse)
async def split_page(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Split expenses overview page."""
    user_currency_code = user_preferences_service.get_user_currency(db, user.id)
    user_currency = CURRENCIES.get(user_currency_code, CURRENCIES["USD"])
    contacts = svc.list_contacts(db, user.id)
    splits = svc.list_splits(db, user.id)
    balances = svc.get_balances(db, user.id)

    return render(request, "split/index.html", {
        "user": user,
        "request": request,
        "user_currency": user_currency,
        "user_currency_code": user_currency_code,
        "contacts": contacts,
        "splits": splits,
        "balances": balances,
    })


# ── Contact endpoints ─────────────────────────────────────────────────────────

@router.get("/api/split/contacts")
async def list_contacts(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    contacts = svc.list_contacts(db, user.id)
    return JSONResponse([svc.contact_to_dict(c) for c in contacts])


@router.post("/api/split/contacts", status_code=201)
async def create_contact(
    data: ContactCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    contact = svc.create_contact(db, user.id, data.name, data.email, data.notes)
    return JSONResponse(svc.contact_to_dict(contact), status_code=201)


@router.put("/api/split/contacts/{contact_id}")
async def update_contact(
    contact_id: int,
    data: ContactUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    contact = svc.update_contact(db, user.id, contact_id, data.name, data.email, data.notes)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return JSONResponse(svc.contact_to_dict(contact))


@router.delete("/api/split/contacts/{contact_id}")
async def delete_contact(
    contact_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if not svc.delete_contact(db, user.id, contact_id):
        raise HTTPException(status_code=404, detail="Contact not found")
    return JSONResponse({"success": True})


# ── Split expense endpoints ──────────────────────────────────────────────────

@router.get("/api/split/expenses")
async def list_splits(
    status: Optional[str] = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    splits = svc.list_splits(db, user.id, status)
    return JSONResponse([svc.split_to_dict(s) for s in splits])


@router.post("/api/split/expenses", status_code=201)
async def create_split(
    data: SplitCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if not any(p.is_payer for p in data.participants):
        raise HTTPException(status_code=422, detail="At least one participant must be marked as the payer.")

    participants = [
        {
            "name": p.name,
            "amount": Decimal(str(p.amount)),
            "contact_id": p.contact_id,
            "is_payer": p.is_payer,
        }
        for p in data.participants
    ]
    split = svc.create_split(
        db=db,
        user_id=user.id,
        title=data.title,
        total_amount=Decimal(str(data.total_amount)),
        currency_code=data.currency_code.upper(),
        split_date=data.date,
        participants=participants,
        notes=data.notes,
        entry_id=data.entry_id,
    )
    return JSONResponse(svc.split_to_dict(split), status_code=201)


@router.get("/api/split/expenses/{split_id}")
async def get_split(
    split_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    split = svc.get_split(db, user.id, split_id)
    if not split:
        raise HTTPException(status_code=404, detail="Split expense not found")
    return JSONResponse(svc.split_to_dict(split))


@router.delete("/api/split/expenses/{split_id}")
async def delete_split(
    split_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if not svc.delete_split(db, user.id, split_id):
        raise HTTPException(status_code=404, detail="Split expense not found")
    return JSONResponse({"success": True})


# ── Settle endpoints ──────────────────────────────────────────────────────────

@router.post("/api/split/expenses/{split_id}/participants/{participant_id}/settle")
async def settle_participant(
    split_id: int,
    participant_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    participant = svc.settle_participant(db, user.id, split_id, participant_id)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    split = svc.get_split(db, user.id, split_id)
    return JSONResponse({"success": True, "split_status": split.status if split else "unknown"})


@router.post("/api/split/expenses/{split_id}/participants/{participant_id}/unsettle")
async def unsettle_participant(
    split_id: int,
    participant_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    participant = svc.unsettle_participant(db, user.id, split_id, participant_id)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    return JSONResponse({"success": True})


# ── Balance endpoint ──────────────────────────────────────────────────────────

@router.get("/api/split/balances")
async def get_balances(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return JSONResponse(svc.get_balances(db, user.id))

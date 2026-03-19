"""Split Expense Service - Phase 31: Social & Collaboration"""
from datetime import datetime, UTC, date
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session

from app.models.split_expense import SplitContact, SplitExpense, SplitParticipant, SplitStatus


# ── Contact helpers ──────────────────────────────────────────────────────────

def list_contacts(db: Session, user_id: int) -> list[SplitContact]:
    return (
        db.query(SplitContact)
        .filter(SplitContact.user_id == user_id)
        .order_by(SplitContact.name)
        .all()
    )


def get_contact(db: Session, user_id: int, contact_id: int) -> Optional[SplitContact]:
    return (
        db.query(SplitContact)
        .filter(SplitContact.user_id == user_id, SplitContact.id == contact_id)
        .first()
    )


def create_contact(db: Session, user_id: int, name: str, email: str | None = None, notes: str | None = None) -> SplitContact:
    contact = SplitContact(user_id=user_id, name=name.strip(), email=email, notes=notes)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def update_contact(db: Session, user_id: int, contact_id: int, name: str | None, email: str | None, notes: str | None) -> Optional[SplitContact]:
    contact = get_contact(db, user_id, contact_id)
    if not contact:
        return None
    if name is not None:
        contact.name = name.strip()
    if email is not None:
        contact.email = email or None
    if notes is not None:
        contact.notes = notes or None
    db.commit()
    db.refresh(contact)
    return contact


def delete_contact(db: Session, user_id: int, contact_id: int) -> bool:
    contact = get_contact(db, user_id, contact_id)
    if not contact:
        return False
    db.delete(contact)
    db.commit()
    return True


# ── Split expense helpers ────────────────────────────────────────────────────

def list_splits(db: Session, user_id: int, status: str | None = None) -> list[SplitExpense]:
    q = db.query(SplitExpense).filter(SplitExpense.user_id == user_id)
    if status:
        q = q.filter(SplitExpense.status == status)
    return q.order_by(SplitExpense.date.desc()).all()


def get_split(db: Session, user_id: int, split_id: int) -> Optional[SplitExpense]:
    return (
        db.query(SplitExpense)
        .filter(SplitExpense.user_id == user_id, SplitExpense.id == split_id)
        .first()
    )


def create_split(
    db: Session,
    user_id: int,
    title: str,
    total_amount: Decimal,
    currency_code: str,
    split_date: date,
    participants: list[dict],  # [{"name": str, "amount": Decimal, "contact_id": int|None, "is_payer": bool}]
    notes: str | None = None,
    entry_id: int | None = None,
) -> SplitExpense:
    split = SplitExpense(
        user_id=user_id,
        entry_id=entry_id,
        title=title.strip(),
        total_amount=total_amount,
        currency_code=currency_code,
        date=split_date,
        notes=notes,
        status=SplitStatus.OPEN,
    )
    db.add(split)
    db.flush()  # get split.id before adding participants

    for p in participants:
        participant = SplitParticipant(
            split_expense_id=split.id,
            contact_id=p.get("contact_id"),
            name=p["name"].strip(),
            amount=Decimal(str(p["amount"])),
            is_payer=bool(p.get("is_payer", False)),
            is_settled=bool(p.get("is_payer", False)),  # payer is auto-settled
        )
        db.add(participant)

    db.commit()
    db.refresh(split)
    return split


def delete_split(db: Session, user_id: int, split_id: int) -> bool:
    split = get_split(db, user_id, split_id)
    if not split:
        return False
    db.delete(split)
    db.commit()
    return True


# ── Settle helpers ───────────────────────────────────────────────────────────

def settle_participant(db: Session, user_id: int, split_id: int, participant_id: int) -> Optional[SplitParticipant]:
    """Mark a participant as having settled their share."""
    split = get_split(db, user_id, split_id)
    if not split:
        return None

    participant = (
        db.query(SplitParticipant)
        .filter(
            SplitParticipant.id == participant_id,
            SplitParticipant.split_expense_id == split_id,
        )
        .first()
    )
    if not participant:
        return None

    participant.is_settled = True
    participant.settled_at = datetime.now(UTC).replace(tzinfo=None)

    # If every participant is now settled, mark the whole split as settled
    all_settled = all(p.is_settled for p in split.participants)
    if all_settled:
        split.status = SplitStatus.SETTLED

    db.commit()
    db.refresh(participant)
    return participant


def unsettle_participant(db: Session, user_id: int, split_id: int, participant_id: int) -> Optional[SplitParticipant]:
    split = get_split(db, user_id, split_id)
    if not split:
        return None

    participant = (
        db.query(SplitParticipant)
        .filter(
            SplitParticipant.id == participant_id,
            SplitParticipant.split_expense_id == split_id,
        )
        .first()
    )
    if not participant:
        return None

    participant.is_settled = False
    participant.settled_at = None
    split.status = SplitStatus.OPEN

    db.commit()
    db.refresh(participant)
    return participant


# ── Balance calculation ──────────────────────────────────────────────────────

def get_balances(db: Session, user_id: int) -> dict:
    """
    Returns a dict of contact balances:
    {
      "contacts": [
        {
          "contact_id": 1,
          "contact_name": "Alice",
          "they_owe_you": 25.00,   # they participated in splits where you paid
          "you_owe_them": 10.00,   # you participated in splits where they paid
          "net": 15.00             # positive = they owe you, negative = you owe them
        }
      ],
      "total_you_are_owed": 25.00,
      "total_you_owe": 10.00,
    }
    """
    splits = list_splits(db, user_id)
    contact_data: dict[int, dict] = {}  # contact_id -> {name, they_owe_you, you_owe_them}

    for split in splits:
        if split.status == SplitStatus.SETTLED:
            continue

        # Find who paid
        payers = [p for p in split.participants if p.is_payer]
        non_payers = [p for p in split.participants if not p.is_payer and not p.is_settled]

        for payer in payers:
            # For each unsettled non-payer, the user is owed their amount
            for np in non_payers:
                if np.contact_id:
                    entry = contact_data.setdefault(np.contact_id, {
                        "contact_id": np.contact_id,
                        "contact_name": np.name,
                        "they_owe_you": Decimal("0"),
                        "you_owe_them": Decimal("0"),
                    })
                    entry["they_owe_you"] += np.amount

        # For splits where someone else is the payer and I'm a non-payer
        for np in [p for p in split.participants if not p.is_payer and not p.is_settled]:
            # Check if this participant represents "me" (the owner of this split isn't a contact)
            pass  # Owner is always the payer in this model — contacts owe the user

    result = []
    for cid, data in contact_data.items():
        net = data["they_owe_you"] - data["you_owe_them"]
        result.append({
            "contact_id": cid,
            "contact_name": data["contact_name"],
            "they_owe_you": float(data["they_owe_you"]),
            "you_owe_them": float(data["you_owe_them"]),
            "net": float(net),
        })

    result.sort(key=lambda x: abs(x["net"]), reverse=True)

    total_owed_to_you = sum(r["they_owe_you"] for r in result if r["net"] > 0)
    total_you_owe = sum(r["you_owe_them"] for r in result if r["net"] < 0)

    return {
        "contacts": result,
        "total_you_are_owed": round(total_owed_to_you, 2),
        "total_you_owe": round(total_you_owe, 2),
    }


def split_to_dict(split: SplitExpense) -> dict:
    """Serialize a SplitExpense to a JSON-safe dict."""
    return {
        "id": split.id,
        "title": split.title,
        "total_amount": float(split.total_amount),
        "currency_code": split.currency_code,
        "date": split.date.isoformat(),
        "notes": split.notes,
        "status": split.status,
        "entry_id": split.entry_id,
        "created_at": split.created_at.isoformat(),
        "participants": [
            {
                "id": p.id,
                "name": p.name,
                "amount": float(p.amount),
                "is_payer": p.is_payer,
                "is_settled": p.is_settled,
                "settled_at": p.settled_at.isoformat() if p.settled_at else None,
                "contact_id": p.contact_id,
            }
            for p in split.participants
        ],
    }


def contact_to_dict(contact: SplitContact) -> dict:
    return {
        "id": contact.id,
        "name": contact.name,
        "email": contact.email,
        "notes": contact.notes,
        "created_at": contact.created_at.isoformat(),
    }

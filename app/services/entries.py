from datetime import date
from sqlalchemy.orm import Session
from app.models.entry import Entry


def list_entries(db: Session, user_id: int):
    return (db.query(Entry)
            .filter(Entry.user_id == user_id)
            .order_by(Entry.date.desc(), Entry.id.desc())
            .all()
        )

def create_entry(db: Session,
                 user_id: int,
                 type: str,
                 amount: float,
                 category_id: int | None,
                 note: str | None,
                 date: date
    ) -> Entry:
    e = Entry(user_id=user_id,
              type=type,
              amount=amount,
              category_id=category_id,
              note=note,
              date=date,
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


def delete_entry(db: Session, user_id: int, entry_id: int) -> None:
    e = db.query(Entry).filter(
        Entry.user_id == user_id, Entry.id == entry_id
    ).first()
    if e:
        db.delete(e)
        db.commit()   


def search_entries(db, user_id, *, type=None, category_id=None, q=None, start=None, end=None):
    qry = db.query(Entry).filter(Entry.user_id == user_id)
    if type in ("income", "expense"):
        qry = qry.filter(Entry.type == type)
    if category_id:
        qry = qry.filter(Entry.category_id == category_id)
    if start and end:
        qry = qry.filter(Entry.date.between(start, end))
    if q:
        qry = qry.filter(Entry.note.ilike(f"%{q}%"))
    return qry.order_by(Entry.date.desc(), Entry.id.desc()).limit(200).all()


def update_entry_amount(db: Session, user_id: int, entry_id: int, new_amount: float) -> Entry | None:
    e = db.query(Entry).filter(
        Entry.user_id == user_id, Entry.id == entry_id
    ).first()
    if not e:
        return None
    e.amount = float(new_amount)
    db.commit()
    db.refresh(e)
    return e
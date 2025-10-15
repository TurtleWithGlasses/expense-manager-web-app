from datetime import date
from sqlalchemy.orm import Session
from app.models.entry import Entry
from app.core.currency import currency_service


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
                 date: date,
                 currency_code: str = 'USD',
    ) -> Entry:
    e = Entry(user_id=user_id,
              type=type,
              amount=amount,
              category_id=category_id,
              note=note,
              date=date,
              currency_code=currency_code,
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    
    # Mark all reports as new when a new entry is created
    from app.services.report_status_service import ReportStatusService
    status_service = ReportStatusService(db)
    status_service.mark_all_reports_as_new(user_id)
    
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


async def bulk_update_entry_currencies(db: Session, user_id: int, new_currency: str) -> dict:
    """
    Update all entries for a user to a new currency, converting amounts appropriately.
    Returns statistics about the update operation.
    """
    # Get all entries for the user
    entries = db.query(Entry).filter(Entry.user_id == user_id).all()
    
    if not entries:
        return {
            "updated_count": 0,
            "message": "No entries found to update"
        }
    
    updated_count = 0
    total_entries = len(entries)
    
    # Get current exchange rates
    exchange_rates = await currency_service.get_exchange_rates()
    
    for entry in entries:
        # Skip if already in target currency
        if entry.currency_code == new_currency:
            continue
            
        # Convert amount from current currency to new currency
        if entry.currency_code != new_currency:
            # Convert to USD first, then to target currency
            if entry.currency_code != 'USD':
                from_rate = exchange_rates.get(entry.currency_code, 1.0)
                if from_rate == 0:
                    from_rate = 1.0
                amount_in_usd = float(entry.amount) / from_rate
            else:
                amount_in_usd = float(entry.amount)
            
            # Convert from USD to target currency
            to_rate = exchange_rates.get(new_currency, 1.0)
            converted_amount = amount_in_usd * to_rate
            
            # Update entry
            entry.amount = converted_amount
            entry.currency_code = new_currency
            updated_count += 1
    
    # Commit all changes
    db.commit()
    
    return {
        "updated_count": updated_count,
        "total_entries": total_entries,
        "message": f"Updated {updated_count} out of {total_entries} entries to {new_currency}"
    }
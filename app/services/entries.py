"""
Entries service - Business logic for entry management.

This service handles:
- CRUD operations for entries
- Filtering, sorting, and pagination
- Date and category parsing
- Currency conversion
- User preference handling
"""

from datetime import date
from typing import Optional, Literal
from sqlalchemy.orm import Session

from app.models.entry import Entry
from app.core.currency import currency_service
from app.core.parsers import parse_date as parse_date_util, parse_category_id as parse_category_id_util
from app.core.pagination import calculate_pagination_info as calculate_pagination_info_util
from app.services.user_preferences import user_preferences_service
from app.services.report_status_service import ReportStatusService


class EntriesService:
    """Service for entry operations"""

    @staticmethod
    def parse_date(date_str: str | date | None) -> date | None:
        """
        Parse date from string or date object.

        Args:
            date_str: Date as ISO string, date object, or None

        Returns:
            Date object or None
        """
        return parse_date_util(date_str)

    @staticmethod
    def parse_category_id(category: str | int | None) -> int | None:
        """
        Parse category parameter to integer ID.

        Args:
            category: Category ID as string, int, or None

        Returns:
            Integer category ID or None
        """
        return parse_category_id_util(category)

    @staticmethod
    def get_sort_preferences(
        db: Session,
        user_id: int,
        sort_by: str | None,
        order: str | None,
        page_name: str = 'entries'
    ) -> tuple[str, str]:
        """
        Get sort preferences, either from parameters or user preferences.

        Args:
            db: Database session
            user_id: User ID
            sort_by: Sort field from query params
            order: Sort order from query params
            page_name: Page name for preferences

        Returns:
            Tuple of (sort_by, order)
        """
        if sort_by is None or order is None:
            saved_sort_by, saved_order = user_preferences_service.get_sort_preference(
                db, user_id, page_name
            )
            if sort_by is None:
                sort_by = saved_sort_by
            if order is None:
                order = saved_order
        else:
            # Save the new sort preference
            user_preferences_service.save_sort_preference(
                db, user_id, page_name, sort_by, order
            )

        return sort_by, order

    @staticmethod
    def calculate_pagination_info(
        offset: int,
        limit: int,
        total_count: int
    ) -> dict:
        """
        Calculate pagination information.

        Args:
            offset: Current offset
            limit: Items per page
            total_count: Total number of items

        Returns:
            Dictionary with pagination info
        """
        return calculate_pagination_info_util(offset, limit, total_count)

    @staticmethod
    def list_entries(
        db: Session,
        user_id: int,
        limit: int | None = None,
        offset: int = 0,
        sort_by: str = "date",
        order: str = "desc"
    ) -> list[Entry]:
        """
        List entries with pagination and sorting support.

        Args:
            db: Database session
            user_id: User ID
            limit: Maximum number of entries to return (None = all)
            offset: Number of entries to skip
            sort_by: Field to sort by (date, amount, category)
            order: Sort order (asc or desc)

        Returns:
            List of Entry objects
        """
        query = db.query(Entry).filter(Entry.user_id == user_id)

        # Apply sorting
        if sort_by == "amount":
            sort_field = Entry.amount
        elif sort_by == "category":
            sort_field = Entry.category_id
        else:  # default to date
            sort_field = Entry.date

        # Apply order
        if order == "asc":
            query = query.order_by(sort_field.asc(), Entry.id.desc())
        else:
            query = query.order_by(sort_field.desc(), Entry.id.desc())

        # Apply pagination
        if offset > 0:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return query.all()

    @staticmethod
    def get_entries_count(db: Session, user_id: int) -> int:
        """Get total count of entries for a user."""
        return db.query(Entry).filter(Entry.user_id == user_id).count()

    @staticmethod
    def search_entries(
        db: Session,
        user_id: int,
        *,
        type: Optional[Literal["income", "expense"]] = None,
        category_id: int | None = None,
        q: str | None = None,
        start: date | None = None,
        end: date | None = None,
        limit: int | None = None,
        offset: int = 0,
        sort_by: str = "date",
        order: str = "desc"
    ) -> list[Entry]:
        """
        Search entries with filters, pagination, and sorting.

        Args:
            db: Database session
            user_id: User ID
            type: Entry type filter (income/expense)
            category_id: Category ID filter
            q: Search query for notes
            start: Start date filter
            end: End date filter
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            sort_by: Field to sort by (date, amount, category)
            order: Sort order (asc or desc)

        Returns:
            List of Entry objects
        """
        qry = db.query(Entry).filter(Entry.user_id == user_id)

        if type in ("income", "expense"):
            qry = qry.filter(Entry.type == type)
        if category_id:
            qry = qry.filter(Entry.category_id == category_id)
        if start and end:
            qry = qry.filter(Entry.date.between(start, end))
        if q:
            qry = qry.filter(Entry.note.ilike(f"%{q}%"))

        # Apply sorting
        if sort_by == "amount":
            sort_field = Entry.amount
        elif sort_by == "category":
            sort_field = Entry.category_id
        else:  # default to date
            sort_field = Entry.date

        # Apply order
        if order == "asc":
            qry = qry.order_by(sort_field.asc(), Entry.id.desc())
        else:
            qry = qry.order_by(sort_field.desc(), Entry.id.desc())

        # Apply pagination
        if offset > 0:
            qry = qry.offset(offset)
        if limit is not None:
            qry = qry.limit(limit)

        return qry.all()

    @staticmethod
    def get_search_entries_count(
        db: Session,
        user_id: int,
        *,
        type: Optional[Literal["income", "expense"]] = None,
        category_id: int | None = None,
        q: str | None = None,
        start: date | None = None,
        end: date | None = None
    ) -> int:
        """Get count of filtered entries."""
        qry = db.query(Entry).filter(Entry.user_id == user_id)

        if type in ("income", "expense"):
            qry = qry.filter(Entry.type == type)
        if category_id:
            qry = qry.filter(Entry.category_id == category_id)
        if start and end:
            qry = qry.filter(Entry.date.between(start, end))
        if q:
            qry = qry.filter(Entry.note.ilike(f"%{q}%"))

        return qry.count()

    @staticmethod
    def get_entry_by_id(
        db: Session,
        user_id: int,
        entry_id: int
    ) -> Entry | None:
        """
        Get a single entry by ID with user isolation.

        Args:
            db: Database session
            user_id: User ID (for isolation)
            entry_id: Entry ID

        Returns:
            Entry object or None if not found
        """
        return db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.id == entry_id
        ).first()

    @staticmethod
    def create_entry(
        db: Session,
        user_id: int,
        type: str,
        amount: float,
        date: date,
        category_id: int | None = None,
        note: str | None = None,
        currency_code: str = 'USD',
    ) -> Entry:
        """
        Create a new entry.

        Args:
            db: Database session
            user_id: User ID
            type: Entry type (income/expense)
            amount: Entry amount
            date: Entry date
            category_id: Optional category ID
            note: Optional note
            currency_code: Currency code

        Returns:
            Created Entry object
        """
        entry = Entry(
            user_id=user_id,
            type=type,
            amount=amount,
            category_id=category_id,
            note=note,
            date=date,
            currency_code=currency_code,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)

        # Mark all reports as new when a new entry is created
        status_service = ReportStatusService(db)
        status_service.mark_all_reports_as_new(user_id)

        return entry

    @staticmethod
    def update_entry(
        db: Session,
        user_id: int,
        entry_id: int,
        *,
        type: str | None = None,
        amount: float | None = None,
        date: date | None = None,
        category_id: int | None = None,
        note: str | None = None,
        currency_code: str | None = None
    ) -> Entry | None:
        """
        Update an entry with provided fields.

        Args:
            db: Database session
            user_id: User ID (for isolation)
            entry_id: Entry ID
            type: New entry type
            amount: New amount
            date: New date
            category_id: New category ID
            note: New note
            currency_code: New currency code

        Returns:
            Updated Entry object or None if not found
        """
        entry = db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.id == entry_id
        ).first()

        if not entry:
            return None

        # Update provided fields
        if type is not None:
            entry.type = type
        if amount is not None:
            entry.amount = float(amount)
        if date is not None:
            entry.date = date
        if category_id is not None:
            entry.category_id = category_id
        if note is not None:
            entry.note = note
        if currency_code is not None:
            entry.currency_code = currency_code

        db.commit()
        db.refresh(entry)

        return entry

    @staticmethod
    def update_entry_amount(
        db: Session,
        user_id: int,
        entry_id: int,
        new_amount: float
    ) -> Entry | None:
        """
        Update only the amount of an entry.

        Args:
            db: Database session
            user_id: User ID (for isolation)
            entry_id: Entry ID
            new_amount: New amount

        Returns:
            Updated Entry object or None if not found
        """
        return EntriesService.update_entry(
            db, user_id, entry_id, amount=new_amount
        )

    @staticmethod
    def delete_entry(
        db: Session,
        user_id: int,
        entry_id: int
    ) -> bool:
        """
        Delete an entry.

        Args:
            db: Database session
            user_id: User ID (for isolation)
            entry_id: Entry ID

        Returns:
            True if deleted, False if not found
        """
        entry = db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.id == entry_id
        ).first()

        if not entry:
            return False

        db.delete(entry)
        db.commit()
        return True

    @staticmethod
    def get_uncategorized_entries(
        db: Session,
        user_id: int,
        limit: int | None = None
    ) -> list[Entry]:
        """
        Get entries without a category.

        Args:
            db: Database session
            user_id: User ID
            limit: Maximum number of entries to return

        Returns:
            List of Entry objects without categories
        """
        query = db.query(Entry).filter(
            Entry.user_id == user_id,
            Entry.category_id.is_(None)
        ).order_by(Entry.date.desc())

        if limit is not None:
            query = query.limit(limit)

        return query.all()

    @staticmethod
    async def bulk_update_entry_currencies(
        db: Session,
        user_id: int,
        new_currency: str
    ) -> dict:
        """
        Update all entries for a user to a new currency, converting amounts appropriately.

        Args:
            db: Database session
            user_id: User ID
            new_currency: Target currency code

        Returns:
            Dictionary with update statistics
        """
        # Get all entries for the user
        entries = db.query(Entry).filter(Entry.user_id == user_id).all()

        if not entries:
            return {
                "updated_count": 0,
                "total_entries": 0,
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


# Create singleton instance
entries_service = EntriesService()


# Backward compatibility - keep old function names
def list_entries(db: Session, user_id: int, limit: int | None = None, offset: int = 0,
                 sort_by: str = "date", order: str = "desc"):
    """Legacy function - use entries_service.list_entries instead"""
    return entries_service.list_entries(db, user_id, limit, offset, sort_by, order)


def get_entries_count(db: Session, user_id: int) -> int:
    """Legacy function - use entries_service.get_entries_count instead"""
    return entries_service.get_entries_count(db, user_id)


def create_entry(db: Session, user_id: int, type: str, amount: float, category_id: int | None,
                 note: str | None, date: date, currency_code: str = 'USD') -> Entry:
    """Legacy function - use entries_service.create_entry instead"""
    return entries_service.create_entry(db, user_id, type, amount, date, category_id, note, currency_code)


def delete_entry(db: Session, user_id: int, entry_id: int) -> None:
    """Legacy function - use entries_service.delete_entry instead"""
    entries_service.delete_entry(db, user_id, entry_id)


def search_entries(db, user_id, *, type=None, category_id=None, q=None, start=None, end=None,
                   limit: int | None = None, offset: int = 0, sort_by: str = "date", order: str = "desc"):
    """Legacy function - use entries_service.search_entries instead"""
    return entries_service.search_entries(db, user_id, type=type, category_id=category_id, q=q,
                                         start=start, end=end, limit=limit, offset=offset,
                                         sort_by=sort_by, order=order)


def get_search_entries_count(db, user_id, *, type=None, category_id=None, q=None, start=None, end=None) -> int:
    """Legacy function - use entries_service.get_search_entries_count instead"""
    return entries_service.get_search_entries_count(db, user_id, type=type, category_id=category_id,
                                                    q=q, start=start, end=end)


def update_entry_amount(db: Session, user_id: int, entry_id: int, new_amount: float) -> Entry | None:
    """Legacy function - use entries_service.update_entry_amount instead"""
    return entries_service.update_entry_amount(db, user_id, entry_id, new_amount)


async def bulk_update_entry_currencies(db: Session, user_id: int, new_currency: str) -> dict:
    """Legacy function - use entries_service.bulk_update_entry_currencies instead"""
    return await entries_service.bulk_update_entry_currencies(db, user_id, new_currency)

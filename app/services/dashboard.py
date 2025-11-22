"""
Dashboard service - Business logic for dashboard data aggregation and display.

This service handles:
- Summary calculations (income, expense, balance)
- Entry list retrieval with filtering, sorting, and pagination
- Currency conversion for multi-currency support
- Date range parsing and validation
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, Literal
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.entry import Entry
from app.core.currency import currency_service
from app.services.user_preferences import user_preferences_service
from app.services.metrics import range_summary_multi_currency


class DashboardService:
    """Service for dashboard data operations"""

    @staticmethod
    def parse_date_range(
        start: date | str | None,
        end: date | str | None
    ) -> tuple[date, date]:
        """
        Parse date range, defaulting to current month if not provided.

        Args:
            start: Start date (date object, ISO string, or None)
            end: End date (date object, ISO string, or None)

        Returns:
            Tuple of (start_date, end_date)
        """
        today = date.today()

        if not start or not end:
            # Default to current month
            month_start = today.replace(day=1)
            next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
            month_end = next_month - timedelta(days=1)
            return month_start, month_end

        # Convert strings to dates if needed
        if isinstance(start, str):
            start = datetime.fromisoformat(start).date()
        if isinstance(end, str):
            end = datetime.fromisoformat(end).date()

        return start, end

    @staticmethod
    def parse_category_id(category: str | int | None) -> int | None:
        """
        Parse category parameter to integer ID.

        Args:
            category: Category ID as string, int, or None

        Returns:
            Integer category ID or None
        """
        if category is None:
            return None

        if isinstance(category, int):
            return category

        # String - try to convert
        if isinstance(category, str):
            if not category.strip():
                return None
            try:
                return int(category)
            except ValueError:
                return None

        return None

    @staticmethod
    async def get_summary(
        db: Session,
        user_id: int,
        start_date: date | str | None = None,
        end_date: date | str | None = None,
        category_id: int | str | None = None,
        user_currency: str | None = None
    ) -> dict:
        """
        Get dashboard summary (income, expense, balance) for date range.

        Args:
            db: Database session
            user_id: User ID
            start_date: Start date (defaults to current month start)
            end_date: End date (defaults to current month end)
            category_id: Optional category filter
            user_currency: User's preferred currency (fetched if not provided)

        Returns:
            Dictionary with income, expense, balance (raw and formatted)
        """
        # Parse dates
        s, e = DashboardService.parse_date_range(start_date, end_date)

        # Parse category
        cat_id = DashboardService.parse_category_id(category_id)

        # Get user currency if not provided
        if not user_currency:
            user_currency = user_preferences_service.get_user_currency(db, user_id)

        # Use existing multi-currency summary service
        totals = await range_summary_multi_currency(
            db, user_id, s, e, user_currency, cat_id
        )

        # Format amounts for display
        return {
            "income": totals["income"],
            "expense": totals["expense"],
            "balance": totals["balance"],
            "income_formatted": currency_service.format_amount(
                totals["income"], user_currency
            ),
            "expense_formatted": currency_service.format_amount(
                totals["expense"], user_currency
            ),
            "balance_formatted": currency_service.format_amount(
                totals["balance"], user_currency
            ),
            "currency_code": user_currency,
            "start_date": s,
            "end_date": e
        }

    @staticmethod
    def _build_entry_query(
        db: Session,
        user_id: int,
        entry_type: Literal["income", "expense"],
        start_date: date,
        end_date: date,
        category_id: int | None = None
    ):
        """
        Build base query for entries.

        Args:
            db: Database session
            user_id: User ID
            entry_type: "income" or "expense"
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            category_id: Optional category filter

        Returns:
            SQLAlchemy query object
        """
        # Add 1 day to end_date for exclusive upper bound
        end_next = end_date + timedelta(days=1)

        query = db.query(Entry).filter(
            Entry.user_id == user_id,
            func.lower(Entry.type) == entry_type.lower(),
            Entry.date >= start_date,
            Entry.date < end_next,
        )

        # Add category filter if specified
        if category_id is not None:
            query = query.filter(Entry.category_id == category_id)

        return query

    @staticmethod
    def _apply_sorting(
        query,
        sort_by: str | None,
        order: str | None
    ):
        """
        Apply sorting to entry query.

        Args:
            query: SQLAlchemy query
            sort_by: Field to sort by (date, amount, category)
            order: Sort order (asc, desc)

        Returns:
            Query with sorting applied
        """
        # Determine sort column
        if sort_by == 'amount':
            order_col = Entry.amount
        elif sort_by == 'category':
            order_col = Entry.category_id
        else:  # default to 'date'
            order_col = Entry.date

        # Apply sort order
        if order == 'asc':
            query = query.order_by(order_col.asc())
        else:
            query = query.order_by(order_col.desc())

        return query

    @staticmethod
    async def _convert_entries(
        entries: list[Entry],
        user_currency: str
    ) -> tuple[list[dict], float]:
        """
        Convert entry amounts to user's currency.

        Args:
            entries: List of Entry objects
            user_currency: Target currency code

        Returns:
            Tuple of (converted_rows, total_amount)
        """
        converted_rows = []
        total_amount = 0

        for entry in entries:
            converted_amount = await currency_service.convert_amount(
                float(entry.amount),
                entry.currency_code,
                user_currency
            )

            converted_row = {
                'id': entry.id,
                'date': entry.date,
                'category': entry.category,
                'description': entry.description,
                'note': entry.note,
                'amount': converted_amount,
                'formatted_amount': currency_service.format_amount(
                    converted_amount, user_currency
                )
            }
            converted_rows.append(converted_row)
            total_amount += converted_amount

        return converted_rows, total_amount

    @staticmethod
    async def get_entries_list(
        db: Session,
        user_id: int,
        entry_type: Literal["income", "expense"],
        start_date: date | str | None = None,
        end_date: date | str | None = None,
        category_id: int | str | None = None,
        limit: int = 10,
        offset: int = 0,
        sort_by: str | None = None,
        order: str | None = None,
        user_currency: str | None = None
    ) -> dict:
        """
        Get paginated list of entries with filtering and sorting.

        Args:
            db: Database session
            user_id: User ID
            entry_type: "income" or "expense"
            start_date: Start date filter
            end_date: End date filter
            category_id: Category filter
            limit: Number of entries per page
            offset: Offset for pagination
            sort_by: Field to sort by (date, amount, category)
            order: Sort order (asc, desc)
            user_currency: User's preferred currency

        Returns:
            Dictionary with entries, pagination info, and totals
        """
        # Parse dates
        s, e = DashboardService.parse_date_range(start_date, end_date)

        # Parse category
        cat_id = DashboardService.parse_category_id(category_id)

        # Get user currency if not provided
        if not user_currency:
            user_currency = user_preferences_service.get_user_currency(db, user_id)

        # Handle sort preferences
        if sort_by is None or order is None:
            saved_sort_by, saved_order = user_preferences_service.get_sort_preference(
                db, user_id, 'dashboard'
            )
            if sort_by is None:
                sort_by = saved_sort_by
            if order is None:
                order = saved_order
        else:
            # Save the new sort preference
            user_preferences_service.save_sort_preference(
                db, user_id, 'dashboard', sort_by, order
            )

        # Build query
        query = DashboardService._build_entry_query(
            db, user_id, entry_type, s, e, cat_id
        )

        # Get total count before pagination
        total_count = query.count()

        # Apply sorting
        query = DashboardService._apply_sorting(query, sort_by, order)

        # Apply pagination
        entries = query.offset(offset).limit(limit).all()

        # Convert currencies
        converted_rows, total_amount = await DashboardService._convert_entries(
            entries, user_currency
        )

        # Calculate pagination info
        showing_from = offset + 1 if total_count > 0 else 0
        showing_to = min(offset + limit, total_count)
        has_more = showing_to < total_count

        return {
            "entries": converted_rows,
            "total_amount": total_amount,
            "formatted_total": currency_service.format_amount(
                total_amount, user_currency
            ),
            "limit": limit,
            "offset": offset,
            "total_count": total_count,
            "showing_from": showing_from,
            "showing_to": showing_to,
            "has_more": has_more,
            "currency_code": user_currency
        }

    @staticmethod
    async def get_expenses_list(
        db: Session,
        user_id: int,
        start_date: date | str | None = None,
        end_date: date | str | None = None,
        category_id: int | str | None = None,
        limit: int = 10,
        offset: int = 0,
        sort_by: str | None = None,
        order: str | None = None,
        user_currency: str | None = None
    ) -> dict:
        """
        Get paginated list of expenses.

        Convenience method that calls get_entries_list with entry_type="expense"
        """
        return await DashboardService.get_entries_list(
            db=db,
            user_id=user_id,
            entry_type="expense",
            start_date=start_date,
            end_date=end_date,
            category_id=category_id,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            order=order,
            user_currency=user_currency
        )

    @staticmethod
    async def get_incomes_list(
        db: Session,
        user_id: int,
        start_date: date | str | None = None,
        end_date: date | str | None = None,
        category_id: int | str | None = None,
        limit: int = 10,
        offset: int = 0,
        sort_by: str | None = None,
        order: str | None = None,
        user_currency: str | None = None
    ) -> dict:
        """
        Get paginated list of incomes.

        Convenience method that calls get_entries_list with entry_type="income"
        """
        return await DashboardService.get_entries_list(
            db=db,
            user_id=user_id,
            entry_type="income",
            start_date=start_date,
            end_date=end_date,
            category_id=category_id,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            order=order,
            user_currency=user_currency
        )


# Create singleton instance
dashboard_service = DashboardService()

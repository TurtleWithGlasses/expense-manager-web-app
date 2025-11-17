"""
Unit tests for entries service
Tests all entry-related business logic functions
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, AsyncMock

from app.services import entries
from app.models.entry import Entry


@pytest.mark.unit
class TestListEntries:
    """Tests for list_entries function"""

    def test_list_entries_returns_user_entries_only(self, db_session, test_user, test_user_2, test_categories):
        """Test that list_entries only returns entries for the specified user"""
        # Create entries for test_user
        entry1 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("50.00"),
            category_id=test_categories[0].id,
            date=date.today(),
            note="User 1 entry"
        )
        # Create entry for test_user_2
        entry2 = Entry(
            user_id=test_user_2.id,
            type="expense",
            amount=Decimal("75.00"),
            category_id=test_categories[0].id,
            date=date.today(),
            note="User 2 entry"
        )
        db_session.add_all([entry1, entry2])
        db_session.commit()

        # Get entries for test_user
        user_entries = entries.list_entries(db_session, test_user.id)

        assert len(user_entries) == 1
        assert user_entries[0].user_id == test_user.id
        assert user_entries[0].note == "User 1 entry"

    def test_list_entries_with_pagination(self, db_session, test_user, test_categories):
        """Test pagination with limit and offset"""
        # Create 5 entries
        for i in range(5):
            entry = Entry(
                user_id=test_user.id,
                type="expense",
                amount=Decimal(f"{i+1}0.00"),
                category_id=test_categories[0].id,
                date=date.today() - timedelta(days=i),
                note=f"Entry {i+1}"
            )
            db_session.add(entry)
        db_session.commit()

        # Test limit
        limited_entries = entries.list_entries(db_session, test_user.id, limit=2)
        assert len(limited_entries) == 2

        # Test offset
        offset_entries = entries.list_entries(db_session, test_user.id, limit=2, offset=2)
        assert len(offset_entries) == 2
        assert offset_entries[0].id != limited_entries[0].id

    def test_list_entries_sort_by_date_desc(self, db_session, test_user, test_categories):
        """Test sorting by date in descending order (newest first)"""
        entry1 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("10.00"),
            category_id=test_categories[0].id,
            date=date(2024, 1, 1),
            note="Old entry"
        )
        entry2 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("20.00"),
            category_id=test_categories[0].id,
            date=date(2024, 12, 31),
            note="New entry"
        )
        db_session.add_all([entry1, entry2])
        db_session.commit()

        result = entries.list_entries(db_session, test_user.id, sort_by="date", order="desc")

        assert len(result) == 2
        assert result[0].note == "New entry"  # Newest first
        assert result[1].note == "Old entry"

    def test_list_entries_sort_by_amount_asc(self, db_session, test_user, test_categories):
        """Test sorting by amount in ascending order"""
        entry1 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("100.00"),
            category_id=test_categories[0].id,
            date=date.today(),
            note="High amount"
        )
        entry2 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("10.00"),
            category_id=test_categories[0].id,
            date=date.today(),
            note="Low amount"
        )
        db_session.add_all([entry1, entry2])
        db_session.commit()

        result = entries.list_entries(db_session, test_user.id, sort_by="amount", order="asc")

        assert len(result) == 2
        assert result[0].note == "Low amount"  # Lowest first
        assert result[1].note == "High amount"


@pytest.mark.unit
class TestGetEntriesCount:
    """Tests for get_entries_count function"""

    def test_get_entries_count_returns_correct_count(self, db_session, test_user, test_categories):
        """Test that count matches number of entries"""
        # Create 3 entries
        for i in range(3):
            entry = Entry(
                user_id=test_user.id,
                type="expense",
                amount=Decimal("10.00"),
                category_id=test_categories[0].id,
                date=date.today()
            )
            db_session.add(entry)
        db_session.commit()

        count = entries.get_entries_count(db_session, test_user.id)

        assert count == 3

    def test_get_entries_count_for_user_with_no_entries(self, db_session, test_user):
        """Test count is 0 for user with no entries"""
        count = entries.get_entries_count(db_session, test_user.id)

        assert count == 0


@pytest.mark.unit
class TestCreateEntry:
    """Tests for create_entry function"""

    def test_create_entry_success(self, db_session, test_user, test_categories):
        """Test successful entry creation"""
        with patch('app.services.report_status_service.ReportStatusService'):
            entry = entries.create_entry(
                db=db_session,
                user_id=test_user.id,
                type="expense",
                amount=50.00,
                category_id=test_categories[0].id,
                note="Test expense",
                date=date.today(),
                currency_code="USD"
            )

        assert entry is not None
        assert entry.id is not None
        assert entry.user_id == test_user.id
        assert entry.type == "expense"
        assert entry.amount == Decimal("50.00")
        assert entry.note == "Test expense"
        assert entry.currency_code == "USD"

    def test_create_entry_income(self, db_session, test_user, test_categories):
        """Test creating an income entry"""
        with patch('app.services.report_status_service.ReportStatusService'):
            entry = entries.create_entry(
                db=db_session,
                user_id=test_user.id,
                type="income",
                amount=1000.00,
                category_id=test_categories[0].id,
                note="Salary",
                date=date.today()
            )

        assert entry.type == "income"
        assert entry.amount == Decimal("1000.00")

    def test_create_entry_without_category(self, db_session, test_user):
        """Test creating entry without category"""
        with patch('app.services.report_status_service.ReportStatusService'):
            entry = entries.create_entry(
                db=db_session,
                user_id=test_user.id,
                type="expense",
                amount=25.00,
                category_id=None,
                note="Uncategorized",
                date=date.today()
            )

        assert entry.category_id is None

    def test_create_entry_without_note(self, db_session, test_user, test_categories):
        """Test creating entry without note"""
        with patch('app.services.report_status_service.ReportStatusService'):
            entry = entries.create_entry(
                db=db_session,
                user_id=test_user.id,
                type="expense",
                amount=15.00,
                category_id=test_categories[0].id,
                note=None,
                date=date.today()
            )

        assert entry.note is None

    def test_create_entry_with_different_currency(self, db_session, test_user, test_categories):
        """Test creating entry with non-USD currency"""
        with patch('app.services.report_status_service.ReportStatusService'):
            entry = entries.create_entry(
                db=db_session,
                user_id=test_user.id,
                type="expense",
                amount=100.00,
                category_id=test_categories[0].id,
                note="EUR expense",
                date=date.today(),
                currency_code="EUR"
            )

        assert entry.currency_code == "EUR"


@pytest.mark.unit
class TestDeleteEntry:
    """Tests for delete_entry function"""

    def test_delete_entry_success(self, db_session, test_user, test_categories):
        """Test successful entry deletion"""
        # Create entry
        entry = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("50.00"),
            category_id=test_categories[0].id,
            date=date.today()
        )
        db_session.add(entry)
        db_session.commit()
        entry_id = entry.id

        # Delete entry
        entries.delete_entry(db_session, test_user.id, entry_id)

        # Verify deletion
        deleted_entry = db_session.query(Entry).filter(Entry.id == entry_id).first()
        assert deleted_entry is None

    def test_delete_entry_wrong_user(self, db_session, test_user, test_user_2, test_categories):
        """Test that user cannot delete another user's entry"""
        # Create entry for test_user
        entry = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("50.00"),
            category_id=test_categories[0].id,
            date=date.today()
        )
        db_session.add(entry)
        db_session.commit()
        entry_id = entry.id

        # Try to delete as test_user_2
        entries.delete_entry(db_session, test_user_2.id, entry_id)

        # Entry should still exist
        existing_entry = db_session.query(Entry).filter(Entry.id == entry_id).first()
        assert existing_entry is not None

    def test_delete_nonexistent_entry(self, db_session, test_user):
        """Test deleting non-existent entry doesn't raise error"""
        # Should not raise any exception
        entries.delete_entry(db_session, test_user.id, 99999)


@pytest.mark.unit
class TestSearchEntries:
    """Tests for search_entries function"""

    def test_search_entries_by_type(self, db_session, test_user, test_categories):
        """Test filtering entries by type"""
        # Create income and expense entries
        income = Entry(
            user_id=test_user.id,
            type="income",
            amount=Decimal("1000.00"),
            category_id=test_categories[0].id,
            date=date.today()
        )
        expense = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("50.00"),
            category_id=test_categories[0].id,
            date=date.today()
        )
        db_session.add_all([income, expense])
        db_session.commit()

        # Search for income only
        result = entries.search_entries(db_session, test_user.id, type="income")

        assert len(result) == 1
        assert result[0].type == "income"

    def test_search_entries_by_category(self, db_session, test_user, test_categories):
        """Test filtering entries by category"""
        entry1 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("50.00"),
            category_id=test_categories[0].id,
            date=date.today(),
            note="Category 0"
        )
        entry2 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("75.00"),
            category_id=test_categories[1].id,
            date=date.today(),
            note="Category 1"
        )
        db_session.add_all([entry1, entry2])
        db_session.commit()

        result = entries.search_entries(db_session, test_user.id, category_id=test_categories[0].id)

        assert len(result) == 1
        assert result[0].category_id == test_categories[0].id

    def test_search_entries_by_text(self, db_session, test_user, test_categories):
        """Test searching entries by note text"""
        entry1 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("50.00"),
            category_id=test_categories[0].id,
            date=date.today(),
            note="Coffee at Starbucks"
        )
        entry2 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("75.00"),
            category_id=test_categories[0].id,
            date=date.today(),
            note="Lunch at restaurant"
        )
        db_session.add_all([entry1, entry2])
        db_session.commit()

        result = entries.search_entries(db_session, test_user.id, q="coffee")

        assert len(result) == 1
        assert "Coffee" in result[0].note

    def test_search_entries_by_date_range(self, db_session, test_user, test_categories):
        """Test filtering entries by date range"""
        entry1 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("50.00"),
            category_id=test_categories[0].id,
            date=date(2024, 1, 15)
        )
        entry2 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("75.00"),
            category_id=test_categories[0].id,
            date=date(2024, 2, 15)
        )
        entry3 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("100.00"),
            category_id=test_categories[0].id,
            date=date(2024, 3, 15)
        )
        db_session.add_all([entry1, entry2, entry3])
        db_session.commit()

        result = entries.search_entries(
            db_session,
            test_user.id,
            start=date(2024, 1, 1),
            end=date(2024, 2, 28)
        )

        assert len(result) == 2

    def test_search_entries_with_pagination(self, db_session, test_user, test_categories):
        """Test search with pagination"""
        # Create 5 entries
        for i in range(5):
            entry = Entry(
                user_id=test_user.id,
                type="expense",
                amount=Decimal("50.00"),
                category_id=test_categories[0].id,
                date=date.today()
            )
            db_session.add(entry)
        db_session.commit()

        result = entries.search_entries(db_session, test_user.id, limit=2, offset=1)

        assert len(result) == 2


@pytest.mark.unit
class TestGetSearchEntriesCount:
    """Tests for get_search_entries_count function"""

    def test_count_matches_search_results(self, db_session, test_user, test_categories):
        """Test that count matches filtered results"""
        # Create 2 income and 3 expense entries
        for i in range(2):
            income = Entry(
                user_id=test_user.id,
                type="income",
                amount=Decimal("1000.00"),
                category_id=test_categories[0].id,
                date=date.today()
            )
            db_session.add(income)

        for i in range(3):
            expense = Entry(
                user_id=test_user.id,
                type="expense",
                amount=Decimal("50.00"),
                category_id=test_categories[0].id,
                date=date.today()
            )
            db_session.add(expense)
        db_session.commit()

        count = entries.get_search_entries_count(db_session, test_user.id, type="expense")

        assert count == 3


@pytest.mark.unit
class TestUpdateEntryAmount:
    """Tests for update_entry_amount function"""

    def test_update_entry_amount_success(self, db_session, test_user, test_categories):
        """Test successful amount update"""
        # Create entry
        entry = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("50.00"),
            category_id=test_categories[0].id,
            date=date.today()
        )
        db_session.add(entry)
        db_session.commit()
        entry_id = entry.id

        # Update amount
        updated_entry = entries.update_entry_amount(db_session, test_user.id, entry_id, 75.50)

        assert updated_entry is not None
        assert updated_entry.amount == Decimal("75.50")

    def test_update_entry_amount_wrong_user(self, db_session, test_user, test_user_2, test_categories):
        """Test that user cannot update another user's entry"""
        # Create entry for test_user
        entry = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("50.00"),
            category_id=test_categories[0].id,
            date=date.today()
        )
        db_session.add(entry)
        db_session.commit()
        entry_id = entry.id

        # Try to update as test_user_2
        result = entries.update_entry_amount(db_session, test_user_2.id, entry_id, 100.00)

        assert result is None
        # Verify amount wasn't changed
        db_session.refresh(entry)
        assert entry.amount == Decimal("50.00")

    def test_update_nonexistent_entry(self, db_session, test_user):
        """Test updating non-existent entry returns None"""
        result = entries.update_entry_amount(db_session, test_user.id, 99999, 100.00)

        assert result is None


@pytest.mark.unit
class TestBulkUpdateEntryCurrencies:
    """Tests for bulk_update_entry_currencies function"""

    @pytest.mark.asyncio
    async def test_bulk_update_converts_currencies(self, db_session, test_user, test_categories):
        """Test bulk currency update with conversion"""
        # Create entries with different currencies
        entry1 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("100.00"),
            category_id=test_categories[0].id,
            date=date.today(),
            currency_code="USD"
        )
        entry2 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("50.00"),
            category_id=test_categories[0].id,
            date=date.today(),
            currency_code="USD"
        )
        db_session.add_all([entry1, entry2])
        db_session.commit()

        # Mock exchange rates
        mock_rates = {"USD": 1.0, "EUR": 0.85}
        with patch('app.services.entries.currency_service.get_exchange_rates',
                   new=AsyncMock(return_value=mock_rates)):
            result = await entries.bulk_update_entry_currencies(db_session, test_user.id, "EUR")

        assert result["updated_count"] == 2
        assert result["total_entries"] == 2

        # Verify currencies were updated
        db_session.refresh(entry1)
        db_session.refresh(entry2)
        assert entry1.currency_code == "EUR"
        assert entry2.currency_code == "EUR"

    @pytest.mark.asyncio
    async def test_bulk_update_no_entries(self, db_session, test_user):
        """Test bulk update with no entries"""
        result = await entries.bulk_update_entry_currencies(db_session, test_user.id, "EUR")

        assert result["updated_count"] == 0
        assert "No entries found" in result["message"]

    @pytest.mark.asyncio
    async def test_bulk_update_skips_matching_currency(self, db_session, test_user, test_categories):
        """Test that entries already in target currency are skipped"""
        # Create entry already in EUR
        entry = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("100.00"),
            category_id=test_categories[0].id,
            date=date.today(),
            currency_code="EUR"
        )
        db_session.add(entry)
        db_session.commit()
        original_amount = entry.amount

        mock_rates = {"USD": 1.0, "EUR": 0.85}
        with patch('app.services.entries.currency_service.get_exchange_rates',
                   new=AsyncMock(return_value=mock_rates)):
            result = await entries.bulk_update_entry_currencies(db_session, test_user.id, "EUR")

        # Should skip this entry
        assert result["updated_count"] == 0
        db_session.refresh(entry)
        assert entry.amount == original_amount

"""
Unit tests for dashboard service.

Tests business logic for dashboard data operations including:
- Date range parsing
- Category ID parsing
- Summary calculations
- Entry list retrieval with filtering, sorting, and pagination
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock

from app.services.dashboard import DashboardService, dashboard_service
from app.models.entry import Entry
from app.models.category import Category


@pytest.mark.unit
class TestDateRangeParsing:
    """Tests for date range parsing logic"""

    def test_parse_date_range_with_none_returns_current_month(self):
        """Test that None dates default to current month"""
        start, end = DashboardService.parse_date_range(None, None)

        today = date.today()
        month_start = today.replace(day=1)
        next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        month_end = next_month - timedelta(days=1)

        assert start == month_start
        assert end == month_end

    def test_parse_date_range_with_date_objects(self):
        """Test parsing with date objects"""
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 31)

        start, end = DashboardService.parse_date_range(start_date, end_date)

        assert start == start_date
        assert end == end_date

    def test_parse_date_range_with_iso_strings(self):
        """Test parsing with ISO date strings"""
        start, end = DashboardService.parse_date_range("2025-01-01", "2025-01-31")

        assert start == date(2025, 1, 1)
        assert end == date(2025, 1, 31)

    def test_parse_date_range_with_empty_strings(self):
        """Test that empty strings default to current month"""
        start, end = DashboardService.parse_date_range("", "")

        today = date.today()
        month_start = today.replace(day=1)

        assert start == month_start


@pytest.mark.unit
class TestGetSummary:
    """Tests for dashboard summary calculation"""

    @pytest.mark.asyncio
    async def test_get_summary_basic(self, db_session, test_user):
        """Test basic summary calculation"""
        with patch('app.services.dashboard.range_summary_multi_currency') as mock_summary:
            mock_summary.return_value = {
                "income": 1000.00,
                "expense": 500.00,
                "balance": 500.00
            }

            with patch('app.services.dashboard.user_preferences_service.get_user_currency') as mock_currency:
                mock_currency.return_value = "USD"

                result = await DashboardService.get_summary(
                    db=db_session,
                    user_id=test_user.id
                )

                assert result["income"] == 1000.00
                assert result["expense"] == 500.00
                assert result["balance"] == 500.00
                assert "income_formatted" in result
                assert "expense_formatted" in result
                assert "balance_formatted" in result
                assert result["currency_code"] == "USD"
                assert "start_date" in result
                assert "end_date" in result

    @pytest.mark.asyncio
    async def test_get_summary_with_date_range(self, db_session, test_user):
        """Test summary with specific date range"""
        with patch('app.services.dashboard.range_summary_multi_currency') as mock_summary:
            mock_summary.return_value = {
                "income": 2000.00,
                "expense": 1500.00,
                "balance": 500.00
            }

            with patch('app.services.dashboard.user_preferences_service.get_user_currency') as mock_currency:
                mock_currency.return_value = "USD"

                result = await DashboardService.get_summary(
                    db=db_session,
                    user_id=test_user.id,
                    start_date="2025-01-01",
                    end_date="2025-01-31"
                )

                assert result["start_date"] == date(2025, 1, 1)
                assert result["end_date"] == date(2025, 1, 31)

    @pytest.mark.asyncio
    async def test_get_summary_with_category_filter(self, db_session, test_user):
        """Test summary with category filter"""
        with patch('app.services.dashboard.range_summary_multi_currency') as mock_summary:
            mock_summary.return_value = {
                "income": 0.00,
                "expense": 300.00,
                "balance": -300.00
            }

            with patch('app.services.dashboard.user_preferences_service.get_user_currency') as mock_currency:
                mock_currency.return_value = "USD"

                result = await DashboardService.get_summary(
                    db=db_session,
                    user_id=test_user.id,
                    category_id=5
                )

                # Verify range_summary_multi_currency was called with category_id
                mock_summary.assert_called_once()
                call_args = mock_summary.call_args
                # Check that category_id=5 was passed (it's the 6th positional arg or a keyword arg)
                assert call_args[0][5] == 5 or call_args[1].get('category_id') == 5


@pytest.mark.unit
class TestGetEntriesList:
    """Tests for entries list retrieval"""

    @pytest.mark.asyncio
    async def test_get_expenses_list_basic(self, db_session, test_user, test_categories):
        """Test basic expenses list retrieval"""
        # Create test expense entries
        expense1 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("50.00"),
            date=date.today(),
            category_id=test_categories[0].id,
            currency_code="USD"
        )
        expense2 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("100.00"),
            date=date.today() - timedelta(days=1),
            category_id=test_categories[1].id,
            currency_code="USD"
        )
        db_session.add_all([expense1, expense2])
        db_session.commit()

        with patch('app.services.dashboard.user_preferences_service.get_user_currency') as mock_currency:
            mock_currency.return_value = "USD"

            with patch('app.services.dashboard.user_preferences_service.get_sort_preference') as mock_sort:
                mock_sort.return_value = ("date", "desc")

                with patch('app.services.dashboard.currency_service.convert_amount') as mock_convert:
                    mock_convert.side_effect = lambda amt, from_cur, to_cur: amt

                    with patch('app.services.dashboard.currency_service.format_amount') as mock_format:
                        mock_format.side_effect = lambda amt, cur: f"${amt:.2f}"

                        result = await DashboardService.get_expenses_list(
                            db=db_session,
                            user_id=test_user.id
                        )

                        assert len(result["entries"]) == 2
                        assert result["total_count"] == 2
                        assert result["limit"] == 10
                        assert result["offset"] == 0
                        assert result["showing_from"] == 1
                        assert result["showing_to"] == 2
                        assert result["has_more"] is False

    @pytest.mark.asyncio
    async def test_get_incomes_list_basic(self, db_session, test_user):
        """Test basic incomes list retrieval"""
        # Create test income entries
        income1 = Entry(
            user_id=test_user.id,
            type="income",
            amount=Decimal("1000.00"),
            date=date.today(),
            currency_code="USD"
        )
        db_session.add(income1)
        db_session.commit()

        with patch('app.services.dashboard.user_preferences_service.get_user_currency') as mock_currency:
            mock_currency.return_value = "USD"

            with patch('app.services.dashboard.user_preferences_service.get_sort_preference') as mock_sort:
                mock_sort.return_value = ("date", "desc")

                with patch('app.services.dashboard.currency_service.convert_amount') as mock_convert:
                    mock_convert.side_effect = lambda amt, from_cur, to_cur: amt

                    with patch('app.services.dashboard.currency_service.format_amount') as mock_format:
                        mock_format.side_effect = lambda amt, cur: f"${amt:.2f}"

                        result = await DashboardService.get_incomes_list(
                            db=db_session,
                            user_id=test_user.id
                        )

                        assert len(result["entries"]) == 1
                        assert result["entries"][0]["amount"] == 1000.00

    @pytest.mark.asyncio
    async def test_get_entries_list_with_pagination(self, db_session, test_user):
        """Test entries list with pagination"""
        # Create 15 expense entries
        for i in range(15):
            entry = Entry(
                user_id=test_user.id,
                type="expense",
                amount=Decimal(f"{i+1}.00"),
                date=date.today() - timedelta(days=i),
                currency_code="USD"
            )
            db_session.add(entry)
        db_session.commit()

        with patch('app.services.dashboard.user_preferences_service.get_user_currency') as mock_currency:
            mock_currency.return_value = "USD"

            with patch('app.services.dashboard.user_preferences_service.get_sort_preference') as mock_sort:
                mock_sort.return_value = ("date", "desc")

                with patch('app.services.dashboard.currency_service.convert_amount') as mock_convert:
                    mock_convert.side_effect = lambda amt, from_cur, to_cur: amt

                    with patch('app.services.dashboard.currency_service.format_amount') as mock_format:
                        mock_format.side_effect = lambda amt, cur: f"${amt:.2f}"

                        # Get first page
                        result = await DashboardService.get_expenses_list(
                            db=db_session,
                            user_id=test_user.id,
                            limit=10,
                            offset=0
                        )

                        assert len(result["entries"]) == 10
                        assert result["total_count"] == 15
                        assert result["showing_from"] == 1
                        assert result["showing_to"] == 10
                        assert result["has_more"] is True

                        # Get second page
                        result2 = await DashboardService.get_expenses_list(
                            db=db_session,
                            user_id=test_user.id,
                            limit=10,
                            offset=10
                        )

                        assert len(result2["entries"]) == 5
                        assert result2["showing_from"] == 11
                        assert result2["showing_to"] == 15
                        assert result2["has_more"] is False

    @pytest.mark.asyncio
    async def test_get_entries_list_with_category_filter(self, db_session, test_user, test_categories):
        """Test entries list with category filter"""
        # Create entries in different categories
        entry1 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("50.00"),
            date=date.today(),
            category_id=test_categories[0].id,
            currency_code="USD"
        )
        entry2 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("100.00"),
            date=date.today(),
            category_id=test_categories[1].id,
            currency_code="USD"
        )
        db_session.add_all([entry1, entry2])
        db_session.commit()

        with patch('app.services.dashboard.user_preferences_service.get_user_currency') as mock_currency:
            mock_currency.return_value = "USD"

            with patch('app.services.dashboard.user_preferences_service.get_sort_preference') as mock_sort:
                mock_sort.return_value = ("date", "desc")

                with patch('app.services.dashboard.currency_service.convert_amount') as mock_convert:
                    mock_convert.side_effect = lambda amt, from_cur, to_cur: amt

                    with patch('app.services.dashboard.currency_service.format_amount') as mock_format:
                        mock_format.side_effect = lambda amt, cur: f"${amt:.2f}"

                        # Filter by first category
                        result = await DashboardService.get_expenses_list(
                            db=db_session,
                            user_id=test_user.id,
                            category_id=test_categories[0].id
                        )

                        assert len(result["entries"]) == 1
                        assert result["entries"][0]["amount"] == 50.00

    @pytest.mark.asyncio
    async def test_get_entries_list_with_sorting(self, db_session, test_user):
        """Test entries list with sorting"""
        # Create entries with different amounts
        entry1 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("100.00"),
            date=date.today(),
            currency_code="USD"
        )
        entry2 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("50.00"),
            date=date.today(),
            currency_code="USD"
        )
        db_session.add_all([entry1, entry2])
        db_session.commit()

        with patch('app.services.dashboard.user_preferences_service.get_user_currency') as mock_currency:
            mock_currency.return_value = "USD"

            with patch('app.services.dashboard.user_preferences_service.save_sort_preference') as mock_save:
                with patch('app.services.dashboard.currency_service.convert_amount') as mock_convert:
                    mock_convert.side_effect = lambda amt, from_cur, to_cur: amt

                    with patch('app.services.dashboard.currency_service.format_amount') as mock_format:
                        mock_format.side_effect = lambda amt, cur: f"${amt:.2f}"

                        # Sort by amount ascending
                        result = await DashboardService.get_expenses_list(
                            db=db_session,
                            user_id=test_user.id,
                            sort_by="amount",
                            order="asc"
                        )

                        assert len(result["entries"]) == 2
                        assert result["entries"][0]["amount"] == 50.00
                        assert result["entries"][1]["amount"] == 100.00

                        # Verify sort preference was saved
                        mock_save.assert_called_once_with(
                            db_session, test_user.id, 'dashboard', 'amount', 'asc'
                        )

    @pytest.mark.asyncio
    async def test_get_entries_list_user_isolation(self, db_session, test_user, test_user_2):
        """Test that users only see their own entries"""
        # Create entries for both users
        entry1 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("50.00"),
            date=date.today(),
            currency_code="USD"
        )
        entry2 = Entry(
            user_id=test_user_2.id,
            type="expense",
            amount=Decimal("100.00"),
            date=date.today(),
            currency_code="USD"
        )
        db_session.add_all([entry1, entry2])
        db_session.commit()

        with patch('app.services.dashboard.user_preferences_service.get_user_currency') as mock_currency:
            mock_currency.return_value = "USD"

            with patch('app.services.dashboard.user_preferences_service.get_sort_preference') as mock_sort:
                mock_sort.return_value = ("date", "desc")

                with patch('app.services.dashboard.currency_service.convert_amount') as mock_convert:
                    mock_convert.side_effect = lambda amt, from_cur, to_cur: amt

                    with patch('app.services.dashboard.currency_service.format_amount') as mock_format:
                        mock_format.side_effect = lambda amt, cur: f"${amt:.2f}"

                        # User 1 should only see their entry
                        result = await DashboardService.get_expenses_list(
                            db=db_session,
                            user_id=test_user.id
                        )

                        assert len(result["entries"]) == 1
                        assert result["entries"][0]["amount"] == 50.00


@pytest.mark.unit
class TestDashboardServiceSingleton:
    """Tests for dashboard_service singleton instance"""

    def test_dashboard_service_instance_exists(self):
        """Test that dashboard_service singleton is accessible"""
        assert dashboard_service is not None
        assert isinstance(dashboard_service, DashboardService)

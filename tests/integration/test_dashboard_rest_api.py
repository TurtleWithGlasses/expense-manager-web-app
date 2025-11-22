"""
Integration tests for dashboard REST API endpoints
Tests the complete HTTP request/response cycle for RESTful JSON dashboard endpoints
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from app.models.entry import Entry
from app.models.category import Category


@pytest.mark.integration
class TestDashboardSummaryEndpoint:
    """Tests for GET /api/dashboard/summary endpoint"""

    @pytest.mark.asyncio
    async def test_get_summary_default_current_month(self, authenticated_client, db_session, test_user):
        """Test summary defaults to current month"""
        # Create test entries for current month
        today = date.today()
        entry_income = Entry(
            user_id=test_user.id,
            type="income",
            amount=Decimal("2000.00"),
            date=today,
            currency_code="USD"
        )
        entry_expense = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("500.00"),
            date=today,
            currency_code="USD"
        )
        db_session.add_all([entry_income, entry_expense])
        db_session.commit()

        response = authenticated_client.get("/api/dashboard/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "income" in data["data"]
        assert "expense" in data["data"]
        assert "balance" in data["data"]
        assert "income_formatted" in data["data"]
        assert "expense_formatted" in data["data"]
        assert "balance_formatted" in data["data"]
        assert "currency_code" in data["data"]
        assert "start_date" in data["data"]
        assert "end_date" in data["data"]

    @pytest.mark.asyncio
    async def test_get_summary_with_date_range(self, authenticated_client, db_session, test_user):
        """Test summary with specific date range"""
        # Create entries
        entry = Entry(
            user_id=test_user.id,
            type="income",
            amount=Decimal("1500.00"),
            date=date(2025, 1, 15),
            currency_code="USD"
        )
        db_session.add(entry)
        db_session.commit()

        response = authenticated_client.get(
            "/api/dashboard/summary?start=2025-01-01&end=2025-01-31"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["start_date"] == "2025-01-01"
        assert data["data"]["end_date"] == "2025-01-31"

    @pytest.mark.asyncio
    async def test_get_summary_with_category_filter(self, authenticated_client, db_session, test_user, test_categories):
        """Test summary with category filter"""
        entry = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("300.00"),
            date=date.today(),
            category_id=test_categories[0].id,
            currency_code="USD"
        )
        db_session.add(entry)
        db_session.commit()

        response = authenticated_client.get(
            f"/api/dashboard/summary?category_id={test_categories[0].id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_get_summary_user_isolation(self, authenticated_client, db_session, test_user, test_user_2):
        """Test summary only includes current user's data"""
        # Create entries for both users
        entry_user1 = Entry(
            user_id=test_user.id,
            type="income",
            amount=Decimal("1000.00"),
            date=date.today(),
            currency_code="USD"
        )
        entry_user2 = Entry(
            user_id=test_user_2.id,
            type="income",
            amount=Decimal("5000.00"),
            date=date.today(),
            currency_code="USD"
        )
        db_session.add_all([entry_user1, entry_user2])
        db_session.commit()

        response = authenticated_client.get("/api/dashboard/summary")

        assert response.status_code == 200
        data = response.json()
        # Should only reflect user1's income
        assert data["data"]["income"] < 5000.00


@pytest.mark.integration
class TestDashboardExpensesEndpoint:
    """Tests for GET /api/dashboard/expenses endpoint"""

    @pytest.mark.asyncio
    async def test_get_expenses_list_basic(self, authenticated_client, db_session, test_user):
        """Test basic expenses list retrieval"""
        # Create test expenses
        expense1 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("50.00"),
            date=date.today(),
            currency_code="USD"
        )
        expense2 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("100.00"),
            date=date.today() - timedelta(days=1),
            currency_code="USD"
        )
        db_session.add_all([expense1, expense2])
        db_session.commit()

        response = authenticated_client.get("/api/dashboard/expenses")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "entries" in data["data"]
        assert "total_amount" in data["data"]
        assert "formatted_total" in data["data"]
        assert "currency_code" in data["data"]
        assert "pagination" in data["data"]
        assert len(data["data"]["entries"]) >= 2

    @pytest.mark.asyncio
    async def test_get_expenses_list_pagination(self, authenticated_client, db_session, test_user):
        """Test expenses list pagination"""
        # Create 15 expenses
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

        # Get first page
        response = authenticated_client.get("/api/dashboard/expenses?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["entries"]) == 10
        assert data["data"]["pagination"]["total_count"] >= 15
        assert data["data"]["pagination"]["has_more"] is True

        # Get second page
        response2 = authenticated_client.get("/api/dashboard/expenses?limit=10&offset=10")
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["data"]["entries"]) >= 5

    @pytest.mark.asyncio
    async def test_get_expenses_list_with_date_range(self, authenticated_client, db_session, test_user):
        """Test expenses list with date range filter"""
        entry_in_range = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("100.00"),
            date=date(2025, 1, 15),
            currency_code="USD"
        )
        entry_out_range = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("200.00"),
            date=date(2025, 2, 15),
            currency_code="USD"
        )
        db_session.add_all([entry_in_range, entry_out_range])
        db_session.commit()

        response = authenticated_client.get(
            "/api/dashboard/expenses?start=2025-01-01&end=2025-01-31"
        )

        assert response.status_code == 200
        data = response.json()
        # Should only include January entry
        assert data["data"]["total_amount"] == 100.00

    @pytest.mark.asyncio
    async def test_get_expenses_list_sorting(self, authenticated_client, db_session, test_user):
        """Test expenses list sorting"""
        expense1 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("100.00"),
            date=date.today(),
            currency_code="USD"
        )
        expense2 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("50.00"),
            date=date.today(),
            currency_code="USD"
        )
        db_session.add_all([expense1, expense2])
        db_session.commit()

        response = authenticated_client.get(
            "/api/dashboard/expenses?sort_by=amount&order=asc"
        )

        assert response.status_code == 200
        data = response.json()
        entries = data["data"]["entries"]
        assert len(entries) >= 2
        # First entry should have smaller amount
        assert entries[0]["amount"] <= entries[1]["amount"]

    @pytest.mark.asyncio
    async def test_get_expenses_list_user_isolation(self, authenticated_client, db_session, test_user, test_user_2):
        """Test expenses list only shows current user's data"""
        expense_user1 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("50.00"),
            date=date.today(),
            note="User 1 expense",
            currency_code="USD"
        )
        expense_user2 = Entry(
            user_id=test_user_2.id,
            type="expense",
            amount=Decimal("100.00"),
            date=date.today(),
            note="User 2 expense",
            currency_code="USD"
        )
        db_session.add_all([expense_user1, expense_user2])
        db_session.commit()

        response = authenticated_client.get("/api/dashboard/expenses")

        assert response.status_code == 200
        data = response.json()
        entry_notes = [e.get("note") for e in data["data"]["entries"]]
        assert "User 1 expense" in entry_notes
        assert "User 2 expense" not in entry_notes


@pytest.mark.integration
class TestDashboardIncomesEndpoint:
    """Tests for GET /api/dashboard/incomes endpoint"""

    @pytest.mark.asyncio
    async def test_get_incomes_list_basic(self, authenticated_client, db_session, test_user):
        """Test basic incomes list retrieval"""
        income1 = Entry(
            user_id=test_user.id,
            type="income",
            amount=Decimal("1000.00"),
            date=date.today(),
            currency_code="USD"
        )
        income2 = Entry(
            user_id=test_user.id,
            type="income",
            amount=Decimal("500.00"),
            date=date.today() - timedelta(days=1),
            currency_code="USD"
        )
        db_session.add_all([income1, income2])
        db_session.commit()

        response = authenticated_client.get("/api/dashboard/incomes")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "entries" in data["data"]
        assert "total_amount" in data["data"]
        assert "formatted_total" in data["data"]
        assert "currency_code" in data["data"]
        assert "pagination" in data["data"]
        assert len(data["data"]["entries"]) >= 2

    @pytest.mark.asyncio
    async def test_get_incomes_list_pagination(self, authenticated_client, db_session, test_user):
        """Test incomes list pagination"""
        # Create 12 incomes
        for i in range(12):
            entry = Entry(
                user_id=test_user.id,
                type="income",
                amount=Decimal(f"{(i+1)*100}.00"),
                date=date.today() - timedelta(days=i),
                currency_code="USD"
            )
            db_session.add(entry)
        db_session.commit()

        response = authenticated_client.get("/api/dashboard/incomes?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["entries"]) == 10
        assert data["data"]["pagination"]["has_more"] is True

    @pytest.mark.asyncio
    async def test_get_incomes_list_with_category(self, authenticated_client, db_session, test_user, test_categories):
        """Test incomes list with category filter"""
        income = Entry(
            user_id=test_user.id,
            type="income",
            amount=Decimal("2000.00"),
            date=date.today(),
            category_id=test_categories[0].id,
            currency_code="USD"
        )
        db_session.add(income)
        db_session.commit()

        response = authenticated_client.get(
            f"/api/dashboard/incomes?category_id={test_categories[0].id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["entries"]) >= 1

    @pytest.mark.asyncio
    async def test_get_incomes_list_user_isolation(self, authenticated_client, db_session, test_user, test_user_2):
        """Test incomes list only shows current user's data"""
        income_user1 = Entry(
            user_id=test_user.id,
            type="income",
            amount=Decimal("1000.00"),
            date=date.today(),
            note="User 1 income",
            currency_code="USD"
        )
        income_user2 = Entry(
            user_id=test_user_2.id,
            type="income",
            amount=Decimal("5000.00"),
            date=date.today(),
            note="User 2 income",
            currency_code="USD"
        )
        db_session.add_all([income_user1, income_user2])
        db_session.commit()

        response = authenticated_client.get("/api/dashboard/incomes")

        assert response.status_code == 200
        data = response.json()
        entry_notes = [e.get("note") for e in data["data"]["entries"]]
        assert "User 1 income" in entry_notes
        assert "User 2 income" not in entry_notes

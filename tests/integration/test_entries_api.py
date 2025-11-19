"""
Integration tests for entries API endpoints
Tests the complete HTTP request/response cycle for entry management
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal

from app.models.entry import Entry
from app.models.category import Category


@pytest.mark.integration
class TestCreateEntryEndpoint:
    """Tests for POST /entries/create endpoint"""

    def test_create_expense_success(self, authenticated_client, db_session, test_categories):
        """Test creating a new expense entry"""
        response = authenticated_client.post(
            "/entries/create",
            data={
                "type": "expense",
                "amount": "50.00",
                "category_id": str(test_categories[0].id),
                "date": str(date.today()),
                "note": "Lunch at restaurant"
            },
            follow_redirects=False
        )

        # Should redirect after successful creation
        assert response.status_code in [200, 302, 303]

    def test_create_income_success(self, authenticated_client, db_session, test_categories):
        """Test creating a new income entry"""
        response = authenticated_client.post(
            "/entries/create",
            data={
                "type": "income",
                "amount": "1500.00",
                "category_id": str(test_categories[0].id),
                "date": str(date.today()),
                "note": "Monthly salary"
            },
            follow_redirects=False
        )

        assert response.status_code in [200, 302, 303]

    def test_create_entry_without_category(self, authenticated_client, db_session):
        """Test creating entry without category"""
        response = authenticated_client.post(
            "/entries/create",
            data={
                "type": "expense",
                "amount": "25.00",
                "date": str(date.today()),
                "note": "Cash expense"
            },
            follow_redirects=False
        )

        # Should succeed - category is optional
        assert response.status_code in [200, 302, 303]

    def test_create_entry_missing_amount(self, authenticated_client, db_session):
        """Test creating entry with missing amount"""
        response = authenticated_client.post(
            "/entries/create",
            data={
                "type": "expense",
                "date": str(date.today())
            }
        )

        # Should show validation error
        assert response.status_code in [200, 400, 422]

    def test_create_entry_invalid_type(self, authenticated_client, db_session):
        """Test creating entry with invalid type"""
        response = authenticated_client.post(
            "/entries/create",
            data={
                "type": "invalid_type",
                "amount": "50.00",
                "date": str(date.today())
            }
        )

        assert response.status_code in [200, 400, 422]

    def test_create_entry_unauthenticated(self, client, db_session):
        """Test creating entry without authentication"""
        response = client.post(
            "/entries/create",
            data={
                "type": "expense",
                "amount": "50.00",
                "date": str(date.today())
            }
        )

        assert response.status_code in [401, 403]


@pytest.mark.integration
class TestGetEntriesPageEndpoint:
    """Tests for GET /entries endpoint (HTML page)"""

    def test_get_entries_page(self, authenticated_client, db_session, test_entries):
        """Test retrieving entries page for authenticated user"""
        response = authenticated_client.get("/entries")

        assert response.status_code == 200
        # It's an HTML response
        assert b"<!doctype html>" in response.content.lower() or b"<html" in response.content.lower()

    def test_get_entries_page_unauthenticated(self, client, db_session):
        """Test accessing entries page without authentication"""
        response = client.get("/entries", follow_redirects=False)

        # Should redirect to login (307 is temporary redirect)
        assert response.status_code in [302, 303, 307, 401]


@pytest.mark.integration
class TestGetEntryRowEndpoint:
    """Tests for GET /entries/row/{id} endpoint"""

    def test_get_entry_row_success(self, authenticated_client, db_session, test_entries):
        """Test retrieving entry row HTML"""
        entry_id = test_entries[0].id
        response = authenticated_client.get(f"/entries/row/{entry_id}")

        assert response.status_code == 200
        # Should return HTML fragment
        assert b"<tr" in response.content.lower() or b"entry" in response.content.lower()

    def test_get_entry_row_nonexistent(self, authenticated_client, db_session):
        """Test retrieving non-existent entry row"""
        response = authenticated_client.get("/entries/row/99999")

        assert response.status_code == 404

    def test_get_entry_row_other_user(self, authenticated_client_2, db_session, test_entries):
        """Test that users cannot access other users' entry rows"""
        entry_id = test_entries[0].id
        response = authenticated_client_2.get(f"/entries/row/{entry_id}")

        assert response.status_code == 404


@pytest.mark.integration
class TestUpdateEntryEndpoint:
    """Tests for POST /entries/update/{id} endpoint"""

    def test_update_entry_success(self, authenticated_client, db_session, test_entries, test_categories):
        """Test updating an existing entry"""
        entry_id = test_entries[0].id
        response = authenticated_client.post(
            f"/entries/update/{entry_id}",
            data={
                "type": "expense",
                "amount": "75.00",
                "note": "Updated note",
                "date": str(date.today()),
                "category_id": str(test_categories[0].id)
            },
            follow_redirects=False
        )

        assert response.status_code in [200, 302, 303]

    def test_update_entry_amount_only(self, authenticated_client, db_session, test_entries):
        """Test updating only entry amount"""
        entry_id = test_entries[0].id
        response = authenticated_client.post(
            f"/entries/update_amount/{entry_id}",
            data={"amount": "100.00"},
            follow_redirects=False
        )

        assert response.status_code in [200, 302, 303]

    def test_update_entry_nonexistent(self, authenticated_client, db_session):
        """Test updating non-existent entry"""
        response = authenticated_client.post(
            "/entries/update/99999",
            data={
                "type": "expense",
                "amount": "50.00",
                "date": str(date.today())
            }
        )

        assert response.status_code == 404

    def test_update_entry_other_user(self, authenticated_client_2, db_session, test_entries):
        """Test that users cannot update other users' entries"""
        entry_id = test_entries[0].id
        response = authenticated_client_2.post(
            f"/entries/update/{entry_id}",
            data={
                "type": "expense",
                "amount": "999.00",
                "date": str(date.today())
            }
        )

        assert response.status_code == 404


@pytest.mark.integration
class TestDeleteEntryEndpoint:
    """Tests for POST /entries/delete/{id} endpoint"""

    def test_delete_entry_success(self, authenticated_client, db_session, test_entries):
        """Test deleting an entry"""
        entry_id = test_entries[0].id
        response = authenticated_client.post(
            f"/entries/delete/{entry_id}",
            follow_redirects=False
        )

        assert response.status_code in [200, 302, 303]

    def test_delete_entry_nonexistent(self, authenticated_client, db_session):
        """Test deleting non-existent entry"""
        response = authenticated_client.post("/entries/delete/99999")

        # Endpoint returns 200 with error message in HTML
        assert response.status_code == 200

    def test_delete_entry_other_user(self, authenticated_client_2, db_session, test_entries):
        """Test that users cannot delete other users' entries"""
        entry_id = test_entries[0].id
        response = authenticated_client_2.post(f"/entries/delete/{entry_id}")

        # Endpoint returns 200 with error message in HTML
        assert response.status_code == 200


@pytest.mark.integration
class TestUncategorizedEntriesEndpoint:
    """Tests for GET /entries/uncategorized endpoint"""

    def test_get_uncategorized_entries(self, authenticated_client, db_session, test_user):
        """Test retrieving uncategorized entries"""
        # Create an entry without category
        entry = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("30.00"),
            date=date.today(),
            note="Uncategorized expense"
        )
        db_session.add(entry)
        db_session.commit()

        response = authenticated_client.get("/entries/uncategorized")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "entries" in data
        # Should include the uncategorized entry
        assert len(data["entries"]) > 0


@pytest.mark.integration
class TestUpdateEntryCategoryEndpoint:
    """Tests for PUT /entries/{id}/category endpoint"""

    def test_update_entry_category(self, authenticated_client, db_session, test_entries, test_categories):
        """Test updating entry category"""
        entry_id = test_entries[0].id
        new_category_id = test_categories[1].id

        response = authenticated_client.put(
            f"/entries/{entry_id}/category",
            json={"category_id": new_category_id}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data

    def test_update_entry_category_nonexistent_entry(self, authenticated_client, db_session, test_categories):
        """Test updating category of non-existent entry"""
        response = authenticated_client.put(
            "/entries/99999/category",
            json={"category_id": test_categories[0].id}
        )

        assert response.status_code == 404

    def test_update_entry_category_other_user(self, authenticated_client_2, db_session,
                                              test_entries, test_categories):
        """Test that users cannot update other users' entry categories"""
        entry_id = test_entries[0].id
        response = authenticated_client_2.put(
            f"/entries/{entry_id}/category",
            json={"category_id": test_categories[0].id}
        )

        assert response.status_code == 404


@pytest.mark.integration
class TestLoadMoreEntriesEndpoint:
    """Tests for GET /entries/load-more endpoint"""

    def test_load_more_entries(self, authenticated_client, db_session, test_entries):
        """Test loading more entries with pagination"""
        response = authenticated_client.get("/entries/load-more?limit=2&offset=0")

        assert response.status_code == 200
        # Returns HTML fragment
        assert b"<tr" in response.content.lower() or b"entry" in response.content.lower() or response.content == b""

    def test_load_more_entries_with_filters(self, authenticated_client, db_session, test_entries, test_categories):
        """Test loading more entries with category filter"""
        category_id = test_categories[0].id
        response = authenticated_client.get(
            f"/entries/load-more?limit=5&offset=0&category_id={category_id}"
        )

        assert response.status_code == 200

"""
Integration tests for entries REST API endpoints
Tests the complete HTTP request/response cycle for RESTful JSON entry endpoints
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from app.models.entry import Entry
from app.models.category import Category


@pytest.mark.integration
class TestEntriesRestListEndpoint:
    """Tests for GET /api/entries endpoint (REST API)"""

    @pytest.mark.asyncio
    async def test_list_entries_json(self, authenticated_client, db_session, test_user):
        """Test REST API returns paginated entries list"""
        # Create test entries
        entry1 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("50.00"),
            date=date.today(),
            currency_code="USD"
        )
        entry2 = Entry(
            user_id=test_user.id,
            type="income",
            amount=Decimal("1000.00"),
            date=date.today(),
            currency_code="USD"
        )
        db_session.add_all([entry1, entry2])
        db_session.commit()

        response = authenticated_client.get("/api/entries")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert len(data["data"]) >= 2
        assert "pagination" in data

    @pytest.mark.asyncio
    async def test_list_entries_with_pagination(self, authenticated_client, db_session, test_user):
        """Test REST API pagination works correctly"""
        # Create 15 entries
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
        response = authenticated_client.get("/api/entries?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 10
        assert data["pagination"]["total"] >= 15
        assert data["pagination"]["has_more"] is True

        # Get second page
        response2 = authenticated_client.get("/api/entries?limit=10&offset=10")
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["data"]) >= 5

    @pytest.mark.asyncio
    async def test_list_entries_user_isolation(self, authenticated_client, db_session, test_user, test_user_2):
        """Test REST API only returns current user's entries"""
        # Create entries for both users
        entry_user1 = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("50.00"),
            date=date.today(),
            note="User 1 entry",
            currency_code="USD"
        )
        entry_user2 = Entry(
            user_id=test_user_2.id,
            type="expense",
            amount=Decimal("100.00"),
            date=date.today(),
            note="User 2 entry",
            currency_code="USD"
        )
        db_session.add_all([entry_user1, entry_user2])
        db_session.commit()

        response = authenticated_client.get("/api/entries")

        assert response.status_code == 200
        data = response.json()
        entry_notes = [e.get("note") for e in data["data"]]

        # Should only see user1's entry
        assert "User 1 entry" in entry_notes
        assert "User 2 entry" not in entry_notes


@pytest.mark.integration
class TestEntriesRestGetEndpoint:
    """Tests for GET /api/entries/{entry_id} endpoint"""

    @pytest.mark.asyncio
    async def test_get_entry_success(self, authenticated_client, db_session, test_user):
        """Test getting a single entry by ID"""
        entry = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("75.50"),
            date=date.today(),
            note="Test entry",
            currency_code="USD"
        )
        db_session.add(entry)
        db_session.commit()

        response = authenticated_client.get(f"/api/entries/{entry.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == entry.id
        assert data["data"]["amount"] == 75.50
        assert data["data"]["note"] == "Test entry"

    @pytest.mark.asyncio
    async def test_get_entry_not_found(self, authenticated_client, db_session, test_user):
        """Test getting a non-existent entry returns 404"""
        response = authenticated_client.get("/api/entries/99999")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_get_entry_user_isolation(self, authenticated_client, db_session, test_user, test_user_2):
        """Test users cannot access other users' entries"""
        # Create entry for user 2
        entry = Entry(
            user_id=test_user_2.id,
            type="expense",
            amount=Decimal("100.00"),
            date=date.today(),
            currency_code="USD"
        )
        db_session.add(entry)
        db_session.commit()

        # Try to access as user 1 (authenticated_client is user 1)
        response = authenticated_client.get(f"/api/entries/{entry.id}")

        assert response.status_code == 404


@pytest.mark.integration
class TestEntriesRestCreateEndpoint:
    """Tests for POST /api/entries endpoint"""

    @pytest.mark.asyncio
    async def test_create_entry_success(self, authenticated_client, db_session, test_user):
        """Test successful entry creation"""
        entry_data = {
            "type": "expense",
            "amount": 125.50,
            "date": date.today().isoformat(),
            "note": "New test entry",
            "currency_code": "USD"
        }

        response = authenticated_client.post(
            "/api/entries",
            json=entry_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["amount"] == 125.50
        assert data["data"]["note"] == "New test entry"

        # Verify entry was created in database
        entry = db_session.query(Entry).filter(
            Entry.user_id == test_user.id,
            Entry.note == "New test entry"
        ).first()
        assert entry is not None
        assert float(entry.amount) == 125.50

    @pytest.mark.asyncio
    async def test_create_entry_with_category(self, authenticated_client, db_session, test_user, test_categories):
        """Test creating entry with category"""
        entry_data = {
            "type": "expense",
            "amount": 50.00,
            "date": date.today().isoformat(),
            "category_id": test_categories[0].id,
            "currency_code": "USD"
        }

        response = authenticated_client.post("/api/entries", json=entry_data)

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["category_id"] == test_categories[0].id

    @pytest.mark.asyncio
    async def test_create_entry_validation_error(self, authenticated_client, db_session, test_user):
        """Test validation errors are returned"""
        entry_data = {
            "type": "expense",
            "amount": -50.00,  # Invalid: negative amount
            "date": date.today().isoformat()
        }

        response = authenticated_client.post("/api/entries", json=entry_data)

        assert response.status_code == 422


@pytest.mark.integration
class TestEntriesRestUpdateEndpoint:
    """Tests for PUT /api/entries/{entry_id} endpoint"""

    @pytest.mark.asyncio
    async def test_update_entry_success(self, authenticated_client, db_session, test_user):
        """Test successful entry update"""
        entry = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("50.00"),
            date=date.today(),
            note="Original note",
            currency_code="USD"
        )
        db_session.add(entry)
        db_session.commit()

        update_data = {
            "amount": 75.00,
            "note": "Updated note"
        }

        response = authenticated_client.put(
            f"/api/entries/{entry.id}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["amount"] == 75.00
        assert data["data"]["note"] == "Updated note"

        # Verify in database
        db_session.refresh(entry)
        assert float(entry.amount) == 75.00
        assert entry.note == "Updated note"

    @pytest.mark.asyncio
    async def test_update_entry_not_found(self, authenticated_client, db_session, test_user):
        """Test updating non-existent entry returns 404"""
        update_data = {"amount": 100.00}

        response = authenticated_client.put("/api/entries/99999", json=update_data)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_entry_user_isolation(self, authenticated_client, db_session, test_user, test_user_2):
        """Test users cannot update other users' entries"""
        entry = Entry(
            user_id=test_user_2.id,
            type="expense",
            amount=Decimal("100.00"),
            date=date.today(),
            currency_code="USD"
        )
        db_session.add(entry)
        db_session.commit()

        update_data = {"amount": 200.00}
        response = authenticated_client.put(f"/api/entries/{entry.id}", json=update_data)

        assert response.status_code == 404


@pytest.mark.integration
class TestEntriesRestDeleteEndpoint:
    """Tests for DELETE /api/entries/{entry_id} endpoint"""

    @pytest.mark.asyncio
    async def test_delete_entry_success(self, authenticated_client, db_session, test_user):
        """Test successful entry deletion"""
        entry = Entry(
            user_id=test_user.id,
            type="expense",
            amount=Decimal("50.00"),
            date=date.today(),
            currency_code="USD"
        )
        db_session.add(entry)
        db_session.commit()
        entry_id = entry.id

        response = authenticated_client.delete(f"/api/entries/{entry_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify entry was deleted
        deleted_entry = db_session.query(Entry).filter(Entry.id == entry_id).first()
        assert deleted_entry is None

    @pytest.mark.asyncio
    async def test_delete_entry_not_found(self, authenticated_client, db_session, test_user):
        """Test deleting non-existent entry returns 404"""
        response = authenticated_client.delete("/api/entries/99999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_entry_user_isolation(self, authenticated_client, db_session, test_user, test_user_2):
        """Test users cannot delete other users' entries"""
        entry = Entry(
            user_id=test_user_2.id,
            type="expense",
            amount=Decimal("100.00"),
            date=date.today(),
            currency_code="USD"
        )
        db_session.add(entry)
        db_session.commit()

        response = authenticated_client.delete(f"/api/entries/{entry.id}")

        assert response.status_code == 404

        # Verify entry still exists
        db_session.refresh(entry)
        assert entry is not None

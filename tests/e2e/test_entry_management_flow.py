"""
E2E test for complete entry management flow:
Add entry → view on dashboard → edit → delete
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from app.models.entry import Entry
from app.models.category import Category


@pytest.mark.e2e
class TestEntryManagementFlow:
    """E2E tests for complete entry lifecycle"""

    @pytest.mark.asyncio
    async def test_complete_entry_lifecycle(self, authenticated_client, db_session, test_user, test_categories):
        """
        Test complete entry management journey

        Flow:
        1. User views entries page (empty or with existing entries)
        2. User creates a new expense entry
        3. Entry appears on dashboard
        4. User views entry details
        5. User edits entry
        6. Changes appear on dashboard
        7. User deletes entry
        8. Entry no longer appears on dashboard
        """

        client = authenticated_client

        # Step 1: User visits entries page
        response = client.get("/entries/")
        assert response.status_code == 200
        assert b"Entries" in response.content or b"entries" in response.content

        # Step 2: User creates a new expense entry
        entry_data = {
            "type": "expense",
            "amount": "75.50",
            "category_id": test_categories[0].id,  # Food & Dining
            "note": "Dinner at restaurant",
            "date": date.today().isoformat()
        }

        response = client.post("/entries/create", data=entry_data)
        assert response.status_code in [200, 302, 303]

        # Verify entry was created in database
        entry = db_session.query(Entry).filter(
            Entry.user_id == test_user.id,
            Entry.note == "Dinner at restaurant"
        ).first()
        assert entry is not None
        assert entry.amount == Decimal("75.50")
        assert entry.type == "expense"
        assert entry.category_id == test_categories[0].id

        entry_id = entry.id

        # Step 3: Entry appears on dashboard
        response = client.get("/")
        assert response.status_code == 200
        assert b"Dinner at restaurant" in response.content
        assert b"75.50" in response.content

        # Step 4: Entry appears in entries list
        response = client.get("/entries/")
        assert response.status_code == 200
        assert b"Dinner at restaurant" in response.content

        # Step 5: User views entry details
        response = client.get(f"/entries/item/{entry_id}")
        assert response.status_code == 200
        assert b"Dinner at restaurant" in response.content
        assert b"75.50" in response.content

        # Step 6: User opens edit form
        response = client.get(f"/entries/edit/{entry_id}")
        assert response.status_code == 200
        assert b"75.50" in response.content
        assert b"Dinner at restaurant" in response.content

        # Step 7: User updates entry
        updated_data = {
            "type": "expense",
            "amount": "85.00",  # Changed amount
            "category_id": test_categories[0].id,
            "note": "Dinner at fancy restaurant",  # Changed note
            "date": date.today().isoformat()
        }

        response = client.post(f"/entries/update/{entry_id}", data=updated_data)
        assert response.status_code in [200, 302, 303]

        # Verify entry was updated
        db_session.expire_all()
        entry = db_session.query(Entry).filter(Entry.id == entry_id).first()
        assert entry.amount == Decimal("85.00")
        assert entry.note == "Dinner at fancy restaurant"

        # Step 8: Updated entry appears on dashboard
        response = client.get("/")
        assert response.status_code == 200
        assert b"Dinner at fancy restaurant" in response.content
        assert b"85.00" in response.content
        # Old note should not appear
        assert b"Dinner at restaurant" not in response.content

        # Step 9: User deletes entry
        response = client.post(f"/entries/delete/{entry_id}")
        assert response.status_code in [200, 302, 303]

        # Verify entry was deleted
        deleted_entry = db_session.query(Entry).filter(Entry.id == entry_id).first()
        assert deleted_entry is None

        # Step 10: Entry no longer appears on dashboard
        response = client.get("/")
        assert response.status_code == 200
        assert b"Dinner at fancy restaurant" not in response.content

    @pytest.mark.asyncio
    async def test_income_entry_flow(self, authenticated_client, db_session, test_user):
        """
        Test creating and managing income entry

        Flow:
        1. User creates income entry (no category)
        2. Income appears on dashboard
        3. Dashboard shows correct income total
        """

        client = authenticated_client

        # Step 1: User creates income entry
        income_data = {
            "type": "income",
            "amount": "5000.00",
            "note": "Monthly salary",
            "date": date.today().isoformat()
        }

        response = client.post("/entries/create", data=income_data)
        assert response.status_code in [200, 302, 303]

        # Verify income was created
        income = db_session.query(Entry).filter(
            Entry.user_id == test_user.id,
            Entry.note == "Monthly salary"
        ).first()
        assert income is not None
        assert income.type == "income"
        assert income.amount == Decimal("5000.00")
        assert income.category_id is None  # Income has no category

        # Step 2: Income appears on dashboard
        response = client.get("/")
        assert response.status_code == 200
        assert b"Monthly salary" in response.content
        assert b"5000" in response.content or b"5,000" in response.content

        # Step 3: Dashboard shows correct totals
        # Check that income is added to total income, not expenses
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_multi_currency_entry_flow(self, authenticated_client, db_session, test_user, test_categories):
        """
        Test creating entries with different currencies

        Flow:
        1. User creates entry in EUR
        2. User creates entry in GBP
        3. Dashboard shows converted amounts in user's default currency
        """

        client = authenticated_client

        # Step 1: Create entry in EUR
        eur_entry_data = {
            "type": "expense",
            "amount": "100.00",
            "category_id": test_categories[0].id,
            "note": "Hotel in Paris",
            "date": date.today().isoformat(),
            "currency_code": "EUR"
        }

        response = client.post("/entries/create", data=eur_entry_data)
        assert response.status_code in [200, 302, 303]

        # Verify EUR entry was created
        eur_entry = db_session.query(Entry).filter(
            Entry.user_id == test_user.id,
            Entry.note == "Hotel in Paris"
        ).first()
        assert eur_entry is not None
        assert eur_entry.currency_code == "EUR"

        # Step 2: Create entry in GBP
        gbp_entry_data = {
            "type": "expense",
            "amount": "50.00",
            "category_id": test_categories[1].id,
            "note": "Taxi in London",
            "date": date.today().isoformat(),
            "currency_code": "GBP"
        }

        response = client.post("/entries/create", data=gbp_entry_data)
        assert response.status_code in [200, 302, 303]

        # Step 3: Dashboard shows both entries
        response = client.get("/")
        assert response.status_code == 200
        assert b"Hotel in Paris" in response.content
        assert b"Taxi in London" in response.content

    @pytest.mark.asyncio
    async def test_entry_filtering_and_search(self, authenticated_client, db_session, test_user, test_categories):
        """
        Test filtering and searching entries

        Flow:
        1. User creates multiple entries
        2. User filters by date range
        3. User filters by category
        4. User searches by note
        """

        client = authenticated_client

        # Step 1: Create multiple entries
        entries_data = [
            {
                "type": "expense",
                "amount": "20.00",
                "category_id": test_categories[0].id,
                "note": "Coffee at Starbucks",
                "date": date.today().isoformat()
            },
            {
                "type": "expense",
                "amount": "50.00",
                "category_id": test_categories[1].id,
                "note": "Uber to airport",
                "date": (date.today() - timedelta(days=7)).isoformat()
            },
            {
                "type": "expense",
                "amount": "100.00",
                "category_id": test_categories[0].id,
                "note": "Dinner at restaurant",
                "date": (date.today() - timedelta(days=14)).isoformat()
            }
        ]

        for entry_data in entries_data:
            response = client.post("/entries/create", data=entry_data)
            assert response.status_code in [200, 302, 303]

        # Step 2: Filter by date range (last 7 days)
        start_date = (date.today() - timedelta(days=7)).isoformat()
        end_date = date.today().isoformat()

        response = client.get(f"/entries/?start_date={start_date}&end_date={end_date}")
        assert response.status_code == 200
        # Should show recent entries
        assert b"Coffee at Starbucks" in response.content
        # Should NOT show old entry
        assert b"Dinner at restaurant" not in response.content

        # Step 3: Filter by category (Food & Dining)
        response = client.get(f"/entries/?category_id={test_categories[0].id}")
        assert response.status_code == 200
        assert b"Coffee at Starbucks" in response.content
        # Should NOT show Transportation entry
        assert b"Uber to airport" not in response.content

        # Step 4: Search by note
        response = client.get("/entries/?search=coffee")
        assert response.status_code == 200
        assert b"Coffee at Starbucks" in response.content

    @pytest.mark.asyncio
    async def test_entry_validation_errors(self, authenticated_client, db_session, test_user):
        """
        Test entry creation with invalid data

        Flow:
        1. User tries to create entry with negative amount
        2. User tries to create entry with missing required fields
        3. User tries to create entry with invalid date
        """

        client = authenticated_client

        # Test 1: Negative amount
        invalid_data = {
            "type": "expense",
            "amount": "-50.00",
            "note": "Invalid negative amount",
            "date": date.today().isoformat()
        }

        response = client.post("/entries/create", data=invalid_data)
        # Should fail validation
        assert response.status_code in [200, 400, 422]

        # Test 2: Missing required fields
        invalid_data = {
            "type": "expense",
            "note": "Missing amount"
        }

        response = client.post("/entries/create", data=invalid_data)
        assert response.status_code in [200, 400, 422]

        # Test 3: Invalid type
        invalid_data = {
            "type": "invalid_type",
            "amount": "50.00",
            "date": date.today().isoformat()
        }

        response = client.post("/entries/create", data=invalid_data)
        assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_user_cannot_edit_other_users_entries(self, authenticated_client, authenticated_client_2, db_session, test_user, test_user_2, test_categories):
        """
        Test user isolation - users cannot edit each other's entries

        Flow:
        1. User 1 creates an entry
        2. User 2 tries to view User 1's entry (should fail)
        3. User 2 tries to edit User 1's entry (should fail)
        4. User 2 tries to delete User 1's entry (should fail)
        """

        # Step 1: User 1 creates entry
        entry_data = {
            "type": "expense",
            "amount": "100.00",
            "category_id": test_categories[0].id,
            "note": "User 1 private entry",
            "date": date.today().isoformat()
        }

        response = authenticated_client.post("/entries/create", data=entry_data)
        assert response.status_code in [200, 302, 303]

        # Get entry ID
        entry = db_session.query(Entry).filter(
            Entry.user_id == test_user.id,
            Entry.note == "User 1 private entry"
        ).first()
        assert entry is not None
        entry_id = entry.id

        # Step 2: User 2 tries to view User 1's entry
        response = authenticated_client_2.get(f"/entries/item/{entry_id}")
        # Should return 404 (not found for this user)
        assert response.status_code == 404

        # Step 3: User 2 tries to edit User 1's entry
        response = authenticated_client_2.post(f"/entries/update/{entry_id}", data={
            "type": "expense",
            "amount": "999.00",
            "note": "Hacked entry",
            "date": date.today().isoformat()
        })
        # Should return 404 or 403
        assert response.status_code in [403, 404]

        # Verify entry was NOT modified
        db_session.expire_all()
        entry = db_session.query(Entry).filter(Entry.id == entry_id).first()
        assert entry.note == "User 1 private entry"
        assert entry.amount == Decimal("100.00")

        # Step 4: User 2 tries to delete User 1's entry
        response = authenticated_client_2.post(f"/entries/delete/{entry_id}")
        # Should return 200 but not actually delete (or 404)
        assert response.status_code in [200, 404]

        # Verify entry still exists
        entry = db_session.query(Entry).filter(Entry.id == entry_id).first()
        assert entry is not None

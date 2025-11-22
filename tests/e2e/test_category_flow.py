"""
E2E test for complete category management flow:
Create category → assign to entry → delete category → verify entry handling
"""
import pytest
from datetime import date
from decimal import Decimal
from app.models.category import Category
from app.models.entry import Entry


@pytest.mark.e2e
class TestCategoryManagementFlow:
    """E2E tests for complete category lifecycle and integration with entries"""

    @pytest.mark.asyncio
    async def test_complete_category_lifecycle_with_entries(self, authenticated_client, db_session, test_user):
        """
        Test complete category management with entry integration

        Flow:
        1. User creates a new category
        2. User creates an entry and assigns it to the category
        3. Entry shows category name on dashboard
        4. User edits category name
        5. Updated category name appears on entry
        6. User deletes category
        7. Entry remains but category_id is set to NULL
        """

        client = authenticated_client

        # Step 1: User visits categories page
        response = client.get("/categories/")
        assert response.status_code == 200
        assert b"Categories" in response.content or b"categories" in response.content

        # Step 2: User creates a new category
        category_data = {
            "name": "Travel Expenses"
        }

        response = client.post("/categories/create", data=category_data)
        assert response.status_code in [200, 302, 303]

        # Verify category was created
        category = db_session.query(Category).filter(
            Category.user_id == test_user.id,
            Category.name == "Travel Expenses"
        ).first()
        assert category is not None
        category_id = category.id

        # Step 3: Category appears in categories list
        response = client.get("/categories/")
        assert response.status_code == 200
        assert b"Travel Expenses" in response.content

        # Step 4: User creates entry with this category
        entry_data = {
            "type": "expense",
            "amount": "250.00",
            "category_id": category_id,
            "note": "Flight to New York",
            "date": date.today().isoformat()
        }

        response = client.post("/entries/create", data=entry_data)
        assert response.status_code in [200, 302, 303]

        # Verify entry was created with category
        entry = db_session.query(Entry).filter(
            Entry.user_id == test_user.id,
            Entry.note == "Flight to New York"
        ).first()
        assert entry is not None
        assert entry.category_id == category_id
        entry_id = entry.id

        # Step 5: Entry shows category on dashboard
        response = client.get("/")
        assert response.status_code == 200
        assert b"Flight to New York" in response.content
        assert b"Travel Expenses" in response.content

        # Step 6: User edits category name
        updated_category_data = {
            "name": "Business Travel"
        }

        response = client.post(f"/categories/update/{category_id}", data=updated_category_data)
        assert response.status_code in [200, 302, 303]

        # Verify category name was updated
        db_session.expire_all()
        category = db_session.query(Category).filter(Category.id == category_id).first()
        assert category.name == "Business Travel"

        # Step 7: Updated category name appears on entry
        response = client.get("/entries/")
        assert response.status_code == 200
        assert b"Business Travel" in response.content
        # Old name should not appear
        assert b"Travel Expenses" not in response.content

        # Step 8: User deletes category
        response = client.post(f"/categories/delete/{category_id}")
        assert response.status_code == 200

        # Verify category was deleted
        deleted_category = db_session.query(Category).filter(Category.id == category_id).first()
        assert deleted_category is None

        # Step 9: Entry still exists but category_id is NULL
        db_session.expire_all()
        entry = db_session.query(Entry).filter(Entry.id == entry_id).first()
        assert entry is not None
        assert entry.category_id is None
        assert entry.note == "Flight to New York"
        assert entry.amount == Decimal("250.00")

        # Step 10: Entry appears on dashboard without category
        response = client.get("/")
        assert response.status_code == 200
        assert b"Flight to New York" in response.content

    @pytest.mark.asyncio
    async def test_multiple_entries_share_category(self, authenticated_client, db_session, test_user):
        """
        Test multiple entries using the same category

        Flow:
        1. User creates a category
        2. User creates multiple entries with this category
        3. All entries show the category
        4. User deletes category
        5. All entries remain but lose category assignment
        """

        client = authenticated_client

        # Step 1: Create category
        category_data = {"name": "Groceries"}
        response = client.post("/categories/create", data=category_data)
        assert response.status_code in [200, 302, 303]

        category = db_session.query(Category).filter(
            Category.user_id == test_user.id,
            Category.name == "Groceries"
        ).first()
        assert category is not None
        category_id = category.id

        # Step 2: Create multiple entries with this category
        entries_data = [
            {
                "type": "expense",
                "amount": "45.00",
                "category_id": category_id,
                "note": "Whole Foods shopping",
                "date": date.today().isoformat()
            },
            {
                "type": "expense",
                "amount": "32.50",
                "category_id": category_id,
                "note": "Trader Joe's",
                "date": date.today().isoformat()
            },
            {
                "type": "expense",
                "amount": "78.00",
                "category_id": category_id,
                "note": "Costco bulk purchase",
                "date": date.today().isoformat()
            }
        ]

        entry_ids = []
        for entry_data in entries_data:
            response = client.post("/entries/create", data=entry_data)
            assert response.status_code in [200, 302, 303]

        # Get all entry IDs
        entries = db_session.query(Entry).filter(
            Entry.user_id == test_user.id,
            Entry.category_id == category_id
        ).all()
        assert len(entries) == 3
        entry_ids = [e.id for e in entries]

        # Step 3: All entries show the category
        response = client.get("/entries/")
        assert response.status_code == 200
        assert b"Groceries" in response.content
        assert b"Whole Foods shopping" in response.content
        assert b"Trader Joe" in response.content
        assert b"Costco" in response.content

        # Step 4: Delete category
        response = client.post(f"/categories/delete/{category_id}")
        assert response.status_code == 200

        # Step 5: All entries remain but category_id is NULL
        db_session.expire_all()
        entries = db_session.query(Entry).filter(Entry.id.in_(entry_ids)).all()
        assert len(entries) == 3
        for entry in entries:
            assert entry.category_id is None

        # Entries still visible on dashboard
        response = client.get("/")
        assert response.status_code == 200
        assert b"Whole Foods shopping" in response.content

    @pytest.mark.asyncio
    async def test_category_filtering_on_dashboard(self, authenticated_client, db_session, test_user):
        """
        Test filtering dashboard by category

        Flow:
        1. User creates two categories
        2. User creates entries in both categories
        3. User filters dashboard by first category
        4. Only entries from first category appear
        """

        client = authenticated_client

        # Step 1: Create two categories
        cat1_response = client.post("/categories/create", data={"name": "Restaurants"})
        cat2_response = client.post("/categories/create", data={"name": "Groceries"})
        assert cat1_response.status_code in [200, 302, 303]
        assert cat2_response.status_code in [200, 302, 303]

        cat1 = db_session.query(Category).filter(
            Category.user_id == test_user.id,
            Category.name == "Restaurants"
        ).first()
        cat2 = db_session.query(Category).filter(
            Category.user_id == test_user.id,
            Category.name == "Groceries"
        ).first()

        # Step 2: Create entries in both categories
        client.post("/entries/create", data={
            "type": "expense",
            "amount": "65.00",
            "category_id": cat1.id,
            "note": "Dinner at Italian restaurant",
            "date": date.today().isoformat()
        })

        client.post("/entries/create", data={
            "type": "expense",
            "amount": "45.00",
            "category_id": cat2.id,
            "note": "Weekly groceries",
            "date": date.today().isoformat()
        })

        # Step 3: Filter by Restaurants category
        response = client.get(f"/?category_id={cat1.id}")
        assert response.status_code == 200
        assert b"Dinner at Italian restaurant" in response.content
        # Should NOT show groceries entry
        assert b"Weekly groceries" not in response.content

    @pytest.mark.asyncio
    async def test_category_validation(self, authenticated_client, db_session, test_user):
        """
        Test category validation rules

        Flow:
        1. User tries to create category with empty name
        2. User tries to create category with too long name
        3. User tries to create category with just whitespace
        """

        client = authenticated_client

        # Test 1: Empty name
        response = client.post("/categories/create", data={"name": ""})
        assert response.status_code in [200, 400, 422]

        # Test 2: Too long name (>80 characters)
        long_name = "A" * 81
        response = client.post("/categories/create", data={"name": long_name})
        assert response.status_code in [200, 400, 422]

        # Test 3: Just whitespace
        response = client.post("/categories/create", data={"name": "   "})
        assert response.status_code in [200, 400, 422]

        # Verify no categories were created
        invalid_categories = db_session.query(Category).filter(
            Category.user_id == test_user.id,
            Category.name.in_(["", long_name, "   "])
        ).all()
        assert len(invalid_categories) == 0

    @pytest.mark.asyncio
    async def test_category_user_isolation(self, authenticated_client, authenticated_client_2, db_session, test_user, test_user_2):
        """
        Test user isolation for categories

        Flow:
        1. User 1 creates a category
        2. User 2 cannot see User 1's category
        3. User 2 cannot edit User 1's category
        4. User 2 cannot delete User 1's category
        """

        # Step 1: User 1 creates category
        response = authenticated_client.post("/categories/create", data={"name": "User 1 Private Category"})
        assert response.status_code in [200, 302, 303]

        cat1 = db_session.query(Category).filter(
            Category.user_id == test_user.id,
            Category.name == "User 1 Private Category"
        ).first()
        assert cat1 is not None

        # Step 2: User 2 views categories page
        response = authenticated_client_2.get("/categories/")
        assert response.status_code == 200
        # Should NOT see User 1's category
        assert b"User 1 Private Category" not in response.content

        # Step 3: User 2 tries to view User 1's category
        response = authenticated_client_2.get(f"/categories/item/{cat1.id}")
        assert response.status_code == 404

        # Step 4: User 2 tries to edit User 1's category
        response = authenticated_client_2.post(f"/categories/update/{cat1.id}", data={"name": "Hacked Category"})
        assert response.status_code == 404

        # Verify category was NOT modified
        db_session.expire_all()
        cat1 = db_session.query(Category).filter(Category.id == cat1.id).first()
        assert cat1.name == "User 1 Private Category"

        # Step 5: User 2 tries to delete User 1's category
        response = authenticated_client_2.post(f"/categories/delete/{cat1.id}")
        assert response.status_code == 200  # Returns 200 but doesn't delete

        # Verify category still exists
        cat1 = db_session.query(Category).filter(Category.id == cat1.id).first()
        assert cat1 is not None

    @pytest.mark.asyncio
    async def test_category_with_entry_creation_flow(self, authenticated_client, db_session, test_user):
        """
        Test creating entry immediately after creating category

        Flow:
        1. User creates new category
        2. User immediately creates entry with that category
        3. Entry correctly shows the category
        """

        client = authenticated_client

        # Step 1: Create category
        response = client.post("/categories/create", data={"name": "Medical"})
        assert response.status_code in [200, 302, 303]

        # Get category
        category = db_session.query(Category).filter(
            Category.user_id == test_user.id,
            Category.name == "Medical"
        ).first()
        assert category is not None

        # Step 2: Immediately create entry with this category
        response = client.post("/entries/create", data={
            "type": "expense",
            "amount": "150.00",
            "category_id": category.id,
            "note": "Doctor visit",
            "date": date.today().isoformat()
        })
        assert response.status_code in [200, 302, 303]

        # Step 3: Verify entry has correct category
        entry = db_session.query(Entry).filter(
            Entry.user_id == test_user.id,
            Entry.note == "Doctor visit"
        ).first()
        assert entry is not None
        assert entry.category_id == category.id

        # Step 4: Entry shows on dashboard with category
        response = client.get("/")
        assert response.status_code == 200
        assert b"Doctor visit" in response.content
        assert b"Medical" in response.content

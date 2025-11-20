"""
Integration tests for categories API endpoints
Tests the complete HTTP request/response cycle for category endpoints
"""
import pytest
from app.models.category import Category
from app.models.entry import Entry


@pytest.mark.integration
class TestCategoriesListEndpoint:
    """Tests for GET /categories/ endpoint (HTML page)"""

    @pytest.mark.asyncio
    async def test_list_categories_page(self, authenticated_client, db_session, test_user):
        """Test categories page loads successfully"""
        response = authenticated_client.get("/categories/")

        assert response.status_code == 200
        assert b"Categories" in response.content or b"categories" in response.content

    @pytest.mark.asyncio
    async def test_list_categories_shows_user_categories(self, authenticated_client, db_session, test_user):
        """Test categories page shows user's categories"""
        # Create test categories
        cat1 = Category(user_id=test_user.id, name="Groceries")
        cat2 = Category(user_id=test_user.id, name="Transport")
        db_session.add_all([cat1, cat2])
        db_session.commit()

        response = authenticated_client.get("/categories/")

        assert response.status_code == 200
        assert b"Groceries" in response.content
        assert b"Transport" in response.content


@pytest.mark.integration
class TestCategoriesAPIListEndpoint:
    """Tests for GET /categories/api/list endpoint (JSON API)"""

    @pytest.mark.asyncio
    async def test_list_categories_json(self, authenticated_client, db_session, test_user):
        """Test JSON API returns categories list"""
        # Create test categories
        cat1 = Category(user_id=test_user.id, name="Food")
        cat2 = Category(user_id=test_user.id, name="Utilities")
        db_session.add_all([cat1, cat2])
        db_session.commit()

        response = authenticated_client.get("/categories/api/list")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["categories"]) >= 2

        # Check categories are in response
        category_names = [c["name"] for c in data["categories"]]
        assert "Food" in category_names
        assert "Utilities" in category_names

    @pytest.mark.asyncio
    async def test_list_categories_json_user_isolation(self, authenticated_client, db_session, test_user, test_user_2):
        """Test JSON API only returns current user's categories"""
        # Create categories for both users
        cat_user1 = Category(user_id=test_user.id, name="User1 Category")
        cat_user2 = Category(user_id=test_user_2.id, name="User2 Category")
        db_session.add_all([cat_user1, cat_user2])
        db_session.commit()

        response = authenticated_client.get("/categories/api/list")

        assert response.status_code == 200
        data = response.json()
        category_names = [c["name"] for c in data["categories"]]

        # Should only see user1's category
        assert "User1 Category" in category_names
        assert "User2 Category" not in category_names


@pytest.mark.integration
class TestCreateCategoryEndpoint:
    """Tests for POST /categories/create endpoint"""

    @pytest.mark.asyncio
    async def test_create_category_success(self, authenticated_client, db_session, test_user):
        """Test successful category creation"""
        response = authenticated_client.post(
            "/categories/create",
            data={"name": "New Test Category"}
        )

        assert response.status_code == 200

        # Verify category was created in database
        category = db_session.query(Category).filter(
            Category.user_id == test_user.id,
            Category.name == "New Test Category"
        ).first()
        assert category is not None
        assert category.name == "New Test Category"

    @pytest.mark.asyncio
    async def test_create_category_empty_name(self, authenticated_client, db_session, test_user):
        """Test category creation with empty name fails"""
        response = authenticated_client.post(
            "/categories/create",
            data={"name": "   "}
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_category_name_too_long(self, authenticated_client, db_session, test_user):
        """Test category creation with name exceeding 80 characters fails"""
        long_name = "A" * 81
        response = authenticated_client.post(
            "/categories/create",
            data={"name": long_name}
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_category_strips_whitespace(self, authenticated_client, db_session, test_user):
        """Test category creation trims whitespace from name"""
        response = authenticated_client.post(
            "/categories/create",
            data={"name": "  Trimmed Category  "}
        )

        assert response.status_code == 200

        # Verify whitespace was trimmed
        category = db_session.query(Category).filter(
            Category.user_id == test_user.id,
            Category.name == "Trimmed Category"
        ).first()
        assert category is not None


@pytest.mark.integration
class TestUpdateCategoryEndpoint:
    """Tests for POST /categories/update/{category_id} endpoint"""

    @pytest.mark.asyncio
    async def test_update_category_success(self, authenticated_client, db_session, test_user):
        """Test successful category update"""
        # Create category to update
        category = Category(user_id=test_user.id, name="Old Name")
        db_session.add(category)
        db_session.commit()
        category_id = category.id

        response = authenticated_client.post(
            f"/categories/update/{category_id}",
            data={"name": "Updated Name"}
        )

        assert response.status_code == 200

        # Verify category was updated
        db_session.refresh(category)
        assert category.name == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_category_not_found(self, authenticated_client, db_session, test_user):
        """Test updating non-existent category returns 404"""
        response = authenticated_client.post(
            "/categories/update/99999",
            data={"name": "Updated Name"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_category_user_isolation(self, authenticated_client, db_session, test_user, test_user_2):
        """Test user cannot update another user's category"""
        # Create category for user 2
        category = Category(user_id=test_user_2.id, name="User2 Category")
        db_session.add(category)
        db_session.commit()
        category_id = category.id

        # Try to update as user 1 (authenticated_client uses test_user)
        response = authenticated_client.post(
            f"/categories/update/{category_id}",
            data={"name": "Hacked Name"}
        )

        # Should get 404 (category not found for this user)
        assert response.status_code == 404

        # Verify category was NOT updated
        db_session.refresh(category)
        assert category.name == "User2 Category"

    @pytest.mark.asyncio
    async def test_update_category_empty_name(self, authenticated_client, db_session, test_user):
        """Test updating category with empty name fails"""
        category = Category(user_id=test_user.id, name="Original Name")
        db_session.add(category)
        db_session.commit()
        category_id = category.id

        response = authenticated_client.post(
            f"/categories/update/{category_id}",
            data={"name": "   "}
        )

        assert response.status_code == 422

        # Verify category name unchanged
        db_session.refresh(category)
        assert category.name == "Original Name"


@pytest.mark.integration
class TestDeleteCategoryEndpoint:
    """Tests for POST /categories/delete/{category_id} endpoint"""

    @pytest.mark.asyncio
    async def test_delete_category_success(self, authenticated_client, db_session, test_user):
        """Test successful category deletion"""
        # Create category to delete
        category = Category(user_id=test_user.id, name="To Delete")
        db_session.add(category)
        db_session.commit()
        category_id = category.id

        response = authenticated_client.post(f"/categories/delete/{category_id}")

        assert response.status_code == 200

        # Verify category was deleted
        deleted = db_session.query(Category).filter(Category.id == category_id).first()
        assert deleted is None

    @pytest.mark.asyncio
    async def test_delete_category_user_isolation(self, authenticated_client, db_session, test_user, test_user_2):
        """Test user cannot delete another user's category"""
        # Create category for user 2
        category = Category(user_id=test_user_2.id, name="User2 Category")
        db_session.add(category)
        db_session.commit()
        category_id = category.id

        # Try to delete as user 1
        response = authenticated_client.post(f"/categories/delete/{category_id}")

        assert response.status_code == 200  # Returns 200 but doesn't delete

        # Verify category still exists
        still_exists = db_session.query(Category).filter(Category.id == category_id).first()
        assert still_exists is not None
        assert still_exists.name == "User2 Category"

    @pytest.mark.asyncio
    async def test_delete_nonexistent_category(self, authenticated_client, db_session, test_user):
        """Test deleting non-existent category succeeds (idempotent)"""
        response = authenticated_client.post("/categories/delete/99999")

        # Should succeed (no error)
        assert response.status_code == 200


@pytest.mark.integration
class TestCategoryItemEndpoints:
    """Tests for GET /categories/item/{id} and GET /categories/edit/{id} endpoints"""

    @pytest.mark.asyncio
    async def test_get_category_item(self, authenticated_client, db_session, test_user):
        """Test viewing single category"""
        category = Category(user_id=test_user.id, name="View Test")
        db_session.add(category)
        db_session.commit()
        category_id = category.id

        response = authenticated_client.get(f"/categories/item/{category_id}")

        assert response.status_code == 200
        assert b"View Test" in response.content

    @pytest.mark.asyncio
    async def test_get_category_item_not_found(self, authenticated_client, db_session, test_user):
        """Test viewing non-existent category returns 404"""
        response = authenticated_client.get("/categories/item/99999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_category_item_user_isolation(self, authenticated_client, db_session, test_user, test_user_2):
        """Test user cannot view another user's category"""
        category = Category(user_id=test_user_2.id, name="User2 Category")
        db_session.add(category)
        db_session.commit()
        category_id = category.id

        response = authenticated_client.get(f"/categories/item/{category_id}")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_category_edit_form(self, authenticated_client, db_session, test_user):
        """Test getting category edit form"""
        category = Category(user_id=test_user.id, name="Edit Test")
        db_session.add(category)
        db_session.commit()
        category_id = category.id

        response = authenticated_client.get(f"/categories/edit/{category_id}")

        assert response.status_code == 200
        assert b"Edit Test" in response.content


@pytest.mark.integration
class TestCategoryWithEntriesIntegration:
    """Tests for category interactions with entries"""

    @pytest.mark.asyncio
    async def test_category_assigned_to_entry(self, authenticated_client, db_session, test_user):
        """Test category can be assigned to an entry"""
        from datetime import date

        # Create category
        category = Category(user_id=test_user.id, name="Test Category")
        db_session.add(category)
        db_session.commit()
        category_id = category.id

        # Create entry with this category
        entry = Entry(
            user_id=test_user.id,
            category_id=category_id,
            amount=100.00,
            date=date.today(),
            type="expense",
            note="Test entry"
        )
        db_session.add(entry)
        db_session.commit()

        # Verify relationship
        db_session.refresh(entry)
        assert entry.category_id == category_id
        assert entry.category.name == "Test Category"

    @pytest.mark.asyncio
    async def test_delete_category_nullifies_entry_references(self, authenticated_client, db_session, test_user):
        """Test deleting category sets entry.category_id to NULL (not CASCADE)"""
        from datetime import date

        # Create category and entry
        category = Category(user_id=test_user.id, name="To Be Deleted")
        db_session.add(category)
        db_session.commit()
        category_id = category.id

        entry = Entry(
            user_id=test_user.id,
            category_id=category_id,
            amount=50.00,
            date=date.today(),
            type="expense"
        )
        db_session.add(entry)
        db_session.commit()
        entry_id = entry.id

        # Delete category
        response = authenticated_client.post(f"/categories/delete/{category_id}")
        assert response.status_code == 200

        # Verify category is deleted
        deleted_cat = db_session.query(Category).filter(Category.id == category_id).first()
        assert deleted_cat is None

        # Verify entry still exists but category_id is NULL
        db_session.expire_all()  # Clear session cache
        entry = db_session.query(Entry).filter(Entry.id == entry_id).first()
        assert entry is not None
        assert entry.category_id is None

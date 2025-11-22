"""
Integration tests for categories REST API endpoints
Tests the complete HTTP request/response cycle for RESTful JSON category endpoints
"""
import pytest
from app.models.category import Category


@pytest.mark.integration
class TestCategoriesRestListEndpoint:
    """Tests for GET /api/categories endpoint (REST API)"""

    @pytest.mark.asyncio
    async def test_list_categories_json(self, authenticated_client, db_session, test_user):
        """Test REST API returns categories list"""
        # Create test categories
        cat1 = Category(user_id=test_user.id, name="Food")
        cat2 = Category(user_id=test_user.id, name="Transport")
        db_session.add_all([cat1, cat2])
        db_session.commit()

        response = authenticated_client.get("/api/categories")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert len(data["data"]) >= 2

        # Check categories are in response
        category_names = [c["name"] for c in data["data"]]
        assert "Food" in category_names
        assert "Transport" in category_names

    @pytest.mark.asyncio
    async def test_list_categories_sorted_alphabetically(self, authenticated_client, db_session, test_user):
        """Test categories are sorted by name"""
        # Create categories in random order
        cat1 = Category(user_id=test_user.id, name="Zebra")
        cat2 = Category(user_id=test_user.id, name="Apple")
        cat3 = Category(user_id=test_user.id, name="Mango")
        db_session.add_all([cat1, cat2, cat3])
        db_session.commit()

        response = authenticated_client.get("/api/categories")

        assert response.status_code == 200
        data = response.json()
        category_names = [c["name"] for c in data["data"]]

        # Find the positions of our test categories
        apple_idx = category_names.index("Apple")
        mango_idx = category_names.index("Mango")
        zebra_idx = category_names.index("Zebra")

        # Verify alphabetical order
        assert apple_idx < mango_idx < zebra_idx

    @pytest.mark.asyncio
    async def test_list_categories_user_isolation(self, authenticated_client, db_session, test_user, test_user_2):
        """Test REST API only returns current user's categories"""
        # Create categories for both users
        cat_user1 = Category(user_id=test_user.id, name="User1 Category")
        cat_user2 = Category(user_id=test_user_2.id, name="User2 Category")
        db_session.add_all([cat_user1, cat_user2])
        db_session.commit()

        response = authenticated_client.get("/api/categories")

        assert response.status_code == 200
        data = response.json()
        category_names = [c["name"] for c in data["data"]]

        # Should only see user1's category
        assert "User1 Category" in category_names
        assert "User2 Category" not in category_names


@pytest.mark.integration
class TestCategoriesRestGetEndpoint:
    """Tests for GET /api/categories/{category_id} endpoint"""

    @pytest.mark.asyncio
    async def test_get_category_success(self, authenticated_client, db_session, test_user):
        """Test getting a single category by ID"""
        category = Category(user_id=test_user.id, name="Test Category")
        db_session.add(category)
        db_session.commit()

        response = authenticated_client.get(f"/api/categories/{category.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == category.id
        assert data["data"]["name"] == "Test Category"

    @pytest.mark.asyncio
    async def test_get_category_not_found(self, authenticated_client, db_session, test_user):
        """Test getting a non-existent category returns 404"""
        response = authenticated_client.get("/api/categories/99999")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_get_category_user_isolation(self, authenticated_client, db_session, test_user, test_user_2):
        """Test users cannot access other users' categories"""
        # Create category for user 2
        category = Category(user_id=test_user_2.id, name="User 2 Category")
        db_session.add(category)
        db_session.commit()

        # Try to access as user 1 (authenticated_client is user 1)
        response = authenticated_client.get(f"/api/categories/{category.id}")

        assert response.status_code == 404


@pytest.mark.integration
class TestCategoriesRestCreateEndpoint:
    """Tests for POST /api/categories endpoint"""

    @pytest.mark.asyncio
    async def test_create_category_success(self, authenticated_client, db_session, test_user):
        """Test successful category creation"""
        category_data = {"name": "New Test Category"}

        response = authenticated_client.post(
            "/api/categories",
            json=category_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "New Test Category"
        assert "id" in data["data"]

        # Verify category was created in database
        category = db_session.query(Category).filter(
            Category.user_id == test_user.id,
            Category.name == "New Test Category"
        ).first()
        assert category is not None

    @pytest.mark.asyncio
    async def test_create_category_trims_whitespace(self, authenticated_client, db_session, test_user):
        """Test category name is trimmed of whitespace"""
        category_data = {"name": "  Trimmed Name  "}

        response = authenticated_client.post("/api/categories", json=category_data)

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["name"] == "Trimmed Name"

    @pytest.mark.asyncio
    async def test_create_category_validation_error_empty_name(self, authenticated_client, db_session, test_user):
        """Test validation error for empty name"""
        category_data = {"name": ""}

        response = authenticated_client.post("/api/categories", json=category_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_category_validation_error_whitespace_only(self, authenticated_client, db_session, test_user):
        """Test validation error for whitespace-only name"""
        category_data = {"name": "   "}

        response = authenticated_client.post("/api/categories", json=category_data)

        assert response.status_code == 422


@pytest.mark.integration
class TestCategoriesRestUpdateEndpoint:
    """Tests for PUT /api/categories/{category_id} endpoint"""

    @pytest.mark.asyncio
    async def test_update_category_success(self, authenticated_client, db_session, test_user):
        """Test successful category update"""
        category = Category(user_id=test_user.id, name="Original Name")
        db_session.add(category)
        db_session.commit()

        update_data = {"name": "Updated Name"}

        response = authenticated_client.put(
            f"/api/categories/{category.id}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Updated Name"

        # Verify in database
        db_session.refresh(category)
        assert category.name == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_category_not_found(self, authenticated_client, db_session, test_user):
        """Test updating non-existent category returns 404"""
        update_data = {"name": "New Name"}

        response = authenticated_client.put("/api/categories/99999", json=update_data)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_category_user_isolation(self, authenticated_client, db_session, test_user, test_user_2):
        """Test users cannot update other users' categories"""
        category = Category(user_id=test_user_2.id, name="User 2 Category")
        db_session.add(category)
        db_session.commit()

        update_data = {"name": "Hacked Name"}
        response = authenticated_client.put(f"/api/categories/{category.id}", json=update_data)

        assert response.status_code == 404

        # Verify category name unchanged
        db_session.refresh(category)
        assert category.name == "User 2 Category"

    @pytest.mark.asyncio
    async def test_update_category_validation_error(self, authenticated_client, db_session, test_user):
        """Test validation error for empty name"""
        category = Category(user_id=test_user.id, name="Valid Name")
        db_session.add(category)
        db_session.commit()

        update_data = {"name": ""}

        response = authenticated_client.put(f"/api/categories/{category.id}", json=update_data)

        assert response.status_code == 422


@pytest.mark.integration
class TestCategoriesRestDeleteEndpoint:
    """Tests for DELETE /api/categories/{category_id} endpoint"""

    @pytest.mark.asyncio
    async def test_delete_category_success(self, authenticated_client, db_session, test_user):
        """Test successful category deletion"""
        category = Category(user_id=test_user.id, name="To Delete")
        db_session.add(category)
        db_session.commit()
        category_id = category.id

        response = authenticated_client.delete(f"/api/categories/{category_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify category was deleted
        deleted_category = db_session.query(Category).filter(Category.id == category_id).first()
        assert deleted_category is None

    @pytest.mark.asyncio
    async def test_delete_category_not_found(self, authenticated_client, db_session, test_user):
        """Test deleting non-existent category returns 404"""
        response = authenticated_client.delete("/api/categories/99999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_category_user_isolation(self, authenticated_client, db_session, test_user, test_user_2):
        """Test users cannot delete other users' categories"""
        category = Category(user_id=test_user_2.id, name="User 2 Category")
        db_session.add(category)
        db_session.commit()

        response = authenticated_client.delete(f"/api/categories/{category.id}")

        assert response.status_code == 404

        # Verify category still exists
        db_session.refresh(category)
        assert category is not None

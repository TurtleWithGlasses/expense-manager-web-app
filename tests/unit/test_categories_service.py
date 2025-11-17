"""
Unit tests for categories service
Tests all category-related business logic functions
"""
import pytest

from app.services import categories
from app.models.category import Category


@pytest.mark.unit
class TestListCategories:
    """Tests for list_categories function"""

    def test_list_categories_returns_user_categories_only(self, db_session, test_user, test_user_2):
        """Test that list_categories only returns categories for the specified user"""
        # Create categories for test_user
        cat1 = Category(user_id=test_user.id, name="Food")
        cat2 = Category(user_id=test_user.id, name="Transport")
        # Create category for test_user_2
        cat3 = Category(user_id=test_user_2.id, name="User 2 Category")

        db_session.add_all([cat1, cat2, cat3])
        db_session.commit()

        # Get categories for test_user
        user_categories = categories.list_categories(db_session, test_user.id)

        assert len(user_categories) == 2
        assert all(cat.user_id == test_user.id for cat in user_categories)
        assert "User 2 Category" not in [cat.name for cat in user_categories]

    def test_list_categories_returns_empty_list_for_no_categories(self, db_session, test_user):
        """Test that empty list is returned when user has no categories"""
        user_categories = categories.list_categories(db_session, test_user.id)

        assert user_categories == []

    def test_list_categories_sorted_alphabetically(self, db_session, test_user):
        """Test that categories are returned in alphabetical order"""
        # Create categories in random order
        cat1 = Category(user_id=test_user.id, name="Zebra")
        cat2 = Category(user_id=test_user.id, name="Apple")
        cat3 = Category(user_id=test_user.id, name="Mango")

        db_session.add_all([cat1, cat2, cat3])
        db_session.commit()

        user_categories = categories.list_categories(db_session, test_user.id)

        category_names = [cat.name for cat in user_categories]
        assert category_names == ["Apple", "Mango", "Zebra"]


@pytest.mark.unit
class TestCreateCategory:
    """Tests for create_category function"""

    def test_create_category_success(self, db_session, test_user):
        """Test successful category creation"""
        category = categories.create_category(
            db=db_session,
            user_id=test_user.id,
            name="New Category"
        )

        assert category is not None
        assert category.id is not None
        assert category.user_id == test_user.id
        assert category.name == "New Category"

    def test_create_category_persisted_to_database(self, db_session, test_user):
        """Test that created category is persisted to database"""
        category = categories.create_category(
            db=db_session,
            user_id=test_user.id,
            name="Persisted Category"
        )

        # Query database directly
        db_category = db_session.query(Category).filter(Category.id == category.id).first()

        assert db_category is not None
        assert db_category.name == "Persisted Category"

    def test_create_multiple_categories_with_same_name_different_users(
        self, db_session, test_user, test_user_2
    ):
        """Test that different users can have categories with the same name"""
        cat1 = categories.create_category(db_session, test_user.id, "Food")
        cat2 = categories.create_category(db_session, test_user_2.id, "Food")

        assert cat1.id != cat2.id
        assert cat1.user_id == test_user.id
        assert cat2.user_id == test_user_2.id
        assert cat1.name == cat2.name == "Food"


@pytest.mark.unit
class TestDeleteCategory:
    """Tests for delete_category function"""

    def test_delete_category_success(self, db_session, test_user):
        """Test successful category deletion"""
        # Create category
        category = Category(user_id=test_user.id, name="To Delete")
        db_session.add(category)
        db_session.commit()
        category_id = category.id

        # Delete category
        categories.delete_category(db_session, test_user.id, category_id)

        # Verify deletion
        deleted_category = db_session.query(Category).filter(Category.id == category_id).first()
        assert deleted_category is None

    def test_delete_category_wrong_user(self, db_session, test_user, test_user_2):
        """Test that user cannot delete another user's category"""
        # Create category for test_user
        category = Category(user_id=test_user.id, name="User 1 Category")
        db_session.add(category)
        db_session.commit()
        category_id = category.id

        # Try to delete as test_user_2
        categories.delete_category(db_session, test_user_2.id, category_id)

        # Category should still exist
        existing_category = db_session.query(Category).filter(Category.id == category_id).first()
        assert existing_category is not None

    def test_delete_nonexistent_category(self, db_session, test_user):
        """Test deleting non-existent category doesn't raise error"""
        # Should not raise any exception
        categories.delete_category(db_session, test_user.id, 99999)


@pytest.mark.unit
class TestUpdateCategoryName:
    """Tests for update_category_name function"""

    def test_update_category_name_success(self, db_session, test_user):
        """Test successful category name update"""
        # Create category
        category = Category(user_id=test_user.id, name="Old Name")
        db_session.add(category)
        db_session.commit()
        category_id = category.id

        # Update name
        updated_category = categories.update_category_name(
            db_session, test_user.id, category_id, "New Name"
        )

        assert updated_category is not None
        assert updated_category.name == "New Name"
        assert updated_category.id == category_id

    def test_update_category_name_strips_whitespace(self, db_session, test_user):
        """Test that category name update strips whitespace"""
        # Create category
        category = Category(user_id=test_user.id, name="Original")
        db_session.add(category)
        db_session.commit()
        category_id = category.id

        # Update with name containing whitespace
        updated_category = categories.update_category_name(
            db_session, test_user.id, category_id, "  Trimmed Name  "
        )

        assert updated_category.name == "Trimmed Name"

    def test_update_category_name_wrong_user(self, db_session, test_user, test_user_2):
        """Test that user cannot update another user's category"""
        # Create category for test_user
        category = Category(user_id=test_user.id, name="Original Name")
        db_session.add(category)
        db_session.commit()
        category_id = category.id

        # Try to update as test_user_2
        result = categories.update_category_name(
            db_session, test_user_2.id, category_id, "Hacked Name"
        )

        assert result is None
        # Verify name wasn't changed
        db_session.refresh(category)
        assert category.name == "Original Name"

    def test_update_nonexistent_category(self, db_session, test_user):
        """Test updating non-existent category returns None"""
        result = categories.update_category_name(
            db_session, test_user.id, 99999, "New Name"
        )

        assert result is None

    def test_update_category_name_empty_string(self, db_session, test_user):
        """Test updating category name to empty string"""
        # Create category
        category = Category(user_id=test_user.id, name="Original")
        db_session.add(category)
        db_session.commit()
        category_id = category.id

        # Update to empty string
        updated_category = categories.update_category_name(
            db_session, test_user.id, category_id, "  "
        )

        # After stripping, it becomes empty
        assert updated_category.name == ""

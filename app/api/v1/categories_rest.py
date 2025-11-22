"""
Categories REST API - JSON endpoints for category management.

This module provides RESTful JSON API endpoints for mobile/external clients.
All endpoints return standardized JSON responses.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import current_user
from app.db.session import get_db
from app.services.categories import (
    list_categories,
    create_category,
    update_category_name,
    delete_category,
    get_category_by_id
)
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryOut
from app.core.responses import (
    success_response,
    created_response,
    not_found_response
)

router = APIRouter(prefix="/api/categories", tags=["categories-rest"])


@router.get("")
async def list_categories_api(
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    List all categories for the current user.

    Returns all categories owned by the authenticated user.
    """
    categories = list_categories(db, user_id=user.id)

    categories_out = [CategoryOut.model_validate(c) for c in categories]
    return success_response(
        data=[c.model_dump(mode='json') for c in categories_out],
        message=f"Found {len(categories_out)} categories"
    )


@router.get("/{category_id}")
async def get_category(
    category_id: int,
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Get a single category by ID.

    Returns the category if found and belongs to the user.
    """
    category = get_category_by_id(db, user.id, category_id)

    if not category:
        return not_found_response("Category not found")

    category_out = CategoryOut.model_validate(category)
    return success_response(
        data=category_out.model_dump(mode='json'),
        message="Category retrieved successfully"
    )


@router.post("")
async def create_category_api(
    category_data: CategoryCreate,
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new category.

    Returns the created category with 201 status code.
    """
    category = create_category(
        db,
        user_id=user.id,
        name=category_data.name
    )

    category_out = CategoryOut.model_validate(category)
    return created_response(
        data=category_out.model_dump(mode='json'),
        message="Category created successfully"
    )


@router.put("/{category_id}")
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Update a category.

    Returns the updated category.
    """
    # Check if category exists
    existing = get_category_by_id(db, user.id, category_id)
    if not existing:
        return not_found_response("Category not found")

    # Update category
    category = update_category_name(
        db,
        user_id=user.id,
        category_id=category_id,
        new_name=category_data.name
    )

    category_out = CategoryOut.model_validate(category)
    return success_response(
        data=category_out.model_dump(mode='json'),
        message="Category updated successfully"
    )


@router.delete("/{category_id}")
async def delete_category_api(
    category_id: int,
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a category.

    Returns success message if deleted.
    """
    # Check if category exists
    category = get_category_by_id(db, user.id, category_id)
    if not category:
        return not_found_response("Category not found")

    # Delete category
    delete_category(db, user_id=user.id, category_id=category_id)

    return success_response(
        message="Category deleted successfully"
    )

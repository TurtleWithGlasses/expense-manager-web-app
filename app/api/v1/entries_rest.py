"""
Entries REST API - JSON endpoints for entry management.

This module provides RESTful JSON API endpoints for mobile/external clients.
All endpoints return standardized JSON responses.
"""

from datetime import date as date_type
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.deps import current_user_jwt
from app.db.session import get_db
from app.services.entries import entries_service
from app.services.user_preferences import user_preferences_service
from app.schemas.entry import EntryCreate, EntryUpdate, EntryOut
from app.core.responses import (
    success_response,
    created_response,
    not_found_response,
    validation_error_response,
    paginated_response
)

router = APIRouter(prefix="/api/entries", tags=["entries-rest"])


@router.get("")
async def list_entries(
    start: str | None = Query(None, description="Start date (ISO format)"),
    end: str | None = Query(None, description="End date (ISO format)"),
    category_id: int | None = Query(None, description="Filter by category ID"),
    type: str | None = Query(None, description="Filter by type (income/expense)"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    sort_by: str = Query("date", description="Sort field"),
    order: str = Query("desc", description="Sort order (asc/desc)"),
    user=Depends(current_user_jwt),
    db: Session = Depends(get_db),
):
    """
    List entries with filtering, sorting, and pagination.

    Returns a paginated list of entries with metadata.
    """
    # Parse dates
    start_date = entries_service.parse_date(start)
    end_date = entries_service.parse_date(end)

    # Get entries
    if start_date and end_date:
        entries = entries_service.search_entries(
            db, user.id,
            start=start_date,
            end=end_date,
            category_id=category_id,
            type=type,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            order=order
        )
        total = entries_service.get_search_entries_count(
            db, user.id,
            start=start_date,
            end=end_date,
            category_id=category_id,
            type=type
        )
    else:
        entries = entries_service.list_entries(
            db, user.id,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            order=order
        )
        total = entries_service.get_entries_count(db, user.id)

    # Convert to schema
    entries_out = [EntryOut.model_validate(e) for e in entries]

    return paginated_response(
        items=[e.model_dump(mode='json') for e in entries_out],
        total=total,
        limit=limit,
        offset=offset,
        message="Entries retrieved successfully"
    )


@router.get("/{entry_id}")
async def get_entry(
    entry_id: int,
    user=Depends(current_user_jwt),
    db: Session = Depends(get_db),
):
    """
    Get a single entry by ID.

    Returns the entry if found and belongs to the user.
    """
    entry = entries_service.get_entry_by_id(db, user.id, entry_id)

    if not entry:
        return not_found_response("Entry not found")

    entry_out = EntryOut.model_validate(entry)
    return success_response(
        data=entry_out.model_dump(mode='json'),
        message="Entry retrieved successfully"
    )


@router.post("")
async def create_entry(
    entry_data: EntryCreate,
    user=Depends(current_user_jwt),
    db: Session = Depends(get_db),
):
    """
    Create a new entry.

    Returns the created entry with 201 status code.
    """
    # Get user's preferred currency if not provided
    currency_code = entry_data.currency_code
    if not currency_code:
        currency_code = user_preferences_service.get_user_currency(db, user.id)

    # Create entry
    entry = entries_service.create_entry(
        db,
        user_id=user.id,
        type=entry_data.type,
        amount=entry_data.amount,
        date=entry_data.date,
        category_id=entry_data.category_id,
        note=entry_data.note,
        currency_code=currency_code
    )

    entry_out = EntryOut.model_validate(entry)
    return created_response(
        data=entry_out.model_dump(mode='json'),
        message="Entry created successfully"
    )


@router.put("/{entry_id}")
async def update_entry(
    entry_id: int,
    entry_data: EntryUpdate,
    user=Depends(current_user_jwt),
    db: Session = Depends(get_db),
):
    """
    Update an existing entry.

    Only provided fields will be updated.
    Returns the updated entry.
    """
    # Check if entry exists
    existing = entries_service.get_entry_by_id(db, user.id, entry_id)
    if not existing:
        return not_found_response("Entry not found")

    # Update entry
    updated_entry = entries_service.update_entry(
        db,
        user.id,
        entry_id,
        type=entry_data.type,
        amount=entry_data.amount,
        date=entry_data.date,
        category_id=entry_data.category_id,
        note=entry_data.note
    )

    entry_out = EntryOut.model_validate(updated_entry)
    return success_response(
        data=entry_out.model_dump(mode='json'),
        message="Entry updated successfully"
    )


@router.delete("/{entry_id}")
async def delete_entry(
    entry_id: int,
    user=Depends(current_user_jwt),
    db: Session = Depends(get_db),
):
    """
    Delete an entry.

    Returns success message if deleted.
    """
    # Check if entry exists
    entry = entries_service.get_entry_by_id(db, user.id, entry_id)
    if not entry:
        return not_found_response("Entry not found")

    # Delete entry
    entries_service.delete_entry(db, user.id, entry_id)

    return success_response(
        message="Entry deleted successfully"
    )


@router.get("/uncategorized/list")
async def list_uncategorized_entries(
    limit: int | None = Query(None, ge=1, le=100, description="Limit results"),
    user=Depends(current_user_jwt),
    db: Session = Depends(get_db),
):
    """
    Get all uncategorized entries for the current user.

    Returns entries without a category assigned.
    """
    entries = entries_service.get_uncategorized_entries(db, user.id, limit=limit)

    entries_out = [EntryOut.model_validate(e) for e in entries]
    return success_response(
        data=[e.model_dump() for e in entries_out],
        message=f"Found {len(entries_out)} uncategorized entries"
    )

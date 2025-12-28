"""
Entries API - HTTP request handlers for entry management.

This module contains thin controller endpoints that delegate to the entries service.
"""

from datetime import date as _date
from fastapi import APIRouter, Depends, Form, Query, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.deps import current_user
from app.db.session import get_db
from app.services.entries import entries_service
from app.services.categories import list_categories
from app.services.user_preferences import user_preferences_service
from app.services.gamification.level_service import LevelService
from app.templates import render
from app.core.cache import get_cache

router = APIRouter(prefix="/entries", tags=["entries"])


# ===== Page Endpoints =====

@router.get("/load-more", response_class=HTMLResponse)
async def load_more_entries(
    request: Request,
    start: str | None = Query(None),
    end: str | None = Query(None),
    category: str | None = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("date", pattern="^(date|amount|category)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    user=Depends(current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """AJAX endpoint for loading more entries (returns only entry rows HTML)"""
    # Parse filters
    start_date = entries_service.parse_date(start)
    end_date = entries_service.parse_date(end)
    category_id = entries_service.parse_category_id(category)

    # Get entries based on filters
    if start_date and end_date:
        entries = entries_service.search_entries(
            db, user.id, start=start_date, end=end_date, category_id=category_id,
            limit=limit, offset=offset, sort_by=sort_by, order=order
        )
    elif category_id:
        entries = entries_service.search_entries(
            db, user.id, category_id=category_id,
            limit=limit, offset=offset, sort_by=sort_by, order=order
        )
    else:
        entries = entries_service.list_entries(
            db, user.id, limit=limit, offset=offset, sort_by=sort_by, order=order
        )

    cats = list_categories(db, user_id=user.id)
    user_currency = user_preferences_service.get_user_currency(db, user.id)

    return render(request, "entries/_list.html",
                  {"entries": entries, "categories": cats, "user_currency": user_currency})


@router.get("/load-more-mobile", response_class=HTMLResponse)
async def load_more_mobile_entries(
    request: Request,
    start: str | None = Query(None),
    end: str | None = Query(None),
    category: str | None = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("date", pattern="^(date|amount|category)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    user=Depends(current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """AJAX endpoint for loading more entries on mobile (returns only mobile cards HTML)"""
    # Parse filters
    start_date = entries_service.parse_date(start)
    end_date = entries_service.parse_date(end)
    category_id = entries_service.parse_category_id(category)

    # Get entries based on filters
    if start_date and end_date:
        entries = entries_service.search_entries(
            db, user.id, start=start_date, end=end_date, category_id=category_id,
            limit=limit, offset=offset, sort_by=sort_by, order=order
        )
    elif category_id:
        entries = entries_service.search_entries(
            db, user.id, category_id=category_id,
            limit=limit, offset=offset, sort_by=sort_by, order=order
        )
    else:
        entries = entries_service.list_entries(
            db, user.id, limit=limit, offset=offset, sort_by=sort_by, order=order
        )

    return render(request, "entries/_mobile_list.html", {"entries": entries})


@router.get("/", response_class=HTMLResponse)
async def page(
    request: Request,
    start: str | None = Query(None),
    end: str | None = Query(None),
    category: str | None = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str | None = Query(None, pattern="^(date|amount|category)$"),
    order: str | None = Query(None, pattern="^(asc|desc)$"),
    user=Depends(current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Main entries page with filtering, sorting, and pagination"""
    # Get sort preferences
    sort_by, order = entries_service.get_sort_preferences(
        db, user.id, sort_by, order, 'entries'
    )

    # Parse filters
    start_date = entries_service.parse_date(start)
    end_date = entries_service.parse_date(end)
    category_id = entries_service.parse_category_id(category)

    # Get entries and total count
    if start_date and end_date:
        entries = entries_service.search_entries(
            db, user.id, start=start_date, end=end_date, category_id=category_id,
            limit=limit, offset=offset, sort_by=sort_by, order=order
        )
        total_count = entries_service.get_search_entries_count(
            db, user.id, start=start_date, end=end_date, category_id=category_id
        )
    elif category_id:
        entries = entries_service.search_entries(
            db, user.id, category_id=category_id,
            limit=limit, offset=offset, sort_by=sort_by, order=order
        )
        total_count = entries_service.get_search_entries_count(
            db, user.id, category_id=category_id
        )
    else:
        entries = entries_service.list_entries(
            db, user.id, limit=limit, offset=offset, sort_by=sort_by, order=order
        )
        total_count = entries_service.get_entries_count(db, user.id)

    # Calculate pagination info
    pagination = entries_service.calculate_pagination_info(offset, limit, total_count)

    cats = list_categories(db, user_id=user.id)
    user_currency = user_preferences_service.get_user_currency(db, user.id)

    return render(request, "entries/index.html", {
        "entries": entries,
        "categories": cats,
        "user": user,
        "today": _date.today().isoformat(),
        "user_currency": user_currency,
        "start_date": start,
        "end_date": end,
        "selected_category": str(category_id) if category_id else None,
        "limit": limit,
        "offset": offset,
        "sort_by": sort_by,
        "order": order,
        **pagination
    })


# ===== Create Entry =====

@router.post("/create", response_class=HTMLResponse)
async def add(
    request: Request,
    type: str = Form(...),
    amount: float = Form(...),
    category_id: int | None = Form(None),
    note: str | None = Form(None),
    date_str: str | None = Form(None),
    currency_code: str | None = Form(None),
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    """Create a new entry"""
    # Get user's preferred currency
    user_currency = currency_code or user_preferences_service.get_user_currency(db, user.id)

    # Parse date
    d = entries_service.parse_date(date_str) or _date.today()

    # Create entry
    entries_service.create_entry(
        db,
        user_id=user.id,
        type=type,
        amount=float(amount),
        date=d,
        category_id=category_id if category_id else None,
        note=note,
        currency_code=user_currency,
    )

    # Award XP for logging entry
    try:
        level_service = LevelService(db)
        level_service.award_entry_xp(user.id)
    except Exception as e:
        # Don't fail entry creation if XP award fails
        print(f"Failed to award XP for entry: {e}")

    # Invalidate forecast cache (spending data changed)
    cache = get_cache()
    cache.invalidate_user_cache(user.id)

    # Return first page of entries
    sort_by, sort_order = entries_service.get_sort_preferences(
        db, user.id, None, None, "entries"
    )
    entries = entries_service.list_entries(
        db, user.id, limit=10, offset=0, sort_by=sort_by, order=sort_order
    )

    user_currency = user_preferences_service.get_user_currency(db, user.id)
    return render(request, "entries/_list.html", {
        "entries": entries,
        "user_currency": user_currency
    })


# ===== Delete Entry =====

@router.post("/delete/{entry_id}", response_class=HTMLResponse)
async def remove(
    request: Request,
    entry_id: int,
    user=Depends(current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Delete an entry"""
    entries_service.delete_entry(db, user.id, entry_id)

    # Invalidate forecast cache (spending data changed)
    cache = get_cache()
    cache.invalidate_user_cache(user.id)

    # Return first page of entries
    sort_by, sort_order = entries_service.get_sort_preferences(
        db, user.id, None, None, "entries"
    )
    entries = entries_service.list_entries(
        db, user.id, limit=10, offset=0, sort_by=sort_by, order=sort_order
    )

    user_currency = user_preferences_service.get_user_currency(db, user.id)
    return render(request, "entries/_list.html", {
        "entries": entries,
        "user_currency": user_currency
    })


# ===== Inline Edit: Amount Cell =====

@router.get("/edit_amount/{entry_id}", response_class=HTMLResponse)
async def edit_amount_cell(
    request: Request,
    entry_id: int,
    user=Depends(current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Get edit form for amount cell"""
    entry = entries_service.get_entry_by_id(db, user.id, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    return render(request, "entries/_cell_amount_edit.html", {"e": entry})


@router.post("/update_amount/{entry_id}", response_class=HTMLResponse)
async def update_amount_cell(
    request: Request,
    entry_id: int,
    amount: float = Form(...),
    user=Depends(current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Update entry amount"""
    entry = entries_service.update_entry_amount(db, user.id, entry_id, amount)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    # Invalidate forecast cache (spending data changed)
    cache = get_cache()
    cache.invalidate_user_cache(user.id)

    return render(request, "entries/_cell_amount.html", {"e": entry})


@router.get("/cell_amount/{entry_id}", response_class=HTMLResponse)
async def amount_cell_display(
    request: Request,
    entry_id: int,
    user=Depends(current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Get display view for amount cell"""
    entry = entries_service.get_entry_by_id(db, user.id, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    return render(request, "entries/_cell_amount.html", {"e": entry})


# ===== Row Display and Edit =====

@router.get("/row/{entry_id}", response_class=HTMLResponse)
async def row_display(
    request: Request,
    entry_id: int,
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    """Get display view for entry row"""
    entry = entries_service.get_entry_by_id(db, user.id, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    cats = list_categories(db, user_id=user.id)
    user_currency = user_preferences_service.get_user_currency(db, user.id)

    return render(request, "entries/_row.html", {
        "e": entry,
        "categories": cats,
        "user_currency": user_currency,
        "wrap": True
    })


@router.get("/edit/{entry_id}", response_class=HTMLResponse)
async def row_edit(
    request: Request,
    entry_id: int,
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    """Get edit form for entry row"""
    entry = entries_service.get_entry_by_id(db, user.id, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    cats = list_categories(db, user_id=user.id)

    return render(request, "entries/_row_edit.html", {
        "e": entry,
        "categories": cats,
        "wrap": True
    })


@router.post("/update/{entry_id}", response_class=HTMLResponse)
async def update_entry_endpoint(
    request: Request,
    entry_id: int,
    type: str = Form(...),
    amount: float = Form(...),
    category_id: int | None = Form(None),
    note: str | None = Form(None),
    date: str = Form(...),
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    """Update an entry"""
    # Parse date
    parsed_date = entries_service.parse_date(date)
    if not parsed_date:
        raise HTTPException(status_code=400, detail="Invalid date format")

    # Update entry
    entry = entries_service.update_entry(
        db,
        user.id,
        entry_id,
        type=type,
        amount=float(amount),
        date=parsed_date,
        category_id=category_id or None,
        note=note
    )

    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    # Invalidate forecast cache (spending data changed)
    cache = get_cache()
    cache.invalidate_user_cache(user.id)

    cats = list_categories(db, user_id=user.id)
    user_currency = user_preferences_service.get_user_currency(db, user.id)

    return render(request, "entries/_row.html", {
        "e": entry,
        "categories": cats,
        "user_currency": user_currency,
        "wrap": True
    })


# ===== JSON API Endpoints =====

@router.get("/uncategorized", response_class=JSONResponse)
async def get_uncategorized_entries(
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    """Get all uncategorized entries for the current user"""
    try:
        entries = entries_service.get_uncategorized_entries(db, user.id)

        entries_data = [
            {
                "id": e.id,
                "type": e.type,
                "amount": float(e.amount),
                "note": e.note,
                "description": e.note,  # Alias for compatibility
                "date": e.date.isoformat() if e.date else None,
                "currency_code": e.currency_code
            }
            for e in entries
        ]

        return JSONResponse({
            "success": True,
            "entries": entries_data,
            "count": len(entries_data)
        })
    except Exception as error:
        return JSONResponse({
            "success": False,
            "message": str(error)
        }, status_code=500)


class UpdateCategoryRequest(BaseModel):
    category_id: int


@router.put("/{entry_id}/category", response_class=JSONResponse)
async def update_entry_category(
    entry_id: int,
    request_data: UpdateCategoryRequest,
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    """Update category for a specific entry"""
    try:
        entry = entries_service.update_entry(
            db,
            user.id,
            entry_id,
            category_id=request_data.category_id
        )

        if not entry:
            return JSONResponse({
                "success": False,
                "message": "Entry not found"
            }, status_code=404)

        # Invalidate forecast cache (category data changed)
        cache = get_cache()
        cache.invalidate_user_cache(user.id)

        return JSONResponse({
            "success": True,
            "message": "Category updated successfully"
        })
    except Exception as error:
        return JSONResponse({
            "success": False,
            "message": str(error)
        }, status_code=500)

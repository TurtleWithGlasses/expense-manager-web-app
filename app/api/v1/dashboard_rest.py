"""
Dashboard REST API - JSON endpoints for dashboard data.

This module provides RESTful JSON API endpoints for mobile/external clients.
All endpoints return standardized JSON responses.
"""

from datetime import date as date_type
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.deps import current_user
from app.db.session import get_db
from app.services.dashboard import dashboard_service
from app.core.responses import success_response

router = APIRouter(prefix="/api/dashboard", tags=["dashboard-rest"])


@router.get("/summary")
async def get_summary(
    start: str | None = Query(None, description="Start date (ISO format)"),
    end: str | None = Query(None, description="End date (ISO format)"),
    category_id: int | None = Query(None, description="Filter by category ID"),
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Get dashboard summary (income, expense, balance) for date range.

    Returns summary statistics with formatted amounts in user's preferred currency.
    Defaults to current month if no date range provided.
    """
    summary = await dashboard_service.get_summary(
        db=db,
        user_id=user.id,
        start_date=start,
        end_date=end,
        category_id=category_id
    )

    # Convert date objects to ISO strings for JSON serialization
    summary["start_date"] = summary["start_date"].isoformat()
    summary["end_date"] = summary["end_date"].isoformat()

    return success_response(
        data=summary,
        message="Dashboard summary retrieved successfully"
    )


@router.get("/expenses")
async def get_expenses_list(
    start: str | None = Query(None, description="Start date (ISO format)"),
    end: str | None = Query(None, description="End date (ISO format)"),
    category_id: int | None = Query(None, description="Filter by category ID"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    sort_by: str | None = Query(None, description="Sort field (date, amount, category)"),
    order: str | None = Query(None, description="Sort order (asc, desc)"),
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Get paginated list of expenses with filtering and sorting.

    Returns expenses list with pagination metadata and total amount.
    Amounts are converted to user's preferred currency.
    """
    result = await dashboard_service.get_expenses_list(
        db=db,
        user_id=user.id,
        start_date=start,
        end_date=end,
        category_id=category_id,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        order=order
    )

    # Convert date and category objects to JSON-serializable format
    for entry in result["entries"]:
        if "date" in entry and entry["date"] is not None:
            entry["date"] = entry["date"].isoformat()
        if "category" in entry and entry["category"] is not None:
            # Convert Category object to dict
            entry["category"] = {
                "id": entry["category"].id,
                "name": entry["category"].name
            }

    return success_response(
        data={
            "entries": result["entries"],
            "total_amount": result["total_amount"],
            "formatted_total": result["formatted_total"],
            "currency_code": result["currency_code"],
            "pagination": {
                "limit": result["limit"],
                "offset": result["offset"],
                "total_count": result["total_count"],
                "showing_from": result["showing_from"],
                "showing_to": result["showing_to"],
                "has_more": result["has_more"]
            }
        },
        message="Expenses list retrieved successfully"
    )


@router.get("/incomes")
async def get_incomes_list(
    start: str | None = Query(None, description="Start date (ISO format)"),
    end: str | None = Query(None, description="End date (ISO format)"),
    category_id: int | None = Query(None, description="Filter by category ID"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    sort_by: str | None = Query(None, description="Sort field (date, amount, category)"),
    order: str | None = Query(None, description="Sort order (asc, desc)"),
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Get paginated list of incomes with filtering and sorting.

    Returns incomes list with pagination metadata and total amount.
    Amounts are converted to user's preferred currency.
    """
    result = await dashboard_service.get_incomes_list(
        db=db,
        user_id=user.id,
        start_date=start,
        end_date=end,
        category_id=category_id,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        order=order
    )

    # Convert date and category objects to JSON-serializable format
    for entry in result["entries"]:
        if "date" in entry and entry["date"] is not None:
            entry["date"] = entry["date"].isoformat()
        if "category" in entry and entry["category"] is not None:
            # Convert Category object to dict
            entry["category"] = {
                "id": entry["category"].id,
                "name": entry["category"].name
            }

    return success_response(
        data={
            "entries": result["entries"],
            "total_amount": result["total_amount"],
            "formatted_total": result["formatted_total"],
            "currency_code": result["currency_code"],
            "pagination": {
                "limit": result["limit"],
                "offset": result["offset"],
                "total_count": result["total_count"],
                "showing_from": result["showing_from"],
                "showing_to": result["showing_to"],
                "has_more": result["has_more"]
            }
        },
        message="Incomes list retrieved successfully"
    )

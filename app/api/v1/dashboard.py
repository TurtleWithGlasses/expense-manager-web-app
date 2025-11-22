from datetime import date
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import current_user
from app.templates import render
from app.services.dashboard import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/summary", response_class=HTMLResponse)
async def summary_panel(
    request: Request,
    start: date | None = Query(None),
    end: date | None = Query(None),
    category: str | None = Query(None),
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    """Get dashboard summary panel (income, expense, balance)"""
    totals = await dashboard_service.get_summary(
        db=db,
        user_id=user.id,
        start_date=start,
        end_date=end,
        category_id=category
    )

    return render(request, "dashboard/_summary.html", {"totals": totals})

@router.get("/expenses", response_class=HTMLResponse)
async def expenses_panel(
    request: Request,
    start: date | None = Query(None),
    end: date | None = Query(None),
    category: str | None = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str | None = Query(None, pattern="^(date|amount|category)$"),
    order: str | None = Query(None, pattern="^(asc|desc)$"),
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    """Get expenses list panel with pagination and sorting"""
    result = await dashboard_service.get_expenses_list(
        db=db,
        user_id=user.id,
        start_date=start,
        end_date=end,
        category_id=category,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        order=order
    )

    return render(
        request,
        "dashboard/_expenses_list.html",
        {
            "rows": result["entries"],
            "total_expense": result["total_amount"],
            "formatted_total": result["formatted_total"],
            "limit": result["limit"],
            "offset": result["offset"],
            "total_count": result["total_count"],
            "showing_from": result["showing_from"],
            "showing_to": result["showing_to"],
            "has_more": result["has_more"]
        },
    )

@router.get("/incomes", response_class=HTMLResponse)
async def incomes_panel(
    request: Request,
    start: date | None = Query(None),
    end: date | None = Query(None),
    category: str | None = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str | None = Query(None, pattern="^(date|amount|category)$"),
    order: str | None = Query(None, pattern="^(asc|desc)$"),
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    """Get incomes list panel with pagination and sorting"""
    result = await dashboard_service.get_incomes_list(
        db=db,
        user_id=user.id,
        start_date=start,
        end_date=end,
        category_id=category,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        order=order
    )

    return render(
        request,
        "dashboard/_incomes_list.html",
        {
            "rows": result["entries"],
            "total_income": result["total_amount"],
            "formatted_total": result["formatted_total"],
            "limit": result["limit"],
            "offset": result["offset"],
            "total_count": result["total_count"],
            "showing_from": result["showing_from"],
            "showing_to": result["showing_to"],
            "has_more": result["has_more"]
        },
    )
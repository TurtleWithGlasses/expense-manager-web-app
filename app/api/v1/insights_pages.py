"""Insights Pages API"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.deps import current_user
from app.templates import render

router = APIRouter(prefix="/insights", tags=["Insights Pages"])


@router.get("/", response_class=HTMLResponse)
async def insights_page(
    request: Request,
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """Financial insights dashboard page"""
    return render(request, "insights.html", {
        "user": user,
        "request": request
    })

"""Goals Pages API"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.deps import current_user
from app.templates import render
from app.core.currency import CURRENCIES
from app.services.user_preferences import user_preferences_service

router = APIRouter(prefix="/goals", tags=["Goals Pages"])


@router.get("/", response_class=HTMLResponse)
async def goals_page(
    request: Request,
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """Financial goals management page"""
    # Get user's currency preference
    user_currency_code = user_preferences_service.get_user_currency(db, user.id)
    user_currency_info = CURRENCIES.get(user_currency_code, CURRENCIES['USD'])

    return render(request, "goals.html", {
        "user": user,
        "request": request,
        "user_currency": user_currency_info,
        "user_currency_code": user_currency_code
    })

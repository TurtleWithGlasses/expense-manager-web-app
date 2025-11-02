"""Settings page endpoint"""
from datetime import datetime
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.deps import current_user
from app.db.session import get_db
from app.models.user import User
from app.models.entry import Entry
from app.models.category import Category
from app.models.user_preferences import UserPreferences
from app.templates import render

router = APIRouter()


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Render the settings page"""

    # Get user preferences
    user_prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()
    user_theme = user_prefs.theme if user_prefs and user_prefs.theme else 'dark'

    # Get account statistics
    entry_count = db.query(func.count(Entry.id)).filter(Entry.user_id == user.id).scalar() or 0
    category_count = db.query(func.count(Category.id)).filter(Category.user_id == user.id).scalar() or 0

    # Calculate days since account creation
    if user.created_at:
        days_active = (datetime.utcnow() - user.created_at).days
    else:
        days_active = 0

    return render(request, "settings/index.html", {
        "user": user,
        "user_theme": user_theme,
        "entry_count": entry_count,
        "category_count": category_count,
        "days_active": days_active,
    })

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
from app.models.weekly_report import UserReportPreferences
from app.templates import render

router = APIRouter()


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Render the settings page"""

    # Refresh user object to ensure we have the latest data (including avatar)
    db.refresh(user)

    # Get user preferences
    user_prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()
    user_theme = user_prefs.theme if user_prefs and user_prefs.theme else 'dark'

    # Get report preferences
    report_prefs = db.query(UserReportPreferences).filter(UserReportPreferences.user_id == user.id).first()

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
        "report_prefs": report_prefs,
        "entry_count": entry_count,
        "category_count": category_count,
        "days_active": days_active,
    })


@router.get("/settings/appearance", response_class=HTMLResponse)
async def appearance_settings_page(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Render the appearance settings page"""

    # Get user preferences
    user_prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()
    user_theme = user_prefs.theme if user_prefs and user_prefs.theme else 'dark'

    # Get display preferences from JSON field
    display_prefs = user_prefs.preferences if user_prefs and user_prefs.preferences else {}
    compact_mode = display_prefs.get('compact_mode', False)
    animations_enabled = display_prefs.get('animations_enabled', True)
    font_size = display_prefs.get('font_size', 'medium')
    voice_commands_enabled = display_prefs.get('voice_commands_enabled', True)  # Default ON

    return render(request, "settings/appearance.html", {
        "user": user,
        "user_theme": user_theme,
        "compact_mode": compact_mode,
        "animations_enabled": animations_enabled,
        "font_size": font_size,
        "voice_commands_enabled": voice_commands_enabled
    })


@router.get("/settings/delete-account", response_class=HTMLResponse)
async def delete_account_page(
    request: Request,
    user: User = Depends(current_user)
):
    """Render the delete account confirmation page"""
    return render(request, "settings/delete_account.html", {
        "user": user
    })


@router.post("/settings/delete-account", response_class=HTMLResponse)
async def delete_account_confirm(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Handle account deletion via POST"""
    # This route will be handled by the JavaScript fetch to /api/profile/account
    # But we keep it here for completeness
    return render(request, "settings/delete_account.html", {
        "user": user
    })

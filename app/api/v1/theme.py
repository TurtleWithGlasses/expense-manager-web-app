"""Theme Settings API"""

from fastapi import APIRouter, Depends, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.deps import current_user
from app.db.session import get_db
from app.models.user_preferences import UserPreferences

router = APIRouter(prefix="/theme", tags=["theme"])


@router.post("/toggle", response_class=JSONResponse)
async def toggle_theme(
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """Toggle between light and dark theme"""
    # Get or create user preferences
    prefs = db.query(UserPreferences).filter(
        UserPreferences.user_id == user.id
    ).first()

    if not prefs:
        prefs = UserPreferences(
            user_id=user.id,
            theme='dark',
            currency_code='USD'
        )
        db.add(prefs)

    # Toggle theme
    current_theme = prefs.theme or 'dark'
    new_theme = 'light' if current_theme == 'dark' else 'dark'
    prefs.theme = new_theme

    db.commit()

    return JSONResponse({
        "success": True,
        "theme": new_theme
    })


@router.post("/set", response_class=JSONResponse)
async def set_theme(
    theme: str = Form(...),
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """Set specific theme (light, dark, or auto)"""
    if theme not in ['light', 'dark', 'auto']:
        return JSONResponse({
            "success": False,
            "message": "Invalid theme. Must be 'light', 'dark', or 'auto'"
        }, status_code=400)

    # Get or create user preferences
    prefs = db.query(UserPreferences).filter(
        UserPreferences.user_id == user.id
    ).first()

    if not prefs:
        prefs = UserPreferences(
            user_id=user.id,
            theme=theme,
            currency_code='USD'
        )
        db.add(prefs)
    else:
        prefs.theme = theme

    db.commit()

    return JSONResponse({
        "success": True,
        "theme": theme
    })


@router.get("/current", response_class=JSONResponse)
async def get_current_theme(
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get current user's theme"""
    prefs = db.query(UserPreferences).filter(
        UserPreferences.user_id == user.id
    ).first()

    theme = prefs.theme if prefs and prefs.theme else 'dark'

    return JSONResponse({
        "theme": theme
    })


@router.post("/preferences", response_class=JSONResponse)
async def set_display_preferences(
    compact_mode: bool = Form(False),
    animations_enabled: bool = Form(True),
    font_size: str = Form("medium"),
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """Set display preferences (compact mode, animations, font size)"""

    # Validate font size
    if font_size not in ['small', 'medium', 'large', 'extra-large']:
        return JSONResponse({
            "success": False,
            "message": "Invalid font size"
        }, status_code=400)

    # Get or create user preferences
    prefs = db.query(UserPreferences).filter(
        UserPreferences.user_id == user.id
    ).first()

    if not prefs:
        prefs = UserPreferences(
            user_id=user.id,
            theme='dark',
            currency_code='USD',
            preferences={}
        )
        db.add(prefs)

    # Update preferences JSON
    if prefs.preferences is None:
        prefs.preferences = {}

    prefs.preferences['compact_mode'] = compact_mode
    prefs.preferences['animations_enabled'] = animations_enabled
    prefs.preferences['font_size'] = font_size

    db.commit()

    return JSONResponse({
        "success": True,
        "message": "Display preferences updated successfully"
    })


@router.get("/preferences", response_class=JSONResponse)
async def get_display_preferences(
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get display preferences"""
    prefs = db.query(UserPreferences).filter(
        UserPreferences.user_id == user.id
    ).first()

    if not prefs or not prefs.preferences:
        return JSONResponse({
            "compact_mode": False,
            "animations_enabled": True,
            "font_size": "medium"
        })

    return JSONResponse({
        "compact_mode": prefs.preferences.get('compact_mode', False),
        "animations_enabled": prefs.preferences.get('animations_enabled', True),
        "font_size": prefs.preferences.get('font_size', 'medium')
    })

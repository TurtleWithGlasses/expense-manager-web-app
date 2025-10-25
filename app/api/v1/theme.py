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
    """Set specific theme (light or dark)"""
    if theme not in ['light', 'dark']:
        return JSONResponse({
            "success": False,
            "message": "Invalid theme. Must be 'light' or 'dark'"
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

"""Achievements Pages API - Phase 3: Full Gamification"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.deps import current_user
from app.templates import render

router = APIRouter(prefix="/achievements", tags=["Achievements Pages"])


@router.get("/", response_class=HTMLResponse)
async def achievements_page(
    request: Request,
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Achievements & Gamification Dashboard Page

    Displays:
    - User's achievement progress and stats
    - All achievements with unlock status
    - Badges collection
    - Leaderboard
    - User level & XP progress
    """
    return render(request, "achievements.html", {
        "user": user,
        "request": request
    })

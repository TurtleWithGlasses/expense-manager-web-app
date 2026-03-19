"""Savings Challenges Pages - Phase 3.2"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import current_user
from app.models.user import User
from app.templates import render
from app.services.gamification.challenge_seed import seed_default_challenges

router = APIRouter(tags=["Challenges Pages"])


@router.get("/challenges", response_class=HTMLResponse)
async def challenges_page(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Savings Challenges overview page."""
    # Seed default challenges on first visit if table is empty
    try:
        created = seed_default_challenges(db)
        if created:
            print(f"Seeded {created} default challenges")
    except Exception as e:
        print(f"Challenge seed error: {e}")

    return render(request, "challenges.html", {
        "user": user,
        "request": request,
    })

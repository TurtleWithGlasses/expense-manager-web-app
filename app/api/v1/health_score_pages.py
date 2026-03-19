"""Financial Health Score UI Page – Phase 34"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import current_user
from app.models.user import User
from app.templates import render

router = APIRouter(prefix="/health-score", tags=["Health Score Pages"])


@router.get("", response_class=HTMLResponse)
async def health_score_page(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Financial Health Score dashboard page."""
    from app.services.gamification.health_score_service import HealthScoreService

    service = HealthScoreService(db)
    score_data = service.calculate_health_score(user.id)
    score_data = HealthScoreService._json_safe(score_data)  # convert Decimals for Jinja2 tojson
    service.save_score(user.id, score_data)
    history = service.get_score_history(user.id, months=6)
    trends = service.get_score_trends(user.id)

    return render(
        request,
        "health_score.html",
        {
            "user": user,
            "request": request,
            "score_data": score_data,
            "history": history,
            "trends": trends,
        },
    )

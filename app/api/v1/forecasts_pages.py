"""
Page routes for Prophet forecasting UI

Phase 4: Advanced ML Features - Prophet Integration
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import current_user
from app.models.user import User


router = APIRouter(prefix="/forecasts", tags=["Forecast Pages"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
@router.get("/index", response_class=HTMLResponse)
def forecasts_page(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Display the Prophet forecasting page

    **Features:**
    - Interactive forecast visualization
    - Configurable forecast horizons (30, 60, 90, 180 days)
    - Chart.js visualizations with confidence bands
    - AI-generated insights
    - Seasonal pattern detection
    - Historical data comparison
    """
    return templates.TemplateResponse(
        "forecasts/index.html",
        {
            "request": request,
            "user": user,
            "active_page": "forecasts"
        }
    )

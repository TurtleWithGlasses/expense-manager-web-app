"""
Scenario Planning Page Routes

UI pages for What-If Analysis and Scenario Planning
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.deps import current_user


router = APIRouter(prefix="/scenarios", tags=["scenarios_pages"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
def scenarios_page(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Scenario Planning page

    Interactive what-if analysis for financial decision making
    """
    return templates.TemplateResponse(
        "scenarios/index.html",
        {
            "request": request,
            "user": user,
            "active_page": "scenarios"
        }
    )

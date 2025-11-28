"""
Help/Documentation Pages

Comprehensive user guide and documentation for all features.
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import current_user
from app.models.user import User
from app.templates import render


router = APIRouter(prefix="", tags=["help"])


@router.get("/help", response_class=HTMLResponse)
async def help_page(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):
    """
    Display comprehensive help and documentation page.

    Covers all features including:
    - Getting started
    - Managing entries
    - Voice commands
    - Categories
    - Reports
    - AI features
    - Settings
    """
    return render(request, "help/help.html", {
        "user": user,
        "active_page": "help"
    })

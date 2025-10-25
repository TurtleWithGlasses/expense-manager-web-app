from fastapi import Request
from starlette.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

_templates = Jinja2Templates(directory="app/templates")

def _get_user_theme(request: Request) -> str:
    """Get user theme from session/database"""
    from app.core.session import get_session
    from app.db.session import SessionLocal
    from app.models.user_preferences import UserPreferences

    # Try to get user from session
    sess = get_session(request)
    if not sess or "id" not in sess:
        return "dark"  # Default theme for non-authenticated users

    # Get user theme from database
    db = SessionLocal()
    try:
        user_id = sess["id"]
        prefs = db.query(UserPreferences).filter(
            UserPreferences.user_id == user_id
        ).first()

        if prefs and prefs.theme:
            return prefs.theme
        return "dark"  # Default theme
    except Exception as e:
        print(f"[WARNING] Error getting user theme: {e}")
        return "dark"
    finally:
        db.close()

def render(a, b=None, c=None) -> HTMLResponse:
    """
    Backward-compatible render:
    - New style: render(request, "tpl.html", {...})
    - Old style: render("tpl.html", {...})  # will still work
    """
    if isinstance(a, Request):
        request: Request = a
        path: str = b  # type: ignore
        context = c or {}
    else:
        # old call style; create a minimal Request so TemplateResponse works
        path: str = a  # type: ignore
        request = Request({"type": "http"})
        context = (b or {})

    # Automatically add user_theme to all templates if not already provided
    if "user_theme" not in context and isinstance(a, Request):
        context["user_theme"] = _get_user_theme(request)

    return _templates.TemplateResponse(path, {"request": request, **context})

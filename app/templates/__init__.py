from fastapi import Request
from starlette.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

_templates = Jinja2Templates(directory="app/templates")

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
    return _templates.TemplateResponse(path, {"request": request, **context})

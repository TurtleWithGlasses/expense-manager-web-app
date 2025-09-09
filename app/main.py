from datetime import date
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import text

from app.api.routes import api_router
from app.core.session import get_session
from app.db.engine import engine
from app.templates import render

app = FastAPI(title="Expense Manager Web")

# ✅ serve everything under /static (css, js, images, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(api_router)

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    sess = get_session(request)
    if not sess:
        return RedirectResponse(url="/login")
    today = date.today()
    start = today.replace(day=1)
    end = today
    return render(
        request,
        "dashboard.html",
        {"user": sess, "start": start.isoformat(), "end": end.isoformat()},
    )

@app.get("/healthz")
async def healthz():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        return {"ok": True}

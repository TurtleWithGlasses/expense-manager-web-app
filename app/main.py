from datetime import date
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import text, func
from sqlalchemy.orm import Session

from app.api.routes import api_router
from app.core.session import get_session
from app.db.engine import engine
from app.db.session import get_db
from app.templates import render
from app.models.entry import Entry

app = FastAPI(title="Expense Manager Web")

# ✅ serve everything under /static (css, js, images, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(api_router)

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    sess = get_session(request)
    if not sess:
        return RedirectResponse(url="/login")

    today = date.today()
    start = today.replace(day=1)
    end = today

    # calculate totals for user
    income_total = db.query(func.sum(Entry.amount))\
        .filter(Entry.user_id == sess["id"], Entry.type == "income").scalar() or 0
    expense_total = db.query(func.sum(Entry.amount))\
        .filter(Entry.user_id == sess["id"], Entry.type == "expense").scalar() or 0

    # pass them to template
    return render(request, "dashboard.html", {
        "user": sess,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "income_total": income_total,
        "expense_total": expense_total
    })

@app.get("/healthz")
async def healthz():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        return {"ok": True}

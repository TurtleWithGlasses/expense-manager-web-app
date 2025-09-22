import os
from datetime import date
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import text, func
from sqlalchemy.orm import Session

from app.api.routes import api_router
from app.core.currency import CURRENCIES
from app.core.session import get_session
from app.db.engine import engine
from app.db.session import get_db
from app.db.base import Base
from app.templates import render
from app.models.entry import Entry
from app.services.user_preferences import user_preferences_service

app = FastAPI(title="Expense Manager Web")

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    try:
        # Create all tables if they don't exist
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        # Don't raise the exception to allow the app to start
        # The health check endpoint will catch database issues

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(api_router)

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    # Check if user is authenticated
    sess = get_session(request)
    if not sess:
        return RedirectResponse(url="/login")
    
    # Get user from database
    from app.models.user import User
    user = db.query(User).filter(User.id == sess["id"]).first()
    if not user:
        return RedirectResponse(url="/login")
    today = date.today()
    start = today.replace(day=1)
    end = today

    # calculate totals for user
    income_total = db.query(func.sum(Entry.amount))\
        .filter(Entry.user_id == user["id"], Entry.type == "income").scalar() or 0
    expense_total = db.query(func.sum(Entry.amount))\
        .filter(Entry.user_id == user["id"], Entry.type == "expense").scalar() or 0
    
    user_currency_code = user_preferences_service.get_user_currency(db, user["id"])
    user_currency_info = CURRENCIES.get(user_currency_code, CURRENCIES['USD'])

    return render(request, "dashboard.html", {
        "user": user,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "income_total": income_total,
        "expense_total": expense_total,
        "user_currency": user_currency_info,
        "user_currency_code": user_currency_code,
    })

@app.get("/healthz")
async def healthz():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        return {"ok": True}
    
    
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
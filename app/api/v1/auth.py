from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.schemas.auth import RegisterIn, LoginIn
from app.services.auth import create_user, authenticate_user
from app.db.session import get_db
from app.core.session import set_session, clear_session
from app.core.config import settings
from app.templates import render


router = APIRouter(tags=["auth"])


@router.get("/login", response_class=HTMLResponse)
async def login_page():
    return render("auth/login.html")

@router.post("/login")
async def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = authenticate_user(db, email=email, password=password)
    if not user:
        return render("auth/login.html", {"error": "Invalid credentials"})
    resp = RedirectResponse(url="/", status_code=303)
    set_session(resp, {"id": user.id, "email": user.email})
    return resp

@router.get("/register", response_class=HTMLResponse)
async def register_page():
    return render("auth/register.html")

@router.post("/register")
async def register(email: str = Form(...), password: str = Form(...), full_name: str = Form(None), db: Session = Depends(get_db)):
    user = create_user(db, email=email, password=password, full_name=full_name)
    resp = RedirectResponse(url="/", status_code=303)
    set_session(resp, {"id": user.id, "email": user.email})
    return resp

@router.post("/logout")
async def logout():
    resp = RedirectResponse(url="/login", status_code=303)
    clear_session(resp)
    return resp
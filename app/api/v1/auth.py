from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.services.auth import create_user, authenticate_user
from app.db.session import get_db
from app.core.session import set_session, clear_session
from app.templates import render

router = APIRouter(tags=["auth"])

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return render(request, "auth/login.html")

@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    try:
        user = authenticate_user(db, email=email, password=password)
        if not user:
            return render(request, "auth/login.html", {"error": "Invalid email or password"})
        
        resp = RedirectResponse(url="/", status_code=303)
        set_session(resp, {"id": user.id, "email": user.email})
        return resp
    except Exception as e:
        return render(request, "auth/login.html", {"error": "Login failed. Please try again."})

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return render(request, "auth/register.html")

@router.post("/register")
async def register(
    request: Request,
    email: str = Form(...), 
    password: str = Form(...), 
    confirm_password: str = Form(...),
    full_name: str = Form(None), 
    db: Session = Depends(get_db)
):
    try:
        # Validate passwords match
        if password != confirm_password:
            return render(request, "auth/register.html", {"error": "Passwords do not match"})
        
        # Validate password strength (basic)
        if len(password) < 8:
            return render(request, "auth/register.html", {"error": "Password must be at least 8 characters long"})
        
        user = create_user(db, email=email, password=password, full_name=full_name)
        resp = RedirectResponse(url="/", status_code=303)
        set_session(resp, {"id": user.id, "email": user.email})
        return resp
        
    except ValueError as e:
        # User already exists or other validation error
        return render(request, "auth/register.html", {"error": str(e)})
    except Exception as e:
        return render(request, "auth/register.html", {"error": "Registration failed. Please try again."})

@router.post("/logout")
async def logout():
    resp = RedirectResponse(url="/login", status_code=303)
    clear_session(resp)
    return resp

@router.get("/logout")  # Also handle GET requests for logout
async def logout_get():
    resp = RedirectResponse(url="/login", status_code=303)
    clear_session(resp)
    return resp
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.services.auth import create_user, authenticate_user, verify_email, resend_verification_email, request_password_reset, reset_password
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
    except ValueError as e:
        # Email not verified error
        print(f"❌ Login failed: {e}")
        return render(request, "auth/login.html", {
            "error": str(e),
            "show_resend": True,
            "email": email
        })
    except Exception as e:
        print(f"❌ Login failed: {e}")
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
        print(f"🔍 Attempting to register user: {email}")
        
        # Validate passwords match
        if password != confirm_password:
            print("❌ Passwords do not match")
            return render(request, "auth/register.html", {"error": "Passwords do not match"})
        
        # Validate password strength (basic)
        if len(password) < 8:
            print("❌ Password too short")
            return render(request, "auth/register.html", {"error": "Password must be at least 8 characters long"})
        
        print("✅ Validation passed, creating user...")
        user = await create_user(db, email=email, password=password, full_name=full_name)
        print(f"✅ User created successfully: {user.id}")
        
        # Redirect to verification sent page instead of dashboard
        resp = RedirectResponse(url="/verification-sent", status_code=303)
        print("✅ Redirecting to verification sent page")
        return resp
        
    except ValueError as e:
        # User already exists or other validation error
        print(f"❌ Validation error: {e}")
        return render(request, "auth/register.html", {"error": str(e)})
    except Exception as e:
        print(f"❌ Registration failed: {e}")
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

@router.get("/confirm-email/{token}", response_class=HTMLResponse)
async def confirm_email_page(request: Request, token: str, db: Session = Depends(get_db)):
    """Email confirmation page"""
    user = verify_email(db, token)
    if user:
        # Set session for verified user and redirect to dashboard
        resp = RedirectResponse(url="/", status_code=303)
        set_session(resp, {"id": user.id, "email": user.email})
        return resp
    else:
        return render(request, "auth/email_confirmed.html", {"error": "Invalid or expired confirmation link"})

@router.get("/verification-sent", response_class=HTMLResponse)
async def verification_sent_page(request: Request):
    """Verification email sent confirmation page"""
    return render(request, "auth/verification_sent.html")

@router.get("/resend-verification", response_class=HTMLResponse)
async def resend_verification_page(request: Request):
    """Resend verification email page"""
    return render(request, "auth/resend_verification.html")

@router.post("/resend-verification", response_class=HTMLResponse)
async def resend_verification(
    request: Request,
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    """Resend verification email"""
    try:
        success = await resend_verification_email(db, email)
        if success:
            return render(request, "auth/verification_sent.html", {"email": email})
        else:
            return render(request, "auth/login.html", {"error": "Email not found or already verified"})
    except Exception as e:
        print(f"❌ Failed to resend verification email: {e}")
        return render(request, "auth/login.html", {"error": "Failed to resend verification email"})

@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    """Password reset request page"""
    return render(request, "auth/forgot_password.html")

@router.post("/forgot-password", response_class=HTMLResponse)
async def forgot_password(
    request: Request,
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    """Request password reset"""
    try:
        success = await request_password_reset(db, email)
        if success:
            return render(request, "auth/password_reset_sent.html", {"email": email})
        else:
            # Don't reveal if email exists for security
            return render(request, "auth/password_reset_sent.html", {"email": email})
    except Exception as e:
        print(f"❌ Password reset request failed: {e}")
        return render(request, "auth/forgot_password.html", {"error": "Failed to process password reset request"})

@router.get("/reset-password/{token}", response_class=HTMLResponse)
async def reset_password_page(request: Request, token: str, db: Session = Depends(get_db)):
    """Password reset form page"""
    # Verify token is valid
    from app.models.user import User
    from datetime import datetime
    user = db.query(User).filter(
        User.password_reset_token == token,
        User.password_reset_expires > datetime.utcnow()
    ).first()
    
    if not user:
        return render(request, "auth/reset_password.html", {"error": "Invalid or expired reset link"})
    
    return render(request, "auth/reset_password.html", {"token": token})

@router.post("/reset-password/{token}", response_class=HTMLResponse)
async def reset_password_submit(
    request: Request,
    token: str,
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Submit new password"""
    try:
        # Validate passwords match
        if password != confirm_password:
            return render(request, "auth/reset_password.html", {"token": token, "error": "Passwords do not match"})
        
        # Validate password strength
        if len(password) < 8:
            return render(request, "auth/reset_password.html", {"token": token, "error": "Password must be at least 8 characters long"})
        
        # Reset password
        user = reset_password(db, token, password)
        if user:
            return render(request, "auth/password_reset_success.html")
        else:
            return render(request, "auth/reset_password.html", {"token": token, "error": "Invalid or expired reset link"})
            
    except Exception as e:
        print(f"❌ Password reset failed: {e}")
        return render(request, "auth/reset_password.html", {"token": token, "error": "Password reset failed. Please try again."})

@router.get("/test-email")
async def test_email():
    """Test email sending functionality"""
    from app.services.email import email_service
    try:
        result = await email_service.send_email(
            to_email="mhmtsoylu1928@gmail.com",
            subject="Test Email from Budget Pulse",
            html_content="<h1>Test Email</h1><p>This is a test email to verify SMTP configuration.</p>",
            text_content="Test Email\n\nThis is a test email to verify SMTP configuration."
        )
        return {"status": "success" if result else "failed", "message": "Email test completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
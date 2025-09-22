import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import hash_password, verify_password
from app.services.email import email_service

def generate_token() -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(32)

async def create_user(db: Session, email: str, password: str, full_name: str = None, send_confirmation: bool = True):
    """Create a new user account with email verification"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise ValueError("User with this email already exists")
    
    # Generate verification token
    verification_token = generate_token()
    verification_expires = datetime.utcnow() + timedelta(hours=24)
    
    # Create new user (unverified by default)
    hashed_password = hash_password(password)
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hashed_password,
        is_verified=False,
        verification_token=verification_token,
        verification_token_expires=verification_expires
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Send confirmation email (don't fail registration if email fails)
    if send_confirmation:
        try:
            await email_service.send_confirmation_email(email, verification_token)
            print(f"✅ Confirmation email sent to {email}")
        except Exception as e:
            print(f"⚠️  Failed to send confirmation email to {email}: {e}")
            # Don't fail registration if email sending fails
    
    return user

def authenticate_user(db: Session, email: str, password: str):
    """Authenticate user with email and password"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    # Check if email is verified
    if not user.is_verified:
        raise ValueError("Please verify your email address before logging in")
    
    return user

def verify_email(db: Session, token: str):
    """Verify user's email with token"""
    user = db.query(User).filter(
        User.verification_token == token,
        User.verification_token_expires > datetime.utcnow()
    ).first()
    
    if not user:
        return None
    
    # Mark as verified and clear token
    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    
    db.commit()
    db.refresh(user)
    return user

async def resend_verification_email(db: Session, email: str):
    """Resend verification email"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    
    if user.is_verified:
        return False  # Already verified
    
    # Generate new token
    verification_token = generate_token()
    verification_expires = datetime.utcnow() + timedelta(hours=24)
    
    user.verification_token = verification_token
    user.verification_token_expires = verification_expires
    
    db.commit()
    
    # Send email
    return await email_service.send_confirmation_email(email, verification_token)

async def request_password_reset(db: Session, email: str):
    """Request password reset"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False  # Don't reveal if email exists
    
    # Generate reset token
    reset_token = generate_token()
    reset_expires = datetime.utcnow() + timedelta(hours=1)
    
    user.password_reset_token = reset_token
    user.password_reset_expires = reset_expires
    
    db.commit()
    
    # Send reset email
    return await email_service.send_password_reset_email(email, reset_token)

def reset_password(db: Session, token: str, new_password: str):
    """Reset password with token"""
    user = db.query(User).filter(
        User.password_reset_token == token,
        User.password_reset_expires > datetime.utcnow()
    ).first()
    
    if not user:
        return None
    
    # Update password and clear reset token
    user.hashed_password = hash_password(new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    
    db.commit()
    db.refresh(user)
    return user
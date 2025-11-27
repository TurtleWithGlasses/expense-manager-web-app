from fastapi import Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.session import get_session
from app.db.session import get_db
from app.models.user import User
from app.core.jwt import get_user_id_from_token

security = HTTPBearer()

def current_user(request: Request, db: Session = Depends(get_db)):
    """Get current authenticated user from session"""
    session_data = get_session(request)
    if not session_data:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_id = session_data.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Verify user still exists in database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Check if email is verified
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email address")
    
    return user

def optional_user(request: Request, db: Session = Depends(get_db)):
    """Get current user if authenticated, None otherwise"""
    try:
        return current_user(request, db)
    except HTTPException:
        return None

def current_user_allow_unverified(request: Request, db: Session = Depends(get_db)):
    """Get current user without email verification check"""
    session_data = get_session(request)
    if not session_data:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = session_data.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid session")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user

def current_user_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user from JWT token.

    This dependency is used by REST API endpoints for mobile/external clients.
    Expects Bearer token in Authorization header.
    """
    # Extract token from credentials
    token = credentials.credentials

    # Extract user ID from token
    user_id = get_user_id_from_token(token)
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    # Verify user still exists in database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    # Check if email is verified
    if not user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Please verify your email address"
        )

    return user

def optional_user_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current user from JWT if authenticated, None otherwise"""
    try:
        return current_user_jwt(credentials, db)
    except HTTPException:
        return None

def admin_user(request: Request, db: Session = Depends(get_db)):
    """
    Get current authenticated admin user.

    Requires:
    - User must be authenticated
    - User must have is_admin = True
    - Only mhmtsoylu1928@gmail.com is admin

    Raises:
    - 401 if not authenticated
    - 403 if not admin
    """
    user = current_user(request, db)

    if not user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    return user
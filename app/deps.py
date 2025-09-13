from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.session import get_session
from app.db.session import get_db
from app.models.user import User

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
    
    return {"id": user.id, "email": user.email}

def optional_user(request: Request, db: Session = Depends(get_db)):
    """Get current user if authenticated, None otherwise"""
    try:
        return current_user(request, db)
    except HTTPException:
        return None
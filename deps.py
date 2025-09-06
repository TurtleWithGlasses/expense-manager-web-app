# app/deps.py
from fastapi import Request, HTTPException, status
from app.core.session import get_session

def current_user(request: Request):
    sess = get_session(request)
    if not sess:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return sess  # {"id": int, "email": str}

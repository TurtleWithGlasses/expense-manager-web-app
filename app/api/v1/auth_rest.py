"""
Authentication REST API - JSON endpoints for JWT token-based authentication.

This module provides RESTful JSON API endpoints for mobile/external clients
using JWT tokens for stateless authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field

from app.db.session import get_db
from app.models.user import User
from app.services.auth import authenticate_user, create_user
from app.core.jwt import create_access_token, create_refresh_token, verify_token
from app.core.responses import success_response, error_response, created_response

router = APIRouter(prefix="/api/auth", tags=["auth-rest"])
security = HTTPBearer()


class LoginRequest(BaseModel):
    """Request schema for login"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")


class RegisterRequest(BaseModel):
    """Request schema for registration"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    full_name: str | None = Field(None, max_length=255, description="Full name (optional)")


class RefreshTokenRequest(BaseModel):
    """Request schema for token refresh"""
    refresh_token: str = Field(..., description="Refresh token")


class TokenResponse(BaseModel):
    """Response schema for token endpoints"""
    access_token: str = Field(..., description="JWT access token (30 min expiry)")
    refresh_token: str = Field(..., description="JWT refresh token (7 day expiry)")
    token_type: str = Field(default="bearer", description="Token type")


@router.post("/login")
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login endpoint for mobile/API clients.

    Returns JWT access and refresh tokens for stateless authentication.
    Unlike the web login, this does not create a session.
    """
    # Authenticate user
    try:
        user = authenticate_user(db, login_data.email, login_data.password)
    except ValueError as e:
        # User exists but email not verified
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return success_response(
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name
            }
        },
        message="Login successful"
    )


@router.post("/register")
async def register(
    register_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Registration endpoint for mobile/API clients.

    Creates a new user account. For mobile clients, email verification is
    bypassed and users are auto-verified.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == register_data.email).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user (without sending email for mobile clients)
    user = await create_user(
        db=db,
        email=register_data.email,
        password=register_data.password,
        full_name=register_data.full_name,
        send_confirmation=False  # Don't send email for mobile
    )

    # Note: In production, you would send a verification email here
    # For now, we'll auto-verify for mobile clients
    user.is_verified = True
    db.commit()

    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return created_response(
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name
            }
        },
        message="Registration successful"
    )


@router.post("/refresh")
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Token refresh endpoint.

    Accepts a valid refresh token and returns a new access token.
    This allows mobile apps to maintain authentication without requiring
    the user to log in again.
    """
    # Verify refresh token
    payload = verify_token(token_data.refresh_token, token_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    # Extract user ID
    try:
        user_id = int(payload.get("sub"))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # Verify user still exists and is verified
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not verified"
        )

    # Generate new access token
    new_access_token = create_access_token(data={"sub": str(user.id)})

    return success_response(
        data={
            "access_token": new_access_token,
            "token_type": "bearer"
        },
        message="Token refreshed successfully"
    )


@router.post("/logout")
async def logout():
    """
    Logout endpoint for mobile/API clients.

    Since JWT is stateless, logout is handled client-side by deleting
    the stored tokens. This endpoint exists for API consistency and
    could be extended with token blacklisting in the future.
    """
    return success_response(
        message="Logout successful. Please delete tokens on client side."
    )

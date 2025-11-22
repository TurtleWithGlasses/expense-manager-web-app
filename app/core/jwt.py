"""
JWT (JSON Web Token) utilities for mobile/API authentication.

This module provides JWT token generation and validation for stateless
authentication, primarily for mobile and external API clients.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from app.core.config import settings


# JWT Configuration
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 minutes
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7 days


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary containing token payload (typically {"sub": user_id})
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string

    Example:
        >>> token = create_access_token({"sub": "123"})
        >>> # Returns: "eyJhbGc..."
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Dictionary containing token payload (typically {"sub": user_id})
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT refresh token string

    Example:
        >>> token = create_refresh_token({"sub": "123"})
        >>> # Returns: "eyJhbGc..."
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string to verify
        token_type: Expected token type ("access" or "refresh")

    Returns:
        Decoded token payload if valid, None if invalid

    Example:
        >>> payload = verify_token("eyJhbGc...")
        >>> if payload:
        ...     user_id = payload["sub"]
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Verify token type
        if payload.get("type") != token_type:
            return None

        return payload

    except JWTError:
        return None


def get_user_id_from_token(token: str) -> Optional[int]:
    """
    Extract user ID from a valid access token.

    Args:
        token: JWT access token string

    Returns:
        User ID as integer if token is valid, None otherwise

    Example:
        >>> user_id = get_user_id_from_token("eyJhbGc...")
        >>> if user_id:
        ...     print(f"User ID: {user_id}")
    """
    payload = verify_token(token, token_type="access")
    if not payload:
        return None

    try:
        user_id = int(payload.get("sub"))
        return user_id
    except (ValueError, TypeError):
        return None

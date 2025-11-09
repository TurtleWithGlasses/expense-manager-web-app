"""
Rate limiting configuration for the application.
Prevents brute force attacks and API abuse.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

# Create limiter instance
limiter = Limiter(key_func=get_remote_address)

# Common rate limit decorators
def auth_rate_limit(request: Request):
    """
    Rate limit for authentication endpoints.
    Allows 5 attempts per 15 minutes per IP address.
    """
    return "5 per 15 minutes"

def api_rate_limit(request: Request):
    """
    Rate limit for general API endpoints.
    Allows 100 requests per minute per IP address.
    """
    return "100 per minute"

def strict_rate_limit(request: Request):
    """
    Strict rate limit for sensitive operations.
    Allows 3 attempts per hour per IP address.
    """
    return "3 per hour"

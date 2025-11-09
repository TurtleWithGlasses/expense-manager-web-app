"""
Security headers middleware for the application.
Adds important security headers to all responses.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.

    Headers added:
    - X-Content-Type-Options: Prevents MIME type sniffing
    - X-Frame-Options: Prevents clickjacking attacks
    - X-XSS-Protection: Enables XSS filter in older browsers
    - Strict-Transport-Security: Enforces HTTPS (only in production)
    - Content-Security-Policy: Controls resource loading
    - Referrer-Policy: Controls referrer information
    - Permissions-Policy: Controls browser features
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking by disallowing framing
        response.headers["X-Frame-Options"] = "DENY"

        # Enable XSS filter in older browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HSTS - Force HTTPS (only in production)
        # Comment out if you're not using HTTPS
        from app.core.config import settings
        if settings.ENV == "production":
            # 1 year = 31536000 seconds
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Content Security Policy
        # Adjust this based on your needs (external scripts, images, etc.)
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' data: https://fonts.gstatic.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
        response.headers["Content-Security-Policy"] = csp_policy

        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Control browser features
        permissions_policy = (
            "geolocation=(), "
            "midi=(), "
            "camera=(), "
            "usb=(), "
            "magnetometer=(), "
            "accelerometer=(), "
            "gyroscope=(), "
            "microphone=()"
        )
        response.headers["Permissions-Policy"] = permissions_policy

        return response

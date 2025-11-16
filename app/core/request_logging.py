"""
Request logging middleware for tracking HTTP requests with unique IDs.

This middleware:
- Assigns a unique request ID to each incoming request
- Logs request start and completion
- Measures request duration
- Captures user information if authenticated
"""

import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests with unique request IDs.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Store request ID in request state for access in route handlers
        request.state.request_id = request_id

        # Get basic request info
        method = request.method
        endpoint = request.url.path
        query_params = str(request.url.query) if request.url.query else ""

        # Skip logging for health check and static files to reduce noise
        skip_logging = (
            endpoint == "/health"
            or endpoint.startswith("/static/")
            or endpoint.startswith("/favicon")
        )

        # Start timing
        start_time = time.time()

        # Log request start (unless skipped)
        if not skip_logging:
            logger.info(
                f"Request started: {method} {endpoint}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "endpoint": endpoint,
                    "query_params": query_params,
                    "client_ip": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", "unknown"),
                }
            )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log request completion (unless skipped)
            if not skip_logging:
                # Try to get user ID from request state if available
                user_id = getattr(request.state, "user_id", None)

                logger.info(
                    f"Request completed: {method} {endpoint} - {response.status_code}",
                    extra={
                        "request_id": request_id,
                        "method": method,
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "duration": duration_ms,
                        "user_id": user_id,
                    }
                )

            # Add request ID to response headers for debugging
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log error
            logger.error(
                f"Request failed: {method} {endpoint} - {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "endpoint": endpoint,
                    "duration": duration_ms,
                },
                exc_info=True
            )

            # Re-raise the exception
            raise


def get_request_id(request: Request) -> str:
    """
    Get the request ID from the request state.

    Args:
        request: FastAPI/Starlette request object

    Returns:
        Request ID string, or "unknown" if not found
    """
    return getattr(request.state, "request_id", "unknown")

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

from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware:
    """
    Middleware to log all HTTP requests with unique request IDs.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Get basic request info
        method = scope["method"]
        endpoint = scope["path"]
        query_string = scope.get("query_string", b"").decode("utf-8")

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
            # Get client info
            client = scope.get("client")
            client_ip = client[0] if client else "unknown"

            # Get headers
            headers = dict(scope.get("headers", []))
            user_agent = headers.get(b"user-agent", b"unknown").decode("utf-8", errors="ignore")

            logger.info(
                f"Request started: {method} {endpoint}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "endpoint": endpoint,
                    "query_params": query_string,
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                }
            )

        # Create a wrapper for send to capture the response status
        status_code = None

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                # Add request ID to response headers
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode()))
                message["headers"] = headers
            await send(message)

        # Process request
        try:
            await self.app(scope, receive, send_wrapper)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log request completion (unless skipped)
            if not skip_logging and status_code is not None:
                logger.info(
                    f"Request completed: {method} {endpoint} - {status_code}",
                    extra={
                        "request_id": request_id,
                        "method": method,
                        "endpoint": endpoint,
                        "status_code": status_code,
                        "duration": duration_ms,
                    }
                )

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
    Get the request ID from the request headers.

    Args:
        request: FastAPI/Starlette request object

    Returns:
        Request ID string, or "unknown" if not found
    """
    return request.headers.get("x-request-id", "unknown")

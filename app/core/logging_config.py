"""
Logging configuration for the Expense Manager application.

This module sets up structured logging with different log levels,
formatters, and handlers for development and production environments.
"""

import logging
import sys
import os
from pathlib import Path
from typing import Optional
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs in JSON format for production.
    Makes it easier to parse logs in log aggregation systems.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "endpoint"):
            log_data["endpoint"] = record.endpoint
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "duration"):
            log_data["duration_ms"] = record.duration

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds colors to log levels for better readability in development.
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"

        # Format the message
        formatted = super().format(record)

        # Reset levelname for potential reuse
        record.levelname = levelname

        return formatted


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    enable_json_logs: bool = False
) -> None:
    """
    Set up logging configuration for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                  Defaults to INFO for production, DEBUG for development.
        log_file: Path to log file. If None, logs only to console.
        enable_json_logs: If True, use JSON formatter (useful for production).
                         If False, use colored formatter (better for development).
    """
    # Get environment from environment variable (avoid circular import)
    env = os.getenv("ENV", "development")

    # Determine log level based on environment
    if log_level is None:
        log_level = "INFO" if env == "production" else "DEBUG"

    # Auto-enable JSON logs in production
    if env == "production" and not enable_json_logs:
        enable_json_logs = True

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    # Choose formatter based on environment
    if enable_json_logs:
        formatter = JSONFormatter()
    else:
        formatter = ColoredFormatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Add file handler if log file specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))

        # Always use JSON format for file logs
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)

    # Set log levels for third-party libraries to reduce noise
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

    # Configure uvicorn.access logger for HTTP request logging
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    if env == "production":
        # Suppress access logs in production
        uvicorn_access_logger.setLevel(logging.WARNING)
    else:
        # Enable access logs in development (env can be "dev" or "development")
        uvicorn_access_logger.setLevel(logging.INFO)
        # Allow propagation so uvicorn can add its own handler and output logs
        uvicorn_access_logger.propagate = True

    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.INFO)
    logging.getLogger("apscheduler").setLevel(logging.INFO)

    # Log initial setup message
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging initialized - Level: {log_level}, Environment: {env}, "
        f"JSON Logs: {enable_json_logs}, Log File: {log_file or 'None'}"
    )

    # Debug: Log uvicorn.access logger configuration in development
    if env != "production":
        uvicorn_access_test = logging.getLogger("uvicorn.access")
        logger.debug(f"uvicorn.access logger level: {uvicorn_access_test.level}")
        logger.debug(f"uvicorn.access logger handlers: {len(uvicorn_access_test.handlers)}")
        logger.debug(f"uvicorn.access logger propagate: {uvicorn_access_test.propagate}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Convenience functions for common logging patterns
def log_request_start(logger: logging.Logger, request_id: str, method: str, endpoint: str, user_id: Optional[int] = None):
    """Log the start of an HTTP request."""
    extra = {"request_id": request_id, "method": method, "endpoint": endpoint}
    if user_id:
        extra["user_id"] = user_id
    logger.info(f"Request started: {method} {endpoint}", extra=extra)


def log_request_end(logger: logging.Logger, request_id: str, status_code: int, duration_ms: float):
    """Log the end of an HTTP request."""
    extra = {"request_id": request_id, "status_code": status_code, "duration": duration_ms}
    logger.info(f"Request completed: {status_code} ({duration_ms:.2f}ms)", extra=extra)


def log_database_query(logger: logging.Logger, query_type: str, table: str, duration_ms: float):
    """Log database query execution."""
    logger.debug(f"Database query: {query_type} on {table} ({duration_ms:.2f}ms)")


def log_ai_operation(logger: logging.Logger, operation: str, user_id: int, success: bool, duration_ms: float):
    """Log AI/ML operations."""
    extra = {"user_id": user_id, "duration": duration_ms}
    status = "succeeded" if success else "failed"
    logger.info(f"AI operation '{operation}' {status} ({duration_ms:.2f}ms)", extra=extra)


def log_email_sent(logger: logging.Logger, recipient: str, subject: str, success: bool):
    """Log email sending attempts."""
    status = "sent successfully" if success else "failed to send"
    logger.info(f"Email {status} to {recipient}: {subject}")


def log_user_action(logger: logging.Logger, user_id: int, action: str, details: Optional[str] = None):
    """Log user actions for audit trail."""
    extra = {"user_id": user_id}
    message = f"User action: {action}"
    if details:
        message += f" - {details}"
    logger.info(message, extra=extra)

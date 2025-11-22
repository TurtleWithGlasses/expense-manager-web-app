"""
JSON response utilities for REST API endpoints.

This module provides standardized response formats for JSON API endpoints,
ensuring consistency across all API responses.
"""

from typing import Any, Optional
from fastapi.responses import JSONResponse


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200
) -> JSONResponse:
    """
    Create a successful JSON response.

    Args:
        data: Response data (can be dict, list, or any JSON-serializable type)
        message: Success message
        status_code: HTTP status code (default: 200)

    Returns:
        JSONResponse with standardized success format

    Examples:
        >>> success_response({"id": 1, "name": "Test"})
        JSONResponse({"success": True, "message": "Success", "data": {"id": 1, "name": "Test"}})

        >>> success_response([1, 2, 3], "Items retrieved")
        JSONResponse({"success": True, "message": "Items retrieved", "data": [1, 2, 3]})
    """
    response_data = {
        "success": True,
        "message": message
    }

    if data is not None:
        response_data["data"] = data

    return JSONResponse(content=response_data, status_code=status_code)


def error_response(
    message: str,
    errors: Optional[dict | list] = None,
    status_code: int = 400
) -> JSONResponse:
    """
    Create an error JSON response.

    Args:
        message: Error message
        errors: Optional detailed errors (validation errors, etc.)
        status_code: HTTP status code (default: 400)

    Returns:
        JSONResponse with standardized error format

    Examples:
        >>> error_response("Validation failed", {"name": "Required"}, 422)
        JSONResponse({"success": False, "message": "Validation failed", "errors": {"name": "Required"}})

        >>> error_response("Not found", status_code=404)
        JSONResponse({"success": False, "message": "Not found"})
    """
    response_data = {
        "success": False,
        "message": message
    }

    if errors is not None:
        response_data["errors"] = errors

    return JSONResponse(content=response_data, status_code=status_code)


def paginated_response(
    items: list,
    total: int,
    limit: int,
    offset: int,
    message: str = "Success"
) -> JSONResponse:
    """
    Create a paginated JSON response.

    Args:
        items: List of items for current page
        total: Total number of items across all pages
        limit: Items per page
        offset: Current offset
        message: Success message

    Returns:
        JSONResponse with paginated data and metadata

    Examples:
        >>> paginated_response([1, 2, 3], 25, 10, 0)
        JSONResponse({
            "success": True,
            "message": "Success",
            "data": [1, 2, 3],
            "pagination": {
                "total": 25,
                "limit": 10,
                "offset": 0,
                "showing_from": 1,
                "showing_to": 3,
                "has_more": True
            }
        })
    """
    showing_from = offset + 1 if total > 0 else 0
    showing_to = min(offset + len(items), total)
    has_more = showing_to < total

    return JSONResponse(content={
        "success": True,
        "message": message,
        "data": items,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "showing_from": showing_from,
            "showing_to": showing_to,
            "has_more": has_more
        }
    })


def created_response(
    data: Any,
    message: str = "Resource created successfully"
) -> JSONResponse:
    """
    Create a 201 Created response.

    Args:
        data: Created resource data
        message: Success message

    Returns:
        JSONResponse with 201 status code

    Examples:
        >>> created_response({"id": 1, "name": "New Item"})
        JSONResponse({"success": True, "message": "Resource created successfully", "data": {...}}, status_code=201)
    """
    return success_response(data, message, status_code=201)


def no_content_response(message: str = "Operation successful") -> JSONResponse:
    """
    Create a 204 No Content response.

    Args:
        message: Success message

    Returns:
        JSONResponse with 204 status code and minimal content

    Examples:
        >>> no_content_response("Deleted successfully")
        JSONResponse({"success": True, "message": "Deleted successfully"}, status_code=204)
    """
    return JSONResponse(
        content={"success": True, "message": message},
        status_code=204
    )


def not_found_response(message: str = "Resource not found") -> JSONResponse:
    """
    Create a 404 Not Found response.

    Args:
        message: Error message

    Returns:
        JSONResponse with 404 status code

    Examples:
        >>> not_found_response("Entry not found")
        JSONResponse({"success": False, "message": "Entry not found"}, status_code=404)
    """
    return error_response(message, status_code=404)


def validation_error_response(
    message: str = "Validation failed",
    errors: dict | list = None
) -> JSONResponse:
    """
    Create a 422 Validation Error response.

    Args:
        message: Error message
        errors: Validation error details

    Returns:
        JSONResponse with 422 status code

    Examples:
        >>> validation_error_response("Invalid input", {"amount": "Must be positive"})
        JSONResponse({
            "success": False,
            "message": "Invalid input",
            "errors": {"amount": "Must be positive"}
        }, status_code=422)
    """
    return error_response(message, errors, status_code=422)


def unauthorized_response(message: str = "Unauthorized") -> JSONResponse:
    """
    Create a 401 Unauthorized response.

    Args:
        message: Error message

    Returns:
        JSONResponse with 401 status code
    """
    return error_response(message, status_code=401)


def forbidden_response(message: str = "Forbidden") -> JSONResponse:
    """
    Create a 403 Forbidden response.

    Args:
        message: Error message

    Returns:
        JSONResponse with 403 status code
    """
    return error_response(message, status_code=403)

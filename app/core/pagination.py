"""
Pagination utilities for list endpoints.

This module provides utilities for calculating pagination metadata
used in API responses and templates.
"""

from typing import TypedDict


class PaginationInfo(TypedDict):
    """Pagination metadata for list responses."""
    showing_from: int
    showing_to: int
    has_more: bool
    total_count: int
    limit: int
    offset: int


def calculate_pagination_info(
    offset: int,
    limit: int,
    total_count: int
) -> PaginationInfo:
    """
    Calculate pagination information for list endpoints.

    Args:
        offset: Number of items to skip (0-based)
        limit: Maximum number of items per page
        total_count: Total number of items available

    Returns:
        Dictionary with pagination metadata:
        - showing_from: First item number (1-based, 0 if no results)
        - showing_to: Last item number (inclusive)
        - has_more: True if there are more items after current page
        - total_count: Total number of items
        - limit: Items per page
        - offset: Current offset

    Examples:
        >>> calculate_pagination_info(0, 10, 25)
        {
            'showing_from': 1,
            'showing_to': 10,
            'has_more': True,
            'total_count': 25,
            'limit': 10,
            'offset': 0
        }

        >>> calculate_pagination_info(20, 10, 25)
        {
            'showing_from': 21,
            'showing_to': 25,
            'has_more': False,
            'total_count': 25,
            'limit': 10,
            'offset': 20
        }

        >>> calculate_pagination_info(0, 10, 0)
        {
            'showing_from': 0,
            'showing_to': 0,
            'has_more': False,
            'total_count': 0,
            'limit': 10,
            'offset': 0
        }
    """
    showing_from = offset + 1 if total_count > 0 else 0
    showing_to = min(offset + limit, total_count)
    has_more = showing_to < total_count

    return {
        "showing_from": showing_from,
        "showing_to": showing_to,
        "has_more": has_more,
        "total_count": total_count,
        "limit": limit,
        "offset": offset
    }


def get_next_offset(offset: int, limit: int, total_count: int) -> int | None:
    """
    Get offset for the next page.

    Args:
        offset: Current offset
        limit: Items per page
        total_count: Total number of items

    Returns:
        Offset for next page, or None if no more pages

    Examples:
        >>> get_next_offset(0, 10, 25)
        10
        >>> get_next_offset(10, 10, 25)
        20
        >>> get_next_offset(20, 10, 25)
        None
    """
    next_offset = offset + limit
    if next_offset >= total_count:
        return None
    return next_offset


def get_previous_offset(offset: int, limit: int) -> int | None:
    """
    Get offset for the previous page.

    Args:
        offset: Current offset
        limit: Items per page

    Returns:
        Offset for previous page, or None if on first page

    Examples:
        >>> get_previous_offset(0, 10)
        None
        >>> get_previous_offset(10, 10)
        0
        >>> get_previous_offset(25, 10)
        15
    """
    if offset <= 0:
        return None
    previous_offset = offset - limit
    return max(0, previous_offset)


def calculate_total_pages(total_count: int, limit: int) -> int:
    """
    Calculate total number of pages.

    Args:
        total_count: Total number of items
        limit: Items per page

    Returns:
        Total number of pages

    Examples:
        >>> calculate_total_pages(25, 10)
        3
        >>> calculate_total_pages(20, 10)
        2
        >>> calculate_total_pages(0, 10)
        0
    """
    if total_count <= 0 or limit <= 0:
        return 0
    return (total_count + limit - 1) // limit


def calculate_current_page(offset: int, limit: int) -> int:
    """
    Calculate current page number (1-based).

    Args:
        offset: Current offset
        limit: Items per page

    Returns:
        Current page number (1-based)

    Examples:
        >>> calculate_current_page(0, 10)
        1
        >>> calculate_current_page(10, 10)
        2
        >>> calculate_current_page(25, 10)
        3
    """
    if limit <= 0:
        return 1
    return (offset // limit) + 1

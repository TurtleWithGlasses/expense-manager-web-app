"""
Parsing utilities for common data transformations.

This module provides utilities for parsing and validating common data types
used throughout the application, including dates and category IDs.
"""

from datetime import date, datetime
from typing import Optional


def parse_date(date_input: str | date | None) -> Optional[date]:
    """
    Parse date from string or date object.

    Args:
        date_input: Date as ISO string, date object, or None

    Returns:
        Date object or None if input is invalid

    Examples:
        >>> parse_date("2025-01-15")
        date(2025, 1, 15)
        >>> parse_date(date(2025, 1, 15))
        date(2025, 1, 15)
        >>> parse_date(None)
        None
        >>> parse_date("")
        None
        >>> parse_date("invalid")
        None
    """
    if date_input is None or date_input == "":
        return None

    if isinstance(date_input, date):
        return date_input

    if isinstance(date_input, str):
        try:
            return datetime.fromisoformat(date_input).date()
        except (ValueError, AttributeError):
            return None

    return None


def parse_category_id(category: str | int | None) -> Optional[int]:
    """
    Parse category parameter to integer ID.

    Args:
        category: Category ID as string, int, or None

    Returns:
        Integer category ID or None if invalid

    Examples:
        >>> parse_category_id(5)
        5
        >>> parse_category_id("10")
        10
        >>> parse_category_id(None)
        None
        >>> parse_category_id("")
        None
        >>> parse_category_id("   ")
        None
        >>> parse_category_id("abc")
        None
    """
    if category is None:
        return None

    if isinstance(category, int):
        return category

    if isinstance(category, str):
        if not category.strip():
            return None
        try:
            return int(category)
        except ValueError:
            return None

    return None


def parse_int(value: str | int | None, default: Optional[int] = None) -> Optional[int]:
    """
    Parse integer from string or int.

    Args:
        value: Integer as string, int, or None
        default: Default value if parsing fails

    Returns:
        Integer or default value

    Examples:
        >>> parse_int("42")
        42
        >>> parse_int(42)
        42
        >>> parse_int(None)
        None
        >>> parse_int("invalid", 0)
        0
    """
    if value is None:
        return default

    if isinstance(value, int):
        return value

    if isinstance(value, str):
        if not value.strip():
            return default
        try:
            return int(value)
        except ValueError:
            return default

    return default


def parse_float(value: str | float | int | None, default: Optional[float] = None) -> Optional[float]:
    """
    Parse float from string, float, or int.

    Args:
        value: Float as string, float, int, or None
        default: Default value if parsing fails

    Returns:
        Float or default value

    Examples:
        >>> parse_float("3.14")
        3.14
        >>> parse_float(3.14)
        3.14
        >>> parse_float(42)
        42.0
        >>> parse_float(None)
        None
        >>> parse_float("invalid", 0.0)
        0.0
    """
    if value is None:
        return default

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        if not value.strip():
            return default
        try:
            return float(value)
        except ValueError:
            return default

    return default

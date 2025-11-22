"""
Unit tests for parsing utilities.

Tests all parsing functions in app.core.parsers module.
"""
import pytest
from datetime import date

from app.core.parsers import (
    parse_date,
    parse_category_id,
    parse_int,
    parse_float
)


@pytest.mark.unit
class TestParseDate:
    """Tests for parse_date function"""

    def test_parse_date_with_none(self):
        """Test that None returns None"""
        assert parse_date(None) is None

    def test_parse_date_with_empty_string(self):
        """Test that empty string returns None"""
        assert parse_date("") is None

    def test_parse_date_with_date_object(self):
        """Test that date object returns same date"""
        test_date = date(2025, 1, 15)
        assert parse_date(test_date) == test_date

    def test_parse_date_with_iso_string(self):
        """Test parsing ISO date string"""
        result = parse_date("2025-01-15")
        assert result == date(2025, 1, 15)

    def test_parse_date_with_datetime_string(self):
        """Test parsing datetime ISO string"""
        result = parse_date("2025-01-15T10:30:00")
        assert result == date(2025, 1, 15)

    def test_parse_date_with_datetime_string_with_timezone(self):
        """Test parsing datetime string with timezone"""
        result = parse_date("2025-01-15T10:30:00+00:00")
        assert result == date(2025, 1, 15)

    def test_parse_date_with_invalid_string(self):
        """Test that invalid string returns None"""
        assert parse_date("invalid-date") is None

    def test_parse_date_with_malformed_date(self):
        """Test that malformed date returns None"""
        assert parse_date("2025-13-45") is None


@pytest.mark.unit
class TestParseCategoryId:
    """Tests for parse_category_id function"""

    def test_parse_category_id_with_none(self):
        """Test that None returns None"""
        assert parse_category_id(None) is None

    def test_parse_category_id_with_int(self):
        """Test that int returns same int"""
        assert parse_category_id(5) == 5

    def test_parse_category_id_with_zero(self):
        """Test that zero is valid"""
        assert parse_category_id(0) == 0

    def test_parse_category_id_with_valid_string(self):
        """Test parsing valid string to int"""
        assert parse_category_id("10") == 10

    def test_parse_category_id_with_empty_string(self):
        """Test that empty string returns None"""
        assert parse_category_id("") is None

    def test_parse_category_id_with_whitespace(self):
        """Test that whitespace string returns None"""
        assert parse_category_id("   ") is None

    def test_parse_category_id_with_invalid_string(self):
        """Test that invalid string returns None"""
        assert parse_category_id("abc") is None

    def test_parse_category_id_with_float_string(self):
        """Test that float string returns None"""
        assert parse_category_id("3.14") is None


@pytest.mark.unit
class TestParseInt:
    """Tests for parse_int function"""

    def test_parse_int_with_none(self):
        """Test that None returns None"""
        assert parse_int(None) is None

    def test_parse_int_with_none_and_default(self):
        """Test that None with default returns default"""
        assert parse_int(None, 0) == 0

    def test_parse_int_with_int(self):
        """Test that int returns same int"""
        assert parse_int(42) == 42

    def test_parse_int_with_valid_string(self):
        """Test parsing valid string to int"""
        assert parse_int("42") == 42

    def test_parse_int_with_negative_string(self):
        """Test parsing negative string"""
        assert parse_int("-10") == -10

    def test_parse_int_with_empty_string(self):
        """Test that empty string returns None"""
        assert parse_int("") is None

    def test_parse_int_with_empty_string_and_default(self):
        """Test that empty string with default returns default"""
        assert parse_int("", 0) == 0

    def test_parse_int_with_whitespace(self):
        """Test that whitespace returns default"""
        assert parse_int("   ", 0) == 0

    def test_parse_int_with_invalid_string(self):
        """Test that invalid string returns None"""
        assert parse_int("abc") is None

    def test_parse_int_with_invalid_string_and_default(self):
        """Test that invalid string with default returns default"""
        assert parse_int("abc", 10) == 10

    def test_parse_int_with_float_string(self):
        """Test that float string returns None"""
        assert parse_int("3.14") is None


@pytest.mark.unit
class TestParseFloat:
    """Tests for parse_float function"""

    def test_parse_float_with_none(self):
        """Test that None returns None"""
        assert parse_float(None) is None

    def test_parse_float_with_none_and_default(self):
        """Test that None with default returns default"""
        assert parse_float(None, 0.0) == 0.0

    def test_parse_float_with_float(self):
        """Test that float returns same float"""
        assert parse_float(3.14) == 3.14

    def test_parse_float_with_int(self):
        """Test that int converts to float"""
        assert parse_float(42) == 42.0

    def test_parse_float_with_valid_string(self):
        """Test parsing valid float string"""
        assert parse_float("3.14") == 3.14

    def test_parse_float_with_int_string(self):
        """Test parsing int string to float"""
        assert parse_float("42") == 42.0

    def test_parse_float_with_negative_string(self):
        """Test parsing negative float string"""
        assert parse_float("-3.14") == -3.14

    def test_parse_float_with_empty_string(self):
        """Test that empty string returns None"""
        assert parse_float("") is None

    def test_parse_float_with_empty_string_and_default(self):
        """Test that empty string with default returns default"""
        assert parse_float("", 0.0) == 0.0

    def test_parse_float_with_whitespace(self):
        """Test that whitespace returns default"""
        assert parse_float("   ", 0.0) == 0.0

    def test_parse_float_with_invalid_string(self):
        """Test that invalid string returns None"""
        assert parse_float("abc") is None

    def test_parse_float_with_invalid_string_and_default(self):
        """Test that invalid string with default returns default"""
        assert parse_float("abc", 1.0) == 1.0

    def test_parse_float_with_scientific_notation(self):
        """Test parsing scientific notation"""
        assert parse_float("1.5e2") == 150.0

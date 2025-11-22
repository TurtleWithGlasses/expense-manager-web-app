"""
Unit tests for pagination utilities.

Tests all pagination functions in app.core.pagination module.
"""
import pytest

from app.core.pagination import (
    calculate_pagination_info,
    get_next_offset,
    get_previous_offset,
    calculate_total_pages,
    calculate_current_page
)


@pytest.mark.unit
class TestCalculatePaginationInfo:
    """Tests for calculate_pagination_info function"""

    def test_calculate_pagination_info_first_page(self):
        """Test pagination info for first page"""
        result = calculate_pagination_info(offset=0, limit=10, total_count=25)

        assert result["showing_from"] == 1
        assert result["showing_to"] == 10
        assert result["has_more"] is True
        assert result["total_count"] == 25
        assert result["limit"] == 10
        assert result["offset"] == 0

    def test_calculate_pagination_info_middle_page(self):
        """Test pagination info for middle page"""
        result = calculate_pagination_info(offset=10, limit=10, total_count=30)

        assert result["showing_from"] == 11
        assert result["showing_to"] == 20
        assert result["has_more"] is True
        assert result["total_count"] == 30
        assert result["limit"] == 10
        assert result["offset"] == 10

    def test_calculate_pagination_info_last_page(self):
        """Test pagination info for last page"""
        result = calculate_pagination_info(offset=20, limit=10, total_count=25)

        assert result["showing_from"] == 21
        assert result["showing_to"] == 25
        assert result["has_more"] is False
        assert result["total_count"] == 25

    def test_calculate_pagination_info_last_page_exact(self):
        """Test pagination info when last page has exactly limit items"""
        result = calculate_pagination_info(offset=20, limit=10, total_count=30)

        assert result["showing_from"] == 21
        assert result["showing_to"] == 30
        assert result["has_more"] is False

    def test_calculate_pagination_info_no_results(self):
        """Test pagination info with no results"""
        result = calculate_pagination_info(offset=0, limit=10, total_count=0)

        assert result["showing_from"] == 0
        assert result["showing_to"] == 0
        assert result["has_more"] is False
        assert result["total_count"] == 0

    def test_calculate_pagination_info_single_page(self):
        """Test pagination info when all items fit on one page"""
        result = calculate_pagination_info(offset=0, limit=10, total_count=5)

        assert result["showing_from"] == 1
        assert result["showing_to"] == 5
        assert result["has_more"] is False


@pytest.mark.unit
class TestGetNextOffset:
    """Tests for get_next_offset function"""

    def test_get_next_offset_first_page(self):
        """Test getting next offset from first page"""
        assert get_next_offset(0, 10, 25) == 10

    def test_get_next_offset_middle_page(self):
        """Test getting next offset from middle page"""
        assert get_next_offset(10, 10, 30) == 20

    def test_get_next_offset_last_page(self):
        """Test that None is returned when on last page"""
        assert get_next_offset(20, 10, 25) is None

    def test_get_next_offset_exact_last_page(self):
        """Test that None is returned when exactly at end"""
        assert get_next_offset(20, 10, 30) is None

    def test_get_next_offset_no_results(self):
        """Test with no results"""
        assert get_next_offset(0, 10, 0) is None


@pytest.mark.unit
class TestGetPreviousOffset:
    """Tests for get_previous_offset function"""

    def test_get_previous_offset_first_page(self):
        """Test that None is returned when on first page"""
        assert get_previous_offset(0, 10) is None

    def test_get_previous_offset_second_page(self):
        """Test getting previous offset from second page"""
        assert get_previous_offset(10, 10) == 0

    def test_get_previous_offset_third_page(self):
        """Test getting previous offset from third page"""
        assert get_previous_offset(20, 10) == 10

    def test_get_previous_offset_partial_offset(self):
        """Test getting previous offset when offset is not multiple of limit"""
        assert get_previous_offset(25, 10) == 15

    def test_get_previous_offset_small_offset(self):
        """Test getting previous offset when offset is less than limit"""
        assert get_previous_offset(5, 10) == 0


@pytest.mark.unit
class TestCalculateTotalPages:
    """Tests for calculate_total_pages function"""

    def test_calculate_total_pages_exact_division(self):
        """Test when total count divides evenly by limit"""
        assert calculate_total_pages(20, 10) == 2

    def test_calculate_total_pages_with_remainder(self):
        """Test when there's a partial last page"""
        assert calculate_total_pages(25, 10) == 3

    def test_calculate_total_pages_single_page(self):
        """Test when all items fit on one page"""
        assert calculate_total_pages(5, 10) == 1

    def test_calculate_total_pages_no_items(self):
        """Test with no items"""
        assert calculate_total_pages(0, 10) == 0

    def test_calculate_total_pages_negative_limit(self):
        """Test with invalid limit"""
        assert calculate_total_pages(25, -10) == 0

    def test_calculate_total_pages_zero_limit(self):
        """Test with zero limit"""
        assert calculate_total_pages(25, 0) == 0


@pytest.mark.unit
class TestCalculateCurrentPage:
    """Tests for calculate_current_page function"""

    def test_calculate_current_page_first_page(self):
        """Test current page calculation for first page"""
        assert calculate_current_page(0, 10) == 1

    def test_calculate_current_page_second_page(self):
        """Test current page calculation for second page"""
        assert calculate_current_page(10, 10) == 2

    def test_calculate_current_page_third_page(self):
        """Test current page calculation for third page"""
        assert calculate_current_page(20, 10) == 3

    def test_calculate_current_page_with_different_limit(self):
        """Test current page calculation with different limit"""
        assert calculate_current_page(50, 25) == 3

    def test_calculate_current_page_partial_offset(self):
        """Test when offset is not multiple of limit"""
        assert calculate_current_page(15, 10) == 2

    def test_calculate_current_page_zero_limit(self):
        """Test with zero limit (edge case)"""
        assert calculate_current_page(10, 0) == 1

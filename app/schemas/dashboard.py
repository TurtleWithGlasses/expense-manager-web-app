"""
Pydantic schemas for Dashboard data.

Provides response models for dashboard summary and analytics.
"""

from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from datetime import date


class DashboardSummary(BaseModel):
    """Schema for dashboard summary (income, expense, balance)"""

    income: Decimal = Field(..., description="Total income for the period")
    expense: Decimal = Field(..., description="Total expenses for the period")
    balance: Decimal = Field(..., description="Net balance (income - expense)")
    currency_code: str = Field(default="USD", description="Currency code")

    # Formatted versions for display
    income_formatted: str | None = None
    expense_formatted: str | None = None
    balance_formatted: str | None = None

    # Period information
    start_date: date
    end_date: date

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "income": 5000.00,
                "expense": 3500.00,
                "balance": 1500.00,
                "currency_code": "USD",
                "start_date": "2025-01-01",
                "end_date": "2025-01-31"
            }
        }
    )


class DashboardEntryList(BaseModel):
    """Schema for dashboard entry lists (expenses or incomes)"""

    entries: list[dict]  # Simplified entry data
    total_amount: Decimal
    total_count: int
    showing_from: int
    showing_to: int
    has_more: bool
    limit: int
    offset: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "entries": [
                    {
                        "id": 1,
                        "date": "2025-01-15",
                        "category": "Groceries",
                        "amount": 50.00
                    }
                ],
                "total_amount": 1500.00,
                "total_count": 100,
                "showing_from": 1,
                "showing_to": 10,
                "has_more": True,
                "limit": 10,
                "offset": 0
            }
        }
    )

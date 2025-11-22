from datetime import date as date_type
from pydantic import BaseModel, Field, field_validator
from typing import Literal


class EntryCreate(BaseModel):
    """Schema for creating a new entry"""
    type: Literal["income", "expense"] = Field(..., description="Entry type")
    amount: float = Field(..., gt=0, description="Entry amount (must be positive)")
    category_id: int | None = Field(None, description="Category ID (optional)")
    note: str | None = Field(None, max_length=500, description="Entry note (optional)")
    date: date_type = Field(..., description="Entry date")
    currency_code: str | None = Field(None, max_length=3, description="Currency code (optional, defaults to user preference)")

    @field_validator('note')
    @classmethod
    def validate_note(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class EntryUpdate(BaseModel):
    """Schema for updating an existing entry"""
    type: Literal["income", "expense"] | None = Field(None, description="Entry type")
    amount: float | None = Field(None, gt=0, description="Entry amount (must be positive)")
    category_id: int | None = Field(None, description="Category ID")
    note: str | None = Field(None, max_length=500, description="Entry note")
    date: date_type | None = Field(None, description="Entry date")

    @field_validator('note')
    @classmethod
    def validate_note(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class EntryOut(BaseModel):
    """Schema for entry output"""
    id: int
    type: str
    amount: float
    category_id: int | None
    note: str | None
    date: date_type
    currency_code: str
    user_id: int

    model_config = {"from_attributes": True}


class EntryListResponse(BaseModel):
    """Schema for list of entries with pagination"""
    success: bool
    message: str
    data: list[EntryOut]
    pagination: dict
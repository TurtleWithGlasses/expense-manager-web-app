from pydantic import BaseModel, Field, field_validator


class CategoryCreate(BaseModel):
    """Schema for creating a new category"""
    name: str = Field(..., min_length=1, max_length=80, description="Category name")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Category name cannot be empty")
        return v


class CategoryUpdate(BaseModel):
    """Schema for updating a category"""
    name: str = Field(..., min_length=1, max_length=80, description="Category name")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Category name cannot be empty")
        return v


class CategoryOut(BaseModel):
    """Schema for category output"""
    id: int
    name: str
    user_id: int

    model_config = {"from_attributes": True}
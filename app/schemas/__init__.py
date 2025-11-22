"""
Pydantic schemas for request/response validation and serialization.
"""

from app.schemas.entry import EntryCreate, EntryOut
from app.schemas.category import CategoryCreate, CategoryOut

__all__ = [
    "EntryCreate",
    "EntryOut",
    "CategoryCreate",
    "CategoryOut",
]

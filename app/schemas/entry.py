from datetime import date
from pydantic import BaseModel


class EntryCreate(BaseModel):
    type: str # income | expense
    amount: float
    category_id: int | None = None
    note: str | None = None
    date: date


class EntryOut(BaseModel):
    id: int
    type: str
    amount: float
    category_id: int | None
    note: str | None
    date: date


class Config:
    from_attributes = True
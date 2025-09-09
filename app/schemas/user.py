from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_namöe: str | None


class Config:
    from_attributes = True
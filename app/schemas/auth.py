from pydantic import BaseModel, EmailStr


class RegisterIn(BaseModel):
    email: EmailStr
    full_name: str | None = None
    password: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str
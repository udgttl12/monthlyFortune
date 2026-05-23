from pydantic import BaseModel, Field


class AuthRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)


class AuthResponse(BaseModel):
    token: str
    email: str


class AuthUserResponse(BaseModel):
    email: str

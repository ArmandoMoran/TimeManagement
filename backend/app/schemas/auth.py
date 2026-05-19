from __future__ import annotations

# Pydantic resolves field annotations at model_validate time; UUID must be
# importable at runtime.
from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import Role


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=120)
    role: Role = Role.EMPLOYEE


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    name: str
    role: Role
    active: bool
    default_hourly_rate_cents: int | None = None


class TokensResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserResponse

from __future__ import annotations

from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ClientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    email: EmailStr | None = None
    billing_address: str | None = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    notes: str | None = None


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    email: EmailStr | None = None
    billing_address: str | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    notes: str | None = None


class ClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str | None
    billing_address: str | None
    currency: str
    notes: str | None

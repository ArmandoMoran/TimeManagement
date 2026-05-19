from __future__ import annotations

from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    client_id: UUID
    name: str = Field(min_length=1, max_length=160)
    billable: bool = True
    default_rate_cents: int | None = Field(default=None, ge=0)
    rounding_minutes: int = Field(default=6, ge=0, le=60)
    active: bool = True


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    billable: bool | None = None
    default_rate_cents: int | None = Field(default=None, ge=0)
    rounding_minutes: int | None = Field(default=None, ge=0, le=60)
    active: bool | None = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID
    name: str
    billable: bool
    default_rate_cents: int | None
    rounding_minutes: int
    active: bool


class ProjectMemberSet(BaseModel):
    user_id: UUID
    rate_override_cents: int | None = Field(default=None, ge=0)


class ProjectMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_id: UUID
    user_id: UUID
    rate_override_cents: int | None

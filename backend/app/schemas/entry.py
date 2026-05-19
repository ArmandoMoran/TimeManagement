from __future__ import annotations

from datetime import datetime  # noqa: TC003
from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, ConfigDict, Field

# Pydantic resolves field annotations at runtime; keep this import here.
from app.models import EntryStatus  # noqa: TC001


class EntryCreate(BaseModel):
    project_id: UUID
    started_at: datetime
    ended_at: datetime
    description: str = Field(default="", max_length=500)
    notes: str | None = None


class EntryUpdate(BaseModel):
    project_id: UUID | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    description: str | None = Field(default=None, max_length=500)
    notes: str | None = None


class EntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    project_id: UUID
    description: str
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int
    rounded_seconds: int
    status: EntryStatus
    approved_by: UUID | None
    approved_at: datetime | None
    invoice_id: UUID | None
    notes: str | None


class BulkSubmitRequest(BaseModel):
    entry_ids: list[UUID]


class BulkApprovalRequest(BaseModel):
    entry_ids: list[UUID]


class BulkRejectionRequest(BaseModel):
    entry_ids: list[UUID]
    reason: str = Field(min_length=1, max_length=500)


class TimerStartRequest(BaseModel):
    project_id: UUID
    description: str = Field(default="", max_length=500)


class CurrentTimerResponse(BaseModel):
    entry: EntryResponse
    elapsed_seconds: int
    state: str  # running | paused

from __future__ import annotations

from datetime import date  # noqa: TC003
from decimal import Decimal
from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, ConfigDict, Field

# Pydantic resolves field annotations at runtime; keep this import here.
from app.models import InvoiceStatus  # noqa: TC001


class InvoicePreviewRequest(BaseModel):
    client_id: UUID
    start: date
    end: date
    project_ids: list[UUID] | None = None


class InvoiceLineResponse(BaseModel):
    description: str
    hours: float
    unit_price_cents: int
    amount_cents: int


class InvoicePreviewResponse(BaseModel):
    client_id: UUID
    client_name: str
    currency: str
    lines: list[InvoiceLineResponse]
    subtotal_cents: int


class InvoiceCreateRequest(BaseModel):
    client_id: UUID
    start: date
    end: date
    issue_date: date | None = None
    due_in_days: int = Field(default=14, ge=0, le=365)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    notes: str | None = None
    project_ids: list[UUID] | None = None


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID
    invoice_number: str
    issue_date: date
    due_date: date
    status: InvoiceStatus
    subtotal_cents: int
    tax_rate: Decimal
    total_cents: int
    notes: str | None
    pdf_path: str | None

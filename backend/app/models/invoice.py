from __future__ import annotations

from datetime import date, datetime  # noqa: TC003
from decimal import Decimal  # noqa: TC003
from uuid import UUID  # noqa: TC003

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import Base, TimestampMixin, UUIDPrimaryKey
from app.models.client import Client  # noqa: TC001 — used in Mapped[]
from app.models.enums import InvoiceStatus


class Invoice(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "invoices"

    client_id: Mapped[UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    invoice_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(
        SAEnum(
            InvoiceStatus,
            name="invoice_status",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=False,
        default=InvoiceStatus.DRAFT,
    )
    subtotal_cents: Mapped[int] = mapped_column(nullable=False, default=0)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=0)
    total_cents: Mapped[int] = mapped_column(nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    client: Mapped[Client] = relationship()
    lines: Mapped[list[InvoiceLine]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )


class InvoiceLine(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "invoice_lines"

    invoice_id: Mapped[UUID] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    time_entry_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("time_entries.id", ondelete="SET NULL"), nullable=True
    )
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, default=1)
    unit_price_cents: Mapped[int] = mapped_column(nullable=False, default=0)
    amount_cents: Mapped[int] = mapped_column(nullable=False, default=0)

    invoice: Mapped[Invoice] = relationship(back_populates="lines")


class InvoiceCounter(Base):
    """Single-row table used to allocate the next global invoice sequence."""

    __tablename__ = "invoice_counter"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    next_value: Mapped[int] = mapped_column(nullable=False, default=1)

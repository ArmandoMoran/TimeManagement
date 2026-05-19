from __future__ import annotations

from datetime import datetime  # noqa: TC003
from uuid import UUID  # noqa: TC003

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import Base, TimestampMixin, UUIDPrimaryKey
from app.models.enums import EntryStatus, TimerEventType
from app.models.project import Project  # noqa: TC001 — used in Mapped[]


class TimeEntry(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "time_entries"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(nullable=False, default=0)
    rounded_seconds: Mapped[int] = mapped_column(nullable=False, default=0)
    status: Mapped[EntryStatus] = mapped_column(
        SAEnum(
            EntryStatus,
            name="entry_status",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=False,
        default=EntryStatus.DRAFT,
        index=True,
    )
    approved_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Foreign key added in phase 7's invoices migration to avoid a forward reference here.
    invoice_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    events: Mapped[list[TimerEvent]] = relationship(
        back_populates="entry",
        cascade="all, delete-orphan",
        order_by="TimerEvent.occurred_at",
    )
    project: Mapped[Project] = relationship(foreign_keys=[project_id])


class TimerEvent(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "timer_events"

    time_entry_id: Mapped[UUID] = mapped_column(
        ForeignKey("time_entries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[TimerEventType] = mapped_column(
        SAEnum(
            TimerEventType,
            name="timer_event_type",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=False,
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    entry: Mapped[TimeEntry] = relationship(back_populates="events")

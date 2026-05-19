from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING, TypedDict

from app.extensions import db
from app.models import (
    Client,
    EntryStatus,
    Invoice,
    InvoiceStatus,
    Project,
    TimeEntry,
    User,
)

if TYPE_CHECKING:
    from uuid import UUID


class UtilizationRow(TypedDict):
    user_id: str
    user_name: str
    total_seconds: int
    billable_seconds: int
    utilization: float  # 0..1


class RevenueRow(TypedDict):
    client_id: str
    client_name: str
    invoiced_cents: int
    paid_cents: int
    outstanding_cents: int


class OutstandingSummary(TypedDict):
    approved_uninvoiced_count: int
    approved_uninvoiced_seconds: int


def _range_to_utc(start: date, end: date) -> tuple[datetime, datetime]:
    start_dt = datetime.combine(start, datetime.min.time()).replace(tzinfo=UTC)
    end_dt = datetime.combine(end + timedelta(days=1), datetime.min.time()).replace(tzinfo=UTC)
    return start_dt, end_dt


def utilization(*, start: date, end: date, user_id: UUID | None = None) -> list[UtilizationRow]:
    start_dt, end_dt = _range_to_utc(start, end)
    query = (
        db.select(
            TimeEntry.user_id,
            User.name,
            db.func.coalesce(db.func.sum(TimeEntry.duration_seconds), 0),
            db.func.coalesce(
                db.func.sum(
                    db.case(
                        (Project.billable.is_(True), TimeEntry.duration_seconds),
                        else_=0,
                    )
                ),
                0,
            ),
        )
        .join(User, User.id == TimeEntry.user_id)
        .join(Project, Project.id == TimeEntry.project_id)
        .where(TimeEntry.started_at >= start_dt, TimeEntry.started_at < end_dt)
        .group_by(TimeEntry.user_id, User.name)
        .order_by(User.name)
    )
    if user_id is not None:
        query = query.where(TimeEntry.user_id == user_id)

    rows: list[UtilizationRow] = []
    for u_id, name, total, billable in db.session.execute(query).all():
        rate = float(billable) / float(total) if total else 0.0
        rows.append(
            {
                "user_id": str(u_id),
                "user_name": name,
                "total_seconds": int(total),
                "billable_seconds": int(billable),
                "utilization": round(rate, 4),
            }
        )
    return rows


def revenue(*, start: date, end: date, client_id: UUID | None = None) -> list[RevenueRow]:
    start_dt, end_dt = _range_to_utc(start, end)
    query = (
        db.select(
            Invoice.client_id,
            Client.name,
            db.func.coalesce(db.func.sum(Invoice.total_cents), 0),
            db.func.coalesce(
                db.func.sum(
                    db.case(
                        (Invoice.status == InvoiceStatus.PAID, Invoice.total_cents),
                        else_=0,
                    )
                ),
                0,
            ),
        )
        .join(Client, Client.id == Invoice.client_id)
        .where(
            Invoice.issue_date >= start_dt.date(),
            Invoice.issue_date < end_dt.date(),
            Invoice.status != InvoiceStatus.VOID,
        )
        .group_by(Invoice.client_id, Client.name)
        .order_by(Client.name)
    )
    if client_id is not None:
        query = query.where(Invoice.client_id == client_id)

    rows: list[RevenueRow] = []
    for c_id, name, invoiced, paid in db.session.execute(query).all():
        rows.append(
            {
                "client_id": str(c_id),
                "client_name": name,
                "invoiced_cents": int(invoiced),
                "paid_cents": int(paid),
                "outstanding_cents": int(invoiced) - int(paid),
            }
        )
    return rows


def outstanding() -> OutstandingSummary:
    row = db.session.execute(
        db.select(
            db.func.count(TimeEntry.id),
            db.func.coalesce(db.func.sum(TimeEntry.duration_seconds), 0),
        ).where(
            TimeEntry.status == EntryStatus.APPROVED,
            TimeEntry.invoice_id.is_(None),
        )
    ).one()
    return {
        "approved_uninvoiced_count": int(row[0]),
        "approved_uninvoiced_seconds": int(row[1]),
    }

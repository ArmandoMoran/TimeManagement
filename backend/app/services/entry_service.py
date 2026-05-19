from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.extensions import db
from app.models import EntryStatus, Project, Role, TimeEntry, User
from app.services.timer_service import round_seconds_up

if TYPE_CHECKING:
    from collections.abc import Sequence
    from uuid import UUID


_EDITABLE_FIELDS = {"description", "started_at", "ended_at", "notes", "project_id"}


def list_entries(
    *,
    actor: User,
    user_id: UUID | None = None,
    project_id: UUID | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    status: EntryStatus | None = None,
) -> list[TimeEntry]:
    query = db.select(TimeEntry).order_by(TimeEntry.started_at.desc())

    # Employees only see their own entries; managers/admins can filter by user_id.
    if actor.role is Role.EMPLOYEE:
        query = query.where(TimeEntry.user_id == actor.id)
    elif user_id is not None:
        query = query.where(TimeEntry.user_id == user_id)

    if project_id is not None:
        query = query.where(TimeEntry.project_id == project_id)
    if status is not None:
        query = query.where(TimeEntry.status == status)
    if start is not None:
        query = query.where(TimeEntry.started_at >= start)
    if end is not None:
        query = query.where(TimeEntry.started_at < end)

    return list(db.session.execute(query).scalars())


def get_entry(entry_id: UUID) -> TimeEntry:
    entry: TimeEntry | None = db.session.get(TimeEntry, entry_id)
    if entry is None:
        raise NotFoundError("entry not found")
    return entry


def _is_actor_authorized(entry: TimeEntry, actor: User) -> bool:
    if actor.role is Role.ADMIN:
        return True
    return entry.user_id == actor.id


def create_manual_entry(
    *,
    actor: User,
    project_id: UUID,
    started_at: datetime,
    ended_at: datetime,
    description: str = "",
    notes: str | None = None,
) -> TimeEntry:
    if ended_at <= started_at:
        raise ValidationError("ended_at must be after started_at")

    project: Project | None = db.session.get(Project, project_id)
    if project is None:
        raise ValidationError("project_id does not refer to an existing project")

    duration = int((ended_at - started_at).total_seconds())
    entry = TimeEntry(
        user_id=actor.id,
        project_id=project_id,
        description=description,
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=duration,
        rounded_seconds=round_seconds_up(duration, project.rounding_minutes),
        status=EntryStatus.DRAFT,
        notes=notes,
    )
    db.session.add(entry)
    db.session.flush()
    return entry


def update_entry(*, actor: User, entry_id: UUID, **fields: object) -> TimeEntry:
    entry = get_entry(entry_id)
    if not _is_actor_authorized(entry, actor):
        raise ForbiddenError("cannot edit another user's entry")

    if (
        entry.status not in {EntryStatus.DRAFT, EntryStatus.SUBMITTED}
        and actor.role is not Role.ADMIN
    ):
        raise ConflictError("only draft or submitted entries can be edited")

    for key, value in fields.items():
        if key not in _EDITABLE_FIELDS or value is None:
            continue
        setattr(entry, key, value)

    if entry.ended_at is not None and entry.started_at is not None:
        if entry.ended_at <= entry.started_at:
            raise ValidationError("ended_at must be after started_at")
        entry.duration_seconds = int((entry.ended_at - entry.started_at).total_seconds())
        if entry.project is not None:
            entry.rounded_seconds = round_seconds_up(
                entry.duration_seconds, entry.project.rounding_minutes
            )

    db.session.flush()
    return entry


def delete_entry(*, actor: User, entry_id: UUID) -> None:
    entry = get_entry(entry_id)
    if not _is_actor_authorized(entry, actor):
        raise ForbiddenError("cannot delete another user's entry")
    if entry.status is EntryStatus.INVOICED:
        raise ConflictError("invoiced entries cannot be deleted")
    db.session.delete(entry)
    db.session.flush()


def submit_entries(*, actor: User, entry_ids: Sequence[UUID]) -> list[TimeEntry]:
    if not entry_ids:
        return []
    entries = list(
        db.session.execute(db.select(TimeEntry).where(TimeEntry.id.in_(entry_ids))).scalars()
    )
    submitted: list[TimeEntry] = []
    for entry in entries:
        if entry.user_id != actor.id:
            raise ForbiddenError("cannot submit another user's entry")
        if entry.status is not EntryStatus.DRAFT:
            raise ConflictError(f"entry {entry.id} is not in draft status")
        if entry.ended_at is None:
            raise ValidationError(f"entry {entry.id} has no end time; stop the timer first")
        entry.status = EntryStatus.SUBMITTED
        submitted.append(entry)
    db.session.flush()
    return submitted


def approve_entries(*, actor: User, entry_ids: Sequence[UUID]) -> list[TimeEntry]:
    if actor.role not in {Role.MANAGER, Role.ADMIN}:
        raise ForbiddenError("only managers or admins can approve entries")
    if not entry_ids:
        return []

    entries = list(
        db.session.execute(db.select(TimeEntry).where(TimeEntry.id.in_(entry_ids))).scalars()
    )
    approved: list[TimeEntry] = []
    for entry in entries:
        if entry.status is not EntryStatus.SUBMITTED:
            raise ConflictError(f"entry {entry.id} is not submitted")
        entry.status = EntryStatus.APPROVED
        entry.approved_by = actor.id
        entry.approved_at = datetime.now(UTC)
        approved.append(entry)
    db.session.flush()
    return approved


def reject_entries(*, actor: User, entry_ids: Sequence[UUID], reason: str) -> list[TimeEntry]:
    if actor.role not in {Role.MANAGER, Role.ADMIN}:
        raise ForbiddenError("only managers or admins can reject entries")
    if not entry_ids:
        return []

    entries = list(
        db.session.execute(db.select(TimeEntry).where(TimeEntry.id.in_(entry_ids))).scalars()
    )
    rejected: list[TimeEntry] = []
    note_prefix = f"[Rejected by {actor.name}]: {reason}\n"
    for entry in entries:
        if entry.status is not EntryStatus.SUBMITTED:
            raise ConflictError(f"entry {entry.id} is not submitted")
        entry.status = EntryStatus.DRAFT
        entry.notes = note_prefix + (entry.notes or "")
        rejected.append(entry)
    db.session.flush()
    return rejected

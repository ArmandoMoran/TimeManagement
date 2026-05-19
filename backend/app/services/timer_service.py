from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Literal

from app.errors import ConflictError, NotFoundError, ValidationError
from app.extensions import db
from app.models import (
    EntryStatus,
    Project,
    TimeEntry,
    TimerEvent,
    TimerEventType,
    User,
)

if TYPE_CHECKING:
    from collections.abc import Sequence
    from uuid import UUID


TimerState = Literal["running", "paused", "stopped"]


def _now() -> datetime:
    return datetime.now(UTC)


def compute_elapsed_seconds(events: Sequence[TimerEvent], *, as_of: datetime | None = None) -> int:
    """Sum the active spans across the event log.

    If the last event is start/resume (no closing pause/stop), the span runs to
    ``as_of`` (defaults to now). The result is in whole seconds, truncated.
    """
    cursor = as_of or _now()
    total = timedelta()
    active_since: datetime | None = None
    for event in events:
        if event.event_type in (TimerEventType.START, TimerEventType.RESUME):
            active_since = event.occurred_at
        elif (
            event.event_type in (TimerEventType.PAUSE, TimerEventType.STOP)
            and active_since is not None
        ):
            total += event.occurred_at - active_since
            active_since = None
    if active_since is not None:
        total += cursor - active_since
    return max(0, int(total.total_seconds()))


def round_seconds_up(seconds: int, rounding_minutes: int) -> int:
    """Round ``seconds`` up to the next multiple of ``rounding_minutes`` minutes."""
    if rounding_minutes <= 0:
        return seconds
    unit = rounding_minutes * 60
    return math.ceil(seconds / unit) * unit


def state_of(entry: TimeEntry) -> TimerState:
    if entry.ended_at is not None:
        return "stopped"
    last = entry.events[-1] if entry.events else None
    if last is None:
        return "stopped"
    if last.event_type in (TimerEventType.START, TimerEventType.RESUME):
        return "running"
    if last.event_type is TimerEventType.PAUSE:
        return "paused"
    return "stopped"


def get_running_entry(user: User) -> TimeEntry | None:
    """A user's currently open entry, if any (running or paused — not yet stopped)."""
    return db.session.execute(
        db.select(TimeEntry)
        .where(TimeEntry.user_id == user.id, TimeEntry.ended_at.is_(None))
        .order_by(TimeEntry.started_at.desc())
    ).scalar_one_or_none()


def start_timer(*, user: User, project_id: UUID, description: str = "") -> TimeEntry:
    if get_running_entry(user) is not None:
        raise ConflictError("another timer is already running — stop it first")

    project: Project | None = db.session.get(Project, project_id)
    if project is None:
        raise ValidationError("project_id does not refer to an existing project")
    if not project.active:
        raise ValidationError("project is archived; cannot start timer")

    now = _now()
    entry = TimeEntry(
        user_id=user.id,
        project_id=project_id,
        description=description,
        started_at=now,
        status=EntryStatus.DRAFT,
    )
    db.session.add(entry)
    db.session.flush()
    db.session.add(
        TimerEvent(
            time_entry_id=entry.id,
            event_type=TimerEventType.START,
            occurred_at=now,
        )
    )
    db.session.flush()
    db.session.refresh(entry)
    return entry


def pause_timer(user: User) -> TimeEntry:
    entry = get_running_entry(user)
    if entry is None:
        raise NotFoundError("no running timer")
    if state_of(entry) != "running":
        raise ConflictError("timer is not currently running")
    db.session.add(
        TimerEvent(
            time_entry_id=entry.id,
            event_type=TimerEventType.PAUSE,
            occurred_at=_now(),
        )
    )
    db.session.flush()
    db.session.refresh(entry)
    return entry


def resume_timer(user: User) -> TimeEntry:
    entry = get_running_entry(user)
    if entry is None:
        raise NotFoundError("no paused timer")
    if state_of(entry) != "paused":
        raise ConflictError("timer is not paused")
    db.session.add(
        TimerEvent(
            time_entry_id=entry.id,
            event_type=TimerEventType.RESUME,
            occurred_at=_now(),
        )
    )
    db.session.flush()
    db.session.refresh(entry)
    return entry


def stop_timer(user: User) -> TimeEntry:
    entry = get_running_entry(user)
    if entry is None:
        raise NotFoundError("no active timer")

    now = _now()
    db.session.add(
        TimerEvent(
            time_entry_id=entry.id,
            event_type=TimerEventType.STOP,
            occurred_at=now,
        )
    )
    db.session.flush()
    db.session.refresh(entry)

    raw = compute_elapsed_seconds(entry.events, as_of=now)
    rounding = entry.project.rounding_minutes if entry.project else 0
    rounded = round_seconds_up(raw, rounding)

    entry.ended_at = now
    entry.duration_seconds = raw
    entry.rounded_seconds = rounded
    db.session.flush()
    return entry

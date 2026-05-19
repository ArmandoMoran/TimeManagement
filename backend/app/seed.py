"""Seed demo data for TimeTrack.

Run with::

    just seed       # uses default DATABASE_URL
    uv run python -m app.seed

Idempotent: aborts if any users already exist so it never clobbers a real DB.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app import create_app
from app.extensions import db
from app.models import (
    Client,
    EntryStatus,
    Project,
    ProjectMember,
    Role,
    TimeEntry,
    User,
)
from app.services import auth_service, invoice_service


def _build_user(*, email: str, name: str, role: Role, rate_cents: int) -> User:
    user = auth_service.register_user(email=email, password="demo-password", name=name, role=role)
    user.default_hourly_rate_cents = rate_cents
    return user


def seed() -> None:
    if db.session.execute(db.select(User).limit(1)).first() is not None:
        print("Database already has users — refusing to seed over existing data.")
        return

    admin = _build_user(
        email="admin@timetrack.dev", name="Avery Admin", role=Role.ADMIN, rate_cents=20000
    )
    manager = _build_user(
        email="manager@timetrack.dev", name="Morgan Manager", role=Role.MANAGER, rate_cents=18000
    )
    emp_a = _build_user(
        email="dev1@timetrack.dev", name="Devon Dev", role=Role.EMPLOYEE, rate_cents=15000
    )
    emp_b = _build_user(
        email="dev2@timetrack.dev", name="Jamie Junior", role=Role.EMPLOYEE, rate_cents=10000
    )

    acme = Client(name="Acme Robotics", email="ar@acme.example.com", currency="USD")
    initech = Client(name="Initech", email="ap@initech.example.com", currency="USD")
    db.session.add_all([acme, initech])
    db.session.flush()

    acme_site = Project(client_id=acme.id, name="Acme Site Refresh", default_rate_cents=18000)
    acme_api = Project(client_id=acme.id, name="Acme API", default_rate_cents=22000)
    initech_audit = Project(client_id=initech.id, name="Initech Audit", default_rate_cents=15000)
    db.session.add_all([acme_site, acme_api, initech_audit])
    db.session.flush()

    db.session.add_all(
        [
            ProjectMember(project_id=acme_site.id, user_id=emp_a.id, rate_override_cents=20000),
            ProjectMember(project_id=acme_api.id, user_id=emp_b.id, rate_override_cents=None),
            ProjectMember(project_id=initech_audit.id, user_id=emp_a.id, rate_override_cents=None),
        ]
    )
    db.session.flush()

    today = datetime.now(UTC).replace(hour=14, minute=0, second=0, microsecond=0)

    def add_entry(
        user: User,
        project: Project,
        days_ago: int,
        hours: float,
        description: str,
        status: EntryStatus = EntryStatus.APPROVED,
    ) -> TimeEntry:
        started = today - timedelta(days=days_ago)
        ended = started + timedelta(hours=hours)
        duration = int((ended - started).total_seconds())
        entry = TimeEntry(
            user_id=user.id,
            project_id=project.id,
            description=description,
            started_at=started,
            ended_at=ended,
            duration_seconds=duration,
            rounded_seconds=duration,
            status=status,
        )
        if status is EntryStatus.APPROVED:
            entry.approved_by = manager.id
            entry.approved_at = today
        db.session.add(entry)
        return entry

    entries = [
        add_entry(emp_a, acme_site, 5, 4.0, "Discovery + wireframes"),
        add_entry(emp_a, acme_site, 4, 6.0, "Homepage build"),
        add_entry(emp_b, acme_api, 4, 3.0, "Auth endpoints"),
        add_entry(emp_a, acme_site, 3, 5.0, "Component library"),
        add_entry(emp_b, acme_api, 3, 4.0, "User CRUD"),
        add_entry(emp_a, initech_audit, 2, 2.5, "Initial walkthrough"),
        add_entry(emp_b, acme_api, 2, 3.5, "Rate limiting"),
        add_entry(emp_a, initech_audit, 1, 4.0, "Findings doc"),
        add_entry(emp_b, acme_api, 1, 2.0, "Bug fixes", status=EntryStatus.SUBMITTED),
        add_entry(emp_a, acme_site, 0, 3.5, "Today's work", status=EntryStatus.DRAFT),
    ]
    db.session.flush()
    print(f"Seeded {len(entries)} time entries")

    # One draft invoice for Acme covering approved entries from the past week.
    week_start = (today - timedelta(days=7)).date()
    week_end = today.date()
    invoice = invoice_service.create_invoice(client_id=acme.id, start=week_start, end=week_end)
    invoice_service.render_pdf(invoice)
    print(f"Created draft invoice {invoice.invoice_number}")

    db.session.commit()

    print("\nDemo accounts (password 'demo-password'):")
    for user in (admin, manager, emp_a, emp_b):
        print(f"  {user.role.value:8}  {user.email}")


def main() -> None:
    app = create_app()
    with app.app_context():
        seed()


if __name__ == "__main__":
    main()

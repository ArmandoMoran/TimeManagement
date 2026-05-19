from __future__ import annotations

from typing import TYPE_CHECKING

from app.errors import NotFoundError, ValidationError
from app.extensions import db
from app.models import Client, Project, ProjectMember, User

if TYPE_CHECKING:
    from uuid import UUID


def list_projects(client_id: UUID | None = None) -> list[Project]:
    query = db.select(Project).order_by(Project.name)
    if client_id is not None:
        query = query.where(Project.client_id == client_id)
    return list(db.session.execute(query).scalars())


def get_project(project_id: UUID) -> Project:
    project: Project | None = db.session.get(Project, project_id)
    if project is None:
        raise NotFoundError("project not found")
    return project


def create_project(*, client_id: UUID, **fields: object) -> Project:
    if db.session.get(Client, client_id) is None:
        raise ValidationError("client_id does not refer to an existing client")
    project = Project(client_id=client_id, **fields)
    db.session.add(project)
    db.session.flush()
    return project


def update_project(project_id: UUID, **fields: object) -> Project:
    project = get_project(project_id)
    for key, value in fields.items():
        if value is not None:
            setattr(project, key, value)
    db.session.flush()
    return project


def delete_project(project_id: UUID) -> None:
    project = get_project(project_id)
    db.session.delete(project)
    db.session.flush()


def list_members(project_id: UUID) -> list[ProjectMember]:
    get_project(project_id)
    return list(
        db.session.execute(
            db.select(ProjectMember).where(ProjectMember.project_id == project_id)
        ).scalars()
    )


def set_member(
    project_id: UUID, *, user_id: UUID, rate_override_cents: int | None
) -> ProjectMember:
    """Idempotent upsert. Adding the same user twice updates the rate override."""
    get_project(project_id)
    if db.session.get(User, user_id) is None:
        raise ValidationError("user_id does not refer to an existing user")

    member: ProjectMember | None = db.session.get(ProjectMember, (project_id, user_id))
    if member is None:
        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            rate_override_cents=rate_override_cents,
        )
        db.session.add(member)
    else:
        member.rate_override_cents = rate_override_cents
    db.session.flush()
    return member


def remove_member(project_id: UUID, user_id: UUID) -> None:
    member = db.session.get(ProjectMember, (project_id, user_id))
    if member is None:
        raise NotFoundError("project member not found")
    db.session.delete(member)
    db.session.flush()

from __future__ import annotations

from uuid import UUID  # noqa: TC003 — used at runtime by SQLAlchemy

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import Base, TimestampMixin, UUIDPrimaryKey


class Project(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "projects"

    client_id: Mapped[UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    billable: Mapped[bool] = mapped_column(nullable=False, default=True)
    default_rate_cents: Mapped[int | None] = mapped_column(nullable=True)
    rounding_minutes: Mapped[int] = mapped_column(nullable=False, default=6)
    active: Mapped[bool] = mapped_column(nullable=False, default=True)

    members: Mapped[list[ProjectMember]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project {self.name}>"


class ProjectMember(TimestampMixin, Base):
    __tablename__ = "project_members"

    # Composite primary key on (project_id, user_id) enforces uniqueness;
    # no separate UniqueConstraint needed.
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    rate_override_cents: Mapped[int | None] = mapped_column(nullable=True)

    project: Mapped[Project] = relationship(back_populates="members")

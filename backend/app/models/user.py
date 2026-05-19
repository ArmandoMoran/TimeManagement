from __future__ import annotations

from sqlalchemy import Enum as SAEnum
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import Base, TimestampMixin, UUIDPrimaryKey
from app.models.enums import Role


class User(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[Role] = mapped_column(
        SAEnum(Role, name="user_role", values_callable=lambda enum: [e.value for e in enum]),
        nullable=False,
        default=Role.EMPLOYEE,
    )
    default_hourly_rate_cents: Mapped[int | None] = mapped_column(nullable=True)
    active: Mapped[bool] = mapped_column(default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<User {self.email} role={self.role}>"

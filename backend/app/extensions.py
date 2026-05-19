from __future__ import annotations

# datetime and UUID are imported at runtime because SQLAlchemy 2.0 uses
# ``get_type_hints`` to resolve ``Mapped[...]`` annotations, which evaluates them.
from datetime import datetime  # noqa: TC003
from uuid import UUID, uuid4

from argon2 import PasswordHasher
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Project-wide declarative base. SQLAlchemy 2.0 typed (``Mapped[...]``)."""


class TimestampMixin:
    """``created_at`` / ``updated_at`` with timezone-aware UTC defaults."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDPrimaryKey:
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)


db = SQLAlchemy(model_class=Base)
migrate = Migrate()
jwt = JWTManager()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",
)
password_hasher = PasswordHasher()

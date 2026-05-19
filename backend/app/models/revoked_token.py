from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import Base, TimestampMixin, UUIDPrimaryKey


class RevokedToken(UUIDPrimaryKey, TimestampMixin, Base):
    """Tracks JWT IDs that have been explicitly revoked (logout, refresh rotation).

    The JWT-Extended ``token_in_blocklist_loader`` checks against this table on
    every authenticated request.
    """

    __tablename__ = "revoked_tokens"

    jti: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import Base, TimestampMixin, UUIDPrimaryKey


class Client(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "clients"

    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    billing_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Client {self.name}>"

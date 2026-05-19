from __future__ import annotations

from typing import TYPE_CHECKING

from app.errors import NotFoundError
from app.extensions import db
from app.models import Client

if TYPE_CHECKING:
    from uuid import UUID


def list_clients() -> list[Client]:
    return list(db.session.execute(db.select(Client).order_by(Client.name)).scalars())


def get_client(client_id: UUID) -> Client:
    client: Client | None = db.session.get(Client, client_id)
    if client is None:
        raise NotFoundError("client not found")
    return client


def create_client(**fields: object) -> Client:
    client = Client(**fields)
    db.session.add(client)
    db.session.flush()
    return client


def update_client(client_id: UUID, **fields: object) -> Client:
    client = get_client(client_id)
    for key, value in fields.items():
        if value is not None:
            setattr(client, key, value)
    db.session.flush()
    return client


def delete_client(client_id: UUID) -> None:
    client = get_client(client_id)
    db.session.delete(client)
    db.session.flush()

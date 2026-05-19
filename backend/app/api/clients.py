from __future__ import annotations

from typing import TYPE_CHECKING

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.api._helpers import parse_json
from app.auth.decorators import require_role
from app.extensions import db
from app.models import Role
from app.schemas.client import ClientCreate, ClientResponse, ClientUpdate
from app.services import client_service

if TYPE_CHECKING:
    from uuid import UUID

    from flask.wrappers import Response

bp = Blueprint("clients", __name__)


def _serialize(client: object) -> dict[str, object]:
    return ClientResponse.model_validate(client).model_dump(mode="json")


@bp.get("")
@jwt_required()
def list_clients() -> Response:
    clients = client_service.list_clients()
    return jsonify({"clients": [_serialize(c) for c in clients]})


@bp.get("/<uuid:client_id>")
@jwt_required()
def get_client(client_id: UUID) -> Response:
    client = client_service.get_client(client_id)
    return jsonify(_serialize(client))


@bp.post("")
@jwt_required()
@require_role(Role.ADMIN)
def create_client() -> tuple[Response, int]:
    payload = parse_json(ClientCreate, request.get_json(silent=True) or {})
    client = client_service.create_client(**payload.model_dump())
    db.session.commit()
    return jsonify(_serialize(client)), 201


@bp.patch("/<uuid:client_id>")
@jwt_required()
@require_role(Role.ADMIN)
def update_client(client_id: UUID) -> Response:
    payload = parse_json(ClientUpdate, request.get_json(silent=True) or {})
    client = client_service.update_client(client_id, **payload.model_dump(exclude_unset=True))
    db.session.commit()
    return jsonify(_serialize(client))


@bp.delete("/<uuid:client_id>")
@jwt_required()
@require_role(Role.ADMIN)
def delete_client(client_id: UUID) -> tuple[Response, int]:
    client_service.delete_client(client_id)
    db.session.commit()
    return jsonify({"deleted": True}), 200

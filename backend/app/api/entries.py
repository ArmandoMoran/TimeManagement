from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from flask import Blueprint, jsonify, request
from flask_jwt_extended import current_user, jwt_required

from app.api._helpers import parse_json
from app.errors import AuthenticationError
from app.extensions import db
from app.models import EntryStatus, User
from app.schemas.entry import (
    BulkSubmitRequest,
    EntryCreate,
    EntryResponse,
    EntryUpdate,
)
from app.services import entry_service

if TYPE_CHECKING:
    from flask.wrappers import Response

bp = Blueprint("entries", __name__)


def _require_user() -> User:
    user: User | None = current_user
    if user is None:
        raise AuthenticationError("session not found")
    return user


def _serialize(entry: object) -> dict[str, object]:
    return EntryResponse.model_validate(entry).model_dump(mode="json")


def _parse_iso(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


@bp.get("")
@jwt_required()
def list_entries() -> Response:
    actor = _require_user()
    raw_user = request.args.get("user_id")
    raw_project = request.args.get("project_id")
    raw_status = request.args.get("status")

    entries = entry_service.list_entries(
        actor=actor,
        user_id=UUID(raw_user) if raw_user else None,
        project_id=UUID(raw_project) if raw_project else None,
        start=_parse_iso(request.args.get("start")),
        end=_parse_iso(request.args.get("end")),
        status=EntryStatus(raw_status) if raw_status else None,
    )
    return jsonify({"entries": [_serialize(e) for e in entries]})


@bp.post("")
@jwt_required()
def create_entry() -> tuple[Response, int]:
    actor = _require_user()
    payload = parse_json(EntryCreate, request.get_json(silent=True) or {})
    entry = entry_service.create_manual_entry(
        actor=actor,
        project_id=payload.project_id,
        started_at=payload.started_at,
        ended_at=payload.ended_at,
        description=payload.description,
        notes=payload.notes,
    )
    db.session.commit()
    return jsonify(_serialize(entry)), 201


@bp.patch("/<uuid:entry_id>")
@jwt_required()
def update_entry(entry_id: UUID) -> Response:
    actor = _require_user()
    payload = parse_json(EntryUpdate, request.get_json(silent=True) or {})
    entry = entry_service.update_entry(
        actor=actor, entry_id=entry_id, **payload.model_dump(exclude_unset=True)
    )
    db.session.commit()
    return jsonify(_serialize(entry))


@bp.delete("/<uuid:entry_id>")
@jwt_required()
def delete_entry(entry_id: UUID) -> tuple[Response, int]:
    actor = _require_user()
    entry_service.delete_entry(actor=actor, entry_id=entry_id)
    db.session.commit()
    return jsonify({"deleted": True}), 200


@bp.post("/<uuid:entry_id>/submit")
@jwt_required()
def submit_entry(entry_id: UUID) -> Response:
    actor = _require_user()
    [entry] = entry_service.submit_entries(actor=actor, entry_ids=[entry_id])
    db.session.commit()
    return jsonify(_serialize(entry))


@bp.post("/bulk-submit")
@jwt_required()
def bulk_submit() -> Response:
    actor = _require_user()
    payload = parse_json(BulkSubmitRequest, request.get_json(silent=True) or {})
    entries = entry_service.submit_entries(actor=actor, entry_ids=payload.entry_ids)
    db.session.commit()
    return jsonify({"entries": [_serialize(e) for e in entries]})

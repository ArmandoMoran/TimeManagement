from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from flask import Blueprint, jsonify, request
from flask_jwt_extended import current_user, jwt_required

from app.api._helpers import parse_json
from app.auth.decorators import require_role
from app.errors import AuthenticationError
from app.extensions import db
from app.models import EntryStatus, Role, User
from app.schemas.entry import (
    BulkApprovalRequest,
    BulkRejectionRequest,
    EntryResponse,
)
from app.services import entry_service

if TYPE_CHECKING:
    from flask.wrappers import Response

bp = Blueprint("approvals", __name__)


def _require_user() -> User:
    user: User | None = current_user
    if user is None:
        raise AuthenticationError("session not found")
    return user


def _serialize(entry: object) -> dict[str, object]:
    return EntryResponse.model_validate(entry).model_dump(mode="json")


@bp.get("")
@jwt_required()
@require_role(Role.MANAGER, Role.ADMIN)
def list_pending() -> Response:
    actor = _require_user()
    raw_user = request.args.get("user_id")
    raw_start = request.args.get("start")
    raw_end = request.args.get("end")
    entries = entry_service.list_entries(
        actor=actor,
        status=EntryStatus.SUBMITTED,
        user_id=UUID(raw_user) if raw_user else None,
        start=datetime.fromisoformat(raw_start) if raw_start else None,
        end=datetime.fromisoformat(raw_end) if raw_end else None,
    )
    return jsonify({"entries": [_serialize(e) for e in entries]})


@bp.post("/approve")
@jwt_required()
@require_role(Role.MANAGER, Role.ADMIN)
def approve() -> Response:
    actor = _require_user()
    payload = parse_json(BulkApprovalRequest, request.get_json(silent=True) or {})
    approved = entry_service.approve_entries(actor=actor, entry_ids=payload.entry_ids)
    db.session.commit()
    return jsonify({"entries": [_serialize(e) for e in approved]})


@bp.post("/reject")
@jwt_required()
@require_role(Role.MANAGER, Role.ADMIN)
def reject() -> Response:
    actor = _require_user()
    payload = parse_json(BulkRejectionRequest, request.get_json(silent=True) or {})
    rejected = entry_service.reject_entries(
        actor=actor, entry_ids=payload.entry_ids, reason=payload.reason
    )
    db.session.commit()
    return jsonify({"entries": [_serialize(e) for e in rejected]})

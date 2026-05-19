from __future__ import annotations

from typing import TYPE_CHECKING, Any

from flask import Blueprint, current_app, jsonify, request
from werkzeug.exceptions import NotFound

from app.extensions import db
from app.models import Role
from app.services import auth_service

if TYPE_CHECKING:
    from flask.wrappers import Response

bp = Blueprint("test_helpers", __name__)


@bp.before_request
def _gate() -> None:
    if not current_app.config.get("TESTING", False):
        # Should be unreachable — blueprint isn't registered outside TESTING.
        raise NotFound


@bp.post("/reset")
def reset() -> Response:
    """Truncate every table. Use between e2e tests for a clean slate."""
    for table in reversed(db.metadata.sorted_tables):
        db.session.execute(table.delete())
    db.session.commit()
    return jsonify({"reset": True})


@bp.post("/seed")
def seed() -> tuple[Response, int]:
    """Seed a minimal scenario from a JSON payload."""
    payload = request.get_json(silent=True) or {}
    users_payload = payload.get("users", [])
    if not isinstance(users_payload, list):
        return jsonify({"error": "users must be a list"}), 422

    created: list[dict[str, Any]] = []
    for entry in users_payload:
        role = Role(entry.get("role", "employee"))
        user = auth_service.register_user(
            email=entry["email"],
            password=entry["password"],
            name=entry["name"],
            role=role,
        )
        created.append(
            {
                "id": str(user.id),
                "email": user.email,
                "role": user.role.value,
            }
        )
    db.session.commit()
    return jsonify({"users": created}), 201

from __future__ import annotations

from typing import TYPE_CHECKING

from flask import Blueprint, jsonify, request
from flask_jwt_extended import current_user, jwt_required

from app.api._helpers import parse_json
from app.errors import AuthenticationError, NotFoundError
from app.extensions import db
from app.schemas.entry import (
    CurrentTimerResponse,
    EntryResponse,
    TimerStartRequest,
)
from app.services import timer_service

if TYPE_CHECKING:
    from flask.wrappers import Response

    from app.models import User

bp = Blueprint("timer", __name__)


def _require_user() -> User:
    user: User | None = current_user
    if user is None:
        raise AuthenticationError("session not found")
    return user


def _serialize(entry: object) -> dict[str, object]:
    return EntryResponse.model_validate(entry).model_dump(mode="json")


@bp.get("/current")
@jwt_required()
def current() -> Response:
    actor = _require_user()
    entry = timer_service.get_running_entry(actor)
    if entry is None:
        return jsonify(None)
    elapsed = timer_service.compute_elapsed_seconds(entry.events)
    state = timer_service.state_of(entry)
    payload = CurrentTimerResponse(
        entry=EntryResponse.model_validate(entry),
        elapsed_seconds=elapsed,
        state=state,
    )
    return jsonify(payload.model_dump(mode="json"))


@bp.post("/start")
@jwt_required()
def start() -> tuple[Response, int]:
    actor = _require_user()
    payload = parse_json(TimerStartRequest, request.get_json(silent=True) or {})
    entry = timer_service.start_timer(
        user=actor, project_id=payload.project_id, description=payload.description
    )
    db.session.commit()
    return jsonify(_serialize(entry)), 201


@bp.post("/pause")
@jwt_required()
def pause() -> Response:
    actor = _require_user()
    entry = timer_service.pause_timer(actor)
    db.session.commit()
    return jsonify(_serialize(entry))


@bp.post("/resume")
@jwt_required()
def resume() -> Response:
    actor = _require_user()
    entry = timer_service.resume_timer(actor)
    db.session.commit()
    return jsonify(_serialize(entry))


@bp.post("/stop")
@jwt_required()
def stop() -> Response:
    actor = _require_user()
    try:
        entry = timer_service.stop_timer(actor)
    except NotFoundError as exc:
        raise NotFoundError("no active timer") from exc
    db.session.commit()
    return jsonify(_serialize(entry))

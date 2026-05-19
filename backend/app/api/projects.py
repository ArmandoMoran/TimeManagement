from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.api._helpers import parse_json
from app.auth.decorators import require_role
from app.extensions import db
from app.models import Role
from app.schemas.project import (
    ProjectCreate,
    ProjectMemberResponse,
    ProjectMemberSet,
    ProjectResponse,
    ProjectUpdate,
)
from app.services import project_service

if TYPE_CHECKING:
    from flask.wrappers import Response

bp = Blueprint("projects", __name__)


def _serialize(project: object) -> dict[str, object]:
    return ProjectResponse.model_validate(project).model_dump(mode="json")


def _serialize_member(member: object) -> dict[str, object]:
    return ProjectMemberResponse.model_validate(member).model_dump(mode="json")


@bp.get("")
@jwt_required()
def list_projects() -> Response:
    raw_client_id = request.args.get("client_id")
    client_id = UUID(raw_client_id) if raw_client_id else None
    projects = project_service.list_projects(client_id)
    return jsonify({"projects": [_serialize(p) for p in projects]})


@bp.get("/<uuid:project_id>")
@jwt_required()
def get_project(project_id: UUID) -> Response:
    project = project_service.get_project(project_id)
    return jsonify(_serialize(project))


@bp.post("")
@jwt_required()
@require_role(Role.ADMIN)
def create_project() -> tuple[Response, int]:
    payload = parse_json(ProjectCreate, request.get_json(silent=True) or {})
    project = project_service.create_project(**payload.model_dump())
    db.session.commit()
    return jsonify(_serialize(project)), 201


@bp.patch("/<uuid:project_id>")
@jwt_required()
@require_role(Role.ADMIN)
def update_project(project_id: UUID) -> Response:
    payload = parse_json(ProjectUpdate, request.get_json(silent=True) or {})
    project = project_service.update_project(project_id, **payload.model_dump(exclude_unset=True))
    db.session.commit()
    return jsonify(_serialize(project))


@bp.delete("/<uuid:project_id>")
@jwt_required()
@require_role(Role.ADMIN)
def delete_project(project_id: UUID) -> tuple[Response, int]:
    project_service.delete_project(project_id)
    db.session.commit()
    return jsonify({"deleted": True}), 200


@bp.get("/<uuid:project_id>/members")
@jwt_required()
def list_members(project_id: UUID) -> Response:
    members = project_service.list_members(project_id)
    return jsonify({"members": [_serialize_member(m) for m in members]})


@bp.post("/<uuid:project_id>/members")
@jwt_required()
@require_role(Role.ADMIN)
def add_member(project_id: UUID) -> tuple[Response, int]:
    payload = parse_json(ProjectMemberSet, request.get_json(silent=True) or {})
    member = project_service.set_member(
        project_id,
        user_id=payload.user_id,
        rate_override_cents=payload.rate_override_cents,
    )
    db.session.commit()
    return jsonify(_serialize_member(member)), 201


@bp.delete("/<uuid:project_id>/members/<uuid:user_id>")
@jwt_required()
@require_role(Role.ADMIN)
def remove_member(project_id: UUID, user_id: UUID) -> tuple[Response, int]:
    project_service.remove_member(project_id, user_id)
    db.session.commit()
    return jsonify({"deleted": True}), 200

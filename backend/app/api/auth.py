from __future__ import annotations

from typing import TYPE_CHECKING, Any

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    current_user,
    get_jwt,
    jwt_required,
    verify_jwt_in_request,
)
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from app.errors import AuthenticationError, ForbiddenError, ValidationError
from app.extensions import db, limiter
from app.models import Role, User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokensResponse,
    UserResponse,
)
from app.services import auth_service

if TYPE_CHECKING:
    from flask.wrappers import Response

bp = Blueprint("auth", __name__)


def _parse_json[M: BaseModel](model_cls: type[M], payload: Any) -> M:
    try:
        return model_cls.model_validate(payload)
    except PydanticValidationError as exc:
        raise ValidationError("invalid request body", details={"errors": exc.errors()}) from exc


def _tokens_envelope(user: User) -> dict[str, Any]:
    tokens = auth_service.issue_tokens(user)
    return TokensResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user=UserResponse.model_validate(user),
    ).model_dump(mode="json")


@bp.post("/register")
def register() -> tuple[Response, int]:
    payload = _parse_json(RegisterRequest, request.get_json(silent=True) or {})

    if auth_service.is_first_user():
        # Bootstrap path: first user becomes admin regardless of requested role.
        user = auth_service.register_user(
            email=payload.email,
            password=payload.password,
            name=payload.name,
            role=Role.ADMIN,
        )
        db.session.commit()
        return jsonify(_tokens_envelope(user)), 201

    # After bootstrap, only an admin can register others.
    verify_jwt_in_request()
    actor: User | None = current_user
    if actor is None or actor.role is not Role.ADMIN:
        raise ForbiddenError("admin required to create users")

    user = auth_service.register_user(
        email=payload.email,
        password=payload.password,
        name=payload.name,
        role=payload.role,
    )
    db.session.commit()
    return jsonify(UserResponse.model_validate(user).model_dump(mode="json")), 201


@bp.post("/login")
@limiter.limit("10 per minute")
def login() -> tuple[Response, int]:
    payload = _parse_json(LoginRequest, request.get_json(silent=True) or {})
    user = auth_service.authenticate(payload.email, payload.password)
    return jsonify(_tokens_envelope(user)), 200


@bp.post("/refresh")
@jwt_required(refresh=True)
def refresh() -> Response:
    user: User | None = current_user
    if user is None:
        raise AuthenticationError("invalid refresh token")
    current_jti = get_jwt()["jti"]
    pair = auth_service.rotate_refresh_token(current_jti, user)
    db.session.commit()
    return jsonify(
        TokensResponse(
            access_token=pair["access_token"],
            refresh_token=pair["refresh_token"],
            user=UserResponse.model_validate(user),
        ).model_dump(mode="json")
    )


@bp.post("/logout")
@jwt_required(verify_type=False)
def logout() -> tuple[Response, int]:
    auth_service.revoke_jti(get_jwt()["jti"])
    db.session.commit()
    return jsonify({"revoked": True}), 200


@bp.get("/me")
@jwt_required()
def me() -> Response:
    user: User | None = current_user
    if user is None:
        raise AuthenticationError("session not found")
    return jsonify(UserResponse.model_validate(user).model_dump(mode="json"))

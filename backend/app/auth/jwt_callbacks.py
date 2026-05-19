from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from app.extensions import db
from app.models import RevokedToken, User

if TYPE_CHECKING:
    from flask_jwt_extended import JWTManager


def register_jwt_callbacks(jwt_manager: JWTManager) -> None:
    @jwt_manager.user_identity_loader
    def user_identity(user: User) -> str:
        return str(user.id)

    @jwt_manager.user_lookup_loader
    def user_lookup(_jwt_header: dict[str, Any], jwt_data: dict[str, Any]) -> User | None:
        identity = jwt_data["sub"]
        return db.session.get(User, UUID(identity))

    @jwt_manager.token_in_blocklist_loader
    def is_token_revoked(_jwt_header: dict[str, Any], jwt_data: dict[str, Any]) -> bool:
        jti: str = jwt_data["jti"]
        return db.session.query(RevokedToken.id).filter_by(jti=jti).first() is not None

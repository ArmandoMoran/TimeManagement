from __future__ import annotations

from typing import TypedDict

from argon2.exceptions import VerifyMismatchError
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token

from app.errors import AuthenticationError, ConflictError
from app.extensions import db, password_hasher
from app.models import RevokedToken, Role, User


class TokenPair(TypedDict):
    access_token: str
    refresh_token: str


def hash_password(plaintext: str) -> str:
    return password_hasher.hash(plaintext)


def verify_password(stored_hash: str, plaintext: str) -> bool:
    try:
        password_hasher.verify(stored_hash, plaintext)
    except VerifyMismatchError:
        return False
    return True


def is_first_user() -> bool:
    return db.session.query(User.id).first() is None


def register_user(*, email: str, password: str, name: str, role: Role = Role.EMPLOYEE) -> User:
    """Create a new user. Caller enforces the bootstrap-admin / admin-only rule."""
    existing = db.session.execute(
        db.select(User).where(User.email == email.lower())
    ).scalar_one_or_none()
    if existing is not None:
        raise ConflictError("a user with that email already exists")

    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        name=name,
        role=role,
    )
    db.session.add(user)
    db.session.flush()
    return user


def authenticate(email: str, password: str) -> User:
    user: User | None = db.session.execute(
        db.select(User).where(User.email == email.lower())
    ).scalar_one_or_none()
    if user is None or not user.active:
        raise AuthenticationError("invalid credentials")
    if not verify_password(user.password_hash, password):
        raise AuthenticationError("invalid credentials")
    return user


def issue_tokens(user: User) -> TokenPair:
    access: str = create_access_token(identity=user)
    refresh: str = create_refresh_token(identity=user)
    return TokenPair(access_token=access, refresh_token=refresh)


def revoke_jti(jti: str) -> None:
    if db.session.query(RevokedToken.id).filter_by(jti=jti).first() is not None:
        return
    db.session.add(RevokedToken(jti=jti))
    db.session.flush()


def rotate_refresh_token(current_refresh_jti: str, user: User) -> TokenPair:
    """Revoke the presented refresh token and issue a new pair (rotation)."""
    revoke_jti(current_refresh_jti)
    return issue_tokens(user)


def jti_from(token: str) -> str:
    decoded = decode_token(token)
    return str(decoded["jti"])

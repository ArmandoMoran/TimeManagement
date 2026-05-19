from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from app.extensions import db
from app.models import RevokedToken, Role, User

if TYPE_CHECKING:
    from flask.testing import FlaskClient


def _bootstrap_admin(client: FlaskClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "founder@example.com",
            "password": "long-enough-pw",
            "name": "Founder",
        },
    )
    assert response.status_code == 201
    body = response.get_json()
    assert isinstance(body, dict)
    return {
        "access_token": body["access_token"],
        "refresh_token": body["refresh_token"],
        "user_id": body["user"]["id"],
    }


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def test_first_register_creates_admin_and_returns_tokens(client: FlaskClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "first@example.com",
            "password": "long-enough-pw",
            "name": "First",
        },
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["user"]["role"] == "admin"
    assert body["user"]["email"] == "first@example.com"
    assert body["access_token"]
    assert body["refresh_token"]


def test_second_register_without_auth_is_forbidden(client: FlaskClient) -> None:
    _bootstrap_admin(client)

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "intruder@example.com",
            "password": "long-enough-pw",
            "name": "Intruder",
        },
    )

    assert response.status_code == 401


def test_admin_can_register_other_users(client: FlaskClient) -> None:
    admin = _bootstrap_admin(client)

    response = client.post(
        "/api/v1/auth/register",
        headers=_auth_headers(admin["access_token"]),
        json={
            "email": "employee@example.com",
            "password": "long-enough-pw",
            "name": "Employee",
            "role": "employee",
        },
    )

    assert response.status_code == 201
    assert response.get_json()["role"] == "employee"


def test_non_admin_cannot_register_other_users(client: FlaskClient) -> None:
    admin = _bootstrap_admin(client)
    client.post(
        "/api/v1/auth/register",
        headers=_auth_headers(admin["access_token"]),
        json={
            "email": "employee@example.com",
            "password": "long-enough-pw",
            "name": "Employee",
            "role": "employee",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "employee@example.com", "password": "long-enough-pw"},
    )
    employee_token = login.get_json()["access_token"]

    response = client.post(
        "/api/v1/auth/register",
        headers=_auth_headers(employee_token),
        json={
            "email": "another@example.com",
            "password": "long-enough-pw",
            "name": "Another",
        },
    )

    assert response.status_code == 403


def test_login_with_valid_credentials_returns_tokens(client: FlaskClient) -> None:
    _bootstrap_admin(client)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "founder@example.com", "password": "long-enough-pw"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["user"]["email"] == "founder@example.com"


def test_login_with_wrong_password_returns_401(client: FlaskClient) -> None:
    _bootstrap_admin(client)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "founder@example.com", "password": "wrong-password-x"},
    )

    assert response.status_code == 401


def test_login_with_unknown_email_returns_401(client: FlaskClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "long-enough-pw"},
    )

    assert response.status_code == 401


def test_me_with_valid_token_returns_user(client: FlaskClient) -> None:
    admin = _bootstrap_admin(client)

    response = client.get("/api/v1/auth/me", headers=_auth_headers(admin["access_token"]))

    assert response.status_code == 200
    body = response.get_json()
    assert body["email"] == "founder@example.com"
    assert body["role"] == "admin"


def test_me_without_token_returns_401(client: FlaskClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_refresh_rotates_token_and_revokes_old(client: FlaskClient) -> None:
    admin = _bootstrap_admin(client)
    old_refresh = admin["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        headers=_auth_headers(old_refresh),
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["refresh_token"] != old_refresh
    assert body["access_token"]

    # Reusing the old refresh should now be revoked → 401.
    reuse = client.post(
        "/api/v1/auth/refresh",
        headers=_auth_headers(old_refresh),
    )
    assert reuse.status_code == 401


def test_logout_revokes_current_token(client: FlaskClient) -> None:
    admin = _bootstrap_admin(client)
    headers = _auth_headers(admin["access_token"])

    logout = client.post("/api/v1/auth/logout", headers=headers)
    assert logout.status_code == 200

    # Same token now blocklisted.
    after = client.get("/api/v1/auth/me", headers=headers)
    assert after.status_code == 401


def test_password_is_stored_as_argon2_hash(client: FlaskClient) -> None:
    _bootstrap_admin(client)

    user = db.session.execute(
        db.select(User).where(User.email == "founder@example.com")
    ).scalar_one()

    assert user.password_hash.startswith("$argon2")
    assert "long-enough-pw" not in user.password_hash


def test_duplicate_email_register_returns_409(client: FlaskClient) -> None:
    admin = _bootstrap_admin(client)

    response = client.post(
        "/api/v1/auth/register",
        headers=_auth_headers(admin["access_token"]),
        json={
            "email": "founder@example.com",
            "password": "long-enough-pw",
            "name": "Dup",
        },
    )

    assert response.status_code == 409


@pytest.mark.parametrize(
    "missing_field",
    ["email", "password", "name"],
)
def test_register_missing_required_field_returns_422(
    client: FlaskClient, missing_field: str
) -> None:
    payload = {
        "email": "x@example.com",
        "password": "long-enough-pw",
        "name": "X",
    }
    del payload[missing_field]

    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 422


def test_revoked_token_table_grows_on_refresh_and_logout(client: FlaskClient) -> None:
    admin = _bootstrap_admin(client)

    assert db.session.scalar(db.select(db.func.count(RevokedToken.id))) == 0

    client.post(
        "/api/v1/auth/refresh",
        headers=_auth_headers(admin["refresh_token"]),
    )
    assert db.session.scalar(db.select(db.func.count(RevokedToken.id))) == 1


def test_inactive_user_cannot_login(client: FlaskClient) -> None:
    _bootstrap_admin(client)
    user = db.session.execute(
        db.select(User).where(User.email == "founder@example.com")
    ).scalar_one()
    user.active = False
    db.session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "founder@example.com", "password": "long-enough-pw"},
    )

    assert response.status_code == 401


def test_role_enum_persisted_as_string(client: FlaskClient) -> None:
    _bootstrap_admin(client)
    user = db.session.execute(
        db.select(User).where(User.email == "founder@example.com")
    ).scalar_one()

    assert user.role is Role.ADMIN
    assert user.role.value == "admin"

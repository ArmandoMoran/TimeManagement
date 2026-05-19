"""Test helpers shared across integration files.

Lightweight functions that POST to endpoints — exercising the same paths real
clients use rather than reaching into the ORM directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask.testing import FlaskClient


def auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def bootstrap_admin(
    client: FlaskClient,
    *,
    email: str = "admin@example.com",
    password: str = "long-enough-pw",
    name: str = "Admin",
) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "name": name},
    )
    assert response.status_code == 201, response.get_json()
    body = response.get_json()
    return {
        "email": email,
        "password": password,
        "name": name,
        "access_token": body["access_token"],
        "refresh_token": body["refresh_token"],
        "user_id": body["user"]["id"],
    }


def register_user(
    client: FlaskClient,
    *,
    admin_token: str,
    email: str,
    password: str = "long-enough-pw",
    name: str = "User",
    role: str = "employee",
) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register",
        headers=auth_headers(admin_token),
        json={"email": email, "password": password, "name": name, "role": role},
    )
    assert response.status_code == 201, response.get_json()
    return {"id": response.get_json()["id"], "email": email, "password": password}


def login(client: FlaskClient, *, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.get_json()
    return str(response.get_json()["access_token"])


def create_client_record(
    client: FlaskClient, *, admin_token: str, name: str = "Acme Co"
) -> dict[str, object]:
    response = client.post(
        "/api/v1/clients",
        headers=auth_headers(admin_token),
        json={"name": name},
    )
    assert response.status_code == 201, response.get_json()
    body = response.get_json()
    assert isinstance(body, dict)
    return body


def create_project(
    client: FlaskClient,
    *,
    admin_token: str,
    client_id: str,
    name: str = "Acme Site",
    default_rate_cents: int | None = 15000,
    rounding_minutes: int = 6,
) -> dict[str, object]:
    response = client.post(
        "/api/v1/projects",
        headers=auth_headers(admin_token),
        json={
            "client_id": client_id,
            "name": name,
            "default_rate_cents": default_rate_cents,
            "rounding_minutes": rounding_minutes,
        },
    )
    assert response.status_code == 201, response.get_json()
    body = response.get_json()
    assert isinstance(body, dict)
    return body
